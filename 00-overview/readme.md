# AI Reference Implementation Overview

## Purpose
This repository shows how enterprise AI architecture decisions are implemented in practice, with vendor-neutral patterns and concrete flow design.

It complements the separate `ai-reference-architecture` repository:
- `ai-reference-architecture`: standards, policy, control objectives, and reference decision framework.
- `ai-reference-implementation`: executable architecture patterns, flow boundaries, interfaces, and operational playbooks.

## Two Reference Flows

### Flow A: Enterprise RAG + Read-Only Tools
A controlled retrieval architecture for grounded answers using enterprise content and read-only enterprise tools.

Core characteristics:
- Query intake, policy-aware routing, and retrieval orchestration.
- Source grounding, citation/traceability, and response safety checks.
- Read-only tool access for lookup-style enterprise systems.
- No mutating actions; lowest operational risk profile.

### Flow B: Bounded Agent + HITL + Write Tools
An extension of Flow A that adds bounded autonomy for action-taking workflows.

Core characteristics:
- Inherits Flow A retrieval, safety, and observability foundations.
- Adds constrained planning, allowlisted write tools, and explicit action boundaries.
- Human-in-the-loop (HITL) approval gates before high-impact or irreversible actions.
- Stronger runbooks, rollback paths, and escalation controls.

## What To Open First
- [`00-overview/reading-guide.md`](reading-guide.md) for the 5/15-minute review paths.
- [`01-architecture/key-decisions.md`](../01-architecture/key-decisions.md) for tradeoffs and decision logic.
- [`01-architecture/c4-context.md`](../01-architecture/c4-context.md) for system boundary and trust zones.
- [`01-architecture/sequence-a-rag-readonly.md`](../01-architecture/sequence-a-rag-readonly.md) for Flow A end-to-end execution.
- [`01-architecture/sequence-b-agent-hitl.md`](../01-architecture/sequence-b-agent-hitl.md) for Flow B end-to-end execution + HITL.
- [`02-governance/model-routing-policy.md`](../02-governance/model-routing-policy.md) and [`02-governance/tool-registry-policy.md`](../02-governance/tool-registry-policy.md) for enforcement controls.
- [`03-evaluations/eval-plan.md`](../03-evaluations/eval-plan.md) for how quality/safety is proven.

## 30-Second Talk Track
This repo is the implementation companion to our architecture standards repo. It demonstrates two enterprise AI patterns: a low-risk RAG system with read-only tools (Flow A), and a bounded agent that can perform write actions with human approval (Flow B). The design focuses on routing, tool governance, observability, runbooks, and safety posture so teams can move from policy to deployable architecture.

## 2-Minute Talk Track
The objective of this repository is to make enterprise AI architecture decisions operational. Our separate architecture repo defines standards and policies; this repo shows how those standards become system boundaries, flow controls, and operating procedures.

Flow A is the baseline: enterprise RAG with read-only tools. It prioritizes grounded responses, controlled retrieval, and low-risk integrations. This is where most organizations start because it balances business value and governance.

Flow B extends Flow A with bounded agency. The agent can plan and execute write actions, but only through allowlisted tools, explicit scopes, and human approval checkpoints for sensitive operations. This flow demonstrates how to introduce autonomy incrementally without losing control.

Across both flows, the emphasis is on architecture concerns that matter in production: request routing, tool registry and access policy, end-to-end observability, operational runbooks, prompt-injection posture, and evaluation quality gates. The result is a vendor-neutral blueprint for scaling enterprise AI safely from retrieval use cases to action-taking workflows.

## Scope

### In Scope
- Enterprise architecture patterns for RAG and bounded agents.
- Control points for policy enforcement, approvals, and tool governance.
- Operational guidance for telemetry, incidents, and quality evaluation.

### Out of Scope
- Provider-specific implementation details or SDK lock-in.
- Full product UI/UX design and feature-level backlog management.
- Domain-specific business process customization.

## Concerns Mapping

| Concern | Where documented |
|---|---|
| Routing | Flow A and Flow B architecture flow documents (intake, policy, dispatch) |
| Tool registry | Tool governance section in flow docs (allowlist, permissions, lifecycle) |
| Observability | Cross-cutting operations docs (traces, metrics, logs, alerts) |
| Runbook | Incident and operations runbook (failure modes, rollback, escalation) |
| Injection posture | Security/safety guidance (prompt injection, data exfiltration controls) |
| Evaluation | Evaluation framework docs (quality, safety, regression criteria) |
