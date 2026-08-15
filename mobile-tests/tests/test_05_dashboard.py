"""Dashboard screen: quick-access cards, avatar/notifications entry
points, and load-error/retry behaviour."""
import pytest

from page_objects.chat_page import ChatPage
from page_objects.dashboard_page import DashboardPage
from page_objects.meal_plan_pages import WeeklyMealPlanPage
from page_objects.profile_page import ProfilePage
from page_objects.progress_page import ProgressPage
from page_objects.recommendations_page import RecommendationsPage
from utils import adb_helpers


class TestDashboardLoad:
    @pytest.mark.dashboard
    @pytest.mark.smoke
    def test_dashboard_loads_after_login(self, driver, on_dashboard):
        assert on_dashboard.is_loaded()

    @pytest.mark.dashboard
    def test_all_four_quick_access_cards_visible(self, driver, on_dashboard):
        for key in [
            on_dashboard.QUICK_RECOMMENDATIONS,
            on_dashboard.QUICK_MEAL_PLAN,
            on_dashboard.QUICK_AI_COACH,
            on_dashboard.QUICK_PROGRESS,
        ]:
            assert on_dashboard.wait_for_key(key, timeout=8), f"Quick card '{key}' not visible"

    @pytest.mark.dashboard
    def test_notifications_button_visible_and_tappable(self, driver, on_dashboard):
        assert on_dashboard.wait_for_key(on_dashboard.NOTIFICATIONS_BUTTON, timeout=5)
        on_dashboard.open_notifications()
        # No dedicated notifications screen exists yet in this codebase --
        # asserting only that tapping it does not crash the dashboard.
        assert on_dashboard.is_loaded(timeout=5)


class TestQuickAccessNavigation:
    @pytest.mark.dashboard
    @pytest.mark.navigation
    def test_recommendations_quick_card_navigates(self, driver, on_dashboard):
        on_dashboard.open_quick_recommendations()
        assert RecommendationsPage(driver).is_loaded(timeout=15)

    @pytest.mark.dashboard
    @pytest.mark.navigation
    def test_meal_plan_quick_card_navigates(self, driver, on_dashboard):
        on_dashboard.open_quick_meal_plan()
        assert WeeklyMealPlanPage(driver).is_loaded(timeout=15)

    @pytest.mark.dashboard
    @pytest.mark.navigation
    def test_ai_coach_quick_card_navigates(self, driver, on_dashboard):
        on_dashboard.open_quick_ai_coach()
        assert ChatPage(driver).is_loaded(timeout=15)

    @pytest.mark.dashboard
    @pytest.mark.navigation
    def test_progress_quick_card_navigates(self, driver, on_dashboard):
        on_dashboard.open_quick_progress()
        assert ProgressPage(driver).is_loaded(timeout=15)

    @pytest.mark.dashboard
    @pytest.mark.navigation
    def test_avatar_navigates_to_profile(self, driver, on_dashboard):
        on_dashboard.open_profile_via_avatar()
        assert ProfilePage(driver).is_loaded(timeout=15)


class TestDashboardErrorHandling:
    @pytest.mark.dashboard
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_dashboard_shows_retry_when_backend_unreachable(self, driver, on_dashboard, restore_network):
        adb_helpers.set_network_offline()
        on_dashboard.nav_to_meals()
        on_dashboard.nav_to_home()  # forces a reload attempt
        has_error = on_dashboard.has_load_error(timeout=15)
        assert has_error, "Dashboard did not show a retry affordance when the backend was unreachable"

    @pytest.mark.dashboard
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_dashboard_retry_recovers_after_network_restored(self, driver, on_dashboard, restore_network):
        adb_helpers.set_network_offline()
        on_dashboard.nav_to_meals()
        on_dashboard.nav_to_home()
        assert on_dashboard.has_load_error(timeout=15)
        adb_helpers.set_network_online()
        on_dashboard.retry_load()
        assert on_dashboard.is_loaded(timeout=15), "Dashboard did not recover after retry with network restored"
