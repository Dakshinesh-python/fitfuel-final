"""Weekly Meal Plan screen (day tabs, generate/regenerate) and the
Meal Detail stub screen (static content, reached only via direct route
push -- see page_objects/meal_plan_pages.py for why)."""
import pytest

from page_objects.dashboard_page import DashboardPage
from page_objects.meal_plan_pages import MealDetailPage, WeeklyMealPlanPage


@pytest.fixture
def on_weekly_plan(driver, on_dashboard):
    on_dashboard.nav_to_home()
    on_dashboard.open_quick_meal_plan()
    page = WeeklyMealPlanPage(driver)
    assert page.is_loaded(timeout=15)
    return page


class TestWeeklyPlanLoad:
    @pytest.mark.meal_plan
    @pytest.mark.smoke
    def test_weekly_plan_screen_loads(self, driver, on_weekly_plan):
        assert on_weekly_plan.is_loaded()

    @pytest.mark.meal_plan
    def test_generate_plan_when_empty_produces_day_tabs(self, driver, on_weekly_plan):
        if not on_weekly_plan.is_empty_state(timeout=5):
            pytest.skip("A plan already exists for this account from a prior test in this run")
        on_weekly_plan.generate_plan()
        assert on_weekly_plan.wait_for_key(on_weekly_plan.DAY_TABS[0], timeout=25), (
            "Generating a plan did not produce a visible day-1 tab"
        )


class TestWeeklyPlanDayTabs:
    @pytest.fixture
    def on_populated_plan(self, driver, on_weekly_plan):
        if on_weekly_plan.is_empty_state(timeout=5):
            on_weekly_plan.generate_plan()
            assert on_weekly_plan.wait_for_key(on_weekly_plan.DAY_TABS[0], timeout=25)
        return on_weekly_plan

    @pytest.mark.meal_plan
    @pytest.mark.parametrize("day_index", list(range(7)))
    def test_each_day_tab_selectable(self, driver, on_populated_plan, day_index):
        on_populated_plan.select_day(day_index)
        assert on_populated_plan.is_loaded(timeout=8), (
            f"Selecting day tab index {day_index} left the screen in a bad state"
        )

    @pytest.mark.meal_plan
    @pytest.mark.slow
    def test_regenerate_from_top_icon(self, driver, on_populated_plan):
        on_populated_plan.regenerate_from_top()
        assert on_populated_plan.wait_for_key(on_populated_plan.DAY_TABS[0], timeout=25), (
            "Regenerating the plan (top icon) did not restore the day tabs"
        )

    @pytest.mark.meal_plan
    @pytest.mark.slow
    def test_regenerate_from_bottom_button(self, driver, on_populated_plan):
        on_populated_plan.regenerate_from_bottom()
        assert on_populated_plan.wait_for_key(on_populated_plan.DAY_TABS[0], timeout=25), (
            "Regenerating the plan (bottom button) did not restore the day tabs"
        )


class TestMealDetailStub:
    """See MealDetailPage's docstring: '/meal-detail' is a registered
    route with a fully built screen behind it, but nothing in the current
    UI navigates there (RecommendationsScreen's order buttons call
    _placeOrder() with an external deep link instead of pushing this
    route), and the app has no intent-filter exposing it for a deep link
    either. appium-flutter-driver has no generic "push an arbitrary named
    route" command -- its automation surface is entirely "find and
    interact with what's on screen right now".

    Net effect: this screen is UNREACHABLE under black-box Appium testing
    as the app is currently built. Rather than fabricate a passing test
    for a path that doesn't exist, that finding is recorded as an
    explicit xfail so it shows up in the report instead of silently
    disappearing from the 400+ count."""

    @pytest.mark.meal_plan
    @pytest.mark.xfail(
        reason="No in-app navigation path or deep link reaches /meal-detail; "
        "unreachable under black-box UI automation as currently built.",
        strict=False,
    )
    def test_meal_detail_is_reachable_from_a_recommendation_card(self, driver, on_dashboard):
        on_dashboard.nav_to_meals()
        from page_objects.recommendations_page import RecommendationsPage

        recs = RecommendationsPage(driver)
        assert recs.is_loaded(timeout=15)
        recs.select_meal_type("Lunch")
        # No tap target on the recommendation card currently navigates to
        # meal-detail -- there is nothing to tap. This assertion is
        # expected to fail, which is the point: it's a live check that
        # will start passing (and the xfail should be removed) the day a
        # dev wires a "View details" tap target to this route.
        assert MealDetailPage(driver).is_loaded(timeout=5)
