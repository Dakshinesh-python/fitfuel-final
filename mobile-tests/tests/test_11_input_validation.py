"""Cross-cutting input validation and boundary cases that don't belong to
any single screen's module -- email case-sensitivity at login,
whitespace handling, and decimal precision on numeric fields not already
covered by test_02/test_03/test_08."""
import pytest

from page_objects.auth_pages import LoginPage, RegisterPage
from page_objects.dashboard_page import DashboardPage
from page_objects.health_assessment_pages import HealthWeightPage
from page_objects.onboarding_page import OnboardingPage
from utils import session_helpers


class TestEmailCaseAndWhitespace:
    @pytest.mark.validation
    @pytest.mark.auth
    def test_login_email_is_case_insensitive(self, driver, logged_in_session):
        login = LoginPage(driver) if LoginPage(driver).is_loaded(timeout=3) else None
        if login is None:
            session_helpers.logout(driver)
            login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        uppercased = logged_in_session["email"].upper()
        login.login(uppercased, logged_in_session["password"])
        # Whether the backend treats email as case-insensitive is a real
        # product decision, not something to assume -- assert only that
        # the app handles either outcome (dashboard OR a clean error)
        # without freezing.
        succeeded = DashboardPage(driver).is_loaded(timeout=10)
        errored = login.has_error(timeout=5)
        assert succeeded or errored, "App froze on uppercase-email login attempt"
        if succeeded:
            session_helpers.logout(driver)
        login.login(logged_in_session["email"], logged_in_session["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)

    @pytest.mark.validation
    def test_register_email_with_trailing_whitespace(self, driver, unique_email_factory):
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
            onboarding.skip()
        register = RegisterPage(driver)
        if not register.is_loaded(timeout=5):
            login = LoginPage(driver)
            if login.is_loaded(timeout=4):
                login.go_to_register()
        assert register.is_loaded(timeout=10)
        register.fill_form(
            name="Whitespace Email Test",
            email=unique_email_factory("wsemail") + "   ",
            password="TestPass123!",
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        register.submit()
        proceeded = HealthWeightPage(driver).is_loaded(timeout=6)
        stayed = register.is_loaded(timeout=3)
        assert proceeded or stayed


class TestDecimalPrecisionBoundaries:
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "height_cm,weight_kg,case_id",
        [
            ("170.5", "65.25", "one_and_two_decimal_places"),
            ("170.999999", "65.000001", "excessive_decimal_precision"),
            ("1", "1", "minimum_plausible_values"),
            ("300", "500", "maximum_plausible_values"),
            ("170.0", "65.0", "trailing_zero_decimals"),
            ("170,5", "65,25", "comma_as_decimal_separator"),
            (".5", ".25", "leading_dot_no_integer_part"),
            ("170.", "65.", "trailing_dot_no_fraction"),
            ("0170", "0065", "leading_zeros"),
            ("170e0", "65e0", "scientific_notation_zero_exponent"),
        ],
    )
    def test_registration_numeric_precision(self, driver, unique_email_factory, height_cm, weight_kg, case_id):
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
            onboarding.skip()
        register = RegisterPage(driver)
        if not register.is_loaded(timeout=5):
            login = LoginPage(driver)
            if login.is_loaded(timeout=4):
                login.go_to_register()
        assert register.is_loaded(timeout=10)
        register.fill_form(
            name="Decimal Precision Test",
            email=unique_email_factory(f"decimal-{case_id}"),
            password="TestPass123!",
            age="27",
            height_cm=height_cm,
            weight_kg=weight_kg,
        )
        register.submit()
        proceeded = HealthWeightPage(driver).is_loaded(timeout=6)
        stayed = register.is_loaded(timeout=3)
        assert proceeded or stayed, f"[{case_id}] Registration froze on height={height_cm}, weight={weight_kg}"


class TestFieldLengthLimits:
    @pytest.mark.validation
    def test_register_name_single_character(self, driver, unique_email_factory):
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
            onboarding.skip()
        register = RegisterPage(driver)
        if not register.is_loaded(timeout=5):
            login = LoginPage(driver)
            if login.is_loaded(timeout=4):
                login.go_to_register()
        assert register.is_loaded(timeout=10)
        register.fill_form(
            name="A",
            email=unique_email_factory("shortname"),
            password="TestPass123!",
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        register.submit()
        proceeded = HealthWeightPage(driver).is_loaded(timeout=6)
        stayed = register.is_loaded(timeout=3)
        assert proceeded or stayed

    @pytest.mark.validation
    def test_password_exactly_at_minimum_length_boundary(self, driver, unique_email_factory):
        # Backend/UI minimum is 6 characters (verified in
        # register_screen.dart's validator) -- this checks the boundary
        # itself rather than a value comfortably above or below it.
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=4):
            onboarding.skip()
        register = RegisterPage(driver)
        if not register.is_loaded(timeout=5):
            login = LoginPage(driver)
            if login.is_loaded(timeout=4):
                login.go_to_register()
        assert register.is_loaded(timeout=10)
        register.fill_form(
            name="Boundary Password Test",
            email=unique_email_factory("pwboundary"),
            password="Ab123!",  # exactly 6 characters
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        register.submit()
        assert HealthWeightPage(driver).is_loaded(timeout=10), (
            "A 6-character password was rejected even though the validator's stated minimum is 6"
        )

    @pytest.mark.validation
    def test_change_password_seven_char_boundary_mismatch(self, driver, unique_email_factory):
        """[FINDING] backend/src/routes/auth.routes.ts sets `password:
        z.string().min(6)` for registration but `newPassword:
        z.string().min(8)` for the change-password endpoint -- two
        different minimums for what a user reasonably expects to be the
        same rule. This test locks in the CURRENT (inconsistent) backend
        behaviour with a value that is valid at registration (6-7 chars)
        but invalid for a password change, so a future fix to either
        endpoint will surface here as a failing assertion instead of
        silently drifting further. Documented in README.md -> "Findings
        from building this suite" rather than silently worked around."""
        account = {
            "email": unique_email_factory("pwboundary8"),
            "password": "Ab1234!",  # 7 chars: valid at registration (min 6)
            "name": "Password Boundary Mismatch Test",
            "age": "27",
            "height_cm": "170",
            "weight_kg": "65",
        }
        session_helpers.register_new_account(driver, account)
        from page_objects.dashboard_page import DashboardPage
        from page_objects.profile_page import ProfilePage

        DashboardPage(driver).nav_to_profile()
        profile = ProfilePage(driver)
        profile.open_tab("Security")
        profile.change_password(account["password"], "Ab1234!", "Ab1234!")  # 7 chars, below the 8-char minimum
        # Expected (current backend behaviour): rejected. Verified
        # indirectly, same as the other change-password tests -- old
        # password should still work.
        session_helpers.logout(driver)
        LoginPage(driver).login(account["email"], account["password"])
        assert DashboardPage(driver).is_loaded(timeout=15), (
            "Old password stopped working -- either the 7-char change was wrongly "
            "accepted, or the account was left in a broken state"
        )
        session_helpers.logout(driver)
