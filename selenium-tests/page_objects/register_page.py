from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from page_objects.base_page import BasePage


class RegisterPage(BasePage):
    NAME_INPUT = (By.ID, "name")
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    AGE_INPUT = (By.ID, "age")
    GENDER_SELECT = (By.ID, "gender")
    HEIGHT_INPUT = (By.ID, "height")
    WEIGHT_INPUT = (By.ID, "weight")
    SUBMIT_BTN = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_BANNER = (By.CSS_SELECTOR, ".bg-error-container")
    LOGIN_LINK = (By.LINK_TEXT, "Log In")
    HEADING = (By.XPATH, "//h2[contains(text(),'Create Account')]")
    PASSWORD_HINT = (By.XPATH, "//p[contains(text(),'at least 8 characters')]")

    def open(self):
        self.open_route("register")
        return self

    def is_loaded(self) -> bool:
        return self.exists(*self.HEADING)

    def fill_form(self, name="", email="", password="", age="", gender="", height="", weight=""):
        if name is not None:
            self.type_text(*self.NAME_INPUT, name)
        if email is not None:
            self.type_text(*self.EMAIL_INPUT, email)
        if password is not None:
            self.type_text(*self.PASSWORD_INPUT, password)
        if age:
            self.type_text(*self.AGE_INPUT, age)
        if gender:
            Select(self.find(*self.GENDER_SELECT)).select_by_value(gender)
        if height:
            self.type_text(*self.HEIGHT_INPUT, height)
        if weight:
            self.type_text(*self.WEIGHT_INPUT, weight)
        return self

    def submit(self):
        self.click(*self.SUBMIT_BTN)
        return self

    def register(self, **fields):
        self.open()
        self.fill_form(**fields)
        self.submit()
        return self

    def has_error(self, timeout: int = 6) -> bool:
        return self.exists(*self.ERROR_BANNER, timeout=timeout)

    def get_error_text(self) -> str:
        if self.exists(*self.ERROR_BANNER, timeout=6):
            return self.text_of(*self.ERROR_BANNER)
        return ""

    def go_to_login(self):
        self.click(*self.LOGIN_LINK)
        return self

    def gender_options(self):
        select = Select(self.find(*self.GENDER_SELECT))
        return [o.get_attribute("value") for o in select.options]

    def is_field_required(self, field_locator) -> bool:
        return self.find(*field_locator).get_attribute("required") is not None

    def field_min_length(self, field_locator):
        return self.find(*field_locator).get_attribute("minlength") or self.find(*field_locator).get_attribute("minLength")
