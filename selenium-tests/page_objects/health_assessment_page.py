from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from page_objects.layout import LayoutNav


class HealthAssessmentPage(LayoutNav):
    CURRENT_WEIGHT = (By.ID, "currentWeight")
    TARGET_WEIGHT = (By.ID, "targetWeight")
    ACTIVITY_SELECT_XPATH = (By.XPATH, "//select[not(@id)]")  # activity level is the sole unlabelled select
    FITNESS_GOAL_RADIOS = (By.CSS_SELECTOR, "input[name='fitness_goal']")
    DIETARY_PREF_RADIOS = (By.CSS_SELECTOR, "input[name='dietary_preference']")
    ALLERGY_INPUT_XPATH = (By.XPATH, "//input[@type='text' and not(@id)]")
    DAILY_BUDGET = (By.ID, "dailyBudget")
    SUBMIT_BTN = (By.CSS_SELECTOR, "button[type='submit']")

    def open(self):
        self.open_route("health-assessment")
        return self

    def set_current_weight(self, value: str):
        self.type_text(*self.CURRENT_WEIGHT, value)
        return self

    def set_target_weight(self, value: str):
        self.type_text(*self.TARGET_WEIGHT, value)
        return self

    def select_fitness_goal(self, index: int = 0):
        radios = self.find_all(*self.FITNESS_GOAL_RADIOS)
        if radios and index < len(radios):
            self.driver.execute_script("arguments[0].click();", radios[index])
        return self

    def select_dietary_preference(self, index: int = 0):
        radios = self.find_all(*self.DIETARY_PREF_RADIOS)
        if radios and index < len(radios):
            self.driver.execute_script("arguments[0].click();", radios[index])
        return self

    def set_daily_budget(self, value: str):
        self.type_text(*self.DAILY_BUDGET, value)
        return self

    def add_allergy(self, text: str):
        el = self.find_all(*self.ALLERGY_INPUT_XPATH)
        if el:
            el[0].clear()
            el[0].send_keys(text)
            el[0].send_keys("\n")
        return self

    def submit(self):
        self.click(*self.SUBMIT_BTN)
        return self

    def fitness_goal_count(self) -> int:
        return len(self.find_all(*self.FITNESS_GOAL_RADIOS))

    def dietary_preference_count(self) -> int:
        return len(self.find_all(*self.DIETARY_PREF_RADIOS))

    def is_loaded(self) -> bool:
        return self.exists(*self.CURRENT_WEIGHT, timeout=8)
