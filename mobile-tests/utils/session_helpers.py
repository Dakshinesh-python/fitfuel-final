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
    if DashboardPage(driver).is_loaded(timeout=8):
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
    if not login.is_loaded(timeout=10):
        # Neither dashboard, onboarding, nor login -- e.g. logged in but
        # on a different shell tab than Dashboard (the dashboard-marker
        # check above only matches the Dashboard tab specifically, not
        # "authenticated"), or some other ambiguous leftover state from
        # a prior test/session-recreate. This was the single largest
        # cluster of CI failures after the off-screen-tap and
        # on_dashboard fixes (15 failures cascading through every module
        # that depends on this shared helper). force-clear local storage
        # to guarantee a known onboarding/login entry point rather than
        # asserting failure on an unrecognized screen.
        from utils import adb_helpers
        import config

        adb_helpers.clear_app_data()
        driver.activate_app(config.APP_PACKAGE)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=15):
            onboarding.skip()
        assert login.is_loaded(timeout=15), (
            "Expected to land on the login screen after onboarding, even after "
            "force-clearing app data"
        )
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
    if not weight.is_loaded(timeout=15):
        # Give the real backend registration call more room before giving
        # up -- confirmed in CI logs that this consistently fails only as
        # the *first* network call of a shard (logged_in_session is
        # session-scoped, so this is its one-time registration), never on
        # later registrations in the same shard. That's consistent with a
        # cold Dio HTTP client / cold backend connection pool needing more
        # than 15s rather than a genuine rejection, but check for an
        # explicit validation/backend error too so a real failure doesn't
        # just look like a timeout if this retry also fails.
        error = register.has_error(timeout=1)
        assert weight.is_loaded(timeout=20), (
            f"Expected health-weight screen after registration"
            + (f" (register screen showed error: {register.error_message()})" if error else "")
        )
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
    already reachable and authenticated. Leaves the app on the Login
    screen -- callers previously had to skip onboarding themselves after
    calling this (two call sites in CI didn't, and both failed
    consistently: adb_helpers.clear_app_data() wipes local storage
    entirely, so a fresh launch always shows onboarding first, never
    login directly, the same as any other first-ever launch).

    Relaunches via `driver.activate_app()`, not a raw `adb shell monkey`
    launch (confirmed against CI logs as the actual bug behind this
    function: the immediately-preceding `force_stop_app()` kills the
    Dart process the Appium session's FlutterDriver socket is connected
    to, and only `activate_app()` -- which internally reconnects
    FlutterDriver to the new process's Observatory port -- brings that
    connection back. A raw adb-launched process leaves the *app*
    running but the *driver* still bound to the dead old connection, so
    every following flutter:* command fails immediately; that's why
    callers saw ~1s failures immediately after this function ran rather
    than a real timeout)."""
    adb_helpers.clear_app_data()
    adb_helpers.force_stop_app()
    driver.activate_app(__import__("config").APP_PACKAGE)
    onboarding = OnboardingPage(driver)
    if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=15):
        onboarding.skip()
