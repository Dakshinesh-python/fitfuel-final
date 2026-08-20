"""
adb-backed replacements for Appium/flutter-driver commands that the
Flutter automation engine does not implement (see final_year.md, item 10
and the "Confirmed architecture bugs" section -- verified against this
repo's own emulator, same three gaps apply since fitfuel_mobile is also a
plain Flutter app with no custom platform channels for these):

    driver.background_app(N)          -> HTTP 500 "not supported"
    driver.set_network_connection()   -> "setNetworkConnection not supported"
    driver.execute_script("mobile: scrollGesture", ...) -> HTTP 500

All three are driven directly via `adb shell` instead.
"""
import subprocess
import time

import config


def _adb(*args: str, timeout: int = 15) -> subprocess.CompletedProcess:
    # encoding/errors explicit: logcat and shell output can contain bytes
    # that aren't valid in Windows' default cp1252 console encoding (e.g.
    # UTF-8 test data like accented names, or raw device log content),
    # which raised UnicodeDecodeError deep in subprocess's reader thread
    # and cascaded into ERROR results for every test that followed.
    return subprocess.run(
        ["adb", "shell", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def background_app(seconds: float) -> None:
    """Sends the app to background for `seconds`, then relaunches it via
    the launcher category (monkey), mirroring driver.background_app(N)."""
    _adb("input", "keyevent", "KEYCODE_HOME")
    time.sleep(seconds)
    _adb(
        "monkey",
        "-p",
        config.APP_PACKAGE,
        "-c",
        "android.intent.category.LAUNCHER",
        "1",
    )
    time.sleep(1.5)  # let the activity resume before the next command


def set_wifi_enabled(enabled: bool) -> None:
    _adb("svc", "wifi", "enable" if enabled else "disable")


def set_mobile_data_enabled(enabled: bool) -> None:
    _adb("svc", "data", "enable" if enabled else "disable")


def set_network_offline() -> None:
    """Simulates a full network outage for error-handling tests."""
    set_wifi_enabled(False)
    set_mobile_data_enabled(False)
    time.sleep(1)


def set_network_online() -> None:
    set_wifi_enabled(True)
    set_mobile_data_enabled(True)
    time.sleep(2)  # give the emulator's virtual radio a moment to reconnect


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 200) -> None:
    """Replacement for execute_script('mobile: scrollGesture', ...), which
    returns HTTP 500 on appium-flutter-driver (see final_year.md item 10,
    [NEW FINDING])."""
    _adb("input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))


def scroll_down(screen_width: int = 1080, screen_height: int = 2280) -> None:
    swipe(screen_width // 2, int(screen_height * 0.75), screen_width // 2, int(screen_height * 0.25))


def scroll_up(screen_width: int = 1080, screen_height: int = 2280) -> None:
    swipe(screen_width // 2, int(screen_height * 0.25), screen_width // 2, int(screen_height * 0.75))


def force_stop_app() -> None:
    _adb("am", "force-stop", config.APP_PACKAGE)


def clear_app_data() -> None:
    """Wipes the app's SharedPreferences (and everything else), used for
    session-management tests that need a clean logged-out state without a
    full uninstall/reinstall cycle."""
    _adb("pm", "clear", config.APP_PACKAGE)


def set_font_scale(scale: float) -> None:
    """Used by accessibility/responsive-UI tests. Restore to 1.0 afterwards."""
    _adb("settings", "put", "system", "font_scale", str(scale))


def rotate_landscape() -> None:
    _adb("settings", "put", "system", "accelerometer_rotation", "0")
    _adb("settings", "put", "system", "user_rotation", "1")


def rotate_portrait() -> None:
    _adb("settings", "put", "system", "user_rotation", "0")


def pull_logcat(dest_path: str, since_marker: str | None = None) -> None:
    """Dumps the current device logcat buffer to `dest_path` for
    attaching to failed-test reports (device log, distinct from the
    Appium *server* log which conftest.py captures separately)."""
    args = ["logcat", "-d"]
    if since_marker:
        args += ["-T", since_marker]
    result = subprocess.run(
        ["adb", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(result.stdout)


def logcat_time_marker() -> str:
    """Returns a timestamp string usable with `pull_logcat(since_marker=...)`
    so each test's log slice only contains lines from that test."""
    result = subprocess.run(
        ["adb", "shell", "date", "+'%m-%d %H:%M:%S.000'"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    return result.stdout.strip().strip("'")
