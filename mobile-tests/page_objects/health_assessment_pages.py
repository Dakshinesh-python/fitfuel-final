from page_objects.base_page import BasePage


class HealthWeightPage(BasePage):
    CURRENT_WEIGHT_FIELD = "health_current_weight_field"
    TARGET_WEIGHT_FIELD = "health_target_weight_field"
    CONTINUE_BUTTON = "health_weight_continue_button"

    def is_loaded(self, timeout: float = None) -> bool:
        return self.is_on_screen("health-weight", timeout=timeout)

    def set_current_weight(self, kg: str) -> None:
        self.enter_text_by_key(self.CURRENT_WEIGHT_FIELD, kg)

    def set_target_weight(self, kg: str) -> None:
        self.enter_text_by_key(self.TARGET_WEIGHT_FIELD, kg)

    def continue_(self) -> None:
        self.tap_key(self.CONTINUE_BUTTON)


class HealthActivityPage(BasePage):
    SKIP_BUTTON = "health_activity_skip_button"
    CONTINUE_BUTTON = "health_activity_continue_button"
    OPTIONS = {
        "SEDENTARY": "health_activity_option_SEDENTARY",
        "LIGHT": "health_activity_option_LIGHT",
        "MODERATE": "health_activity_option_MODERATE",
        "ACTIVE": "health_activity_option_ACTIVE",
        "VERY_ACTIVE": "health_activity_option_VERY_ACTIVE",
    }

    def is_loaded(self, timeout: float = None) -> bool:
        return self.is_on_screen("health-activity", timeout=timeout)

    def select(self, level: str) -> None:
        self.tap_key(self.OPTIONS[level])

    def continue_(self) -> None:
        self.tap_key(self.CONTINUE_BUTTON)

    def skip(self) -> None:
        self.tap_key(self.SKIP_BUTTON)


class HealthGoalsPage(BasePage):
    SKIP_BUTTON = "health_goals_skip_button"
    CONTINUE_BUTTON = "health_goals_continue_button"
    OPTIONS = {
        "WEIGHT_LOSS": "health_goal_option_WEIGHT_LOSS",
        "MUSCLE_GAIN": "health_goal_option_MUSCLE_GAIN",
        "WEIGHT_GAIN": "health_goal_option_WEIGHT_GAIN",
        "MAINTENANCE": "health_goal_option_MAINTENANCE",
    }

    def is_loaded(self, timeout: float = None) -> bool:
        return self.is_on_screen("health-goals", timeout=timeout)

    def select(self, goal: str) -> None:
        self.tap_key(self.OPTIONS[goal])

    def continue_(self) -> None:
        self.tap_key(self.CONTINUE_BUTTON)

    def skip(self) -> None:
        self.tap_key(self.SKIP_BUTTON)


class HealthPrefsPage(BasePage):
    BUDGET_FIELD = "health_budget_field"
    BUDGET_SLIDER = "health_budget_slider"
    ADD_OTHER_BUTTON = "health_allergy_add_other_button"
    ERROR_TEXT = "health_prefs_error_text"
    SKIP_BUTTON = "health_prefs_skip_button"
    SUBMIT_BUTTON = "health_prefs_submit_button"
    DIET_OPTIONS = {
        "VEGETARIAN": "health_diet_option_VEGETARIAN",
        "NON_VEGETARIAN": "health_diet_option_NON_VEGETARIAN",
        "VEGAN": "health_diet_option_VEGAN",
    }
    ALLERGY_CHIPS = {
        "Dairy": "health_allergy_chip_Dairy",
        "Egg": "health_allergy_chip_Egg",
        "Gluten": "health_allergy_chip_Gluten",
        "Nuts": "health_allergy_chip_Nuts",
        "Shellfish": "health_allergy_chip_Shellfish",
    }

    def is_loaded(self, timeout: float = None) -> bool:
        return self.is_on_screen("health-prefs", timeout=timeout)

    def select_diet(self, diet: str) -> None:
        self.tap_key(self.DIET_OPTIONS[diet])

    def toggle_allergy(self, allergy: str) -> None:
        self.tap_key(self.ALLERGY_CHIPS[allergy])

    def set_budget(self, rupees: str) -> None:
        self.enter_text_by_key(self.BUDGET_FIELD, rupees)

    def submit(self) -> None:
        self.tap_key(self.SUBMIT_BUTTON)

    def skip(self) -> None:
        self.tap_key(self.SKIP_BUTTON)

    def has_error(self, timeout: float = 8) -> bool:
        return self.wait_for_key(self.ERROR_TEXT, timeout)


class PlanReadyPage(BasePage):
    CONTINUE_BUTTON = "plan_ready_continue_button"

    def is_loaded(self, timeout: float = None) -> bool:
        return self.is_on_screen("plan-ready", timeout=timeout)

    def continue_to_dashboard(self) -> None:
        self.tap_key(self.CONTINUE_BUTTON)
