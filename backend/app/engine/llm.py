"""LLM provider adapter. Reads LLM_PROVIDER / LLM_MODEL / LLM_API_KEY. Temperature 0, 20 s timeout, one retry.
Any failure raises LLMError so the caller can fall back to the offline path."""
import json
import re

import httpx

from app.config import get_settings

TIMEOUT = 20.0


class LLMError(Exception):
    pass


def strip_fences(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    return re.sub(r"\s*```$", "", t).strip()


def _gemini(system: str, user: str) -> str:
    from google import genai
    from google.genai import types
    s = get_settings()
    client = genai.Client(api_key=s.llm_api_key, http_options=types.HttpOptions(timeout=int(TIMEOUT * 1000)))
    res = client.models.generate_content(
        model=s.llm_model, contents=user,
        config=types.GenerateContentConfig(system_instruction=system, temperature=0,
                                           response_mime_type="application/json"))
    return res.text or ""


def _anthropic(system: str, user: str) -> str:
    s = get_settings()
    r = httpx.post("https://api.anthropic.com/v1/messages", timeout=TIMEOUT,
                   headers={"x-api-key": s.llm_api_key, "anthropic-version": "2023-06-01"},
                   json={"model": s.llm_model, "max_tokens": 2000, "temperature": 0, "system": system,
                         "messages": [{"role": "user", "content": user}]})
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def _openai(system: str, user: str) -> str:
    s = get_settings()
    r = httpx.post("https://api.openai.com/v1/chat/completions", timeout=TIMEOUT,
                   headers={"Authorization": f"Bearer {s.llm_api_key}"},
                   json={"model": s.llm_model, "temperature": 0, "response_format": {"type": "json_object"},
                         "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


PROVIDERS = {"gemini": _gemini, "anthropic": _anthropic, "openai": _openai}


def complete_json(system: str, user: str) -> dict:
    s = get_settings()
    if not s.llm_available:
        raise LLMError("No LLM key configured")
    fn = PROVIDERS.get(s.llm_provider)
    if not fn:
        raise LLMError(f"Unknown LLM_PROVIDER {s.llm_provider}")
    last: Exception = LLMError("unknown")
    for _ in range(2):  # one retry
        try:
            return json.loads(strip_fences(fn(system, user)))
        except Exception as e:  # network, timeout, bad JSON
            last = e
    raise LLMError(str(last))
