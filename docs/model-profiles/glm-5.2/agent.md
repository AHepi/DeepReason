# glm-5.2

The model most of this repo's committed runs were made on. Unlike its
successor, `none` really does switch its thinking off here — which is exactly
why a single constant looked correct for so long.

P-S1, conjecturer seat, 5 trials at `reasoning_effort: none`: **5/5 clean
content, 0/5 separate reasoning field, 6 median completion tokens.** The trace
is not moved anywhere; there is no trace.

**Unset is still not off.** In coin canonicity `run-c5f901f3` a live profile
carried `reasoning=None`, which sends no reasoning field at all; this model
then thought by default, the first conjecture turn returned
`completion_tokens` exactly equal to the 24576 cap, and no candidate was
emitted. Omitting the knob and disabling the knob are different acts.

`context_window_tokens`, `max_output_tokens` and `tokens_per_second` are left
out: the record measures configured route capacity, not this model's own
limits.

```deepreason-model-profile-v1
schema: deepreason-model-profile.v1
model_id: glm-5.2
measured_on: 2026-08-31
reasoning:
  documented_values: [none, low, medium, high, max]
  extraction_value: none
  thinking_disablable: true
  disabling_values: [none]
  trace_destination:
    none: absent
evidence:
  - "5/5 clean content, 0/5 separate reasoning field, 6 median completion tokens at none: git show origin/claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md (blob 00b7914fc66a0bec96e838c3317974e9d2eb9646), section 3"
  - "unset is not off, and cost the whole 24576 cap: docs/map/SUB-llm.md Traps, coin canonicity run-c5f901f3"
probe: "python scripts/model_profile_probe.py --document docs/model-profiles/glm-5.2/agent.md"
```
