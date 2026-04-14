# Pitfalls & Implementation Lessons

## What Broke When We Built This (So You Don't Repeat It)

---

## 1. Hardcoding Policy Rules in Code

**❌ The Mistake:**
```python
if intent == "APPEAL_INITIATION":
    require_hitl = True
elif intent == "CLAIM_STATUS":
    require_hitl = False
# ... 50 more if statements
```

**What Happened:**
- Changing policy required redeploying code
- Typos in intent names broke routing
- No one dared touch policy code (too fragile)
- Policy rules mixed with business logic
- Hard to audit: where IS the actual policy?

**✅ What We Do Now:**
```yaml
# skill_registry.yaml - separate file, version controlled
skills:
  skill.claim_update.v1:
    hitl_required: true
    max_tool_calls_per_turn: 2
```

- Policy is data, not code
- Change policy without redeploying
- Audit tool sees exact rules
- Non-engineers can read it

**Why It Matters:**
Policy and implementation must be separate. Otherwise policy becomes invisible.

---

## 2. Tool Allowlisting Only in LLM Context

**❌ The Mistake:**
```python
# In the LLM prompt:
"You have access to: claims.read, case.create, claim.update"

# That's it. No schema validation. No enforcement outside LLM.
```

**What Happened:**
- LLM called tools that didn't exist
- Tool parameters were wrong type (string instead of int)
- Same tool called 100 times in one request (no rate limit)
- Schema validation happened inside tool (too late)
- One bad tool call could corrupt data

**✅ What We Do Now:**
```yaml
# tool_allowlist.yaml - enforced OUTSIDE LLM
intents:
  APPEAL_INITIATION:
    allowed_tools:
      - name: "case.create.v1"
        requires_approval: true
        max_calls_per_turn: 1
    
# Python validates BEFORE tool call:
tool_schema = get_schema("case.create.v1")
if not validate(tool_call, tool_schema):
    raise InvalidToolCall()
```

- Allowlist is external (orchestrator enforces)
- Schema validation before execution
- Rate limiting per skill
- LLM can't bypass these rules

**Why It Matters:**
The LLM is creative but unreliable. Gatekeepers must be outside the LLM.

---

## 3. No Rate Limiting on Tool Calls

**❌ The Mistake:**
```python
# User: "Call this tool 1000 times"
# LLM: "OK!"
for i in range(1000):
    call_tool("kb_search.v1")
```

**What Happened:**
- One request exhausted database quota
- System slowed down for all users
- Tool costs exploded
- No way to stop runaway loops
- DOS vulnerability

**✅ What We Do Now:**
```yaml
# In skill_registry.yaml:
skill.kb_grounded_answer.v1:
  max_tool_calls_per_turn: 2
  max_turn_duration_ms: 5000

# Python enforces:
if tool_call_count > max_allowed:
    raise RateLimitError("Max 2 calls per turn")
```

- Hard limits per skill
- Timeout on turn duration
- Monitoring alerts on usage spikes
- Graceful degradation

**Why It Matters:**
Without rate limits, the LLM can accidentally DOS your system.

---

## 4. Storing Config in Environment Variables

**❌ The Mistake:**
```bash
export SKILL_REGISTRY="skill_registry.yaml"
export TOOL_ALLOWLIST="tool_allowlist.yaml"
export POLICY_RULES="policy.json"
# ... 30 more env vars
```

**What Happened:**
- Config scattered across env, files, code
- Hard to know what's configured
- Deployments failed silently (wrong env var)
- No version history
- Rollback was impossible

**✅ What We Do Now:**
```
reference-implementation/config/
  ├── skill_registry.yaml (versioned in git)
  ├── tool_allowlist.yaml (versioned in git)
  └── observability_config.yaml (versioned in git)

# Load from disk, not env
config = load_yaml("config/skill_registry.yaml")
```

- All config in git
- Version history for every change
- Diffs show exactly what changed
- Rollback is `git checkout`

**Why It Matters:**
Config is code. Treat it like code.

---

## 5. Tool Contracts Were Unclear

**❌ The Mistake:**
LLM thinks it knows what `claims.read` does, but:
```
Engineer A says: "It returns claim details"
Engineer B says: "It requires claim_id AND member_id"
LLM learned: "Just pass claim_id, it'll figure it out"
Result: Tool fails silently, LLM hallucinates the result
```

**What Happened:**
- Ambiguous tool contracts
- Different engineers, different assumptions
- LLM called tools with incomplete parameters
- Tools failed but no error message
- Output was garbage

**✅ What We Do Now:**
```yaml
# reference-implementation/standards/tool-contract-standard.md
tool: "claims.read.v1"
description: "Read claim details with full history"
input_schema:
  type: object
  required:
    - claim_id
    - member_id
  properties:
    claim_id:
      type: string
      pattern: "^claim:[0-9]{10}$"
    member_id:
      type: string
      pattern: "^member:[0-9]{6}$"
output_schema:
  type: object
  properties:
    status: {type: string, enum: [APPROVED, DENIED, PENDING]}
    amount: {type: number}
    denial_reason: {type: string}
```

- JSON schema for every tool
- Clear input/output contracts
- Pattern validation
- Schema validation before and after

**Why It Matters:**
Tools are APIs. APIs need schemas.

---

## 6. No Tracing Across Tool Calls

**❌ The Mistake:**
```
Request comes in
  → Tool call 1: kb_search
  → Tool call 2: claims.read
  → Tool call 3: case.create

Logs show:
  [kb_search] Success
  [claims.read] Success
  [case.create] Failed

But which request? How did they connect? No idea.
```

**What Happened:**
- Tool calls were logged separately
- No way to trace request through system
- Incident investigation took hours
- Logs were useless for debugging

**✅ What We Do Now:**
```python
# All events share trace_id
trace_id = "tr-9f8d2e1c"

log_event({
  "trace_id": trace_id,
  "event": "tool_called",
  "tool": "kb_search.v1",
  "status": "success"
})

log_event({
  "trace_id": trace_id,
  "event": "tool_called",
  "tool": "claims.read.v1",
  "status": "success"
})

log_event({
  "trace_id": trace_id,
  "event": "tool_called",
  "tool": "case.create.v1",
  "status": "failed",
  "reason": "Database timeout"
})

# Now you can: grep trace_id and see entire flow
```

- Every event has trace_id
- Query by trace_id = see entire request
- Incident investigation is fast

**Why It Matters:**
Without tracing, logs are noise.

---

## 7. Tool Execution Without Approval Verification

**❌ The Mistake:**
```python
approval = get_hitl_approval(intent)  # Returns True/False

if approval:
    execute_tool(call)  # But we don't verify approval is still valid
```

**What Happened:**
- Approval expired
- Human changed mind
- Approval was from wrong user
- Tool executed without valid approval
- Audit trail was incomplete

**✅ What We Do Now:**
```python
approval = get_hitl_approval(intent)

if not approval:
    raise ApprovalRequired()

# Verify approval is still valid
verify_approval_signature(approval)
verify_approval_timestamp_recent(approval)
verify_approver_has_permission(approval.approver)

# Then execute with approval token
execute_tool(call, approval_token=approval.token)

# Log with approval evidence
log_event({
  "event": "tool_executed",
  "tool": call.tool,
  "approved_by": approval.approver,
  "approval_timestamp": approval.timestamp
})
```

- Approval signature validated
- Expiration checked
- Approver permissions verified
- Execution logged with approval evidence

**Why It Matters:**
HITL means nothing if you don't verify the approval.

---

## 8. Confusing Intent with Skill with Tool

**❌ The Mistake:**
```
User says: "I want to appeal"
Is that:
  - An INTENT? (What the user wants)
  - A SKILL? (How we handle it)
  - A TOOL? (What system changes)

Code mixed all three concepts. Nobody knew which was which.
```

**What Happened:**
- Mapping was unclear (intent → skill → tool)
- Same name used for different concepts
- Routing logic was fragile
- Adding new intents was confusing

**✅ What We Do Now:**
```yaml
# Clear separation:

# 1. INTENT (user-facing)
APPEAL_INITIATION: "User wants to appeal a claim"

# 2. SKILL (how we handle it)
skill.claim_update.v1: "Update claim records with HITL approval"

# 3. TOOL (what actually changes data)
case.create.v1: "Create case in system of record"

# Mapping is explicit:
intent_to_skill:
  APPEAL_INITIATION: skill.claim_update.v1

skill_to_tools:
  skill.claim_update.v1: [case.create.v1]
```

- Intent = user request
- Skill = orchestration logic
- Tool = actual execution
- Mapping is explicit and auditable

**Why It Matters:**
Clarity about concepts prevents bugs.

---

## 9. No Observability Events for Policy Decisions

**❌ The Mistake:**
```python
# Policy checks, makes decision, but doesn't log it
if policy.check(intent):
    execute()
else:
    deny()
# No event logged about the decision
```

**What Happened:**
- Policy decisions were invisible
- Couldn't audit what was allowed/denied
- Compliance review found missing evidence
- "Did policy actually gate this?" — No way to tell

**✅ What We Do Now:**
```python
decision = policy.check(intent)

log_event({
  "event_type": "policy_decision",
  "timestamp": "2026-04-14T14:23:45.123Z",
  "intent": "APPEAL_INITIATION",
  "decision": "HITL_REQUIRED",
  "risk_tier": "HIGH",
  "reason": "High-risk transactional operation"
})

if decision == "ALLOW":
    execute()
elif decision == "HITL_REQUIRED":
    escalate_to_human()
else:
    deny()
```

- Every policy decision is logged
- Full audit trail
- Compliance can see exactly what was gated
- Incident investigation is complete

**Why It Matters:**
Policy is only useful if you can prove it worked.

---

## 10. Reusing Configs Across Different Environments

**❌ The Mistake:**
```yaml
# config.yaml (same for dev, staging, prod)
db_host: localhost
log_level: DEBUG
max_retries: 10
tool_timeout: 5000  # Too short for prod
```

**What Happened:**
- Prod inherited dev settings
- Timeouts too short → requests failed
- Debug logging slowed prod
- One bad deploy broke everything
- Rollback was painful

**✅ What We Do Now:**
```
config/
  ├── defaults.yaml (baseline)
  ├── dev.yaml (dev overrides)
  ├── staging.yaml (staging overrides)
  └── prod.yaml (prod overrides)
```

```python
# Load layered config
config = load_yaml("config/defaults.yaml")
config.update(load_yaml(f"config/{ENVIRONMENT}.yaml"))

# Prod config is tested separately
# No surprises at deployment
```

- Environment-specific configs
- Overrides are explicit
- Each environment tested independently
- Rollback per environment

**Why It Matters:**
Prod is different. Config should reflect that.

---

## What We Still Get Wrong

- Sometimes skill definitions get out of sync with actual implementation
- Tool timeouts still occasionally need tuning
- Rate limits sometimes too strict (user frustration) or too loose (DOS risk)
- New tools sometimes added without updating allowlist

The difference: We have a framework to catch these and fix them quickly.

---

## The Core Implementation Lesson

> **Configuration must be external, versioned, and validated. Code must enforce it strictly.**

When configuration is external:
- Non-engineers can change policy
- Changes are auditable
- Rollback is possible
- Tests can verify before deploy

Everything else follows.
