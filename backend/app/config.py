import os
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Search for .env in current dir, backend/, or parent dir without hardcoding
for env_path in [
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env",
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break


class Settings(BaseModel):
    app_name: str = "BrandGuard API"
    app_version: str = "0.1.0"
    mock_llm: bool = os.getenv("MOCK_LLM", "true").lower() in ("true", "1", "yes")
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-004")
    embed_dim: int = int(os.getenv("EMBED_DIM", "768"))
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    port: int = int(os.getenv("PORT", "8000"))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
