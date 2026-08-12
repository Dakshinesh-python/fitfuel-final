"""
Module: Responsive
Covers: layout behavior across mobile/tablet/desktop breakpoints, including
the exact 767/768 and 1023/1024 boundary pixels (Tailwind's md: and lg:
breakpoints) where FitFuel's Layout.tsx switches between the mobile drawer
nav and the persistent desktop sidebar.
"""

import pytest

from config import NAV_ROUTES
from page_objects.layout import LayoutNav
from page_objects.login_page import LoginPage
from utils.driver_factory import build_driver
from utils.test_data import RESPONSIVE_BREAKPOINTS

pytestmark = pytest.mark.responsive


@pytest.fixture
def sized_driver():
    """A driver we build ourselves so each test can control window size
    precisely (the shared `driver` fixture always uses a fixed 1440x900)."""
    drv = build_driver(window_size=(1440, 900))
    yield drv
    try:
        drv.quit()
    except Exception:
        pass


class TestLoginResponsive:
    @pytest.mark.parametrize("name,width,height", RESPONSIVE_BREAKPOINTS)
    def test_login_form_visible_and_usable_at_breakpoint(self, sized_driver, name, width, height):
        sized_driver.set_window_size(width, height)
        page = LoginPage(sized_driver).open()
        assert page.is_visible(*page.EMAIL_INPUT, timeout=8)
        assert page.is_visible(*page.SUBMIT_BTN, timeout=8)

    @pytest.mark.parametrize("name,width,height", RESPONSIVE_BREAKPOINTS)
    def test_no_horizontal_overflow_on_login_at_breakpoint(self, sized_driver, name, width, height):
        sized_driver.set_window_size(width, height)
        LoginPage(sized_driver).open()
        scroll_width = sized_driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = sized_driver.execute_script("return document.documentElement.clientWidth;")
        # Allow a small tolerance for scrollbar width differences across
        # headless Chrome versions.
        assert scroll_width <= client_width + 20


class TestNavResponsive:
    @pytest.mark.parametrize("name,width,height", RESPONSIVE_BREAKPOINTS)
    def test_dashboard_renders_without_crashing_at_breakpoint(self, sized_driver, name, width, height):
        sized_driver.set_window_size(width, height)
        nav = LayoutNav(sized_driver)
        nav.inject_auth_token()
        nav.open_route("dashboard")
        assert nav.wait_for_url_contains("dashboard")
        body = sized_driver.find_element("tag name", "body").text
        assert len(body.strip()) > 0

    def test_desktop_width_shows_persistent_sidebar_nav(self, sized_driver):
        sized_driver.set_window_size(1440, 900)
        nav = LayoutNav(sized_driver)
        nav.inject_auth_token()
        nav.open_route("dashboard")
        nav.wait_for_url_contains("dashboard")
        assert nav.is_nav_link_present("dashboard", timeout=8)

    def test_mobile_width_still_exposes_navigation_somehow(self, sized_driver):
        """Below the md: breakpoint the sidebar collapses behind a hamburger
        trigger, but at minimum the page must still expose a way to reach
        every route (either the same <nav> markup shown/hidden via CSS, or
        a mobile menu trigger) - it must never disappear from the DOM
        entirely, which would break keyboard/screen-reader users."""
        sized_driver.set_window_size(375, 667)
        nav = LayoutNav(sized_driver)
        nav.inject_auth_token()
        nav.open_route("dashboard")
        nav.wait_for_url_contains("dashboard")
        nav_present_in_dom = nav.exists("css selector", "nav", timeout=8)
        assert nav_present_in_dom

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_each_page_renders_at_mobile_width(self, sized_driver, route):
        sized_driver.set_window_size(375, 667)
        nav = LayoutNav(sized_driver)
        nav.inject_auth_token()
        nav.open_route(route)
        assert nav.wait_for_url_contains(route)

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_each_page_renders_at_tablet_width(self, sized_driver, route):
        sized_driver.set_window_size(834, 1112)
        nav = LayoutNav(sized_driver)
        nav.inject_auth_token()
        nav.open_route(route)
        assert nav.wait_for_url_contains(route)


class TestRegisterFormResponsive:
    @pytest.mark.parametrize("name,width,height", RESPONSIVE_BREAKPOINTS)
    def test_register_form_fields_all_reachable_at_breakpoint(self, sized_driver, name, width, height):
        sized_driver.set_window_size(width, height)
        from page_objects.register_page import RegisterPage

        page = RegisterPage(sized_driver).open()
        assert page.is_visible(*page.NAME_INPUT, timeout=8)
        assert page.is_visible(*page.EMAIL_INPUT, timeout=8)
        assert page.is_visible(*page.SUBMIT_BTN, timeout=8)


class TestOrientationChange:
    def test_layout_survives_portrait_to_landscape_resize(self, sized_driver):
        sized_driver.set_window_size(375, 667)
        nav = LayoutNav(sized_driver)
        nav.inject_auth_token()
        nav.open_route("dashboard")
        nav.wait_for_url_contains("dashboard")
        sized_driver.set_window_size(667, 375)
        assert nav.is_brand_visible()

    def test_layout_survives_landscape_to_portrait_resize(self, sized_driver):
        sized_driver.set_window_size(1024, 768)
        nav = LayoutNav(sized_driver)
        nav.inject_auth_token()
        nav.open_route("dashboard")
        nav.wait_for_url_contains("dashboard")
        sized_driver.set_window_size(768, 1024)
        assert nav.is_brand_visible()
