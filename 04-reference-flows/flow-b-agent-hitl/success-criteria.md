# Flow B Success Criteria

## Purpose
Define measurable success criteria for Flow B (bounded agent + HITL + write tools), aligned with the evaluation plan.

## 1) Safety Invariants (Must Always Hold)
- Write actions require HITL approval in production.
- Deny-by-default tool policy is enforced for all tool calls.
- Idempotency is required for all write tools.
- No PHI/PII in logs by default.
- Pass signal: zero violations of any invariant in gated evaluation and canary.

## 2) Workflow Correctness Criteria
- Action proposal quality:
  - Each write-intent proposal includes `intent`, `tool_id`, and arguments.
- Approver preview quality:
  - Preview is redacted, understandable, and includes impact-relevant context.
- Approval path behavior:
  - Approve path executes once with policy-compliant constraints.
  - Deny path blocks execution and returns controlled no-action response.
  - Timeout path is treated as deny by default.
- Post-execution verification:
  - When applicable, a read-back/verification step confirms resulting state before user confirmation.
- Pass signal: all HITL and post-exec workflow tests pass.

## 3) Reliability Criteria
- Conflict handling: write conflicts return deterministic, policy-safe errors.
- Retry behavior: retries are bounded and respect idempotency/replay rules.
- Rollback guidance: partial failures produce clear rollback/compensating-action direction per policy.
- Pass signal: no duplicate writes and no uncontrolled retry loops in failure simulations.

## 4) Cost and Budget Criteria
- Tool-call limits enforced per request and per workflow stage.
- Planner/tool loop prevention controls trigger before budget exhaustion.
- Token and execution budgets remain within defined operational guardrails.
- Pass signal: no budget-limit bypasses in evaluation and canary runs.

## 5) Observability and Audit Criteria
- `correlation_id` is propagated across proposal, approval, and execution stages.
- Approval events are captured with outcome (`approve`/`deny`/`timeout`) and timestamps.
- Audit logs include tool identifiers, policy versions, and idempotency outcomes.
- Logs remain redacted and compliant with no PHI/PII-by-default policy.
- Pass signal: required audit fields are complete and queryable for each write attempt.

## Definition of Done
- Safety invariants are explicit and enforced in tests.
- Action proposal contract is validated (`intent`, `tool_id`, args).
- Approver preview quality and redaction requirements are met.
- Approve/deny/timeout paths are deterministic and tested.
- Post-execution verification behavior is defined and tested where applicable.
- Conflict/retry behavior respects idempotency and replay protection.
- Tool-call and loop budgets are enforced.
- Required observability/audit fields are captured end-to-end.
- Criteria are mapped to evaluation suites in the eval plan.
