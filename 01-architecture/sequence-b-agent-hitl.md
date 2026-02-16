# Flow B Sequence: Bounded Agent + HITL + Write Tools

## Context Note
Flow B is an extension of Flow A and is typically enabled after Flow A is stable in production with governance controls in place (tool registry enforcement, routing/fallback, observability, and incident runbooks).

## Assumptions
- Write tools are disabled by default and enabled only via explicit allowlist.
- HITL approval is required for any state-changing action in production.
- Idempotency keys are mandatory for all write actions.
- Full audit trail is required with end-to-end `correlation_id` propagation.

## End-to-End Sequence
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Channel UI (Chat)
    participant Agent as AI Orchestrator/Agent (Planner)
    participant Router as Router (Model Tier Selection)
    participant RAG as Retrieval Service (Optional Grounding)
    participant Gate as Tool Registry Enforcement (Allow/Deny + Policy)
    actor Approver as Human Approver (HITL)
    participant Write as Write Tool (Claim_Update / Case_Create)
    participant SoR as Systems of Record (Downstream)
    participant Safe as Safety/Validation
    participant Obs as Observability/Audit (Logs/Metrics/Traces + Audit Sink)

    User->>UI: Request action-oriented outcome
    UI->>Agent: Send request + identity context
    Agent->>Obs: Start trace + correlation_id

    Agent->>Router: Route by intent/risk/SLA
    Router-->>Agent: Model tier selected
    Agent->>Obs: Record routing decision

    opt Grounding needed before action
        Agent->>RAG: Retrieve supporting evidence
        RAG-->>Agent: Evidence + confidence
        Agent->>Obs: Record retrieval usage
    end

    Agent->>Safe: Pre-exec validation (intent/tool/args sanity)
    Safe-->>Agent: Validation result

    Agent->>Gate: Propose action (intent + tool_id + args + risk)
    Gate->>Gate: Allowlist + scope + policy checks

    alt Kill switch active (tool disabled / HITL-first / KB-only)
        Gate-->>Agent: Reject write path or force restricted mode
        Agent->>Obs: Emit kill-switch enforcement event
        Agent-->>UI: Return restricted-mode response
        UI-->>User: Explain action unavailable / KB-only fallback
    else Write path permitted
        Gate->>Gate: Require HITL due to write tool/risk level
        Gate->>Approver: Show redacted preview (action + args + impact)

        alt Approval denied or timeout
            Approver-->>Gate: Deny / no response in SLA
            Gate-->>Agent: Approval failed
            Agent->>Obs: Emit approval denial/timeout audit event
            Agent-->>UI: Return no-action outcome + next steps
            UI-->>User: Display denial/timeout message
        else Approved
            Approver-->>Gate: Approve
            Gate->>Gate: Apply idempotency key + replay protection
            Gate->>Write: Execute write action

            alt Write success
                Write->>SoR: Persist state change
                SoR-->>Write: Commit result
                Write-->>Gate: Action result + identifiers
                Gate-->>Agent: Approved write outcome
                Agent->>Obs: Emit write success audit event

                opt Post-execution verification
                    Agent->>Gate: Invoke read-only verification tool
                    Gate-->>Agent: Read-back state/result
                end

                Agent->>Safe: Post-exec confirmation formatting + redaction
                Safe-->>UI: User-safe confirmation
                UI-->>User: Confirm completed action
            else Conflict / retryable error
                Write-->>Gate: Conflict or transient failure
                Gate-->>Agent: Error + retry guidance
                Agent->>Obs: Emit failure + retry/audit event
                Agent-->>UI: Return controlled failure response
                UI-->>User: Show retry/alternate path
            end
        end
    end
```

## Decision Points Called Out
- Agent proposes action with explicit `intent`, `tool_id`, and arguments.
- Enforcement layer requires HITL because request is write-capable and risk-scored.
- Approver receives a redacted action preview and approves or denies.
- Idempotency key is applied before execution to prevent replay/duplicate writes.
- Post-execution verification performs read-back using a read-only capability when applicable.
- Kill switch path can force tool disablement, HITL-first hard mode, or KB-only operating mode.

## Safety Invariants
- Deny-by-default tools.
- Least-privilege scopes.
- No raw PHI in logs.
- Bounded tool call budgets.
- Approvals recorded.

## Failure Modes and Handling
- Approval timeout/denial:
  - No write is executed; return a no-action outcome and escalation path.
- Write tool conflict/retryable errors:
  - Use controlled retries under idempotency rules; surface deterministic retry guidance.
- Partial failure and rollback guidance:
  - Record action phase boundaries and apply compensating/rollback procedures per runbook.
- Incident containment mode:
  - Enable kill switches, restrict to KB-only/read-only behavior, and route to ops escalation.
