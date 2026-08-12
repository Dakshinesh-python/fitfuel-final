from selenium.webdriver.common.by import By

from page_objects.layout import LayoutNav


class DashboardPage(LayoutNav):
    ERROR_BANNER = (By.CSS_SELECTOR, "[data-testid='dashboard-error']")
    ROOT_MAIN = (By.TAG_NAME, "main")

    def open(self):
        self.open_route("dashboard")
        return self

    def has_data_error(self, timeout: int = 8) -> bool:
        return self.exists(*self.ERROR_BANNER, timeout=timeout)

    def error_text(self) -> str:
        if self.has_data_error(timeout=6):
            return self.text_of(*self.ERROR_BANNER)
        return ""

    def is_shell_rendered(self) -> bool:
        # Page shell (nav + header) rendering is what "protected route granted
        # access" means; the data payload itself legitimately depends on the
        # live API and is asserted separately via has_data_error().
        return self.is_brand_visible()
