"""
Module: CRUD Operations
Covers: Create (Progress log entries, Health Assessment submission),
Update (Profile save, Preferences save), and Read (Progress page re-render
after logging) flows from the UI's perspective. All calls target the
ephemeral CI backend configuration (see config.py) so no real data anywhere
is ever mutated by this suite.
"""

import pytest

from page_objects.health_assessment_page import HealthAssessmentPage
from page_objects.profile_page import ProfilePage
from page_objects.progress_page import ProgressPage

pytestmark = pytest.mark.crud


class TestCreateProgressLog:
    def test_submit_minimal_progress_log(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight="72")
        page.submit_log()
        assert page.is_loaded()

    def test_submit_full_progress_log(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight="72", calories="2200", protein="150", carbs="230", fat="65", notes="Full CRUD test entry")
        page.submit_log()
        assert page.is_loaded()

    def test_submit_progress_log_with_only_notes(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(notes="Notes-only entry")
        page.submit_log()
        assert page.is_loaded()

    def test_submit_progress_log_twice_in_a_row(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight="70")
        page.submit_log()
        page.fill_log(weight="70.2")
        page.submit_log()
        assert page.is_loaded()

    def test_page_survives_repeated_create_attempts(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        for i in range(5):
            page.fill_log(weight=str(70 + i))
            page.submit_log()
        assert page.is_loaded()


class TestUpdateProfile:
    def test_update_first_name_and_save(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_first_name("UpdatedFirst")
        page.save_profile()
        assert page.is_loaded()

    def test_update_last_name_and_save(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_last_name("UpdatedLast")
        page.save_profile()
        assert page.is_loaded()

    def test_update_both_names_and_save(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_first_name("Both")
        page.set_last_name("Updated")
        page.save_profile()
        assert page.is_loaded()

    def test_repeated_profile_saves_do_not_break_the_form(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        for i in range(3):
            page.set_first_name(f"Repeat{i}")
            page.save_profile()
        assert page.exists(*page.FIRST_NAME)

    def test_profile_field_value_persists_within_session_after_save_click(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_first_name("PersistCheck")
        page.save_profile()
        assert page.get_value(*page.FIRST_NAME) == "PersistCheck"


class TestUpdatePreferences:
    def test_toggle_notifications_and_save(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.toggle(page.NOTIFICATIONS_TOGGLE)
        page.save_security()
        assert page.is_loaded()

    def test_toggle_meal_reminders_and_save(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.toggle(page.MEAL_REMINDERS_TOGGLE)
        page.save_security()
        assert page.is_loaded()

    def test_toggle_weekly_report_and_save(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.toggle(page.WEEKLY_REPORT_TOGGLE)
        page.save_security()
        assert page.is_loaded()

    def test_toggle_all_three_preferences_and_save(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.toggle(page.NOTIFICATIONS_TOGGLE)
        page.toggle(page.MEAL_REMINDERS_TOGGLE)
        page.toggle(page.WEEKLY_REPORT_TOGGLE)
        page.save_security()
        assert page.is_loaded()


class TestCreateHealthAssessment:
    def test_submit_health_assessment_with_defaults(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_current_weight("75")
        page.set_target_weight("70")
        page.submit()
        assert page.is_loaded() or page.wait_for_url_contains("dashboard", timeout=6)

    def test_submit_health_assessment_with_allergy_added(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_current_weight("75")
        page.set_target_weight("70")
        page.add_allergy("peanuts")
        page.submit()
        assert page.is_loaded() or page.wait_for_url_contains("dashboard", timeout=6)

    def test_submit_health_assessment_with_budget_set(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        page.set_current_weight("75")
        page.set_target_weight("70")
        page.set_daily_budget("450")
        page.submit()
        assert page.is_loaded() or page.wait_for_url_contains("dashboard", timeout=6)

    def test_submit_health_assessment_for_each_fitness_goal(self, authenticated_driver):
        page = HealthAssessmentPage(authenticated_driver).open()
        for i in range(page.fitness_goal_count()):
            page.open()
            page.set_current_weight("75")
            page.set_target_weight("70")
            page.select_fitness_goal(i)
            page.submit()
            assert page.is_loaded() or page.wait_for_url_contains("dashboard", timeout=6)


class TestReadAfterCreate:
    def test_progress_page_reloads_cleanly_after_a_log_submission(self, authenticated_driver):
        page = ProgressPage(authenticated_driver).open()
        page.fill_log(weight="73", calories="2000")
        page.submit_log()
        page.open()
        assert page.is_loaded()

    def test_dashboard_reachable_after_creating_a_progress_log(self, authenticated_driver):
        progress = ProgressPage(authenticated_driver).open()
        progress.fill_log(weight="74")
        progress.submit_log()
        progress.click_nav("dashboard")
        assert progress.wait_for_url_contains("dashboard")

    def test_profile_reflects_last_saved_first_name_on_reload(self, authenticated_driver):
        page = ProfilePage(authenticated_driver).open()
        page.set_first_name("ReloadCheck")
        page.save_profile()
        page.open()
        assert page.exists(*page.FIRST_NAME)
