"""
FitFuelBottomNav mixin.

Note on final_year.md item 13 (Material 3 NavigationBar dual-label
crossfade forcing ValueKey-based finding instead of by_text): re-verified
against this app's actual widget (widgets/app_widgets.dart ->
FitFuelBottomNav) and it does NOT apply here -- FitFuel's bottom nav is a
plain custom Row of GestureDetector + single Text per tab, not a Material
3 NavigationBar, so there is no crossfade / no duplicate-Text-widget
ambiguity. We still key every tab (nav_tab_home / nav_tab_meals /
nav_tab_progress / nav_tab_profile) because a handful of
tabs share the same Icon/Column structure and a key is more robust than
a positional index regardless of the crossfade issue -- but it's included
here as a deliberate best-practice choice, not a workaround for a bug
this app doesn't have. Documented so this reads as a verified "not
applicable" rather than a silently skipped lesson.
"""
from page_objects.base_page import BasePage


class NavBarMixin(BasePage):
    NAV_HOME = "nav_tab_home"
    NAV_MEALS = "nav_tab_meals"
    NAV_PROGRESS = "nav_tab_progress"
    NAV_PROFILE = "nav_tab_profile"

    def nav_to_home(self):
        self.tap_key(self.NAV_HOME)

    def nav_to_meals(self):
        self.tap_key(self.NAV_MEALS)

    def nav_to_progress(self):
        self.tap_key(self.NAV_PROGRESS)

    def nav_to_profile(self):
        self.tap_key(self.NAV_PROFILE)

    def is_nav_tab_visible(self, tab_key: str) -> bool:
        return self.wait_for_key(tab_key, timeout=5)
