# Flow B Skills Enforcement Stubs

## Purpose
This folder provides minimal, documentation-first enforcement examples for Agent Skills defined in the companion architecture repo.

This is not a production runtime. It demonstrates how skills can be enforced through policy and control points in a vendor-neutral way.

## Skill Mapping
| Skill Name | Supporting files in this folder |
|---|---|
| `skill_claim_update` | `skill_contract_claim_update.md`, `skill_enforcement_pseudocode.md` |

### Example Skills in this folder

- `claim_update`  
  - Contract: `skill_contract_claim_update.md`  
  - Enforcement pattern: `skill_enforcement_pseudocode.md`

- `knowledge_retrieval` (read-only baseline)  
  - Contract (mini): see below  
  - Enforcement: same allowlist + tool-permission checks (no approval gate)

#### Mini Skill Contract: knowledge_retrieval (read-only baseline)

- skill_name: knowledge_retrieval
- version: v1
- intent_signals:
  - "What is..."
  - "Explain..."
  - "Find policy..."
  - "Show documentation for..."
- allowed_tools:
  - retrieval_kb (allowlisted internal knowledge base / RAG index)
  - policy_kb (governance/policy documents)
- data_scope:
  - Read-only. No PHI writes. No account actions. No transactional updates.
- approval_required: false
- observability_events:
  - skill_invoked
  - retrieval_started
  - retrieval_completed
  - citations_attached
  - skill_failed
- timeouts/retries:
  - Short timeouts; retry retrieval once on transient failure.
- error_handling:
  - If retrieval fails or confidence is low, ask a clarifying question or route to a human/help channel per product policy.
- routing_rule:
  - If the user request implies changing state (update/submit/cancel/pay), do NOT use this skill; route to a transactional skill instead.

## Enforcement Approach (High Level)
- Resolve skill from an approved allowlist before any tool action.
- Verify the requested tool type is permitted by the skill contract.
- Apply policy checks for role, scope, and data boundary.
- Trigger HITL approval gates when required by risk policy.
- Emit audit/observability events across intent, approval, execution, and outcome.
- Execute tools through contracted adapters, not free-form model calls.
- Use safe fallback behavior when checks, approvals, or tool execution fail.
