from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from tools.case_create_tool import case_create
from tools.claims_read_tool import claims_read
from tools.registry import load_tool_registry


@dataclass
class ToolExecutionError(Exception):
    code: str
    message: str


def execute_tools(
    *,
    policy: dict,
    intent: dict,
    tool_requests: list[dict] | None,
    approval_id: str | None = None,
    approval_status: str | None = None,
    kill_switch_state: dict | None = None,
    max_tool_calls_per_turn: int | None = None,
) -> list[dict]:
    """
    Executes tool calls only if policy allows them.
    Emits schema-aligned tool events for audit and UI inspection.
    """
    tool_requests = tool_requests or []
    kill_switch_state = kill_switch_state or {}

    decision = policy.get("decision")
    if decision in ("DENY", "DEGRADED_KB_ONLY"):
        return []

    allowed = set(policy.get("allowedTools", []))
    if not allowed:
        return []

    registry = load_tool_registry()
    registry_tools = {t["name"]: t for t in registry.get("tools", [])}
    breakers = kill_switch_state.get("tool_circuit_breakers") or {}

    results: list[dict] = []

    for index, req in enumerate(tool_requests):
        tool_name = req.get("name")
        tool_input = req.get("input") or {}
        tool_request_id = f"t-{uuid.uuid4().hex[:8]}"

        if max_tool_calls_per_turn is not None and index >= max_tool_calls_per_turn:
            results.append(
                _tool_event(
                    tool_name=tool_name or "UNKNOWN",
                    tool_version=_tool_version(tool_name or "UNKNOWN"),
                    request_id=tool_request_id,
                    result="BLOCKED",
                    duration_ms=0,
                    input_summary=_summarize_input(tool_input),
                    output_summary={},
                    error_code="TOOL_CALL_BUDGET_EXCEEDED",
                    error_message="Skill budget exceeded max tool calls for this turn",
                )
            )
            continue

        if not tool_name:
            results.append(
                _tool_event(
                    tool_name="UNKNOWN",
                    tool_version="v0",
                    request_id=tool_request_id,
                    result="BLOCKED",
                    duration_ms=0,
                    input_summary={},
                    output_summary={},
                    error_code="VALIDATION_ERROR",
                    error_message="Missing tool name",
                )
            )
            continue

        meta = registry_tools.get(tool_name)
        tool_version = _tool_version(tool_name)
        if not meta:
            results.append(
                _tool_event(
                    tool_name=tool_name,
                    tool_version=tool_version,
                    request_id=tool_request_id,
                    result="FAILURE",
                    duration_ms=0,
                    input_summary=_summarize_input(tool_input),
                    output_summary={},
                    error_code="VALIDATION_ERROR",
                    error_message="Tool not found in registry",
                )
            )
            continue

        if tool_name not in allowed:
            results.append(
                _tool_event(
                    tool_name=tool_name,
                    tool_version=tool_version,
                    request_id=tool_request_id,
                    result="BLOCKED",
                    duration_ms=0,
                    input_summary=_summarize_input(tool_input),
                    output_summary={},
                    error_code="AUTHZ_DENIED",
                    error_message="Tool not allowed by policy",
                )
            )
            continue

        if breakers.get(tool_name):
            results.append(
                _tool_event(
                    tool_name=tool_name,
                    tool_version=tool_version,
                    request_id=tool_request_id,
                    result="BLOCKED",
                    duration_ms=0,
                    input_summary=_summarize_input(tool_input),
                    output_summary={},
                    error_code="CIRCUIT_BREAKER_OPEN",
                    error_message="Tool temporarily disabled by circuit breaker",
                )
            )
            continue

        if meta.get("type") == "TRANSACTIONAL":
            if approval_status == "REJECTED":
                results.append(
                    _tool_event(
                        tool_name=tool_name,
                        tool_version=tool_version,
                        request_id=tool_request_id,
                        result="BLOCKED",
                        duration_ms=0,
                        input_summary=_summarize_input(tool_input),
                        output_summary={},
                        error_code="HITL_APPROVAL_REJECTED",
                        error_message="Transactional tool denied: approval was rejected.",
                    )
                )
                continue
            if approval_status in {"PENDING", "UNKNOWN", "MISSING"}:
                results.append(
                    _tool_event(
                        tool_name=tool_name,
                        tool_version=tool_version,
                        request_id=tool_request_id,
                        result="BLOCKED",
                        duration_ms=0,
                        input_summary=_summarize_input(tool_input),
                        output_summary={},
                        error_code="HITL_APPROVAL_PENDING",
                        error_message="Transactional tool blocked until approval is approved.",
                    )
                )
                continue
            if not approval_id:
                results.append(
                    _tool_event(
                        tool_name=tool_name,
                        tool_version=tool_version,
                        request_id=tool_request_id,
                        result="BLOCKED",
                        duration_ms=0,
                        input_summary=_summarize_input(tool_input),
                        output_summary={},
                        error_code="HITL_APPROVAL_REQUIRED",
                        error_message="Transactional tool requires approvalId (HITL).",
                    )
                )
                continue
            tool_input = dict(tool_input)
            tool_input.setdefault("approvalId", approval_id)

        start = time.time()
        try:
            output = _dispatch(tool_name, tool_input)
            output_duration = int((time.time() - start) * 1000)

            if isinstance(output, dict) and output.get("result") in {"FAILED", "BLOCKED"}:
                error = output.get("error") or {}
                normalized_result = "BLOCKED" if output.get("result") == "BLOCKED" else "FAILURE"
                results.append(
                    _tool_event(
                        tool_name=tool_name,
                        tool_version=tool_version,
                        request_id=tool_request_id,
                        result=normalized_result,
                        duration_ms=output_duration,
                        input_summary=_summarize_input(tool_input),
                        output_summary={},
                        error_code=error.get("code", "UNKNOWN"),
                        error_message=error.get("message", "Tool execution failed"),
                    )
                )
                continue

            results.append(
                _tool_event(
                    tool_name=tool_name,
                    tool_version=tool_version,
                    request_id=tool_request_id,
                    result="SUCCESS",
                    duration_ms=int((output or {}).get("durationMs", output_duration)),
                    input_summary=_summarize_input(tool_input),
                    output_summary=_summarize_output(output),
                )
            )
        except ToolExecutionError as exc:
            results.append(
                _tool_event(
                    tool_name=tool_name,
                    tool_version=tool_version,
                    request_id=tool_request_id,
                    result="FAILURE",
                    duration_ms=int((time.time() - start) * 1000),
                    input_summary=_summarize_input(tool_input),
                    output_summary={},
                    error_code=exc.code,
                    error_message=exc.message,
                )
            )
        except Exception as exc:  # safe fallback
            results.append(
                _tool_event(
                    tool_name=tool_name,
                    tool_version=tool_version,
                    request_id=tool_request_id,
                    result="FAILURE",
                    duration_ms=int((time.time() - start) * 1000),
                    input_summary=_summarize_input(tool_input),
                    output_summary={},
                    error_code="UNKNOWN",
                    error_message=str(exc),
                )
            )

    return results


def _dispatch(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "claims.read.v1":
        _require(tool_input, ["claimId"])
        return claims_read(claim_id=tool_input["claimId"])

    if tool_name == "case.create.v1":
        _require(tool_input, ["subject", "description", "claimId", "approvalId"])
        return case_create(
            subject=tool_input["subject"],
            description=tool_input["description"],
            claim_id=tool_input["claimId"],
            approval_id=tool_input["approvalId"],
        )

    raise ToolExecutionError("VALIDATION_ERROR", f"Unknown tool: {tool_name}")


def _tool_version(tool_name: str) -> str:
    if ".v" in tool_name:
        return "v" + tool_name.split(".v")[-1]
    return "v1"


def _require(payload: dict[str, Any], keys: list[str]) -> None:
    missing = [key for key in keys if not payload.get(key)]
    if missing:
        raise ToolExecutionError("VALIDATION_ERROR", f"Missing required inputs: {', '.join(missing)}")


def _summarize_input(tool_input: dict[str, Any]) -> dict:
    return {key: tool_input.get(key) for key in ("claimId", "approvalId", "subject") if key in tool_input}


def _summarize_output(output: dict[str, Any] | None) -> dict:
    output = output or {}
    return {
        key: output.get(key)
        for key in ("claimId", "caseId", "status", "lastUpdated", "durationMs")
        if key in output
    }


def _tool_event(
    *,
    tool_name: str,
    tool_version: str,
    request_id: str,
    result: str,
    duration_ms: int,
    input_summary: dict,
    output_summary: dict,
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict:
    event = {
        "toolName": tool_name,
        "toolVersion": tool_version,
        "requestId": request_id,
        "durationMs": duration_ms,
        "result": result,
        "inputSummary": input_summary,
        "outputSummary": output_summary,
        # Legacy key kept for UI backward compatibility.
        "name": tool_name,
    }
    if error_code:
        event["errorCode"] = error_code
        event["error"] = {"code": error_code, "message": error_message or ""}
    return event
