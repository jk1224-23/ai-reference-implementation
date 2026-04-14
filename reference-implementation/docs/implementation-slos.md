# Implementation SLOs: Operational Metrics

## What We Measure (For Runnable Code)

When you deploy this reference implementation, measure these operational metrics.

---

## Configuration & Policy SLOs

### Policy Reload Latency
**Metric:** Time from config file change to enforcement  
**Target:** < 5 seconds  
**Why:** Policy changes should take effect quickly  

```yaml
# When you edit tool_allowlist.yaml
# Code watches for changes and reloads
# Max 5 seconds until new policy is active
```

**How to test:**
```bash
# Edit config
sed -i 's/max_tool_calls: 2/max_tool_calls: 1/' config/skill_registry.yaml

# Verify new limit takes effect
# (tool call 2 should be rejected within 5 seconds)
```

---

### Configuration Validation Success Rate
**Metric:** % of config changes that pass schema validation  
**Target:** 100% (no invalid configs reach production)  

```yaml
# Before deploying config change:
# - JSON schema validation
# - Intent/skill/tool mapping consistency
# - Required fields present
# - Enum values valid

# Invalid config = rejected, not deployed
```

**Validation checks:**
```python
def validate_skill_registry(config):
    """Ensure skill config is valid before using"""
    
    # Check 1: All referenced tools exist
    for skill_name, skill in config["skills"].items():
        for tool in skill.get("allowed_tools", []):
            assert tool in all_registered_tools
    
    # Check 2: All skills have required fields
    for skill in config["skills"].values():
        assert "category" in skill
        assert "hitl_required" in skill
        assert "max_tool_calls_per_turn" in skill
    
    # Check 3: Intent to skill mapping valid
    for intent, skill_name in config.get("intent_to_skill", {}).items():
        assert skill_name in config["skills"]
    
    return True  # Valid
```

---

## Tool Execution SLOs

### Schema Validation Pass Rate
**Metric:** % of tool calls that pass schema validation  
**Target:** > 99%  
**Why:** If schema validation fails, tool can't execute  

```
Tool call comes in
  → Is it valid against schema? YES (99%+)
  → Execute
  
Tool call comes in
  → Invalid schema? NO (< 1%)
  → Reject immediately
```

**Alert:** If schema validation fails > 1%, investigate:
- Is LLM generating malformed calls?
- Is schema too strict?
- Is tool contract outdated?

---

### Rate Limit Enforcement
**Metric:** % of requests that respect rate limits  
**Target:** 100%  
**Why:** Rate limits must always be enforced  

```python
# From skill_registry.yaml:
max_tool_calls_per_turn: 2
max_turn_duration_ms: 5000

# Enforcement:
tool_call_count = 0
for tool_call in request.tool_calls:
    tool_call_count += 1
    if tool_call_count > 2:
        raise RateLimitExceeded("Max 2 calls per turn")
    
    elapsed = time.time() - request.start_time
    if elapsed > 5000:
        raise TimeoutError("Max 5 seconds per turn")
```

**Measurement:**
```bash
# Monitor logs for rate limit violations
grep "RateLimitExceeded\|TimeoutError" logs/*.log | wc -l

# Target: 0 (limits always enforced)
# If > 0, something is wrong
```

---

## Policy Decision SLOs

### Policy Decision Consistency
**Metric:** Same intent always gets same decision  
**Target:** 100%  
**Why:** Policy must be predictable  

```python
def test_policy_consistency():
    """Same intent should always get same decision"""
    
    intent = Intent("APPEAL_INITIATION", user_id="M-123")
    decision1 = apply_policy(intent)
    decision2 = apply_policy(intent)
    decision3 = apply_policy(intent)
    
    assert decision1 == decision2 == decision3
```

**In production:**
- Spot-check: Random requests, replay decision
- Deterministic: No randomness in policy logic
- Versioned: Config changes are tracked

---

### HITL Gate Effectiveness
**Metric:** % of HIGH-risk intents that require HITL  
**Target:** 100%  
**Why:** All high-risk operations must escalate to humans  

```yaml
# In tool_allowlist.yaml
APPEAL_INITIATION:
  risk_tier: HIGH
  allowed_tools:
    - name: "case.create.v1"
      requires_approval: true
```

**Monitoring:**
```bash
# Every request with risk_tier=HIGH should have:
# - policy_decision: HITL_REQUIRED
# - approval event: approved_by: [human]

# If HIGH-risk request executed WITHOUT approval = incident
```

---

## Audit Trail SLOs

### Trace Completeness
**Metric:** % of requests with complete trace  
**Target:** 100%  
**Why:** Incomplete traces break compliance  

```
Complete trace has:
✓ intent_recognized event
✓ policy_decision event
✓ tool_call event(s)
✓ outcome/approval event(s)

Missing ANY event = incomplete
```

**Validation:**
```python
def validate_trace_completeness(trace_id):
    """Ensure trace has all required events"""
    
    events = audit_log.get_events(trace_id)
    required_events = [
        "intent_recognized",
        "policy_decision",
    ]
    
    if request.requires_hitl:
        required_events.append("approval_decision")
    
    if request.executes_tool:
        required_events.append("tool_executed")
    
    found = {e["event_type"] for e in events}
    assert required_events.issubset(found)
```

---

### Event Timestamp Accuracy
**Metric:** All audit events have precise timestamps  
**Target:** All events timestamped (UTC, precise to ms)  

```json
{
  "trace_id": "tr-9f8d2e1c",
  "event_type": "tool_executed",
  "timestamp": "2026-04-14T14:25:12.567Z",  // Must be present
  "tool": "case.create.v1",
  "status": "success"
}
```

**Validation:**
```python
def validate_event_timestamps():
    """All events must have timestamps"""
    
    for event in audit_log.all_events():
        assert "timestamp" in event
        assert event["timestamp"].isoformat().endswith("Z")  # UTC
```

---

### Audit Log Immutability
**Metric:** Audit logs cannot be edited or deleted  
**Target:** Write-once, append-only storage  
**Why:** Compliance requires immutable audit trail  

**Implementation:**
```python
class AuditLog:
    def write(self, event):
        """Append only, no edits or deletes"""
        # Write to append-only storage
        # (database with no UPDATE/DELETE, or immutable log files)
        
    def read(self, trace_id):
        """Read for investigation"""
        return self.storage.get(trace_id)
    
    def delete(self):
        """FORBIDDEN"""
        raise NotImplementedError("Audit logs are immutable")
    
    def edit(self):
        """FORBIDDEN"""
        raise NotImplementedError("Audit logs are immutable")
```

---

## Observability SLOs

### Log Ingestion Success Rate
**Metric:** % of events successfully written to audit log  
**Target:** 99%+  
**Why:** If logging fails, audit trail has gaps  

```python
# Track success
events_logged = 0
events_failed = 0

for event in request.events:
    try:
        audit_log.write(event)
        events_logged += 1
    except Exception as e:
        events_failed += 1
        alert(f"Failed to log: {e}")

success_rate = events_logged / (events_logged + events_failed)
# Alert if < 99%
```

---

### Configuration Drift Detection
**Metric:** Deployed config matches config in git  
**Target:** Always in sync (0% drift)  
**Why:** Config drift = audit trail becomes unreliable  

```python
def detect_config_drift():
    """Verify deployed config matches git"""
    
    deployed = load_from_runtime()
    git_version = load_from_git()
    
    if deployed != git_version:
        alert("CONFIG_DRIFT_DETECTED")
        # Is someone editing config at runtime?
        # Is deployment broken?
```

**Prevention:**
- Config files in git (source of truth)
- Runtime loads from git (no local edits)
- Checksum validation on startup

---

## What NOT to Measure

### ❌ "LLM Accuracy"
Don't measure how often the LLM is "correct" because:
- Configuration gates bad outputs
- Tool schema validation catches errors
- Architecture assumes hallucinations will happen

**Instead:** Measure if bad outputs are caught before reaching data.

---

### ❌ "Latency"
Don't optimize for speed because:
- Policy decisions add latency
- HITL adds latency
- That's the point

**Instead:** Measure if decisions are made consistently.

---

### ❌ "Cost per Request"
Don't optimize for token efficiency because:
- Audit trail requires logging
- Schema validation adds tokens
- Safety > cost

**Instead:** Measure if resources are being wasted (runaway loops, etc).

---

## Monitoring Dashboard

```
┌─────────────────────────────────────┐
│ Configuration Reloads (Last 24h)    │
│ Successful: 47                      │
│ Failed: 0 ✅                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Tool Call Validation Success        │
│ Target: > 99%                       │
│ Current: 99.7% ✅                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Audit Trail Completeness            │
│ Complete traces: 12,456             │
│ Incomplete: 0 ✅                    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Rate Limit Violations               │
│ Target: 0                           │
│ Current: 0 ✅                       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Config Drift                        │
│ Status: Synced ✅                   │
│ Last Check: 5 minutes ago           │
└─────────────────────────────────────┘
```

---

## Testing These SLOs

```python
# Test policy consistency
def test_policy_consistency():
    for _ in range(100):
        decision = apply_policy(intent)
        assert decision == expected_decision

# Test rate limits
def test_rate_limits():
    for i in range(10):
        if i < max_calls:
            execute_tool()  # OK
        else:
            with pytest.raises(RateLimitExceeded):
                execute_tool()  # Blocked

# Test HITL requirement
def test_high_risk_requires_hitl():
    policy = get_policy("APPEAL_INITIATION")
    assert policy["risk_tier"] == "HIGH"
    assert policy["allowed_tools"][0]["requires_approval"] == True

# Test audit trail
def test_trace_completeness():
    trace = audit_log.get_trace(trace_id)
    assert "intent_recognized" in trace
    assert "policy_decision" in trace
    assert "tool_executed" in trace
```

---

## Key Insight

> **Measure governance, not performance. Measure if the system stays in control, not if it's fast.**

Configuration drives everything. SLOs measure if configuration is working.
