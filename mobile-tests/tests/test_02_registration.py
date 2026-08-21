"""
Registration form: field-level validation, gender selector, and the
happy path through to a created account. Deliberately independent of
test_01_authentication.py's `registered_account` fixture -- every test
here either registers its own throwaway account or only inspects
client-side validation before submission, so this module can be run in
isolation (`pytest tests/test_02_registration.py`) without needing
test_01 to have executed first.
"""
import pytest

import config
from page_objects.auth_pages import LoginPage, RegisterPage
from page_objects.dashboard_page import DashboardPage
from page_objects.health_assessment_pages import HealthWeightPage
from page_objects.onboarding_page import OnboardingPage
from utils import adb_helpers, session_helpers


@pytest.fixture
def on_register_screen(driver):
    """Gets to RegisterPage from whatever state the app is currently in.

    A handful of tests in this module intentionally submit a partial
    registration and stop (e.g. test_each_gender_option_selectable lands
    on the health-assessment flow, logged in, without completing it or
    logging out -- there's no meaningful "gender was accepted" screen to
    assert on besides that). That leaves the app authenticated but on
    neither onboarding, register, nor login, which the plain
    skip-or-navigate chain below can't recover from on its own.
    `clear_app_data` (adb `pm clear`) is the guaranteed fallback: it
    wipes local storage entirely, so the next launch always starts back
    at onboarding regardless of what the previous test left behind.
    """
    onboarding = OnboardingPage(driver)
    if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
        onboarding.skip()
    register = RegisterPage(driver)
    if not register.is_loaded(timeout=5):
        login = LoginPage(driver)
        if login.is_loaded(timeout=4):
            login.go_to_register()
    if not register.is_loaded(timeout=5):
        adb_helpers.clear_app_data()
        driver.activate_app(config.APP_PACKAGE)
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=10):
            onboarding.skip()
        login = LoginPage(driver)
        if login.is_loaded(timeout=10):
            login.go_to_register()
    assert register.is_loaded(timeout=10)
    return register


class TestRegistrationHappyPath:
    @pytest.mark.smoke
    @pytest.mark.registration
    def test_full_registration_reaches_dashboard(self, driver, unique_email_factory):
        account = {
            "email": unique_email_factory("reg"),
            "password": "TestPass123!",
            "name": "New QA User",
            "age": "30",
            "height_cm": "165",
            "weight_kg": "60",
            "gender": "female",
        }
        session_helpers.register_new_account(driver, account)
        assert DashboardPage(driver).is_loaded(timeout=10)
        session_helpers.logout(driver)

    @pytest.mark.registration
    @pytest.mark.parametrize("gender", ["male", "female", "other"])
    def test_each_gender_option_selectable(self, driver, on_register_screen, unique_email_factory, gender):
        account = {
            "email": unique_email_factory(f"gender-{gender}"),
            "password": "TestPass123!",
            "name": "Gender Test User",
            "age": "25",
            "height_cm": "170",
            "weight_kg": "65",
            "gender": gender,
        }
        on_register_screen.fill_form(**account)
        on_register_screen.submit()
        weight_screen = HealthWeightPage(driver)
        assert weight_screen.is_loaded(timeout=15), f"Registration with gender={gender} did not proceed"


class TestRegistrationValidation:
    @pytest.mark.registration
    @pytest.mark.validation
    def test_submit_with_all_fields_empty_shows_error(self, driver, on_register_screen):
        on_register_screen.submit()
        assert not HealthWeightPage(driver).is_loaded(timeout=4), (
            "Empty registration form was accepted"
        )

    @pytest.mark.registration
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "email,case_id",
        [
            ("not-an-email", "no_at_sign"),
            ("missing-domain@", "missing_domain"),
            ("@missing-local.com", "missing_local_part"),
            ("spaces in@email.com", "embedded_spaces"),
            ("double@@at.com", "double_at_sign"),
            ("no-dot-in-domain@localhost", "missing_dot_in_domain"),
            ("trailing-dot@example.com.", "trailing_dot"),
            (".leading-dot@example.com", "leading_dot_in_local_part"),
            ("email@[123.123.123.123]", "ip_address_literal_domain"),
            ("email@-example.com", "domain_starts_with_hyphen"),
            ("a" * 250 + "@example.com", "extremely_long_local_part"),
            ("email@example..com", "consecutive_dots_in_domain"),
        ],
    )
    def test_malformed_email_rejected(self, driver, on_register_screen, unique_email_factory, email, case_id):
        on_register_screen.fill_form(
            name="Validation Test",
            email=email,
            password="TestPass123!",
            age="25",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        assert not HealthWeightPage(driver).is_loaded(timeout=4), (
            f"[{case_id}] Malformed email '{email}' was accepted"
        )

    @pytest.mark.registration
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "password,case_id",
        [
            ("123", "too_short_numeric"),
            ("abc", "too_short_alpha"),
            ("", "empty_password"),
            ("     ", "whitespace_only"),
            ("1", "single_character"),
            ("ab12", "four_characters"),
            pytest.param(
                "     x", "mostly_whitespace_with_one_char",
                marks=pytest.mark.xfail(
                    reason=(
                        "Confirmed pre-existing backend gap, not a test bug: "
                        "auth.routes.ts's registration schema is a bare "
                        "z.string().min(6), so a 6-character password that's "
                        "5 spaces + 1 real character passes length validation "
                        "with no complexity/entropy check behind it. Every "
                        "other case in this parametrize list is correctly "
                        "rejected (all are under the 6-char minimum); this is "
                        "the one boundary case that clears length while still "
                        "being a degenerate password. Left as xfail rather "
                        "than silently tightening backend password policy, "
                        "which is a product decision, not a test-infra fix."
                    ),
                    strict=True,
                ),
            ),
            ("\t\n", "tab_and_newline_only"),
            ("12345", "five_digits_below_minimum"),
            ("abcde", "five_letters_below_minimum"),
        ],
    )
    def test_weak_password_rejected(self, driver, on_register_screen, unique_email_factory, password, case_id):
        on_register_screen.fill_form(
            name="Validation Test",
            email=unique_email_factory("weakpw"),
            password=password,
            age="25",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        assert not HealthWeightPage(driver).is_loaded(timeout=4), (
            f"[{case_id}] Weak password was accepted"
        )

    @pytest.mark.registration
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "age,height_cm,weight_kg,case_id",
        [
            ("0", "170", "65", "zero_age"),
            ("-5", "170", "65", "negative_age"),
            ("999", "170", "65", "implausibly_high_age"),
            ("25", "0", "65", "zero_height"),
            ("25", "-10", "65", "negative_height"),
            ("25", "170", "0", "zero_weight"),
            ("25", "170", "-5", "negative_weight"),
            ("abc", "170", "65", "non_numeric_age"),
            ("1", "170", "65", "minimum_plausible_age"),
            ("120", "170", "65", "maximum_plausible_age"),
            ("25", "abc", "65", "non_numeric_height"),
            ("25", "170", "abc", "non_numeric_weight"),
            ("25.5", "170", "65", "decimal_age"),
            ("25", "9999", "65", "implausibly_high_height"),
            ("25", "170", "9999", "implausibly_high_weight"),
            ("", "170", "65", "empty_age"),
        ],
    )
    def test_boundary_numeric_fields_rejected_or_handled_gracefully(
        self, driver, on_register_screen, unique_email_factory, age, height_cm, weight_kg, case_id
    ):
        on_register_screen.fill_form(
            name="Boundary Test",
            email=unique_email_factory(f"boundary-{case_id}"),
            password="TestPass123!",
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
        )
        on_register_screen.submit()
        # We assert the app does not silently crash/hang -- either it
        # rejects the value (stays on register) or the backend accepts it
        # and the flow proceeds. What must NEVER happen is the app
        # freezing with no visible state, which is why this checks for
        # EITHER a valid outcome rather than a single hardcoded one.
        proceeded = HealthWeightPage(driver).is_loaded(timeout=6)
        still_on_register = on_register_screen.is_loaded(timeout=3)
        assert proceeded or still_on_register, (
            f"[{case_id}] App reached neither the register screen nor the next "
            f"step after submitting age={age}, height={height_cm}, weight={weight_kg}"
        )
    @pytest.mark.registration
    @pytest.mark.validation
    def test_duplicate_email_registration_rejected(self, driver, on_register_screen, primary_test_account, logged_in_session):
        # `logged_in_session` guarantees primary_test_account already
        # exists in the backend by the time this test runs.
        on_register_screen.fill_form(
            name="Duplicate Email Test",
            email=primary_test_account["email"],
            password="AnotherPass123!",
            age="25",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        assert not HealthWeightPage(driver).is_loaded(timeout=6), (
            "Registration with an already-registered email unexpectedly succeeded"
        )
        assert on_register_screen.has_error(timeout=6), (
            "No error shown for duplicate-email registration attempt"
        )

    @pytest.mark.registration
    @pytest.mark.validation
    def test_very_long_name_does_not_crash_form(self, driver, on_register_screen, unique_email_factory):
        long_name = "A" * 250
        on_register_screen.fill_form(
            name=long_name,
            email=unique_email_factory("longname"),
            password="TestPass123!",
            age="25",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        # Same "must not silently freeze" contract as the boundary-numeric test.
        proceeded = HealthWeightPage(driver).is_loaded(timeout=6)
        still_on_register = on_register_screen.is_loaded(timeout=3)
        assert proceeded or still_on_register

    @pytest.mark.registration
    @pytest.mark.validation
    def test_unicode_and_special_characters_in_name(self, driver, on_register_screen, unique_email_factory):
        on_register_screen.fill_form(
            name="Jöhn O'Brien-Śmith 日本語 🎉",
            email=unique_email_factory("unicode"),
            password="TestPass123!",
            age="25",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        proceeded = HealthWeightPage(driver).is_loaded(timeout=6)
        still_on_register = on_register_screen.is_loaded(timeout=3)
        assert proceeded or still_on_register


class TestRegisterLoginNavigation:
    @pytest.mark.registration
    def test_go_to_login_link_from_register(self, driver, on_register_screen):
        on_register_screen.go_to_login()
        assert LoginPage(driver).is_loaded(timeout=10)
