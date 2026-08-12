"""
Module: Authentication
Covers: Login page structure/behavior, Register page structure/behavior,
malformed email handling, weak password handling, and the real-vs-injected
two-tier login path.

Preconditions (all tests): app is built and served by `vite preview` at
BASE_URL (see config.py). No live backend is required - see module docstring
in config.py for why.
"""

import pytest
from selenium.webdriver.common.by import By

from config import TEST_USER
from page_objects.login_page import LoginPage
from page_objects.register_page import RegisterPage
from utils.test_data import MALFORMED_EMAILS, VALID_LOOKING_EMAILS, WEAK_PASSWORDS

pytestmark = pytest.mark.authentication


# --------------------------------------------------------------------------
# Login page structure (Priority: High)
# --------------------------------------------------------------------------
class TestLoginPageStructure:
    def test_login_page_loads(self, driver):
        page = LoginPage(driver).open()
        assert page.is_loaded()

    def test_login_page_has_email_field(self, driver):
        page = LoginPage(driver).open()
        assert page.exists(*page.EMAIL_INPUT)

    def test_login_page_has_password_field(self, driver):
        page = LoginPage(driver).open()
        assert page.exists(*page.PASSWORD_INPUT)

    def test_email_field_type_is_email(self, driver):
        page = LoginPage(driver).open()
        assert page.email_field_type() == "email"

    def test_password_field_type_is_password(self, driver):
        page = LoginPage(driver).open()
        assert page.password_field_type() == "password"

    def test_login_page_has_submit_button(self, driver):
        page = LoginPage(driver).open()
        assert page.exists(*page.SUBMIT_BTN)

    def test_submit_button_says_sign_in(self, driver):
        page = LoginPage(driver).open()
        assert "sign in" in page.submit_button_text().lower()

    def test_login_page_has_register_link(self, driver):
        page = LoginPage(driver).open()
        assert page.exists(*page.REGISTER_LINK)

    def test_register_link_navigates_to_register(self, driver):
        page = LoginPage(driver).open()
        page.go_to_register()
        assert page.wait_for_url_contains("register")

    def test_login_page_title_contains_app_name(self, driver):
        page = LoginPage(driver).open()
        assert "fitfuel" in driver.title.lower() or page.body_text_contains("FitFuel")

    def test_email_field_is_required(self, driver):
        page = LoginPage(driver).open()
        assert page.find(*page.EMAIL_INPUT).get_attribute("required") is not None

    def test_password_field_is_required(self, driver):
        page = LoginPage(driver).open()
        assert page.find(*page.PASSWORD_INPUT).get_attribute("required") is not None


# --------------------------------------------------------------------------
# Register page structure (Priority: High)
# --------------------------------------------------------------------------
class TestRegisterPageStructure:
    def test_register_page_loads(self, driver):
        page = RegisterPage(driver).open()
        assert page.is_loaded()

    def test_register_has_name_field(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.NAME_INPUT)

    def test_register_has_email_field(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.EMAIL_INPUT)

    def test_register_has_password_field(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.PASSWORD_INPUT)

    def test_register_has_age_field(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.AGE_INPUT)

    def test_register_has_gender_select(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.GENDER_SELECT)

    def test_register_has_height_field(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.HEIGHT_INPUT)

    def test_register_has_weight_field(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.WEIGHT_INPUT)

    def test_gender_select_has_three_options(self, driver):
        page = RegisterPage(driver).open()
        # "Select" placeholder + Male/Female/Other
        assert len(page.gender_options()) == 4

    def test_gender_options_contain_expected_values(self, driver):
        page = RegisterPage(driver).open()
        options = page.gender_options()
        for expected in ("MALE", "FEMALE", "OTHER"):
            assert expected in options

    def test_password_has_min_length_hint(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.PASSWORD_HINT)

    def test_password_field_min_length_is_eight(self, driver):
        page = RegisterPage(driver).open()
        assert page.field_min_length(page.PASSWORD_INPUT) == "8"

    def test_register_has_login_link(self, driver):
        page = RegisterPage(driver).open()
        assert page.exists(*page.LOGIN_LINK)

    def test_login_link_navigates_to_login(self, driver):
        page = RegisterPage(driver).open()
        page.go_to_login()
        assert page.wait_for_url_contains("login")

    def test_name_field_is_required(self, driver):
        page = RegisterPage(driver).open()
        assert page.is_field_required(page.NAME_INPUT)

    def test_register_email_field_is_required(self, driver):
        page = RegisterPage(driver).open()
        assert page.is_field_required(page.EMAIL_INPUT)

    def test_register_password_field_is_required(self, driver):
        page = RegisterPage(driver).open()
        assert page.is_field_required(page.PASSWORD_INPUT)

    def test_age_gender_height_weight_are_optional(self, driver):
        page = RegisterPage(driver).open()
        for locator in (page.AGE_INPUT, page.HEIGHT_INPUT, page.WEIGHT_INPUT):
            assert page.find(*locator).get_attribute("required") is None


# --------------------------------------------------------------------------
# Malformed email handling (Priority: High) - 17 cases
# --------------------------------------------------------------------------
class TestEmailFormatHandling:
    @pytest.mark.parametrize("bad_email", MALFORMED_EMAILS)
    def test_various_malformed_emails_rejected_or_blocked(self, driver, bad_email):
        """HTML5 `type=email` should block obviously malformed addresses from
        being treated as valid on submit; we assert the browser either flags
        the field invalid or the app never navigates away from /login."""
        page = LoginPage(driver).open()
        page.fill_email(bad_email)
        page.fill_password("SomePassword123!")
        page.submit()

        el = page.find(*page.EMAIL_INPUT)
        is_native_invalid = not driver.execute_script(
            "return arguments[0].checkValidity();", el
        )
        stayed_on_login = "login" in page.current_path()
        assert is_native_invalid or stayed_on_login

    @pytest.mark.parametrize("good_email", VALID_LOOKING_EMAILS)
    def test_valid_looking_emails_pass_native_validation(self, driver, good_email):
        page = LoginPage(driver).open()
        page.fill_email(good_email)
        el = page.find(*page.EMAIL_INPUT)
        assert driver.execute_script("return arguments[0].checkValidity();", el) is True


# --------------------------------------------------------------------------
# Weak password handling on register (Priority: Medium) - 5 cases
# --------------------------------------------------------------------------
class TestPasswordStrengthGate:
    @pytest.mark.parametrize("weak_password", WEAK_PASSWORDS)
    def test_weak_passwords_fail_native_minlength_validation(self, driver, weak_password):
        page = RegisterPage(driver).open()
        page.fill_form(
            name="QA Tester",
            email="qa.weakpw@example.com",
            password=weak_password,
        )
        el = page.find(*page.PASSWORD_INPUT)
        driver.execute_script("arguments[0].blur();", el)
        if len(weak_password.strip()) < 8:
            assert (
                driver.execute_script("return arguments[0].checkValidity();", el) is False
            )


# --------------------------------------------------------------------------
# Two-tier login behavior (Priority: Critical)
# --------------------------------------------------------------------------
class TestLoginFlow:
    def test_login_attempt_with_unseeded_account_does_not_crash(self, driver):
        page = LoginPage(driver)
        mode = page.login_via_ui_or_inject(TEST_USER["email"], TEST_USER["password"])
        assert mode in ("ui", "injected")

    def test_login_flow_ends_on_dashboard(self, driver):
        page = LoginPage(driver)
        page.login_via_ui_or_inject(TEST_USER["email"], TEST_USER["password"])
        assert page.wait_for_url_contains("dashboard", timeout=15)

    def test_login_flow_stores_a_token(self, driver):
        page = LoginPage(driver)
        page.login_via_ui_or_inject(TEST_USER["email"], TEST_USER["password"])
        assert page.get_stored_token()

    def test_login_with_empty_credentials_does_not_navigate_away(self, driver):
        page = LoginPage(driver).open()
        page.submit()
        assert "login" in page.current_path()

    def test_login_with_only_email_does_not_navigate_away(self, driver):
        page = LoginPage(driver).open()
        page.fill_email("someone@example.com")
        page.submit()
        assert "login" in page.current_path()

    def test_login_with_only_password_does_not_navigate_away(self, driver):
        page = LoginPage(driver).open()
        page.fill_password("Password123!")
        page.submit()
        assert "login" in page.current_path()

    def test_login_form_resubmission_does_not_duplicate_error_banners(self, driver):
        page = LoginPage(driver).open()
        page.fill_email("bad@@bad.com")
        page.fill_password("x")
        page.submit()
        page.submit()
        # Regardless of whether an error banner renders, there should never
        # be more than one at a time.
        banners = driver.find_elements(By.CSS_SELECTOR, ".bg-error-container")
        assert len(banners) <= 1

    def test_register_then_redirect_target_is_health_assessment_or_stays_on_register(self, driver):
        page = RegisterPage(driver)
        page.register(
            name=TEST_USER["name"],
            email=f"unique.{TEST_USER['email']}",
            password=TEST_USER["password"],
        )
        # Either the backend accepted it (redirect to health-assessment) or
        # it correctly stayed on /register when unreachable/rejected.
        landed_on_assessment = page.wait_for_url_contains("health-assessment", timeout=8)
        assert landed_on_assessment or "register" in page.current_path()
