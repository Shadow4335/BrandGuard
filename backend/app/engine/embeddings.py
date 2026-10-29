"""Embeddings behind a tiny adapter. Returns None whenever embeddings are unavailable;
retrieval then falls back to keyword search so the demo never blocks."""
from typing import List, Optional

from app.config import get_settings


def embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    s = get_settings()
    if s.mock_llm or not s.llm_api_key or not texts:  # embeddings use the main (Gemini) key only
        return None
    try:
        if s.llm_provider == "gemini":
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=s.llm_api_key)
            res = client.models.embed_content(
                model=s.embed_model, contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=s.embed_dim))
            vecs = [list(e.values) for e in res.embeddings]
            return vecs if len(vecs) == len(texts) and all(len(v) == s.embed_dim for v in vecs) else None
    except Exception as e:
        print(f"Embedding call failed ({s.embed_model}): {type(e).__name__}: {str(e)[:200]}", flush=True)
        return None
    return None
