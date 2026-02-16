# Enterprise AI Reference Architecture (RAG + Agents)

> **Note:** This is a **vendor-neutral reference architecture + templates** repository for learning, interviews, and enterprise adoption guidance.  
> It contains **no proprietary employer/client data**; all examples are **generic**. Implementation is **minimal by design** to keep focus on architecture artifacts.

## Overview
This repository presents a minimal enterprise AI reference architecture designed for learning, interviews, and adoption planning. It is intentionally artifact-first: architecture decisions, governance policies, evaluation plans, and reference flow documentation.

## Reference Flows
### Flow A — Enterprise RAG + Read-Only Tools
- Grounded knowledge responses using retrieval and approved enterprise sources.
- Read-only tool usage only, with routing, safety checks, and observability.

### Flow B — Bounded Agent + HITL + Write Tools
- Controlled action workflow where the agent proposes actions.
- Write execution is gated by policy enforcement, HITL approvals, and idempotency protections.

## How To Use This Repo
1. Start with `00-overview/reading-guide.md` for 5-minute and 15-minute paths.
2. Review architecture intent in `01-architecture/key-decisions.md` and `01-architecture/c4-context.md`.
3. Walk through execution behavior in `01-architecture/sequence-a-rag-readonly.md` and `01-architecture/sequence-b-agent-hitl.md`.
4. Validate controls in `02-governance/` (routing, tool registry, observability, incident response).
5. Confirm proof strategy in `03-evaluations/eval-plan.md` and related evaluation suites.

## Status
- **Step 1 (Entry + Interview Kit):** Complete (`README.md`, `08-interview-kit/README.md`, overview and reading paths).
- **Step 2 (2 C4 Diagrams):** Complete (`docs/diagrams/c4-context.mmd`, `docs/diagrams/c4-container.mmd`).
- **Step 3 (1 Case Study):** Complete (`docs/case-studies/case-study-01-incident-triage-hitl.md`).

## Proof (artifacts)
- [ ] C4 Context diagram (Flow A + Flow B)
- [ ] C4 Container diagram (Flow A + Flow B)
- [ ] Tool Contract Standard (v1)
- [ ] Evaluation plan (v1: golden set + regression gate)
- [ ] Observability spec (v1: traces + audit events)
- [ ] Sample trace (illustrative prompt -> tool call -> audit event -> redaction)

Maintained by: Jitendra Koppu
