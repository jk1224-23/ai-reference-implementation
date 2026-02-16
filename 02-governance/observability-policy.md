# Observability Policy

## Purpose and Scope
This policy defines minimum observability requirements for both:
- Flow A: Enterprise RAG + read-only tools
- Flow B: Bounded agent + HITL + write tools

The goal is reliable operations, safety monitoring, security response, and auditable traceability. Primary consumers are development, operations/SRE, security, and audit/compliance teams.

## Required Identifiers
All telemetry should carry consistent identifiers where applicable:
- `correlation_id` propagated end-to-end across services and tool calls
- `session_id` and/or `request_id`
- `agent_id`, `consumer_id`/`app_id`, and tenant identifier
- `model_id` and provider identifier, plus selected routing tier
- `tool_call_id`, `tool_id`, and tool contract/version
- policy version, prompt version, and tool-contract version used at decision time

## Minimum Logging Requirements (Safe by Default)
### Ingress log fields
- Timestamp, environment, service name
- `correlation_id`, `request_id`, optional `session_id`
- Tenant/app/agent identifiers
- Channel/entrypoint, route tier decision, high-level intent classification
- Request size indicators (token estimates, context size)

### Tool call decision log fields (allow/deny + reason)
- `correlation_id`, `tool_call_id`, `tool_id`, tool version
- Decision outcome: allow/deny/block
- Deny/block reason category (policy, schema, authz, budget, kill switch)
- Scope and policy versions evaluated

### Retrieval log fields
- `correlation_id`, retrieval request id
- Index/source identifier
- Opaque document/chunk ids returned and rank positions
- Retrieval confidence and budget usage (`topK`, token budget consumed)
- Explicit rule: no raw retrieved content in logs

### HITL approval audit fields
- `correlation_id`, action id, approver role/id (policy-compliant form)
- Approval decision (approve/deny/timeout)
- Decision timestamp, request timestamp, response latency
- Redaction flag and policy version used for preview generation

### Sensitive data rule
- No PHI/PII in logs by default.
- Exceptions require documented approval, scoped retention, and secure evidence handling controls.

## Minimum Metrics
### Reliability
- End-to-end latency (`p95`, `p99`)
- Error rate by stage (routing, retrieval, tool, validation)
- Throttle/timeout rate

### Safety
- Safety blocks and redaction counts
- HITL-required rate and approval/deny/timeout rates
- Policy-deny rate for tool invocation

### Tools
- Tool deny counts by reason
- Tool timeout/error rates
- Circuit breaker open events and duration

### Cost
- Tokens in/out per request and per stage
- Estimated per-request and per-tenant cost
- Cost anomaly indicators (sudden token/cost spikes)

## Tracing Requirements
At minimum, traces must include standardized span names for:
- agent turn
- retrieval
- tool call
- validation
- safety checks

Each span should include `correlation_id`, outcome status, duration, and key budget counters.

## Alerting Guidance
### SEV-1 triggers
- PHI leakage indicator in telemetry or downstream sinks
- Any write-tool execution path without required HITL approval
- Abnormal cost spike above defined incident threshold

### SLO breach triggers
- Sustained latency SLO breach (`p95`/`p99`)
- Sustained error-rate increase
- Elevated tool timeout/circuit-breaker-open conditions

## Retention Guidance
- Operational logs: short-to-medium retention for day-to-day reliability and tuning.
- Secure evidence store: restricted-access, incident-focused retention for forensic/audit needs only.
- Retention windows must align with legal, compliance, and data minimization requirements.

## Definition of Done
- End-to-end `correlation_id` propagation is implemented and verified.
- Required identifiers are present in logs, metrics labels, and traces.
- Ingress, retrieval, tool-decision, and HITL audit logs are defined.
- PHI/PII-safe logging defaults are enforced.
- Reliability, safety, tool, and cost metric baselines are live.
- Standard tracing spans are adopted across the request lifecycle.
- SEV-1 and SLO alerts are configured and tested.
- Retention tiers are documented (operational vs secure evidence).
- Version metadata (policy/prompt/tool-contract) is captured in telemetry.
- Runbooks reference observability signals for incident triage.
