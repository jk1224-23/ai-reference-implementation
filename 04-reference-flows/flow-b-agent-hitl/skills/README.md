# Flow B Skills Enforcement Stubs

## Purpose
This folder provides minimal, documentation-first enforcement examples for Agent Skills defined in the companion architecture repo.

This is not a production runtime. It demonstrates how skills can be enforced through policy and control points in a vendor-neutral way.

## Skill Mapping
| Skill Name | Supporting files in this folder |
|---|---|
| `skill_claim_update` | `skill_contract_claim_update.md`, `skill_enforcement_pseudocode.md` |

## Enforcement Approach (High Level)
- Resolve skill from an approved allowlist before any tool action.
- Verify the requested tool type is permitted by the skill contract.
- Apply policy checks for role, scope, and data boundary.
- Trigger HITL approval gates when required by risk policy.
- Emit audit/observability events across intent, approval, execution, and outcome.
- Execute tools through contracted adapters, not free-form model calls.
- Use safe fallback behavior when checks, approvals, or tool execution fail.
