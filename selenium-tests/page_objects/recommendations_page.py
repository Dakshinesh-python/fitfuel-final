from selenium.webdriver.common.by import By

from page_objects.layout import LayoutNav


class RecommendationsPage(LayoutNav):
    ACTION_BUTTONS = (By.TAG_NAME, "button")

    def open(self):
        self.open_route("recommendations")
        return self

    def is_loaded(self) -> bool:
        return self.is_brand_visible()

    def button_count(self) -> int:
        return len(self.find_all(*self.ACTION_BUTTONS, timeout=8))
