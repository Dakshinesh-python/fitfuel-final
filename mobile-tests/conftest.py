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

    def _warm_up_shader_cache(self) -> None:
        """Best-effort: force RegisterScreen's first paint once per fresh
        session/process, so its BoxShadow-heavy widgets (the form card,
        the gender selector, StepProgressBar -- see fitfuel_mobile/lib/
        screens/register_screen.dart) get their GPU shaders compiled here
        instead of during a real test's timed tap.

        Why this is needed at all, root-caused against a real CI log
        (mobile-tests/README.md -> "First-paint shader jank on
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

        Deliberately swallows everything: this is a best-effort perf
        optimization, not a correctness requirement. If the warm-up tap
        itself times out, that's fine -- the shader compile almost
        certainly still happened on the GPU/raster thread even though our
        client gave up waiting for the ack, so the cache is warm
        regardless of whether we saw a clean response back.
        """
        from appium_flutter_finder import FlutterElement, FlutterFinder

        f = FlutterFinder()
        try:
            self._raw.execute_script(
                "flutter:waitFor", f.by_value_key("onboarding_skip_button"), 15000
            )
            FlutterElement(
                self._raw, f.by_value_key("onboarding_skip_button")
            ).click()
        except Exception:
            # If the click (not just the waitFor) failed, the Appium server's
            # single FlutterDriver command queue may now be wedged behind a
            # tap command the Dart side never acked. Recreating here costs one
            # extra session startup but guarantees a clean queue for the
            # login_register_link step below -- better than letting a wedge
            # from warm-up propagate to the first real test.
            # _is_recovery_create=True prevents the new session from calling
            # _warm_up_shader_cache() again, which would recurse.
            try:
                self._raw.quit()
            except Exception:
                pass
            self._create(_is_recovery_create=True)
            return  # new session is already warm enough; skip the register tap
        try:
            self._raw.execute_script(
                "flutter:waitFor", f.by_value_key("login_register_link"), 15000
            )
            FlutterElement(
                self._raw, f.by_value_key("login_register_link")
            ).click()
        except Exception:
            # Same reasoning as above: a failed tap on login_register_link is
            # the single most common wedge site (confirmed in CI logs -- see
            # file-level docstring). Recreating the session here ensures the
            # wedge is cleared before any real test runs.
            # _is_recovery_create=True prevents recursion.
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
        # specific screen loaded". `_restart_app_between_tests` restarts
        # the app to splash before the first real test regardless, so this
        # warm-up doesn't need to leave the app in any particular screen
        # state.
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
    recommendations, progress, chat, profile, navigation, etc.) depends
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


@pytest.fixture(scope="function")
def on_dashboard(driver, logged_in_session):
    """Function-scoped convenience fixture: guarantees the test starts
    on the dashboard tab regardless of where the previous test in the
    session left the app (bottom nav is always reachable from any of the
    5 shell screens, so a single tap recovers from anywhere)."""
    from page_objects.dashboard_page import DashboardPage

    dashboard = DashboardPage(driver)
    if not dashboard.is_loaded(timeout=3):
        dashboard.nav_to_home()
        assert dashboard.is_loaded(timeout=10)
    return dashboard


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