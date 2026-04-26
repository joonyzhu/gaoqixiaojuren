from llm.base import BaseLLMAdapter, ModelInfo, GenerationResult


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini."""

    provider = "gemini"

    def _get_model(self, model=None):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(model or "gemini-2.0-flash")

    async def generate(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        import asyncio
        gemini_model = self._get_model(model)
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [system_prompt]})
            contents.append({"role": "model", "parts": ["Understood."]})
        contents.append({"role": "user", "parts": [prompt]})
        resp = await asyncio.to_thread(
            gemini_model.generate_content,
            contents,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        return GenerationResult(
            text=resp.text or "",
            model=model or "gemini-2.0-flash",
        )

    async def stream(self, prompt, system_prompt="", model=None, temperature=0.7, max_tokens=4096):
        import asyncio
        gemini_model = self._get_model(model)
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [system_prompt]})
            contents.append({"role": "model", "parts": ["Understood."]})
        contents.append({"role": "user", "parts": [prompt]})
        resp = await asyncio.to_thread(
            gemini_model.generate_content,
            contents,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
            stream=True,
        )
        for chunk in resp:
            if chunk.text:
                yield chunk.text

    async def list_models(self):
        return [
            ModelInfo(id="gemini-2.0-flash", name="Gemini 2.0 Flash", provider=self.provider, configured=self.is_configured),
            ModelInfo(id="gemini-2.0-pro", name="Gemini 2.0 Pro", provider=self.provider, configured=self.is_configured),
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
        return "gemini-2.0-flash"
