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
        # "Track your journey" (the ROUTE_TEXT_MARKERS["progress"] text)
        # only renders after 3 parallel backend calls all succeed -- see
        # progress_screen.dart's _buildBody(): while loading it's a bare
        # CircularProgressIndicator (no identifying text or key at all),
        # and on any fetch error it shows the Retry button instead,
        # permanently, with no polling of its own. A transient backend
        # hiccup on this screen's very first load therefore looked
        # identical to "never navigated here at all" -- confirmed in CI
        # as the single largest failure cluster in
        # test_16_form_field_matrices (46 failures, all stuck here,
        # always this account's first-ever visit to Progress). Retrying
        # once via the app's own Retry button before giving up handles
        # that without weakening what is_loaded() actually means (the
        # real, interactive screen is showing) -- unlike treating the
        # error state itself as "loaded", which isn't safe for callers
        # that go on to interact with content (e.g. the Log button)
        # that only exists in the success state.
        if self.is_on_screen("progress", timeout=timeout):
            return True
        if self.wait_for_key(self.RETRY_BUTTON, timeout=3):
            self.tap_key(self.RETRY_BUTTON)
            return self.is_on_screen("progress", timeout=timeout)
        return False

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
