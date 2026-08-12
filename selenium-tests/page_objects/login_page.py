from selenium.webdriver.common.by import By

from page_objects.base_page import BasePage


class LoginPage(BasePage):
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BTN = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_BANNER = (By.CSS_SELECTOR, ".bg-error-container")
    REGISTER_LINK = (By.LINK_TEXT, "Register now")
    HEADING = (By.XPATH, "//h2[contains(text(),'Welcome back')]")

    def open(self):
        self.open_route("login")
        return self

    def fill_email(self, value: str):
        self.type_text(*self.EMAIL_INPUT, value)
        return self

    def fill_password(self, value: str):
        self.type_text(*self.PASSWORD_INPUT, value)
        return self

    def submit(self):
        self.click(*self.SUBMIT_BTN)
        return self

    def login(self, email: str, password: str):
        self.open()
        self.fill_email(email)
        self.fill_password(password)
        self.submit()
        return self

    def is_loaded(self) -> bool:
        return self.exists(*self.HEADING)

    def get_error_text(self) -> str:
        if self.exists(*self.ERROR_BANNER, timeout=6):
            return self.text_of(*self.ERROR_BANNER)
        return ""

    def has_error(self, timeout: int = 6) -> bool:
        return self.exists(*self.ERROR_BANNER, timeout=timeout)

    def go_to_register(self):
        self.click(*self.REGISTER_LINK)
        return self

    def email_field_type(self) -> str:
        return self.find(*self.EMAIL_INPUT).get_attribute("type")

    def password_field_type(self) -> str:
        return self.find(*self.PASSWORD_INPUT).get_attribute("type")

    def is_submit_disabled(self) -> bool:
        return self.find(*self.SUBMIT_BTN).get_attribute("disabled") is not None

    def submit_button_text(self) -> str:
        return self.text_of(*self.SUBMIT_BTN)
