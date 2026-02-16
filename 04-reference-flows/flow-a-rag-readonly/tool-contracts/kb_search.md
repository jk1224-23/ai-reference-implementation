# Tool Contract: KB_Search

## 1) Tool Identity
| Field | Value |
|---|---|
| tool_id | `KB_Search` |
| name | Knowledge Base Search |
| owner | Enterprise Knowledge Platform Team |
| version | v1.0 |
| status | Active |

## 2) Purpose
### When to use
- Retrieve enterprise knowledge snippets and source references for grounded answers.
- Resolve policy/process questions requiring citation to approved sources.

### When not to use
- Any state-changing operation.
- Transactional lookups requiring system-of-record writes.
- Requests that require privileged data beyond caller scope.

## 3) Input Schema
| Field | Required | Type | Validation / Limits |
|---|---|---|---|
| query_text | Yes | String | 3-1000 characters; trimmed; no empty query |
| filters | No | Object | Allowed keys only: `source_type`, `domain`, `effective_date_range` |
| top_k | No | Integer | Range 1-20; default 5 |
| cursor | No | String | Opaque paging token from prior response |
| locale | No | String | BCP-47 style tag if provided |

Validation rules:
- Reject unknown fields.
- Reject invalid ranges/types.
- Enforce caller scope constraints on filtered domains.

## 4) Output Schema
| Field | Type | Description |
|---|---|---|
| results | List | Ordered result list |
| results[].result_id | String | Opaque result identifier |
| results[].source_id | String | Opaque source/document identifier |
| results[].title | String | Source title/heading |
| results[].snippet | String | Short redacted excerpt |
| results[].score | Number | Relevance score (normalized) |
| next_cursor | String or null | Opaque token for next page |

## 5) Behavioral Guarantees
- Pagination supported via `cursor` and `next_cursor`.
- Deterministic ordering by relevance score, then stable tie-breaker.
- Response timeout target is bounded and published in operational SLOs.
- Retries are safe for transient failures because operation is read-only.

## 6) Security
- Required auth scopes: read-only knowledge scope appropriate to tenant/app role.
- Data classification: internal enterprise knowledge; may contain sensitive internal content.
- Logging/redaction rules:
  - Log opaque IDs and metadata, not raw document bodies.
  - Redact sensitive fragments in snippets where policy requires.

## 7) Error Model
Standard error envelope fields:
- `error_code`
- `error_message`
- `correlation_id`
- `retryable` (yes/no)

Common codes:
- `INVALID_ARGUMENT`
- `UNAUTHORIZED`
- `PERMISSION_DENIED`
- `RATE_LIMITED`
- `TIMEOUT`
- `UPSTREAM_UNAVAILABLE`

## 8) Observability Requirements
Required log/metric dimensions:
- `correlation_id`, `request_id`, `tool_call_id`
- `tool_id`, `tool_version`
- query size indicators (not raw query content where restricted)
- result count, timeout flag, error code
- budget metadata (`top_k`, token budget consumption indicator)

## 9) Example Calls (Structured)
| Example | Input summary | Expected outcome |
|---|---|---|
| KB-EX-01 | Query: claims escalation policy; `top_k=5` | 5 ranked snippets with source IDs and citations |
| KB-EX-02 | Query with domain filter + cursor | Next page of ordered results with `next_cursor` |
| KB-EX-03 | Query includes unknown field `debug_mode` | Rejected with `INVALID_ARGUMENT` |

## 10) Contract Test Checklist
- Valid query returns ordered results and source IDs.
- Unknown fields are rejected.
- Type/range violations are rejected.
- Unauthorized scope requests are denied.
- Pagination contract (`cursor`/`next_cursor`) is consistent.
- Timeout/error envelope is standardized.
- Logging includes required IDs and excludes raw sensitive content.
- Retry behavior is safe and bounded for transient read failures.
