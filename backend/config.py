import os
from pydantic_settings import BaseSettings
from pathlib import Path


def _resolve_data_dir() -> Path:
    """Resolve data directory. In production, use DATA_DIR env var so data
    is stored in a persistent, writable location (e.g. Electron's userData)."""
    if env_data := os.environ.get("DATA_DIR"):
        return Path(env_data)
    return Path(__file__).parent.parent / "data"


class Settings(BaseSettings):
    app_name: str = "高企小巨人智能申报系统"
    data_dir: str = str(_resolve_data_dir())
    upload_dir: str = str(_resolve_data_dir() / "uploads")
    chroma_dir: str = str(_resolve_data_dir() / "chroma")
    db_url: str = f"sqlite+aiosqlite:///{_resolve_data_dir() / 'app.db'}"

    # LLM API Keys (configured by user via UI)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    dashscope_api_key: str = ""
    qianfan_access_key: str = ""
    qianfan_secret_key: str = ""
    zhipu_api_key: str = ""
    deepseek_api_key: str = ""
    moonshot_api_key: str = ""
    tavily_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
