"""App-wide network-failure handling not already covered per-screen in
test_05/06/08/09 -- login, registration submit, weekly-plan generation,
and profile save, all attempted with the emulator's network fully
disabled."""
import pytest

from page_objects.auth_pages import LoginPage, RegisterPage
from page_objects.dashboard_page import DashboardPage
from page_objects.health_assessment_pages import HealthWeightPage
from page_objects.meal_plan_pages import WeeklyMealPlanPage
from page_objects.onboarding_page import OnboardingPage
from page_objects.profile_page import ProfilePage
from utils import adb_helpers, session_helpers


class TestLoginOffline:
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_login_while_offline_shows_error_not_crash(self, driver, logged_in_session, on_dashboard, restore_network):
        session_helpers.logout(driver)
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        adb_helpers.set_network_offline()
        login.login(logged_in_session["email"], logged_in_session["password"])
        assert login.has_error(timeout=20), "No error shown for login attempt while offline"
        adb_helpers.set_network_online()
        login.login(logged_in_session["email"], logged_in_session["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)


class TestRegistrationOffline:
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_registration_submit_while_offline(self, driver, unique_email_factory, restore_network):
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

            adb_helpers.clear_app_data()
            driver.activate_app(config.APP_PACKAGE)
            if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=15):
                onboarding.skip()
            login = LoginPage(driver)
            if login.is_loaded(timeout=10):
                login.go_to_register()
        assert register.is_loaded(timeout=10)
        register.fill_form(
            name="Offline Registration Test",
            email=unique_email_factory("offlinereg"),
            password="TestPass123!",
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        adb_helpers.set_network_offline()
        register.submit()
        assert not HealthWeightPage(driver).is_loaded(timeout=8), (
            "Registration appeared to succeed while the network was offline"
        )
        assert register.has_error(timeout=15) or register.is_loaded(timeout=3), (
            "Registration screen became unresponsive after an offline submit"
        )


class TestWeeklyPlanGenerationOffline:
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_generate_plan_while_offline(self, driver, on_dashboard, restore_network):
        on_dashboard.open_quick_meal_plan()
        plan = WeeklyMealPlanPage(driver)
        assert plan.is_loaded(timeout=15)
        if not plan.is_empty_state(timeout=5):
            pytest.skip("A plan already exists for this account; empty-state generate path not reachable")
        adb_helpers.set_network_offline()
        plan.generate_plan()
        # Must not silently hang forever -- either an error surfaces or
        # the screen remains interactive (still showing the generate
        # button) within a reasonable window.
        recovered = plan.is_empty_state(timeout=20)
        assert recovered, "Weekly plan generation while offline left the screen in an unrecoverable state"


class TestProfileSaveOffline:
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_save_name_while_offline(self, driver, on_dashboard, restore_network):
        on_dashboard.nav_to_profile()
        profile = ProfilePage(driver)
        assert profile.is_loaded(timeout=15)
        profile.open_tab("Personal")
        adb_helpers.set_network_offline()
        profile.set_name("Offline Save Attempt")
        profile.save_name()
        # Must not crash; profile screen should still be responsive.
        assert profile.is_loaded(timeout=15)
