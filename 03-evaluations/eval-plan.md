# Evaluation Plan

## Purpose
This plan defines how the AI Reference Implementation proves quality, safety, and control integrity for:
- **Flow A**: Enterprise RAG + read-only tools
- **Flow B**: Bounded agent + HITL + write tools

Evaluations protect against hallucinations, prompt/tool injection, tool misuse, and silent regressions from model/prompt/policy/tool changes.

## Evaluation Layers
- **Retrieval quality (RAG)**: relevance, ranking quality, and evidence sufficiency.
- **Response quality**: groundedness, correctness, and completeness for user tasks.
- **Safety/compliance**: PHI/PII leakage prevention and injection resistance.
- **Tool correctness**: schema enforcement, allow/deny policy behavior, and budget adherence.
- **Workflow correctness**: HITL gating enforcement and idempotency behavior for write actions.

## Test Suite Types
- **Golden set (Flow A)**:
  - Curated enterprise Q&A set with expected evidence/source references.
  - Includes normal and edge-case knowledge requests.
- **Injection test set**:
  - User-input injection attempts.
  - Retrieved-document injection attempts.
  - Tool-output injection attempts.
- **Tool contract tests**:
  - Invalid arguments are rejected.
  - Unknown fields are rejected.
  - Policy-denied tools cannot execute.
- **Routing tests**:
  - Tier selection aligns with intent/risk/SLA.
  - Fallback ladder behavior under throttle/outage is correct.
- **HITL tests (Flow B)**:
  - Approval required for write paths.
  - Timeout path blocks execution.
  - Deny path blocks execution and returns controlled response.

## Scoring and Acceptance Criteria
- **Groundedness/citation present rate** (where applicable):
  - Flow A: >= 95% for golden-set answers requiring evidence.
  - Flow B planning/confirmation steps: citations present when retrieval is used.
- **Schema validation failure behavior**:
  - 100% of invalid/unknown input field test cases must be rejected.
  - False-reject rate for valid tool calls should remain below agreed operational threshold.
- **Zero-tolerance conditions**:
  - Any write-tool execution without required HITL approval.
  - Any PHI in logs by default policy.

## Regression Policy
- Evaluations must run for:
  - Pull requests affecting prompts, routing policy, tool registry/enforcement, retrieval config, or safety policy.
  - Model/provider changes.
  - Tool contract changes.
  - Runtime configuration changes that affect budgets/fallbacks.
- Release gating concept:
  - **Canary gate**: run targeted smoke/regression/safety set on limited traffic.
  - **Full rollout gate**: require full suite pass and no zero-tolerance violations.

## Minimum Evaluation Artifacts to Store
- Dataset/test-suite version.
- Policy, prompt, and tool-contract versions.
- Model/provider configuration used for the run.
- Summary results (pass/fail by suite) and failure list with identifiers.

## Definition of Done
- Golden-set coverage exists for key Flow A user intents.
- Injection tests exist across user, retrieval, and tool-output vectors.
- Tool contract tests verify invalid/unknown fields are rejected.
- Routing tests verify tier selection and fallback behavior.
- HITL tests verify approval, timeout, and deny enforcement.
- Groundedness/citation acceptance thresholds are defined and measured.
- Zero-tolerance checks are enforced and fail the gate.
- Regression triggers are documented for PR/config/prompt/tool changes.
- Canary and full-rollout gating criteria are defined.
- Evaluation artifacts are versioned and retained for auditability.
