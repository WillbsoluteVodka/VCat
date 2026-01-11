"""
Chat handler for VCat dialog feature.
Manages chat history and message processing.
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional

import httpx
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from .commands import get_response, handle_command
from src.llm.config import load_llm_config, get_default_provider
from src.llm.personality import build_system_prompt
from src.llm.security import decrypt_api_key
from src.llm.session import ChatSession
from src.llm.openai_provider import OpenAICompatibleProvider


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    text: str
    is_user: bool  # True if from user, False if from cat


@dataclass
class SendResult:
    kind: str  # "command", "error", "stream"
    response: str = ""
    action: Optional[str] = None


class LLMStreamWorker(QObject):
    chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, provider, messages, temperature, max_tokens):
        super().__init__()
        self._provider = provider
        self._messages = messages
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            asyncio.run(self._run_async())
        except Exception as exc:
            self.error.emit(self._friendly_error(exc))

    async def _run_async(self):
        response_text = ""
        async for chunk in self._provider.chat_stream(
            self._messages,
            self._temperature,
            self._max_tokens,
        ):
            if self._cancelled:
                break
            response_text += chunk
            self.chunk.emit(chunk)
        if not self._cancelled:
            self.finished.emit(response_text)

    def _friendly_error(self, exc: Exception) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return "连接超时喵～请检查网络设置喵～"
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            if status in (401, 403):
                return "API Key 无效喵～请检查设置喵～"
            return "服务器开小差了喵～稍后再试喵～"
        return f"出错了喵～{exc}"


class ChatHandler(QObject):
    """
    Handles chat messages and generates responses.
    Maintains chat history for the current session.
    """

    response_chunk = pyqtSignal(str)
    response_complete = pyqtSignal(str)
    response_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.history: List[ChatMessage] = []
        self._load_config()
        self._stream_thread: Optional[QThread] = None
        self._stream_worker: Optional[LLMStreamWorker] = None

    def _load_config(self):
        self.config = load_llm_config()
        prompt = build_system_prompt(
            self.config.get("language"),
            self.config.get("custom_personality"),
        )
        self.session = ChatSession(prompt)

    def reload_config(self):
        self._load_config()

    def is_configured(self) -> bool:
        provider = get_default_provider(self.config)
        if not provider:
            return False
        if not provider.get("endpoint_url") or not provider.get("model_name"):
            return False
        return True

    def _build_provider(self):
        provider = get_default_provider(self.config)
        if not provider:
            return None, "请先配置 API 设置喵～"

        endpoint = provider.get("endpoint_url") or ""
        model = provider.get("model_name") or ""
        encrypted_key = provider.get("encrypted_api_key") or ""
        api_key = decrypt_api_key(encrypted_key)

        if encrypted_key and not api_key:
            return None, "API Key 解密失败喵～请重新保存设置喵～"

        if not endpoint or not model:
            return None, "配置不完整喵～请检查设置喵～"

        timeout = int(self.config.get("timeout_seconds", 30))
        return OpenAICompatibleProvider(endpoint, api_key, model, timeout), ""

    def send_message(self, user_input: str) -> SendResult:
        """
        Process user input and generate a response.
        Returns a SendResult indicating command, error, or streaming mode.
        """
        user_input = (user_input or "").strip()
        if not user_input:
            return SendResult("error", "请输入内容喵～")

        command_result = handle_command(user_input)
        if command_result.handled:
            if command_result.action == "new_session":
                self.clear_history()
            return SendResult("command", command_result.response, command_result.action)

        if not self.is_configured():
            return SendResult("error", "需要先完成 LLM 配置喵～", "open_setup")

        provider, error = self._build_provider()
        if error:
            return SendResult("error", error, "open_setup")

        if self._stream_thread and self._stream_thread.isRunning():
            return SendResult("error", "我还在回复中喵～稍等一下喵～")

        self.history.append(ChatMessage(text=user_input, is_user=True))
        self.session.add_user_message(user_input)

        self._start_stream(provider)
        return SendResult("stream")

    def _start_stream(self, provider):
        temperature = float(self.config.get("temperature", 0.7))
        max_tokens = int(self.config.get("max_tokens", 1024))

        self._stream_worker = LLMStreamWorker(
            provider,
            self.session.messages(),
            temperature,
            max_tokens,
        )
        self._stream_thread = QThread()
        self._stream_worker.moveToThread(self._stream_thread)

        self._stream_thread.started.connect(self._stream_worker.run)
        self._stream_worker.chunk.connect(self.response_chunk.emit)
        self._stream_worker.finished.connect(self._on_stream_finished)
        self._stream_worker.error.connect(self._on_stream_error)

        self._stream_worker.finished.connect(self._stream_thread.quit)
        self._stream_worker.error.connect(self._stream_thread.quit)
        self._stream_thread.finished.connect(self._cleanup_stream)

        self._stream_thread.start()

    def _on_stream_finished(self, response_text: str):
        response_text = response_text or get_response("")
        self.history.append(ChatMessage(text=response_text, is_user=False))
        self.session.add_assistant_message(response_text)
        self.response_complete.emit(response_text)

    def _on_stream_error(self, message: str):
        self.response_error.emit(message)

    def _cleanup_stream(self):
        if self._stream_worker:
            self._stream_worker.deleteLater()
        self._stream_worker = None
        if self._stream_thread:
            self._stream_thread.deleteLater()
        self._stream_thread = None

    def get_history(self) -> List[ChatMessage]:
        """Return the full chat history."""
        return self.history

    def clear_history(self):
        """Clear all chat history."""
        self.history = []
        prompt = build_system_prompt(
            self.config.get("language"),
            self.config.get("custom_personality"),
        )
        self.session.reset(prompt)
