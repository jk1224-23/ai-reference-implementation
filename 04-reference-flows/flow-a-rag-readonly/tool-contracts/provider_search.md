# Tool Contract: Provider_Search

## 1) Tool Identity
| Field | Value |
|---|---|
| tool_id | `Provider_Search` |
| name | Provider Directory Search |
| owner | Provider Data Services Team |
| version | v1.0 |
| status | Active |

## 2) Purpose
### When to use
- Find provider directory information for read-only lookup workflows.
- Support Flow A responses requiring provider identity, specialty, and service-area discovery.

### When not to use
- Any provider profile update or enrollment mutation.
- Any workflow requiring write/transactional actions.
- Any request outside authorized tenant/scope boundaries.

## 3) Input Schema
| Field | Required | Type | Validation / Limits |
|---|---|---|---|
| npi | No | String | Exactly 10 digits when provided |
| name_query | No | String | 2-120 characters |
| specialty | No | String | Must match allowed specialty taxonomy value |
| location | No | Object | Allowed fields: `city`, `state`, `postal_code`, `radius_miles` |
| location.radius_miles | No | Integer | Range 1-100 |
| page_size | No | Integer | Range 1-50; default 20 |
| cursor | No | String | Opaque pagination token |

Validation rules:
- At least one of `npi` or `name_query` must be present.
- Reject unknown fields.
- Enforce type/range checks on all inputs.

## 4) Output Schema
| Field | Type | Description |
|---|---|---|
| providers | List | Ordered provider summaries |
| providers[].provider_id | String | Opaque provider identifier |
| providers[].npi | String | NPI (masked/normalized where required) |
| providers[].display_name | String | Provider display name |
| providers[].specialty | String | Primary specialty label |
| providers[].location_summary | String | City/state or service-area summary |
| total_estimate | Integer | Estimated total match count |
| next_cursor | String or null | Opaque paging token |

## 5) Behavioral Guarantees
- Stable pagination with `cursor` and `next_cursor`.
- Deterministic ordering (exact NPI match priority, then relevance).
- Bounded response timeout aligned to operational SLO.
- Safe retry behavior for transient read failures.

## 6) Security
- Required auth scopes: provider-directory read scope, tenant-constrained.
- Data classification: internal and potentially sensitive operational data.
- Logging/redaction rules:
  - Log metadata and opaque IDs; avoid raw sensitive fields where not required.
  - Apply masking/redaction for sensitive identifiers based on policy.

## 7) Error Model
Standard error envelope fields:
- `error_code`
- `error_message`
- `correlation_id`
- `retryable`

Common codes:
- `INVALID_ARGUMENT`
- `UNAUTHORIZED`
- `PERMISSION_DENIED`
- `RATE_LIMITED`
- `TIMEOUT`
- `UPSTREAM_UNAVAILABLE`

## 8) Observability Requirements
Required log/metric fields:
- `correlation_id`, `request_id`, `tool_call_id`
- `tool_id`, `tool_version`
- search mode (`npi` exact vs name/specialty/location)
- result count, page size, timeout/retry indicators
- error code and policy-deny reason where applicable

## 9) Example Calls (Structured)
| Example | Input summary | Expected outcome |
|---|---|---|
| PR-EX-01 | `npi=1234567890` | Exact provider summary returned if in-scope |
| PR-EX-02 | `name_query="Taylor"`, `specialty="Cardiology"`, location radius | Ranked provider list with paging token |
| PR-EX-03 | Input includes unknown field `include_debug` | Rejected with `INVALID_ARGUMENT` |

## 10) Contract Test Checklist
- NPI validation enforces exact 10-digit format.
- Name/specialty/location validation enforces type and limits.
- Unknown fields are rejected.
- Scope/authz failures are denied with consistent error envelope.
- Pagination behavior is stable and deterministic.
- Timeout and transient error handling are standardized.
- Observability fields are present for success and failure cases.
- Sensitive data handling follows redaction policy.
