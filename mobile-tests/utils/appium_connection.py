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

CORRECTION (found by diffing this project's timeout plumbing against
KrishiIQ's, a sibling project where the equivalent mechanism is known to
work): `set_timeout()` must be called BEFORE the connection object is
constructed, not after. `AppiumConnection.__init__` -> `RemoteConnection.
__init__` builds the urllib3 pool manager eagerly, once, right there in
__init__ (`self._conn = self._get_connection_manager()`), and
`_get_connection_manager()` reads `self.get_timeout()` at that exact
moment. `set_timeout()` is a classmethod that only ever writes the class
attribute for *future* instances -- calling it on an object that already
exists has no effect on that object's already-built pool. The previous
version of `build_session_creation_executor` / `build_short_timeout_executor`
constructed the connection first and called `.set_timeout()` second, which
meant the value never actually reached the pool: `SessionCreationConnection`
silently inherited `AppiumConnection`'s 12s default instead of getting the
intended 60s (session creation was getting LESS headroom than everyday
commands, not more), and `build_short_timeout_executor` only "worked" by
coincidence because 12 already equalled 12 at construction time. Setting
the class-level timeout before constructing (as KrishiIQ's conftest.py
does inline) is what actually wires the value into the pool.
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
    # Set the class-level timeout BEFORE constructing -- the pool manager
    # is built eagerly in __init__ and reads this value at that moment.
    # Setting it after construction (the old code) never reaches the pool.
    SessionCreationConnection.set_timeout(config.SESSION_CREATION_TIMEOUT)
    return SessionCreationConnection(server_url)


def build_short_timeout_executor(server_url: str) -> AppiumConnection:
    # Same fix -- set before constructing. This one happened to produce
    # the right value before (12 == 12 by coincidence with the import-time
    # default), but was fragile: any future change to APPIUM_COMMAND_TIMEOUT
    # that didn't also touch configure_default_timeout() would have silently
    # broken it again.
    AppiumConnection.set_timeout(config.APPIUM_COMMAND_TIMEOUT)
    return AppiumConnection(server_url)


def swap_to_short_timeout(driver, server_url: str) -> None:
    """Call immediately after a session is successfully created. Downgrades
    the driver's command executor from the long session-creation timeout to
    the short everyday-command timeout."""
    driver.command_executor = build_short_timeout_executor(server_url)