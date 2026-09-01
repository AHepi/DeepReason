# deepseek-v4-pro:0813

Sat the argumentative-critic seat in P-S1. Thinking-off works here, and the
provider spells it differently from the others: the DeepSeek adapter sends
`{"thinking": {"type": "disabled"}}` rather than a `reasoning_effort` string.
That spelling is a PROVIDER fact and lives in `llm/providers.py`; what the
model does with it is the fact recorded below.

P-S1, 5 trials at the neutral `none`: **5/5 clean content, 0/5 separate
reasoning field, 6 median completion tokens.**

`documented_values` is left EMPTY: this repo's committed record carries no
citation for DeepSeek's own documented value set, and a list written from
memory is exactly what these documents exist to stop. It is descriptive only —
nothing on the dispatch path reads it — so leaving it out costs nothing but a
probe that cannot yet sweep the full set.

**Sibling hazard, already fixed and worth knowing.** An earlier version of the
DeepSeek effort table collapsed `low` and `medium` up to `high`, silently
billing maximum-cost reasoning for the cheapest configured setting. That was a
provider-table bug, not a model fact, and it is pinned by
`tests/test_review_fixes.py::test_deepseek_low_effort_stays_cheap`.

```deepreason-model-profile-v1
schema: deepreason-model-profile.v1
model_id: deepseek-v4-pro:0813
measured_on: 2026-08-31
reasoning:
  extraction_value: none
  thinking_disablable: true
  disabling_values: [none]
  trace_destination:
    none: absent
evidence:
  - "5/5 clean content, 0/5 separate reasoning field, 6 median completion tokens at none: git show origin/claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md (blob 00b7914fc66a0bec96e838c3317974e9d2eb9646), section 3"
probe: "python scripts/model_profile_probe.py --document 'docs/model-profiles/deepseek-v4-pro:0813/agent.md'"
```
