from page_objects.nav_bar import NavBarMixin


class ProgressPage(NavBarMixin):
    RETRY_BUTTON = "progress_retry_button"
    LOG_BUTTON = "progress_log_button"
    WEIGHT_FIELD = "progress_log_weight_field"
    CALORIES_FIELD = "progress_log_calories_field"
    PROTEIN_FIELD = "progress_log_protein_field"
    CARBS_FIELD = "progress_log_carbs_field"
    FAT_FIELD = "progress_log_fat_field"
    NOTES_FIELD = "progress_log_notes_field"
    ERROR_TEXT = "progress_log_error_text"
    SUBMIT_BUTTON = "progress_log_submit_button"

    def is_loaded(self, timeout: float = 15) -> bool:
        return self.is_on_screen("progress", timeout=timeout)

    def has_load_error(self, timeout: float = 5) -> bool:
        return self.wait_for_key(self.RETRY_BUTTON, timeout)

    def retry_load(self) -> None:
        self.tap_key(self.RETRY_BUTTON)

    def open_log_sheet(self) -> None:
        self.tap_key(self.LOG_BUTTON)

    def fill_log_entry(
        self,
        weight_kg: str = "",
        calories: str = "",
        protein_g: str = "",
        carbs_g: str = "",
        fat_g: str = "",
        notes: str = "",
    ) -> None:
        if weight_kg:
            self.enter_text_by_key(self.WEIGHT_FIELD, weight_kg)
        if calories:
            self.enter_text_by_key(self.CALORIES_FIELD, calories)
        if protein_g:
            self.enter_text_by_key(self.PROTEIN_FIELD, protein_g)
        if carbs_g:
            self.enter_text_by_key(self.CARBS_FIELD, carbs_g)
        if fat_g:
            self.enter_text_by_key(self.FAT_FIELD, fat_g)
        if notes:
            self.enter_text_by_key(self.NOTES_FIELD, notes)

    def submit_log(self) -> None:
        self.tap_key(self.SUBMIT_BUTTON)

    def has_log_error(self, timeout: float = 5) -> bool:
        return self.wait_for_key(self.ERROR_TEXT, timeout)
