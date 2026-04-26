from llm.base import BaseLLMAdapter, ModelInfo
from llm.custom import GenericAdapter
from llm.custom_store import load_custom_models
from config import settings


class ModelRegistry:
    """Central registry for all LLM adapters. Manages adapter instances and model discovery."""

    def __init__(self):
        self._adapters: dict[str, BaseLLMAdapter] = {}
        self._model_map: dict[str, BaseLLMAdapter] = {}
        self._initialized = False

    def register(self, adapter: BaseLLMAdapter) -> None:
        self._adapters[adapter.provider] = adapter

    def unregister(self, provider: str) -> None:
        self._adapters.pop(provider, None)
        # Clean model map entries for this provider
        self._model_map = {k: v for k, v in self._model_map.items() if v.provider != provider}

    def get_adapter(self, provider: str) -> BaseLLMAdapter | None:
        return self._adapters.get(provider)

    def get_adapter_for_model(self, model_id: str) -> BaseLLMAdapter | None:
        return self._model_map.get(model_id)

    def _build_model_map(self, models: list[ModelInfo], adapter: BaseLLMAdapter):
        for m in models:
            self._model_map[m.id] = adapter

    async def list_all_models(self) -> list[ModelInfo]:
        all_models: list[ModelInfo] = []
        for adapter in self._adapters.values():
            try:
                models = await adapter.list_models()
                self._build_model_map(models, adapter)
                all_models.extend(models)
            except Exception:
                pass
        return all_models

    async def test_all(self) -> dict[str, bool]:
        results = {}
        for provider, adapter in self._adapters.items():
            try:
                results[provider] = await adapter.test_connection()
            except Exception:
                results[provider] = False
        return results

    @property
    def configured_providers(self) -> list[str]:
        return [p for p, a in self._adapters.items() if a.is_configured]


registry = ModelRegistry()


def init_registry():
    """Initialize the registry with built-in and custom adapters."""

    from llm.claude import ClaudeAdapter
    from llm.openai_adapter import OpenAIAdapter
    from llm.gemini import GeminiAdapter
    from llm.qwen import QwenAdapter
    from llm.qianfan_adapter import QianfanAdapter
    from llm.deepseek import DeepSeekAdapter
    from llm.zhipu import ZhipuAdapter
    from llm.moonshot import MoonshotAdapter

    registry.register(ClaudeAdapter(api_key=settings.anthropic_api_key))
    registry.register(OpenAIAdapter(api_key=settings.openai_api_key))
    registry.register(GeminiAdapter(api_key=settings.google_api_key))
    registry.register(QwenAdapter(api_key=settings.dashscope_api_key))
    registry.register(QianfanAdapter(
        api_key=settings.qianfan_access_key,
        api_secret=settings.qianfan_secret_key,
    ))
    registry.register(DeepSeekAdapter(api_key=settings.deepseek_api_key))
    registry.register(ZhipuAdapter(api_key=settings.zhipu_api_key))
    registry.register(MoonshotAdapter(api_key=settings.moonshot_api_key))

    # Load custom models from disk
    load_custom_adapters()


def load_custom_adapters():
    """Load user-defined custom model configurations and register them."""
    registry.unregister("custom")  # Remove previous custom adapter if any
    custom_configs = load_custom_models()
    if not custom_configs:
        return

    # Group custom models by (base_url, api_key) to create one adapter per unique endpoint
    groups: dict[str, GenericAdapter] = {}
    for cfg in custom_configs:
        key = f"{cfg.base_url}|{cfg.api_key or 'unkeyed'}"
        if key not in groups:
            groups[key] = GenericAdapter(
                api_key=cfg.api_key,
                base_url=cfg.base_url,
                models=[],
            )
            # Provider label shown in UI
            groups[key].provider = cfg.provider_label if groups[key].provider == "custom" else groups[key].provider
            groups[key].provider = "custom"
        groups[key]._models.append(cfg.id)

    # Register each unique adapter as "custom_{index}"
    for i, (key, adapter) in enumerate(groups.items()):
        provider_name = f"custom_{i}"
        adapter.provider = provider_name
        registry.register(adapter)
