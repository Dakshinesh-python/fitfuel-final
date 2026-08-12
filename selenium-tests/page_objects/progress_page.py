from selenium.webdriver.common.by import By

from page_objects.layout import LayoutNav


class ProgressPage(LayoutNav):
    WEIGHT = (By.ID, "weightKg")
    CALORIES = (By.ID, "caloriesConsumed")
    PROTEIN = (By.ID, "proteinConsumedG")
    CARBS = (By.ID, "carbsConsumedG")
    FAT = (By.ID, "fatConsumedG")
    NOTES = (By.ID, "notes")
    LOG_BTN = (By.ID, "progress-log-btn")

    def open(self):
        self.open_route("progress")
        return self

    def fill_log(self, weight="", calories="", protein="", carbs="", fat="", notes=""):
        if weight:
            self.type_text(*self.WEIGHT, weight)
        if calories:
            self.type_text(*self.CALORIES, calories)
        if protein:
            self.type_text(*self.PROTEIN, protein)
        if carbs:
            self.type_text(*self.CARBS, carbs)
        if fat:
            self.type_text(*self.FAT, fat)
        if notes:
            self.type_text(*self.NOTES, notes)
        return self

    def submit_log(self):
        self.click(*self.LOG_BTN)
        return self

    def is_loaded(self) -> bool:
        return self.exists(*self.WEIGHT, timeout=8)

    def notes_max_length(self):
        return self.find(*self.NOTES).get_attribute("maxlength")
