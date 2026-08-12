"""
Central configuration for the FitFuel Selenium suite.

CI ARCHITECTURE DECISION (read this before changing BASE_URL):
----------------------------------------------------------------
FitFuel web is a Vite + React SPA using react-router-dom's BrowserRouter
(NOT HashRouter) and it is deployed to GitHub Pages with base "/fitfuel-final/".
GitHub Pages serves static files with no server-side rewrite, and this repo's
web-deploy.yml does not publish a 404.html SPA-fallback trick. That means a
direct hit on a deep link such as https://<user>.github.io/fitfuel-final/dashboard
returns a real GitHub Pages 404 - it never reaches React Router at all.

`vite preview` DOES serve an SPA fallback (any unknown path returns index.html),
so this suite builds the app in CI and serves it with `vite preview` on
http://localhost:4173/fitfuel-final/ and runs the whole suite against that.
This is also why the suite never depends on the live Render backend: the
production API base URL is intentionally pointed at a dead local address at
build time (see web-ci workflow) so every real network call fails fast and
deterministically, and the suite's two-tier auth fixture (see conftest.py)
falls back to localStorage token injection. This keeps the pipeline green on
every push without ever writing test accounts into the real production
database. A `base_url` / `api_base_url` workflow_dispatch input lets you point
the same suite at the real deployed GitHub Pages site + live backend when you
want an end-to-end smoke run against production.
"""

import os

# ---------------------------------------------------------------------------
# Base URL / environment
# ---------------------------------------------------------------------------
_env_base_url = os.environ.get("BASE_URL", "").strip()
BASE_URL = (_env_base_url or "http://localhost:4173/fitfuel-final/").rstrip("/") + "/"
HEADLESS = os.environ.get("HEADLESS", "true").lower() != "false"
IMPLICIT_WAIT = 0  # we use explicit waits everywhere; never mix with implicit waits
DEFAULT_TIMEOUT = int(os.environ.get("SELENIUM_TIMEOUT", "12"))
SHORT_TIMEOUT = 4
LONG_TIMEOUT = 20

# How long the two-tier login helper waits for a REAL backend redirect
# before falling back to token injection (see base_page.py). This is
# separate from LONG_TIMEOUT and deliberately short by default: in the
# default CI configuration the backend is unreachable ON PURPOSE (see
# module docstring above), so this wait is pure dead time paid by every
# single test that uses the `authenticated_driver` fixture - roughly 300+
# of the suite's 525 tests. At the old 20s default that was ~25 minutes of
# wall-clock time wasted waiting for a redirect that can never happen,
# tripled again for any test that got rerun. 5s is generous enough to catch
# a real redirect if it happens fast, while cutting that tax by 4x.
#
# If you run this suite with `base_url`/a real reachable backend (e.g. a
# workflow_dispatch production smoke run) and want the real-login path to
# get a fair, longer chance to actually succeed (e.g. Render free-tier cold
# starts can take 20-30s), override this via the AUTH_UI_TIMEOUT env var.
AUTH_UI_TIMEOUT = int(os.environ.get("AUTH_UI_TIMEOUT", "5"))

# ---------------------------------------------------------------------------
# Routes (BrowserRouter - no leading '#')
# ---------------------------------------------------------------------------
ROUTES = {
    "root": "",
    "login": "login",
    "register": "register",
    "health-assessment": "health-assessment",
    "dashboard": "dashboard",
    "recommendations": "recommendations",
    "progress": "progress",
    "meal-plan": "meal-plan",
    "chat": "chat",
    "profile": "profile",
}

PROTECTED_ROUTES = [
    "health-assessment",
    "dashboard",
    "recommendations",
    "progress",
    "meal-plan",
    "chat",
    "profile",
]

PUBLIC_ROUTES = ["login", "register"]

NAV_ROUTES = [
    "dashboard",
    "recommendations",
    "meal-plan",
    "progress",
    "chat",
    "profile",
]

NAV_LABELS = {
    "dashboard": "Dashboard",
    "recommendations": "Recommendations",
    "meal-plan": "Meal Plan",
    "progress": "Progress",
    "chat": "Chat",
    "profile": "Profile",
}


def route_url(name: str) -> str:
    """Build a full URL for a named route against BASE_URL."""
    path = ROUTES.get(name, name)
    return BASE_URL + path


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
TOKEN_STORAGE_KEY = "fitfuel_token"

# A syntactically-valid-looking but entirely fake JWT. RequireAuth in App.tsx
# only checks `if (!token)`, it never verifies the signature client-side, so
# this is sufficient to exercise every client-side route guard without ever
# touching a real account. It is NOT a working credential against any backend.
FAKE_JWT_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJzZWxlbml1bS10ZXN0LXVzZXIiLCJyb2xlIjoidXNlciIsImlhdCI6MTcwMDAwMDAwMH0."
    "selenium-suite-fake-signature-do-not-trust"
)

# Unique-per-run credentials used for the (best-effort) real registration /
# login flow. Backend calls are expected to fail in the default ephemeral CI
# configuration (see module docstring) - these exist so the suite still
# demonstrates and logs the real-UI attempt before falling back.
import time as _time  # noqa: E402

_RUN_ID = os.environ.get("GITHUB_RUN_ID", str(int(_time.time())))
TEST_USER = {
    "name": "Selenium QA",
    "email": f"selenium.qa.{_RUN_ID}@example.com",
    "password": "SeleniumTest123!",
    "age": "29",
    "gender": "MALE",
    "height": "175",
    "weight": "72",
}

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
LOGS_DIR = os.path.join(REPORTS_DIR, "logs")
RESULTS_DIR = os.path.join(REPORTS_DIR, "results")
PASS_RATE_GATE = float(os.environ.get("PASS_RATE_GATE", "90"))
