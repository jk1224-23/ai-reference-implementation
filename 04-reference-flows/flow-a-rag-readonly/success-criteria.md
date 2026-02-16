# Flow A Success Criteria

## Purpose
Define measurable success criteria for Flow A (Enterprise RAG + read-only tools), aligned with the evaluation plan.

## 1) Quality Criteria
- Groundedness: >= 95% of golden-set answers that require evidence include valid source references.
- Correctness: >= 90% of golden-set answers match expected factual points.
- Completeness: >= 85% of answers include all required key points from expected answer rubrics.
- Pass signal: criteria above are met on release-gating evaluation runs.

## 2) Retrieval Criteria
- Coverage: retrieval returns at least one relevant source for >= 95% of golden-set queries.
- Evidence budget behavior: `topK` and token/context limits are always enforced; no budget bypass.
- Empty/low-confidence handling: when confidence is below threshold, system abstains or returns constrained response with clarification prompt.
- Pass signal: no unsupported high-confidence answers when retrieval confidence is low.

## 3) Safety Criteria
- No PHI/PII leakage in user responses beyond policy-authorized minimum disclosure.
- Safe refusal behavior for disallowed requests is consistent and policy-aligned.
- Injection resilience: user/document/tool-output injection tests do not cause policy bypass or unauthorized tool invocation.
- Pass signal: zero critical safety violations in gated runs.

## 4) Reliability Criteria
- Latency expectations: end-to-end p95 and p99 remain within agreed SLO targets.
- Fallback behavior: model throttles/outages trigger routing fallback without losing request traceability.
- Tool timeout handling: read-only tool failures degrade gracefully to retrieval-only path when possible.
- Pass signal: no uncontrolled failures for modeled outage/timeout scenarios.

## 5) Cost and Budget Criteria
- Token budgets respected per request and per stage (prompt, retrieval context, response).
- Tool-call budgets enforced per request/turn.
- Cost variance remains within agreed operational guardbands.
- Pass signal: no budget-policy violations in evaluation and canary telemetry.

## 6) Observability Criteria
- Required IDs captured end-to-end: `correlation_id`, `request_id` (and session/app/tenant where applicable).
- Route decision, fallback reason, and budget usage are logged as metadata.
- Logs remain audit-safe: no raw PHI/PII by default; opaque source identifiers used.
- Pass signal: observability checks pass for required fields and redaction policy.

## Definition of Done
- Quality thresholds are documented and measured.
- Retrieval behavior includes budget enforcement and low-confidence handling.
- Safety criteria include leakage prevention and injection resistance.
- Reliability criteria include fallback and timeout behavior.
- Token/tool budgets are defined and enforced.
- Required observability identifiers are consistently captured.
- Audit-safe logging constraints are validated.
- Criteria are mapped to evaluation suites in the eval plan.
