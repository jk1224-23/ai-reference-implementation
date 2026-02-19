from __future__ import annotations

from app.demo_data import get_claim, get_user_access

SUBJECT_REQUIRED_INTENTS = {"CLAIM_STATUS", "APPEAL_INITIATION"}


def verify_subject_binding(*, intent: str, entities: dict, user_id: str, user_role: str) -> dict:
    """
    Verifies that the request is bound to an authorized subject.
    Returns a structured result the policy engine can enforce deterministically.
    """
    if intent not in SUBJECT_REQUIRED_INTENTS:
        return {
            "required": False,
            "verified": True,
            "event": "subject_binding_not_required",
            "subject": {},
        }

    claim_id = (entities or {}).get("claimId")
    if not claim_id:
        return {
            "required": True,
            "verified": False,
            "event": "subject_binding_failed",
            "reason": "MISSING_SUBJECT_ID",
            "subject": {},
        }

    claim = get_claim(claim_id)
    if not claim:
        return {
            "required": True,
            "verified": False,
            "event": "subject_binding_failed",
            "reason": "SUBJECT_NOT_FOUND",
            "subject": {"claimId": claim_id},
        }

    member_id = claim.get("memberId")
    access = get_user_access(user_id)
    if not access:
        return {
            "required": True,
            "verified": False,
            "event": "authz_denied",
            "reason": "UNKNOWN_USER",
            "subject": {"claimId": claim_id, "memberId": member_id},
        }

    if user_role == "AGENT":
        return {
            "required": True,
            "verified": True,
            "event": "subject_binding_verified",
            "subject": {"claimId": claim_id, "memberId": member_id},
        }

    allowed_members = set(access.get("memberIds") or [])
    if member_id not in allowed_members:
        return {
            "required": True,
            "verified": False,
            "event": "authz_denied",
            "reason": "SUBJECT_NOT_AUTHORIZED",
            "subject": {"claimId": claim_id, "memberId": member_id},
        }

    return {
        "required": True,
        "verified": True,
        "event": "subject_binding_verified",
        "subject": {"claimId": claim_id, "memberId": member_id},
    }
