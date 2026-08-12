from selenium.webdriver.common.by import By

from page_objects.layout import LayoutNav


class ChatPage(LayoutNav):
    MESSAGES_CONTAINER = (By.ID, "chat-messages")
    INPUT = (By.ID, "chat-input")
    SEND_BTN = (By.ID, "chat-send")

    def open(self):
        self.open_route("chat")
        return self

    def is_loaded(self) -> bool:
        return self.exists(*self.INPUT, timeout=8)

    def type_message(self, text: str):
        self.type_text(*self.INPUT, text)
        return self

    def send(self):
        self.click(*self.SEND_BTN)
        return self

    def send_message(self, text: str):
        self.type_message(text)
        self.send()
        return self

    def input_placeholder(self) -> str:
        return self.find(*self.INPUT).get_attribute("placeholder")

    def is_send_disabled(self) -> bool:
        return self.find(*self.SEND_BTN).get_attribute("disabled") is not None
