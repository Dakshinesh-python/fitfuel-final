"""
BasePage - shared, explicit-wait-only helpers for every page object.

HARD RULES enforced by construction (see docs/final_year testing prompt):
- No time.sleep() inside test bodies or page objects. Every wait here is a
  WebDriverWait + expected_conditions call with a bounded timeout.
- No `assert x or True` / bare `assert True` anywhere in this suite. Grep
  before trusting a green run:
      grep -rn "or True\\|assert True" selenium-tests/tests/
"""

from __future__ import annotations

import logging

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import (
    BASE_URL,
    DEFAULT_TIMEOUT,
    FAKE_JWT_TOKEN,
    LONG_TIMEOUT,
    SHORT_TIMEOUT,
    TOKEN_STORAGE_KEY,
    route_url,
)

logger = logging.getLogger("fitfuel.selenium")


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def open_route(self, route_name: str):
        url = route_url(route_name)
        self.driver.get(url)
        return self

    def open_base(self):
        self.driver.get(BASE_URL)
        return self

    def current_path(self) -> str:
        """Return the path portion of the current URL relative to BASE_URL."""
        url = self.driver.current_url
        if url.startswith(BASE_URL):
            return url[len(BASE_URL):]
        return url

    def wait_for_url_contains(self, fragment: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.url_contains(fragment))
            return True
        except TimeoutException:
            return False

    # ------------------------------------------------------------------
    # Element helpers (explicit waits only)
    # ------------------------------------------------------------------
    def find(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )

    def find_clickable(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )

    def find_visible(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, selector))
        )

    def find_all(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            return []
        return self.driver.find_elements(by, selector)

    def exists(self, by: str, selector: str, timeout: int = SHORT_TIMEOUT) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            return False

    def is_visible(self, by: str, selector: str, timeout: int = SHORT_TIMEOUT) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            return False

    def type_text(self, by: str, selector: str, text: str, clear_first: bool = True, timeout: int = DEFAULT_TIMEOUT):
        el = self.find_visible(by, selector, timeout)
        if clear_first:
            el.clear()
        if text:
            el.send_keys(text)
        return el

    def click(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT):
        el = self.find_clickable(by, selector, timeout)
        try:
            el.click()
        except StaleElementReferenceException:
            el = self.find_clickable(by, selector, timeout)
            el.click()
        return el

    def text_of(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        return self.find_visible(by, selector, timeout).text

    def get_value(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        return self.find(by, selector, timeout).get_attribute("value") or ""

    def wait_gone(self, by: str, selector: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            return False

    def body_text_contains(self, phrase: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: phrase.lower() in d.find_element(By.TAG_NAME, "body").text.lower()
            )
            return True
        except TimeoutException:
            return False

    # ------------------------------------------------------------------
    # Auth (two-tier: real UI attempt with fallback to token injection)
    # ------------------------------------------------------------------
    def inject_auth_token(self, token: str = FAKE_JWT_TOKEN):
        """
        Force an authenticated client-side session without a live backend.

        RequireAuth (App.tsx) only checks `localStorage.getItem('fitfuel_token')`
        truthiness before rendering a protected page - it performs no
        client-side signature validation. This lets the suite exercise every
        route guard, nav item, and protected-page shell deterministically,
        independent of whether the live API is reachable from CI.
        """
        # localStorage is only reachable once we're on an app origin.
        self.driver.get(BASE_URL + "login")
        self.driver.execute_script(
            "window.localStorage.setItem(arguments[0], arguments[1]);",
            TOKEN_STORAGE_KEY,
            token,
        )
        return self

    def clear_auth_token(self):
        if not self.driver.current_url.startswith("http"):
            self.driver.get(BASE_URL + "login")
        self.driver.execute_script(
            "window.localStorage.removeItem(arguments[0]);", TOKEN_STORAGE_KEY
        )
        return self

    def get_stored_token(self):
        try:
            return self.driver.execute_script(
                "return window.localStorage.getItem(arguments[0]);", TOKEN_STORAGE_KEY
            )
        except Exception:
            return None

    def login_via_ui_or_inject(self, email: str, password: str, timeout: int = LONG_TIMEOUT) -> str:
        """
        Two-tier login fixture.

        Tier 1: attempt a real UI login against whatever API base the build
        was compiled with; wait briefly for a redirect to /dashboard.
        Tier 2: if that doesn't happen (API unreachable / account doesn't
        exist in this ephemeral environment - expected in the default CI
        configuration, see config.py docstring), inject a token directly and
        hard-navigate to /dashboard.

        Returns "ui" or "injected" so tests / logs can record which path ran.
        """
        self.open_route("login")
        self.type_text(By.ID, "email", email)
        self.type_text(By.ID, "password", password)
        self.click(By.CSS_SELECTOR, "button[type='submit']")

        if self.wait_for_url_contains("dashboard", timeout=timeout):
            logger.info("login_via_ui_or_inject: real UI login succeeded for %s", email)
            return "ui"

        logger.info(
            "login_via_ui_or_inject: UI login did not redirect within %ss for %s, "
            "falling back to token injection (expected when no live backend is reachable)",
            timeout,
            email,
        )
        self.inject_auth_token()
        self.driver.get(BASE_URL + "dashboard")
        return "injected"

    def is_authenticated_client_side(self) -> bool:
        return bool(self.get_stored_token())
