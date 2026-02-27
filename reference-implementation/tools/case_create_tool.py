from __future__ import annotations

import hashlib
import time
from threading import Lock


_IDEMPOTENCY_LOCK = Lock()
_IDEMPOTENCY_CACHE: dict[str, dict] = {}


def case_create(
    subject: str,
    description: str,
    claim_id: str,
    approval_id: str,
    idempotency_key: str | None = None,
) -> dict:
    """Mock transactional tool requiring approvalId.

    Demo idempotency behavior:
    - If idempotency_key repeats, return the previously generated result.
    - Cache is in-memory only; production should use durable storage.
    """
    start = time.time()

    if not approval_id:
        return {
            "result": "BLOCKED",
            "error": {"code": "HITL_APPROVAL_REQUIRED", "message": "approvalId required"},
        }

    if idempotency_key:
        with _IDEMPOTENCY_LOCK:
            existing = _IDEMPOTENCY_CACHE.get(idempotency_key)
            if existing:
                replay = dict(existing)
                replay["idempotencyReplay"] = True
                replay["durationMs"] = int((time.time() - start) * 1000)
                return replay

    # Deterministic identifier for repeatable demos/tests.
    key_basis = idempotency_key or f"{claim_id}:{approval_id}"
    suffix = hashlib.sha256(key_basis.encode("utf-8")).hexdigest()[:6].upper()
    case_id = f"CASE-{claim_id or 'unknown'}-{suffix}"
    dur = int((time.time() - start) * 1000)
    response = {
        "caseId": case_id,
        "status": "PENDING_REVIEW",
        "durationMs": dur,
        "subject": subject,
        "description": description,
        "idempotencyReplay": False,
    }
    if idempotency_key:
        with _IDEMPOTENCY_LOCK:
            _IDEMPOTENCY_CACHE[idempotency_key] = dict(response)
    return response
