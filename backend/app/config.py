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


# Default model per backup provider when LLM_BACKUP_MODEL is not set (OpenAI and xAI must set it)
BACKUP_DEFAULT_MODELS = {"anthropic": "claude-haiku-5-5", "gemini": "gemini-flash-lite-latest",
                         "groq": "openai/gpt-oss-120b"}


def backup_provider(name: str, key: str) -> str:
    """Normalise the provider name. "grok" means xAI; Groq and xAI are easy to mix up, so a key in
    Groq's format (gsk_...) is sent to Groq and one in xAI's format (xai-...) to xAI."""
    name = name.strip().lower()
    name = {"grok": "xai", "x.ai": "xai"}.get(name, name)
    key = key.strip()
    if name in ("xai", "groq"):
        if key.startswith("gsk_"):
            return "groq"
        if key.startswith("xai-"):
            return "xai"
    return name


MIN_ROLE_PASSWORD = 12


class Settings(BaseModel):
    app_name: str = "BrandGuard API"
    app_version: str = "0.2.0"
    mock_llm: bool = _flag("MOCK_LLM", "true")
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    llm_fallback_model: str = os.getenv("LLM_FALLBACK_MODEL", "gemini-flash-lite-latest")  # used when the main model is overloaded
    # Optional second provider with its own key, tried after the main provider fails
    llm_backup_api_key: str = os.getenv("LLM_BACKUP_API_KEY", "").strip()
    llm_backup_provider: str = backup_provider(os.getenv("LLM_BACKUP_PROVIDER", ""), os.getenv("LLM_BACKUP_API_KEY", ""))
    llm_backup_model: str = os.getenv("LLM_BACKUP_MODEL", "").strip() or BACKUP_DEFAULT_MODELS.get(
        backup_provider(os.getenv("LLM_BACKUP_PROVIDER", ""), os.getenv("LLM_BACKUP_API_KEY", "")), "")
    embed_model: str = os.getenv("EMBED_MODEL", "gemini-embedding-001")
    embed_dim: int = int(os.getenv("EMBED_DIM", "768"))
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    demo_password: str = os.getenv("DEMO_USER_PASSWORD") or "BrandGuard2026!"  # an empty value also means the default
    # One-click demo accounts. Off unless DEMO_MODE=true: a deployment has real accounts only by default.
    demo_mode: bool = _flag("DEMO_MODE", "false")
    # Google sign-in through Firebase: only the project ID is needed to check ID tokens. Empty = off.
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")
    port: int = int(os.getenv("PORT", "8000"))

    @property
    def signup_roles(self) -> list:
        """Only Creator can ever be self-assigned without admin authorization."""
        return ["creator"]

    @property
    def role_password(self) -> str:
        """Admin-set password that unlocks manager, reviewer and admin at sign-up (PRIVILEGED_SIGNUP_PASSWORD). Ignored
        if shorter than MIN_ROLE_PASSWORD, so a weak value can't open those roles to guessing."""
        pw = os.getenv("PRIVILEGED_SIGNUP_PASSWORD", "").strip()
        return pw if len(pw) >= MIN_ROLE_PASSWORD else ""

    @property
    def password_roles(self) -> list:
        """Roles that can be chosen at sign-up with the admin password (those not already open to everyone)."""
        if not self.role_password:
            return []
        return [r for r in ("manager", "reviewer", "admin") if r not in self.signup_roles]

    @property
    def use_supabase(self) -> bool:
        """Supabase is used when credentials exist; otherwise an in-memory demo store."""
        return bool(self.supabase_url and self.supabase_service_key) and not _flag("FORCE_MEMORY_STORE", "false")

    @property
    def llm_available(self) -> bool:
        return (not self.mock_llm) and bool(self.llm_api_key or self.llm_backup_ready)

    @property
    def llm_backup_ready(self) -> bool:
        return bool(self.llm_backup_provider in ("gemini", "anthropic", "openai", "groq", "xai")
                    and self.llm_backup_api_key and self.llm_backup_model)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
