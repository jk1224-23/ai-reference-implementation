# Key Architecture Decisions

This page summarizes the major architecture tradeoffs for two flows in this repo:
- **Flow A**: Enterprise RAG + read-only tools
- **Flow B**: Bounded agent + HITL + write tools

## DR-01: RAG vs Fine-Tuning for Enterprise Knowledge
**Context**: Enterprise knowledge changes frequently, includes confidential content, and requires source traceability.

**Decision**: Use RAG as the default knowledge access pattern; reserve fine-tuning for specialized behaviors, not core enterprise facts.

**Alternatives Considered**:
- Fine-tune a base model on enterprise documents.
- Hybrid (light fine-tune + RAG).

**Tradeoffs**:
- RAG improves freshness and citations but adds retrieval complexity.
- Fine-tuning can improve style/domain fluency but is slower to update and weaker on provenance.

**What would change the decision**: Stable corpus, limited update cadence, and strong evidence that retrieval latency/quality is the bottleneck.

## DR-02: Chunking, Retrieval Strategy, and Evidence Budgeting
**Context**: Retrieval quality depends on chunk granularity, ranking quality, and bounded context windows.

**Decision**: Use structure-aware chunking with overlap, hybrid retrieval (semantic + lexical), and explicit evidence budgets (`topK`, token ceilings per answer).

**Alternatives Considered**:
- Single-strategy semantic retrieval only.
- Large chunks with minimal overlap.
- Unbounded retrieval injection.

**Tradeoffs**:
- Hybrid retrieval improves recall but increases pipeline complexity.
- Tight evidence budgets reduce hallucination risk and cost, but may miss edge evidence.

**What would change the decision**: If long-context models become cheap/fast enough, evidence budgets can be relaxed while maintaining groundedness checks.

## DR-03: Model Routing Tiers and Fallback Ladder
**Context**: Workloads vary by difficulty, latency sensitivity, and failure tolerance.

**Decision**: Route requests by policy into model tiers (economy, balanced, premium) with a fallback ladder for outage/timeout/degradation.

**Alternatives Considered**:
- Single model for all requests.
- Manual routing by application teams.

**Tradeoffs**:
- Tiering improves cost/latency control and resilience, but requires routing governance and monitoring.
- Fallbacks improve availability, but response quality can vary by tier.

**What would change the decision**: Extremely stable demand profile with uniform quality needs, or hard compliance constraints that force a single approved model.

## DR-04: Tool Registry Enforcement Outside the Model
**Context**: Model-generated tool calls are non-deterministic and must not define their own authority boundaries.

**Decision**: Enforce tool registration, authz, schema validation, and policy checks in a control layer outside the model; deny by default.

**Alternatives Considered**:
- Prompt-only tool constraints.
- Allow-by-default with logging.

**Tradeoffs**:
- External enforcement increases safety and auditability, with added integration overhead.
- Deny-by-default reduces accidental risk but increases onboarding friction.

**What would change the decision**: Never for enterprise production; this is a foundational control requirement.

## DR-05: Separation of Read-Only vs Write Tools + HITL for Writes
**Context**: Flow A prioritizes low-risk retrieval; Flow B introduces action-taking risk.

**Decision**: Maintain strict read/write tool classes. Require HITL approval for write actions based on risk tier, impact scope, and reversibility.

**Alternatives Considered**:
- Unified tool pool with soft prompts.
- Fully autonomous writes for low-risk actions.

**Tradeoffs**:
- Separation and HITL reduce blast radius and improve trust, but add latency and operational steps.
- Automation speed is lower for action workflows.

**What would change the decision**: High-confidence, low-impact, reversible actions with proven controls may move from mandatory HITL to conditional HITL.

## DR-06: Idempotency and Replay Protection for Write Tools
**Context**: Retries, network faults, and agent loops can cause duplicate writes.

**Decision**: Require idempotency keys, operation fingerprints, and replay windows for all write tools; reject duplicate execution within policy window.

**Alternatives Considered**:
- Best-effort retries without dedupe.
- Tool-specific ad hoc dedupe logic.

**Tradeoffs**:
- Strong replay controls reduce financial/operational risk but require coordinated contract design across tools.
- Operational debugging can be more complex when duplicate attempts are intentionally blocked.

**What would change the decision**: Never for non-trivial writes; at most, lighter controls for explicitly ephemeral, reversible actions.

## DR-07: Observability Baseline (Correlation, Logs, Metrics, Traces)
**Context**: Multi-step AI flows require end-to-end diagnosability across routing, retrieval, model, and tools.

**Decision**: Propagate `correlation_id` through every stage and enforce minimum telemetry: structured logs, latency/error metrics, and distributed traces.

**Alternatives Considered**:
- Log-only observability.
- Stage-local IDs without cross-service propagation.

**Tradeoffs**:
- Full telemetry improves incident response and tuning, with extra storage and instrumentation cost.
- Strict schema discipline is required across teams.

**What would change the decision**: Only scope of telemetry detail may change; correlation and baseline telemetry remain mandatory.

## DR-08: Prompt Injection Posture and Blast Radius Control
**Context**: Retrieved or user-supplied content may contain malicious instructions targeting model/tool behavior.

**Decision**: Treat external text as untrusted data, not executable instruction. Apply instruction hierarchy, tool-call policy checks, and context isolation to limit blast radius.

**Alternatives Considered**:
- Rely on system prompt robustness alone.
- Minimal filtering with after-the-fact monitoring.

**Tradeoffs**:
- Layered defenses reduce compromise probability but can suppress some legitimate advanced behaviors.
- Security controls require ongoing red-team validation.

**What would change the decision**: Stronger controls may be added for high-risk domains; baseline untrusted-data posture does not relax.

## DR-09: Data Retention and Memory Stance
**Context**: Enterprise and regulated environments require controlled retention and minimization, especially for sensitive data categories.

**Decision**: Prefer short-lived, purpose-bound memory using summaries over raw transcript retention; enforce stricter handling for PHI/PII and regulated fields.

**Alternatives Considered**:
- Full transcript retention for all sessions.
- Long-term memory by default.

**Tradeoffs**:
- Summary-first memory reduces privacy and compliance risk, but may lose nuanced context.
- Additional logic is needed to regenerate context safely when required.

**What would change the decision**: Explicit legal/business requirements for long-term auditability with approved controls and data governance sign-off.

## DR-10: Evaluation Strategy and Release Gates
**Context**: AI behavior can regress silently with prompt/model/retrieval/tool changes.

**Decision**: Use a layered evaluation suite: golden task set, regression thresholds, safety checks, and prompt-injection/adversarial tests as release gates.

**Alternatives Considered**:
- Manual spot checks only.
- Offline benchmark-only evaluation.

**Tradeoffs**:
- Gated evaluation improves reliability and safety but slows deployment velocity.
- Maintaining representative test sets requires continuous investment.

**What would change the decision**: If risk profile decreases for a non-critical workload, gate strictness can be reduced; core regression and safety checks remain.
