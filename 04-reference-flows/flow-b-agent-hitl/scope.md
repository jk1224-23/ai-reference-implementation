# Flow B Scope: Bounded Agent + HITL

## Problem Statement
Flow B enables safe action-oriented workflows with bounded autonomy, where the agent can propose state-changing actions but execution remains controlled by policy enforcement and human approval.

## In-Scope Capabilities
- Agent proposes actions with explicit intent, tool, and argument structure.
- Tool registry enforcement is deny-by-default and outside the model.
- HITL approval is required for write actions in production.
- Idempotency keys and replay protection are enforced for write execution.
- Audit trail requirements include end-to-end `correlation_id`, approval outcome, and tool execution metadata.

## Out of Scope
- Fully autonomous write execution in production.
- Any bypass of required approvals.
- Direct model-to-tool execution without enforcement layer checks.
- Unbounded planning/tool loops without budget and stop conditions.

## Approval Policy Summary
- Approver sees a redacted preview including action intent, target entity, key fields, and estimated impact.
- Approver outcomes:
  - Approve: execution may proceed within policy constraints.
  - Deny: execution is blocked; no state change occurs.
  - Timeout: treated as deny by default.

## Success Criteria (Aligned to Eval Plan)
- 100% enforcement of HITL on write-action paths in production scenarios.
- 100% rejection of write requests missing idempotency keys.
- Replay attempts do not produce duplicate state changes.
- Approval deny and timeout paths consistently block execution.
- Tool schema and policy denials remain deterministic and auditable.
- No unauthorized tool invocation succeeds under injection tests.
- No PHI/PII appears in default logs or approval artifacts.
- Post-execution confirmation reflects verified outcome state.

## Failure Modes Summary
- Approval denied/timeout:
  - Block execution and return controlled no-action outcome.
- Write tool conflict or retryable error:
  - Apply idempotent retry rules and bounded retry policy.
- Partial failure:
  - Follow rollback or compensating-action guidance from incident policy/runbook.
- Incident containment mode:
  - Enable kill switches (disable writes, HITL-first, or KB-only fallback as needed).

## Related Architecture Documents
- Context: [C4 Context](../../01-architecture/c4-context.md)
- Sequence: [Flow B Sequence](../../01-architecture/sequence-b-agent-hitl.md)
- Decisions: [Key Decisions](../../01-architecture/key-decisions.md)
- Evaluation baseline: [Evaluation Plan](../../03-evaluations/eval-plan.md)

## Definition of Done
- Bounded-autonomy problem statement is documented.
- In-scope capabilities include enforcement, HITL, idempotency, and audit trail requirements.
- Out-of-scope boundaries explicitly prohibit autonomous writes and approval bypass.
- Approval policy covers approver view and approve/deny/timeout behavior.
- Success criteria map to evaluation plan metrics/tests.
- Failure modes include denial/timeout, conflict, and rollback guidance.
- Architecture and evaluation links are present and valid.
- Scope is vendor-neutral and implementation-agnostic.
