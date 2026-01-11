"""OpenAI-compatible provider implementation."""

import json
from typing import AsyncIterator, Dict, List, Tuple

import httpx

from .provider import BaseLLMProvider


class OpenAICompatibleProvider(BaseLLMProvider):
    def _base_url(self) -> str:
        return self.endpoint_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def list_models(self) -> Tuple[List[str], str]:
        url = f"{self._base_url()}/models"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            return [], f"HTTP {exc.response.status_code}: {exc.response.text}"
        except Exception as exc:
            return [], str(exc)

        models = []
        for item in payload.get("data", []) or []:
            model_id = item.get("id")
            if model_id:
                models.append(model_id)
        return models, ""

    async def test_connection(self) -> Tuple[bool, str]:
        models, error = await self.list_models()
        if error:
            return False, error
        if not models:
            return True, "Connected, but no models returned."
        return True, "Connected."

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        url = f"{self._base_url()}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream("POST", url, json=payload, headers=self._headers()) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data = line[len("data:"):].strip()
                    else:
                        data = line.strip()

                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices") or []
                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield content
