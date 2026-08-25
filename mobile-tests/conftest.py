"""
Session-scoped, self-healing Appium driver + pytest reporting hooks for
the FitFuel Android suite.

Background: this project and KrishiIQ (a sibling final-year project,
github.com/Siddamharinireddy/KrishiIQ) share the same underlying
failure mode -- appium-flutter-driver processes commands through a
single serial queue, and if the *client* gives up on a `flutter:waitFor`
(its own APPIUM_COMMAND_TIMEOUT expires) while the *Dart side* never
actually resolves that call, the server does not cancel it. It just
sits in the queue forever, and every command issued afterwards queues
up behind it -- confirmed against real CI logs here as a flat ~12s tax
(exactly APPIUM_COMMAND_TIMEOUT) on every subsequent command, and in
KrishiIQ's own conftest.py as "the Flutter Observatory connection drops
and FlutterDriver can never reconnect it again for the rest of that
session."

A previous version of this file worked around that by creating a fresh
Appium session (full APK reinstall) per test MODULE instead of once per
whole run, to bound a wedge's blast radius to one file. That works, but
it's the expensive version of the fix and KrishiIQ already solved the
same problem more cheaply: keep ONE Appium session per shard, but
relaunch the *app* (terminate_app + activate_app -- an activity
restart, not a session/APK reinstall) before every single test via an
autouse fixture. That gives every test a genuinely fresh app process
(and therefore a fresh Dart isolate, which is what actually clears a
wedge) for a fraction of the cost, and it doubles as real test
isolation instead of relying on tests leaving the app in a state the
next test expects.

If the relaunch itself fails -- the one case a fresh app process can't
fix, because the FlutterDriver/Observatory connection to the *old*
process is what's actually dead -- `ResilientDriver.recreate()` quits
and reopens the whole Appium session once, reactively, and only then.
This is strictly better than the module-scoped approach: recovery is
attempted at the cheap layer first (app restart) and only escalates to
the expensive layer (new session) when that's not enough, instead of
always paying the expensive cost on every module boundary regardless of
whether anything actually went wrong.

CORRECTION (root-caused against a real 4-shard CI run where 223/225
tests failed): "relaunch the app before every test" turned out NOT to
be sufficient on its own, and the diagnosis above ("a fresh Dart isolate
is what actually clears a wedge") was incomplete. The FlutterDriver
command queue that gets wedged lives in the *Appium server process*,
keyed to the WebDriver *session* -- not in the app's Dart isolate. Killing
and relaunching the app process does nothing to a queue that lives one
layer up, outside that process entirely. In the real failure, one
`tap()` call (`login_register_link`, called from a page object's
`tap_key()`) never got acked, and because that particular call site was
unguarded, the resulting exception propagated straight out of the test
instead of being caught anywhere -- so nothing ever told this fixture,
or `ResilientDriver`, that the session needed recreating. Every later
test in the shard then queued up behind the dead command and timed out
too, one after another, for the rest of the run.

The actual fix lives in `page_objects/base_page.py`: every raw
driver/element call (`click()`, `clear()`, `send_keys()`, `.text`, plus
the two genuinely-a-timeout branches of `is_displayed()`) is now wrapped
in `BasePage._recovering()`, which calls `driver.recreate()` itself the
moment one of those calls raises a real timeout -- proactively, from
wherever the wedge actually happens, rather than only reactively here
when `activate_app()` happens to raise. This fixture's own
activate_app-failure escalation stays as a second, cheaper-to-reach
layer of the same circuit breaker; the two are complementary, not
redundant.

Because the app now restarts before every test, `logged_in_session` and
`primary_test_account` go back to session scope: `noReset: False` means
the installed app's local storage (including the auth token
SharedPreferences checks on splash) survives an app restart even though
the process doesn't, so after the first test registers
`primary_test_account`, every later test's restart lands back on the
dashboard already logged in -- no re-registration, no re-login call
needed, exactly like the original once-per-run design intended.

This mirrors selenium-tests/conftest.py's "one browser, function-scoped
auth fixture layered on top" pattern as closely as the driver-per-app
constraint of mobile testing allows.
"""
from __future__ import annotations

import json
import os
import random
import string
import subprocess
import time
from datetime import datetime, timezone

import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions

import config
from utils import adb_helpers
from utils.appium_connection import (
    build_session_creation_executor,
    configure_default_timeout,
    swap_to_short_timeout,
)

# Must happen before any AppiumConnection/session is created.
configure_default_timeout()

if config.CAPTURE_SCREENSHOTS:
    os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(config.LOGS_DIR, exist_ok=True)

_RESULTS: list[dict] = []
_RUN_STARTED_AT = datetime.now(timezone.utc)
_LOGCAT_MARKERS: dict[str, str] = {}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    # Record where the device logcat buffer is *before* this test runs,
    # so a failure only pulls this test's own lines instead of the
    # entire (ever-growing) buffer since boot -- see _capture_failure_artifacts.
    try:
        _LOGCAT_MARKERS[item.nodeid] = adb_helpers.logcat_time_marker()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────
# Driver session: ONE Appium session per shard's pytest process (back to
# session scope -- see file-level docstring for why the module-scoped
# version was replaced). `ResilientDriver` wraps the real session behind
# a stable object so that `recreate()` can swap out a dead `_raw` session
# for a fresh one without invalidating every page object's `self.driver`
# reference -- they all hold this wrapper, not the raw webdriver, so
# recreation is transparent to already-instantiated page objects.
# ─────────────────────────────────────────────────────────────────────────
class ResilientDriver:
    def __init__(self):
        self._raw = None
        self._create()

    def _create(self, _is_recovery_create: bool = False):
        apk_path = os.path.abspath(config.APK_PATH)
        assert os.path.exists(apk_path), (
            f"Test APK not found at {apk_path}. Build it first with:\n"
            f"  cd fitfuel_mobile && flutter build apk --debug -t lib/main_test.dart "
            f"--dart-define=API_BASE_URL={config.BACKEND_BASE_URL}"
        )

        options = AppiumOptions()
        options.set_capability("platformName", "Android")
        options.set_capability("appium:automationName", "Flutter")
        options.set_capability("appium:deviceName", config.DEVICE_NAME)
        options.set_capability("appium:app", apk_path)
        options.set_capability("appium:appPackage", config.APP_PACKAGE)
        options.set_capability("appium:appActivity", config.APP_ACTIVITY)
        options.set_capability("appium:newCommandTimeout", 300)
        options.set_capability("appium:autoGrantPermissions", True)
        options.set_capability("appium:noReset", False)
        if config.PLATFORM_VERSION:  # empty = auto-detect (don't send cap at all)
            options.set_capability("appium:platformVersion", config.PLATFORM_VERSION)
        # Gives Appium's own session-creation-time wait for the Flutter Driver
        # extension to become responsive more headroom (was previously unset,
        # falling back to appium-flutter-driver's default, which is tighter
        # than this emulator's actual cold-start latency needs).
        options.set_capability("appium:flutterServerLaunchTimeout", 45000)

        creation_executor = build_session_creation_executor(config.APPIUM_SERVER_URL)
        self._raw = webdriver.Remote(
            command_executor=creation_executor,
            options=options,
        )
        # Appium's NEW_SESSION response returning successfully only means the
        # app was installed and launched -- it does NOT guarantee the Flutter
        # Dart VM + Observatory handshake (enableFlutterDriverExtension in
        # main_test.dart) has actually finished. On this CI emulator that cold
        # start can legitimately take longer than the everyday 12s command
        # timeout. Every single test_02_registration.py failure was a raw
        # urllib3 ReadTimeoutError (read timeout=12) on the very first
        # command of the session -- not a controlled "element not found"
        # 500 -- confirming this was a startup race, not a real app/test bug.
        #
        # CORRECTION: an earlier version of this warm-up used a
        # `wait_for_key("onboarding_skip_button", timeout=30)` call instead of
        # a plain sleep. That was a real regression: with `noReset: False`,
        # if the app happens to already have onboarding marked complete from
        # a prior install, that key never appears, and a real CI run showed
        # every single test after this point failing in a flat, exact ~12.0s
        # each while the raw Appium server log showed its internal command
        # queue depth climbing without bound and never draining -- consistent
        # with appium-flutter-driver's single-command-at-a-time extension
        # getting permanently wedged behind one Dart-side waitFor call that
        # the client gave up on but the server never actually cancelled. A
        # plain sleep cannot get stuck like this regardless of what screen
        # the app lands on, at the cost of not adapting to a faster-than-usual
        # boot -- worth the trade-off given the alternative is a fully dead
        # session for the rest of the run.
        time.sleep(20)
        # Session exists now -- fall back to the short everyday-command
        # timeout so a single wedged find/tap fails fast instead of hanging
        # for the (much longer) session-creation timeout on every command.
        swap_to_short_timeout(self._raw, config.APPIUM_SERVER_URL)
        # Skip the shader warm-up when _create() is being called recursively
        # as recovery from a warm-up failure -- the new session already had
        # its 20s startup sleep and calling warm-up again would recurse.
        if not _is_recovery_create:
            self._warm_up_shader_cache()

    def _warm_up_shader_cache(
        self,
        steps: list[str] | None = None,
        recover_on_failure: bool = True,
    ) -> None:
        """Best-effort: force a screen's first paint so its GPU shaders
        get compiled here instead of during a real test's timed tap.

        `steps`: sequence of ValueKeys to wait-for-then-tap, in order.
        Defaults to `["onboarding_skip_button", "login_register_link"]`,
        which warms RegisterScreen's first paint -- this is what every
        fresh session/process creation calls with no arguments. See
        below for why RegisterScreen specifically needs this.

        `recover_on_failure`: if a step's wait/tap fails, escalate to a
        full session recreate. That's the right call when this runs
        right after a session was JUST created (the original call site
        below, in `_create()`) -- there's nothing valuable to lose yet.
        Pass False when warming an ALREADY-established, valuable app
        state instead (e.g. warming Progress right after
        `ensure_on_dashboard`'s own clear_app_data recovery has just
        landed back on Dashboard) -- a session recreate there would be
        far more disruptive than just leaving that one screen's shader
        cold, so the failure is swallowed and we move on instead.

        Why RegisterScreen needs this at all, root-caused against a real
        CI log (mobile-tests/README.md -> "First-paint shader jank on
        login_register_link" has the full annotated trace): every fresh
        Appium session -- not just the first one of the whole run -- does
        `pm clear` on the app as part of `appium:noReset: False`'s "fast
        reset" (visible as "Performing fast reset ... (stop and clear)"
        in the server log on every single session creation, including
        ones from `recreate()` mid-shard). `pm clear` wipes the app's
        on-disk Skia GPU-program cache along with everything else in its
        data dir, so EVERY fresh session hits first-paint shader-compile
        cost on the exact same widget tree, not just once per run.
        RegisterScreen is the first screen in the whole suite that paints
        a BoxShadow at all. appium-flutter-driver's tap command carries
        no timeout of its own (unlike flutter:waitFor, which always sends
        an explicit timeout the Dart side enforces) -- confirmed by
        diffing the actual command payloads in a CI log: waitFor calls
        always include a "timeout" key, tap/click calls never do. So a
        slow first paint there leaves the tap with nothing to time it out
        Dart-side; our own client eventually gives up (APPIUM_COMMAND_TIMEOUT,
        see utils/appium_connection.py) and `_recovering()` in base_page.py
        recreates the session -- which itself does another `pm clear`,
        restarting the exact same cycle on the next Register-touching
        test. Paying the shader-warm cost once here, right after every
        session creation/recreation and before any real test runs, means
        every actual test tap on that widget tree hits an
        already-compiled shader instead.

        The exact same mechanism applies to `adb_helpers.clear_app_data()`
        calls elsewhere (it's the same `pm clear` under the hood) -- see
        `ensure_on_dashboard()`'s call with `steps=[NAV_PROGRESS, NAV_HOME]`
        for Progress, which hits the identical first-paint cost as the
        first not-yet-painted screen visited right after such a recovery.

        Deliberately swallows everything: this is a best-effort perf
        optimization, not a correctness requirement. If a warm-up tap
        itself times out, that's fine -- the shader compile almost
        certainly still happened on the GPU/raster thread even though our
        client gave up waiting for the ack, so the cache is warm
        regardless of whether we saw a clean response back.
        """
        from appium_flutter_finder import FlutterElement, FlutterFinder

        if steps is None:
            steps = ["onboarding_skip_button", "login_register_link"]

        f = FlutterFinder()
        for key in steps:
            try:
                self._raw.execute_script("flutter:waitFor", f.by_value_key(key), 15000)
                FlutterElement(self._raw, f.by_value_key(key)).click()
            except Exception:
                # If the click (not just the waitFor) failed, the Appium
                # server's single FlutterDriver command queue may now be
                # wedged behind a tap command the Dart side never acked.
                if recover_on_failure:
                    # Recreating here costs one extra session startup but
                    # guarantees a clean queue for whatever real test runs
                    # next -- better than letting a wedge from warm-up
                    # propagate. _is_recovery_create=True prevents the new
                    # session from calling _warm_up_shader_cache() again,
                    # which would recurse.
                    try:
                        self._raw.quit()
                    except Exception:
                        pass
                    self._create(_is_recovery_create=True)
                return
        # Give the (possibly still in-flight) shader compile + first frame
        # a moment to actually finish on the GPU/raster thread before
        # handing control back -- a plain sleep, not a wait_for, because
        # the point is just "don't race the compile", not "confirm a
        # specific screen loaded".
        time.sleep(5)

    def recreate(self):
        """Quit whatever's left of a dead session and open a fresh one.
        Only called reactively, from `_restart_app_between_tests` below,
        when a plain app restart (terminate_app + activate_app) wasn't
        enough to recover -- i.e. the FlutterDriver/Observatory
        connection to the old process is what's actually wedged, not
        just the app's UI state."""
        try:
            self._raw.quit()
        except Exception:
            pass
        self._create()

    def __getattr__(self, name):
        # Forwards everything else -- terminate_app, activate_app,
        # execute_script, get_screenshot_as_file, quit, etc. -- to
        # whichever real session is currently live.
        return getattr(self._raw, name)


@pytest.fixture(scope="session")
def driver():
    drv = ResilientDriver()

    yield drv

    try:
        drv.quit()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _restart_app_between_tests(driver):
    """Relaunch the app fresh before every test (terminate_app +
    activate_app -- a fast activity restart, not a new Appium session)
    so every test gets a genuinely fresh Dart isolate/FlutterDriver
    connection instead of relying on whatever state the previous test
    left behind. This is what actually clears a wedged command queue
    (see file-level docstring): the wedge lives in the *old* isolate,
    and killing that process is what un-sticks it, cheaply.

    If activate_app itself fails, the wedge is bad enough that the old
    process's FlutterDriver/Observatory connection can't be recovered
    at all -- escalate to a full session recreate, once, then retry.
    """
    try:
        driver.terminate_app(config.APP_PACKAGE)
    except Exception:
        pass
    try:
        driver.activate_app(config.APP_PACKAGE)
    except Exception:
        driver.recreate()
        driver.activate_app(config.APP_PACKAGE)
    yield


@pytest.fixture(scope="session")
def unique_email_factory():
    """fitfuel-final has NO seeded demo accounts (unlike the KrishiIQ
    reference project) -- every auth-dependent test that needs its own
    account registers a fresh one with a collision-proof email."""

    def _make(prefix: str = "qa") -> str:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{prefix}.{suffix}@fitfuel-mobile-tests.invalid"

    return _make


@pytest.fixture(scope="session")
def primary_test_account(unique_email_factory):
    """One registered + fully onboarded account, created once per whole
    run. `noReset: False` plus the per-test app restart in
    `_restart_app_between_tests` means this account's login persists in
    local storage across every later test's restart, so
    `logged_in_session` only ever needs to register once and every
    subsequent test lands back on the dashboard already logged in."""
    return {
        "email": unique_email_factory("primary"),
        "password": "TestPass123!",
        "name": "QA Primary Account",
        "age": "27",
        "height_cm": "170",
        "weight_kg": "68",
        "gender": "female",
    }


@pytest.fixture(scope="function")
def restore_network(request):
    """Any test that flips the emulator's network off (error-handling
    tests) MUST restore it on the way out, even on failure -- otherwise
    every subsequent test in the session silently fails for an unrelated
    reason. This fixture guarantees the restore regardless of outcome."""
    yield
    adb_helpers.set_network_online()


@pytest.fixture(scope="function")
def restore_font_scale():
    yield
    adb_helpers.set_font_scale(1.0)


@pytest.fixture(scope="function")
def restore_orientation():
    yield
    adb_helpers.rotate_portrait()


@pytest.fixture(scope="session")
def logged_in_session(driver, primary_test_account):
    """Registers `primary_test_account` exactly once for the whole run
    (first call) and leaves the driver on the dashboard, logged in.
    Every module that just needs an authenticated app (dashboard,
    recommendations, progress, profile, navigation, etc.) depends
    on this fixture rather than re-registering per test -- registration
    itself is covered exhaustively and independently in
    test_02_registration.py.

    Robustness note: if a mid-shard session recreate (see _recovering()
    in base_page.py) left the app in an ambiguous state -- e.g. neither
    on dashboard nor on a clean onboarding/login screen -- we force-clear
    app data to guarantee a known starting point before attempting the
    full registration flow."""
    from page_objects.dashboard_page import DashboardPage
    from utils import adb_helpers, session_helpers

    dashboard = DashboardPage(driver)
    # Give the dashboard a generous look -- after a session recreate the
    # app may still be mid-splash/startup.
    if dashboard.is_loaded(timeout=8):
        # Already logged in from a prior test in this shard (e.g. a
        # test_01_authentication test that registered and didn't log out).
        # Nothing to do -- the account already exists and the app is on
        # the right screen.
        return primary_test_account
    # Not on dashboard. Try to reach a clean onboarding/login state.
    # If the app is in some mid-flow or unexpected screen (post-recreate),
    # force-clear its data so register_new_account() always starts from
    # a known onboarding/login entry point.
    from page_objects.onboarding_page import OnboardingPage
    from page_objects.auth_pages import LoginPage
    on_onboarding = OnboardingPage(driver).is_loaded(timeout=4)
    on_login = LoginPage(driver).is_loaded(timeout=4)
    if not on_onboarding and not on_login:
        adb_helpers.clear_app_data()
        driver.activate_app(config.APP_PACKAGE)
        time.sleep(5)
    session_helpers.register_new_account(driver, primary_test_account)
    return primary_test_account


def ensure_on_dashboard(driver, logged_in_session):
    """Plain function holding on_dashboard's self-healing "wait for the
    dashboard nav bar, recover if needed" logic, extracted out of the
    fixture below so module/class-scoped fixtures can reuse it too.
    pytest forbids a wider-scoped fixture from depending on a
    narrower-scoped one (ScopeMismatch) -- test_01_authentication.py's
    module-scoped `registered_account` only ever needed this recovery
    logic to make its own logout() call reliable, not the function-scoped
    fixture injection itself, so it imports and calls this directly
    instead of declaring on_dashboard as a dependency.

    Two distinct "not on dashboard" cases, handled differently (found by
    root-causing the single largest cluster of CI failures -- 157 of 229
    -- which all traced back to this function's old, single-branch
    recovery):
      1. On a *different* shell screen (nav bar exists, just not on the
         home tab) -- a single nav_to_home() tap recovers, as before.
      2. Logged out entirely, with no nav bar at all -- e.g.
         test_02_registration.py's happy-path test explicitly calls
         session_helpers.logout() on its own throwaway account. That
         clears the app's one stored session token regardless of which
         account was logged in, so with noReset:False every later
         `_restart_app_between_tests` relaunch lands back on the login
         screen instead of auto-resuming to dashboard -- for the rest of
         the shard, not just that one test. The old code assumed case 1
         unconditionally and tapped nav_tab_home blindly; with no nav
         bar to tap, that just timed out and cascaded into every test
         that depended on this fixture afterwards. Check the nav bar
         actually exists before assuming a tap will work; if it doesn't,
         log the already-registered primary_test_account back in
         instead.
    """
    from page_objects.dashboard_page import DashboardPage
    from page_objects.onboarding_page import OnboardingPage
    from page_objects.auth_pages import LoginPage
    from utils import adb_helpers, session_helpers

    dashboard = DashboardPage(driver)
    if dashboard.is_loaded(timeout=8):
        return dashboard

    if dashboard.wait_for_key(dashboard.NAV_HOME, timeout=5):
        dashboard.nav_to_home()
        assert dashboard.is_loaded(timeout=10)
        return dashboard

    # No nav bar at all -- get to a known login entry point, then log
    # the already-registered account back in rather than re-registering.
    onboarding = OnboardingPage(driver)
    if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
        onboarding.skip()
    login = LoginPage(driver)
    cleared_app_data = False
    if not login.is_loaded(timeout=5):
        adb_helpers.clear_app_data()
        cleared_app_data = True
        driver.activate_app(config.APP_PACKAGE)
        time.sleep(5)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=10):
            onboarding.skip()
    session_helpers.login(
        driver, logged_in_session["email"], logged_in_session["password"]
    )
    assert dashboard.is_loaded(timeout=15)
    if cleared_app_data:
        # clear_app_data (pm clear) wipes the on-disk Skia GPU-program
        # cache along with everything else, so the next not-yet-painted
        # screen pays a cold first-paint shader-compile cost -- the same
        # problem _warm_up_shader_cache() already solves for Register at
        # session-creation time. Progress is the specific screen this
        # bites: test_16_form_field_matrices.py's TestProgressLogFieldMatrix
        # runs right after tests that push this exact recovery branch,
        # and is the first thing to visit a not-yet-painted screen
        # afterwards -- confirmed in CI as 46/46 failures in that class
        # until this warm-up covered it too. recover_on_failure=False:
        # we already have a hard-won, valid Dashboard state above: a
        # session recreate here would throw that away for a
        # perf-optimization that isn't worth the cost if it doesn't work.
        driver._warm_up_shader_cache(
            steps=[dashboard.NAV_PROGRESS, dashboard.NAV_HOME],
            recover_on_failure=False,
        )
        assert dashboard.is_loaded(timeout=15)
    return dashboard


@pytest.fixture(scope="function")
def on_dashboard(driver, logged_in_session):
    """Function-scoped convenience fixture: guarantees the test starts
    on the dashboard tab regardless of where the previous test in the
    session left the app. See ensure_on_dashboard()'s docstring above
    for the actual recovery logic -- this fixture is just a thin,
    function-scoped wrapper around it for the many tests that depend on
    it directly."""
    return ensure_on_dashboard(driver, logged_in_session)


# ─────────────────────────────────────────────────────────────────────────
# Rerun-then-report: pytest-rerunfailures absorbs flaky first-attempt
# failures automatically (see pytest.ini reruns=1). We only record the
# FINAL outcome of each test in execution-results.json, so a test that
# failed once then passed on rerun shows as PASSED, not RERUN -- exactly
# selenium-tests/conftest.py's documented behaviour, kept identical here
# for report-format consistency across the whole test-quality suite.
# ─────────────────────────────────────────────────────────────────────────
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
        return

    existing = next((r for r in _RESULTS if r["nodeid"] == item.nodeid), None)
    status = report.outcome.upper()  # PASSED / FAILED / SKIPPED
    if status == "FAILED" and getattr(report, "wasxfail", None):
        status = "XFAIL"

    module_file = item.location[0]
    module_name = os.path.splitext(os.path.basename(module_file))[0]
    markers = [m.name for m in item.iter_markers()]

    record = {
        "nodeid": item.nodeid,
        "status": status,
        "duration_s": round(report.duration, 3),
        "module": module_file,
        "module_name": module_name,
        "markers": markers,
        "longrepr": str(report.longrepr) if report.failed else None,
    }

    if existing:
        existing.update(record)  # reruns overwrite with the final outcome
    else:
        _RESULTS.append(record)

    if report.failed:
        _capture_failure_artifacts(item)

    # Persist after EVERY test, not just at session end. 402 Appium tests
    # with --reruns 1 is a multi-hour run in the worst case (every failing
    # test runs twice), and this job has already been observed to get
    # killed mid-run (job timeout / emulator or Appium session death /
    # runner OOM) before pytest_sessionfinish ever executes. When that
    # happens, the old "write once at the end" approach silently left
    # whatever execution-results.json already existed on disk untouched --
    # in CI that's the all-zero placeholder checked into git, so
    # generate_reports.py reports "0 tests, gate FAILED" with no hint that
    # hundreds of tests actually ran and failed for real (their logcat
    # captures were still sitting right there in reports/logs/). Writing a
    # fresh, real snapshot after every single test means the on-disk JSON
    # is never more than one test behind reality, however the process ends.
    try:
        _write_results_snapshot()
    except Exception:
        # Never let report bookkeeping fail the actual test run.
        pass


def _capture_failure_artifacts(item) -> None:
    safe_name = item.nodeid.replace("::", "__").replace("/", "_")
    if config.CAPTURE_SCREENSHOTS:
        driver_fixture = item.funcargs.get("driver")
        if driver_fixture is not None:
            try:
                screenshot_path = os.path.join(config.SCREENSHOTS_DIR, f"{safe_name}.png")
                driver_fixture.get_screenshot_as_file(screenshot_path)
            except Exception:
                pass
    try:
        log_path = os.path.join(config.LOGS_DIR, f"{safe_name}.log")
        # Slice to just this test's window -- without since_marker, `adb
        # logcat -d` dumps the ENTIRE buffer since boot on every single
        # call, which is what actually bloated the reports zip (not the
        # screenshots): with reruns=1 and hundreds of failing tests, each
        # one wrote a near-full, ever-growing copy of the whole log.
        adb_helpers.pull_logcat(log_path, since_marker=_LOGCAT_MARKERS.get(item.nodeid))
    except Exception:
        pass


def _build_payload() -> dict:
    total = len(_RESULTS)
    passed = sum(1 for r in _RESULTS if r["status"] == "PASSED")
    failed = sum(1 for r in _RESULTS if r["status"] == "FAILED")
    skipped = sum(1 for r in _RESULTS if r["status"] == "SKIPPED")
    pass_rate = round((passed / total) * 100, 2) if total else 0.0

    by_module: dict[str, dict] = {}
    for r in _RESULTS:
        m = by_module.setdefault(
            r["module_name"], {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        )
        m["total"] += 1
        if r["status"] == "PASSED":
            m["passed"] += 1
        elif r["status"] == "FAILED":
            m["failed"] += 1
        elif r["status"] == "SKIPPED":
            m["skipped"] += 1

    total_duration = round(sum(r["duration_s"] for r in _RESULTS), 2)

    return {
        "app_under_test": {
            "package": config.APP_PACKAGE,
            "backend_base_url": config.BACKEND_BASE_URL,
            "platform": "Android",
            "platform_version": config.PLATFORM_VERSION,
        },
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": pass_rate,
            "total_duration_s": total_duration,
            "gate_threshold_pct": config.GATE_THRESHOLD_PCT,
            "gate_passed": pass_rate >= config.GATE_THRESHOLD_PCT,
            # Not necessarily true yet if this snapshot is mid-run --
            # see "partial" below.
            "by_module": by_module,
        },
        "results": _RESULTS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # True on every snapshot except the one written from
        # pytest_sessionfinish, so a consumer (generate_reports.py, a
        # human reading the artifact after a killed job) can tell a
        # genuinely-finished 0-total run apart from a run that was cut
        # short mid-way, instead of both looking identically like "0
        # tests, gate failed".
        "partial": True,
    }


def _write_results_snapshot() -> None:
    """Atomically (over)write reports/execution-results.json with the
    current in-memory _RESULTS. Called after every single test AND at
    session end, so the file on disk is never more than one test stale --
    if the process dies (job timeout, OOM, Appium/emulator crash) before
    pytest_sessionfinish runs, whatever was recorded up to that point is
    still there instead of a stale placeholder from git being left in
    place. Write-to-temp-then-os.replace keeps a concurrent reader (or a
    kill mid-write) from ever seeing a truncated/corrupt JSON file."""
    payload = _build_payload()
    out_path = os.path.join(config.REPORTS_DIR, "execution-results.json")
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, out_path)


def pytest_sessionfinish(session, exitstatus):
    _write_results_snapshot()
    # Overwrite the "partial" flag set by _build_payload() now that the
    # session has genuinely finished on its own (not been killed).
    out_path = os.path.join(config.REPORTS_DIR, "execution-results.json")
    with open(out_path, encoding="utf-8") as f:
        payload = json.load(f)
    payload["partial"] = False
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, out_path)