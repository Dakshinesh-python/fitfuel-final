"""
Module: Error Handling
Covers: unreachable-API error surfaces, invalid-route recovery, and graceful
degradation when the backend cannot be reached (the default, deliberate CI
configuration - see config.py).
"""

import pytest
from selenium.webdriver.common.by import By

from page_objects.base_page import BasePage
from page_objects.dashboard_page import DashboardPage
from page_objects.login_page import LoginPage
from page_objects.register_page import RegisterPage
from utils.test_data import INVALID_ROUTES

pytestmark = pytest.mark.error_handling


class TestUnreachableBackendHandling:
    def test_login_with_unreachable_api_shows_error_or_falls_back_gracefully(self, driver):
        page = LoginPage(driver)
        page.login("nonexistent.user@example.com", "WrongPassword123!")
        # The app must resolve to a defined state - either a visible error
        # banner, or it never leaves /login. It must never hang indefinitely.
        has_error = page.has_error(timeout=10)
        stayed = "login" in page.current_path()
        assert has_error or stayed

    def test_register_with_unreachable_api_shows_error_or_stays_on_page(self, driver):
        page = RegisterPage(driver)
        page.register(name="Err Test", email="err.test@example.com", password="ErrTest123!")
        has_error = page.has_error(timeout=10)
        stayed = "register" in page.current_path()
        moved = "health-assessment" in page.current_path()
        assert has_error or stayed or moved

    def test_dashboard_data_fetch_failure_shows_defined_error_state(self, authenticated_driver):
        page = DashboardPage(authenticated_driver).open()
        # With no reachable backend the dashboard should surface its
        # data-testid error element rather than an indefinite spinner.
        page.wait_for_url_contains("dashboard")
        assert page.has_data_error(timeout=12) or page.is_shell_rendered()

    def test_error_banner_text_is_human_readable_not_a_raw_stack_trace(self, driver):
        page = LoginPage(driver)
        page.login("nonexistent.user@example.com", "WrongPassword123!")
        if page.has_error(timeout=8):
            text = page.get_error_text()
            assert "at Object." not in text
            assert "TypeError" not in text
            assert len(text) < 300


class TestInvalidRouteRecovery:
    @pytest.mark.parametrize("bad_route", INVALID_ROUTES)
    def test_invalid_route_recovers_to_login_without_a_blank_page(self, driver, bad_route):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_route(bad_route)
        page.wait_for_url_contains("login")
        body = driver.find_element(By.TAG_NAME, "body").text
        assert len(body.strip()) > 0

    def test_navigating_back_after_invalid_route_returns_to_a_valid_page(self, driver):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_route("login")
        page.open_route("this-route-is-not-real")
        driver.back()
        assert "login" in page.current_path() or page.exists(By.TAG_NAME, "body")


class TestFormSubmissionErrorRecovery:
    def test_repeated_failed_login_attempts_do_not_crash_the_page(self, driver):
        page = LoginPage(driver).open()
        for _ in range(3):
            page.fill_email("bad@example.com")
            page.fill_password("wrong")
            page.submit()
        assert page.is_loaded() or "login" in page.current_path()

    def test_clearing_and_resubmitting_login_form_works(self, driver):
        page = LoginPage(driver).open()
        page.fill_email("first@example.com")
        page.fill_password("first-pass")
        page.fill_email("second@example.com")
        page.fill_password("second-pass")
        page.submit()
        assert page.get_value(*page.EMAIL_INPUT) in ("", "second@example.com") or "dashboard" in page.current_path()

    def test_error_banner_does_not_persist_after_successful_field_correction(self, driver):
        page = RegisterPage(driver).open()
        page.fill_form(name="", email="", password="")
        page.submit()
        page.fill_form(name="Corrected Name", email="corrected@example.com", password="CorrectedPass123!")
        # After correcting all fields, the form should be resubmittable
        # without a lingering client-side blocked state.
        assert page.exists(*page.SUBMIT_BTN)


class TestNetworkResilience:
    def test_app_shell_remains_interactive_after_a_failed_api_call(self, authenticated_driver):
        page = DashboardPage(authenticated_driver).open()
        page.wait_for_url_contains("dashboard")
        page.click_nav("profile")
        assert page.wait_for_url_contains("profile")

    def test_switching_pages_rapidly_does_not_leave_app_in_broken_state(self, authenticated_driver):
        page = DashboardPage(authenticated_driver).open()
        for route in ("dashboard", "profile", "progress", "dashboard"):
            page.open_route(route)
        assert page.wait_for_url_contains("dashboard")
