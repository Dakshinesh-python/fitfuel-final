"""
Shared fixtures and hooks for the FitFuel Selenium suite.

Key rules encoded here (learned from the suite's first real CI run):

1. Screenshot/log filenames are sanitized (re.sub on \\/*?:"<>|) - GitHub
   Actions artifact upload silently drops files with those characters.

2. Reruns are absorbed, not reported. pytest-rerunfailures re-invokes a
   flaky test up to N times; `pytest_runtest_logreport` fires once per
   attempt (status "rerun" for every attempt but the last). We deliberately
   keep only the LAST report per nodeid in `_RESULTS` (a dict keyed by
   nodeid, overwritten on every call) rather than appending every attempt.
   That means:
     - the final reports/execution-results.json always has exactly one row
       per test that ran - 525 rows for the full suite, never inflated by
       retries - and every row's status is a real final PASSED/FAILED/
       SKIPPED, never "RERUN".
     - a test that failed twice and passed on the 3rd attempt is reported
       as PASSED, full stop - which is the correct, honest outcome: the
       test passed. Only its own console log for that specific final
       attempt is what gets kept.

3. Single-process architecture. Earlier iterations of this suite split
   execution across a 4-job GitHub Actions matrix using pytest-split, which
   turned out to be silently broken (each shard ran the full suite instead
   of 1/4 of it) and required a fragile merge step. That's gone: CI now runs
   pytest once, in one job, using `-n auto` (pytest-xdist) purely for
   in-process parallelism across CPU cores - not across separate jobs. This
   file's result-writing logic works identically whether or not xdist is
   active (results are still deduped by nodeid, still exactly one row per
   test), so nothing here needs to change if you ever do reintroduce
   multi-job sharding later.

4. Every real browser console message is captured per test into
   reports/logs/<nodeid>.console.log - useful for debugging CI-only
   failures without ever needing to reproduce locally.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from config import (  # noqa: E402
    BASE_URL,
    LOGS_DIR,
    REPORTS_DIR,
    RESULTS_DIR,
    SCREENSHOTS_DIR,
)
from utils.driver_factory import build_driver  # noqa: E402

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "selenium-tests.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("fitfuel.selenium.conftest")


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption("--base-url", action="store", default=None, help="Override BASE_URL")


def pytest_configure(config):
    override = config.getoption("--base-url")
    if override:
        import config as app_config

        app_config.BASE_URL = override.rstrip("/") + "/"
        logger.info("BASE_URL overridden via CLI to %s", app_config.BASE_URL)
    logger.info("Effective BASE_URL: %s", BASE_URL)


# ---------------------------------------------------------------------------
# Driver fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def driver():
    drv = build_driver()
    yield drv
    try:
        drv.quit()
    except Exception:
        pass


@pytest.fixture
def authenticated_driver(driver):
    """A driver with a valid client-side session already established.

    Uses the two-tier login helper (real UI attempt, falls back to
    localStorage token injection) so authorization/CRUD/form tests don't
    need to duplicate that logic in every module.
    """
    from config import TEST_USER
    from page_objects.base_page import BasePage

    page = BasePage(driver)
    mode = page.login_via_ui_or_inject(TEST_USER["email"], TEST_USER["password"])
    driver.__fitfuel_auth_mode__ = mode  # exposed for tests/logs that care
    return driver


# ---------------------------------------------------------------------------
# Screenshot + console log capture on failure
# ---------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    node_id_safe = sanitize_filename(item.nodeid.replace("::", "__").replace("/", "_"))
    driver = item.funcargs.get("driver") or item.funcargs.get("authenticated_driver")

    # Always dump browser console output for the test's most recent attempt,
    # pass or fail - overwritten on each rerun so only the final attempt's
    # console output survives, matching the final-status-only result policy.
    if driver is not None:
        try:
            log_path = os.path.join(LOGS_DIR, f"{node_id_safe}.console.log")
            with open(log_path, "w", encoding="utf-8") as f:
                try:
                    entries = driver.get_log("browser")
                except Exception:
                    entries = []
                for entry in entries:
                    f.write(f"[{entry.get('level')}] {entry.get('message')}\n")
                if not entries:
                    f.write("(no browser console output captured for this test)\n")
        except Exception as exc:  # never fail a test because logging failed
            logger.warning("Could not write console log for %s: %s", item.nodeid, exc)

    if report.failed and driver is not None:
        try:
            shot_path = os.path.join(SCREENSHOTS_DIR, f"{node_id_safe}.png")
            driver.save_screenshot(shot_path)
            report.screenshot_path = shot_path
            logger.info("Saved failure screenshot: %s", shot_path)
        except Exception as exc:
            logger.warning("Could not capture screenshot for %s: %s", item.nodeid, exc)
    elif report.passed and driver is not None:
        # A previous attempt may have left a stale failure screenshot behind
        # (e.g. attempt 1 failed, attempt 2 - the rerun - passed). Remove it
        # so a test that ultimately passed never leaves a "failure" artifact.
        stale_path = os.path.join(SCREENSHOTS_DIR, f"{node_id_safe}.png")
        if os.path.exists(stale_path):
            try:
                os.remove(stale_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Result capture -> reports/results/result_<id>.json
#
# _RESULTS is keyed by nodeid and OVERWRITTEN on every report for that
# nodeid (including intermediate "rerun" attempts), so by the time a test
# is truly done, only its final outcome remains. This is what guarantees
# the final report always has exactly one row per test - 525 for the full
# suite - never inflated by retries, and never shows a "RERUN" status.
# ---------------------------------------------------------------------------
_RESULTS: dict[str, dict] = {}

MODULE_NAME_OVERRIDES = {
    "test_authentication": "Authentication",
    "test_authorization": "Authorization",
    "test_navigation": "Navigation",
    "test_ui_validation": "UI Validation",
    "test_forms": "Forms",
    "test_crud_operations": "CRUD Operations",
    "test_input_validation": "Input Validation",
    "test_error_handling": "Error Handling",
    "test_session_management": "Session Management",
    "test_downloads_export": "Downloads & Export",
    "test_accessibility": "Accessibility",
    "test_responsive": "Responsive",
}

KNOWN_MARKERS = set(MODULE_NAME_OVERRIDES.keys()) | {
    "authentication", "authorization", "navigation", "ui_validation", "forms",
    "crud", "input_validation", "error_handling", "session", "downloads",
    "accessibility", "responsive", "smoke",
}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    # A rerun attempt reports through the "call" phase with outcome "rerun"
    # (pytest-rerunfailures); a hard setup failure/skip reports through
    # "setup". We want the FINAL attempt only, so: always take "call", and
    # additionally take "setup" only when it didn't pass (e.g. a
    # fixture-level skip that never reaches "call" at all).
    if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
        return

    status = report.outcome  # "passed" | "failed" | "skipped" | "rerun"
    module = report.nodeid.split("::")[0]
    stem = os.path.basename(module).replace(".py", "")
    module_name = MODULE_NAME_OVERRIDES.get(stem, stem.replace("test_", "").replace("_", " ").title())

    markers = sorted(
        m for m in getattr(report, "keywords", {}) if m in KNOWN_MARKERS
    )

    longrepr = None
    if status == "failed" and getattr(report, "longrepr", None):
        try:
            longrepr = str(report.longrepr)[:2000]
        except Exception:
            longrepr = "<unrepresentable longrepr>"

    # A "rerun" report is always followed by a real final report for the
    # same nodeid (that's the whole point of pytest-rerunfailures), so we
    # still record it here - but only ever as the CURRENT value for that
    # nodeid. The instant the real final report arrives, this line
    # overwrites it. Nothing that stays "rerun" forever is possible: pytest
    # always emits a terminal passed/failed/skipped report per test.
    _RESULTS[report.nodeid] = {
        "nodeid": report.nodeid,
        "status": status,
        "duration_s": round(getattr(report, "duration", 0.0), 3),
        "module": module,
        "module_name": module_name,
        "markers": ",".join(markers),
        "longrepr": longrepr,
    }


def _worker_id(session) -> str:
    if hasattr(session.config, "workerinput"):
        return session.config.workerinput.get("workerid", "worker")
    return "master"


def pytest_sessionfinish(session, exitstatus):
    worker_id = _worker_id(session)

    # Drop any entry that somehow still reads "rerun" at session end (should
    # never happen in practice - pytest always emits a terminal report - but
    # guards against ever surfacing a "RERUN" row in the final reports).
    final_results = [r for r in _RESULTS.values() if r["status"] != "rerun"]

    payload = {
        "worker": worker_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "+00:00",
        "base_url": BASE_URL,
        "results": final_results,
    }
    out_path = os.path.join(RESULTS_DIR, f"result_{worker_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info(
        "Worker '%s' wrote %d final result entries (deduped, no reruns) to %s",
        worker_id,
        len(final_results),
        out_path,
    )
