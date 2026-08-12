"""
Module: Authorization
Covers: RequireAuth route guarding in App.tsx - every protected route must
redirect to /login without a token, and must render its shell once a token
(real or injected) is present. Also covers cross-route consistency and
unknown-route handling.

Preconditions: served via `vite preview` (SPA fallback works for direct deep
links - see config.py docstring for why this matters on GitHub Pages).
"""

import pytest
from selenium.webdriver.common.by import By

from config import PROTECTED_ROUTES, PUBLIC_ROUTES
from page_objects.base_page import BasePage
from utils.test_data import INVALID_ROUTES

pytestmark = pytest.mark.authorization


class TestUnauthenticatedRedirects:
    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_direct_navigation_to_protected_route_redirects_to_login(self, driver, route):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_route(route)
        assert page.wait_for_url_contains("login")

    def test_root_redirects_to_login_when_unauthenticated(self, driver):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_base()
        assert page.wait_for_url_contains("login")


class TestAuthorizedAccess:
    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_protected_route_renders_shell_with_token_present(self, driver, route):
        page = BasePage(driver)
        page.inject_auth_token()
        page.open_route(route)
        assert page.wait_for_url_contains(route)
        assert "login" not in page.current_path()

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_protected_route_does_not_bounce_back_to_login(self, driver, route):
        page = BasePage(driver)
        page.inject_auth_token()
        page.open_route(route)
        page.wait_for_url_contains(route)
        # give the SPA a beat via explicit wait on URL stability rather than sleep
        assert page.wait_for_url_contains(route, timeout=6)


class TestPublicRoutesStayPublic:
    @pytest.mark.parametrize("route", PUBLIC_ROUTES)
    def test_public_route_reachable_without_token(self, driver, route):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_route(route)
        assert route in page.current_path()

    @pytest.mark.parametrize("route", PUBLIC_ROUTES)
    def test_public_route_still_reachable_with_token_present(self, driver, route):
        """Logging in doesn't lock a user out of /login or /register directly;
        the app doesn't force-redirect authenticated users away from them."""
        page = BasePage(driver)
        page.inject_auth_token()
        page.open_route(route)
        assert route in page.current_path()


class TestCrossRouteAuthorizationConsistency:
    def test_each_protected_route_individually_blocks_a_fresh_session(self, driver):
        page = BasePage(driver)
        for route in PROTECTED_ROUTES:
            page.clear_auth_token()
            page.open_route(route)
            assert page.wait_for_url_contains("login"), f"{route} did not redirect"

    def test_login_route_itself_is_never_treated_as_protected(self, driver):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_route("login")
        assert page.wait_for_url_contains("login")

    def test_token_removed_mid_session_blocks_next_protected_navigation(self, driver):
        page = BasePage(driver)
        page.inject_auth_token()
        page.open_route("dashboard")
        page.wait_for_url_contains("dashboard")
        page.clear_auth_token()
        page.open_route("profile")
        assert page.wait_for_url_contains("login")


class TestGuestFlagValueStrictness:
    """RequireAuth checks token truthiness, not a special 'guest' flag - these
    tests confirm no alternate localStorage key or loosely-typed value can be
    used to bypass the guard, only the real fitfuel_token key."""

    from utils.test_data import GUEST_FLAG_LIKE_VALUES

    @pytest.mark.parametrize("route", PROTECTED_ROUTES[:3])
    @pytest.mark.parametrize("flag_value", GUEST_FLAG_LIKE_VALUES)
    def test_non_exact_guest_flag_values_do_not_bypass_login(self, driver, route, flag_value):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_route("login")
        driver.execute_script(
            "window.localStorage.setItem('guest', arguments[0]);", flag_value
        )
        page.open_route(route)
        assert page.wait_for_url_contains("login")

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_exact_true_string_bypasses_login_for_every_protected_route(self, driver, route):
        """Confirms the ONLY key that grants access is fitfuel_token, and that
        setting it to a truthy string is sufficient - documenting the actual
        (weak) client-side guard behavior rather than assuming it."""
        page = BasePage(driver)
        page.inject_auth_token("true")
        page.open_route(route)
        assert "login" not in page.current_path()


class TestUnknownRoutes:
    @pytest.mark.parametrize("bad_route", INVALID_ROUTES)
    def test_unknown_route_when_unauthenticated_goes_to_login(self, driver, bad_route):
        page = BasePage(driver)
        page.clear_auth_token()
        page.open_route(bad_route)
        assert page.wait_for_url_contains("login")

    def test_unknown_route_when_authenticated_falls_back_to_login_catchall(self, driver):
        page = BasePage(driver)
        page.inject_auth_token()
        page.open_route("this-route-does-not-exist")
        # App.tsx's catch-all always redirects to /login regardless of token,
        # so an authenticated user hitting a bad path still lands on /login.
        assert page.wait_for_url_contains("login")
