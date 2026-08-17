"""
Session-scoped Appium driver + pytest reporting hooks for the FitFuel
Android suite.

Session strategy (deliberately different from a naive "launch the app
fresh for every test" approach, which is far too slow for 400+ Appium
tests): ONE Appium session is created for the whole pytest run. Test
modules that need a logged-out state (test_01_authentication.py,
test_02_registration.py) run FIRST (enforced by the `01_`/`02_` file name
prefixes, since pytest collects alphabetically within a directory by
default) and are responsible for putting the app back into a known
logged-in state before finishing, via the `logged_in_session` fixture.
Every other module assumes it starts logged in.

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
# Driver session (module-scoped isn't enough -- Appium/flutter-driver
# session creation costs ~20-40s each time because it reinstalls the APK.
# We create exactly one session per pytest run and reuse it everywhere.)
# ─────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def driver():
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
    options.set_capability("appium:platformVersion", config.PLATFORM_VERSION)
    # Gives Appium's own session-creation-time wait for the Flutter Driver
    # extension to become responsive more headroom (was previously unset,
    # falling back to appium-flutter-driver's default, which is tighter
    # than this emulator's actual cold-start latency needs).
    options.set_capability("appium:flutterServerLaunchTimeout", 45000)

    creation_executor = build_session_creation_executor(config.APPIUM_SERVER_URL)
    drv = webdriver.Remote(
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
    swap_to_short_timeout(drv, config.APPIUM_SERVER_URL)

    yield drv

    try:
        drv.quit()
    except Exception:
        pass


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
    """One registered + fully onboarded account, created once per run and
    reused (via re-login, not re-registration) by every module that just
    needs *a* logged-in user rather than testing registration itself."""
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
    test_02_registration.py."""
    from page_objects.dashboard_page import DashboardPage
    from utils import session_helpers

    dashboard = DashboardPage(driver)
    if not dashboard.is_loaded(timeout=4):
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