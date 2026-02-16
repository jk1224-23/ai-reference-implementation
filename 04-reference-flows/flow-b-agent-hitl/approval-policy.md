# Flow B Approval Policy

## Purpose
Define the human-in-the-loop (HITL) approval policy for Flow B (bounded agent + write tools), with clear controls for safety, auditability, and operational consistency.

## 1) When Approval Is Required
Approval is required by default for any write-tool execution in production.

Additional high-risk conditions that require approval:
- Sensitive-domain updates or regulated data impact.
- Irreversible or high-blast-radius actions.
- Elevated risk score from policy/routing controls.
- Incident-containment mode where HITL-first is enforced.

## 2) Agent Submission Requirements
Before requesting approval, the agent must provide:
- Intent summary.
- `tool_id` and tool version.
- Redacted argument preview (no PHI by default).
- Expected side effects.
- Confirmation that `idempotency_key` is present.
- High-level rollback or compensating-action guidance.

## 3) Approver UX Expectations
Approver actions:
- Approve
- Deny
- Request clarification

Timeout policy:
- Approval requests have a defined timeout window.
- Timeout is treated as deny by default.
- No write execution occurs after timeout unless a new approval request is issued.

## 4) Audit Requirements
Every approval workflow must capture:
- `correlation_id`
- Approver identity (role-based identifier)
- Request, decision, and completion timestamps
- Decision outcome and reason

## 5) Safety Constraints
- Tool access remains deny-by-default.
- Least-privilege scopes are mandatory for callers and services.
- No bypass paths are permitted around approval controls.

## 6) Failure Handling
- Approval denied:
  - Block execution and return no-action outcome with next-step guidance.
- Approval timeout:
  - Block execution and mark request as timed out; require new approval cycle.
- Tool conflict or partial failure after approval:
  - Return deterministic failure status.
  - Apply idempotent retry rules where permitted.
  - Follow rollback/compensating-action guidance and incident policy.

## Definition of Done
- Approval-required conditions are explicitly defined.
- Agent submission bundle includes all required decision fields.
- Approver actions include approve/deny/clarify.
- Timeout behavior is deterministic and blocks execution.
- Audit fields are captured and queryable.
- Deny-by-default and least-privilege controls are enforced.
- No bypass paths exist in production workflow.
- Failure handling covers denial, timeout, and post-approval execution errors.
