from selenium.webdriver.common.by import By

from page_objects.layout import LayoutNav


class ProfilePage(LayoutNav):
    FIRST_NAME = (By.ID, "profile-first-name")
    LAST_NAME = (By.ID, "profile-last-name")
    EMAIL = (By.ID, "profile-email")
    SAVE_BTN = (By.ID, "profile-save-btn")

    NOTIFICATIONS_TOGGLE = (By.ID, "pref-notifications")
    MEAL_REMINDERS_TOGGLE = (By.ID, "pref-meal-reminders")
    WEEKLY_REPORT_TOGGLE = (By.ID, "pref-weekly-report")

    SECURITY_SAVE_BTN = (By.ID, "sec-save-btn")

    def open(self):
        self.open_route("profile")
        return self

    def set_first_name(self, value: str):
        self.type_text(*self.FIRST_NAME, value)
        return self

    def set_last_name(self, value: str):
        self.type_text(*self.LAST_NAME, value)
        return self

    def set_email(self, value: str):
        self.type_text(*self.EMAIL, value)
        return self

    def save_profile(self):
        self.click(*self.SAVE_BTN)
        return self

    def save_security(self):
        self.click(*self.SECURITY_SAVE_BTN)
        return self

    def toggle(self, locator):
        self.click(*locator)
        return self

    def is_loaded(self) -> bool:
        return self.exists(*self.FIRST_NAME, timeout=8) or self.exists(*self.EMAIL, timeout=8)

    def email_field_disabled(self) -> bool:
        el = self.find(*self.EMAIL)
        return el.get_attribute("disabled") is not None or el.get_attribute("readonly") is not None
