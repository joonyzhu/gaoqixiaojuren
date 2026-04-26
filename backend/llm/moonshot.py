from openai import AsyncOpenAI
from llm.base import BaseLLMAdapter, ModelInfo, GenerationResult


class MoonshotAdapter(BaseLLMAdapter):
    """Kimi (月之暗面) — OpenAI-compatible API."""

    provider = "moonshot"
    base_url = "https://api.moonshot.cn/v1"

    def _get_client(self):
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def generate(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        client = self._get_client()
        model = model or "moonshot-v1-8k"
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
        model = model or "moonshot-v1-8k"
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
            ModelInfo(id="moonshot-v1-8k", name="Kimi 8K", provider=self.provider, configured=self.is_configured),
            ModelInfo(id="moonshot-v1-32k", name="Kimi 32K", provider=self.provider, configured=self.is_configured),
            ModelInfo(id="moonshot-v1-128k", name="Kimi 128K", provider=self.provider, configured=self.is_configured),
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
        return "moonshot-v1-32k"
