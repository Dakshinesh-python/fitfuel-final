from page_objects.nav_bar import NavBarMixin


class ProfilePage(NavBarMixin):
    LOGOUT_BUTTON = "profile_logout_button"
    NAME_FIELD = "profile_name_field"
    EMAIL_FIELD = "profile_email_field"
    SAVE_NAME_BUTTON = "profile_save_name_button"
    DELETE_ACCOUNT_BUTTON = "profile_delete_account_button"
    COMPLETE_ASSESSMENT_BUTTON = "profile_complete_assessment_button"
    RETAKE_ASSESSMENT_BUTTON = "profile_retake_assessment_button"
    TOGGLE_PUSH = "profile_toggle_push_notifications"
    TOGGLE_MEALS = "profile_toggle_meal_reminders"
    TOGGLE_WEEKLY = "profile_toggle_weekly_report"
    CURRENT_PASSWORD_FIELD = "profile_current_password_field"
    NEW_PASSWORD_FIELD = "profile_new_password_field"
    CONFIRM_PASSWORD_FIELD = "profile_confirm_password_field"
    CHANGE_PASSWORD_BUTTON = "profile_change_password_button"

    TABS = ["Personal", "Health", "Preferences", "Security"]

    def is_loaded(self, timeout: float = 10) -> bool:
        return self.is_on_screen("profile", timeout=timeout)

    def open_tab(self, tab_name: str) -> None:
        assert tab_name in self.TABS
        self.tap_text(tab_name)

    def logout(self) -> None:
        self.tap_key(self.LOGOUT_BUTTON)

    def set_name(self, name: str) -> None:
        self.enter_text_by_key(self.NAME_FIELD, name)

    def save_name(self) -> None:
        self.tap_key(self.SAVE_NAME_BUTTON)

    def delete_account(self) -> None:
        self.tap_key(self.DELETE_ACCOUNT_BUTTON)

    def toggle_push_notifications(self) -> None:
        self.tap_key(self.TOGGLE_PUSH)

    def toggle_meal_reminders(self) -> None:
        self.tap_key(self.TOGGLE_MEALS)

    def toggle_weekly_report(self) -> None:
        self.tap_key(self.TOGGLE_WEEKLY)

    def change_password(self, current: str, new: str, confirm: str) -> None:
        self.enter_text_by_key(self.CURRENT_PASSWORD_FIELD, current)
        self.enter_text_by_key(self.NEW_PASSWORD_FIELD, new)
        self.enter_text_by_key(self.CONFIRM_PASSWORD_FIELD, confirm)
        self.tap_key(self.CHANGE_PASSWORD_BUTTON)
