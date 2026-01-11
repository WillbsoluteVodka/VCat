"""Abstract provider interface for LLM integrations."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Tuple


class BaseLLMProvider(ABC):
    def __init__(self, endpoint_url: str, api_key: str, model_name: str, timeout_seconds: int):
        self.endpoint_url = (endpoint_url or "").strip()
        self.api_key = api_key or ""
        self.model_name = (model_name or "").strip()
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> Tuple[List[str], str]:
        raise NotImplementedError
