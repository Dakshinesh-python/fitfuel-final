"""
The 4-step health assessment flow (weight -> activity -> goals -> prefs
-> plan-ready), tested both as a full happy-path E2E and as isolated
per-screen option/boundary checks. Each test drives its own fresh
registration up to the relevant screen rather than depending on shared
state, since this flow only runs once per account and can't be
re-entered after completion.
"""
import pytest

from page_objects.auth_pages import LoginPage, RegisterPage
from page_objects.dashboard_page import DashboardPage
from page_objects.health_assessment_pages import (
    HealthActivityPage,
    HealthGoalsPage,
    HealthPrefsPage,
    HealthWeightPage,
    PlanReadyPage,
)
from page_objects.onboarding_page import OnboardingPage


def _register_to_weight_screen(driver, unique_email_factory, prefix="ha"):
    onboarding = OnboardingPage(driver)
    if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
        onboarding.skip()
    # Skip navigates to /login, not /register -- same fix as
    # session_helpers.register_new_account() and matching the fallback
    # already present in test_02_registration.py's on_register_screen
    # fixture. This was an independent copy of the same wrong assumption
    # and was why every test in this module failed at setup (0/47).
    register = RegisterPage(driver)
    if not register.is_loaded(timeout=5):
        login = LoginPage(driver)
        if login.is_loaded(timeout=4):
            login.go_to_register()
    assert register.is_loaded(timeout=10)
    register.fill_form(
        name="Health Assessment Test",
        email=unique_email_factory(prefix),
        password="TestPass123!",
        age="28",
        height_cm="172",
        weight_kg="70",
    )
    register.submit()
    weight = HealthWeightPage(driver)
    assert weight.is_loaded(timeout=15)
    return weight


class TestWeightStep:
    @pytest.mark.health_assessment
    @pytest.mark.smoke
    def test_weight_step_continue_with_valid_values(self, driver, unique_email_factory):
        weight = _register_to_weight_screen(driver, unique_email_factory, "weight-happy")
        weight.set_current_weight("70")
        weight.set_target_weight("65")
        weight.continue_()
        assert HealthActivityPage(driver).is_loaded(timeout=10)

    @pytest.mark.health_assessment
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "current,target,case_id",
        [
            ("0", "65", "zero_current_weight"),
            ("70", "0", "zero_target_weight"),
            ("-10", "65", "negative_current_weight"),
            ("70", "500", "implausibly_high_target"),
            ("35.5", "32.25", "decimal_values"),
            ("70", "70", "identical_current_and_target"),
            ("70", "200", "target_far_above_current"),
            ("abc", "65", "non_numeric_current"),
            ("70", "abc", "non_numeric_target"),
            ("1", "1", "minimum_plausible_both"),
        ],
    )
    def test_weight_step_boundary_values(self, driver, unique_email_factory, current, target, case_id):
        weight = _register_to_weight_screen(driver, unique_email_factory, f"weight-{case_id}")
        weight.set_current_weight(current)
        weight.set_target_weight(target)
        weight.continue_()
        # Contract: never a silent freeze -- either advances or stays put.
        advanced = HealthActivityPage(driver).is_loaded(timeout=6)
        stayed = weight.is_loaded(timeout=3)
        assert advanced or stayed, f"[{case_id}] App reached neither state after weight input"


class TestActivityStep:
    @pytest.fixture
    def on_activity_screen(self, driver, unique_email_factory):
        weight = _register_to_weight_screen(driver, unique_email_factory, "activity")
        weight.set_current_weight("70")
        weight.set_target_weight("65")
        weight.continue_()
        activity = HealthActivityPage(driver)
        assert activity.is_loaded(timeout=10)
        return activity

    @pytest.mark.health_assessment
    @pytest.mark.parametrize(
        "level", ["SEDENTARY", "LIGHT", "MODERATE", "ACTIVE", "VERY_ACTIVE"]
    )
    def test_each_activity_level_selectable_and_continues(self, driver, on_activity_screen, level):
        on_activity_screen.select(level)
        on_activity_screen.continue_()
        assert HealthGoalsPage(driver).is_loaded(timeout=10), (
            f"Selecting activity level {level} did not advance to the goals screen"
        )

    @pytest.mark.health_assessment
    def test_skip_activity_step(self, driver, on_activity_screen):
        on_activity_screen.skip()
        assert HealthGoalsPage(driver).is_loaded(timeout=10)


class TestGoalsStep:
    @pytest.fixture
    def on_goals_screen(self, driver, unique_email_factory):
        weight = _register_to_weight_screen(driver, unique_email_factory, "goals")
        weight.set_current_weight("70")
        weight.set_target_weight("65")
        weight.continue_()
        activity = HealthActivityPage(driver)
        assert activity.is_loaded(timeout=10)
        activity.select("MODERATE")
        activity.continue_()
        goals = HealthGoalsPage(driver)
        assert goals.is_loaded(timeout=10)
        return goals

    @pytest.mark.health_assessment
    @pytest.mark.parametrize(
        "goal", ["WEIGHT_LOSS", "MUSCLE_GAIN", "WEIGHT_GAIN", "MAINTENANCE"]
    )
    def test_each_goal_selectable_and_continues(self, driver, on_goals_screen, goal):
        on_goals_screen.select(goal)
        on_goals_screen.continue_()
        assert HealthPrefsPage(driver).is_loaded(timeout=10), (
            f"Selecting goal {goal} did not advance to the preferences screen"
        )

    @pytest.mark.health_assessment
    def test_skip_goals_step(self, driver, on_goals_screen):
        on_goals_screen.skip()
        assert HealthPrefsPage(driver).is_loaded(timeout=10)


class TestPreferencesStep:
    @pytest.fixture
    def on_prefs_screen(self, driver, unique_email_factory):
        weight = _register_to_weight_screen(driver, unique_email_factory, "prefs")
        weight.set_current_weight("70")
        weight.set_target_weight("65")
        weight.continue_()
        HealthActivityPage(driver).select("MODERATE")
        HealthActivityPage(driver).continue_()
        HealthGoalsPage(driver).select("WEIGHT_LOSS")
        HealthGoalsPage(driver).continue_()
        prefs = HealthPrefsPage(driver)
        assert prefs.is_loaded(timeout=10)
        return prefs

    @pytest.mark.health_assessment
    @pytest.mark.parametrize("diet", ["VEGETARIAN", "NON_VEGETARIAN", "VEGAN"])
    def test_each_diet_type_selectable(self, driver, on_prefs_screen, diet):
        on_prefs_screen.select_diet(diet)
        on_prefs_screen.set_budget("300")
        on_prefs_screen.submit()
        assert PlanReadyPage(driver).is_loaded(timeout=20), (
            f"Diet type {diet} did not reach the plan-ready screen"
        )

    @pytest.mark.health_assessment
    @pytest.mark.parametrize("allergy", ["Dairy", "Egg", "Gluten", "Nuts", "Shellfish"])
    def test_each_allergy_chip_toggleable(self, driver, on_prefs_screen, allergy):
        on_prefs_screen.select_diet("NON_VEGETARIAN")
        on_prefs_screen.toggle_allergy(allergy)  # select
        on_prefs_screen.toggle_allergy(allergy)  # deselect -- must not error either way
        on_prefs_screen.set_budget("250")
        on_prefs_screen.submit()
        assert PlanReadyPage(driver).is_loaded(timeout=20)

    @pytest.mark.health_assessment
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "budget,case_id",
        [
            ("0", "zero_budget"),
            ("-100", "negative_budget"),
            ("50", "minimum_slider_bound"),
            ("1000", "maximum_slider_bound"),
            ("50000", "far_above_slider_bound"),
            ("abc", "non_numeric_budget"),
            ("49", "just_below_minimum_bound"),
            ("1001", "just_above_maximum_bound"),
            ("500.50", "decimal_budget"),
            ("", "empty_budget"),
            ("   ", "whitespace_only_budget"),
            ("1e5", "scientific_notation_budget"),
        ],
    )
    def test_budget_field_boundary_values(self, driver, on_prefs_screen, budget, case_id):
        on_prefs_screen.select_diet("VEGETARIAN")
        on_prefs_screen.set_budget(budget)
        on_prefs_screen.submit()
        advanced = PlanReadyPage(driver).is_loaded(timeout=10)
        stayed = on_prefs_screen.is_loaded(timeout=3)
        assert advanced or stayed, f"[{case_id}] App reached neither state after budget={budget}"

    @pytest.mark.health_assessment
    def test_multiple_allergies_selected_together(self, driver, on_prefs_screen):
        on_prefs_screen.select_diet("VEGETARIAN")
        on_prefs_screen.toggle_allergy("Dairy")
        on_prefs_screen.toggle_allergy("Egg")
        on_prefs_screen.toggle_allergy("Gluten")
        on_prefs_screen.set_budget("350")
        on_prefs_screen.submit()
        assert PlanReadyPage(driver).is_loaded(timeout=20), (
            "Selecting 3 allergy chips together broke the preferences submit flow"
        )

    @pytest.mark.health_assessment
    def test_add_custom_allergy(self, driver, on_prefs_screen):
        # Exercises the "Add other" dialog entrypoint without asserting
        # on the native text-input dialog itself (out of Flutter's
        # widget tree once shown as a platform dialog on some Android
        # versions) -- verifies it does not crash the screen.
        on_prefs_screen.tap_key(on_prefs_screen.ADD_OTHER_BUTTON)
        assert on_prefs_screen.is_loaded(timeout=5)
        driver.back()  # dismiss dialog if shown

    @pytest.mark.health_assessment
    def test_skip_preferences_step(self, driver, on_prefs_screen):
        on_prefs_screen.skip()
        assert PlanReadyPage(driver).is_loaded(timeout=20)


class TestFullHealthAssessmentE2E:
    @pytest.mark.health_assessment
    @pytest.mark.smoke
    def test_complete_flow_all_default_choices_reaches_dashboard(self, driver, unique_email_factory):
        weight = _register_to_weight_screen(driver, unique_email_factory, "e2e")
        weight.set_current_weight("70")
        weight.set_target_weight("65")
        weight.continue_()
        HealthActivityPage(driver).select("ACTIVE")
        HealthActivityPage(driver).continue_()
        HealthGoalsPage(driver).select("MUSCLE_GAIN")
        HealthGoalsPage(driver).continue_()
        prefs = HealthPrefsPage(driver)
        prefs.select_diet("NON_VEGETARIAN")
        prefs.toggle_allergy("Nuts")
        prefs.set_budget("400")
        prefs.submit()
        plan_ready = PlanReadyPage(driver)
        assert plan_ready.is_loaded(timeout=20)
        plan_ready.continue_to_dashboard()
        assert DashboardPage(driver).is_loaded(timeout=15)

    @pytest.mark.health_assessment
    def test_full_flow_skipping_every_optional_step(self, driver, unique_email_factory):
        weight = _register_to_weight_screen(driver, unique_email_factory, "skip-all")
        weight.set_current_weight("70")
        weight.set_target_weight("65")
        weight.continue_()
        HealthActivityPage(driver).skip()
        HealthGoalsPage(driver).skip()
        HealthPrefsPage(driver).skip()
        assert PlanReadyPage(driver).is_loaded(timeout=20), (
            "Skipping every optional health-assessment step did not reach plan-ready"
        )
