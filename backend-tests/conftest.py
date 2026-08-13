"""
Shared fixtures for the FitFuel backend test suite.

Design notes (see reports/backend-inventory.md for full evidence):
- Talks to a REAL running instance over HTTP (httpx), never imports the
  app in-process. This exercises CORS, helmet, JSON parsing, the auth
  middleware, and real DB round trips end to end.
- fitfuel-final has no auto-seeded demo accounts (unlike the template this
  suite's structure was adapted from), so two fresh users are registered
  through the public API itself at session start and reused everywhere.
  This mirrors the template's "seed two same-role users for cross-tenant
  IDOR tests" requirement without needing DB-level seeding access.
- Every test's docstring is parsed for CATEGORY / TITLE / OBJECTIVE /
  EXPECTED / SEVERITY metadata at collection time. New tests show up in
  test-cases.xlsx automatically -- no separate spreadsheet to hand-maintain.
"""
import json
import logging
import re
import time
import uuid
from pathlib import Path

import httpx
import pytest

from config import BASE_URL, API_PREFIX, TIMEOUT_S, TEST_USER_A, TEST_USER_B

REPORTS_DIR = Path(__file__).parent.parent / "reports"
LOGS_DIR = REPORTS_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOGS_DIR / "backend-tests.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("backend-tests")

DOCSTRING_FIELD_RE = re.compile(
    r"CATEGORY:\s*(?P<category>.+?)\s*\n"
    r"\s*TITLE:\s*(?P<title>.+?)\s*\n"
    r"\s*OBJECTIVE:\s*(?P<objective>.+?)\s*\n"
    r"\s*EXPECTED[^:\n]*:\s*(?P<expected>.+?)\s*\n"
    r"\s*SEVERITY:\s*(?P<severity>.+?)\s*(\n|$)",
    re.DOTALL,
)

# ─── Test run-wide state, populated via pytest hooks below ─────────────────
_collected_results = []  # one dict per test outcome, dumped at session end
_test_start_times = {}


def pytest_addoption(parser):
    parser.addoption(
        "--target-url",
        action="store",
        default=None,
        help="Override BASE_URL for this run (falls back to $BASE_URL / config.py default).",
    )


@pytest.fixture(scope="session")
def base_url(pytestconfig):
    return pytestconfig.getoption("--target-url") or BASE_URL


@pytest.fixture(scope="session")
def api_prefix():
    return API_PREFIX


@pytest.fixture(scope="session")
def client(base_url):
    with httpx.Client(base_url=base_url, timeout=TIMEOUT_S) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def wait_for_backend(base_url):
    """Poll /health before the suite starts so failures are 'app is down',
    not 500 test collection errors from a cold server."""
    deadline = time.time() + 60
    last_err = None
    with httpx.Client(base_url=base_url, timeout=5) as c:
        while time.time() < deadline:
            try:
                r = c.get("/health")
                if r.status_code == 200:
                    log.info("Backend healthy at %s", base_url)
                    return
            except httpx.HTTPError as e:
                last_err = e
            time.sleep(1)
    pytest.exit(f"Backend at {base_url} never became healthy: {last_err}", returncode=2)


def _unique_email(prefix: str, domain: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@{domain}"


def _register(client: httpx.Client, prefix_conf: dict, name_prefix: str) -> dict:
    email = _unique_email(name_prefix, prefix_conf["email_domain"])
    payload = {
        "name": prefix_conf["name"],
        "email": email,
        "password": prefix_conf["password"],
        "age": prefix_conf["age"],
        "gender": prefix_conf["gender"],
        "heightCm": prefix_conf["heightCm"],
        "weightKg": prefix_conf["weightKg"],
    }
    r = client.post(f"{API_PREFIX}/auth/register", json=payload)
    assert r.status_code == 201, f"Fixture setup failed to register {email}: {r.status_code} {r.text}"
    body = r.json()
    return {
        "email": email,
        "password": prefix_conf["password"],
        "token": body["token"],
        "id": body["user"]["id"],
        "headers": {"Authorization": f"Bearer {body['token']}"},
    }


@pytest.fixture(scope="session")
def user_a(client):
    """Primary ephemeral test user (analogous to template's farmer1)."""
    return _register(client, TEST_USER_A, "qa-alpha")


@pytest.fixture(scope="session")
def user_b(client):
    """Secondary ephemeral test user, used for cross-tenant/IDOR checks
    (analogous to template's farmer2 in a different city)."""
    return _register(client, TEST_USER_B, "qa-beta")


@pytest.fixture(scope="session")
def any_meal_id(client):
    """A real, existing meal id from the public catalog (GET /api/meals
    requires no auth). Used wherever a test needs a valid mealId, e.g.
    placing an order."""
    r = client.get(f"{API_PREFIX}/meals")
    assert r.status_code == 200, f"Fixture setup: GET /meals failed: {r.text}"
    meals = r.json()["meals"]
    assert meals, "Fixture setup: meal catalog is empty -- seed data required for order/plan tests"
    return meals[0]["id"]


# Backwards/forwards-compatible alias used by test_authorization.py
@pytest.fixture(scope="session")
def user_b_meal(any_meal_id):
    return any_meal_id


@pytest.fixture(scope="session")
def user_a_with_profile(client, user_a):
    """user_a but with a completed health assessment -- several endpoints
    (recommendations, meal-plan generation) 400 without one."""
    payload = {
        "currentWeightKg": 62,
        "targetWeightKg": 58,
        "activityLevel": "MODERATE",
        "fitnessGoal": "WEIGHT_LOSS",
        "dietaryPreference": "NON_VEGETARIAN",
        "allergies": [],
        "dailyBudget": 500,
    }
    r = client.post(f"{API_PREFIX}/health-profile", json=payload, headers=user_a["headers"])
    assert r.status_code == 201, f"Fixture setup: health-profile failed: {r.text}"
    return user_a


# ─── Docstring metadata parsing + result capture for report generation ────

def _parse_metadata(docstring: str) -> dict:
    if not docstring:
        return {}
    m = DOCSTRING_FIELD_RE.search(docstring)
    if not m:
        return {}
    return {k: v.strip() for k, v in m.groupdict().items() if k != "0"}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
        return

    meta = _parse_metadata(item.function.__doc__ if hasattr(item, "function") else "")
    module_name = item.module.__name__.replace("tests.", "") if hasattr(item, "module") else "unknown"

    entry = {
        "nodeid": item.nodeid,
        "status": report.outcome,  # passed / failed / skipped
        "duration_s": round(report.duration, 4),
        "module": module_name,
        "category": meta.get("category", module_name),
        "title": meta.get("title", item.name),
        "objective": meta.get("objective", ""),
        "expected": meta.get("expected", ""),
        "severity": meta.get("severity", "LOW"),
        "longrepr": str(report.longrepr) if report.failed else None,
    }
    _collected_results.append(entry)
    log.info("%s %s (%.3fs)", entry["status"].upper(), entry["nodeid"], entry["duration_s"])


def pytest_sessionfinish(session, exitstatus):
    # xdist/workers guard, mirroring the template's master-node-only rule
    if hasattr(session.config, "workerinput"):
        return

    # Guard against --collect-only (or any run that collects but executes
    # nothing) silently overwriting a previous real run's results with an
    # empty summary.
    if session.config.getoption("--collect-only", default=False):
        return
    if not _collected_results:
        return

    total = len(_collected_results)
    passed = sum(1 for r in _collected_results if r["status"] == "passed")
    failed = sum(1 for r in _collected_results if r["status"] == "failed")
    skipped = sum(1 for r in _collected_results if r["status"] == "skipped")
    pass_rate = round((passed / total) * 100, 2) if total else 0.0

    output = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "base_url": BASE_URL,
        "api_prefix": API_PREFIX,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": pass_rate,
        },
        "results": _collected_results,
    }
    out_path = REPORTS_DIR / "execution-results.json"
    out_path.write_text(json.dumps(output, indent=2))
    log.info("Wrote %s (%d total, %.2f%% pass rate)", out_path, total, pass_rate)
