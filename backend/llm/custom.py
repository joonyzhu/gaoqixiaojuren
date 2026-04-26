from openai import AsyncOpenAI
from llm.base import BaseLLMAdapter, ModelInfo, GenerationResult


class GenericAdapter(BaseLLMAdapter):
    """Generic OpenAI-compatible adapter. User provides base_url, api_key, and model ID."""

    provider = "custom"

    def __init__(self, api_key="", base_url="", api_secret="", models: list[str] | None = None, **kwargs):
        super().__init__(api_key=api_key, api_secret=api_secret, **kwargs)
        self.base_url = base_url
        self._models = models or []

    @property
    def is_configured(self):
        return bool(self.api_key) and bool(self.base_url)

    def _get_client(self):
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        client = self._get_client()
        model = model or (self._models[0] if self._models else "default")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = await client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, max_tokens=max_tokens,
        )
        return GenerationResult(
            text=resp.choices[0].message.content or "",
            model=model,
            usage={"prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                   "completion_tokens": resp.usage.completion_tokens if resp.usage else 0},
        )

    async def stream(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        client = self._get_client()
        model = model or (self._models[0] if self._models else "default")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        stream_resp = await client.chat.completions.create(
            model=model, messages=messages, temperature=temperature,
            max_tokens=max_tokens, stream=True,
        )
        async for chunk in stream_resp:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def list_models(self):
        return [
            ModelInfo(id=m, name=f"Custom: {m}", provider=self.provider,
                      available=True, configured=self.is_configured)
            for m in self._models
        ]

    async def test_connection(self):
        if not self.is_configured or not self._models:
            return False
        try:
            await self.generate("Hi", max_tokens=10, model=self._models[0])
            return True
        except Exception:
            return False

    def get_default_model(self):
        return self._models[0] if self._models else ""
