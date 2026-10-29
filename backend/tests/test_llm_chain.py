"""The provider chain: main model -> Gemini fallback model -> backup provider -> offline checks.
Providers are faked, so no real API is called."""
import uuid

import pytest

from app.config import get_settings
from app.engine import llm
from app.engine.layer_a import ReviewContext
from app.engine.layer_b import run_layer_b
from app.engine.retrieval import RetrievedSource

OK = '{"findings": []}'


@pytest.fixture
def cfg(monkeypatch):
    s = get_settings()
    for k, v in {"mock_llm": False, "llm_provider": "gemini", "llm_model": "main", "llm_fallback_model": "lite",
                 "llm_api_key": "GEMINI-KEY", "llm_backup_provider": "anthropic", "llm_backup_model": "claude-x",
                 "llm_backup_api_key": "ANTHROPIC-KEY"}.items():
        monkeypatch.setattr(s, k, v)
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)
    return s


def fake(monkeypatch, behaviour):
    """behaviour: {(provider, model): exception-or-text}; records every call."""
    calls = []
    def make(provider):
        def fn(system, user, model, key):
            calls.append((provider, model, key))
            out = behaviour.get((provider, model), Exception("503 UNAVAILABLE"))
            if isinstance(out, Exception):
                raise out
            return out
        return fn
    monkeypatch.setattr(llm, "PROVIDERS", {p: make(p) for p in ("gemini", "anthropic", "openai")})
    return calls


def test_main_model_answers(cfg, monkeypatch):
    calls = fake(monkeypatch, {("gemini", "main"): OK})
    assert llm.complete_json("s", "u") == ({"findings": []}, "gemini:main")
    assert len(calls) == 1


def test_quota_skips_to_fallback_model_without_retry(cfg, monkeypatch):
    calls = fake(monkeypatch, {("gemini", "main"): Exception("429 RESOURCE_EXHAUSTED"), ("gemini", "lite"): OK})
    assert llm.complete_json("s", "u")[1] == "gemini:lite"
    assert [c[:2] for c in calls] == [("gemini", "main"), ("gemini", "lite")]


def test_backup_provider_used_with_its_own_key_when_gemini_fails(cfg, monkeypatch):
    calls = fake(monkeypatch, {("gemini", "main"): Exception("429 quota"), ("gemini", "lite"): Exception("404 NOT_FOUND"),
                               ("anthropic", "claude-x"): OK})
    assert llm.complete_json("s", "u")[1] == "anthropic:claude-x"
    assert calls[-1] == ("anthropic", "claude-x", "ANTHROPIC-KEY")


def test_transient_errors_retry_once_per_model(cfg, monkeypatch):
    calls = fake(monkeypatch, {("anthropic", "claude-x"): OK})  # gemini models always 503
    llm.complete_json("s", "u")
    assert [c[:2] for c in calls] == [("gemini", "main")] * 2 + [("gemini", "lite")] * 2 + [("anthropic", "claude-x")]


def test_backup_alone_works_without_gemini_key(cfg, monkeypatch):
    monkeypatch.setattr(cfg, "llm_api_key", "")
    calls = fake(monkeypatch, {("anthropic", "claude-x"): OK})
    assert cfg.llm_available and llm.complete_json("s", "u")[1] == "anthropic:claude-x" and len(calls) == 1


def test_all_fail_falls_back_offline_and_redacts_keys(cfg, monkeypatch):
    fake(monkeypatch, {("anthropic", "claude-x"): Exception("401 bad key ANTHROPIC-KEY")})
    v = uuid.uuid4()
    findings, used_fallback, model = run_layer_b(ReviewContext(v, v, "Our balm works in 1 day!"),
                                                 [RetrievedSource("1", "GUIDE-TONE-01", "guideline", "No hype.")])
    assert used_fallback and model.startswith("offline-heuristic") and "ANTHROPIC-KEY" not in model
    assert findings  # offline checks still produced results


def test_review_records_which_provider_answered(cfg, monkeypatch):
    fake(monkeypatch, {("gemini", "main"): Exception("429"), ("gemini", "lite"): Exception("429"),
                       ("anthropic", "claude-x"): OK})
    v = uuid.uuid4()
    _, used_fallback, model = run_layer_b(ReviewContext(v, v, "Plain text for you."), [])
    assert not used_fallback and model == "anthropic:claude-x"


def test_no_backup_configured_means_no_backup_call(cfg, monkeypatch):
    monkeypatch.setattr(cfg, "llm_backup_api_key", "")
    calls = fake(monkeypatch, {})
    with pytest.raises(llm.LLMError):
        llm.complete_json("s", "u")
    assert {c[0] for c in calls} == {"gemini"}


def test_unknown_backup_provider_is_ignored(cfg, monkeypatch):
    monkeypatch.setattr(cfg, "llm_backup_provider", "acme")
    assert all(p != "acme" for p, _, _ in llm.chain()) and not cfg.llm_backup_ready


@pytest.mark.parametrize("name,key,expected", [
    ("groq", "gsk_abc", "groq"),
    ("grok", "gsk_abc", "groq"),       # Groq key labelled "grok": sent to Groq, not xAI
    ("grok", "xai-abc", "xai"),
    ("xai", "xai-abc", "xai"),
    ("groq", "xai-abc", "xai"),        # xAI key labelled "groq": sent to xAI
    ("Anthropic", "sk-ant-x", "anthropic"),
    ("openai", "sk-x", "openai"),
])
def test_backup_provider_name_and_key_format(name, key, expected):
    from app.config import backup_provider
    assert backup_provider(name, key) == expected


def test_groq_and_xai_use_their_own_endpoints(monkeypatch):
    seen = []
    class R:
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": OK}}]}
    monkeypatch.setattr(llm.httpx, "post", lambda url, **kw: seen.append((url, kw["headers"]["Authorization"])) or R())
    llm.PROVIDERS["groq"]("s", "u", "m", "gsk_k")
    llm.PROVIDERS["xai"]("s", "u", "m", "xai-k")
    assert seen == [("https://api.groq.com/openai/v1/chat/completions", "Bearer gsk_k"),
                    ("https://api.x.ai/v1/chat/completions", "Bearer xai-k")]
