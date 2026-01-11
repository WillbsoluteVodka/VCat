"""Session memory for a single chat conversation."""

from typing import List, Dict


class ChatSession:
    def __init__(self, system_prompt: str):
        self._system_prompt = system_prompt
        self._messages: List[Dict[str, str]] = []
        self.reset(system_prompt)

    def reset(self, system_prompt: str = None):
        if system_prompt is not None:
            self._system_prompt = system_prompt
        self._messages = [{"role": "system", "content": self._system_prompt}]

    def add_user_message(self, text: str):
        self._messages.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str):
        self._messages.append({"role": "assistant", "content": text})

    def messages(self) -> List[Dict[str, str]]:
        return list(self._messages)
