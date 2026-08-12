from selenium.webdriver.common.by import By

from page_objects.layout import LayoutNav


class MealPlanPage(LayoutNav):
    REGENERATE_BTN = (By.ID, "meal-plan-regenerate")
    DOWNLOAD_BTN = (By.ID, "meal-plan-download")

    def open(self):
        self.open_route("meal-plan")
        return self

    def regenerate(self):
        self.click(*self.REGENERATE_BTN)
        return self

    def has_regenerate_button(self, timeout: int = 8) -> bool:
        return self.exists(*self.REGENERATE_BTN, timeout=timeout)

    def has_download_button(self, timeout: int = 8) -> bool:
        return self.exists(*self.DOWNLOAD_BTN, timeout=timeout)

    def click_download(self):
        self.click(*self.DOWNLOAD_BTN)
        return self

    def is_loaded(self) -> bool:
        return self.has_regenerate_button(timeout=8)
