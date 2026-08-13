"""
Chrome WebDriver factory.

Learned-the-hard-way rules baked in here (in the order they were found):

1. GitHub's ubuntu-latest runner ships a pre-installed /usr/bin/chromedriver
   that is frequently version-mismatched against whatever Chrome gets
   installed alongside it, and Selenium Manager can end up preferring that
   stale PATH binary. The CI workflow removes it before Chrome/tests ever
   run (see .github/workflows/selenium-tests.yml) - that part matters
   regardless of anything below.

2. Do NOT rely on a third-party action to bundle a "matched" chromedriver.
   An earlier version of this file explicitly wired CHROMEDRIVER_PATH from
   browser-actions/setup-chrome's `install-chromedriver: true` output,
   trying to route around Selenium Manager entirely. That backfired hard:
   it's a known, currently open bug in that action
   (browser-actions/setup-chrome#619) where the Chrome build and the
   bundled chromedriver build can resolve to different versions
   independently of each other - which produced a hard
   `session not created: This version of ChromeDriver only supports
   Chrome version X` error and failed 100% of the suite immediately at
   driver-launch time (worse than the original PATH-shadowing problem it
   was meant to fix, since nothing even reached a page).

   The fix: trust Selenium Manager (bundled with Selenium 4.6+) as the
   PRIMARY path, not something to avoid. Given an explicit
   `binary_location` (CHROME_PATH, set below from the actual Chrome the
   workflow installed), Selenium Manager inspects THAT EXACT binary's real
   version and downloads a correctly matched driver from the official
   Chrome for Testing endpoint at runtime - it doesn't need a second,
   separately-versioned "matched pair" from anywhere else. CHROMEDRIVER_PATH
   is still supported below as an optional manual override (e.g. for a
   pinned local install), but CI no longer sets it.

3. Headless uses the new `--headless=new` flag (old `--headless` renders
   differently for some layout/responsive assertions).

4. A fixed, deterministic window size is set explicitly rather than relying
   on the OS default, so responsive/breakpoint tests are reproducible in CI.
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

    # Points Selenium Manager at the exact Chrome binary this run should
    # use (set by CI to the browser-actions/setup-chrome install). Selenium
    # Manager reads this to determine which driver version to fetch.
    chrome_path = os.environ.get("CHROME_PATH")
    if chrome_path:
        opts.binary_location = chrome_path

    return opts


def build_driver(window_size: tuple[int, int] = (1440, 900)) -> webdriver.Chrome:
    options = build_chrome_options(window_size)

    # CHROMEDRIVER_PATH is an optional manual override only - CI does not
    # set it. Default path is plain Service(), which hands resolution to
    # Selenium Manager against the CHROME_PATH binary configured above.
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    service = Service(executable_path=chromedriver_path) if chromedriver_path else Service()

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver
