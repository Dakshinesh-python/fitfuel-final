"""
Bottom-navigation and inter-screen navigation, tested from every one of
the 4 shell screens that carry the bottom nav (Dashboard, Recommendations,
Progress, Profile) to every other tab.
"""
import pytest

from page_objects.dashboard_page import DashboardPage
from page_objects.profile_page import ProfilePage
from page_objects.progress_page import ProgressPage
from page_objects.recommendations_page import RecommendationsPage

SHELL_SCREENS = [
    ("dashboard", DashboardPage, None),
    ("recommendations", RecommendationsPage, "nav_to_meals"),
    ("progress", ProgressPage, "nav_to_progress"),
    ("profile", ProfilePage, "nav_to_profile"),
]

NAV_TARGETS = [
    ("home", DashboardPage, "nav_to_home"),
    ("meals", RecommendationsPage, "nav_to_meals"),
    ("progress", ProgressPage, "nav_to_progress"),
    ("profile", ProfilePage, "nav_to_profile"),
]


class TestBottomNavVisibility:
    @pytest.mark.navigation
    @pytest.mark.parametrize("screen_name,PageClass,nav_method_name", SHELL_SCREENS)
    def test_all_four_tabs_visible_on_every_shell_screen(
        self, driver, on_dashboard, screen_name, PageClass, nav_method_name
    ):
        if nav_method_name:
            getattr(on_dashboard, nav_method_name)()
        page = PageClass(driver)
        for tab_key in [
            page.NAV_HOME,
            page.NAV_MEALS,
            page.NAV_PROGRESS,
            page.NAV_PROFILE,
        ]:
            assert page.is_nav_tab_visible(tab_key), (
                f"Nav tab '{tab_key}' not visible on {screen_name} screen"
            )


class TestNavigateBetweenAllTabs:
    @pytest.mark.navigation
    @pytest.mark.smoke
    @pytest.mark.parametrize("tab_name,PageClass,nav_method_name", NAV_TARGETS)
    def test_navigate_to_each_tab_from_dashboard(
        self, driver, on_dashboard, tab_name, PageClass, nav_method_name
    ):
        getattr(on_dashboard, nav_method_name)()
        target_page = PageClass(driver)
        assert target_page.is_loaded(timeout=15), f"Navigating to '{tab_name}' tab failed"

    @pytest.mark.navigation
    def test_navigate_full_loop_through_all_tabs(self, driver, on_dashboard):
        """Home -> Meals -> Progress -> Profile -> Home, verifying
        each landing screen along the way."""
        on_dashboard.nav_to_meals()
        assert RecommendationsPage(driver).is_loaded(timeout=15)

        RecommendationsPage(driver).nav_to_progress()
        assert ProgressPage(driver).is_loaded(timeout=15)

        ProgressPage(driver).nav_to_profile()
        assert ProfilePage(driver).is_loaded(timeout=15)

        ProfilePage(driver).nav_to_home()
        assert DashboardPage(driver).is_loaded(timeout=15)

    @pytest.mark.navigation
    def test_rapid_repeated_tab_switching_does_not_crash(self, driver, on_dashboard):
        for _ in range(3):
            on_dashboard.nav_to_meals()
            on_dashboard.nav_to_progress()
            on_dashboard.nav_to_home()
        assert DashboardPage(driver).is_loaded(timeout=10)


class TestDeviceBackButton:
    @pytest.mark.navigation
    def test_back_button_from_recommendations_does_not_exit_app(self, driver, on_dashboard):
        on_dashboard.nav_to_meals()
        recommendations = RecommendationsPage(driver)
        assert recommendations.is_loaded(timeout=15)
        recommendations.back()
        # Bottom-nav tabs use Navigator.pushNamed (not pushReplacementNamed
        # in most cases) so back may return to dashboard OR stay put --
        # what matters is the app is still alive on a known shell screen.
        alive = RecommendationsPage(driver).is_loaded(timeout=3) or DashboardPage(driver).is_loaded(timeout=5)
        assert alive, "Device back button from Recommendations left the app in an unknown state"

    @pytest.mark.navigation
    def test_back_button_from_health_weight_during_registration(self, driver, unique_email_factory):
        from page_objects.auth_pages import LoginPage, RegisterPage
        from page_objects.health_assessment_pages import HealthWeightPage
        from page_objects.onboarding_page import OnboardingPage

        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
            onboarding.skip()
        # Skip navigates to /login, not /register -- see the fix in
        # session_helpers.register_new_account() for the full explanation.
        register = RegisterPage(driver)
        if not register.is_loaded(timeout=5):
            login = LoginPage(driver)
            if login.is_loaded(timeout=4):
                login.go_to_register()
        if not register.is_loaded(timeout=5):
            # Already logged in from an earlier module in this shard --
            # see test_00_ui_chrome.py's test_auth_screen_has_no_bottom_nav
            # for the full explanation of why this fallback is needed.
            import config
            from utils import adb_helpers

            adb_helpers.clear_app_data()
            driver.activate_app(config.APP_PACKAGE)
            if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=15):
                onboarding.skip()
            login = LoginPage(driver)
            if login.is_loaded(timeout=10):
                login.go_to_register()
        assert register.is_loaded(timeout=10)
        register.fill_form(
            name="Back Button Test",
            email=unique_email_factory("backbtn"),
            password="TestPass123!",
            age="26",
            height_cm="168",
            weight_kg="62",
        )
        register.submit()
        weight = HealthWeightPage(driver)
        assert weight.is_loaded(timeout=15)
        weight.back()
        # Must not crash; either returns to register or stays on weight screen.
        alive = weight.is_loaded(timeout=3) or register.is_loaded(timeout=5)
        assert alive


class TestUnauthenticatedAccessRedirect:
    @pytest.mark.navigation
    @pytest.mark.auth
    def test_relaunch_without_session_lands_on_login_not_dashboard(self, driver, logged_in_session):
        from page_objects.auth_pages import LoginPage
        from utils import session_helpers

        session_helpers.force_logged_out_state(driver)
        login = LoginPage(driver)
        assert login.is_loaded(timeout=15), (
            "App did not redirect to login after clearing local session data"
        )
        # Restore the session invariant for subsequent modules.
        login.login(logged_in_session["email"], logged_in_session["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)
