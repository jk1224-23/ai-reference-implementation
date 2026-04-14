# Worked Example: From Config to Execution

## How Configuration Becomes Control

This example shows exactly how `skill_registry.yaml` and `tool_allowlist.yaml` control what the LLM can actually do.

---

## The Request: "I want to appeal my claim"

### Step 1: User Input
```
member_id: member:M-789456
intent_text: "My claim was denied. I want to appeal."
```

---

## Step 2: Load Configuration

**First, the system loads all policy configuration:**

```python
# Load skill registry (defines what skills exist and their constraints)
skill_registry = load_yaml("config/skill_registry.yaml")

# Load tool allowlist (maps intents to allowed tools)
tool_allowlist = load_yaml("config/tool_allowlist.yaml")
```

**What's in skill_registry.yaml:**
```yaml
skills:
  skill.claim_update.v1:
    category: "TRANSACTIONAL"
    allowed_tools:
      - "case.create.v1"
    hitl_required: true
    subject_binding_required: true
    max_tool_calls_per_turn: 2
    max_turn_duration_ms: 9000
    description: "State-changing claim assistance requiring HITL."
```

**What's in tool_allowlist.yaml:**
```yaml
intents:
  APPEAL_INITIATION:
    skill: "skill.claim_update.v1"
    risk_tier: HIGH
    allowed_tools:
      - name: "case.create.v1"
        requires_approval: true
        approval_type: "HITL"
        tool_type: "TRANSACTIONAL"
    notes: "Appeals/grievances are supervised. Assistant drafts; human approves."
```

---

## Step 3: Intent Recognition

```python
# Orchestrator recognizes the user's intent
def recognize_intent(text):
    # (In real system: ML classifier)
    if "appeal" in text.lower():
        return Intent(
            name="APPEAL_INITIATION",
            confidence=0.94,
            user_id="member:M-789456"
        )

intent = recognize_intent("My claim was denied. I want to appeal.")
# Returns: Intent(name="APPEAL_INITIATION", ...)
```

---

## Step 4: Policy Lookup (Configuration Enforcement)

```python
def get_policy_for_intent(intent_name):
    """Look up this intent in tool_allowlist.yaml"""
    policy = tool_allowlist["intents"].get(intent_name)
    if not policy:
        raise IntentNotConfigured(f"{intent_name} not in allowlist")
    return policy

policy = get_policy_for_intent("APPEAL_INITIATION")

# policy now contains:
# {
#   "skill": "skill.claim_update.v1",
#   "risk_tier": "HIGH",
#   "allowed_tools": [{"name": "case.create.v1", "requires_approval": true}],
#   "notes": "Appeals/grievances are supervised..."
# }
```

**Key insight:** The LLM doesn't decide what it can do. Configuration does.

---

## Step 5: Get Skill Constraints

```python
def get_skill_constraints(skill_name):
    """Look up skill definition in skill_registry.yaml"""
    skill = skill_registry["skills"].get(skill_name)
    if not skill:
        raise SkillNotDefined(f"{skill_name} not in registry")
    return skill

skill = get_skill_constraints(policy["skill"])

# skill now contains:
# {
#   "category": "TRANSACTIONAL",
#   "allowed_tools": ["case.create.v1"],
#   "hitl_required": true,
#   "subject_binding_required": true,
#   "max_tool_calls_per_turn": 2,
#   "max_turn_duration_ms": 9000
# }
```

---

## Step 6: Pre-Execution Checks (Before LLM Sees Anything)

```python
def validate_request_against_policy(intent, policy, skill):
    """Check constraints BEFORE we let LLM execute"""
    
    # Check 1: Risk tier → HITL required?
    if policy["risk_tier"] == "HIGH":
        check_hitl_queue_availability()
        # If HITL unavailable, return DENY
    
    # Check 2: Subject binding required?
    if skill["subject_binding_required"]:
        if not user_owns_resource(user_id, claim_id):
            return PolicyDecision.DENY
    
    # Check 3: Tool allowlist
    allowed = skill["allowed_tools"]
    if "case.create.v1" not in allowed:
        return PolicyDecision.DENY
    
    # All checks pass → HITL required
    return PolicyDecision.HITL_REQUIRED

decision = validate_request_against_policy(intent, policy, skill)
# Returns: PolicyDecision.HITL_REQUIRED
```

**Key insight:** No tool execution yet. Just validation.

---

## Step 7: Orchestration Decision

```python
def apply_policy_decision(decision, intent):
    """Route based on policy decision"""
    
    if decision == PolicyDecision.ALLOW:
        # Policy approved → execute tool directly
        return route_to_tool_execution(intent)
    
    elif decision == PolicyDecision.HITL_REQUIRED:
        # Policy says humans must approve
        return route_to_human_approval(intent)
    
    elif decision == PolicyDecision.DENY:
        # Policy blocked it
        return deny_with_reason(intent, "Policy denied this request")

result = apply_policy_decision(decision, intent)
# Routes to: route_to_human_approval
```

**Log event:**
```json
{
  "event_type": "policy_decision",
  "timestamp": "2026-04-14T14:23:45Z",
  "intent": "APPEAL_INITIATION",
  "decision": "HITL_REQUIRED",
  "reason": "risk_tier=HIGH"
}
```

---

## Step 8: LLM Generates Draft (With Constraints)

```python
def prepare_lm_context(intent, policy, skill):
    """Tell LLM what it CAN'T do"""
    
    allowed_tools = skill["allowed_tools"]
    
    prompt = f"""
You are helping with: {intent.name}

Policy constraints:
- Allowed tools: {allowed_tools}
- HITL required: {skill['hitl_required']}
- Do NOT call tools
- Prepare draft response for human review

Your job: Summarize the user's appeal clearly for human review.
"""
    
    return prompt

# LLM reads prompt, understands:
# "I can prepare a draft, but NOT execute tools"
# "A human must approve first"

lm_output = call_lm(prompt)
# Returns: "Appeal draft: Member disputes coverage..."
```

**Key insight:** LLM knows its constraints before it thinks.

---

## Step 9: Human Review & Approval

```python
def route_to_human_approval(intent, lm_draft):
    """Queue for human review"""
    
    approval_request = ApprovalRequest(
        intent=intent.name,
        draft=lm_draft,
        required_tool="case.create.v1",
        risk_tier="HIGH",
        member_id=intent.user_id
    )
    
    # Add to human approval queue
    approval_queue.enqueue(approval_request)
    
    return {
        "status": "PENDING_APPROVAL",
        "queue_position": 5,
        "user_message": "A specialist will review this shortly."
    }

result = route_to_human_approval(intent, lm_draft)
```

**Human sees:**
```
APPEAL REQUEST (HIGH RISK - REQUIRES APPROVAL)

Member: John Smith
Claim: C-2024-001234
Appeal Draft: "Coverage determination dispute - member disputes denial"

Policy Gate: HITL_REQUIRED (Risk: HIGH)

[APPROVE] [DENY] [REQUEST_INFO]
```

**Human clicks: [APPROVE]**

```json
{
  "decision": "APPROVED",
  "approved_by": "support_agent:A-5432",
  "timestamp": "2026-04-14T14:25:12Z",
  "signature": "..."  // Cryptographic signature
}
```

---

## Step 10: Construct Tool Call (Validate Against Schema)

```python
def build_tool_call(intent, lm_draft, approval):
    """After approval, prepare actual tool call"""
    
    # Step 1: Get tool schema
    tool_schema = get_schema("case.create.v1")
    # {
    #   "required": ["claim_id", "case_type"],
    #   "properties": {
    #     "claim_id": {"type": "string", "pattern": "^claim:..."}
    #     "case_type": {"type": "string", "enum": ["APPEAL", ...]}
    #   }
    # }
    
    # Step 2: Build parameters
    tool_call = {
        "tool": "case.create.v1",
        "parameters": {
            "claim_id": "C-2024-001234",
            "case_type": "APPEAL",
            "member_statement": lm_draft,
            "approver": approval["approved_by"],
            "approval_timestamp": approval["timestamp"]
        }
    }
    
    # Step 3: Validate parameters against schema
    if not validate_schema(tool_call["parameters"], tool_schema):
        raise InvalidToolCall("Parameters don't match schema")
    
    # Step 4: Check constraints from skill registry
    skill = get_skill_constraints("skill.claim_update.v1")
    if skill["max_tool_calls_per_turn"] <= tool_call_count:
        raise RateLimitExceeded()
    
    return tool_call

tool_call = build_tool_call(intent, lm_draft, approval)
```

**Validation events logged:**
```json
{
  "event_type": "tool_call_validated",
  "tool": "case.create.v1",
  "validation_status": "PASSED",
  "parameters_match_schema": true,
  "rate_limits_ok": true
}
```

---

## Step 11: Execute Tool (External System)

```python
def execute_tool_call(tool_call, approval):
    """Call the actual system of record"""
    
    # Tool execution is privileged - approval required
    if not approval or not verify_approval_signature(approval):
        raise ApprovalRequired()
    
    # Execute the tool
    result = systems_of_record.execute(
        tool_call["tool"],
        tool_call["parameters"],
        approval_token=approval["signature"]
    )
    
    return result

result = execute_tool_call(tool_call, approval)
# Returns: {
#   "case_id": "AP-2024-005678",
#   "status": "created",
#   "next_steps": "Appeal review team will contact..."
# }
```

---

## Step 12: Complete Audit Trail

```python
def log_complete_flow(events):
    """All events linked by trace_id"""
    
    trace_id = "tr-9f8d2e1c"
    
    events = [
        {"trace_id": trace_id, "event": "intent_recognized", "intent": "APPEAL_INITIATION"},
        {"trace_id": trace_id, "event": "policy_decision", "decision": "HITL_REQUIRED"},
        {"trace_id": trace_id, "event": "hitl_escalated", "status": "queued"},
        {"trace_id": trace_id, "event": "approval_decision", "decision": "APPROVED", "approver": "A-5432"},
        {"trace_id": trace_id, "event": "tool_call_validated", "tool": "case.create.v1"},
        {"trace_id": trace_id, "event": "tool_executed", "case_id": "AP-2024-005678"}
    ]
    
    for event in events:
        audit_log.write(event)
```

**Result: Complete, auditable trace**
```bash
$ grep "tr-9f8d2e1c" audit.log
# See entire request flow, start to finish
```

---

## The Key Insight

This entire flow is **configuration-driven**:

1. **skill_registry.yaml** defines: Can this skill execute? What are the constraints?
2. **tool_allowlist.yaml** defines: Which tools? Do they require approval?
3. **Code enforces** all constraints before LLM acts

**The LLM never decides:**
- What it can do
- What approval is needed
- What rate limits apply
- What schemas are required

**Configuration decides all of this.**

---

## What Changes When You Edit Config

### Before Edit:
```yaml
APPEAL_INITIATION:
  allowed_tools:
    - "case.create.v1"
```

Result: Tool executed immediately (no HITL)

### After Edit:
```yaml
APPEAL_INITIATION:
  allowed_tools:
    - "case.create.v1"
  risk_tier: HIGH  # ← Added this
```

Result: Tool execution now requires HITL approval

**No code changes. Just config.**

This is the power of external configuration.

---

## Testing This Flow

```python
# Test 1: Verify policy blocks unauthorized tool
def test_unauthorized_tool():
    intent = Intent("UNAUTHORIZED_ACTION")
    policy = tool_allowlist["intents"].get(intent)
    assert policy is None  # Not configured
    assert apply_policy(intent) == PolicyDecision.DENY

# Test 2: Verify rate limits enforced
def test_rate_limit():
    skill = get_skill("skill.kb_grounded_answer.v1")
    assert skill["max_tool_calls_per_turn"] == 2
    
    for i in range(3):
        if i < 2:
            execute_tool()  # OK
        else:
            with pytest.raises(RateLimitExceeded):
                execute_tool()  # Blocked

# Test 3: Verify HITL required
def test_hitl_required():
    policy = tool_allowlist["intents"]["APPEAL_INITIATION"]
    assert policy["risk_tier"] == "HIGH"
    decision = apply_policy_decision(...)
    assert decision == PolicyDecision.HITL_REQUIRED
```

---

## Summary

Configuration → Policy → Validation → Execution → Audit

Each step enforced by code, driven by configuration, verified by tests.

The LLM is creative. Configuration keeps it in control.
