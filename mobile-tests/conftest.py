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
from appium.options.android import UiAutomator2Options

import config
from utils import adb_helpers
from utils.appium_connection import (
    build_session_creation_executor,
    configure_default_timeout,
    swap_to_short_timeout,
)

# Must happen before any AppiumConnection/session is created.
configure_default_timeout()

os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(config.LOGS_DIR, exist_ok=True)

_RESULTS: list[dict] = []
_RUN_STARTED_AT = datetime.now(timezone.utc)


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

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "Flutter"
    options.device_name = config.DEVICE_NAME
    options.app = apk_path
    options.app_package = config.APP_PACKAGE
    options.app_activity = config.APP_ACTIVITY
    options.new_command_timeout = 300
    options.set_capability("appium:autoGrantPermissions", True)
    options.set_capability("appium:noReset", False)
    options.set_capability("appium:platformVersion", config.PLATFORM_VERSION)

    creation_executor = build_session_creation_executor(config.APPIUM_SERVER_URL)
    drv = webdriver.Remote(
        command_executor=creation_executor,
        options=options,
    )
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


def _capture_failure_artifacts(item) -> None:
    safe_name = item.nodeid.replace("::", "__").replace("/", "_")
    driver_fixture = item.funcargs.get("driver")
    if driver_fixture is not None:
        try:
            screenshot_path = os.path.join(config.SCREENSHOTS_DIR, f"{safe_name}.png")
            driver_fixture.get_screenshot_as_file(screenshot_path)
        except Exception:
            pass
    try:
        log_path = os.path.join(config.LOGS_DIR, f"{safe_name}.log")
        adb_helpers.pull_logcat(log_path)
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
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

    payload = {
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
            "by_module": by_module,
        },
        "results": _RESULTS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    out_path = os.path.join(config.REPORTS_DIR, "execution-results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
