# NetSage Human Review Prompt

Review the AI diagnosis before any fix is accepted.

Return valid JSON only:

```json
{
  "case_id": "string",
  "decision": "Accepted|Edited|Rejected",
  "final_root_cause": "string",
  "review_notes": "string",
  "approved_fix_steps": ["string"],
  "verification_required": ["string"]
}
```

Reviewer checklist:

- Does the diagnosis cite real evidence from the case?
- Does the OSI layer match the fault?
- Is the next command safe and useful?
- Are the fix steps specific enough for Packet Tracer or Cisco IOS?
- Could the suggested fix create a security or availability risk?
- Has verification been listed before the case is closed?
