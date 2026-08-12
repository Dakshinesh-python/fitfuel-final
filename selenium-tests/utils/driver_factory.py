"""
Chrome WebDriver factory.

Learned-the-hard-way rules baked in here:
- Never manually install chromedriver. Selenium 4.6+ ships Selenium Manager,
  which resolves a matching driver automatically. CI installs Chrome itself
  via browser-actions/setup-chrome@v1 (see .github/workflows/selenium-tests.yml)
  and exports CHROME_PATH; we honor that env var if present.
- Headless uses the new `--headless=new` flag (old `--headless` renders
  differently for some layout/responsive assertions).
- A fixed, deterministic window size is set explicitly rather than relying on
  the OS default, so responsive/breakpoint tests are reproducible in CI.
"""

import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver
