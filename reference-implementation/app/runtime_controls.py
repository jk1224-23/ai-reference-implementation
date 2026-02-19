from __future__ import annotations

import os
from datetime import datetime, timezone
from threading import Lock
from typing import Optional

_LOCK = Lock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_tool_breakers(raw_value: Optional[str]) -> dict:
    if not raw_value:
        return {}
    tools = [token.strip() for token in raw_value.split(",") if token.strip()]
    return {tool_name: True for tool_name in tools}


def _default_kill_switch_state() -> dict:
    return {
        "kb_only_mode": _as_bool(os.getenv("AI_KB_ONLY_MODE")),
        "hitl_first_mode": _as_bool(os.getenv("AI_HITL_FIRST_MODE")),
        "tool_circuit_breakers": _parse_tool_breakers(os.getenv("AI_TOOL_CIRCUIT_BREAKERS")),
    }


_STATE = {
    "kill_switches": _default_kill_switch_state(),
    "approvals": {},
    "lastUpdated": _utc_now_iso(),
}


def _kill_switch_snapshot(current: dict) -> dict:
    return {
        "kb_only_mode": bool(current.get("kb_only_mode", False)),
        "hitl_first_mode": bool(current.get("hitl_first_mode", False)),
        "tool_circuit_breakers": dict(current.get("tool_circuit_breakers") or {}),
    }


def get_kill_switch_state() -> dict:
    with _LOCK:
        return _kill_switch_snapshot(_STATE["kill_switches"])


def set_kill_switch_state(
    *,
    kb_only_mode: Optional[bool] = None,
    hitl_first_mode: Optional[bool] = None,
    tool_circuit_breakers: Optional[list[str]] = None,
) -> dict:
    with _LOCK:
        current = _STATE["kill_switches"]
        if kb_only_mode is not None:
            current["kb_only_mode"] = bool(kb_only_mode)
        if hitl_first_mode is not None:
            current["hitl_first_mode"] = bool(hitl_first_mode)
        if tool_circuit_breakers is not None:
            current["tool_circuit_breakers"] = {tool_name: True for tool_name in tool_circuit_breakers}
        _STATE["lastUpdated"] = _utc_now_iso()
        return _kill_switch_snapshot(current)


def register_approval_request(*, approval_id: str, context: dict) -> dict:
    with _LOCK:
        approvals = _STATE["approvals"]
        if approval_id not in approvals:
            approvals[approval_id] = {
                "approvalId": approval_id,
                "status": "PENDING",
                "context": context,
                "createdAt": _utc_now_iso(),
                "updatedAt": _utc_now_iso(),
                "approver": None,
            }
            _STATE["lastUpdated"] = _utc_now_iso()
        return dict(approvals[approval_id])


def get_approval_status(approval_id: Optional[str]) -> str:
    if not approval_id:
        return "MISSING"
    with _LOCK:
        record = _STATE["approvals"].get(approval_id)
        if not record:
            return "UNKNOWN"
        return str(record.get("status", "UNKNOWN"))


def record_approval_decision(*, approval_id: str, decision: str, approver: str) -> dict:
    normalized = decision.upper()
    if normalized not in {"APPROVED", "REJECTED"}:
        raise ValueError("Invalid decision")
    with _LOCK:
        approvals = _STATE["approvals"]
        record = approvals.get(approval_id) or {
            "approvalId": approval_id,
            "context": {},
            "createdAt": _utc_now_iso(),
        }
        record["status"] = normalized
        record["approver"] = approver
        record["updatedAt"] = _utc_now_iso()
        approvals[approval_id] = record
        _STATE["lastUpdated"] = _utc_now_iso()
        return dict(record)


def get_runtime_state() -> dict:
    with _LOCK:
        approvals = list(_STATE["approvals"].values())
        approvals.sort(key=lambda item: item.get("updatedAt", ""), reverse=True)
        return {
            "killSwitches": _kill_switch_snapshot(_STATE["kill_switches"]),
            "approvals": approvals[:20],
            "lastUpdated": _STATE.get("lastUpdated"),
        }
