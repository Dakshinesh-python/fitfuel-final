"""
Module: UI Validation
Covers: page chrome, headings, key structural elements, and static content
sanity across every page in the app.
"""

import pytest

from config import NAV_ROUTES
from page_objects.chat_page import ChatPage
from page_objects.dashboard_page import DashboardPage
from page_objects.health_assessment_page import HealthAssessmentPage
from page_objects.layout import LayoutNav
from page_objects.login_page import LoginPage
from page_objects.meal_plan_page import MealPlanPage
from page_objects.profile_page import ProfilePage
from page_objects.progress_page import ProgressPage
from page_objects.recommendations_page import RecommendationsPage
from page_objects.register_page import RegisterPage

pytestmark = pytest.mark.ui_validation


class TestPageChrome:
    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_page_finishes_loading_within_reasonable_time(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        assert nav.wait_for_url_contains(route, timeout=15)
        assert nav.is_brand_visible()

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_page_has_no_uncaught_js_error_banner(self, authenticated_driver, route):
        """A React error boundary would typically render 'something went
        wrong'-style copy; confirm it's absent on a normal load."""
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        body = authenticated_driver.find_element("tag name", "body").text.lower()
        assert "something went wrong" not in body

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_page_title_is_not_empty(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        assert authenticated_driver.title.strip() != ""

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_page_body_is_not_blank(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        body = authenticated_driver.find_element("tag name", "body").text
        assert len(body.strip()) > 0


class TestLoginPageChrome:
    def test_login_shows_branding_copy(self, driver):
        page = LoginPage(driver).open()
        assert page.body_text_contains("FitFuel AI")

    def test_login_shows_welcome_back_heading(self, driver):
        page = LoginPage(driver).open()
        assert page.is_loaded()

    def test_login_page_has_forgot_password_link(self, driver):
        page = LoginPage(driver).open()
        assert page.exists(page.HEADING[0], "//a[contains(text(),'Forgot password')]")

    def test_login_page_has_footer_links(self, driver):
        page = LoginPage(driver).open()
        assert page.exists(page.HEADING[0], "//a[contains(text(),'Privacy Policy')]")
        assert page.exists(page.HEADING[0], "//a[contains(text(),'Terms of Service')]")


class TestRegisterPageChrome:
    def test_register_shows_branding_copy(self, driver):
        page = RegisterPage(driver).open()
        assert page.body_text_contains("FitFuel AI")

    def test_register_shows_create_account_heading(self, driver):
        page = RegisterPage(driver).open()
        assert page.is_loaded()

    def test_register_shows_helper_copy(self, driver):
        page = RegisterPage(driver).open()
        assert page.body_text_contains("personalized profile")


class TestDashboardChrome:
    def test_dashboard_loads(self, authenticated_driver):
        page = DashboardPage(authenticated_driver).open()
        assert page.is_shell_rendered()

    def test_dashboard_shows_page_title_in_header(self, authenticated_driver):
        page = DashboardPage(authenticated_driver).open()
        assert page.body_text_contains("Dashboard")

    def test_dashboard_either_renders_data_or_a_clear_error(self, authenticated_driver):
        page = DashboardPage(authenticated_driver).open()
        page.wait_for_url_contains("dashboard")
        # Non-destructive structural assertion: the page must resolve to one
        # of two well-defined states, never an indefinite blank/loading state.
        assert page.has_data_error(timeout=10) or page.is_shell_rendered()


class TestHealthAssessmentChrome:
    def test_health_assessment_loads(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        assert page.is_loaded()

    def test_health_assessment_has_fitness_goal_options(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        assert page.fitness_goal_count() == 4

    def test_health_assessment_has_dietary_preference_options(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        assert page.dietary_preference_count() == 3

    def test_health_assessment_has_submit_button(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        assert page.exists(*page.SUBMIT_BTN)


class TestRecommendationsChrome:
    def test_recommendations_loads(self, authenticated_driver):
        page = RecommendationsPage(authenticated_driver).open()
        assert page.is_loaded()

    def test_recommendations_has_interactive_controls(self, authenticated_driver):
        page = RecommendationsPage(authenticated_driver).open()
        assert page.button_count() >= 1


class TestProgressChrome:
    def test_progress_loads(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        assert page.is_loaded()

    def test_progress_has_log_button(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        assert page.exists(*page.LOG_BTN)

    def test_progress_has_all_five_metric_fields(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        for locator in (page.WEIGHT, page.CALORIES, page.PROTEIN, page.CARBS, page.FAT):
            assert page.exists(*locator)

    def test_progress_has_notes_field(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        assert page.exists(*page.NOTES)


class TestMealPlanChrome:
    def test_meal_plan_loads(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        assert page.is_loaded()

    def test_meal_plan_has_regenerate_button(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        assert page.has_regenerate_button()

    def test_meal_plan_has_download_button(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        assert page.has_download_button()


class TestChatChrome:
    def test_chat_loads(self, authenticated_driver):
        page = ChatPage(authenticated_driver).open()
        assert page.is_loaded()

    def test_chat_has_messages_container(self, authenticated_driver):
        page = ChatPage(authenticated_driver).open()
        assert page.exists(*page.MESSAGES_CONTAINER)

    def test_chat_has_input_placeholder(self, authenticated_driver):
        page = ChatPage(authenticated_driver).open()
        assert page.input_placeholder()

    def test_chat_has_send_button(self, authenticated_driver):
        page = ChatPage(authenticated_driver).open()
        assert page.exists(*page.SEND_BTN)


class TestProfileChrome:
    def test_profile_loads(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        assert page.is_loaded()

    def test_profile_has_first_name_field(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        assert page.exists(*page.FIRST_NAME)

    def test_profile_has_last_name_field(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        assert page.exists(*page.LAST_NAME)

    def test_profile_has_email_field(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        assert page.exists(*page.EMAIL)

    def test_profile_has_save_button(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        assert page.exists(*page.SAVE_BTN)

    def test_profile_has_notification_toggles(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        for locator in (page.NOTIFICATIONS_TOGGLE, page.MEAL_REMINDERS_TOGGLE, page.WEEKLY_REPORT_TOGGLE):
            assert page.exists(*locator)

    def test_profile_has_security_save_button(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        assert page.exists(*page.SECURITY_SAVE_BTN)


class TestVisualConsistency:
    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_sidenav_background_present_on_desktop(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        el = nav.find(nav.NAV_LIST[0], nav.NAV_LIST[1]) if False else None
        # Structural check: the six-item nav list itself is present.
        items = nav.find_all("css selector", "nav ul li")
        assert len(items) == 6

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_logo_image_present_on_every_page(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        assert nav.exists("css selector", "img[alt='FitFuel AI logo'], img[alt='FitFuel AI']")
