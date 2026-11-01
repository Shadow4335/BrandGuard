import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
os.environ["FORCE_MEMORY_STORE"] = "true"
os.environ["MOCK_LLM"] = "true"
os.environ["DEMO_MODE"] = "true"  # most tests use the seeded demo accounts; demo mode is off by default

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Rate limits are per process, so clear them between tests (many tests upload or review as the same user)."""
    from app.routers import content, core, review, sources
    buckets = (core._signups, core._logins, core._demos, core._google, content._uploads, review._reviews,
               sources._source_uploads)
    for b in buckets:
        b.clear()
    yield
    for b in buckets:
        b.clear()
