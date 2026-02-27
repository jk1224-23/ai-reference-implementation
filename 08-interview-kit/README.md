# Interview Kit — AI Architect (Enterprise)

> **Note:** This is a **vendor-neutral reference architecture + templates** repository for learning, interviews, and enterprise adoption guidance.  
> It contains **no proprietary employer/client data**; all examples are **generic**. Implementation is **minimal by design** to keep focus on architecture artifacts.

## 2-Minute Interview Story
I design enterprise AI systems that move from low-risk retrieval use cases to controlled action-taking workflows. I start with a grounded RAG baseline (Flow A) so responses are evidence-backed and operationally observable. I then extend to bounded agents (Flow B) only when governance controls are in place: deny-by-default tool enforcement, HITL approvals for write actions, idempotency and replay protection, and release gates driven by evaluation. I design for architecture clarity first, implementation second, so teams can adopt safely across identity, policy, observability, and audit requirements.

## Five Keywords
- Governance
- Evaluation
- Observability
- Tool Contracts
- HITL

## What I Can Whiteboard Quickly
- Flow A end-to-end sequence: routing -> retrieval -> read-only tools -> safety -> response.
- Flow B control path: proposal -> policy gate -> HITL -> write execution -> verification.
- Tool registry model: contracts, allowlists, schema checks, budgets, kill switches.
- C4 context/container view with trust boundaries and telemetry boundaries.
- Evaluation and release gating model (golden set, injection tests, regression checks).

## Default Design Principles
- Vendor-neutral architecture with explicit control points.
- Deny-by-default for tool execution.
- Least privilege and data minimization by default.
- Human approval for state-changing actions in production.
- Traceability and auditability as first-class requirements.
- Safety and quality gates before rollout expansion.

## STAR Examples (Interview-Ready, Demo)
### STAR Example 1 — RAG Quality and Risk Reduction
- **Situation:** Early demos mixed policy explanations with occasional unsupported claim-status wording.
- **Task:** Ensure member-facing status answers are evidence-backed while preserving helpful policy explanations.
- **Action:** Split routes by intent (`CLAIM_STATUS` tool-backed, `POLICY_EXPLANATION` KB-first), enforced deny-by-default tool policy, and added golden-set checks for unsupported SoR claims.
- **Result:** In illustrative/demo regression runs, unsupported status assertions dropped from frequent to rare, and evidence-missing paths consistently degraded to safe escalation messaging.

### STAR Example 2 — Agent Workflow with HITL Controls
- **Situation:** Appeal initiation requires strict controls because it can trigger state-changing workflows.
- **Task:** Enable assisted appeal drafting without allowing autonomous write execution.
- **Action:** Routed transactional requests to `case.create.v1` behind `ALLOW_HITL`, required `approvalId`, enforced subject binding, and logged approval lifecycle + tool outcomes for audit.
- **Result:** Write attempts in demo smoke scenarios stayed fully gated; unapproved paths were blocked and escalated with traceable approval status at each step.
