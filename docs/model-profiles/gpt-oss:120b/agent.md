# gpt-oss:120b

The interesting middle case, and the reason `thinking_disablable` and
`trace_destination` had to be separate fields.

P-S1, judge seat, 5 trials at `reasoning_effort: none`: **5/5 clean content,
but 5/5 with a POPULATED reasoning field, and 89 median completion tokens**
against 5-6 for the other three seats that day. This model keeps thinking
whatever it is asked.

**This is not the glm-5.3 failure.** The content stays clean, the trace is
properly quarantined in its own field, and `llm/endpoints.py` reads
`message.reasoning` / `reasoning_content` into `last_reasoning_trace`, so the
spend is auditable rather than hidden. What it means is narrower and still
worth recording: a run that believes it turned thinking off on this seat is
wrong, and will be billed for roughly fifteen times the completion tokens it
expects.

Ollama's own documentation says so directly: GPT-OSS cannot fully disable its
reasoning trace, and takes `"low" | "medium" | "high"` rather than a boolean.

**`extraction_value` is `none`, not `low`, and that is a deliberate choice
about evidence.** `low` is documented but was never measured here; `none` was
measured and produced clean content on every trial. Declaring the documented
value over the measured one would be exactly the substitution these documents
exist to prevent. Running the probe against both is the way to change it.

```deepreason-model-profile-v1
schema: deepreason-model-profile.v1
model_id: gpt-oss:120b
measured_on: 2026-08-31
reasoning:
  documented_values: [low, medium, high]
  extraction_value: none
  thinking_disablable: false
  disabling_values: []
  trace_destination:
    none: side_channel
evidence:
  - "5/5 clean content, 5/5 populated reasoning field, 89 median completion tokens at none: git show origin/claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md (blob 00b7914fc66a0bec96e838c3317974e9d2eb9646), section 3"
  - "cannot fully disable its reasoning trace, and takes low|medium|high rather than a boolean: Ollama documentation, quoted in the same section"
probe: "python scripts/model_profile_probe.py --document 'docs/model-profiles/gpt-oss:120b/agent.md'"
```
