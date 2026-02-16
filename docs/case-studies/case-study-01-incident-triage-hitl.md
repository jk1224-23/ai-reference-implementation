# Case Study 01: Agent + HITL — Incident Triage + Change Request Approvals

## Goal
Demonstrate a bounded-agent reference workflow for incident triage where recommended actions and change requests are routed through human approval before any production-impacting write action.

## Non-Goals
- Full autonomous remediation in production.
- Vendor-specific implementation details.
- Organization-specific process or tooling names.

## Actors and Roles
- **Enterprise User (Operator):** Submits incident context and receives triage guidance.
- **Agent Runtime:** Proposes next actions and candidate change requests.
- **Policy Engine:** Evaluates risk, tool eligibility, and approval requirements.
- **Human Approver:** Reviews redacted action preview and decides approve/deny.
- **Platform/Admin:** Maintains policy, tool allowlists, and operational controls.

## Boundaries
- **Flow A boundary:** Retrieval and read-only enrichment for incident context.
- **Flow B boundary:** Action proposals can progress to write execution only after policy pass and HITL approval.
- **Data boundary:** Sensitive fields are minimized and redacted in logs and approval previews.

## Happy Path Flow
1. Operator submits incident summary and scope.
2. System performs retrieval for runbooks/history and generates a triage recommendation.
3. Agent proposes a change request with structured intent, tool identifier, and arguments.
4. Policy engine checks allowlist, risk, scopes, and idempotency requirements.
5. HITL approval task is presented with redacted impact summary.
6. Approver accepts request.
7. Write tool executes once with idempotency protection.
8. Result is verified and returned to operator with audit references.

## HITL Policy
- Required for state-changing actions in production.
- Approval payload includes intent summary, tool/version, redacted args, expected side effects, and rollback hint.
- Timeout defaults to deny; no write action proceeds without explicit approval.

## Tool Contract Enforcement
- Deny-by-default tool posture.
- Strict input schema validation (unknown fields rejected).
- Least-privilege scope checks before invocation.
- Idempotency key required for write actions; replay attempts are blocked.

## Audit and Observability
- `correlation_id` propagated across request, approval, and tool execution.
- Audit events captured for proposal, policy decision, approval outcome, execution attempt, and final result.
- Observability captures latency, error, safety, and cost dimensions without logging raw sensitive content by default.

## Failure Handling
- **Approval denied/timeout:** Workflow returns no-action outcome with escalation guidance.
- **Tool conflict/transient failure:** Retry only within idempotency-safe policy; otherwise return controlled failure.
- **Partial failure:** Use compensating action guidance and incident containment controls.
- **Containment mode:** Enforce HITL-first or restrict to read-only/knowledge-only operation.

## Evaluation
### Offline
- Golden scenarios for incident classification and recommendation quality.
- Injection tests across user prompt, retrieved content, and tool-output vectors.
- Tool contract tests for validation, deny paths, and idempotency behavior.

### Online
- Canary rollout with approval-path monitoring.
- Regression gate on safety invariants (no write without HITL, no PHI-in-logs by default).
- SLO monitoring for latency, error rate, and approval cycle completion.

## Definition of Done
- Workflow enforces HITL for production write actions.
- Tool contract checks pass for schema, scope, and idempotency requirements.
- Audit events are complete and queryable by `correlation_id`.
- Failure paths produce deterministic, policy-safe outcomes.
- Offline and online evaluation gates pass before expanded rollout.

## Future Enhancements
- Risk-adaptive approval thresholds with explicit policy controls.
- Stronger post-execution verification with automated read-back checks.
- Expanded scenario library for edge-case incident classes and failure injections.
