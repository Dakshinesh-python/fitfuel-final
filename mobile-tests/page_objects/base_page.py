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

THE WEDGE, AND WHY EVERY RAW DRIVER CALL BELOW IS WRAPPED IN
`_recovering()` (root-caused against a real CI run -- see
mobile-tests/README.md -> "The command-queue wedge" for the full writeup
with the annotated Appium server log):

  appium-flutter-driver processes every `flutter:*` command through a
  single serial queue that lives in the Appium SERVER process, tied to
  the WebDriver *session* -- not to the app's Dart process. If a command
  is sent and the Dart side never acks it, our client gives up after
  APPIUM_COMMAND_TIMEOUT (12s) and raises, but the server-side queue
  entry is never cancelled. Every command issued afterwards -- for the
  rest of that Appium session -- queues up behind the dead one and times
  out too, one after another, forever ("Scheduling the 'execute' command
  to the FlutterDriver commands queue. N queue items are already waiting
  for execution." climbing without bound in the server log).

  `conftest.py`'s per-test `_restart_app_between_tests` fixture restarts
  the *app* (terminate_app + activate_app) before every test, which is
  cheap and normally enough to clear a wedge -- but NOT this one, because
  the jammed queue is server/session state, not app-process state. A
  fresh Dart isolate does nothing to un-stick it.

  The one call site that mattered in the real failure this fixes:
  `is_displayed()` already caught driver exceptions and returned False,
  but `tap_key()` / `tap_text()` / `enter_text_by_key()` / `text_of_key()`
  called `.click()` / `.clear()` / `.send_keys()` / `.text` completely
  unguarded. When one of *those* commands is the one that never gets
  acked (confirmed in CI logs: the very first `tap` on
  `login_register_link` in every single one of 4 independent shards),
  the resulting exception propagates straight out of the page object,
  uncaught -- so nothing ever told the driver its session was wedged, and
  every later test in the shard queued up and timed out too. That's the
  actual mechanism behind a run going from "one bad tap" to "223 of 225
  tests failed".

  The fix: every raw driver/element call in this file now goes through
  `_recovering()`, which -- on any of the driver-level exceptions that
  really mean "the Appium session may be wedged" -- immediately tells
  the driver to recreate its whole Appium session (fresh APK
  launch, fresh command queue) before re-raising. The current command
  (and therefore the current test, whose app state was mid-flow when the
  wedge hit) still fails -- that's correct and unavoidable once a wedge
  has actually happened -- but every *later* test now starts against a
  healthy session instead of inheriting the jam. One test failing beats
  223.
"""
from __future__ import annotations

from contextlib import contextmanager

from appium_flutter_finder import FlutterElement, FlutterFinder
from selenium.common.exceptions import WebDriverException
from urllib3.exceptions import HTTPError as Urllib3HTTPError

import config

finder = FlutterFinder()

# Exceptions that mean "this command may have wedged the Appium session's
# single FlutterDriver command queue", not just "this element isn't
# there yet". See the file docstring and Urllib3HTTPError's own note
# below for why each of these three groups is needed -- none of them is
# redundant with the others.
_RECOVERABLE_EXCEPTIONS = (WebDriverException, TimeoutError, OSError, Urllib3HTTPError)

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

    # ── self-healing wrapper for every raw driver/element call ─────────
    @contextmanager
    def _recovering(self):
        """Wrap a single raw driver/element call. If it raises one of the
        exceptions that can mean the Appium session's FlutterDriver
        command queue is now wedged (see file docstring), immediately
        trigger a full session recreate on the way out, before
        re-raising, instead of letting the wedge silently propagate to
        every later test in the shard."""
        try:
            yield
        except _RECOVERABLE_EXCEPTIONS:
            self._recover_from_possible_wedge()
            raise

    def _recover_from_possible_wedge(self) -> None:
        recreate = getattr(self.driver, "recreate", None)
        if callable(recreate):
            try:
                recreate()
            except Exception:
                # Recreating is a best-effort circuit breaker -- if it
                # itself fails, there's nothing more we can do from a
                # page object; let the original exception (already
                # re-raised by the `_recovering()` caller) surface
                # normally and let the next test's own driver fixture /
                # autouse restart fixture deal with a still-dead session.
                pass

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
            # A clean "not found" response from a healthy Appium server
            # (the widget genuinely isn't there within `timeout`) comes
            # back as a normal WebDriverException -- this is the expected
            # outcome of a huge fraction of is_displayed()/wait_for_*()
            # calls (e.g. every `if not dashboard.is_loaded(timeout=3):`
            # style check) and does NOT indicate a wedged session, so it
            # deliberately does not trigger `_recover_from_possible_wedge()`.
            return False
        except (TimeoutError, OSError):
            # Real socket-level timeouts/OSErrors -- the client gave up
            # waiting for a response at all, which is exactly the signal
            # that this command may have wedged the Appium session's
            # single FlutterDriver command queue for every later command
            # (see file docstring). Unlike the WebDriverException branch
            # above, this is NOT a normal "not found" outcome, so it
            # escalates to a session recreate before returning False.
            self._recover_from_possible_wedge()
            return False
        except Urllib3HTTPError:
            # CORRECTION to a previous fix: urllib3.exceptions.ReadTimeoutError
            # (what a wedged/overloaded Appium server actually raises) does
            # NOT inherit from the built-in TimeoutError or OSError despite
            # sharing the name -- confirmed directly against urllib3's
            # source (urllib3.exceptions.ReadTimeoutError -> urllib3.
            # exceptions.TimeoutError -> ... -> HTTPError -> Exception, no
            # relation to the stdlib TimeoutError/OSError hierarchy at
            # all). The `except (TimeoutError, OSError)` added previously
            # never actually caught anything; this exception kept
            # propagating uncaught all the way out of wait_for_key() into
            # conftest.py's fixtures, confirmed against a real CI
            # traceback. Catching urllib3's actual HTTPError base class
            # (which ReadTimeoutError, MaxRetryError, etc. all inherit
            # from) here is the real fix.
            #
            # This is also, concretely, the exception a genuinely wedged
            # command-queue produces (ReadTimeoutError, no response ever
            # comes back) -- same reasoning as the (TimeoutError, OSError)
            # branch above, so it escalates the same way.
            self._recover_from_possible_wedge()
            return False

    def wait_for_key(self, value_key: str, timeout: float = None) -> bool:
        return self.is_displayed(self.by_key(value_key), timeout)

    def _scroll_into_view(self, element_finder, timeout_ms: int = 8000) -> None:
        """Best-effort: bring the target fully into the visible viewport
        before tapping it.

        THE REAL ROOT CAUSE OF THE "login_register_link WEDGE" (see the
        file docstring above and mobile-tests/README.md): it was never
        the Android accessibility service. `flutter:waitFor` only checks
        tree membership, not on-screen visibility, so `wait_for_key()`
        happily reports success for a widget that is laid out below the
        fold inside a `SingleChildScrollView` -- confirmed directly
        against this app's actual login/register screens, both of which
        put their footer link (and, on the longer register form, the
        submit button too) below the fold on a stock Pixel_6 AVD. Tapping
        such a widget via plain `.click()` sends `flutter:tap` with no
        timeout of its own (unlike `flutter:waitFor`, which always
        carries an explicit one), so the command just never resolves --
        that's the actual mechanism behind the command-queue wedge this
        file otherwise recovers from reactively. Enabling TalkBack (what
        CI was missing) never touched this: appium-flutter-driver's
        `key`/`text` finders resolve against the Flutter widget tree via
        the Dart VM service, not Android's accessibility tree, so that
        fix was solving a different, non-existent problem for these
        commands specifically.

        `flutter:scrollIntoView` uses Flutter's own
        `Scrollable.ensureVisible()` under the hood, which is a genuine
        no-op when the target is already on-screen (verified: ~0.1s for
        an already-visible field, same as for one that needed scrolling)
        and carries its own bounded timeout -- so it's safe to call
        unconditionally before every tap rather than only at known
        below-the-fold call sites. Widgets with no `Scrollable` ancestor
        (e.g. bottom-nav items) make the Dart side raise; that just means
        there's nothing to scroll, so swallow and proceed to the tap as
        before.
        """
        with self._recovering():
            try:
                self.driver.execute_script(
                    "flutter:scrollIntoView",
                    element_finder,
                    {"alignment": 0.5, "timeout": timeout_ms},
                )
            except WebDriverException:
                pass

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
        # standard click command onto a Flutter tap internally.
        #
        # This click() call is exactly the command that wedged the whole
        # suite in the CI run this fixes (the `login_register_link` tap
        # -- see file docstring): it was previously unguarded, so the
        # resulting timeout propagated straight out of every test that
        # happened to run after the wedge instead of triggering recovery.
        # `_recovering()` below closes that gap.
        self._scroll_into_view(self.by_key(value_key))
        with self._recovering():
            self._element(self.by_key(value_key)).click()

    def tap_text(self, text: str, timeout: float = None) -> None:
        assert self.wait_for_text(text, timeout), (
            f"Text '{text}' never became visible within "
            f"{timeout or config.DEFAULT_WAIT_SECONDS}s"
        )
        self._scroll_into_view(self.by_text(text))
        with self._recovering():
            self._element(self.by_text(text)).click()

    def enter_text_by_key(self, value_key: str, value: str, timeout: float = None) -> None:
        assert self.wait_for_key(value_key, timeout), (
            f"Input field with key '{value_key}' never became visible"
        )
        el = self._element(self.by_key(value_key))
        with self._recovering():
            el.clear()
            el.send_keys(value)

    def text_of_key(self, value_key: str, timeout: float = None) -> str:
        """The one legitimate use of .text -- only ever call this on a
        widget that actually renders text (Text / TextField)."""
        assert self.wait_for_key(value_key, timeout)
        el = self._element(self.by_key(value_key))
        with self._recovering():
            return el.text

    def scroll_down(self) -> None:
        from utils import adb_helpers
        adb_helpers.scroll_down()

    def scroll_up(self) -> None:
        from utils import adb_helpers
        adb_helpers.scroll_up()

    def back(self) -> None:
        with self._recovering():
            self.driver.back()