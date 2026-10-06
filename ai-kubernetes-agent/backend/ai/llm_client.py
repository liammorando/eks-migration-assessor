"""LLM Client for OpenRouter API."""

from typing import Any

import httpx
from core.config import get_settings
from core.logging import logger


class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors."""
    def __init__(self, message: str, status_code: int | None = None, response: str | None = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class LLMClient:
    """Client for interacting with OpenRouter API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            logger.warning("OpenRouter API key not configured")

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ai-kubernetes-agent",
            "X-Title": "AI Kubernetes Agent",
        }

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Send chat completion request to OpenRouter."""
        if not self.api_key:
            raise OpenRouterError("OpenRouter API key not configured")

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        headers=self._get_headers(),
                        json=payload,
                    )

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    logger.warning(f"Rate limited, attempt {attempt + 1}/{self.max_retries}")
                    continue

                error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise OpenRouterError(
                    error_msg,
                    status_code=response.status_code,
                    response=response.text,
                )

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout, attempt {attempt + 1}/{self.max_retries}")
            except httpx.RequestError as e:
                last_error = e
                logger.error(f"Request failed: {e}")
                break

        raise OpenRouterError(f"Request failed after {self.max_retries} attempts: {last_error}")

    def chat_completion_sync(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """Synchronous version of chat completion."""
        if not self.api_key:
            raise OpenRouterError("OpenRouter API key not configured")

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        url,
                        headers=self._get_headers(),
                        json=payload,
                    )

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    logger.warning(f"Rate limited, attempt {attempt + 1}/{self.max_retries}")
                    continue

                error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise OpenRouterError(
                    error_msg,
                    status_code=response.status_code,
                    response=response.text,
                )

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Request timeout, attempt {attempt + 1}/{self.max_retries}")
            except httpx.RequestError as e:
                last_error = e
                logger.error(f"Request failed: {e}")
                break

        raise OpenRouterError(f"Request failed after {self.max_retries} attempts: {last_error}")


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
