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
        return self.wait_for_key(f"chat_quick_reply_{index}", timeout)
