from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    available: bool = False
    configured: bool = False


@dataclass
class GenerationResult:
    text: str = ""
    model: str = ""
    usage: dict = field(default_factory=dict)  # {"prompt_tokens": 0, "completion_tokens": 0}


class BaseLLMAdapter(ABC):
    """Unified interface for all LLM providers."""

    provider: str = "base"

    def __init__(self, api_key: str = "", api_secret: str = "", **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret
        self.kwargs = kwargs

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GenerationResult:
        """Generate a completion. Returns the full response."""
        ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream a completion. Yields text chunks."""
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models for this provider."""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the API credentials are valid."""
        ...

    def get_default_model(self) -> str:
        return ""
