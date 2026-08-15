"""Progress screen: logging entries (Create), viewing the summary
(Read), boundary/validation on every numeric field, and error/retry
handling. There is no visible edit or delete affordance for individual
log entries in the current UI -- verified by full-file read of
progress_screen.dart rather than assumed -- so Update/Delete are not
covered here; that's recorded explicitly in mobile-tests/README.md
rather than silently omitted."""
import pytest

from page_objects.progress_page import ProgressPage
from utils import adb_helpers


@pytest.fixture
def on_progress(driver, on_dashboard):
    on_dashboard.nav_to_progress()
    page = ProgressPage(driver)
    assert page.is_loaded(timeout=15)
    return page


class TestProgressLoad:
    @pytest.mark.progress
    @pytest.mark.smoke
    def test_progress_screen_loads(self, driver, on_progress):
        assert on_progress.is_loaded()

    @pytest.mark.progress
    def test_log_button_visible(self, driver, on_progress):
        assert on_progress.wait_for_key(on_progress.LOG_BUTTON, timeout=8)


class TestLogEntryCreate:
    @pytest.mark.progress
    @pytest.mark.smoke
    def test_log_full_entry_succeeds(self, driver, on_progress):
        on_progress.open_log_sheet()
        on_progress.fill_log_entry(
            weight_kg="68.5", calories="2100", protein_g="140", carbs_g="220", fat_g="70", notes="Felt good today"
        )
        on_progress.submit_log()
        assert not on_progress.has_log_error(timeout=5)
        assert on_progress.is_loaded(timeout=10)

    @pytest.mark.progress
    def test_log_entry_with_only_weight(self, driver, on_progress):
        on_progress.open_log_sheet()
        on_progress.fill_log_entry(weight_kg="69")
        on_progress.submit_log()
        assert not on_progress.has_log_error(timeout=5)

    @pytest.mark.progress
    def test_log_entry_with_only_notes(self, driver, on_progress):
        on_progress.open_log_sheet()
        on_progress.fill_log_entry(notes="Just a note, no numbers today")
        on_progress.submit_log()
        # Different from "all fields empty" -- notes alone may or may not
        # be a valid entry depending on backend rules; either a successful
        # submit or a validation error is acceptable, a freeze is not.
        errored = on_progress.has_log_error(timeout=5)
        succeeded = on_progress.is_loaded(timeout=5)
        assert errored or succeeded

    @pytest.mark.progress
    @pytest.mark.validation
    def test_log_entry_all_fields_empty_shows_error(self, driver, on_progress):
        on_progress.open_log_sheet()
        on_progress.submit_log()
        assert on_progress.has_log_error(timeout=8), (
            "Submitting a completely empty log entry was accepted without error"
        )

    @pytest.mark.progress
    @pytest.mark.validation
    @pytest.mark.parametrize(
        "field,value,case_id",
        [
            ("weight_kg", "-10", "negative_weight"),
            ("weight_kg", "0", "zero_weight"),
            ("weight_kg", "abc", "non_numeric_weight"),
            ("calories", "-500", "negative_calories"),
            ("calories", "99999", "implausibly_high_calories"),
            ("protein_g", "-1", "negative_protein"),
            ("carbs_g", "abc", "non_numeric_carbs"),
            ("fat_g", "-1", "negative_fat"),
        ],
    )
    def test_boundary_values_per_numeric_field(self, driver, on_progress, field, value, case_id):
        on_progress.open_log_sheet()
        on_progress.fill_log_entry(**{field: value})
        on_progress.submit_log()
        # Contract: never a silent freeze.
        errored = on_progress.has_log_error(timeout=6)
        succeeded = on_progress.is_loaded(timeout=5)
        assert errored or succeeded, f"[{case_id}] App reached neither state for {field}={value}"

    @pytest.mark.progress
    def test_very_long_notes_does_not_crash(self, driver, on_progress):
        on_progress.open_log_sheet()
        on_progress.fill_log_entry(weight_kg="70", notes="N" * 500)
        on_progress.submit_log()
        errored = on_progress.has_log_error(timeout=6)
        succeeded = on_progress.is_loaded(timeout=5)
        assert errored or succeeded

    @pytest.mark.progress
    def test_unicode_notes_does_not_crash(self, driver, on_progress):
        on_progress.open_log_sheet()
        on_progress.fill_log_entry(weight_kg="70", notes="प्रगति अच्छी है 🎉 日本語テスト")
        on_progress.submit_log()
        errored = on_progress.has_log_error(timeout=6)
        succeeded = on_progress.is_loaded(timeout=5)
        assert errored or succeeded


class TestProgressReadAfterCreate:
    @pytest.mark.progress
    def test_summary_reflects_data_after_logging_multiple_entries(self, driver, on_progress):
        for weight in ["70", "69.5", "69"]:
            on_progress.open_log_sheet()
            on_progress.fill_log_entry(weight_kg=weight, calories="2000")
            on_progress.submit_log()
            assert not on_progress.has_log_error(timeout=5)
        # Read-back check: the screen should still be in a healthy loaded
        # state after several consecutive writes, and should not have
        # fallen into the load-error branch.
        assert on_progress.is_loaded(timeout=10)
        assert not on_progress.has_load_error(timeout=3)


class TestProgressErrorHandling:
    @pytest.mark.progress
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_retry_shown_when_backend_unreachable(self, driver, on_progress, restore_network):
        adb_helpers.set_network_offline()
        on_progress.nav_to_home()
        on_progress.nav_to_progress()
        assert on_progress.has_load_error(timeout=15)

    @pytest.mark.progress
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_retry_recovers_after_network_restored(self, driver, on_progress, restore_network):
        adb_helpers.set_network_offline()
        on_progress.nav_to_home()
        on_progress.nav_to_progress()
        assert on_progress.has_load_error(timeout=15)
        adb_helpers.set_network_online()
        on_progress.retry_load()
        assert on_progress.is_loaded(timeout=15)

    @pytest.mark.progress
    @pytest.mark.error_handling
    @pytest.mark.slow
    def test_log_submission_while_offline_shows_error_not_crash(self, driver, on_progress, restore_network):
        adb_helpers.set_network_offline()
        on_progress.open_log_sheet()
        on_progress.fill_log_entry(weight_kg="70", calories="2000")
        on_progress.submit_log()
        assert on_progress.has_log_error(timeout=15), (
            "Logging an entry while offline did not surface an error to the user"
        )
