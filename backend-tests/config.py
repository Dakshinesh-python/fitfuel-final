"""
Central configuration for the FitFuel backend test suite.

Every value here was confirmed against the actual fitfuel-final repo
(https://github.com/Dakshinesh-python/fitfuel-final), not assumed from a
template. See ../reports/backend-inventory.md for the full evidence trail
(file paths + line references) behind each of these.
"""
import os

# ─── Target ─────────────────────────────────────────────────────────────────
# Confirmed: backend/src/server.ts -> const PORT = process.env.PORT ?? 4000
# Confirmed: docs/TESTING_GUIDE.md -> "Runs on http://localhost:4000"
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4000")

# Confirmed: backend/src/app.ts -> app.use("/api/auth", ...) etc.
# NOTE [CORRECTION vs template]: this repo mounts routes at /api/<resource>,
# there is NO /api/v1 prefix (unlike the KrishiIQ template this project list
# was adapted from).
API_PREFIX = os.environ.get("API_PREFIX", "/api")

TIMEOUT_S = float(os.environ.get("REQUEST_TIMEOUT_S", "15"))

# ─── Auth ───────────────────────────────────────────────────────────────────
# Confirmed: backend/src/middleware/auth.ts
#   header.startsWith("Bearer ") -> jwt.verify(token, secret)
#   secret = process.env.JWT_SECRET ?? "dev-secret-change-me"
AUTH_HEADER_SCHEME = "Bearer"
DEFAULT_JWT_SECRET_FALLBACK = "dev-secret-change-me"  # hardcoded in source; used by test_dast.py

# ─── Seed accounts ──────────────────────────────────────────────────────────
# [CORRECTION vs template]: unlike KrishiIQ's `_auto_seed()`, this repo does
# NOT auto-seed demo user accounts on startup. prisma/seed.ts only seeds the
# Meal catalog. There are no fixed demo credentials to reference across
# tracks. This suite therefore creates its own ephemeral users at session
# start via POST /api/auth/register (see conftest.py) instead of relying on
# pre-seeded accounts. Two users (A and B) are created so authorization
# tests can check cross-tenant access the same way the template's
# farmer1/farmer2 pair did.
TEST_USER_A = {
    "name": "QA Tester Alpha",
    "email_domain": "backendtests.local",
    "password": "TestPass123!",
    "age": 27,
    "gender": "FEMALE",
    "heightCm": 165,
    "weightKg": 62,
}
TEST_USER_B = {
    "name": "QA Tester Beta",
    "email_domain": "backendtests.local",
    "password": "TestPass456!",
    "age": 31,
    "gender": "MALE",
    "heightCm": 178,
    "weightKg": 80,
}

# ─── Endpoint inventory (confirmed from backend/src/routes/*.ts) ───────────
# method, path, requires_auth, description
ENDPOINTS = [
    ("GET",   "/health",                       False, "Liveness/health check"),
    ("POST",  "/api/auth/register",             False, "Create account"),
    ("POST",  "/api/auth/login",                False, "Obtain JWT"),
    ("GET",   "/api/auth/me",                   True,  "Current user profile"),
    ("PATCH", "/api/auth/profile",              True,  "Update display name"),
    ("PATCH", "/api/auth/password",             True,  "Change password"),
    ("POST",  "/api/health-profile",            True,  "Submit health assessment (BMI/BMR/TDEE)"),
    ("GET",   "/api/health-profile",             True,  "Get current health profile"),
    ("GET",   "/api/meals",                     False, "List/filter meal catalog"),
    ("GET",   "/api/meals/:id",                 False, "Get single meal"),
    ("GET",   "/api/recommendations",           True,  "Ranked meal recommendations"),
    ("POST",  "/api/meal-plans/generate",       True,  "Generate 7-day meal plan"),
    ("GET",   "/api/meal-plans/current",        True,  "Get latest meal plan"),
    ("POST",  "/api/orders",                    True,  "Log an order / get deep link"),
    ("GET",   "/api/orders",                    True,  "List own orders"),
    ("POST",  "/api/progress",                  True,  "Log a progress entry"),
    ("GET",   "/api/progress/summary",          True,  "Weekly nutrition summary"),
    ("GET",   "/api/progress/weight-history",   True,  "Weight history (90d)"),
    ("GET",   "/api/progress",                  True,  "List progress logs"),
]
