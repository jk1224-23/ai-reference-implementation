from __future__ import annotations

from app.runtime_controls import get_kill_switch_state as _get_kill_switch_state


def get_kill_switch_state() -> dict:
    return _get_kill_switch_state()
