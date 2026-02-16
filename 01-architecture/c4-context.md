# C4 Context: AI Assistant System

> **Status:** Architecture-focused | Vendor-neutral | Flow A + Flow B  
> **Flows:** Flow A (RAG + Read-Only Tools) | Flow B (Bounded Agent + HITL + Write Tools)  
> **Start Here:** [Reading Guide](../00-overview/reading-guide.md) | [Key Decisions](key-decisions.md) | [Flow Sequences](sequence-a-rag-readonly.md)

## TL;DR
- The AI Assistant System sits at the enterprise trust boundary and coordinates users, tools, and data systems.
- Flow A emphasizes grounded retrieval and read-only interactions.
- Flow B adds bounded write actions with HITL and stronger operational controls.
- Identity, policy enforcement, and observability anchor both flows.

## Navigation
- Overview: [`00-overview/readme.md`](../00-overview/readme.md) | [`00-overview/reading-guide.md`](../00-overview/reading-guide.md)
- Architecture: [`01-architecture/key-decisions.md`](key-decisions.md) | [`01-architecture/c4-context.md`](c4-context.md) | [`01-architecture/sequence-a-rag-readonly.md`](sequence-a-rag-readonly.md) | [`01-architecture/sequence-b-agent-hitl.md`](sequence-b-agent-hitl.md)
- Governance: [`02-governance/model-routing-policy.md`](../02-governance/model-routing-policy.md) | [`02-governance/tool-registry-policy.md`](../02-governance/tool-registry-policy.md)
- Evaluation: [`03-evaluations/eval-plan.md`](../03-evaluations/eval-plan.md)

## System Narrative
The **AI Assistant System** is an enterprise AI boundary system that supports two operating modes:
- **Flow A**: Enterprise RAG with read-only tools for grounded, low-risk question answering.
- **Flow B**: Bounded agent behavior with human-in-the-loop (HITL) approvals and controlled write tools for action workflows.

At context level, the system sits between users and enterprise data/services, enforcing identity, policy, tool governance, and observability while limiting risk from untrusted input and high-impact actions.

## External Actors
- **End User (customer or employee)**: Authenticates and submits requests; receives grounded answers (Flow A) and guided action outcomes (Flow B).
- **Human Approver/Reviewer (HITL role)**: Reviews and approves/rejects write actions when risk, impact, or reversibility requires human control.
- **Platform Ops/SRE**: Monitors reliability and safety posture, handles incidents, and can apply kill switches or feature gates.

## External Systems
- **Identity Provider (SSO/OIDC)**: Issues and validates identity/session claims used for access control and audit.
- **Knowledge Sources (SharePoint/Confluence/Docs/Files)**: Enterprise content for retrieval and grounding.
- **Systems of Record (Claims/Members/Providers/etc.)**: Authoritative business systems read in Flow A and conditionally written in Flow B.
- **Tool Gateway / API Management**: Central policy/authn/authz/schema enforcement point for all tool calls.
- **Observability Stack (logs/metrics/traces)**: Receives telemetry, alerts, and audit signals for operations and compliance.

## Trust Boundaries and Data Classification
| Boundary | Typical data classes | Context-level controls |
|---|---|---|
| User to AI Assistant System | Internal, PII, possible PHI in prompts | SSO/OIDC identity, session controls, request policy checks |
| AI Assistant System to Knowledge Sources | Internal docs, sensitive internal content, possible regulated data | Retrieval authorization, scoped connectors, source-level ACL propagation |
| AI Assistant System to Tool Gateway/API Mgmt | Internal operational data, PII/PHI depending on domain | Deny-by-default tool policy, schema validation, action allowlists |
| Tool Gateway to Systems of Record | High-impact transactional data, PII/PHI | Least-privilege service identity, audit logging, write constraints |
| AI Assistant System to Observability Stack | Metadata, operational telemetry, limited payload snippets by policy | Correlation IDs, redaction/minimization, retention controls |

## C4-Style Context Diagram
```mermaid
flowchart LR
    %% External actors
    EU["End User - Customer or Employee"]
    HA["Human Approver or Reviewer - HITL Role"]
    OPS["Platform Ops/SRE"]

    %% Enterprise trust boundary
    subgraph ENT["Enterprise Trust Boundary"]
        AAS["AI Assistant System - Flow A RAG Read-Only Tools - Flow B Bounded Agent HITL Write Tools"]
        TG["Tool Gateway / API Management"]
        OBS["Observability Stack - Logs Metrics Traces"]
    end

    %% External systems
    IDP["Identity Provider - SSO OIDC"]
    KS["Knowledge Sources - SharePoint Confluence Docs Files"]
    SOR["Systems of Record - Claims Members Providers etc"]

    EU -->|Authenticate and Submit Request| AAS
    AAS -->|Token and Claims Validation| IDP

    AAS -->|Retrieve Grounding Evidence for Flow A| KS

    AAS -->|Tool Intents| TG
    TG -->|Governed API Calls| SOR

    AAS -->|Approval Request for Write Actions| HA
    HA -->|Approve Reject or Comment| AAS

    AAS -->|Telemetry and Audit Events| OBS
    OPS -->|Monitor Incident Response Kill Switch| AAS
    OPS -->|Alert Triage and SLO Tracking| OBS
```

## Key Risks at the Context Level
> ⚠️ **Risk / Guardrail**
> Untrusted content and write-capable tools require layered controls: policy enforcement, approval gates, and redaction-safe telemetry.

- **Prompt injection vectors**: Malicious instructions can enter through user input or retrieved content.
  - **High-level mitigation**: Treat external text as untrusted, enforce policy outside the model, and keep tool invocation behind gateway controls.
- **Data leakage (PII/PHI/internal)**: Sensitive data may be exposed in responses, logs, or cross-tenant/tool paths.
  - **High-level mitigation**: Identity-scoped retrieval, least-privilege access, redaction/minimization in telemetry, and strict retention boundaries.
- **Tool misuse or overreach**: Unbounded tool execution can cause unauthorized or high-impact changes.
  - **High-level mitigation**: Deny-by-default registry, read/write separation, HITL gates for write actions, and auditable approval trails.
