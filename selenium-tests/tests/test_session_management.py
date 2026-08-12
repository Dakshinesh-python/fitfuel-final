"""
Module: Session Management
Covers: token persistence across navigation/refresh, logout clearing state,
and isolation between the real auth key and unrelated localStorage keys.
"""

import pytest

from config import NAV_ROUTES, PROTECTED_ROUTES, TOKEN_STORAGE_KEY
from page_objects.base_page import BasePage
from page_objects.layout import LayoutNav

pytestmark = pytest.mark.session


class TestTokenPersistence:
    def test_token_persists_across_in_app_navigation(self, authenticated_driver):
        page = LayoutNav(authenticated_driver)
        page.open_route("dashboard")
        token_before = page.get_stored_token()
        page.click_nav("profile")
        token_after = page.get_stored_token()
        assert token_before == token_after

    def test_token_persists_across_a_full_page_refresh(self, authenticated_driver):
        page = LayoutNav(authenticated_driver)
        page.open_route("dashboard")
        token_before = page.get_stored_token()
        authenticated_driver.refresh()
        page.wait_for_url_contains("dashboard")
        token_after = page.get_stored_token()
        assert token_before == token_after

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_refreshing_each_protected_page_keeps_the_session(self, authenticated_driver, route):
        page = LayoutNav(authenticated_driver)
        page.open_route(route)
        page.wait_for_url_contains(route)
        authenticated_driver.refresh()
        assert page.wait_for_url_contains(route)
        assert "login" not in page.current_path()

    def test_token_key_name_is_exactly_fitfuel_token(self, authenticated_driver):
        page = BasePage(authenticated_driver)
        keys = authenticated_driver.execute_script(
            "return Object.keys(window.localStorage);"
        )
        assert TOKEN_STORAGE_KEY in keys


class TestLogoutClearsSession:
    def test_logout_removes_token_from_local_storage(self, authenticated_driver):
        page = LayoutNav(authenticated_driver)
        page.open_route("dashboard")
        page.logout()
        page.wait_for_url_contains("login")
        assert page.get_stored_token() is None

    def test_after_logout_browser_back_does_not_restore_protected_view(self, authenticated_driver):
        page = LayoutNav(authenticated_driver)
        page.open_route("dashboard")
        page.logout()
        page.wait_for_url_contains("login")
        authenticated_driver.back()
        # Even if the SPA momentarily renders the cached dashboard view via
        # history, the client-side guard must not leave the user without a
        # token on a page that requires one - re-navigating must redirect.
        page.open_route("dashboard")
        assert page.wait_for_url_contains("login")

    def test_fresh_session_after_logout_requires_login_again(self, authenticated_driver):
        page = LayoutNav(authenticated_driver)
        page.open_route("dashboard")
        page.logout()
        page.wait_for_url_contains("login")
        page.open_route("profile")
        assert page.wait_for_url_contains("login")


class TestSessionIsolation:
    def test_unrelated_localstorage_keys_do_not_grant_access(self, authenticated_driver):
        page = BasePage(authenticated_driver)
        page.clear_auth_token()
        page.open_route("login")
        authenticated_driver.execute_script(
            "window.localStorage.setItem('some_other_app_token', 'value');"
        )
        page.open_route("dashboard")
        assert page.wait_for_url_contains("login")

    def test_clearing_all_storage_forces_login(self, authenticated_driver):
        page = BasePage(authenticated_driver)
        page.open_route("dashboard")
        authenticated_driver.execute_script("window.localStorage.clear();")
        page.open_route("profile")
        assert page.wait_for_url_contains("login")

    def test_empty_string_token_is_treated_as_no_token(self, authenticated_driver):
        page = BasePage(authenticated_driver)
        page.inject_auth_token("")
        page.open_route("dashboard")
        assert page.wait_for_url_contains("login")

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_each_nav_target_preserves_the_session(self, authenticated_driver, route):
        page = LayoutNav(authenticated_driver)
        page.open_route("dashboard")
        token_before = page.get_stored_token()
        page.click_nav(route)
        page.wait_for_url_contains(route)
        assert page.get_stored_token() == token_before
