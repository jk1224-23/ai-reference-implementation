from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REGISTRY_PATH = BASE_DIR / "tools" / "tool_registry.json"

_registry = None


def load_registry() -> dict:
    """Load the tool registry JSON."""
    global _registry
    if _registry is None:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            _registry = json.load(f)
    return _registry


def load_tool_registry() -> dict:
    """Alias used by executor; kept for clarity."""
    return load_registry()


def get_tool(tool_name: str) -> dict | None:
    """Lookup a tool by name."""
    reg = load_registry()
    for t in reg.get("tools", []):
        if t.get("name") == tool_name:
            return t
    return None
