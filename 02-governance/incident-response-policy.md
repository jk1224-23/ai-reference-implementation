# Incident Response Policy

## Purpose and Scope
This policy defines incident response requirements for enterprise AI systems operating in:
- **Flow A**: RAG + read-only tools
- **Flow B**: Bounded agent + HITL + write tools

It covers reliability, safety, security, compliance, and business-impact incidents across model routing, retrieval, tool execution, and approval workflows.

## Incident Categories
- **Sensitive data disclosure (PHI/PII)**
- **Prompt injection/jailbreak spike**
- **Tool misuse/abuse** (unexpected tool calls, abnormal cost surge)
- **Hallucination with business impact** (incorrect output leading to decisions/actions)
- **Availability/latency outage** (degraded or unavailable user/service path)

## Severity Levels
| Severity | Description | Example |
|---|---|---|
| SEV-1 | Critical security/compliance or production integrity breach requiring immediate containment | PHI exposed in outputs/logs; write tool executed without required HITL |
| SEV-2 | Major business-impacting incident with limited containment window | Prompt injection campaign causing broad unsafe responses; sustained write-tool abuse/cost spike |
| SEV-3 | Moderate impact, localized or recoverable without major customer harm | Hallucinated answer with workflow disruption for a subset of users |
| SEV-4 | Low impact or near miss with no material customer harm | Short latency regression, transient non-critical tool timeout trend |

## Mandatory Operational Controls (Must Exist)
- Kill switches:
  - KB-only mode
  - HITL-first mode
  - Disable all write tools
  - Disable specific `tool_id`
  - Disable memory/persistence
- Model/provider failover control via routing override.
- Rate-limit and budget-tightening switch for containment.

## Triage Requirements
- Capture and preserve `correlation_id` for all affected requests.
- Determine blast radius by tenant, app, agent, tool, model route, and time window.
- Notify required stakeholders by severity:
  - Platform/Ops
  - Security
  - Compliance/Privacy (when regulated/sensitive data risk exists)

## Evidence Bundle Policy
For each incident, capture:
- Incident timeline and severity declaration history.
- Affected identifiers (`correlation_id`, request ids, tool_call ids, policy/prompt/tool-contract versions).
- Routing decisions, fallback events, and kill-switch states.
- Relevant logs/metrics/traces and approval records (if HITL involved).
- Containment actions, recovery actions, and verification results.

Storage requirements:
- Store evidence in a restricted secure evidence repository with access controls and retention policy.
- **No PHI in tickets** by default; ticketing systems should reference secure evidence locations, not raw sensitive content.

## Recovery Policy
- **Rollback vs forward-fix criteria**:
  - Roll back when a recent change is clearly causal and reversible.
  - Forward-fix when rollback risk is higher or issue is systemic/configurational.
- **Canary requirements for restore**:
  - Restore in phased canary with strict guardrails and elevated monitoring.
- **Evaluation gate before return to normal**:
  - Pass regression checks for safety, quality, routing, and tool controls before removing containment switches.

## Postmortem Requirements
- Document root cause and contributing factors.
- Define corrective actions with owners and due dates.
- Add/adjust tests and detection rules to prevent recurrence.
- Update policy/architecture/runbook documentation based on findings.

## Definition of Done
- Incident category and severity were assigned and recorded.
- Containment controls were applied and timestamped.
- Blast radius analysis completed (tenant/app/agent/tool scope).
- Required stakeholders were notified by severity policy.
- Evidence bundle captured in secure repository.
- Tickets contain no PHI/PII by default.
- Recovery path selected with rollback/forward-fix rationale.
- Canary restore executed with explicit success criteria.
- Regression evaluation gate passed before normal mode restored.
- Postmortem completed with actions, owners, and due dates.
- Detection/tests/documentation were updated from learnings.
