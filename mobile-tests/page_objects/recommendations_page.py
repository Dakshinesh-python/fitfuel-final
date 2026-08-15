from page_objects.nav_bar import NavBarMixin


class RecommendationsPage(NavBarMixin):
    RETRY_BUTTON = "recommendations_retry_button"
    MEAL_TYPE_TABS = {
        "Breakfast": "pill_tab_breakfast",
        "Lunch": "pill_tab_lunch",
        "Dinner": "pill_tab_dinner",
        "Snack": "pill_tab_snack",
    }

    def is_loaded(self, timeout: float = 15) -> bool:
        return self.is_on_screen("recommendations", timeout=timeout)

    def select_meal_type(self, meal_type: str) -> None:
        self.tap_key(self.MEAL_TYPE_TABS[meal_type])

    def retry_load(self) -> None:
        self.tap_key(self.RETRY_BUTTON)

    def has_load_error(self, timeout: float = 5) -> bool:
        return self.wait_for_key(self.RETRY_BUTTON, timeout)

    def has_any_card(self, meal_id: str, timeout: float = 10) -> bool:
        return self.wait_for_key(f"recommendation_card_{meal_id}", timeout)

    def toggle_breakdown(self, meal_id: str) -> None:
        self.tap_key(f"recommendation_expand_{meal_id}")

    def order_swiggy(self, meal_id: str) -> None:
        self.tap_key(f"recommendation_order_swiggy_{meal_id}")

    def order_zomato(self, meal_id: str) -> None:
        self.tap_key(f"recommendation_order_zomato_{meal_id}")

    def is_empty_state(self, meal_type_label: str, timeout: float = 8) -> bool:
        return self.wait_for_text(f"No meals found for {meal_type_label} yet.", timeout)
