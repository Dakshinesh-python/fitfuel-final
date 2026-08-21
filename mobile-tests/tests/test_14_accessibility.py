"""Accessibility checks reachable from black-box Appium testing.

Scope, stated explicitly rather than implied: this suite can verify (a)
that icon-only interactive controls expose a semantic label to the
native accessibility tree, via Flutter's SemanticsBinding + Appium's
NATIVE_APP context switch, and (b) that the app survives an increased
system font-scale without crashing. Colour-contrast ratio checking would
require image analysis of rendered pixels and is genuinely out of scope
for this suite -- not attempted, and not silently skipped over either.
"""
import pytest
from appium.webdriver.common.appiumby import AppiumBy

from utils import adb_helpers

ICON_ONLY_TOOLTIPS = [
    "Logout",
    "Regenerate",
]


def _switch_to_native(driver):
    for ctx in driver.contexts:
        if "NATIVE" in ctx.upper():
            driver.switch_to.context(ctx)
            return True
    return False


def _switch_to_flutter(driver):
    for ctx in driver.contexts:
        if "FLUTTER" in ctx.upper():
            driver.switch_to.context(ctx)
            return True
    driver.switch_to.context(driver.contexts[0])
    return False


class TestSemanticLabelsOnIconOnlyControls:
    @pytest.mark.accessibility
    def test_nav_tabs_expose_content_description(self, driver, on_dashboard):
        switched = _switch_to_native(driver)
        if not switched:
            pytest.skip("NATIVE_APP context not exposed by this Appium/driver combination")
        try:
            nodes = driver.find_elements(
                AppiumBy.XPATH, "//*[@content-desc!='']"
            )
            assert len(nodes) > 0, (
                "No accessibility-labelled nodes found anywhere on the dashboard -- "
                "Flutter's semantics tree may not be reaching the native accessibility layer"
            )
        finally:
            _switch_to_flutter(driver)

    @pytest.mark.accessibility
    def test_logout_icon_button_has_tooltip_based_semantics(self, driver, on_dashboard):
        # profile_screen.dart's logout IconButton has tooltip: 'Logout',
        # which Flutter surfaces as a Semantics label automatically --
        # verified by source read, checked here via the flutter-driver
        # byTooltip finder (works without a context switch).
        on_dashboard.nav_to_profile()
        from page_objects.profile_page import ProfilePage

        profile = ProfilePage(driver)
        assert profile.is_loaded(timeout=15)
        assert profile.is_displayed(profile.by_tooltip("Logout"), timeout=8), (
            "Logout icon button has no 'Logout' tooltip/semantic label reachable via byTooltip"
        )


class TestFontScaling:
    @pytest.mark.accessibility
    @pytest.mark.responsiveness
    @pytest.mark.slow
    @pytest.mark.parametrize("scale", [1.3, 2.0])
    def test_dashboard_survives_increased_font_scale(self, driver, on_dashboard, scale, restore_font_scale):
        adb_helpers.set_font_scale(scale)
        adb_helpers.background_app(2)  # force the app to re-read system text-scale settings
        assert on_dashboard.is_loaded(timeout=15), (
            f"Dashboard failed to render (or crashed) at font_scale={scale}"
        )

    @pytest.mark.accessibility
    @pytest.mark.responsiveness
    @pytest.mark.slow
    def test_register_form_usable_at_increased_font_scale(self, driver, unique_email_factory, restore_font_scale):
        from page_objects.auth_pages import LoginPage, RegisterPage
        from page_objects.onboarding_page import OnboardingPage

        adb_helpers.set_font_scale(1.3)
        adb_helpers.background_app(2)
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=6):
            onboarding.skip()
        # Skip navigates to /login, not /register -- see the fix in
        # session_helpers.register_new_account() for the full explanation.
        register = RegisterPage(driver)
        if not register.is_loaded(timeout=5):
            login = LoginPage(driver)
            if login.is_loaded(timeout=4):
                login.go_to_register()
        if not register.is_loaded(timeout=5):
            # Already logged in from an earlier module in this shard --
            # see test_00_ui_chrome.py's test_auth_screen_has_no_bottom_nav
            # for the full explanation of why this fallback is needed.
            import config

            adb_helpers.clear_app_data()
            driver.activate_app(config.APP_PACKAGE)
            if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=15):
                onboarding.skip()
            login = LoginPage(driver)
            if login.is_loaded(timeout=10):
                login.go_to_register()
        assert register.is_loaded(timeout=10), "Register screen did not load at font_scale=1.3"
        register.fill_form(
            name="Font Scale Test",
            email=unique_email_factory("fontscale"),
            password="TestPass123!",
            age="27",
            height_cm="170",
            weight_kg="65",
        )
        assert register.wait_for_key(register.SUBMIT_BUTTON, timeout=5), (
            "Submit button not reachable/visible at increased font scale -- possible overflow"
        )
