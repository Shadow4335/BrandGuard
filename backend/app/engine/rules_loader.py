"""Load the YAML rule library (backend/rules/*.yaml) once and expose it as dicts."""
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

RULES_DIR = Path(__file__).resolve().parents[2] / "rules"


@lru_cache()
def load_rules() -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for f in sorted(RULES_DIR.glob("*.yaml")):
        for r in yaml.safe_load(f.read_text(encoding="utf-8")) or []:
            r.setdefault("layer", "A")
            rules.append(r)
    return rules


def rules_by_id() -> Dict[str, Dict[str, Any]]:
    return {r["id"]: r for r in load_rules()}


def rule_title(rule_id: str) -> str:
    return rules_by_id().get(rule_id, {}).get("title", rule_id)
