import os
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Search for .env in backend/ or the repo root
for env_path in [
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env",
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() in ("true", "1", "yes")


class Settings(BaseModel):
    app_name: str = "BrandGuard API"
    app_version: str = "0.2.0"
    mock_llm: bool = _flag("MOCK_LLM", "true")
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    llm_fallback_model: str = os.getenv("LLM_FALLBACK_MODEL", "gemini-flash-lite-latest")  # used when the main model is overloaded
    # Optional second provider with its own key, tried after the main provider fails
    llm_backup_provider: str = os.getenv("LLM_BACKUP_PROVIDER", "").strip().lower()
    llm_backup_api_key: str = os.getenv("LLM_BACKUP_API_KEY", "").strip()
    llm_backup_model: str = os.getenv("LLM_BACKUP_MODEL", "").strip() or {
        "anthropic": "claude-haiku-5-5", "gemini": "gemini-flash-lite-latest"}.get(
        os.getenv("LLM_BACKUP_PROVIDER", "").strip().lower(), "")
    embed_model: str = os.getenv("EMBED_MODEL", "gemini-embedding-001")
    embed_dim: int = int(os.getenv("EMBED_DIM", "768"))
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    demo_password: str = os.getenv("DEMO_USER_PASSWORD", "BrandGuard2026!")
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")
    port: int = int(os.getenv("PORT", "8000"))

    @property
    def use_supabase(self) -> bool:
        """Supabase is used when credentials exist; otherwise an in-memory demo store."""
        return bool(self.supabase_url and self.supabase_service_key) and not _flag("FORCE_MEMORY_STORE", "false")

    @property
    def llm_available(self) -> bool:
        return (not self.mock_llm) and bool(self.llm_api_key or self.llm_backup_ready)

    @property
    def llm_backup_ready(self) -> bool:
        return bool(self.llm_backup_provider in ("gemini", "anthropic", "openai")
                    and self.llm_backup_api_key and self.llm_backup_model)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
