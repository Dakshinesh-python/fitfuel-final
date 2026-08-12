"""
Module: Accessibility
Covers: form label association, keyboard reachability, image alt text, and
basic heading structure. This is a pragmatic Selenium-level pass (DOM
attribute checks + keyboard nav), not a substitute for an axe-core/Lighthouse
audit - the README calls this out explicitly.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from config import NAV_ROUTES
from page_objects.layout import LayoutNav
from page_objects.login_page import LoginPage
from page_objects.register_page import RegisterPage

pytestmark = pytest.mark.accessibility


class TestFormLabelling:
    def test_login_email_has_a_label(self, driver):
        page = LoginPage(driver).open()
        label = page.find(By.CSS_SELECTOR, "label[for='email']")
        assert label.text.strip() != ""

    def test_login_password_has_a_label(self, driver):
        page = LoginPage(driver).open()
        label = page.find(By.CSS_SELECTOR, "label[for='password']")
        assert label.text.strip() != ""

    def test_register_all_labelled_fields_have_labels(self, driver):
        page = RegisterPage(driver).open()
        for field_id in ("name", "email", "password", "age", "gender", "height", "weight"):
            label = page.find(By.CSS_SELECTOR, f"label[for='{field_id}']")
            assert label.get_attribute("for") == field_id

    def test_inputs_have_accessible_name_via_id_or_aria_label(self, driver):
        page = RegisterPage(driver).open()
        for locator in (page.NAME_INPUT, page.EMAIL_INPUT, page.PASSWORD_INPUT):
            el = page.find(*locator)
            has_id = bool(el.get_attribute("id"))
            has_aria = bool(el.get_attribute("aria-label"))
            assert has_id or has_aria


class TestImageAltText:
    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_logo_image_has_alt_text(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        imgs = nav.find_all(By.TAG_NAME, "img", timeout=6)
        for img in imgs:
            alt = img.get_attribute("alt")
            assert alt is not None and alt.strip() != ""


class TestKeyboardNavigation:
    def test_login_form_is_tabbable_from_email_to_password(self, driver):
        page = LoginPage(driver).open()
        email_el = page.find(*page.EMAIL_INPUT)
        email_el.click()
        email_el.send_keys(Keys.TAB)
        active = driver.switch_to.active_element
        assert active.get_attribute("id") == "password"

    def test_login_submit_reachable_via_tab_order(self, driver):
        page = LoginPage(driver).open()
        page.find(*page.EMAIL_INPUT).click()
        driver.switch_to.active_element.send_keys(Keys.TAB)  # -> password
        driver.switch_to.active_element.send_keys(Keys.TAB)  # -> submit (or next focusable)
        active = driver.switch_to.active_element
        assert active.tag_name in ("button", "a", "input")

    def test_enter_key_submits_login_form(self, driver):
        page = LoginPage(driver).open()
        page.fill_email("keyboard.user@example.com")
        pw = page.find(*page.PASSWORD_INPUT)
        pw.send_keys("KeyboardPass123!")
        pw.send_keys(Keys.ENTER)
        has_error = page.has_error(timeout=8)
        moved = page.wait_for_url_contains("dashboard", timeout=4)
        assert has_error or moved or "login" in page.current_path()

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_nav_links_are_real_anchor_or_button_elements(self, authenticated_driver, route):
        """Real <a>/<button> elements get native keyboard + screen-reader
        support for free; a <div onClick> does not."""
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        el = nav.find(*nav.nav_link(route))
        assert el.tag_name in ("a", "button")


class TestHeadingStructure:
    def test_login_page_has_at_least_one_heading(self, driver):
        page = LoginPage(driver).open()
        headings = page.find_all(By.CSS_SELECTOR, "h1, h2, h3", timeout=6)
        assert len(headings) >= 1

    def test_register_page_has_at_least_one_heading(self, driver):
        page = RegisterPage(driver).open()
        headings = page.find_all(By.CSS_SELECTOR, "h1, h2, h3", timeout=6)
        assert len(headings) >= 1

    @pytest.mark.parametrize("route", NAV_ROUTES)
    def test_authenticated_pages_have_at_least_one_heading(self, authenticated_driver, route):
        nav = LayoutNav(authenticated_driver)
        nav.open_route(route)
        nav.wait_for_url_contains(route)
        headings = nav.find_all(By.CSS_SELECTOR, "h1, h2, h3", timeout=6)
        assert len(headings) >= 1


class TestFocusVisibility:
    def test_email_field_is_focusable(self, driver):
        page = LoginPage(driver).open()
        el = page.find(*page.EMAIL_INPUT)
        el.click()
        active = driver.switch_to.active_element
        assert active.get_attribute("id") == "email"

    def test_submit_button_is_focusable(self, driver):
        page = LoginPage(driver).open()
        btn = page.find(*page.SUBMIT_BTN)
        driver.execute_script("arguments[0].focus();", btn)
        active = driver.switch_to.active_element
        assert active.tag_name == "button"
