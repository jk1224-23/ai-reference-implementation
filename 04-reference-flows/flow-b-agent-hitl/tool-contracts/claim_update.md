# Tool Contract: Claim_Update

## 1) Tool Identity
| Field | Value |
|---|---|
| tool_id | `Claim_Update` |
| name | Claim Update Action |
| owner | Claims Operations Platform Team |
| version | v1.0 |
| status | Active (Controlled) |

## 2) Purpose
### When to use
- Apply approved, bounded updates to claim records in controlled workflows.
- Execute state changes only after policy checks and HITL approval.

### When not to use
- Any unapproved or out-of-scope claim mutation.
- Bulk updates outside approved workflow controls.
- Any production write request lacking HITL or idempotency requirements.

## 3) Side Effects and Rollback Notes
- Side effects:
  - Updates claim state and associated workflow attributes in system of record.
  - Emits audit events and downstream notifications where configured.
- Rollback notes (high level):
  - Prefer compensating action or controlled status reversion via approved process.
  - Rollback path must follow incident/recovery policy and preserve audit integrity.

## 4) Input Schema
### Required identifiers
- `claim_id` (opaque claim identifier)
- `tenant_id` (where applicable)
- `idempotency_key` (mandatory)

### Allowed update fields (allowlist)
- `status` (enum allowlist)
- `status_reason_code` (enum allowlist)
- `priority_level` (bounded enum)
- `assignment_group` (allowlisted values)
- `note_summary` (length-limited, sanitized)

### Validation rules
- Reject unknown fields.
- Enforce enum/range/length constraints.
- Reject attempts to modify non-allowlisted claim attributes.
- Require valid `idempotency_key` format and replay window compliance.

## 5) Output Schema
| Field | Type | Description |
|---|---|---|
| operation_status | String | `SUCCESS`, `NO_OP_IDEMPOTENT`, or `FAILED` |
| updated_entity_summary | Object | Redacted summary of post-update claim state |
| correlation_id | String | End-to-end trace identifier |
| policy_outcome | String | Approval/policy result summary |

## 6) Mandatory Policy Constraints
- HITL is required in production for write execution.
- Tool execution is deny-by-default and must be explicitly allowlisted.
- Least-privilege scopes are mandatory for caller and service identity.

## 7) Behavioral Guarantees
- Idempotency:
  - Repeated requests with same `idempotency_key` and identical payload return non-duplicative result.
- Conflict handling:
  - Concurrent or incompatible updates return deterministic conflict errors.
- Timeouts/retries:
  - Retries for writes are cautious, bounded, and idempotency-aware.
  - No blind retries that risk duplicate mutation.

## 8) Security and Compliance
- PHI stance:
  - Claim data may contain regulated/sensitive fields; apply strict minimization.
- Logging/redaction:
  - No raw PHI/PII in logs by default.
  - Log metadata, outcome codes, and opaque identifiers.
- Audit events required:
  - Proposal, approval outcome, execution attempt, execution result, and actor/context identifiers.

## 9) Error Model
Standard error envelope fields:
- `error_code`
- `error_message`
- `correlation_id`
- `retryable`

Common codes:
- `INVALID_ARGUMENT`
- `UNAUTHORIZED`
- `PERMISSION_DENIED`
- `HITL_REQUIRED`
- `HITL_DENIED`
- `HITL_TIMEOUT`
- `CONFLICT`
- `IDEMPOTENCY_VIOLATION`
- `RATE_LIMITED`
- `TIMEOUT`
- `UPSTREAM_UNAVAILABLE`

## 10) Contract Test Checklist
- Write request without HITL approval is blocked in production mode.
- Deny and timeout approval outcomes block execution.
- Missing or malformed `idempotency_key` is rejected.
- Replay with same key does not produce duplicate mutation.
- Unknown or non-allowlisted update fields are rejected.
- Enum/range/length validation is enforced.
- Conflict scenarios return deterministic `CONFLICT` handling.
- Retry logic remains bounded and idempotency-safe.
- Audit events capture approval and execution lifecycle with `correlation_id`.
- Logs remain redacted and PHI/PII-safe by default.
