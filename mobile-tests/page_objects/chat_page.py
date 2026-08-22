from page_objects.nav_bar import NavBarMixin


class ChatPage(NavBarMixin):
    INPUT_FIELD = "chat_input_field"
    SEND_BUTTON = "chat_send_button"

    def is_loaded(self, timeout: float = 10) -> bool:
        return self.is_on_screen("chat", timeout=timeout)

    def send_message(self, message: str) -> None:
        self.enter_text_by_key(self.INPUT_FIELD, message)
        self.tap_key(self.SEND_BUTTON)

    def tap_quick_reply(self, index: int) -> None:
        self.tap_key(f"chat_quick_reply_{index}")

    def has_quick_reply(self, index: int, timeout: float = 5) -> bool:
        # The quick-reply chips render in a horizontally-scrolling list
        # (chat_screen.dart's itemBuilder over _shownQuickReplies); a
        # chip past the initial viewport width may not be built into
        # the widget tree at all until scrolled into view -- confirmed
        # in CI as the cause of index 2 (the 3rd, rightmost chip)
        # consistently not being found by a bare existence check, while
        # indices 0-1 always were. wait_for_key() alone never scrolls
        # (only tap_key()/tap_text() do, via _scroll_into_view());
        # nudge it here explicitly since this is a pure visibility
        # check, not a tap.
        key = f"chat_quick_reply_{index}"
        found = self.wait_for_key(key, timeout)
        if found:
            return True
        self._scroll_into_view(self.by_key(key), timeout_ms=int(timeout * 1000))
        # 2s was too tight for index 2 specifically (confirmed as a genuine
        # flake, not a missing scroll: 0/1 pass reliably via the same
        # mechanism used elsewhere in the suite) -- the chip is scrolled
        # into the tree by the line above but its own re-render/re-layout
        # can still lag past a 2s recheck under CI load.
        return self.wait_for_key(key, timeout=5)
