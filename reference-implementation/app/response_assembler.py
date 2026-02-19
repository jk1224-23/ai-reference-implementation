from __future__ import annotations

def _is_subject_binding_denial(reasons: list[str]) -> bool:
    return any(
        reason in {"SUBJECT_BINDING_REQUIRED", "MISSING_SUBJECT_ID", "SUBJECT_NOT_FOUND", "SUBJECT_NOT_AUTHORIZED", "UNKNOWN_USER"}
        for reason in reasons
    )


def _is_circuit_breaker_denial(reasons: list[str]) -> bool:
    return any(reason.startswith("TOOL_CIRCUIT_BREAKER_ACTIVE:") for reason in reasons)


def _is_approval_denial(reasons: list[str]) -> bool:
    return any(reason in {"HITL_APPROVAL_REJECTED"} for reason in reasons)


def _find_tool_success(tool_calls: list[dict], tool_name: str) -> dict | None:
    for tool_call in tool_calls:
        call_name = tool_call.get("toolName") or tool_call.get("name")
        if call_name == tool_name and tool_call.get("result") == "SUCCESS":
            return tool_call
    return None


def assemble_response(message: str, intent: dict, policy: dict, tool_calls: list[dict], channel: str) -> dict:
    decision = policy["decision"]
    intent_name = intent["intent"]
    reasons = policy.get("reasons", [])

    if decision == "DENY":
        if _is_approval_denial(reasons):
            return {
                "responseType": "ESCALATION",
                "responseSummary": "Write action denied because HITL approval was rejected.",
                "message": "That action was denied by the approver. I can help draft a revised request."
            }
        if _is_subject_binding_denial(reasons):
            return {
                "responseType": "REFUSAL",
                "responseSummary": "Denied due to missing or unauthorized subject binding.",
                "message": "I can’t access that claim in this session. Verify the claim ID and authorization, or contact support."
            }
        if _is_circuit_breaker_denial(reasons):
            return {
                "responseType": "ESCALATION",
                "responseSummary": "Denied because a required tool is temporarily disabled.",
                "message": "That action is temporarily unavailable due to a safety control. Please try again later or contact support."
            }
        return {
            "responseType": "REFUSAL",
            "responseSummary": "Refused unsafe or unmapped request; no tool executed.",
            "message": "I can’t help with that request. If you need support, I can connect you to a representative."
        }

    if decision == "DEGRADED_KB_ONLY":
        return {
            "responseType": "KB_ONLY",
            "responseSummary": "KB-only mode active; tools disabled.",
            "message": "Tools are temporarily unavailable. I can still help with general policy/FAQ questions, or connect you to support for account-specific requests."
        }

    if decision == "ALLOW_WITH_CONFIRMATION":
        return {
            "responseType": "ESCALATION",
            "responseSummary": "Voice confirmation required before tool execution.",
            "message": "I can help, but I need to confirm the claim number first. Please repeat the claim ID."
        }

    if decision == "ALLOW_HITL" and policy.get("hitlRequired", False):
        success = _find_tool_success(tool_calls, "case.create.v1")
        if success:
            case_id = (success.get("outputSummary") or {}).get("caseId", "pending")
            status = (success.get("outputSummary") or {}).get("status", "PENDING_REVIEW")
            return {
                "responseType": "TOOL_BACKED",
                "responseSummary": "Transactional action executed after approval.",
                "message": f"Appeal case {case_id} created. Status: {status}.",
            }
        approval_id = policy.get("approvalId", "approval-required")
        return {
            "responseType": "ESCALATION",
            "responseSummary": "High-risk intent; execution blocked pending human approval.",
            "hitl": {"approvalRequired": True, "approvalId": approval_id, "approvalStatus": "PENDING"},
            "message": "I can draft this request, but a representative must approve it before submission. Provide the approval ID to proceed."
        }

    # Tool-backed SoR response (MVP: claim status only)
    if intent_name == "CLAIM_STATUS" and policy["decision"] == "ALLOW":
        success = _find_tool_success(tool_calls, "claims.read.v1")
        if not success:
            return {
                "responseType": "ESCALATION",
                "responseSummary": "Tool evidence missing; did not assert SoR truth.",
                "message": "I can’t verify that right now because the system evidence wasn’t available. Please try again or contact support."
            }

        status = (success.get("outputSummary") or {}).get("status", "Unknown")
        last_updated = (success.get("outputSummary") or {}).get("lastUpdated", "")
        claim_id = (intent.get("entities") or {}).get("claimId")

        return {
            "responseType": "TOOL_BACKED",
            "responseSummary": "Returned claim status using tool evidence.",
            "message": f"Claim {claim_id} status: {status}. Last updated: {last_updated}."
        }

    return {
        "responseType": "KB_ONLY",
        "responseSummary": "Defaulted to safe response path.",
        "message": "I can help with general questions, or connect you to support for account-specific requests."
    }
