"""
Chrome WebDriver factory.

Learned-the-hard-way rules baked in here:
- GitHub's ubuntu-latest runner ships a pre-installed /usr/bin/chromedriver
  that is frequently version-mismatched against whatever Chrome version gets
  installed alongside it. Selenium Manager can end up preferring that stale
  PATH binary, which causes exactly the kind of widespread, non-deterministic
  TimeoutExceptions this suite hit in its first CI run (elements "never
  becoming visible" on completely standard, correct locators - even on
  public, unauthenticated pages). The fix: never let Selenium Manager guess.
  CI installs Chrome AND a version-matched chromedriver together via
  browser-actions/setup-chrome's `install-chromedriver: true`, exports both
  paths, and we wire the driver path explicitly via Service(executable_path=...)
  below so there's no ambiguity about which binary gets used.
- Headless uses the new `--headless=new` flag (old `--headless` renders
  differently for some layout/responsive assertions).
- A fixed, deterministic window size is set explicitly rather than relying on
  the OS default, so responsive/breakpoint tests are reproducible in CI.
"""

import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from config import HEADLESS


def build_chrome_options(window_size: tuple[int, int] = (1440, 900)) -> Options:
    opts = Options()

    if HEADLESS:
        opts.add_argument("--headless=new")

    opts.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--log-level=3")
    opts.add_argument("--remote-allow-origins=*")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    chrome_path = os.environ.get("CHROME_PATH")
    if chrome_path:
        opts.binary_location = chrome_path

    return opts


def build_driver(window_size: tuple[int, int] = (1440, 900)) -> webdriver.Chrome:
    options = build_chrome_options(window_size)

    # Explicit, version-matched driver takes priority over Selenium Manager's
    # own resolution (which is what caused the chromedriver/Chrome version
    # mismatch instability in CI). Falls back to plain Service() - and
    # therefore Selenium Manager - only when CHROMEDRIVER_PATH isn't set,
    # e.g. for local runs on a developer machine.
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    service = Service(executable_path=chromedriver_path) if chromedriver_path else Service()

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver
