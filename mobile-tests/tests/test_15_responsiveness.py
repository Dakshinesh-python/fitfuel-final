"""Orientation/rotation handling.

[FINDING, not a test] fitfuel_mobile/lib/main.dart's MaterialApp does not
set `darkTheme` or `themeMode` -- the app does not implement dark mode
(verified by source read of main.dart and theme/app_theme.dart). A
dark-mode test suite is therefore intentionally NOT included here rather
than written against a feature that doesn't exist; see README.md ->
"Findings from building this suite" for the full list of these.
"""
import pytest

from page_objects.dashboard_page import DashboardPage
from utils import adb_helpers


class TestOrientationChange:
    @pytest.mark.responsiveness
    @pytest.mark.slow
    def test_dashboard_survives_rotation_to_landscape_and_back(self, driver, on_dashboard, restore_orientation):
        adb_helpers.rotate_landscape()
        assert DashboardPage(driver).is_loaded(timeout=15), "Dashboard did not survive rotation to landscape"
        adb_helpers.rotate_portrait()
        assert DashboardPage(driver).is_loaded(timeout=15), "Dashboard did not survive rotation back to portrait"

    @pytest.mark.responsiveness
    @pytest.mark.slow
    def test_login_screen_survives_rotation(self, driver, logged_in_session, on_dashboard, restore_orientation):
        from utils import session_helpers
        from page_objects.auth_pages import LoginPage

        session_helpers.logout(driver)
        login = LoginPage(driver)
        assert login.is_loaded(timeout=10)
        adb_helpers.rotate_landscape()
        assert login.is_loaded(timeout=10), "Login screen did not survive rotation to landscape"
        adb_helpers.rotate_portrait()
        assert login.is_loaded(timeout=10)
        login.login(logged_in_session["email"], logged_in_session["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)

    @pytest.mark.responsiveness
    @pytest.mark.slow
    def test_progress_log_sheet_survives_rotation(self, driver, on_dashboard, restore_orientation):
        on_dashboard.nav_to_progress()
        from page_objects.progress_page import ProgressPage

        progress = ProgressPage(driver)
        assert progress.is_loaded(timeout=15)
        progress.open_log_sheet()
        adb_helpers.rotate_landscape()
        assert progress.wait_for_key(progress.SUBMIT_BUTTON, timeout=10), (
            "Log-entry submit button not reachable after rotating to landscape mid-entry"
        )
        adb_helpers.rotate_portrait()
