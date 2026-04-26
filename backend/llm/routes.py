from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llm.registry import registry, init_registry, load_custom_adapters
from llm.custom_store import (
    load_custom_models,
    add_custom_model,
    remove_custom_model,
    CustomModelConfig,
)

router = APIRouter(tags=["llm"])


class TestModelRequest(BaseModel):
    model_id: str


class GenerateRequest(BaseModel):
    model_id: str
    prompt: str
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096


class CustomModelCreate(BaseModel):
    id: str
    name: str
    base_url: str
    api_key: str = ""


@router.get("/llm/models")
async def list_models():
    """List all available models and their configuration status."""
    init_registry()
    models = await registry.list_all_models()
    # Include custom model configs (from store) so frontend knows what's configured
    custom_configs = {c.id: c for c in load_custom_models()}
    return [
        {
            "id": m.id,
            "name": m.name,
            "provider": m.provider,
            "available": m.available,
            "configured": m.configured,
            "is_custom": m.id in custom_configs,
            "base_url": custom_configs[m.id].base_url if m.id in custom_configs else None,
        }
        for m in models
    ]


@router.post("/llm/test")
async def test_model(data: TestModelRequest):
    """Test connectivity for a specific model."""
    init_registry()
    adapter = registry.get_adapter_for_model(data.model_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Model {data.model_id} not found")

    ok = await adapter.test_connection()
    return {"model_id": data.model_id, "connected": ok, "provider": adapter.provider}


@router.post("/llm/generate")
async def generate_text(data: GenerateRequest):
    """Generate text using the specified model (non-streaming)."""
    init_registry()
    adapter = registry.get_adapter_for_model(data.model_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Model {data.model_id} not found")

    if not adapter.is_configured:
        raise HTTPException(status_code=400, detail=f"Provider {adapter.provider} is not configured")

    result = await adapter.generate(
        prompt=data.prompt,
        system_prompt=data.system_prompt,
        model=data.model_id,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
    )
    return {"text": result.text, "model": result.model, "usage": result.usage}


# --- Custom model management ---

@router.get("/llm/custom-models")
async def list_custom_models():
    """Get all user-configured custom models."""
    return [{"id": c.id, "name": c.name, "base_url": c.base_url,
             "api_key_set": bool(c.api_key), "provider_label": c.provider_label}
            for c in load_custom_models()]


@router.post("/llm/custom-models")
async def create_custom_model(data: CustomModelCreate):
    """Add a custom OpenAI-compatible model."""
    if not data.id or not data.base_url:
        raise HTTPException(status_code=400, detail="id and base_url are required")

    config = CustomModelConfig(
        id=data.id,
        name=data.name or data.id,
        base_url=data.base_url.rstrip("/"),
        api_key=data.api_key,
    )
    add_custom_model(config)
    load_custom_adapters()  # Reload the registry
    return {"status": "ok", "id": data.id}


@router.delete("/llm/custom-models/{model_id}")
async def delete_custom_model(model_id: str):
    """Remove a custom model."""
    if not remove_custom_model(model_id):
        raise HTTPException(status_code=404, detail="Custom model not found")
    load_custom_adapters()
    return {"status": "deleted"}
