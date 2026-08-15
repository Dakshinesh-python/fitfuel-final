from page_objects.base_page import BasePage


class LoginPage(BasePage):
    EMAIL_FIELD = "login_email_field"
    PASSWORD_FIELD = "login_password_field"
    PASSWORD_TOGGLE = "login_password_visibility_toggle"
    SUBMIT_BUTTON = "login_submit_button"
    REGISTER_LINK = "login_register_link"
    ERROR_TEXT = "login_error_text"

    def is_loaded(self) -> bool:
        return self.is_on_screen("login")

    def login(self, email: str, password: str) -> None:
        self.enter_text_by_key(self.EMAIL_FIELD, email)
        self.enter_text_by_key(self.PASSWORD_FIELD, password)
        self.tap_key(self.SUBMIT_BUTTON)

    def toggle_password_visibility(self) -> None:
        self.tap_key(self.PASSWORD_TOGGLE)

    def go_to_register(self) -> None:
        self.tap_key(self.REGISTER_LINK)

    def has_error(self, timeout: float = 8) -> bool:
        return self.wait_for_key(self.ERROR_TEXT, timeout)

    def error_message(self) -> str:
        return self.text_of_key(self.ERROR_TEXT)


class RegisterPage(BasePage):
    NAME_FIELD = "register_name_field"
    EMAIL_FIELD = "register_email_field"
    PASSWORD_FIELD = "register_password_field"
    AGE_FIELD = "register_age_field"
    HEIGHT_FIELD = "register_height_field"
    WEIGHT_FIELD = "register_weight_field"
    SUBMIT_BUTTON = "register_submit_button"
    LOGIN_LINK = "register_login_link"
    ERROR_TEXT = "register_error_text"
    GENDER_OPTIONS = {
        "male": "register_gender_option_male",
        "female": "register_gender_option_female",
        "other": "register_gender_option_other",
    }

    def is_loaded(self) -> bool:
        return self.is_on_screen("register")

    def select_gender(self, gender: str) -> None:
        self.tap_key(self.GENDER_OPTIONS[gender])

    def fill_form(
        self,
        name: str,
        email: str,
        password: str,
        age: str,
        height_cm: str,
        weight_kg: str,
        gender: str = "female",
    ) -> None:
        self.enter_text_by_key(self.NAME_FIELD, name)
        self.enter_text_by_key(self.EMAIL_FIELD, email)
        self.enter_text_by_key(self.PASSWORD_FIELD, password)
        self.enter_text_by_key(self.AGE_FIELD, age)
        self.select_gender(gender)
        self.enter_text_by_key(self.HEIGHT_FIELD, height_cm)
        self.enter_text_by_key(self.WEIGHT_FIELD, weight_kg)

    def submit(self) -> None:
        self.tap_key(self.SUBMIT_BUTTON)

    def go_to_login(self) -> None:
        self.tap_key(self.LOGIN_LINK)

    def has_error(self, timeout: float = 8) -> bool:
        return self.wait_for_key(self.ERROR_TEXT, timeout)

    def error_message(self) -> str:
        return self.text_of_key(self.ERROR_TEXT)
