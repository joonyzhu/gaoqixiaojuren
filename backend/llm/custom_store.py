import json
import os
from dataclasses import dataclass, asdict

CUSTOM_MODELS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "custom_models.json")


@dataclass
class CustomModelConfig:
    id: str                          # unique model id (user-defined)
    name: str                        # display name
    base_url: str                    # API base URL
    api_key: str = ""               # API key
    provider_label: str = "custom"   # provider group label in UI


def load_custom_models() -> list[CustomModelConfig]:
    if not os.path.exists(CUSTOM_MODELS_FILE):
        return []
    try:
        with open(CUSTOM_MODELS_FILE, "r") as f:
            data = json.load(f)
        return [CustomModelConfig(**item) for item in data]
    except Exception:
        return []


def save_custom_models(models: list[CustomModelConfig]) -> None:
    os.makedirs(os.path.dirname(CUSTOM_MODELS_FILE), exist_ok=True)
    with open(CUSTOM_MODELS_FILE, "w") as f:
        json.dump([asdict(m) for m in models], f, ensure_ascii=False, indent=2)


def add_custom_model(config: CustomModelConfig) -> None:
    models = load_custom_models()
    # Replace if same ID exists
    models = [m for m in models if m.id != config.id]
    models.append(config)
    save_custom_models(models)


def remove_custom_model(model_id: str) -> bool:
    models = load_custom_models()
    new_models = [m for m in models if m.id != model_id]
    if len(new_models) == len(models):
        return False
    save_custom_models(new_models)
    return True
