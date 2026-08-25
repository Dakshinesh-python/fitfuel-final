from page_objects.nav_bar import NavBarMixin


class DashboardPage(NavBarMixin):
    NOTIFICATIONS_BUTTON = "dashboard_notifications_button"
    PROFILE_AVATAR_BUTTON = "dashboard_profile_avatar_button"
    RETRY_BUTTON = "dashboard_retry_button"
    QUICK_RECOMMENDATIONS = "dashboard_quick_recommendations"
    QUICK_MEAL_PLAN = "dashboard_quick_meal_plan"
    QUICK_PROGRESS = "dashboard_quick_progress"

    def is_loaded(self, timeout: float = 15) -> bool:
        return self.is_on_screen("dashboard", timeout=timeout)

    def open_notifications(self) -> None:
        self.tap_key(self.NOTIFICATIONS_BUTTON)

    def open_profile_via_avatar(self) -> None:
        self.tap_key(self.PROFILE_AVATAR_BUTTON)

    def retry_load(self) -> None:
        self.tap_key(self.RETRY_BUTTON)

    def has_load_error(self, timeout: float = 5) -> bool:
        return self.wait_for_key(self.RETRY_BUTTON, timeout)

    def open_quick_recommendations(self) -> None:
        self.tap_key(self.QUICK_RECOMMENDATIONS)

    def open_quick_meal_plan(self) -> None:
        self.tap_key(self.QUICK_MEAL_PLAN)

    def open_quick_progress(self) -> None:
        self.tap_key(self.QUICK_PROGRESS)
