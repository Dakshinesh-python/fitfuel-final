"""
Module: Navigation
Covers: side-nav presence/labels/links on every authenticated page, active
state on the current route, brand/logo presence, and logout navigation.

Preconditions: authenticated_driver fixture (two-tier login already applied).
"""

import pytest

from config import NAV_ROUTES
from page_objects.layout import LayoutNav

pytestmark = pytest.mark.navigation


class TestSideNavPresence:
    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_all_six_nav_links_present_on_every_page(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        presence = nav.all_expected_nav_labels_present()
        missing = [r for r, ok in presence.items() if not ok]
        assert not missing, f"Missing nav links on {route}: {missing}"

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_brand_heading_visible_on_every_page(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        assert nav.is_brand_visible()


class TestNavLinkNavigation:
    @pytest.mark.parametrize("target", NAV_ROUTES)
    def test_clicking_each_nav_link_navigates_to_its_route(self, authenticated_driver, target):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        nav.click_nav(target)
        assert nav.wait_for_url_contains(target)

    def test_navigation_between_all_pages_in_sequence_never_errors(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        for route in NAV_ROUTES:
            nav.click_nav(route)
            assert nav.wait_for_url_contains(route)


class TestActiveNavState:
    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_current_route_nav_item_is_marked_active(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        assert nav.is_nav_link_active(route)

    def test_only_one_nav_item_is_active_at_a_time(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("progress")
        active_count = sum(1 for r in NAV_ROUTES if nav.is_nav_link_active(r))
        assert active_count == 1


class TestNavLabels:
    def test_dashboard_label_text(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        assert "Dashboard" in nav.nav_link_text("dashboard")

    def test_recommendations_label_text(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        assert "Recommendations" in nav.nav_link_text("recommendations")

    def test_meal_plan_label_text(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        assert "Meal Plan" in nav.nav_link_text("meal-plan")

    def test_progress_label_text(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        assert "Progress" in nav.nav_link_text("progress")

    def test_chat_label_text(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        assert "Chat" in nav.nav_link_text("chat")

    def test_profile_label_text(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        assert "Profile" in nav.nav_link_text("profile")


class TestLogoutNavigation:
    def test_logout_button_present(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        buttons = nav.find_all(*nav.LOGOUT_BTNS)
        assert len(buttons) >= 1

    def test_logout_navigates_to_login(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        nav.logout()
        assert nav.wait_for_url_contains("login")

    def test_logout_clears_stored_token(self, authenticated_driver):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        nav.logout()
        nav.wait_for_url_contains("login")
        assert nav.get_stored_token() is None

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_logout_then_direct_nav_to_protected_route_redirects_again(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route("dashboard")
        nav.logout()
        nav.wait_for_url_contains("login")
        nav.open_route(route)
        assert nav.wait_for_url_contains("login")
