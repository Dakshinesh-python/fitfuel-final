"""
Shared fixtures and hooks for the FitFuel Selenium suite.

Key learned-the-hard-way rules encoded here (see the testing prompt this
suite was built from):
1. Screenshot filenames are sanitized (re.sub on \\/*?:"<>|) - GitHub Actions
   artifact upload silently drops files with those characters.
2. The execution-results.json summary is written from a pytest_sessionfinish
   hook that only runs on the xdist MASTER node (guarded via
   `hasattr(session.config, "workerinput")`), so parallel workers never race
   on the same output file. Excel/HTML/dashboard generation is a separate
   `generate_reports.py` CI step that runs AFTER pytest, reading the raw
   pytest-json-report output plus the per-worker files this hook merges.
3. Every real browser console message is captured per test into
   reports/logs/<nodeid>.console.log - useful for debugging CI-only failures
   without ever needing to reproduce locally.
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

    # Always dump browser console output for the test, pass or fail - this is
    # what "full logging" means in practice, not just failures.
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


# ---------------------------------------------------------------------------
# Per-process result capture -> reports/results/result_<worker-or-master>.json
#
# Each pytest process (an xdist worker, OR the single process in a non-xdist
# run) writes ONLY its own results, exactly once, to its own file. Nothing
# is ever double-counted because no process ever reads or re-writes another
# process's file - that merge happens later, once, in generate_reports.py.
# ---------------------------------------------------------------------------
_RESULTS: list[dict] = []

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
    # "setup". We want exactly one entry per real attempt, so: always take
    # "call", and additionally take "setup" only when it didn't pass (e.g.
    # a fixture-level skip that never reaches "call" at all).
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

    _RESULTS.append(
        {
            "nodeid": report.nodeid,
            "status": status,
            "duration_s": round(getattr(report, "duration", 0.0), 3),
            "module": module,
            "module_name": module_name,
            "markers": ",".join(markers),
            "longrepr": longrepr,
        }
    )


def _worker_id(session) -> str:
    shard = os.environ.get("MATRIX_SHARD", "single")
    if hasattr(session.config, "workerinput"):
        xdist_id = session.config.workerinput.get("workerid", "worker")
        return f"shard{shard}-{xdist_id}"
    return f"shard{shard}-master"


def pytest_sessionfinish(session, exitstatus):
    worker_id = _worker_id(session)
    payload = {
        "worker": worker_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "+00:00",
        "base_url": BASE_URL,
        "results": _RESULTS,
    }
    out_path = os.path.join(RESULTS_DIR, f"result_{worker_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info(
        "Worker '%s' wrote %d result entries to %s", worker_id, len(_RESULTS), out_path
    )
