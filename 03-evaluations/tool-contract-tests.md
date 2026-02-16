# Tool Contract Test Requirements

## Purpose
This document defines vendor-neutral tool contract testing requirements for:
- Flow A: read-only tools
- Flow B: write tools with HITL controls

## What Tool Contract Testing Covers
- Schema strictness, including rejection of unknown fields.
- Type and range validation for required/optional fields.
- Authorization and scope checks at enforcement layer (conceptual).
- Rate-limit and budget behavior (conceptual).
- Error envelope consistency across failures.
- Output validation, sanitization, and redaction before model/user exposure.

## Read-Only Tools (Flow A)
Read-only tools are validated for safe retrieval behavior and strict contract conformance.

Required checks:
- Valid requests are accepted with normalized outputs.
- Unknown fields are rejected deterministically.
- Type/range violations fail with consistent contract errors.
- Out-of-scope access is denied by policy/authz rules.
- Budget/rate-limit controls trigger predictable denial responses.
- Returned content is sanitized/redacted per policy.

## Write Tools (Flow B)
Write tools require all read-only checks plus write-specific controls.

Required checks:
- Mandatory HITL approval gate before execution in production mode.
- Idempotency key required and replay/duplicate protection enforced.
- Deny and timeout approval paths block execution.
- High-risk scope escalation remains blocked without proper approval/policy.
- Post-execution responses use consistent confirmation/error envelope.

## Test Case Table
| Test case | Flow | Input shape | Expected outcome |
|---|---|---|---|
| RO-Valid-Query | A | Valid `KB_Search` query with allowed filters | Accepted; normalized result returned |
| RO-Unknown-Field-Reject | A | `Provider_Search` request with extra field `debug_mode` | Rejected with schema error (unknown field) |
| RO-Type-Range-Reject | A | `Provider_Search` with invalid page size type/range | Rejected with validation error |
| RO-Scope-Deny | A | Valid shape but caller lacks permitted scope | Rejected with authorization/policy deny |
| RO-Budget-Limit | A | Repeated valid calls exceeding request/tool budget | Rejected with budget/rate-limit error envelope |
| RO-Output-Sanitize | A | Tool returns sensitive/untrusted text segments | Sensitive/untrusted content sanitized or redacted |
| WR-Missing-HITL | B | Valid `Claim_Update` write request without approval token | Rejected; execution blocked |
| WR-Approval-Deny | B | Valid write request with explicit deny outcome | Rejected; no downstream state change |
| WR-Approval-Timeout | B | Valid write request with approval timeout | Rejected; timeout treated as deny |
| WR-Missing-Idempotency | B | Valid write request without idempotency key | Rejected with policy/contract error |
| WR-Replay-Attempt | B | Duplicate write with reused idempotency key | Blocked as replay/no duplicate mutation |
| WR-Error-Envelope-Consistency | B | Downstream write failure (conflict/transient) | Consistent, policy-safe error envelope returned |

## Definition of Done
- Contract checks cover schema, type/range, and unknown-field rejection.
- Authz/scope denial behavior is tested for both flows.
- Budget/rate-limit behavior is tested with deterministic outcomes.
- Error envelopes are consistent across validation, policy, and runtime failures.
- Output sanitization/redaction checks are defined.
- Read-only and write tool suites are separated and complete.
- HITL approval/deny/timeout cases are covered for write tools.
- Idempotency and replay-protection cases are covered for write tools.
- Expected outcomes are explicit and auditable for each test case.
