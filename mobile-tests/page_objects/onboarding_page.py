from page_objects.base_page import BasePage


class SplashPage(BasePage):
    """No interactive elements -- purely a timed/auth-check redirect
    screen. Verified via full_file read of splash_screen.dart (0 buttons,
    0 text fields) rather than assumed."""

    def is_loaded(self, timeout: float = 5) -> bool:
        return self.is_on_screen("splash", timeout=timeout)


class OnboardingPage(BasePage):
    SKIP_BUTTON = "onboarding_skip_button"
    NEXT_BUTTON = "onboarding_next_button"

    def is_loaded(self, timeout: float = 10) -> bool:
        return self.is_on_screen("onboarding", timeout=timeout)

    def skip(self) -> None:
        self.tap_key(self.SKIP_BUTTON)

    def next(self) -> None:
        self.tap_key(self.NEXT_BUTTON)

    def complete_onboarding(self, slide_count: int = 3) -> None:
        for _ in range(slide_count):
            self.next()
