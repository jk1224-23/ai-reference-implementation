from __future__ import annotations

import uuid
from datetime import datetime, timezone
from time import perf_counter

from app.audit_logger import write_audit_event
from app.intent_classifier import classify_intent
from app.kill_switches import get_kill_switch_state
from app.policy_engine import decide_policy
from app.response_assembler import assemble_response
from app.runtime_controls import get_approval_status, register_approval_request
from app.skill_router import resolve_skill
from tools.claims_read_tool import claims_read
from tools.executor import execute_tools


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _timeline_step(timeline: list[dict], step: str, status: str, detail: str, started_at: float) -> None:
    timeline.append(
        {
            "step": step,
            "status": status,
            "detail": detail,
            "elapsedMs": int((perf_counter() - started_at) * 1000),
            "timestamp": utc_now_iso(),
        }
    )


def _hash_user(user_id: str) -> str:
    import hashlib

    return "uHash-" + hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:8]


def _build_decision_support(intent_result: dict, policy_result: dict) -> dict:
    decision = policy_result.get("decision")
    reasons = policy_result.get("reasons", [])
    escalated = decision in {"ALLOW_HITL", "ALLOW_WITH_CONFIRMATION", "DENY", "DEGRADED_KB_ONLY"}
    return {
        "confidence": float(intent_result.get("confidence", 0.0)),
        "riskTier": intent_result.get("riskTier"),
        "decision": decision,
        "escalated": escalated,
        "why": reasons[:6],
    }


def _needs_verification(skill_result: dict, tool_calls: list[dict]) -> bool:
    if skill_result.get("category") != "TRANSACTIONAL":
        return False
    for call in tool_calls:
        if (call.get("toolName") or call.get("name")) == "case.create.v1" and call.get("result") == "SUCCESS":
            return True
    return False


def _run_post_exec_verification(claim_id: str | None) -> dict:
    if not claim_id:
        return {
            "verified": False,
            "status": "SKIPPED",
            "reason": "MISSING_CLAIM_ID",
        }

    result = claims_read(claim_id=claim_id)
    if result.get("result") == "FAILED":
        return {
            "verified": False,
            "status": "FAILED",
            "reason": (result.get("error") or {}).get("code", "UNKNOWN"),
        }

    return {
        "verified": True,
        "status": "VERIFIED",
        "claimId": claim_id,
        "readBack": {
            "status": result.get("status"),
            "lastUpdated": result.get("lastUpdated"),
        },
    }


def handle_request(
    message: str,
    channel: str,
    user_role: str,
    user_id: str,
    session_id: str,
    approval_id: str | None = None,
):
    started_at = perf_counter()
    timeline: list[dict] = []

    correlation_id = f"c-{uuid.uuid4().hex[:8]}"
    request_id = f"r-{uuid.uuid4().hex[:8]}"
    timestamp = utc_now_iso()

    kill_switch_state = get_kill_switch_state()
    _timeline_step(
        timeline,
        "RUNTIME_CONTROLS",
        "OK",
        f"kbOnly={kill_switch_state.get('kb_only_mode')} hitlFirst={kill_switch_state.get('hitl_first_mode')}",
        started_at,
    )

    # 1) intent classification
    intent_result = classify_intent(message=message, channel=channel)
    _timeline_step(
        timeline,
        "INTENT_CLASSIFIED",
        "OK",
        f"{intent_result['intent']} ({intent_result['riskTier']})",
        started_at,
    )

    # 2) skill routing (intent -> approved skill)
    skill_result = resolve_skill(
        intent=intent_result["intent"],
        risk_tier=intent_result["riskTier"],
        entities=intent_result.get("entities", {}),
    )
    _timeline_step(
        timeline,
        "SKILL_RESOLVED",
        "OK" if skill_result.get("resolved") else "BLOCKED",
        str(skill_result.get("skillId") or "NO_SKILL_ROUTE"),
        started_at,
    )

    # 3) deterministic policy decision
    policy_result = decide_policy(
        intent=intent_result["intent"],
        confidence=float(intent_result["confidence"]),
        risk_tier=intent_result["riskTier"],
        entities=intent_result.get("entities", {}),
        skill_route=skill_result,
        channel=channel,
        user_role=user_role,
        user_id=user_id,
        kill_switch_state=kill_switch_state,
    )
    _timeline_step(
        timeline,
        "POLICY_DECIDED",
        "OK" if policy_result.get("decision") != "DENY" else "BLOCKED",
        f"{policy_result.get('decision')} :: {','.join(policy_result.get('reasons', [])[:2])}",
        started_at,
    )

    approval_status = get_approval_status(approval_id)
    if policy_result.get("hitlRequired"):
        if not approval_id:
            approval_id = f"apr-{request_id}"
            register_approval_request(
                approval_id=approval_id,
                context={
                    "requestId": request_id,
                    "intent": intent_result.get("intent"),
                    "skillId": skill_result.get("skillId"),
                    "userRole": user_role,
                    "userIdHash": _hash_user(user_id),
                },
            )
            approval_status = "PENDING"
            _timeline_step(
                timeline,
                "HITL_APPROVAL",
                "PENDING",
                f"approvalId={approval_id}",
                started_at,
            )
        else:
            _timeline_step(
                timeline,
                "HITL_APPROVAL",
                "OK" if approval_status == "APPROVED" else "BLOCKED",
                f"approvalId={approval_id} status={approval_status}",
                started_at,
            )

        policy_result["approvalId"] = approval_id
        policy_result["approvalStatus"] = approval_status
        if approval_status == "APPROVED":
            policy_result.setdefault("reasons", []).append("HITL_APPROVAL_VERIFIED")
        elif approval_status == "REJECTED":
            policy_result["decision"] = "DENY"
            policy_result["allowedTools"] = []
            policy_result.setdefault("reasons", []).append("HITL_APPROVAL_REJECTED")
        elif approval_status in {"PENDING", "UNKNOWN", "MISSING"}:
            policy_result.setdefault("reasons", []).append(f"HITL_APPROVAL_{approval_status}")

    # 4) prepare tool requests (only for allowed tools)
    tool_requests = []
    entities = intent_result.get("entities", {}) or {}
    claim_id = entities.get("claimId")
    for tool_name in policy_result.get("allowedTools", []):
        if tool_name == "claims.read.v1":
            tool_requests.append({"name": tool_name, "input": {"claimId": claim_id}})
        elif tool_name == "case.create.v1":
            tool_requests.append(
                {
                    "name": tool_name,
                    "input": {
                        "subject": "Appeal request",
                        "description": message,
                        "claimId": claim_id,
                    },
                }
            )

    max_tool_calls_per_turn = int(skill_result.get("maxToolCallsPerTurn", len(tool_requests)))
    max_turn_duration_ms = int(skill_result.get("maxTurnDurationMs", 6000))
    requested_tool_calls = len(tool_requests)
    if requested_tool_calls > max_tool_calls_per_turn:
        policy_result.setdefault("reasons", []).append("TOOL_CALL_BUDGET_EXCEEDED")
        tool_requests = tool_requests[:max_tool_calls_per_turn]

    # 5) tool execution (only if allowed)
    tool_calls = execute_tools(
        policy=policy_result,
        intent=intent_result,
        tool_requests=tool_requests,
        approval_id=approval_id,
        approval_status=approval_status,
        kill_switch_state=kill_switch_state,
        max_tool_calls_per_turn=max_tool_calls_per_turn,
    )
    _timeline_step(
        timeline,
        "TOOLS_EXECUTED",
        "OK" if any(call.get("result") == "SUCCESS" for call in tool_calls) else "SAFE",
        f"calls={len(tool_calls)}",
        started_at,
    )

    verification = None
    if _needs_verification(skill_result, tool_calls):
        verification = _run_post_exec_verification(claim_id=claim_id)
        verification_call = {
            "toolName": "claims.read.v1",
            "toolVersion": "v1",
            "requestId": f"verify-{uuid.uuid4().hex[:6]}",
            "durationMs": 0,
            "result": "SUCCESS" if verification.get("verified") else "FAILURE",
            "inputSummary": {"claimId": claim_id},
            "outputSummary": verification.get("readBack", {}),
            "phase": "POST_EXEC_VERIFICATION",
            "name": "claims.read.v1",
        }
        if not verification.get("verified"):
            verification_call["errorCode"] = verification.get("reason", "VERIFICATION_FAILED")
        tool_calls.append(verification_call)
        _timeline_step(
            timeline,
            "POST_EXEC_VERIFICATION",
            "OK" if verification.get("verified") else "FAILED",
            verification.get("status", "UNKNOWN"),
            started_at,
        )

    turn_duration_ms = int((perf_counter() - started_at) * 1000)
    budget_status = {
        "maxToolCallsPerTurn": max_tool_calls_per_turn,
        "requestedToolCalls": requested_tool_calls,
        "executedToolCalls": len(tool_calls),
        "maxTurnDurationMs": max_turn_duration_ms,
        "turnDurationMs": turn_duration_ms,
        "withinToolBudget": requested_tool_calls <= max_tool_calls_per_turn,
        "withinTurnBudget": turn_duration_ms <= max_turn_duration_ms,
    }
    if not budget_status["withinTurnBudget"]:
        policy_result.setdefault("reasons", []).append("TURN_BUDGET_EXCEEDED")
        _timeline_step(
            timeline,
            "TURN_BUDGET",
            "FAILED",
            f"durationMs={turn_duration_ms} limitMs={max_turn_duration_ms}",
            started_at,
        )

    # 6) response assembly (evidence-first)
    response = assemble_response(
        message=message,
        intent=intent_result,
        policy=policy_result,
        tool_calls=tool_calls,
        channel=channel,
    )
    if verification:
        response["verification"] = verification
    if not budget_status["withinTurnBudget"]:
        response = {
            "responseType": "ESCALATION",
            "responseSummary": "Turn exceeded skill time budget; safe fallback triggered.",
            "message": "This request exceeded the skill time budget. Please retry or escalate to support.",
            "verification": verification,
        }
    _timeline_step(
        timeline,
        "RESPONSE_ASSEMBLED",
        "OK",
        response.get("responseType", "UNKNOWN"),
        started_at,
    )

    decision_support = _build_decision_support(intent_result, policy_result)

    # 7) audit event
    audit_event = {
        "correlationId": correlation_id,
        "requestId": request_id,
        "timestamp": timestamp,
        "channel": channel,
        "actor": {
            "userRole": user_role,
            "userIdHash": _hash_user(user_id),
            "sessionId": session_id,
        },
        "intent": {
            "name": intent_result["intent"],
            "confidence": float(intent_result["confidence"]),
            "riskTier": intent_result["riskTier"],
            "entities": intent_result.get("entities", {}),
        },
        "skill": {
            "skillId": skill_result.get("skillId"),
            "resolved": bool(skill_result.get("resolved", False)),
            "category": skill_result.get("category"),
            "reasons": skill_result.get("reasons", []),
            "maxToolCallsPerTurn": skill_result.get("maxToolCallsPerTurn"),
            "maxTurnDurationMs": skill_result.get("maxTurnDurationMs"),
        },
        "policy": {
            "decision": policy_result["decision"],
            "reasons": policy_result.get("reasons", []),
            "allowedTools": policy_result.get("allowedTools", []),
            "hitlRequired": bool(policy_result.get("hitlRequired", False)),
            "approvalId": policy_result.get("approvalId"),
            "approvalStatus": policy_result.get("approvalStatus"),
            "killSwitchesActive": policy_result.get("killSwitchesActive", []),
        },
        "toolCalls": tool_calls,
        "budgets": budget_status,
        "timeline": timeline,
        "decisionSupport": decision_support,
        "outcome": {
            "responseType": response["responseType"],
            "responseSummary": response.get("responseSummary", ""),
            "citations": response.get("citations", []),
            "killSwitchesActive": policy_result.get("killSwitchesActive", []),
            "verification": verification,
        },
    }

    subject_binding = policy_result.get("subjectBinding")
    if subject_binding:
        audit_event["subjectBinding"] = subject_binding

    if "hitl" in response:
        audit_event["hitl"] = response["hitl"]

    write_audit_event(audit_event)
    _timeline_step(timeline, "AUDIT_WRITTEN", "OK", "audit.jsonl append", started_at)

    return {
        "correlationId": correlation_id,
        "intent": audit_event["intent"],
        "skill": audit_event["skill"],
        "policy": audit_event["policy"],
        "toolCalls": tool_calls,
        "budgets": budget_status,
        "timeline": timeline,
        "decisionSupport": decision_support,
        "response": {
            "message": response["message"],
            "responseType": response["responseType"],
            "responseSummary": response.get("responseSummary", ""),
            "verification": verification,
        },
        "audit": {
            "correlationId": correlation_id,
            "requestId": request_id,
            "timestamp": timestamp,
        },
    }
