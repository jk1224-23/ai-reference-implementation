# Model Routing Policy

## Purpose and Scope
This policy defines how requests are routed across model tiers for both:
- **Flow A**: Enterprise RAG + read-only tools
- **Flow B**: Bounded agent + HITL + write tools

Routing governs model selection, fallback behavior, and operating guardrails. It does **not** replace business authorization policy, tool enforcement policy, or domain workflow rules.

## Routing Tiers
| Tier | Intent | Typical use cases |
|---|---|---|
| Tier 0 Deterministic | No generative reasoning required | Policy lookups, templates, fixed transformations, safe canned responses |
| Tier 1 Fast/Cost | High-throughput, low-to-medium complexity | Flow A FAQ-style Q&A, summarization, lightweight retrieval synthesis |
| Tier 2 Reasoning | Higher complexity and synthesis depth | Multi-step evidence synthesis, nuanced enterprise questions, exception handling |
| Tier 3 High-Risk/Controlled | Sensitive/high-impact tasks under stricter controls | Flow B action planning with write intent, high-risk domains, HITL-first paths |

## Routing Signals
- User intent and task type
- Risk level (data sensitivity, action impact, reversibility)
- Reasoning complexity
- Latency SLO and channel expectations
- Tool requirement (none, read-only, write)
- Cost budget and quota state
- Context size and evidence volume

## Routing Decision Table
| Scenario | Flow | Signals | Selected tier |
|---|---|---|---|
| Standard enterprise knowledge question with citations | A | Low risk, read-only, moderate context | Tier 1 |
| Ambiguous policy question requiring deeper synthesis | A | Medium complexity, larger evidence set | Tier 2 |
| Low-latency status lookup with deterministic template | A | Deterministic output, strict latency | Tier 0 |
| Action proposal requiring write capability | B | Write tool required, higher risk | Tier 3 |
| Write action with moderate complexity and mandatory approval | B | High impact, HITL required | Tier 3 |
| Tool-free planning draft before human review | B | Medium complexity, no execution yet | Tier 2 |

## Fallback Ladder
1. Retry same tier once for transient errors/timeouts within request SLA.
2. Fail over to alternate provider/model in the same tier.
3. Degrade to adjacent lower tier if quality/risk constraints remain acceptable.
4. Enter **safe mode** when instability or incidents are detected:
   - **KB-only** (Flow A retrieval-only path)
   - **HITL-first** (Flow B requires approval before any action progression)
5. Return constrained response/abstain when safe execution cannot be guaranteed.

## Guardrails
- Token budgets per stage (prompt, retrieval evidence, response).
- Tool-call budgets per request and per turn.
- Loop detection for repeated planner/tool cycles.
- Stop conditions: budget exhaustion, repeated validation failure, approval timeout, risk escalation.

## Context Strategy
- Truncation order:
  1. Drop duplicate/low-relevance evidence
  2. Trim oldest conversational turns
  3. Keep latest user intent + governing instructions + high-signal evidence
- Summarization approach:
  - Summarize prior context into task-relevant state.
  - Do not include raw PHI in summaries by default.
  - Preserve citation anchors and decision-critical constraints.

## Logging Requirements
Capture at minimum:
- `correlation_id` and request/turn identifiers
- Routing decision (selected tier + key signals)
- Fallback reason and step taken
- Budgets allocated/consumed (token/tool/time)
- Outcome status (success, constrained, failed)

Do not log sensitive raw content beyond approved minimization/redaction policy.

## Definition of Done
- Routing tiers are documented and approved.
- Tier selection criteria are explicit and testable.
- Decision table covers both Flow A and Flow B.
- Fallback ladder is defined with safe-mode behavior.
- Token and tool budgets are set for each flow.
- Loop detection and stop conditions are defined.
- Context truncation/summarization policy is documented.
- Logging schema includes routing and fallback metadata.
- Sensitive-content logging restrictions are enforced.
- Operations can force safe mode during incidents.
