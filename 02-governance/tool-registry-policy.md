# Tool Registry and Enforcement Policy

## Purpose and Scope
This policy defines how tools are registered, authorized, and executed for both Flow A and Flow B. Enforcement is performed **outside the LLM** through a control layer, and execution is **deny-by-default**.

## Definitions
- **Tool**: An external capability callable by the assistant (query or action).
- **Tool contract**: Versioned interface definition (inputs, outputs, error modes, limits).
- **Tool registry**: Authoritative catalog of active tools, metadata, risk tags, and lifecycle state.
- **Enforcement layer**: Policy gate that validates/authorizes every tool call before execution.
- **Allowlist**: Explicit set of tools permitted for a given environment/app/agent.
- **Read-only tool**: Tool that does not change system state.
- **Write tool**: Tool that creates/updates/deletes state in downstream systems.

## Policy Principles
- Deny-by-default.
- Least privilege scopes and identities.
- Strict schema validation.
- Request/tool budgets and runtime limits.
- Full auditability and traceability.
- Kill switches for rapid containment.

## Tool Classification Matrix
| Tool class | Risk level | PHI impact | HITL required |
|---|---|---|---|
| Read-only lookup (non-sensitive) | Low | None/Low | No (unless incident mode) |
| Read-only lookup (sensitive domain) | Medium | Possible | Conditional |
| Write tool (reversible, scoped) | Medium/High | Possible | Yes in production |
| Write tool (high-impact/irreversible) | High | Likely | Yes (mandatory) |

## Mandatory Enforcement Checks
1. Tool exists in registry and is active.
2. Tool is allowlisted for the current environment, app, and agent profile.
3. Authentication and authorization pass with required scopes.
4. Input schema is strictly valid; unknown fields are rejected.
5. Rate limits, budgets, and circuit breakers are within policy.
6. Write tools include valid idempotency keys and replay protection.
7. Tool output is validated/sanitized and redacted before model/user exposure.
8. Audit logging is emitted with `correlation_id`.

## HITL Policy
- HITL is required for production state-changing actions and any high-risk action path.
- Approver view includes redacted action preview: intent, target, key arguments, estimated impact, and rollback posture.
- Outcomes:
  - **Approve**: execution may proceed within policy window.
  - **Deny**: execution is blocked; no write occurs.
  - **Timeout**: treated as deny by default.

## Kill Switch Policy
- **Global**: disable all tool execution platform-wide.
- **Tool-level**: disable a specific tool.
- **Category-level**: disable all write tools (read-only mode).
- **Agent-level**: restrict a specific agent profile to safer capabilities.

Kill switch usage is part of incident response and must align with the incident runbook.

## Versioning and Deprecation
- Tool contracts are versioned (`v1`, `v2`, ...).
- Breaking changes require a new major version.
- `v1` to `v2` migration must support a defined dual-run/deprecation window.
- Registry metadata must include owner, sunset date, and migration guidance.
- Deprecated versions are blocked after window closure unless explicit exception is approved.

## Definition of Done
- Registry ownership and lifecycle fields are defined.
- Deny-by-default is enforced in all environments.
- Allowlist rules exist per environment/app/agent.
- AuthN/AuthZ and scope checks are documented and tested.
- Strict schema validation rejects unknown fields.
- Budgets, rate limits, and circuit breakers are configured.
- Idempotency is required for every write-capable tool.
- HITL requirements are defined by risk tier.
- Kill switches are operational and tested.
- Audit logs include correlation IDs and approval outcomes.
