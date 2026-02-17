# Skill Enforcement Pseudocode (Documentation Only)

This pseudocode is illustrative and vendor-neutral. It is not executable runtime code.

```text
FUNCTION handle_request(request):
  emit_event("intent_received", request.correlation_id)

  intent = recognize_intent(request)
  emit_event("intent_recognized", intent)

  skill = resolve_skill_from_allowlist(intent)
  IF skill is null:
    emit_event("safe_fallback_triggered", "skill_not_allowlisted")
    RETURN safe_response("No approved skill available")

  policy_result = check_policy(skill, request.user_context, request.data_scope)
  IF policy_result.denied:
    emit_event("safe_fallback_triggered", "policy_denied")
    RETURN safe_response("Action not permitted")

  IF skill.requires_approval:
    approval = request_hitl_approval(skill, request.summary)
    emit_event("approval_decision", approval.status)
    IF approval.status != "approved":
      emit_event("safe_fallback_triggered", "approval_not_granted")
      RETURN safe_response("Approval required before execution")

  tool_result = execute_via_tool_adapter(skill.allowed_tools, request.payload)
  emit_event("tool_execution_completed", tool_result.status)

  IF tool_result.failed:
    emit_event("safe_fallback_triggered", "tool_failure")
    RETURN safe_response("Execution failed; routed to manual follow-up")

  emit_event("outcome_recorded", tool_result.summary)
  RETURN success_response(tool_result)
```

## Example Walkthrough: `skill_claim_update`
1. Request intent is recognized as claim update.
2. Resolver selects `skill_claim_update` from approved allowlist.
3. Policy checks validate data scope and write permission.
4. HITL approval is requested for production write action.
5. On approval, `Claim_Update` executes via tool adapter.
6. Events are emitted for approval, execution, and outcome.
7. If any step fails, system returns a safe fallback response with escalation guidance.
