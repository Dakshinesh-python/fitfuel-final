"""
Per-field boundary matrices for the two largest forms in the app
(registration, progress log entry), testing each field in isolation
against the same set of edge-case value classes. This complements
test_02/test_08's flow-level validation tests (which check specific
known-important combinations) with systematic single-field coverage --
same technique selenium-tests/ uses for its own boundary matrices.
"""
import pytest

from page_objects.auth_pages import RegisterPage
from page_objects.health_assessment_pages import HealthWeightPage
from page_objects.onboarding_page import OnboardingPage
from page_objects.progress_page import ProgressPage

EDGE_CASE_VALUES = {
    "empty": "",
    "whitespace_only": "   ",
    "very_long": "X" * 300,
    "leading_trailing_space": "  value  ",
    "special_characters": "!@#$%^&*()",
    "unicode": "日本語テスト🎉",
}

REGISTER_FIELD_EDGE_VALUES = {
    "name": EDGE_CASE_VALUES,
    "email_local_part": {
        "very_long_local": "x" * 60 + "@fitfuel-mobile-tests.invalid",
        "numeric_local": "123456@fitfuel-mobile-tests.invalid",
        "plus_addressing": "user+tag@fitfuel-mobile-tests.invalid",
        "hyphenated_local": "first-last@fitfuel-mobile-tests.invalid",
        "dotted_local": "first.last@fitfuel-mobile-tests.invalid",
        "underscored_local": "first_last@fitfuel-mobile-tests.invalid",
    },
    "password": {
        "only_letters_long": "abcdefghij",
        "only_digits_long": "1234567890",
        "mixed_case": "AbCdEfGh12",
        "with_spaces": "pass word 123",
        "with_symbols": "P@ssw0rd!#$",
        "unicode_password": "pässwörd123",
    },
}

BASE_REGISTER_FORM = {
    "name": "Matrix Test User",
    "email": None,  # filled per-test via unique_email_factory
    "password": "TestPass123!",
    "age": "27",
    "height_cm": "170",
    "weight_kg": "65",
}

REGISTER_TEXT_FIELDS = ["name"]  # email/password/numeric fields have their own dedicated, more meaningful cases elsewhere


@pytest.fixture
def on_register_screen(driver):
    onboarding = OnboardingPage(driver)
    if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=5):
        onboarding.skip()
    register = RegisterPage(driver)
    assert register.is_loaded(timeout=10)
    return register


class TestRegisterNameFieldMatrix:
    @pytest.mark.registration
    @pytest.mark.validation
    @pytest.mark.parametrize("case_id,value", list(EDGE_CASE_VALUES.items()))
    def test_name_field_edge_cases(self, driver, on_register_screen, unique_email_factory, case_id, value):
        on_register_screen.fill_form(
            name=value,
            email=unique_email_factory(f"namematrix-{case_id}"),
            password="TestPass123!",
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        proceeded = HealthWeightPage(driver).is_loaded(timeout=6)
        stayed = on_register_screen.is_loaded(timeout=3)
        assert proceeded or stayed, f"[name={case_id}] App reached neither expected state"


class TestRegisterEmailLocalPartMatrix:
    @pytest.mark.registration
    @pytest.mark.validation
    @pytest.mark.parametrize("case_id,email", list(REGISTER_FIELD_EDGE_VALUES["email_local_part"].items()))
    def test_email_local_part_variants(self, driver, on_register_screen, case_id, email):
        on_register_screen.fill_form(
            name="Email Matrix Test",
            email=email,
            password="TestPass123!",
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        proceeded = HealthWeightPage(driver).is_loaded(timeout=8)
        stayed = on_register_screen.is_loaded(timeout=3)
        assert proceeded or stayed, f"[email={case_id}] App reached neither expected state"


class TestRegisterPasswordVariantMatrix:
    @pytest.mark.registration
    @pytest.mark.validation
    @pytest.mark.parametrize("case_id,password", list(REGISTER_FIELD_EDGE_VALUES["password"].items()))
    def test_password_variants_all_meeting_minimum_length(self, driver, on_register_screen, unique_email_factory, case_id, password):
        on_register_screen.fill_form(
            name="Password Matrix Test",
            email=unique_email_factory(f"pwvariant-{case_id}"),
            password=password,
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        on_register_screen.submit()
        # All these values meet the stated 6-char minimum, so the
        # expectation here (unlike the weak-password matrix) IS that
        # registration succeeds -- this validates the form doesn't
        # reject well-formed-but-unusual passwords.
        assert HealthWeightPage(driver).is_loaded(timeout=10), (
            f"[password={case_id}] Valid password meeting the length minimum was rejected"
        )


class TestProfileNameFieldMatrix:
    @pytest.mark.profile
    @pytest.mark.validation
    @pytest.mark.parametrize("case_id,value", list(EDGE_CASE_VALUES.items()))
    def test_profile_name_field_edge_cases(self, driver, on_dashboard, case_id, value):
        from page_objects.profile_page import ProfilePage

        on_dashboard.nav_to_profile()
        profile = ProfilePage(driver)
        assert profile.is_loaded(timeout=15)
        profile.open_tab("Personal")
        profile.set_name(value)
        profile.save_name()
        # Must not crash regardless of whether the value is accepted.
        assert profile.is_loaded(timeout=8), f"[name={case_id}] Profile screen unresponsive after save"
        on_dashboard.nav_to_home()


class TestProgressLogFieldMatrix:
    """Each numeric field of the progress-log sheet, checked against a
    distinct edge-case value class (not overlapping test_08's
    negative/zero/non-numeric boundary set)."""

    FIELDS = ["weight_kg", "calories", "protein_g", "carbs_g", "fat_g"]
    EXTREME_VALUES = {
        "very_long_digit_string": "9" * 20,
        "scientific_notation": "1e10",
        "leading_zeros": "007",
        "plus_sign_prefix": "+42",
        "trailing_decimal_point": "42.",
        "multiple_decimal_points": "4.2.5",
    }
    REALISTIC_BOUNDARY_VALUES = {
        "minimum_plausible": "1",
        "typical_midrange": "150",
        "one_decimal_place": "42.5",
        "two_decimal_places": "42.55",
        "comma_thousands_separator": "1,000",
        "value_with_unit_suffix": "150kg",
    }

    @pytest.fixture
    def on_log_sheet(self, driver, on_dashboard):
        on_dashboard.nav_to_progress()
        page = ProgressPage(driver)
        assert page.is_loaded(timeout=15)
        page.open_log_sheet()
        return page

    @pytest.mark.progress
    @pytest.mark.validation
    @pytest.mark.parametrize("field", FIELDS)
    @pytest.mark.parametrize("case_id,value", list(EXTREME_VALUES.items()))
    def test_field_extreme_value_does_not_crash(self, driver, on_log_sheet, field, case_id, value):
        on_log_sheet.fill_log_entry(**{field: value})
        on_log_sheet.submit_log()
        errored = on_log_sheet.has_log_error(timeout=6)
        succeeded = on_log_sheet.is_loaded(timeout=5)
        assert errored or succeeded, f"[{field}={case_id}] App reached neither expected state"

    @pytest.mark.progress
    @pytest.mark.validation
    @pytest.mark.parametrize("field", FIELDS)
    @pytest.mark.parametrize("case_id,value", list(REALISTIC_BOUNDARY_VALUES.items()))
    def test_field_realistic_boundary_value(self, driver, on_log_sheet, field, case_id, value):
        on_log_sheet.fill_log_entry(**{field: value})
        on_log_sheet.submit_log()
        errored = on_log_sheet.has_log_error(timeout=6)
        succeeded = on_log_sheet.is_loaded(timeout=5)
        assert errored or succeeded, f"[{field}={case_id}] App reached neither expected state"
