# Flow A Sequence: Enterprise RAG + Read-Only Tools

> **Status:** Architecture-focused | Vendor-neutral | Flow A + Flow B  
> **Flows:** Flow A (RAG + Read-Only Tools) | Flow B (Bounded Agent + HITL + Write Tools)  
> **Start Here:** [Reading Guide](../00-overview/reading-guide.md) | [Flow A Scope](../04-reference-flows/flow-a-rag-readonly/scope.md) | [Key Decisions](key-decisions.md)

## TL;DR
- Flow A routes requests, retrieves evidence, and optionally uses read-only tools.
- Tool usage is gated by allowlist and schema validation outside the model.
- Fallbacks handle model throttles and tool failures without mutating systems.
- Safety/validation determines final response release and observability records outcomes.

## Navigation
- Overview: [`00-overview/readme.md`](../00-overview/readme.md) | [`00-overview/reading-guide.md`](../00-overview/reading-guide.md)
- Architecture: [`01-architecture/key-decisions.md`](key-decisions.md) | [`01-architecture/c4-context.md`](c4-context.md) | [`01-architecture/sequence-a-rag-readonly.md`](sequence-a-rag-readonly.md) | [`01-architecture/sequence-b-agent-hitl.md`](sequence-b-agent-hitl.md)
- Governance: [`02-governance/model-routing-policy.md`](../02-governance/model-routing-policy.md) | [`02-governance/tool-registry-policy.md`](../02-governance/tool-registry-policy.md)
- Evaluation: [`03-evaluations/eval-plan.md`](../03-evaluations/eval-plan.md)

## Assumptions
- Only read-only tools are available in this flow; no mutating actions are permitted.
- Retrieval is required for enterprise knowledge answers; responses must be evidence-grounded.
- Request budgets are enforced (retrieval `topK`, context/token limits, and latency limits).

## End-to-End Sequence
```mermaid
sequenceDiagram
    autonumber
    %% Actors and core services
    actor User
    participant UI as Channel UI (Chat)
    participant Orch as AI Orchestrator/Agent
    participant Router as Router (Model Tier Selection)
    participant RAG as Retrieval Service (RAG)
    participant Gate as Tool Registry Enforcement
    participant Tools as Read-only Tools (KB_Search, Provider_Search)
    participant Safe as Safety/Validation
    participant Obs as Observability (Logs/Metrics/Traces)

    %% Request intake and routing
    User->>UI: Ask enterprise question
    UI->>Orch: Submit request + user context
    Orch->>Obs: Start trace + correlation_id

    Orch->>Router: Route request (intent, SLA, risk)
    Router-->>Orch: Selected model tier
    Orch->>Obs: Log routing tier decision

    Orch->>RAG: Retrieve evidence candidates
    RAG->>RAG: Apply evidence budget (topK, token limit)
    RAG-->>Orch: Ranked evidence set + confidence
    Orch->>Obs: Log retrieval budget + confidence

    %% Optional read-only tool path with policy enforcement
    alt Tool lookup needed
        Orch->>Gate: Request tool call (KB_Search or Provider_Search)
        Gate->>Gate: Allowlist check (read-only tool?)
        alt Tool allowed
            Gate->>Gate: Validate tool arg schema
            alt Schema valid
                Gate->>Tools: Execute read-only query
                alt Tool success
                    Tools-->>Gate: Tool result
                    Gate-->>Orch: Normalized tool output
                else Tool timeout/error
                    Gate-->>Orch: Tool failure
                    Orch->>Obs: Record tool timeout/error
                    Orch->>Orch: Fallback to retrieval-only answer path
                end
            else Schema invalid
                Gate-->>Orch: Reject call (validation error)
                Orch->>Obs: Record schema validation failure
            end
        else Tool denied
            Gate-->>Orch: Deny (not allowlisted)
            Orch->>Obs: Record policy deny
        end
    end

    alt Model throttled or tier unavailable
        Orch->>Router: Request fallback tier
        Router-->>Orch: Fallback model tier
        Orch->>Obs: Record throttle + fallback event
    end

    %% Response safety validation and release
    Orch->>Safe: Compose answer with citations + validate/redact
    alt Safety pass
        Safe-->>UI: Grounded response + citations
        UI-->>User: Display response
        Orch->>Obs: Emit success logs/metrics/traces
    else Safety block
        Safe-->>UI: Safe fallback response
        UI-->>User: Display blocked/safe response
        Orch->>Obs: Emit safety block event
    end
```

> 🧪 **How we validate**
> This flow is verified through golden-set retrieval/groundedness tests, tool contract checks, and fallback-path reliability scenarios.

## Decision Points Called Out
- Routing tier decision: request intent/SLA/risk selects the primary model tier.
- Retrieval evidence budget: retrieval applies `topK` and token/context limits before generation.
- Tool allowlist check: tool registry enforces deny-by-default and read-only scope.
- Schema validation for tool arguments: invalid arguments are rejected before tool execution.
- Fallback behavior: model throttle/tier outage triggers routing fallback; tool failures trigger retrieval-only answer path.

## Failure Modes and Handling
- Model throttle/outage:
  - Use fallback ladder to a lower-cost or higher-availability tier.
  - Preserve trace continuity and emit throttle/fallback telemetry.
- Retrieval empty/low confidence:
  - Return a constrained answer (or abstain), include confidence language, and request clarification.
  - Avoid unsupported claims when evidence budget does not yield sufficient grounding.
- Tool timeout:
  - Treat tool call as optional enrichment; continue via retrieval-only path when possible.
  - Record timeout metrics for SLO tuning and tool reliability remediation.
- Safety block:
  - Replace blocked output with a safe response pattern.
  - Emit safety event with correlation metadata for review and policy tuning.
