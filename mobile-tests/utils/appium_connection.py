"""
Two-tier Appium HTTP timeout wrapper.

Why this exists (see mobile-tests/README.md -> "Timeout tuning" for the
full write-up): with Appium-Python-Client==3.1.1 + selenium==4.21.0,
`socket.setdefaulttimeout(N)` does not reliably bound Appium HTTP calls,
and `AppiumClientConfig` (which would be the "obvious" 4.x-style fix)
does not exist in 3.1.1 -- importing it raises ImportError, which kills
an entire pytest collection with zero tests collected. The correct
mechanism at this client version is:

    AppiumConnection.set_timeout(seconds)

called once, at import time, before any session exists --
`AppiumConnection._get_connection_manager()` reads this value when it
builds its urllib3 connection pool.

We use two tiers:
  * a SHORT timeout (config.APPIUM_COMMAND_TIMEOUT) for everyday find /
    tap / text commands, so a single wedged call fails fast instead of
    burning the whole per-test budget, and
  * a LONG timeout (config.SESSION_CREATION_TIMEOUT) used only while
    creating a new session (APK install + Dart Observatory handshake,
    which legitimately takes longer).

After the session is created we swap the driver's command_executor back
to the short-timeout connection.
"""
from appium.webdriver.appium_connection import AppiumConnection

import config


class SessionCreationConnection(AppiumConnection):
    """Same as AppiumConnection but used only for the initial NEW_SESSION
    call, where APK install + Observatory handshake can legitimately take
    longer than the everyday command timeout."""
    pass


def configure_default_timeout():
    """Must be called once at import time, before any Appium session is
    created. Sets the process-wide default used by AppiumConnection's
    connection pool."""
    AppiumConnection.set_timeout(config.APPIUM_COMMAND_TIMEOUT)


def build_session_creation_executor(server_url: str) -> SessionCreationConnection:
    conn = SessionCreationConnection(server_url)
    conn.set_timeout(config.SESSION_CREATION_TIMEOUT)
    return conn


def build_short_timeout_executor(server_url: str) -> AppiumConnection:
    conn = AppiumConnection(server_url)
    conn.set_timeout(config.APPIUM_COMMAND_TIMEOUT)
    return conn


def swap_to_short_timeout(driver, server_url: str) -> None:
    """Call immediately after a session is successfully created. Downgrades
    the driver's command executor from the long session-creation timeout to
    the short everyday-command timeout."""
    driver.command_executor = build_short_timeout_executor(server_url)
