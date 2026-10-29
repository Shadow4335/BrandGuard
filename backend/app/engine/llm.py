"""LLM provider adapter. Temperature 0, 20 s timeout, JSON only.

Tries, in order: the main model (LLM_PROVIDER / LLM_MODEL / LLM_API_KEY), the Gemini fallback model
(LLM_FALLBACK_MODEL, same key), then an optional backup provider with its own key
(LLM_BACKUP_PROVIDER / LLM_BACKUP_MODEL / LLM_BACKUP_API_KEY). If every attempt fails, LLMError is
raised so the caller can fall back to the offline checks."""
import json
import re
import time
from typing import List, Tuple

import httpx

from app.config import get_settings

TIMEOUT = 20.0
# Errors where retrying the same model can't help: quota, bad key, unknown model
PERMANENT = ("429", "RESOURCE_EXHAUSTED", "401", "403", "404", "NOT_FOUND", "PERMISSION_DENIED", "API_KEY_INVALID")


class LLMError(Exception):
    pass


def strip_fences(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    return re.sub(r"\s*```$", "", t).strip()


def _gemini(system: str, user: str, model: str, key: str) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=int(TIMEOUT * 1000)))
    res = client.models.generate_content(
        model=model, contents=user,
        config=types.GenerateContentConfig(system_instruction=system, temperature=0,
                                           response_mime_type="application/json"))
    return res.text or ""


def _anthropic(system: str, user: str, model: str, key: str) -> str:
    r = httpx.post("https://api.anthropic.com/v1/messages", timeout=TIMEOUT,
                   headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                   json={"model": model, "max_tokens": 4000, "temperature": 0, "system": system,
                         "messages": [{"role": "user", "content": user}]})
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")


def _openai_compatible(base_url: str):
    """OpenAI-style chat completions; used for OpenAI, Groq and xAI (Grok)."""
    def call(system: str, user: str, model: str, key: str) -> str:
        r = httpx.post(f"{base_url}/chat/completions", timeout=TIMEOUT,
                       headers={"Authorization": f"Bearer {key}"},
                       json={"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    return call


PROVIDERS = {
    "gemini": _gemini,
    "anthropic": _anthropic,
    "openai": _openai_compatible("https://api.openai.com/v1"),
    "groq": _openai_compatible("https://api.groq.com/openai/v1"),
    "xai": _openai_compatible("https://api.x.ai/v1"),
}


def chain() -> List[Tuple[str, str, str]]:
    """(provider, model, key) in the order they are tried. Keys are never logged."""
    s = get_settings()
    out: List[Tuple[str, str, str]] = []
    if s.llm_api_key:
        out.append((s.llm_provider, s.llm_model, s.llm_api_key))
        if s.llm_provider == "gemini" and s.llm_fallback_model and s.llm_fallback_model != s.llm_model:
            out.append(("gemini", s.llm_fallback_model, s.llm_api_key))
    if s.llm_backup_api_key and s.llm_backup_provider and s.llm_backup_model:
        out.append((s.llm_backup_provider, s.llm_backup_model, s.llm_backup_api_key))
    return [c for c in out if c[0] in PROVIDERS]


def complete_json(system: str, user: str) -> Tuple[dict, str]:
    """-> (parsed JSON, "provider:model" that answered)"""
    s = get_settings()
    steps = chain()
    if s.mock_llm or not steps:
        raise LLMError("No LLM key configured")
    last: Exception = LLMError("unknown")
    for provider, model, key in steps:
        for attempt in range(2):  # one retry for transient errors (timeouts, 503 overload)
            try:
                text = PROVIDERS[provider](system, user, model, key)
                return json.loads(strip_fences(text)), f"{provider}:{model}"
            except Exception as e:  # network, timeout, overload, quota, bad key, bad JSON
                last = e
                msg = str(e).replace(key, "***")
                print(f"LLM call failed ({provider}/{model}): {type(e).__name__}: {msg[:160]}", flush=True)
                if any(code in msg for code in PERMANENT):
                    break
                if attempt == 0:
                    time.sleep(1.5)
    raise LLMError(str(last))
