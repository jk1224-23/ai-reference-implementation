# Enterprise AI Reference Architecture (RAG + Agents)

> **Note:** This is a **vendor-neutral reference architecture + templates** repository for learning, interviews, and enterprise adoption guidance.  
> It contains **no proprietary employer/client data**; all examples are **generic**. Implementation is **minimal by design** to keep focus on architecture artifacts.

## Start Here
- **What this repo is:** implementation-facing reference flows for policy-first RAG and bounded agent execution.
- **Read first:** [00-overview/reading-guide.md](./00-overview/reading-guide.md), [00-overview/readme.md](./00-overview/readme.md), [01-architecture/key-decisions.md](./01-architecture/key-decisions.md), [03-evaluations/eval-plan.md](./03-evaluations/eval-plan.md).
- **Run the control-plane demo:** [reference-implementation/README.md](./reference-implementation/README.md).

## Why this exists
This repository provides a concise, interview-first reference implementation for enterprise AI adoption. It is artifact-first and minimal by design, demonstrating how architecture controls like tool contracts, policy enforcement, and HITL approvals are applied in practice.

## Repo Boundaries
- This repo is self-contained: reference flows, runnable sample code, governance templates, evaluation artifacts, and C4 diagrams.
- It is not a production-ready framework; it demonstrates how controls like Skills, tool contracts, and approvals can be enforced.
- A companion architecture repo (`ai-reference-architecture`) covers vendor-neutral principles, patterns, and ADRs — see its own README for details.

## What you get
- Flow A pattern for grounded RAG with read-only tools.
- Flow B pattern for bounded agent actions with HITL approvals.
- Governance artifacts for routing, tool policy, observability, and incident response.
- Evaluation artifacts for quality, safety, and regression checks.
- C4 diagrams and a case study for architecture walkthroughs.

## Control Plane Snapshot
```mermaid
flowchart TD
  U[User] --> UI[UI / Channel Adapter]
  UI --> IC[Config-driven Intent Mapping (demo)]
  IC --> PE[Policy Engine]
  PE -->|DENY| DENY[Deny-by-default]
  PE -->|ALLOW| TE[Tool Executor]
  PE -->|ALLOW_HITL| HITL[HITL approval required]
  TE --> SOE[Systems of record via allowlisted tools]
  TE --> RA[Response Assembler]
  HITL --> RA
  DENY --> RA
  RA --> AUDIT[Audit Logger]
```

## On this page
- [Start Here](#start-here)
- [Why this exists](#why-this-exists)
- [What you get](#what-you-get)
- [Control Plane Snapshot](#control-plane-snapshot)
- [Doc Conventions](#doc-conventions)
- [How it works](#how-it-works)
- [Metrics (what we measure)](#metrics-what-we-measure)
- [Proof (artifacts)](#proof-artifacts)
- [Architecture](#architecture)
- [Status](#status)

## Doc Conventions
- Use vendor-neutral language and generic examples only.
- Keep this repo focused on reference flows and enforcement patterns, not full runtime builds.
- Use relative links for internal references.
- Keep PHI/PII out of examples, traces, and logs.

## How it works
### Flow A — RAG (grounded Q&A)
- Routes requests to retrieval-first processing.
- Uses approved knowledge sources and read-only tools for grounding.
- Applies safety checks and returns citation-backed responses.

### Flow B — Agent + HITL (approvals + audit)
- Agent proposes structured actions with policy checks.
- Risky/write actions require explicit human approval.
- Execution and outcomes are audited with traceable metadata.

## Metrics (what we measure)
| Category | Example metric | Signal |
|---|---|---|
| Safety | HITL compliance rate for gated write actions | Must remain 100% for gated actions |
| Correctness | Incident triage classification accuracy | Tracked against evaluation set |
| Operational | Time-to-triage improvement | Better than manual baseline |
| Reliability | Tool-call failure rate and latency (P95) | Within defined SLO/error budget |

## Proof (artifacts)
- [x] C4 Context diagram (Flow A + Flow B) — `docs/diagrams/c4-context.mmd`
- [x] C4 Container diagram (Flow A + Flow B) — `docs/diagrams/c4-container.mmd`
- [x] Tool Contract Standard (v1) — defined in companion architecture repo (`ai-reference-architecture`)
- [x] Evaluation plan (v1: golden set + regression gate) — `03-evaluations/eval-plan.md`
- [x] Observability spec (v1: traces + audit events) — `02-governance/observability-policy.md`
- [ ] Sample trace (illustrative prompt -> tool call -> audit event -> redaction)

## Architecture
- `docs/diagrams`
- `docs/case-studies`

## Status
- **Step 1 (Entry + Interview Kit):** Complete (`README.md`, `08-interview-kit/README.md`, overview and reading paths).
- **Step 2 (2 C4 Diagrams):** Complete (`docs/diagrams/c4-context.mmd`, `docs/diagrams/c4-container.mmd`).
- **Step 3 (1 Case Study):** Complete (`docs/case-studies/case-study-01-incident-triage-hitl.md`).

---

## Platform

This repo is part of a larger AI architecture platform:

| Repo | What It Does |
|------|-------------|
| [agentlens](https://github.com/jk/agentlens) | Animated visual guide — understand the patterns before reading the code |
| [ai-reference-architecture](https://github.com/jk/ai-reference-architecture) | Architecture decisions — the why behind every config choice in this repo |
| [js-reference-architecture](https://github.com/jk/js-reference-architecture) | Production JS/TS backend — how to expose tools for AI agents |

**Why the config looks the way it does:** Every decision in `skill_registry.yaml` and `tool_allowlist.yaml` maps back to an architecture decision in [ai-reference-architecture](https://github.com/jk/ai-reference-architecture).
