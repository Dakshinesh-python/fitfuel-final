from selenium.webdriver.common.by import By

from config import NAV_LABELS, NAV_ROUTES
from page_objects.base_page import BasePage


class LayoutNav(BasePage):
    """Shared side-nav / header behaviors present on every authenticated page."""

    LOGOUT_BTNS = (By.XPATH, "//button[.//text()[contains(.,'Logout')]] | //button[@aria-label='Logout']")
    NAV_LIST = (By.CSS_SELECTOR, "nav ul li a")
    BRAND_HEADING = (By.XPATH, "//h1[contains(text(),'FitFuel AI')]")

    def nav_link(self, route: str):
        return (By.CSS_SELECTOR, f"nav a[href$='/{route}']")

    def click_nav(self, route: str):
        self.click(*self.nav_link(route))
        return self

    def is_nav_link_present(self, route: str, timeout: int = 6) -> bool:
        return self.exists(*self.nav_link(route), timeout=timeout)

    def is_nav_link_active(self, route: str) -> bool:
        el = self.find(*self.nav_link(route))
        cls = el.get_attribute("class") or ""
        return "text-white" in cls

    def nav_link_text(self, route: str) -> str:
        return self.text_of(*self.nav_link(route))

    def logout(self):
        # Desktop or mobile logout button - click whichever is present/visible.
        btns = self.find_all(*self.LOGOUT_BTNS, timeout=8)
        for btn in btns:
            try:
                if btn.is_displayed():
                    btn.click()
                    return self
            except Exception:
                continue
        # Fallback: click the first one regardless of visibility check outcome.
        if btns:
            self.driver.execute_script("arguments[0].click();", btns[0])
        return self

    def is_brand_visible(self) -> bool:
        return self.is_visible(*self.BRAND_HEADING, timeout=6) or self.exists(
            By.XPATH, "//h1[contains(text(),'FitFuel AI')]", timeout=6
        )

    def all_expected_nav_labels_present(self) -> dict:
        result = {}
        for route in NAV_ROUTES:
            result[route] = self.is_nav_link_present(route, timeout=4)
        return result
