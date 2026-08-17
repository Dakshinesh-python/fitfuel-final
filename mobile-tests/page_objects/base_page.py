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

from appium_flutter_finder import FlutterElement, FlutterFinder
from selenium.common.exceptions import WebDriverException

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

    def _element(self, element_finder) -> FlutterElement:
        """Build a FlutterElement directly from a serialized finder.

        appium-flutter-driver does NOT implement the standard /element
        find endpoint (its `locatorStrategies` is only `['key', 'css
        selector']` -- 'flutter' has never been a valid locator strategy,
        in any driver version). The correct way to reference a Flutter
        widget is to construct the element client-side with the base64
        finder itself as the element id, then act on it via the driver's
        `flutter:*` execute-script commands. See appium-flutter-driver's
        own examples/README for this pattern.
        """
        return FlutterElement(self.driver, element_finder)

    # ── waits / existence checks (is_displayed(), never .text) ─────────
    def is_displayed(self, element_finder, timeout: float = None) -> bool:
        timeout = config.DEFAULT_WAIT_SECONDS if timeout is None else timeout
        try:
            # flutter:waitFor blocks (up to timeout ms) until the widget
            # described by element_finder appears, then raises if it
            # never does -- this replaces the old find_element("flutter",
            # ...) polling loop, which failed instantly and identically
            # on every single call because "flutter" is not a supported
            # locator strategy for this driver.
            self.driver.execute_script(
                "flutter:waitFor", element_finder, int(timeout * 1000)
            )
            return True
        except WebDriverException:
            return False
        except (TimeoutError, OSError):
            # A wedged/overloaded Appium server can raise a raw socket-level
            # read timeout (urllib3.exceptions.ReadTimeoutError, a subclass
            # of OSError) that never gets wrapped as a WebDriverException --
            # confirmed against real CI failures where this propagated all
            # the way out of wait_for_key() as an uncaught error instead of
            # a clean False/assertion failure. Treat it the same as "not
            # found within timeout" here.
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
        # NOTE: neither "flutter:click" nor "flutter:tap" is a supported
        # execute_script command in this driver version -- both fail
        # with "Command not support: <name>". Tapping a widget in
        # appium-flutter-driver goes through the *standard* WebDriver
        # element-click command instead: build the FlutterElement (the
        # same way enter_text_by_key()/text_of_key() already do below)
        # and call the ordinary .click() on it -- the driver maps that
        # standard click command onto a Flutter tap internally. This was
        # the single point of failure behind nearly the entire suite
        # (this helper -- along with tap_text() below -- is called by
        # every page object).
        self._element(self.by_key(value_key)).click()

    def tap_text(self, text: str, timeout: float = None) -> None:
        assert self.wait_for_text(text, timeout), (
            f"Text '{text}' never became visible within "
            f"{timeout or config.DEFAULT_WAIT_SECONDS}s"
        )
        self._element(self.by_text(text)).click()

    def enter_text_by_key(self, value_key: str, value: str, timeout: float = None) -> None:
        assert self.wait_for_key(value_key, timeout), (
            f"Input field with key '{value_key}' never became visible"
        )
        el = self._element(self.by_key(value_key))
        el.clear()
        el.send_keys(value)

    def text_of_key(self, value_key: str, timeout: float = None) -> str:
        """The one legitimate use of .text -- only ever call this on a
        widget that actually renders text (Text / TextField)."""
        assert self.wait_for_key(value_key, timeout)
        el = self._element(self.by_key(value_key))
        return el.text

    def scroll_down(self) -> None:
        from utils import adb_helpers
        adb_helpers.scroll_down()

    def scroll_up(self) -> None:
        from utils import adb_helpers
        adb_helpers.scroll_up()

    def back(self) -> None:
        self.driver.back()