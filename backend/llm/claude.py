import anthropic
from llm.base import BaseLLMAdapter, ModelInfo, GenerationResult


class ClaudeAdapter(BaseLLMAdapter):
    provider = "anthropic"

    async def _get_client(self):
        return anthropic.AsyncAnthropic(api_key=self.api_key)

    async def generate(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        client = await self._get_client()
        model = model or "claude-sonnet-4-6"
        messages = [{"role": "user", "content": prompt}]
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or anthropic.NOT_GIVEN,
            messages=messages,
        )
        text = ""
        for block in resp.content:
            if block.type == "text":
                text += block.text
        return GenerationResult(
            text=text,
            model=model,
            usage={
                "prompt_tokens": resp.usage.input_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.output_tokens if resp.usage else 0,
            },
        )

    async def stream(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        client = await self._get_client()
        model = model or "claude-sonnet-4-6"
        messages = [{"role": "user", "content": prompt}]
        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or anthropic.NOT_GIVEN,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def list_models(self):
        return [
            ModelInfo(id="claude-opus-4-7", name="Claude Opus 4.7", provider=self.provider, configured=self.is_configured),
            ModelInfo(id="claude-sonnet-4-6", name="Claude Sonnet 4.6", provider=self.provider, configured=self.is_configured),
            ModelInfo(id="claude-haiku-4-5-20251001", name="Claude Haiku 4.5", provider=self.provider, configured=self.is_configured),
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
        return "claude-sonnet-4-6"
