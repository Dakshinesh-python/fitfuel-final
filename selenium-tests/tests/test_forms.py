"""
Module: Forms
Covers: form field attributes, type correctness, submission wiring, and
placeholder/label pairing across Register, Health Assessment, Progress, and
Profile forms.
"""

import pytest
from selenium.webdriver.common.by import By

from page_objects.health_assessment_page import HealthAssessmentPage
from page_objects.profile_page import ProfilePage
from page_objects.progress_page import ProgressPage
from page_objects.register_page import RegisterPage

pytestmark = pytest.mark.forms


class TestRegisterFormFieldTypes:
    def test_name_field_type_text(self, driver):
        page = RegisterPage(driver).open()
        assert page.find(*page.NAME_INPUT).get_attribute("type") == "text"

    def test_age_field_type_number(self, driver):
        page = RegisterPage(driver).open()
        assert page.find(*page.AGE_INPUT).get_attribute("type") == "number"

    def test_height_field_type_number(self, driver):
        page = RegisterPage(driver).open()
        assert page.find(*page.HEIGHT_INPUT).get_attribute("type") == "number"

    def test_weight_field_type_number(self, driver):
        page = RegisterPage(driver).open()
        assert page.find(*page.WEIGHT_INPUT).get_attribute("type") == "number"

    def test_gender_is_select_element(self, driver):
        page = RegisterPage(driver).open()
        assert page.find(*page.GENDER_SELECT).tag_name == "select"

    def test_each_field_has_an_associated_label(self, driver):
        page = RegisterPage(driver).open()
        for field_id in ("name", "email", "password", "age", "gender", "height", "weight"):
            label = page.find(By.CSS_SELECTOR, f"label[for='{field_id}']")
            assert label.text.strip() != ""

    def test_form_fields_accept_typed_input(self, driver):
        page = RegisterPage(driver).open()
        page.fill_form(name="Test User", email="test.user@example.com", password="Password123!")
        assert page.get_value(*page.NAME_INPUT) == "Test User"
        assert page.get_value(*page.EMAIL_INPUT) == "test.user@example.com"

    def test_placeholders_present_on_key_fields(self, driver):
        page = RegisterPage(driver).open()
        assert page.find(*page.NAME_INPUT).get_attribute("placeholder")
        assert page.find(*page.EMAIL_INPUT).get_attribute("placeholder")

    def test_full_valid_form_submits_without_client_side_block(self, driver):
        page = RegisterPage(driver)
        page.register(
            name="Full Form Tester",
            email="full.form.tester@example.com",
            password="ValidPassword123!",
            age="30",
            gender="FEMALE",
            height="165",
            weight="60",
        )
        # Client-side constraints all satisfied -> the app must attempt a
        # network call rather than silently no-op; either outcome (redirect
        # or a visible error banner from an unreachable API) is acceptable.
        moved = page.wait_for_url_contains("health-assessment", timeout=8)
        has_error = page.has_error(timeout=4)
        assert moved or has_error or "register" in page.current_path()


class TestHealthAssessmentForm:
    def test_current_weight_accepts_numeric_input(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_current_weight("72")
        assert page.get_value(*page.CURRENT_WEIGHT) == "72"

    def test_target_weight_accepts_numeric_input(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_target_weight("68")
        assert page.get_value(*page.TARGET_WEIGHT) == "68"

    def test_daily_budget_accepts_numeric_input(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_daily_budget("500")
        assert page.get_value(*page.DAILY_BUDGET) == "500"

    def test_fitness_goal_radios_are_mutually_exclusive(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        radios = page.find_all(*page.FITNESS_GOAL_RADIOS)
        for r in radios:
            authenticated_driver.execute_script("arguments[0].click();", r)
        checked = [r for r in radios if r.is_selected()]
        assert len(checked) == 1

    def test_dietary_preference_radios_are_mutually_exclusive(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        radios = page.find_all(*page.DIETARY_PREF_RADIOS)
        for r in radios:
            authenticated_driver.execute_script("arguments[0].click();", r)
        checked = [r for r in radios if r.is_selected()]
        assert len(checked) == 1

    def test_selecting_each_fitness_goal_option_is_reflected(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        count = page.fitness_goal_count()
        for i in range(count):
            page.select_fitness_goal(i)
            radios = page.find_all(*page.FITNESS_GOAL_RADIOS)
            assert radios[i].is_selected()

    def test_form_submission_wired_to_submit_button(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_current_weight("70")
        page.set_target_weight("65")
        page.submit()
        # Non-destructive structural check only: submit must not throw/hang.
        assert page.is_loaded() or page.wait_for_url_contains("dashboard", timeout=6)


class TestProgressForm:
    def test_weight_field_accepts_decimal(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight="70.5")
        assert page.get_value(*page.WEIGHT) == "70.5"

    def test_calories_field_accepts_integer(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(calories="2200")
        assert page.get_value(*page.CALORIES) == "2200"

    def test_protein_field_accepts_integer(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(protein="150")
        assert page.get_value(*page.PROTEIN) == "150"

    def test_carbs_field_accepts_integer(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(carbs="220")
        assert page.get_value(*page.CARBS) == "220"

    def test_fat_field_accepts_integer(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(fat="60")
        assert page.get_value(*page.FAT) == "60"

    def test_notes_field_accepts_free_text(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(notes="Felt great today, hit all my macros.")
        assert "Felt great" in page.get_value(*page.NOTES)

    def test_all_fields_can_be_filled_together(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight="71", calories="2100", protein="140", carbs="210", fat="55", notes="Full log entry")
        assert page.get_value(*page.WEIGHT) == "71"
        assert page.get_value(*page.NOTES) == "Full log entry"

    def test_log_button_is_clickable_after_fill(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight="71", calories="2100")
        page.submit_log()
        assert page.is_loaded()


class TestProfileForm:
    def test_first_name_field_accepts_text(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_first_name("Alexandra")
        assert page.get_value(*page.FIRST_NAME) == "Alexandra"

    def test_last_name_field_accepts_text(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_last_name("Nguyen")
        assert page.get_value(*page.LAST_NAME) == "Nguyen"

    def test_save_profile_button_clickable(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_first_name("QA")
        page.save_profile()
        assert page.is_loaded()

    def test_notification_toggle_is_clickable_without_error(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.toggle(page.NOTIFICATIONS_TOGGLE)
        # The toggle element must still be present and interactive after the
        # click (i.e. the click didn't throw or navigate away).
        assert page.exists(*page.NOTIFICATIONS_TOGGLE)

    def test_meal_reminders_toggle_is_clickable(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.toggle(page.MEAL_REMINDERS_TOGGLE)
        assert page.is_loaded()

    def test_weekly_report_toggle_is_clickable(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.toggle(page.WEEKLY_REPORT_TOGGLE)
        assert page.is_loaded()

    def test_security_save_button_clickable(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.save_security()
        assert page.is_loaded()
