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

## STAR Placeholders
### STAR Example 1 — RAG Quality and Risk Reduction
- **Situation:** [Insert context]
- **Task:** [Insert objective]
- **Action:** [Insert architecture decisions and controls]
- **Result:** [Insert measurable outcome]

### STAR Example 2 — Agent Workflow with HITL Controls
- **Situation:** [Insert context]
- **Task:** [Insert objective]
- **Action:** [Insert governance, approval, and reliability controls]
- **Result:** [Insert measurable outcome]
