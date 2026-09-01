# qwen3.5:397b

Sat a judge seat in P-S1. Thinking-off works, and it is the cheapest of the
four seats measured that day.

P-S1, 5 trials at `reasoning_effort: none`: **5/5 clean content, 0/5 separate
reasoning field, 5 median completion tokens.**

`documented_values` is left empty for the same reason as the DeepSeek document:
no committed citation for this model's own published value set.

```deepreason-model-profile-v1
schema: deepreason-model-profile.v1
model_id: qwen3.5:397b
measured_on: 2026-08-31
reasoning:
  extraction_value: none
  thinking_disablable: true
  disabling_values: [none]
  trace_destination:
    none: absent
evidence:
  - "5/5 clean content, 0/5 separate reasoning field, 5 median completion tokens at none: git show origin/claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md (blob 00b7914fc66a0bec96e838c3317974e9d2eb9646), section 3"
probe: "python scripts/model_profile_probe.py --document 'docs/model-profiles/qwen3.5:397b/agent.md'"
```
