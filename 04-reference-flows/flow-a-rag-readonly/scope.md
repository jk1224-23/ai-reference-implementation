# Flow A Scope: Enterprise RAG + Read-Only Tools

## Problem Statement and Target Users
Flow A addresses enterprise question-answering where responses must be grounded in approved sources and enriched by safe read-only lookups.

Target users:
- Internal support teams
- Customer support operations
- Knowledge workers needing policy/process answers

## In-Scope Capabilities
- Retrieval-augmented generation (RAG) is required for knowledge answers.
- Read-only tools only.
- Example read-only tools:
  - `KB_Search` for policy/knowledge retrieval
  - `Provider_Search` for lookup-style reference data
- Routing and fallback behavior:
  - Tiered model routing based on intent/risk/SLA.
  - Fallback ladder for model throttles and tool timeouts.
  - Safe constrained response when evidence or availability is insufficient.

## Out of Scope
- Any write, create, update, or delete actions in downstream systems.
- Autonomous task execution that changes business state.
- Approval workflows for state changes (covered by Flow B).
- Long-term memory/persistence strategies beyond scoped conversational context.

## Data Boundaries and Logging Constraints
- Treat all user and retrieved content as potentially sensitive.
- Follow data minimization and least-privilege retrieval access.
- No PHI/PII in logs by default.
- Log opaque document/chunk IDs rather than raw source content.

## Success Criteria (Aligned to Eval Plan)
- Groundedness/citation rate meets target thresholds in the golden set.
- Retrieval quality remains within accepted relevance/confidence bounds.
- Unauthorized or out-of-scope tool invocations are consistently denied.
- Injection test scenarios preserve policy and prevent unsafe behavior.
- Latency and error rates meet defined SLO thresholds.
- Fallback behavior is reliable under model/tool degradation.

## Failure Modes Summary and Handling
- Model throttle or outage:
  - Apply routing fallback and controlled degradation.
- Retrieval empty or low confidence:
  - Return constrained answer or abstain with clarification request.
- Tool timeout or deny:
  - Continue with retrieval-only path when possible; log event for reliability tuning.
- Safety block triggered:
  - Return safe response template and emit safety signal for review.

## Related Architecture Documents
- Context: [C4 Context](../../01-architecture/c4-context.md)
- Sequence: [Flow A Sequence](../../01-architecture/sequence-a-rag-readonly.md)
- Decisions: [Key Decisions](../../01-architecture/key-decisions.md)
- Evaluation baseline: [Evaluation Plan](../../03-evaluations/eval-plan.md)

## Definition of Done
- Problem statement and target users are documented.
- RAG-required behavior is explicitly defined.
- Read-only tool boundary is explicit with examples.
- Routing and fallback expectations are documented.
- Out-of-scope list explicitly excludes write actions.
- Data/logging constraints include no PHI/PII-by-default logging.
- Success criteria map to the evaluation plan.
- Failure modes and high-level handling are documented.
- Architecture links are present and valid.
