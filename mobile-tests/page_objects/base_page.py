"""
Base page object shared by every screen's page object.

Two hard constraints drive the design here (see final_year.md items 11-12,
re-verified against this repo rather than assumed):

  * appium-flutter-driver has NO page_source and no URL/route concept --
    `driver.page_source` returns HTTP 405 permanently. There is nothing to
    parse. Instead we keep a small map of one distinctive, always-visible
    string per screen (`_ROUTE_TEXT_MARKERS` below) and match against
    that. It's a heuristic, not a guarantee -- see the docstring on
    `is_on_screen()` for the one known collision in this app.

  * `.text` only resolves for Text/EditableText widgets. Calling it on an
    IconButton, Container, GestureDetector etc. blocks for the FULL
    command timeout on every poll before failing. `is_displayed()` is the
    correct generic "does this exist" check; `.text` is reserved for
    cases where the test genuinely needs the string content of a Text
    widget.
"""
from __future__ import annotations

import time

from appium_flutter_finder import FlutterFinder
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

import config

finder = FlutterFinder()

# One distinctive, always-rendered string per screen. Used only for loose
# "did navigation land where we expected" smoke checks -- NOT relied on
# for anything that needs to be airtight, because appium-flutter-driver
# gives us nothing better to work with.
#
# KNOWN COLLISION (documented rather than hidden, per the "test what's
# actually there" principle): the dashboard's "Meal Plan" quick-access
# card and the Weekly Meal Plan screen's own AppBar title are both the
# literal string "Meal Plan". Tests that need to disambiguate the two use
# a second, screen-specific marker (see WeeklyMealPlanPage.is_loaded())
# rather than relying on this map alone.
ROUTE_TEXT_MARKERS = {
    "splash": "Intelligent nutrition, effortlessly.",
    "onboarding": "Skip",
    "login": "Enter your details to sign in.",
    "register": "Create your health profile",
    "health-weight": "Let's set your baseline.",
    "health-activity": "What's your daily activity level?",
    "health-goals": "What is your primary goal?",
    "health-prefs": "Dietary Details",
    "plan-ready": "Your Plan is Ready",
    "dashboard": "Quick Access",
    "recommendations": "AI Picks for you",
    "meal-detail": "Macro Breakdown",
    "weekly-plan": "Meal Plan",  # see collision note above
    "progress": "Track your journey",
    "chat": "Nutrition Coach",
    "profile": "Profile",
}


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    # ── low-level element access ───────────────────────────────────────
    def by_key(self, value_key: str):
        return finder.by_value_key(value_key)

    def by_text(self, text: str):
        return finder.by_text(text)

    def by_type(self, widget_type: str):
        return finder.by_type(widget_type)

    def by_tooltip(self, tooltip: str):
        return finder.by_tooltip(tooltip)

    # ── waits / existence checks (is_displayed(), never .text) ─────────
    def is_displayed(self, element_finder, timeout: float = None) -> bool:
        timeout = config.DEFAULT_WAIT_SECONDS if timeout is None else timeout
        deadline = time.time() + timeout
        last_exc = None
        while time.time() < deadline:
            try:
                el = self.driver.find_element("flutter", element_finder)
                if el.is_displayed():
                    return True
            except (
                NoSuchElementException,
                StaleElementReferenceException,
                WebDriverException,
            ) as exc:
                last_exc = exc
            time.sleep(0.3)
        return False

    def wait_for_key(self, value_key: str, timeout: float = None) -> bool:
        return self.is_displayed(self.by_key(value_key), timeout)

    def wait_for_text(self, text: str, timeout: float = None) -> bool:
        return self.is_displayed(self.by_text(text), timeout)

    def is_on_screen(self, route_name: str, timeout: float = None) -> bool:
        """Loose smoke check for "did we land where we expected".
        See ROUTE_TEXT_MARKERS docstring for the one known collision."""
        marker = ROUTE_TEXT_MARKERS[route_name]
        return self.wait_for_text(marker, timeout)

    # ── actions ──────────────────────────────────────────────────────
    def tap_key(self, value_key: str, timeout: float = None) -> None:
        assert self.wait_for_key(value_key, timeout), (
            f"Element with key '{value_key}' never became visible "
            f"within {timeout or config.DEFAULT_WAIT_SECONDS}s"
        )
        self.driver.execute_script("flutter:click", self.by_key(value_key))

    def tap_text(self, text: str, timeout: float = None) -> None:
        assert self.wait_for_text(text, timeout), (
            f"Text '{text}' never became visible within "
            f"{timeout or config.DEFAULT_WAIT_SECONDS}s"
        )
        self.driver.execute_script("flutter:click", self.by_text(text))

    def enter_text_by_key(self, value_key: str, value: str, timeout: float = None) -> None:
        assert self.wait_for_key(value_key, timeout), (
            f"Input field with key '{value_key}' never became visible"
        )
        el = self.driver.find_element("flutter", self.by_key(value_key))
        el.clear()
        el.send_keys(value)

    def text_of_key(self, value_key: str, timeout: float = None) -> str:
        """The one legitimate use of .text -- only ever call this on a
        widget that actually renders text (Text / TextField)."""
        assert self.wait_for_key(value_key, timeout)
        el = self.driver.find_element("flutter", self.by_key(value_key))
        return el.text

    def scroll_down(self) -> None:
        from utils import adb_helpers
        adb_helpers.scroll_down()

    def scroll_up(self) -> None:
        from utils import adb_helpers
        adb_helpers.scroll_up()

    def back(self) -> None:
        self.driver.back()
