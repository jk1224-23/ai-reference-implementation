from __future__ import annotations

import re
from typing import Iterable

# Config-driven intent mapping (demo).
# Production replacement: external intent service/LLM classifier returning the same contract.
# Input: (message, channel) -> Output: {intent, confidence, riskTier, entities}


def classify_intent(message: str, channel: str) -> dict:
    text = message.lower().strip()
    claim_id = _extract_claim_id(text)

    # Obvious prompt-injection / policy-bypass patterns map to high-risk unknown.
    if _matches(text, any_terms=("ignore",), all_terms=(("polic", "rules"), ("dump", "all claims"))):
        return _result("UNKNOWN_OR_BLOCKED", 0.62, "HIGH")

    if _matches(text, any_terms=("appeal", "grievance")):
        return _result("APPEAL_INITIATION", 0.78, "HIGH", _entities(claim_id))

    if _matches(text, any_terms=("status", "check"), all_terms=("claim",)):
        conf = 0.86 if claim_id else (0.65 if channel == "voice" else 0.72)
        return _result("CLAIM_STATUS", conf, "MEDIUM", _entities(claim_id))

    if _matches(text, any_terms=("policy", "benefit", "benefits", "coverage", "covered", "explain")):
        return _result("POLICY_EXPLANATION", 0.75, "LOW")

    if _matches(text, any_terms=("faq", "how do i")):
        return _result("FAQ_GENERAL", 0.70, "LOW")

    return _result("UNKNOWN_OR_BLOCKED", 0.60, "HIGH")


def _matches(text: str, *, any_terms: tuple[str, ...], all_terms: Iterable[tuple[str, ...] | str] = ()) -> bool:
    if any_terms and not any(term in text for term in any_terms):
        return False

    for group in all_terms:
        if isinstance(group, str):
            if group not in text:
                return False
            continue
        if not any(token in text for token in group):
            return False

    return True


def _result(intent: str, confidence: float, risk_tier: str, entities: dict | None = None) -> dict:
    return {
        "intent": intent,
        "confidence": confidence,
        "riskTier": risk_tier,
        "entities": entities or {},
    }


def _extract_claim_id(text: str) -> str | None:
    m = re.search(r"\bclaim\s+(\d{4,})\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{5,})\b", text)
    return m.group(1) if m else None


def _entities(claim_id: str | None) -> dict:
    return {"claimId": claim_id} if claim_id else {}
