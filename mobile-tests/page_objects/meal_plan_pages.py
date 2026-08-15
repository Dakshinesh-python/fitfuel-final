from page_objects.base_page import BasePage
from page_objects.nav_bar import NavBarMixin


class MealDetailPage(BasePage):
    """This screen is registered at the '/meal-detail' route but, as of
    the current codebase, nothing in the app actually navigates to it --
    RecommendationsScreen's order buttons call _placeOrder() directly
    with a Swiggy/Zomato deep link instead of pushing this route. It also
    renders fully static/hardcoded content (no ModalRoute arguments are
    read). Per final_year.md's own guidance ("if a listed module does not
    exist ... test what is actually there"), this is tested as a static
    screen reached only via a direct named-route push, not as part of a
    user-driven flow -- documented here rather than silently treated as
    a normal reachable screen."""
    BACK_BUTTON = "meal_detail_back_button"

    def is_loaded(self) -> bool:
        return self.is_on_screen("meal-detail")

    def go_back(self) -> None:
        self.tap_key(self.BACK_BUTTON)


class WeeklyMealPlanPage(NavBarMixin):
    REGENERATE_TOP_BUTTON = "weekly_plan_regenerate_button"
    GENERATE_BUTTON = "weekly_plan_generate_button"  # empty-state only
    REGENERATE_BOTTOM_BUTTON = "weekly_plan_regenerate_bottom_button"  # loaded-state only
    DAY_TABS = [f"weekly_plan_day_tab_{i}" for i in range(7)]

    def is_loaded(self, timeout: float = 10) -> bool:
        # "Meal Plan" collides with the dashboard quick-card label (see
        # base_page.ROUTE_TEXT_MARKERS docstring) so we additionally
        # require the day-selector or the empty-state generate button to
        # be visible before calling this screen "loaded".
        if not self.is_on_screen("weekly-plan", timeout=timeout):
            return False
        return self.wait_for_key(self.GENERATE_BUTTON, timeout=3) or self.wait_for_key(
            self.DAY_TABS[0], timeout=3
        )

    def is_empty_state(self, timeout: float = 8) -> bool:
        return self.wait_for_key(self.GENERATE_BUTTON, timeout)

    def generate_plan(self) -> None:
        self.tap_key(self.GENERATE_BUTTON)

    def regenerate_from_top(self) -> None:
        self.tap_key(self.REGENERATE_TOP_BUTTON)

    def regenerate_from_bottom(self) -> None:
        self.tap_key(self.REGENERATE_BOTTOM_BUTTON)

    def select_day(self, day_index: int) -> None:
        assert 0 <= day_index <= 6
        self.tap_key(self.DAY_TABS[day_index])
