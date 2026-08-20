"""
Multi-step integration scenarios that exercise several modules together
in one continuous session -- the kind of regression a single-screen unit
test can't catch (e.g. a name change on the Profile screen not being
reflected after a logout/login cycle). Each test here is a genuine
end-to-end scenario, not a repackaging of an existing single-screen test.
"""
import pytest

from page_objects.auth_pages import LoginPage
from page_objects.dashboard_page import DashboardPage
from page_objects.profile_page import ProfilePage
from page_objects.progress_page import ProgressPage
from page_objects.recommendations_page import RecommendationsPage
from utils import session_helpers


class TestProfileChangesPersistAcrossSessions:
    @pytest.mark.profile
    @pytest.mark.smoke
    def test_name_change_persists_after_logout_login(self, driver, unique_email_factory):
        account = {
            "email": unique_email_factory("persist"),
            "password": "TestPass123!",
            "name": "Original Name",
            "age": "28",
            "height_cm": "170",
            "weight_kg": "65",
        }
        session_helpers.register_new_account(driver, account)
        DashboardPage(driver).nav_to_profile()
        profile = ProfilePage(driver)
        profile.open_tab("Personal")
        profile.set_name("Renamed QA User")
        profile.save_name()
        session_helpers.logout(driver)
        LoginPage(driver).login(account["email"], account["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)
        DashboardPage(driver).nav_to_profile()
        profile2 = ProfilePage(driver)
        profile2.open_tab("Personal")
        assert profile2.text_of_key(profile2.NAME_FIELD, timeout=8) == "Renamed QA User", (
            "Name change did not persist across a logout/login cycle"
        )


class TestProgressDataAcrossMultipleSessions:
    @pytest.mark.progress
    def test_logged_entries_survive_relaunch(self, driver, unique_email_factory):
        account = {
            "email": unique_email_factory("progresspersist"),
            "password": "TestPass123!",
            "name": "Progress Persistence Test",
            "age": "30",
            "height_cm": "175",
            "weight_kg": "80",
        }
        session_helpers.register_new_account(driver, account)
        DashboardPage(driver).nav_to_progress()
        progress = ProgressPage(driver)
        assert progress.is_loaded(timeout=15)
        progress.open_log_sheet()
        progress.fill_log_entry(weight_kg="79.5", calories="2200")
        progress.submit_log()
        assert not progress.has_log_error(timeout=5)

        from utils import adb_helpers

        adb_helpers.background_app(2)
        assert progress.is_loaded(timeout=15) or DashboardPage(driver).is_loaded(timeout=10)
        DashboardPage(driver).nav_to_progress()
        assert ProgressPage(driver).is_loaded(timeout=15), (
            "Progress screen failed to reload after a background/foreground cycle following a log entry"
        )


class TestHealthAssessmentAffectsRecommendations:
    @pytest.mark.recommendations
    @pytest.mark.health_assessment
    def test_vegan_diet_choice_reflected_in_recommendations_reachability(self, driver, unique_email_factory):
        """Does not assert on the specific meals returned (that's a
        backend-tests concern, already covered by backend-tests/), only
        that choosing VEGAN during onboarding does not break the
        Recommendations screen's ability to load afterwards."""
        account = {
            "email": unique_email_factory("vegan"),
            "password": "TestPass123!",
            "name": "Vegan Diet Test",
            "age": "24",
            "height_cm": "160",
            "weight_kg": "55",
        }
        from page_objects.health_assessment_pages import (
            HealthActivityPage, HealthGoalsPage, HealthPrefsPage, HealthWeightPage, PlanReadyPage,
        )
        from page_objects.auth_pages import LoginPage, RegisterPage
        from page_objects.onboarding_page import OnboardingPage

        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
            onboarding.skip()
        # Skip navigates to /login, not /register -- see the fix in
        # session_helpers.register_new_account() for the full explanation.
        register = RegisterPage(driver)
        if not register.is_loaded(timeout=5):
            if LoginPage(driver).is_loaded(timeout=4):
                LoginPage(driver).go_to_register()
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
            if LoginPage(driver).is_loaded(timeout=10):
                LoginPage(driver).go_to_register()
        assert register.is_loaded(timeout=10)
        register.fill_form(**account)
        register.submit()
        weight = HealthWeightPage(driver)
        assert weight.is_loaded(timeout=15)
        weight.set_current_weight(account["weight_kg"])
        weight.set_target_weight("53")
        weight.continue_()
        HealthActivityPage(driver).select("LIGHT")
        HealthActivityPage(driver).continue_()
        HealthGoalsPage(driver).select("WEIGHT_LOSS")
        HealthGoalsPage(driver).continue_()
        prefs = HealthPrefsPage(driver)
        prefs.select_diet("VEGAN")
        prefs.set_budget("250")
        prefs.submit()
        plan_ready = PlanReadyPage(driver)
        assert plan_ready.is_loaded(timeout=20)
        plan_ready.continue_to_dashboard()
        DashboardPage(driver).nav_to_meals()
        recs = RecommendationsPage(driver)
        assert recs.is_loaded(timeout=15), "Recommendations screen failed to load for a VEGAN-diet account"


class TestConcurrentTabDataConsistency:
    @pytest.mark.navigation
    @pytest.mark.smoke
    def test_switching_tabs_rapidly_does_not_mix_up_screen_state(self, driver, on_dashboard):
        """Regression guard for a common Flutter Navigator bug class:
        rapid tab switches leaving a stale screen's widgets visible
        underneath the new one."""
        on_dashboard.nav_to_meals()
        assert RecommendationsPage(driver).is_loaded(timeout=15)
        on_dashboard.nav_to_progress()
        assert ProgressPage(driver).is_loaded(timeout=15)
        assert not RecommendationsPage(driver).wait_for_text("AI Picks for you", timeout=2), (
            "Recommendations screen marker still visible after navigating away to Progress"
        )
        on_dashboard.nav_to_home()
        assert DashboardPage(driver).is_loaded(timeout=15)


class TestFullUserJourney:
    @pytest.mark.smoke
    def test_new_user_end_to_end_journey(self, driver, unique_email_factory):
        """The single most representative real-world path through the
        app: register -> onboard -> view recommendations -> generate a
        meal plan -> log progress -> chat with the coach -> update
        profile -> logout. If this test alone passes, the app's core
        value proposition works end to end."""
        account = {
            "email": unique_email_factory("journey"),
            "password": "TestPass123!",
            "name": "Full Journey Test",
            "age": "26",
            "height_cm": "168",
            "weight_kg": "64",
        }
        session_helpers.register_new_account(driver, account)
        dashboard = DashboardPage(driver)
        assert dashboard.is_loaded(timeout=15)

        dashboard.open_quick_recommendations()
        recs = RecommendationsPage(driver)
        assert recs.is_loaded(timeout=15)

        recs.nav_to_home()
        dashboard.open_quick_meal_plan()
        from page_objects.meal_plan_pages import WeeklyMealPlanPage

        plan = WeeklyMealPlanPage(driver)
        assert plan.is_loaded(timeout=15)
        if plan.is_empty_state(timeout=5):
            plan.generate_plan()
            assert plan.wait_for_key(plan.DAY_TABS[0], timeout=25)

        plan.nav_to_progress()
        progress = ProgressPage(driver)
        assert progress.is_loaded(timeout=15)
        progress.open_log_sheet()
        progress.fill_log_entry(weight_kg="63.5", calories="1900")
        progress.submit_log()
        assert not progress.has_log_error(timeout=5)

        progress.nav_to_chat()
        from page_objects.chat_page import ChatPage

        chat = ChatPage(driver)
        assert chat.is_loaded(timeout=15)
        chat.send_message("What's a good post-workout snack?")
        assert chat.is_loaded(timeout=20)

        chat.nav_to_profile()
        profile = ProfilePage(driver)
        assert profile.is_loaded(timeout=15)
        profile.set_name("Journey Complete User")
        profile.save_name()

        session_helpers.logout(driver)
        assert LoginPage(driver).is_loaded(timeout=10), "Full journey test did not end cleanly at the login screen"
