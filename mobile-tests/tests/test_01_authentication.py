"""
Authentication: login happy path, invalid-credential paths, password
visibility toggle, register-link navigation, logout, and the redirect
that should occur when a protected screen is reached without a session.

Runs BEFORE test_02_registration.py (enforced by filename ordering --
see conftest.py's session-strategy docstring) so the app starts in
whatever state the emulator boots into (fresh install -> onboarding).
"""
import pytest

import config
from page_objects.auth_pages import LoginPage, RegisterPage
from page_objects.dashboard_page import DashboardPage
from page_objects.onboarding_page import OnboardingPage
from utils import adb_helpers, session_helpers


def _ensure_on_login_screen(driver) -> None:
    """Navigate to the login screen from any app state.

    `_restart_app_between_tests` relaunches the app before every test,
    but with noReset:False the auth token in SharedPreferences survives
    the relaunch -- so the app comes back on the dashboard, not on
    onboarding or login. Tests that need to start from the login screen
    must explicitly get there.

    Strategy:
      * Already on login  → nothing to do.
      * On dashboard      → tap the profile nav and use the logout button
                            (fastest path, no data wipe).
      * On onboarding     → skip (navigates to login).
      * Unknown/mid-flow  → clear app data + relaunch (guaranteed fallback).
    """
    login = LoginPage(driver)
    if login.is_loaded(timeout=4):
        return
    dashboard = DashboardPage(driver)
    if dashboard.is_loaded(timeout=4):
        session_helpers.logout(driver)
        return
    onboarding = OnboardingPage(driver)
    if onboarding.is_loaded(timeout=4):
        onboarding.skip()
        assert login.is_loaded(timeout=10)
        return
    # Unknown state — force a clean launch.
    adb_helpers.clear_app_data()
    driver.activate_app(config.APP_PACKAGE)
    onboarding2 = OnboardingPage(driver)
    if onboarding2.is_loaded(timeout=10):
        onboarding2.skip()
    assert login.is_loaded(timeout=10)


@pytest.fixture(scope="module")
def registered_account(driver, logged_in_session):
    """Ensures `primary_test_account` exists in the backend before any
    login test in this module runs, without depending on
    test_02_registration.py's execution order (registration is a
    separate, independently-tested concern).

    Depends on the shared, session-scoped `logged_in_session` fixture
    rather than re-implementing its own "is this already registered"
    check -- this fixture previously used `dashboard.is_loaded(timeout=4)`
    to decide whether to call register_new_account(), which is both too
    narrow (authenticated but on some other screen right after an
    app-relaunch reads as "not registered yet") and redundant with
    logged_in_session's own, more robust registration-or-reuse logic.
    When some other module in the same shard used logged_in_session
    first (registering primary_test_account), this fixture's own check
    could still miss it and call register_new_account() a second time
    with the same email -- confirmed in CI as a real "Email already
    registered" backend rejection, not a flake, cascading through every
    test in this module since the fixture is module-scoped.

    Calls conftest.ensure_on_dashboard() (not the on_dashboard fixture
    itself) before logout() -- logged_in_session's own contract is "the
    app is on the dashboard", but the autouse per-test app-relaunch
    fixture still runs after it for this test, and logout() itself just
    taps the profile nav tab with no check that it has actually
    rendered yet. A previous fix declared `on_dashboard` as an explicit
    dependency here to get that same self-healing wait, but on_dashboard
    is function-scoped while this fixture is module-scoped -- pytest
    raises ScopeMismatch for a wider-scoped fixture depending on a
    narrower-scoped one, erroring out every test in this module before
    any of them ran. This fixture only ever needed on_dashboard's
    recovery logic to make logout() reliable, not the fixture injection
    itself, so it calls the plain function version directly."""
    from conftest import ensure_on_dashboard

    ensure_on_dashboard(driver, logged_in_session)
    session_helpers.logout(driver)
    return logged_in_session


class TestOnboardingReachesLogin:
    @pytest.fixture(autouse=True)
    def _force_fresh_launch(self, driver):
        """These tests specifically verify cold-launch behaviour (onboarding
        appearing on first run, skip navigating to login, etc.). They must
        start from a genuinely fresh app state -- clearing local storage is
        the only reliable way to guarantee onboarding appears rather than
        the dashboard (which the app restarts to when noReset:False preserves
        an auth token from a previous test in the same shard)."""
        adb_helpers.clear_app_data()
        driver.activate_app(config.APP_PACKAGE)

    @pytest.mark.smoke
    def test_app_launches_to_onboarding_or_login(self, driver):
        onboarding = OnboardingPage(driver)
        login = LoginPage(driver)
        landed = onboarding.is_loaded(timeout=15) or login.is_loaded(timeout=5)
        assert landed, "App did not land on onboarding or login on cold launch"

    def test_skip_onboarding_reaches_register(self, driver):
        onboarding = OnboardingPage(driver)
        if onboarding.is_loaded(timeout=10):
            onboarding.skip()
        # Skip navigates to /login (onboarding_screen.dart's _finish()),
        # not directly to /register -- this test previously asserted the
        # opposite and failed immediately, and since nearly every other
        # module's fixtures ultimately call session_helpers.register_
        # new_account() which had the identical wrong assumption, this
        # single incorrect expectation was the root cause of ~98% of the
        # whole suite failing in one shot. Register is reached from here
        # via the login screen's "go to register" link instead.
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        login.go_to_register()
        register = RegisterPage(driver)
        assert register.is_loaded(timeout=10)
        register.go_to_login()
        assert LoginPage(driver).is_loaded(timeout=10)


class TestLoginHappyPath:
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_valid_login_reaches_dashboard(self, driver, registered_account):
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        login.login(registered_account["email"], registered_account["password"])
        dashboard = DashboardPage(driver)
        assert dashboard.is_loaded(timeout=15), "Valid login did not reach the dashboard"
        session_helpers.logout(driver)

    @pytest.mark.auth
    def test_password_visibility_toggle(self, driver, registered_account):
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        # obscured by default -- toggling twice should not raise, and the
        # field should still be usable afterwards
        login.toggle_password_visibility()
        login.toggle_password_visibility()
        login.login(registered_account["email"], registered_account["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)
        session_helpers.logout(driver)

    @pytest.mark.auth
    def test_navigate_to_register_from_login(self, driver):
        # _restart_app_between_tests relaunches to dashboard when the auth
        # token is present (noReset:False); navigate to login first.
        _ensure_on_login_screen(driver)
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        login.go_to_register()
        assert RegisterPage(driver).is_loaded(timeout=10)
        RegisterPage(driver).go_to_login()
        assert LoginPage(driver).is_loaded(timeout=10)


class TestLoginInvalidCredentials:
    @pytest.mark.auth
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "email,password,case_id",
        [
            ("nonexistent.user@fitfuel-mobile-tests.invalid", "WrongPass123!", "unregistered_email"),
            (None, "WrongPass123!", "wrong_password_for_valid_email"),  # email filled at test time
            ("not-an-email", "whatever123", "malformed_email_no_at_sign"),
            ("", "whatever123", "empty_email"),
            ("valid@example.com", "", "empty_password"),
            ("", "", "both_fields_empty"),
            ("  leading.space@example.com", "Pass123!", "leading_whitespace_email"),
            ("UPPERCASE@EXAMPLE.COM", "WrongPass123!", "uppercase_email_wrong_password"),
            ("valid@example.com", "   ", "whitespace_only_password"),
            ("valid@example.com", "a" * 300, "extremely_long_password_attempt"),
        ],
    )
    def test_login_rejected(self, driver, registered_account, email, password, case_id):
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        actual_email = registered_account["email"] if email is None else email
        login.login(actual_email, password)
        assert not DashboardPage(driver).is_loaded(timeout=4), (
            f"[{case_id}] Login unexpectedly succeeded with invalid credentials"
        )

    @pytest.mark.auth
    def test_login_error_message_is_visible_and_nonempty(self, driver):
        # _restart_app_between_tests relaunches to dashboard when auth token
        # is present (noReset:False); navigate to login first.
        _ensure_on_login_screen(driver)
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        login.login("nobody@fitfuel-mobile-tests.invalid", "WrongPass123!")
        assert login.has_error(timeout=10), "No error message shown for invalid login"
        assert login.error_message().strip() != ""

    @pytest.mark.auth
    def test_repeated_failed_logins_do_not_crash_the_screen(self, driver):
        # Same navigation fix as above.
        _ensure_on_login_screen(driver)
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        for _ in range(3):
            login.login("nobody@fitfuel-mobile-tests.invalid", "WrongPass123!")
            assert login.has_error(timeout=10)
        assert login.is_loaded(timeout=5), "Login screen became unresponsive after repeated failures"


class TestLogout:
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_logout_returns_to_login_screen(self, driver, logged_in_session, on_dashboard):
        session_helpers.logout(driver)
        # Re-establish the session-scoped logged_in_session invariant for
        # every module that runs after this one.
        login = LoginPage(driver)
        login.login(logged_in_session["email"], logged_in_session["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)

    @pytest.mark.auth
    def test_logout_clears_session_so_relaunch_requires_login(self, driver, logged_in_session, on_dashboard):
        from utils import adb_helpers

        session_helpers.logout(driver)
        adb_helpers.background_app(2)
        assert LoginPage(driver).is_loaded(timeout=10), (
            "App did not require login again after logout + background/foreground cycle"
        )
        LoginPage(driver).login(logged_in_session["email"], logged_in_session["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)
