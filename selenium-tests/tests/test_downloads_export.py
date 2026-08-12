"""
Module: Downloads & Export
Covers: the Meal Plan page's Regenerate and Download actions. This is the
real feature-equivalent of a "file upload" module for this app - FitFuel web
has no file upload input anywhere in its source (verified: no `type="file"`
element exists in web/src), so this suite tests the export-side actions that
actually exist rather than fabricating an upload flow that isn't there.
"""

import pytest

from page_objects.meal_plan_page import MealPlanPage

pytestmark = pytest.mark.downloads


class TestRegenerateAction:
    def test_regenerate_button_present(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        assert page.has_regenerate_button()

    def test_regenerate_button_is_clickable(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        page.regenerate()
        assert page.is_loaded()

    def test_regenerate_can_be_triggered_multiple_times(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        for _ in range(3):
            page.regenerate()
        assert page.is_loaded()

    def test_regenerate_does_not_navigate_away_from_meal_plan(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        page.regenerate()
        assert "meal-plan" in page.current_path()

    def test_page_remains_authenticated_after_regenerate(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        token_before = page.get_stored_token()
        page.regenerate()
        assert page.get_stored_token() == token_before


class TestDownloadAction:
    def test_download_button_present(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        assert page.has_download_button()

    def test_download_button_is_clickable(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        page.click_download()
        assert page.is_loaded()

    def test_download_does_not_navigate_away_from_meal_plan(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        page.click_download()
        assert "meal-plan" in page.current_path()

    def test_download_does_not_open_an_unhandled_native_alert(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        page.click_download()
        alert_present = False
        try:
            authenticated_driver.switch_to.alert
            alert_present = True
        except Exception:
            alert_present = False
        assert not alert_present

    def test_regenerate_then_download_sequence_does_not_error(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        page.regenerate()
        page.click_download()
        assert page.is_loaded()


class TestMealPlanNavigationInteraction:
    def test_navigating_away_and_back_preserves_buttons(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        page.click_nav("dashboard")
        page.wait_for_url_contains("dashboard")
        page.click_nav("meal-plan")
        page.wait_for_url_contains("meal-plan")
        assert page.has_regenerate_button()
        assert page.has_download_button()

    def test_meal_plan_reachable_directly_when_authenticated(self, authenticated_driver):
        page = MealPlanPage(authenticated_driver).open()
        assert "meal-plan" in page.current_path()
