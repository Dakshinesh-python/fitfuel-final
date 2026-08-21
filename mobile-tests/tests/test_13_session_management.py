"""Token persistence and forced-logout behaviour: does the session
survive a background/foreground cycle, does clearing local storage force
a re-login, and does the app stay usable across repeated backgrounding."""
import pytest

from page_objects.auth_pages import LoginPage
from page_objects.dashboard_page import DashboardPage
from utils import adb_helpers, session_helpers


class TestSessionPersistence:
    @pytest.mark.session_mgmt
    @pytest.mark.smoke
    def test_session_survives_background_foreground_cycle(self, driver, on_dashboard):
        adb_helpers.background_app(3)
        assert DashboardPage(driver).is_loaded(timeout=15), (
            "Session was lost after a short background/foreground cycle"
        )

    @pytest.mark.session_mgmt
    @pytest.mark.slow
    def test_session_survives_longer_background_period(self, driver, on_dashboard):
        adb_helpers.background_app(15)
        assert DashboardPage(driver).is_loaded(timeout=15), (
            "Session was lost after a 15s background period"
        )

    @pytest.mark.session_mgmt
    def test_session_survives_navigating_while_backgrounded_and_resumed(self, driver, on_dashboard):
        on_dashboard.nav_to_progress()
        adb_helpers.background_app(3)
        from page_objects.progress_page import ProgressPage

        assert ProgressPage(driver).is_loaded(timeout=15), (
            "App did not resume on the same screen (or at least logged in) after backgrounding mid-navigation"
        )


class TestForcedLogout:
    @pytest.mark.session_mgmt
    @pytest.mark.auth
    def test_clearing_app_data_forces_login_screen(self, driver, logged_in_session):
        session_helpers.force_logged_out_state(driver)
        login = LoginPage(driver)
        assert login.is_loaded(timeout=20), "Clearing app data did not force a return to the login screen"
        login.login(logged_in_session["email"], logged_in_session["password"])
        assert DashboardPage(driver).is_loaded(timeout=15)

    @pytest.mark.session_mgmt
    def test_force_stopping_and_relaunching_preserves_session(self, driver, on_dashboard):
        import config

        # Relaunch via driver.activate_app(), not a raw adb monkey launch
        # -- force_stop_app() kills the Dart process the Appium session's
        # FlutterDriver socket is connected to, and only activate_app()
        # reconnects FlutterDriver to the new process's Observatory port.
        # A raw adb-launched process leaves the *app* running but the
        # *driver* still bound to the dead old connection, so every
        # following flutter:* command fails immediately (confirmed as a
        # real CI bug in session_helpers.force_logged_out_state(), which
        # had the exact same pattern).
        adb_helpers.force_stop_app()
        driver.activate_app(config.APP_PACKAGE)
        assert DashboardPage(driver).is_loaded(timeout=20), (
            "A force-stop + relaunch (not a logout) unexpectedly required re-login -- "
            "session should persist across process death since the token is in SharedPreferences"
        )


class TestRepeatedBackgrounding:
    @pytest.mark.session_mgmt
    @pytest.mark.slow
    def test_ten_rapid_background_foreground_cycles(self, driver, on_dashboard):
        for _ in range(10):
            adb_helpers.background_app(1)
        assert DashboardPage(driver).is_loaded(timeout=15), (
            "App became unstable after 10 rapid background/foreground cycles"
        )
