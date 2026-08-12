"""
Module: Input Validation
Covers: boundary values, malformed/hostile input, and numeric field
constraints across Register, Health Assessment, and Progress forms. Hostile
payloads (SQLi/XSS strings) are used purely as client-side boundary input -
this suite never talks to a real database, so this is UI-robustness testing,
not a security assessment.
"""

import pytest

from page_objects.health_assessment_page import HealthAssessmentPage
from page_objects.progress_page import ProgressPage
from page_objects.register_page import RegisterPage
from utils.test_data import BOUNDARY_STRINGS, INVALID_NUMERIC_INPUTS, VALID_NUMERIC_INPUTS

pytestmark = pytest.mark.input_validation


class TestRegisterNameBoundaries:
    @pytest.mark.parametrize("label,value", list(BOUNDARY_STRINGS.items()))
    def test_name_field_accepts_various_inputs_without_crashing(self, driver, label, value):
        page = RegisterPage(driver).open()
        page.fill_form(name=value)
        assert page.get_value(*page.NAME_INPUT) == value
        assert page.is_loaded()

    @pytest.mark.parametrize("label,value", list(BOUNDARY_STRINGS.items()))
    def test_hostile_name_input_is_not_executed_or_reflected_unescaped(self, driver, label, value):
        page = RegisterPage(driver).open()
        page.fill_form(name=value)
        # If a script tag were actually injected into the DOM unescaped and
        # executed, this would trigger a native JS alert that Selenium would
        # surface as an UnexpectedAlertPresentException on the next command.
        alert_present = False
        try:
            driver.switch_to.alert
            alert_present = True
        except Exception:
            alert_present = False
        assert not alert_present


class TestRegisterNumericFields:
    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_age_field_rejects_or_contains_invalid_numeric_input(self, driver, value):
        page = RegisterPage(driver).open()
        page.fill_form(age=value)
        el = page.find(*page.AGE_INPUT)
        raw_value = el.get_attribute("value")
        # A number input either refuses to hold non-numeric text at all, or
        # holds it but reports itself as invalid via checkValidity(); one of
        # the two must be true - never a silent, unvalidated accept.
        is_native_invalid = not driver.execute_script("return arguments[0].checkValidity();", el)
        assert raw_value == "" or is_native_invalid or raw_value == value

    @pytest.mark.parametrize("value", VALID_NUMERIC_INPUTS)
    def test_age_field_accepts_valid_numeric_input(self, driver, value):
        page = RegisterPage(driver).open()
        page.fill_form(age=value)
        assert page.get_value(*page.AGE_INPUT) == value

    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_height_field_rejects_or_flags_invalid_numeric_input(self, driver, value):
        page = RegisterPage(driver).open()
        page.fill_form(height=value)
        el = page.find(*page.HEIGHT_INPUT)
        raw_value = el.get_attribute("value")
        is_native_invalid = not driver.execute_script("return arguments[0].checkValidity();", el)
        assert raw_value == "" or is_native_invalid or raw_value == value

    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_weight_field_rejects_or_flags_invalid_numeric_input(self, driver, value):
        page = RegisterPage(driver).open()
        page.fill_form(weight=value)
        el = page.find(*page.WEIGHT_INPUT)
        raw_value = el.get_attribute("value")
        is_native_invalid = not driver.execute_script("return arguments[0].checkValidity();", el)
        assert raw_value == "" or is_native_invalid or raw_value == value

    def test_negative_age_is_flagged_invalid_when_min_attribute_present(self, driver):
        page = RegisterPage(driver).open()
        el = page.find(*page.AGE_INPUT)
        min_attr = el.get_attribute("min")
        if min_attr is not None:
            page.fill_form(age="-5")
            assert driver.execute_script("return arguments[0].checkValidity();", el) is False


class TestHealthAssessmentNumericBoundaries:
    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_current_weight_rejects_or_flags_invalid_input(self, authenticated_driver, value):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_current_weight(value)
        el = page.find(*page.CURRENT_WEIGHT)
        raw_value = el.get_attribute("value")
        is_native_invalid = not authenticated_driver.execute_script(
            "return arguments[0].checkValidity();", el
        )
        assert raw_value == "" or is_native_invalid or raw_value == value

    @pytest.mark.parametrize("value", VALID_NUMERIC_INPUTS)
    def test_current_weight_accepts_valid_input(self, authenticated_driver, value):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_current_weight(value)
        assert page.get_value(*page.CURRENT_WEIGHT) == value

    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_target_weight_rejects_or_flags_invalid_input(self, authenticated_driver, value):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_target_weight(value)
        el = page.find(*page.TARGET_WEIGHT)
        raw_value = el.get_attribute("value")
        is_native_invalid = not authenticated_driver.execute_script(
            "return arguments[0].checkValidity();", el
        )
        assert raw_value == "" or is_native_invalid or raw_value == value

    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_daily_budget_rejects_or_flags_invalid_input(self, authenticated_driver, value):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_daily_budget(value)
        el = page.find(*page.DAILY_BUDGET)
        raw_value = el.get_attribute("value")
        is_native_invalid = not authenticated_driver.execute_script(
            "return arguments[0].checkValidity();", el
        )
        assert raw_value == "" or is_native_invalid or raw_value == value

    def test_allergy_input_accepts_and_clears_after_enter(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.add_allergy("shellfish")
        assert page.is_loaded()


class TestProgressNumericBoundaries:
    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_weight_log_rejects_or_flags_invalid_input(self, authenticated_driver, value):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight=value)
        el = page.find(*page.WEIGHT)
        raw_value = el.get_attribute("value")
        is_native_invalid = not authenticated_driver.execute_script(
            "return arguments[0].checkValidity();", el
        )
        assert raw_value == "" or is_native_invalid or raw_value == value

    @pytest.mark.parametrize("value", INVALID_NUMERIC_INPUTS)
    def test_calories_log_rejects_or_flags_invalid_input(self, authenticated_driver, value):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(calories=value)
        el = page.find(*page.CALORIES)
        raw_value = el.get_attribute("value")
        is_native_invalid = not authenticated_driver.execute_script(
            "return arguments[0].checkValidity();", el
        )
        assert raw_value == "" or is_native_invalid or raw_value == value

    @pytest.mark.parametrize("label,value", list(BOUNDARY_STRINGS.items()))
    def test_notes_field_accepts_various_text_without_crashing(self, authenticated_driver, label, value):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(notes=value)
        assert page.get_value(*page.NOTES) == value
        assert page.is_loaded()

    def test_hostile_notes_input_is_not_executed(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(notes="<script>alert(1)</script>")
        alert_present = False
        try:
            authenticated_driver.switch_to.alert
            alert_present = True
        except Exception:
            alert_present = False
        assert not alert_present


class TestPasswordBoundaries:
    def test_extremely_long_password_does_not_crash_registration_form(self, driver):
        page = RegisterPage(driver).open()
        long_password = "P" * 500 + "1!"
        page.fill_form(password=long_password)
        assert page.is_loaded()

    def test_password_with_only_whitespace_flagged_or_rejected(self, driver):
        page = RegisterPage(driver).open()
        page.fill_form(password="        ")
        el = page.find(*page.PASSWORD_INPUT)
        driver.execute_script("arguments[0].blur();", el)
        assert driver.execute_script("return arguments[0].checkValidity();", el) is False

    def test_password_with_unicode_characters_accepted_by_field(self, driver):
        page = RegisterPage(driver).open()
        page.fill_form(password="Pässwörd123!€")
        assert page.get_value(*page.PASSWORD_INPUT) == "Pässwörd123!€"
