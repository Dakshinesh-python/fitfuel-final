"""
Central configuration for the FitFuel Selenium suite.

CORRECTION - ROUTER TYPE (read this before touching route_url/BASE_URL):
----------------------------------------------------------------
An earlier version of this suite incorrectly assumed the app used
react-router-dom's BrowserRouter. It actually uses HashRouter
(web/src/main.tsx: `<HashRouter><App /></HashRouter>`), which was only
discovered after CI runs showed nearly every test failing/timing out with
no clear cause. Every real route lives after a '#/' fragment - e.g. the
dashboard is at BASE_URL + '#/dashboard', never BASE_URL + 'dashboard'.
route_url() builds hash-based URLs accordingly; don't hand-build a route URL
elsewhere without going through it.

One consequence worth knowing: because HashRouter never sends the fragment
to the server, GitHub Pages' lack of a 404.html SPA-fallback trick was
actually never a problem for this app - the server only ever needs to serve
the same index.html at the bare BASE_URL, and 100% of routing happens
client-side off the hash. That's different from what an earlier version of
this file claimed.

CI ARCHITECTURE DECISION (unaffected by the above, still applies):
----------------------------------------------------------------
This suite builds the app in CI and serves it with `vite preview` on
http://localhost:4173/fitfuel-final/ and runs the whole suite against that,
rather than the live GitHub Pages deployment, so it never depends on the
live Render backend or the live deployment being up to date: the production
API base URL is intentionally pointed at a dead local address at build time
(VITE_API_BASE_URL is left unset - see web/src/api/client.ts's own
localhost:4000 fallback) so every real network call fails fast and
deterministically, and the suite's two-tier auth fixture (see conftest.py)
falls back to localStorage token injection. This keeps the pipeline green on
every push without ever writing test accounts into the real production
database. A `base_url` workflow_dispatch input lets you point the same
suite at the real deployed GitHub Pages site + live backend when you want an
end-to-end smoke run against production.
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
# Routes (values are bare path segments - route_url() adds the HashRouter
# '#/' prefix; don't add a leading '/' or '#' here)
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
    """Build a full URL for a named route against BASE_URL.

    The app uses react-router-dom's HashRouter (web/src/main.tsx), NOT
    BrowserRouter - every real route lives after a '#/' fragment, e.g. the
    dashboard is reachable at BASE_URL + '#/dashboard', never
    BASE_URL + 'dashboard'. Getting this wrong (which an earlier version of
    this suite did) means every direct navigation actually loads the app at
    an empty/root hash, which the app then client-side-redirects away from
    - producing URLs like '.../chat#/login' and making nearly every test
    that navigates directly to a route fail, regardless of chromedriver,
    timeouts, or anything else.
    """
    path = ROUTES.get(name, name)
    return BASE_URL + "#/" + path


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
