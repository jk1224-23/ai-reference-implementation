from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.skill_router import resolve_skill  # noqa: E402


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def test_allowlist_intents_have_skill_mapping():
    allowlist = _load_yaml(ROOT / "config" / "tool_allowlist.yaml")
    skills = _load_yaml(ROOT / "config" / "skill_registry.yaml")

    allowlist_intents = set((allowlist.get("intents") or {}).keys())
    skill_intents = set((skills.get("intent_to_skill") or {}).keys())

    assert allowlist_intents.issubset(skill_intents)


def test_resolve_skill_returns_budget_fields():
    result = resolve_skill(intent="CLAIM_STATUS", risk_tier="MEDIUM", entities={"claimId": "12345"})
    assert result["resolved"] is True
    assert result["skillId"] == "skill.claim_status_lookup.v1"
    assert result["maxToolCallsPerTurn"] >= 1
    assert result["maxTurnDurationMs"] > 0


def test_unknown_intent_denies_by_default():
    result = resolve_skill(intent="UNKNOWN_OR_BLOCKED", risk_tier="HIGH", entities={})
    assert result["resolved"] is False
    assert "DENY_BY_DEFAULT_NO_SKILL_ROUTE" in result["reasons"]
