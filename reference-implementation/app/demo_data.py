from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "mock_data.json"


@lru_cache(maxsize=1)
def load_demo_data() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_claim(claim_id: str | None) -> dict | None:
    if not claim_id:
        return None
    claims = load_demo_data().get("claims", {})
    return claims.get(claim_id)


def get_user_access(user_id: str) -> dict | None:
    users = load_demo_data().get("users", {})
    return users.get(user_id)
