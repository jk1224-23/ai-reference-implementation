from __future__ import annotations

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
SKILL_REGISTRY_PATH = BASE_DIR / "config" / "skill_registry.yaml"

_registry = None


def _load_registry() -> dict:
    with open(SKILL_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _ensure_loaded() -> dict:
    global _registry
    if _registry is None:
        _registry = _load_registry()
    return _registry


def resolve_skill(*, intent: str, risk_tier: str, entities: dict) -> dict:
    """
    Deterministic skill routing:
    intent -> skill_id -> skill contract metadata.
    """
    registry = _ensure_loaded()
    intent_map = registry.get("intent_to_skill") or {}
    skills = registry.get("skills") or {}

    skill_id = intent_map.get(intent)
    if not skill_id:
        return {
            "resolved": False,
            "skillId": None,
            "category": None,
            "allowedTools": [],
            "hitlRequiredBySkill": False,
            "subjectBindingRequired": False,
            "reasons": ["DENY_BY_DEFAULT_NO_SKILL_ROUTE"],
            "metadata": {"intent": intent, "riskTier": risk_tier, "entities": entities or {}},
        }

    skill_cfg = skills.get(skill_id)
    if not skill_cfg:
        return {
            "resolved": False,
            "skillId": skill_id,
            "category": None,
            "allowedTools": [],
            "hitlRequiredBySkill": False,
            "subjectBindingRequired": False,
            "reasons": ["SKILL_CONFIG_NOT_FOUND"],
            "metadata": {"intent": intent, "riskTier": risk_tier, "entities": entities or {}},
        }

    return {
        "resolved": True,
        "skillId": skill_id,
        "category": skill_cfg.get("category", "READ_ONLY"),
        "allowedTools": list(skill_cfg.get("allowed_tools") or []),
        "hitlRequiredBySkill": bool(skill_cfg.get("hitl_required", False)),
        "subjectBindingRequired": bool(skill_cfg.get("subject_binding_required", False)),
        "maxToolCallsPerTurn": int(skill_cfg.get("max_tool_calls_per_turn", len(skill_cfg.get("allowed_tools") or []))),
        "maxTurnDurationMs": int(skill_cfg.get("max_turn_duration_ms", 6000)),
        "description": skill_cfg.get("description", ""),
        "reasons": ["SKILL_ROUTE_MATCH"],
        "metadata": {"intent": intent, "riskTier": risk_tier, "entities": entities or {}},
    }
