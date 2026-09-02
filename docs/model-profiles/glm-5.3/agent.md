# glm-5.3

The model this whole mechanism was built for. Three runs died because the
harness sent it `reasoning_effort: "none"` — a value that, on this model, does
not stop the thinking. It stops the SEPARATION.

**If you read one line here:** set this seat's `reasoning` to `low`, not
`none`, and not unset.

## What `none` actually does here, measured

P-S1 ran 8 trials per setting on `/v1/chat/completions`:

| `reasoning_effort` | clean content | separate `reasoning` field | median completion tokens |
|---|---|---|---|
| `none` | **0/8** | 0/8 | 64 |
| `low` | **8/8** | 3/8 | **7** |
| omitted | 8/8 | 8/8 | 61 |

`none` is the worst setting on both axes at once: it is the only one that
contaminates the answer, AND it is nine times dearer than `low` on a prompt
whose bare answer is about six tokens. The trace does not disappear under
`none`; it moves into `message.content` ahead of the answer.

Confirmed on the native surface too, so this is not an artifact of choosing the
OpenAI-compatible one: `POST /api/chat` with `"think": false` produces reasoning
prose then the answer, while `"think": true` produces a clean `{"ok":true}` with
the thinking in its own field.

## Two documents about "accepted values", and both are right

Ollama's **API** page lists `reasoning_effort` as taking
`"high" | "medium" | "low" | "max" | "none"`. Ollama's **glm-5.3 model** page
lists `low`, `high`, `max`, defaulting to `max`. The wire accepts `none` — the
provider does not reject it — and the model behaves badly with it.

That is why `documented_values` and `trace_destination` are separate fields
below. Collapsing "what the wire takes" into "what the model does with it" is
precisely the mistake that produced the hard-coded constant this document
replaces.

## What killed the runs

Two different envelopes, one cause, recorded in P-S1's `MISTAKES.md`:

- **M-1, cycle 0.** The split protocol handed the emission leg 512 tokens with
  `reasoning: none`. The leg opened with thinking prose, was cut before any
  JSON, and the seat died `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`.
- **M-16, cycle 11.** The allocation controller's cap ratchet stepped the
  completion budget down at 1/1.6 — 32768 → 20480 → 12800 → 8000 → 5000 → 3125
  → 1953 — telling the model to "respond MORE COMPACTLY" at each step. This
  model cannot do that. A model that cannot shorten its output meeting a
  monotonically shrinking budget makes truncation more likely at every retry,
  not less.

P-A1 then re-ran M-1's mechanism verbatim in run `4565139800f5ca02`: every
glm-5.3 emission-leg blob opens with thinking prose, cut at 512 tokens.

## Still open, and not answered here

The `~300 s` transport wall at `max` effort is real and is not fixed by this
document — it is described below and parked as its own tranche. `low` keeps
these calls far inside it, which is a mitigation and not a fix.

`context_window_tokens`, `max_output_tokens` and `tokens_per_second` are LEFT
OUT deliberately. The record measures what the P-A1 run's configuration
declared, not what the model actually offers, and a profile that quotes a
config back as a model fact is the same error in a new place.

```deepreason-model-profile-v1
schema: deepreason-model-profile.v1
model_id: glm-5.3
measured_on: 2026-08-31
reasoning:
  documented_values: [low, high, max]
  extraction_value: low
  thinking_disablable: false
  disabling_values: []
  trace_destination:
    none: content
    low: side_channel
    high: side_channel
    max: side_channel
can_compact: false
transport_notes:
  - "reasoning defaults to max when the knob is omitted; at max effort P-A1 saw calls dropped at roughly 300 seconds, and blind identical retries then spent the same 300 seconds again"
  - "at low, 3 of 8 trials returned no separate reasoning field at all; the content was clean in all 8, so an absent trace is not a failure here"
evidence:
  - "0/8 clean at none, 8/8 clean at low, 8 trials each: git show origin/claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/SEAT_REASONING_FINDINGS.md (blob 00b7914fc66a0bec96e838c3317974e9d2eb9646), section 2"
  - "can_compact false, and the 32768->1953 cap ratchet at 1/1.6 that exploits it: same branch, experiments/2026-08-31-p-s1-commitments/MISTAKES.md (blob 095233a1db5a59d990b8ae2fbf3e01edf637bef3), M-1 and M-16"
  - "the same failure re-run live, with seq numbers: experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md at commit e9eb97e775342cba05793543d8436a9168c90a91, addendum of 2026-09-01, run 4565139800f5ca02"
probe: "python scripts/model_profile_probe.py --document docs/model-profiles/glm-5.3/agent.md"
```
