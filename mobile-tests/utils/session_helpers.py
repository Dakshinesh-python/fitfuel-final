"""
High-level "get the app into a known state" helpers, layered on top of
the page objects. Kept separate from conftest.py so individual test
modules can also call these directly for multi-step setup without
re-deriving the flow.
"""
from page_objects.auth_pages import LoginPage, RegisterPage
from page_objects.dashboard_page import DashboardPage
from page_objects.health_assessment_pages import (
    HealthActivityPage,
    HealthGoalsPage,
    HealthPrefsPage,
    HealthWeightPage,
    PlanReadyPage,
)
from page_objects.onboarding_page import OnboardingPage
from utils import adb_helpers


def register_new_account(driver, account: dict) -> None:
    """Drives: (fresh app state) -> onboarding -> register -> full health
    assessment happy path -> plan-ready -> dashboard. Leaves the app on
    the dashboard, logged in as `account`.

    Handles the case where the app is already on the dashboard (e.g.
    after a session recreate with noReset:False preserving the auth
    token in SharedPreferences) by returning early -- the account
    already exists and the driver is already in the correct state."""
    from page_objects.dashboard_page import DashboardPage

    # If already logged in and on the dashboard, nothing to do.
    if DashboardPage(driver).is_loaded(timeout=5):
        return

    onboarding = OnboardingPage(driver)
    if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=5):
        onboarding.skip()

    # Onboarding's Skip button navigates to /login, not /register (see
    # onboarding_screen.dart's _finish()) -- confirmed against the app
    # source and matching the test class name "TestOnboardingReachesLogin"
    # in test_01_authentication.py. This function previously asserted
    # landing directly on Register after Skip, which was simply wrong
    # about the app's actual navigation and failed on the very first line
    # for almost every test in the suite, since nearly all modules besides
    # test_02_registration.py go through this fixture. Register is reached
    # via the "go to register" link on the Login screen instead.
    login = LoginPage(driver)
    assert login.is_loaded(timeout=10), "Expected to land on the login screen after onboarding"
    login.go_to_register()

    register = RegisterPage(driver)
    assert register.is_loaded(), "Expected to land on the register screen after onboarding"
    register.fill_form(
        name=account["name"],
        email=account["email"],
        password=account["password"],
        age=account["age"],
        height_cm=account["height_cm"],
        weight_kg=account["weight_kg"],
        gender=account.get("gender", "female"),
    )
    register.submit()

    weight = HealthWeightPage(driver)
    assert weight.is_loaded(timeout=15), "Expected health-weight screen after registration"
    weight.set_current_weight(account["weight_kg"])
    weight.set_target_weight(str(float(account["weight_kg"]) - 3))
    weight.continue_()

    activity = HealthActivityPage(driver)
    assert activity.is_loaded()
    activity.select("MODERATE")
    activity.continue_()

    goals = HealthGoalsPage(driver)
    assert goals.is_loaded()
    goals.select("WEIGHT_LOSS")
    goals.continue_()

    prefs = HealthPrefsPage(driver)
    assert prefs.is_loaded()
    prefs.select_diet("NON_VEGETARIAN")
    prefs.set_budget("300")
    prefs.submit()

    plan_ready = PlanReadyPage(driver)
    assert plan_ready.is_loaded(timeout=20), "Plan generation took too long or failed"
    plan_ready.continue_to_dashboard()

    dashboard = DashboardPage(driver)
    assert dashboard.is_loaded(timeout=15)


def logout(driver) -> None:
    profile_nav = DashboardPage(driver)  # NavBarMixin is on every shell screen
    profile_nav.nav_to_profile()
    from page_objects.profile_page import ProfilePage

    profile = ProfilePage(driver)
    assert profile.is_loaded()
    profile.logout()

    login = LoginPage(driver)
    assert login.is_loaded(), "Expected redirect to login screen after logout"


def login(driver, email: str, password: str) -> None:
    login_page = LoginPage(driver)
    assert login_page.is_loaded(), "login() called but app is not on the login screen"
    login_page.login(email, password)


def force_logged_out_state(driver) -> None:
    """Used by tests that need a guaranteed clean slate (e.g. session
    tests) rather than a `logout()` UI flow that assumes the app is
    already reachable and authenticated."""
    adb_helpers.clear_app_data()
    adb_helpers.force_stop_app()
    import subprocess

    subprocess.run(
        [
            "adb",
            "shell",
            "monkey",
            "-p",
            __import__("config").APP_PACKAGE,
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        ],
        capture_output=True,
        timeout=15,
    )
