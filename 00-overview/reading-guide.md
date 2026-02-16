# Reading Guide

> **Status:** Architecture-focused | Vendor-neutral | Flow A + Flow B  
> **Flows:** Flow A (RAG + Read-Only Tools) | Flow B (Bounded Agent + HITL + Write Tools)  
> **Start Here:** [5-Minute Path](#5-minute-path-max-5-links) | [15-Minute Path](#15-minute-path-max-8-links) | [Deep Dive](#deep-dive-path)

## TL;DR
- Use the 5-minute path for interview intros and architecture story framing.
- Use the 15-minute path for key decisions, sequences, and enforcement controls.
- Use the deep dive to inspect governance, evaluation, and tool contracts end-to-end.

## Navigation
- Overview: [`00-overview/readme.md`](readme.md) | [`00-overview/reading-guide.md`](reading-guide.md)
- Architecture: [`01-architecture/key-decisions.md`](../01-architecture/key-decisions.md) | [`01-architecture/c4-context.md`](../01-architecture/c4-context.md) | [`01-architecture/sequence-a-rag-readonly.md`](../01-architecture/sequence-a-rag-readonly.md) | [`01-architecture/sequence-b-agent-hitl.md`](../01-architecture/sequence-b-agent-hitl.md)
- Governance: [`02-governance/model-routing-policy.md`](../02-governance/model-routing-policy.md) | [`02-governance/tool-registry-policy.md`](../02-governance/tool-registry-policy.md) | [`02-governance/tool-registry-examples.md`](../02-governance/tool-registry-examples.md)
- Evaluation: [`03-evaluations/eval-plan.md`](../03-evaluations/eval-plan.md)

A fast review path for the AI Reference Implementation (Flow A + Flow B).

> 🔍 **What to look for**
> Start at decisions and sequences first, then validate governance and evaluation gates.

## 5-Minute Path (max 5 links)
- [Overview README](readme.md)
- [Key Decisions](../01-architecture/key-decisions.md)
- [C4 Context](../01-architecture/c4-context.md)
- [Flow A Sequence](../01-architecture/sequence-a-rag-readonly.md)
- [Flow B Sequence](../01-architecture/sequence-b-agent-hitl.md)

## 15-Minute Path (max 8 links)
- [Overview README](readme.md)
- [Key Decisions](../01-architecture/key-decisions.md)
- [C4 Context](../01-architecture/c4-context.md)
- [Flow A Sequence](../01-architecture/sequence-a-rag-readonly.md)
- [Flow B Sequence](../01-architecture/sequence-b-agent-hitl.md)
- [Tool Registry Policy](../02-governance/tool-registry-policy.md)
- [Tool Registry Examples](../02-governance/tool-registry-examples.md)
- [Flow B Approval Policy](../04-reference-flows/flow-b-agent-hitl/approval-policy.md)

## Deep Dive Path
### Architecture
- [Overview README](readme.md)
- [Key Decisions](../01-architecture/key-decisions.md)
- [C4 Context](../01-architecture/c4-context.md)
- [Flow A Sequence](../01-architecture/sequence-a-rag-readonly.md)
- [Flow B Sequence](../01-architecture/sequence-b-agent-hitl.md)

### Governance
- [Model Routing Policy](../02-governance/model-routing-policy.md)
- [Tool Registry Policy](../02-governance/tool-registry-policy.md)
- [Tool Registry Examples](../02-governance/tool-registry-examples.md)
- [Observability Policy](../02-governance/observability-policy.md)
- [Incident Response Policy](../02-governance/incident-response-policy.md)

### Evaluation
- [Evaluation Plan](../03-evaluations/eval-plan.md)
- [Evaluation Datasets](../03-evaluations/eval-datasets.md)
- [Injection Tests](../03-evaluations/injection-tests.md)
- [Tool Contract Tests](../03-evaluations/tool-contract-tests.md)

### Flows
- [Flow A Scope](../04-reference-flows/flow-a-rag-readonly/scope.md)
- [Flow A Success Criteria](../04-reference-flows/flow-a-rag-readonly/success-criteria.md)
- [KB_Search Contract](../04-reference-flows/flow-a-rag-readonly/tool-contracts/kb_search.md)
- [Provider_Search Contract](../04-reference-flows/flow-a-rag-readonly/tool-contracts/provider_search.md)
- [Flow B Scope](../04-reference-flows/flow-b-agent-hitl/scope.md)
- [Flow B Approval Policy](../04-reference-flows/flow-b-agent-hitl/approval-policy.md)
- [Flow B Success Criteria](../04-reference-flows/flow-b-agent-hitl/success-criteria.md)
- [Claim_Update Contract](../04-reference-flows/flow-b-agent-hitl/tool-contracts/claim_update.md)
