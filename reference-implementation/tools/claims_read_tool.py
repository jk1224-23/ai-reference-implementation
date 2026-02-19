import time

from app.demo_data import get_claim


def claims_read(claim_id: str) -> dict:
    start = time.time()
    if not claim_id:
        return {
            "result": "FAILED",
            "error": {"code": "VALIDATION_ERROR", "message": "Missing claimId"},
        }

    claim = get_claim(claim_id)
    if not claim:
        return {
            "result": "FAILED",
            "error": {"code": "NOT_FOUND", "message": f"Claim {claim_id} not found"},
        }

    dur = int((time.time() - start) * 1000)
    return {
        "claimId": claim_id,
        "memberId": claim.get("memberId"),
        "status": claim.get("status", "Unknown"),
        "lastUpdated": claim.get("lastUpdated", ""),
        "durationMs": dur,
    }
