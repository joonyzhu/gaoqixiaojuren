import asyncio
from llm.base import BaseLLMAdapter, ModelInfo, GenerationResult


class QianfanAdapter(BaseLLMAdapter):
    """百度文心一言 — via qianfan SDK."""

    provider = "qianfan"

    def __init__(self, api_key="", api_secret="", **kwargs):
        super().__init__(api_key=api_key, api_secret=api_secret, **kwargs)

    @property
    def is_configured(self):
        return bool(self.api_key) and bool(self.api_secret)

    def _get_model(self, model=None):
        import qianfan
        return qianfan.ChatCompletion(model=model or "ernie-4.0-turbo-8k")

    async def generate(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        chat = self._get_model(model)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = await asyncio.to_thread(
            chat.do,
            messages=messages,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        return GenerationResult(
            text=resp.get("result", ""),
            model=model or "ernie-4.0-turbo-8k",
            usage=resp.get("usage", {}),
        )

    async def stream(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        chat = self._get_model(model)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = await asyncio.to_thread(
            chat.do,
            messages=messages,
            temperature=temperature,
            max_output_tokens=max_tokens,
            stream=True,
        )
        for chunk in resp:
            yield chunk.get("result", "")

    async def list_models(self):
        return [
            ModelInfo(id="ernie-4.0-turbo-8k", name="文心一言 ERNIE 4.0 Turbo", provider=self.provider, configured=self.is_configured),
            ModelInfo(id="ernie-4.0-8k", name="文心一言 ERNIE 4.0", provider=self.provider, configured=self.is_configured),
            ModelInfo(id="ernie-3.5-8k", name="文心一言 ERNIE 3.5", provider=self.provider, configured=self.is_configured),
        ]

    async def test_connection(self):
        if not self.is_configured:
            return False
        try:
            await self.generate("Hi", max_tokens=10)
            return True
        except Exception:
            return False

    def get_default_model(self):
        return "ernie-4.0-turbo-8k"
