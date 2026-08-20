"""
Central configuration for the FitFuel Android (Appium/Flutter) test suite.

Everything here is overridable via environment variable so the same test
code runs unmodified on a developer's laptop and in CI. Nothing here is a
secret — test accounts are generated fresh per run (see conftest.py), not
hardcoded, because (unlike the reference KrishiIQ project) fitfuel-final's
backend does NOT auto-seed demo accounts. See mobile-tests/README.md
-> "Why there are no seeded test accounts" for the full explanation.
"""
import os

# ─────────────────────────────────────────────────────────────────────────
# Appium server
# ─────────────────────────────────────────────────────────────────────────
APPIUM_SERVER_URL = os.environ.get("APPIUM_SERVER_URL", "http://127.0.0.1:4723")

# Tuned from observed CI behaviour on this project (see README "Timeout
# tuning" section): every healthy Flutter-driver command on this app
# completes well under 5s once the Observatory handshake is warm. 30s
# was increased from 12 because the CI emulator's first-paint shader
# compile for RegisterScreen's BoxShadow widgets (login_register_link tap)
# consistently exceeded 12s under load, causing ReadTimeoutError and
# wedging the Appium server's single serial command queue for the rest of
# the shard. 30s gives real headroom while still failing fast on a
# genuinely wedged session instead of hanging for the default 45s.
APPIUM_COMMAND_TIMEOUT = int(os.environ.get("APPIUM_COMMAND_TIMEOUT", "30"))
SESSION_CREATION_TIMEOUT = int(os.environ.get("SESSION_CREATION_TIMEOUT", "60"))

# ─────────────────────────────────────────────────────────────────────────
# App under test
# ─────────────────────────────────────────────────────────────────────────
APP_PACKAGE = os.environ.get("APP_PACKAGE", "com.example.fitfuel_mobile")
APP_ACTIVITY = os.environ.get("APP_ACTIVITY", ".MainActivity")

# Absolute path to the flutter-driver-enabled debug APK, built with:
#   flutter build apk --debug -t lib/main_test.dart
# Resolved to an absolute path in conftest.py per lesson #4 (Appium
# resolves `appium:app` relative to ITS OWN working directory, not the
# pytest client's).
APK_PATH = os.environ.get(
    "APK_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "fitfuel_mobile",
        "build",
        "app",
        "outputs",
        "flutter-apk",
        "app-debug.apk",
    ),
)

# Leave PLATFORM_VERSION empty to let Appium auto-detect the connected emulator's
# Android version. Hardcoding a version works locally but fails in CI where the
# API level differs, producing "Unable to find an active device or emulator with
# OS XX" errors. Auto-detection removes this mismatch entirely.
PLATFORM_VERSION = os.environ.get("PLATFORM_VERSION", "")
DEVICE_NAME = os.environ.get("DEVICE_NAME", "Android Emulator")
AVD_NAME = os.environ.get("AVD_NAME", "test")

# ─────────────────────────────────────────────────────────────────────────
# Backend under test (reached from inside the emulator via the special
# 10.0.2.2 alias for the host loopback interface)
# ─────────────────────────────────────────────────────────────────────────
# NOTE: fitfuel_mobile/lib/services/api_config.dart hardcodes
# https://fitfuel-final.onrender.com as the compiled-in baseUrl, and only
# reads a different URL if the APK is built with
#   --dart-define=API_BASE_URL=http://10.0.2.2:4000
# This suite assumes CI builds the test APK against a disposable local
# backend (see .github/workflows/android-e2e.yml), matching the pattern
# backend-tests.yml already uses (real Postgres service container, not
# a mocked API). Running locally against the deployed Render backend also
# works but is slower and shares data with anyone else hitting it.
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://10.0.2.2:4000")

# ─────────────────────────────────────────────────────────────────────────
# Reporting / execution
# ─────────────────────────────────────────────────────────────────────────
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
LOGS_DIR = os.path.join(REPORTS_DIR, "logs")

# Failure-screenshot capture is off by default: on a run with lots of
# failures these are the single biggest contributor to the uploaded
# reports artifact (hundreds of full-res PNGs), while logcat (still
# captured regardless of this flag) covers most of the same debugging
# need at a fraction of the size. Set CAPTURE_SCREENSHOTS=1 to re-enable.
CAPTURE_SCREENSHOTS = os.environ.get("CAPTURE_SCREENSHOTS", "0") == "1"

# Same gate style as selenium-tests/config.py (pick ONE number, use it
# consistently in the CI job summary AND the actual exit-code check —
# final_year.md flags this exact 90-vs-95 drift in the reference repo).
GATE_THRESHOLD_PCT = float(os.environ.get("GATE_THRESHOLD_PCT", "90"))

# Implicit wait used by page_objects for "wait until visible" polling.
DEFAULT_WAIT_SECONDS = float(os.environ.get("DEFAULT_WAIT_SECONDS", "10"))