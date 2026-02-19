import json
import sys
from pathlib import Path

import yaml
from jsonschema import validate


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tools" / "tool_registry.json"
SCHEMA = ROOT / "standards" / "schemas" / "tool-contract.schema.json"
ALLOWLIST = ROOT / "config" / "tool_allowlist.yaml"
SKILL_REGISTRY = ROOT / "config" / "skill_registry.yaml"


def main() -> int:
    required_files = [REGISTRY, SCHEMA, ALLOWLIST, SKILL_REGISTRY]
    missing = [path for path in required_files if not path.exists()]
    if missing:
        for path in missing:
            print(f"ERROR: Missing required file: {path}")
        return 2

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    allowlist = yaml.safe_load(ALLOWLIST.read_text(encoding="utf-8"))
    skill_registry = yaml.safe_load(SKILL_REGISTRY.read_text(encoding="utf-8"))

    validate(instance=registry, schema=schema)

    tool_names = [tool["name"] for tool in registry.get("tools", [])]
    if len(tool_names) != len(set(tool_names)):
        dupes = sorted({name for name in tool_names if tool_names.count(name) > 1})
        print(f"ERROR: Duplicate tool names found: {dupes}")
        return 2

    registry_map = {tool["name"]: tool for tool in registry.get("tools", [])}
    errors: list[str] = []

    intents = (allowlist or {}).get("intents") or {}
    skills = (skill_registry or {}).get("skills") or {}
    intent_to_skill = (skill_registry or {}).get("intent_to_skill") or {}

    for intent_name, skill_name in intent_to_skill.items():
        if skill_name not in skills:
            errors.append(f"skill_registry: intent '{intent_name}' maps to missing skill '{skill_name}'")

    for skill_name, skill_cfg in skills.items():
        max_tools = int(skill_cfg.get("max_tool_calls_per_turn", -1))
        max_turn_ms = int(skill_cfg.get("max_turn_duration_ms", 0))
        if max_tools < 0:
            errors.append(f"{skill_name}: max_tool_calls_per_turn must be >= 0")
        if max_turn_ms <= 0:
            errors.append(f"{skill_name}: max_turn_duration_ms must be > 0")

    for intent_name, intent_cfg in intents.items():
        allowlist_skill = intent_cfg.get("skill")
        routed_skill = intent_to_skill.get(intent_name)
        if not allowlist_skill:
            errors.append(f"{intent_name}: missing skill mapping in allowlist")
        elif allowlist_skill not in skills:
            errors.append(f"{intent_name}: allowlist skill '{allowlist_skill}' not found in skill registry")
        elif routed_skill != allowlist_skill:
            errors.append(
                f"{intent_name}: skill mismatch (allowlist={allowlist_skill}, skill_registry={routed_skill})"
            )

        skill_tools = set((skills.get(allowlist_skill) or {}).get("allowed_tools") or [])
        for allowed in intent_cfg.get("allowed_tools", []) or []:
            tool_name = allowed.get("name")
            if not tool_name:
                errors.append(f"{intent_name}: allowed_tools entry missing name")
                continue

            registry_tool = registry_map.get(tool_name)
            if not registry_tool:
                errors.append(f"{intent_name}: tool '{tool_name}' is not defined in tool_registry.json")
                continue

            declared_type = allowed.get("tool_type")
            actual_type = registry_tool.get("type")
            if declared_type and declared_type != actual_type:
                errors.append(
                    f"{intent_name}: tool '{tool_name}' type mismatch (allowlist={declared_type}, registry={actual_type})"
                )

            requires_approval = bool(allowed.get("requires_approval", False))
            registry_requires_approval = bool(registry_tool.get("requiresApprovalId", False))
            if requires_approval and not registry_requires_approval:
                errors.append(
                    f"{intent_name}: tool '{tool_name}' requires approval in allowlist but registry does not enforce it"
                )
            if actual_type == "TRANSACTIONAL" and not requires_approval:
                errors.append(
                    f"{intent_name}: transactional tool '{tool_name}' must set requires_approval=true in allowlist"
                )

            if skill_tools and tool_name not in skill_tools:
                errors.append(f"{intent_name}: tool '{tool_name}' is not declared in skill '{allowlist_skill}'")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2

    print("OK: tool_registry.json matches schema and allowlist mappings are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
