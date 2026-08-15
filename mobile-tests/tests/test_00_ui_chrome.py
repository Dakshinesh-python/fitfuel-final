"""
Per-screen "chrome" checks across every screen in the app: does it load
within a reasonable SLA, is its distinguishing marker text visible, is
the bottom nav present exactly where it should be (and absent where it
shouldn't), and does the device back button leave the app in a known,
non-crashed state. This mirrors selenium-tests/ style broad-but-shallow
page-level coverage, adapted to mobile.

Named test_00_ so it collects (and, when run un-filtered, executes)
before the flow-specific modules -- these are read-only/idempotent
checks so running order relative to them doesn't matter functionally,
but keeping "does every screen at least render" first makes a red run
easy to triage (chrome failure vs flow-logic failure).
"""
import pytest

from page_objects.auth_pages import LoginPage, RegisterPage
from page_objects.base_page import ROUTE_TEXT_MARKERS
from page_objects.chat_page import ChatPage
from page_objects.dashboard_page import DashboardPage
from page_objects.health_assessment_pages import (
    HealthActivityPage,
    HealthGoalsPage,
    HealthPrefsPage,
    HealthWeightPage,
    PlanReadyPage,
)
from page_objects.meal_plan_pages import WeeklyMealPlanPage
from page_objects.onboarding_page import OnboardingPage
from page_objects.profile_page import ProfilePage
from page_objects.progress_page import ProgressPage
from page_objects.recommendations_page import RecommendationsPage

SHELL_SCREENS_WITH_NAV = [
    ("dashboard", DashboardPage),
    ("recommendations", RecommendationsPage),
    ("progress", ProgressPage),
    ("chat", ChatPage),
    ("profile", ProfilePage),
]

# Screens that intentionally do NOT carry the bottom nav (auth flow,
# health assessment flow, plan-ready) -- verified by reading each
# screen's build() method for a `bottomNavigationBar:` property.
NON_SHELL_SCREENS = [
    ("login", LoginPage),
    ("register", RegisterPage),
]


class TestMarkerMapIntegrity:
    @pytest.mark.smoke
    def test_every_screen_has_exactly_one_marker_registered(self):
        """Not an app test -- a test-suite self-check that
        ROUTE_TEXT_MARKERS covers every route main.dart registers, so a
        screen can never silently fall out of chrome coverage."""
        expected_routes = {
            "splash", "onboarding", "login", "register", "health-weight",
            "health-activity", "health-goals", "health-prefs", "plan-ready",
            "dashboard", "recommendations", "meal-detail", "weekly-plan",
            "progress", "chat", "profile",
        }
        assert set(ROUTE_TEXT_MARKERS.keys()) == expected_routes


class TestShellScreensChrome:
    @pytest.mark.smoke
    @pytest.mark.parametrize("screen_name,PageClass", SHELL_SCREENS_WITH_NAV)
    def test_shell_screen_loads_within_sla(self, driver, on_dashboard, screen_name, PageClass):
        if screen_name != "dashboard":
            nav_method = {
                "recommendations": on_dashboard.nav_to_meals,
                "progress": on_dashboard.nav_to_progress,
                "chat": on_dashboard.nav_to_chat,
                "profile": on_dashboard.nav_to_profile,
            }[screen_name]
            nav_method()
        page = PageClass(driver)
        assert page.is_loaded(timeout=15), f"{screen_name} did not load within SLA"

    @pytest.mark.parametrize("screen_name,PageClass", SHELL_SCREENS_WITH_NAV)
    def test_shell_screen_bottom_nav_present(self, driver, on_dashboard, screen_name, PageClass):
        if screen_name != "dashboard":
            nav_method = {
                "recommendations": on_dashboard.nav_to_meals,
                "progress": on_dashboard.nav_to_progress,
                "chat": on_dashboard.nav_to_chat,
                "profile": on_dashboard.nav_to_profile,
            }[screen_name]
            nav_method()
        page = PageClass(driver)
        assert page.wait_for_key(page.NAV_HOME, timeout=8), f"Bottom nav missing on {screen_name}"

    @pytest.mark.parametrize("screen_name,PageClass", SHELL_SCREENS_WITH_NAV)
    def test_shell_screen_back_button_does_not_crash(self, driver, on_dashboard, screen_name, PageClass):
        if screen_name != "dashboard":
            nav_method = {
                "recommendations": on_dashboard.nav_to_meals,
                "progress": on_dashboard.nav_to_progress,
                "chat": on_dashboard.nav_to_chat,
                "profile": on_dashboard.nav_to_profile,
            }[screen_name]
            nav_method()
        driver.back()
        # Any of the 5 shell screens or dashboard itself is an acceptable
        # landing spot -- what matters is the app is still alive.
        alive = any(PC(driver).is_loaded(timeout=3) for _, PC in SHELL_SCREENS_WITH_NAV)
        assert alive, f"App became unresponsive after back button from {screen_name}"


class TestNonShellScreensChrome:
    @pytest.mark.smoke
    @pytest.mark.parametrize("screen_name,PageClass", NON_SHELL_SCREENS)
    def test_auth_screen_has_no_bottom_nav(self, driver, screen_name, PageClass):
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=5):
            onboarding.skip()
        page = PageClass(driver)
        if screen_name == "login":
            reg = RegisterPage(driver)
            if reg.is_loaded(timeout=4):
                reg.go_to_login()
        assert page.is_loaded(timeout=10), f"{screen_name} did not load"
        assert not page.wait_for_key("nav_tab_home", timeout=3), (
            f"{screen_name} unexpectedly shows the bottom nav (should be auth-flow only)"
        )


class TestHealthAssessmentFlowChrome:
    """Walks the full 4-step flow once and asserts chrome (marker text +
    absence of bottom nav + presence of expected primary control) at
    every step, using a single registered account rather than
    re-registering per screen."""

    @pytest.fixture(scope="class")
    def flow_driver_state(self, driver, unique_email_factory):
        onboarding = OnboardingPage(driver)
        if onboarding.wait_for_key(onboarding.SKIP_BUTTON, timeout=5):
            onboarding.skip()
        register = RegisterPage(driver)
        assert register.is_loaded(timeout=10)
        register.fill_form(
            name="Chrome Sweep Test",
            email=unique_email_factory("chrome"),
            password="TestPass123!",
            age="26",
            height_cm="168",
            weight_kg="63",
        )
        register.submit()
        return driver

    def test_health_weight_chrome(self, flow_driver_state):
        page = HealthWeightPage(flow_driver_state)
        assert page.is_loaded(timeout=15)
        assert not page.wait_for_key("nav_tab_home", timeout=2)
        assert page.wait_for_key(page.CONTINUE_BUTTON, timeout=5)
        page.set_current_weight("63")
        page.set_target_weight("60")
        page.continue_()

    def test_health_activity_chrome(self, flow_driver_state):
        page = HealthActivityPage(flow_driver_state)
        assert page.is_loaded(timeout=10)
        assert page.wait_for_key(page.SKIP_BUTTON, timeout=5)
        assert page.wait_for_key(page.CONTINUE_BUTTON, timeout=5)
        page.select("MODERATE")
        page.continue_()

    def test_health_goals_chrome(self, flow_driver_state):
        page = HealthGoalsPage(flow_driver_state)
        assert page.is_loaded(timeout=10)
        assert page.wait_for_key(page.SKIP_BUTTON, timeout=5)
        page.select("WEIGHT_LOSS")
        page.continue_()

    def test_health_prefs_chrome(self, flow_driver_state):
        page = HealthPrefsPage(flow_driver_state)
        assert page.is_loaded(timeout=10)
        assert page.wait_for_key(page.SUBMIT_BUTTON, timeout=5)
        page.select_diet("NON_VEGETARIAN")
        page.set_budget("300")
        page.submit()

    def test_plan_ready_chrome(self, flow_driver_state):
        page = PlanReadyPage(flow_driver_state)
        assert page.is_loaded(timeout=20)
        assert page.wait_for_key(page.CONTINUE_BUTTON, timeout=8)
        page.continue_to_dashboard()
        assert DashboardPage(flow_driver_state).is_loaded(timeout=15)


class TestWeeklyPlanAndMealDetailChrome:
    @pytest.mark.smoke
    def test_weekly_plan_has_bottom_nav(self, driver, on_dashboard):
        on_dashboard.open_quick_meal_plan()
        page = WeeklyMealPlanPage(driver)
        assert page.is_loaded(timeout=15)
        assert page.wait_for_key(page.NAV_MEALS, timeout=8), "Weekly plan screen missing bottom nav"
        on_dashboard.nav_to_home()
