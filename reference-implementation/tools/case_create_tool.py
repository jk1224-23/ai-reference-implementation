import hashlib
import time


def case_create(subject: str, description: str, claim_id: str, approval_id: str) -> dict:
    """Mock transactional tool requiring approvalId."""
    start = time.time()

    if not approval_id:
        return {
            "result": "BLOCKED",
            "error": {"code": "HITL_APPROVAL_REQUIRED", "message": "approvalId required"},
        }

    # Deterministic identifier for repeatable demos/tests.
    suffix = hashlib.sha256(f"{claim_id}:{approval_id}".encode("utf-8")).hexdigest()[:6].upper()
    case_id = f"CASE-{claim_id or 'unknown'}-{suffix}"
    dur = int((time.time() - start) * 1000)
    return {
        "caseId": case_id,
        "status": "PENDING_REVIEW",
        "durationMs": dur,
        "subject": subject,
        "description": description,
    }
