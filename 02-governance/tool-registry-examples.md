# Tool Registry Examples

These examples show how policy-conformant registry entries map to:
- **Flow A**: `KB_Search` and `Provider_Search` (read-only)
- **Flow B**: `Claim_Update` (write, HITL + idempotency required)

## Example Entry 1: KB_Search (Read-Only)
```yaml
tool_id: KB_Search
name: Knowledge Base Search
version: v1.0
owner: Enterprise Knowledge Platform Team
status: active
risk_level: medium
data_classification: internal_sensitive
side_effects: read_only
allowed_environments: [dev, test, prod]
required_scopes: [knowledge.read]
input_schema_ref: ../04-reference-flows/flow-a-rag-readonly/tool-contracts/kb_search.md#3-input-schema
output_schema_ref: ../04-reference-flows/flow-a-rag-readonly/tool-contracts/kb_search.md#4-output-schema
timeouts_ms: 3000
retry_policy: transient_read_retry_bounded
rate_limits:
  steady_rps: 20
  burst_rps: 40
budgets:
  max_calls_per_turn: 2
  max_calls_per_session: 20
requires_HITL: false
kill_switch_flags:
  tool_disabled: false
  category_disabled: false
audit_events_required:
  - TOOL_CALL_REQUESTED
  - TOOL_CALL_ALLOWED_OR_DENIED
  - TOOL_CALL_COMPLETED_OR_FAILED
```

## Example Entry 2: Provider_Search (Read-Only)
```yaml
tool_id: Provider_Search
name: Provider Directory Search
version: v1.0
owner: Provider Data Services Team
status: active
risk_level: medium
data_classification: internal_sensitive
side_effects: read_only
allowed_environments: [dev, test, prod]
required_scopes: [provider.read]
input_schema_ref: ../04-reference-flows/flow-a-rag-readonly/tool-contracts/provider_search.md#3-input-schema
output_schema_ref: ../04-reference-flows/flow-a-rag-readonly/tool-contracts/provider_search.md#4-output-schema
timeouts_ms: 2500
retry_policy: transient_read_retry_bounded
rate_limits:
  steady_rps: 15
  burst_rps: 30
budgets:
  max_calls_per_turn: 2
  max_calls_per_session: 15
requires_HITL: false
kill_switch_flags:
  tool_disabled: false
  category_disabled: false
audit_events_required:
  - TOOL_CALL_REQUESTED
  - TOOL_CALL_ALLOWED_OR_DENIED
  - TOOL_CALL_COMPLETED_OR_FAILED
```

## Example Entry 3: Claim_Update (Write, HITL + Idempotency)
```yaml
tool_id: Claim_Update
name: Claim Update Action
version: v1.0
owner: Claims Operations Platform Team
status: active_controlled
risk_level: high
data_classification: phi_regulated
side_effects: write
allowed_environments: [dev, test, prod]
required_scopes: [claim.write.limited]
input_schema_ref: ../04-reference-flows/flow-b-agent-hitl/tool-contracts/claim_update.md#4-input-schema
output_schema_ref: ../04-reference-flows/flow-b-agent-hitl/tool-contracts/claim_update.md#5-output-schema
timeouts_ms: 4000
retry_policy: idempotent_write_retry_guarded
rate_limits:
  steady_rps: 5
  burst_rps: 10
budgets:
  max_calls_per_turn: 1
  max_calls_per_session: 5
requires_HITL: true
kill_switch_flags:
  tool_disabled: false
  category_disabled: false
audit_events_required:
  - APPROVAL_REQUESTED
  - APPROVAL_DECISION_RECORDED
  - WRITE_EXECUTION_ATTEMPTED
  - WRITE_EXECUTION_RESULT
```

## Mapping Note
- `KB_Search` and `Provider_Search` implement Flow A’s read-only enrichment pattern.
- `Claim_Update` implements Flow B’s controlled write path with mandatory HITL and idempotency protections.
