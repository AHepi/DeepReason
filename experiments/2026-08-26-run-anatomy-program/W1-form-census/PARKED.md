# PARKED — findings W1 measured and did not fix

W1 is a measurement tranche. Nothing below was touched. Each entry is one
line of WHAT, then a ready-to-send prompt: starting the follow-up should cost
the operator a paste, not an authoring session.

Ordered by measured cost, largest first.

---

## P1 — the composite conjecturer form loses a third of its calls

**WHAT.** `conjecturer.turn.v6` arrives valid 66.3% of the time (816
attempts). Its atomic decomposition `conjecturer.atomic-candidate.v1` — same
role, same seat, same route, one candidate per call — arrives valid 94.9%
(373 attempts), and does so on the HARDER cases, since it only runs after the
composite form already failed. Decomposition is currently a LAST RESORT
reached by exhausting a repair grant; the census says it is the better first
ask.

```
Route through dr-change-orchestrator.

REQUEST: The conjecturer's composite turn contract is the single largest
source of invalid provider output in the committed record, and the harness
already owns a better-performing alternative that it only reaches after
paying for failure.

Evidence, all in experiments/2026-08-26-run-anatomy-program/W1-form-census/:
- Held to glm-5.2 alone (75% of the corpus), so model is controlled:
  conjecturer.turn.v6 659 attempts / 61.9% valid, against
  conjecturer.atomic-candidate.v1 339 attempts / 96.8% valid. Same role,
  same seat instance, same route_sha256.
- The atomic contract runs only on work the composite one already failed, so
  96.8% is measured on a harder sample, not an easier one.
- COUNTEREXAMPLE, do not omit it from the spec: deepseek-v4-flash:0731 goes
  the OTHER way (84.6% composite on 52 attempts, 63.6% atomic on 22). Small
  samples, but the effect is not established as universal, so the change
  should be a per-route-seat policy rather than a global default.
- CENSUS_AGGREGATE.json "repair_fights": conjecturer.turn.v6 opens 134 repair
  ladders consuming 459 provider calls, and hits its grant ceiling 52 times.

SPEC the change as: when (and whether) the controller should decompose a
conjecturer turn BEFORE exhausting the repair grant rather than after.
Consider a per-route-seat policy flag rather than a global default -- the
all-configurations law forbids denying any configuration, so this must be a
policy the manifest carries, never a refusal.

Do NOT touch route_seat_contract_decomposition_plan's schema without checking
docs/map/INV-frozen-surfaces.md first; manifest schemas are frozen.

Measure the outcome against the same census: re-run
W1-form-census/census.py over the new root and compare by_contract validity.
```

---

## P2 — seats invent handles for fields the record has just told them to omit

**WHAT.** 257 diagnostics carry `omission_or_unknown_legal: true` and an
instruction saying in plain words "never invent a handle to fill an optional
reference". In 255 of them the seat invented one anyway (CFR 99.2%). Escape
utilization on the next attempt is 7 of 120 (EUR 5.8%). Where an escape value
exists in the ENUM instead of only in the instruction text — `claim_class:
unknown` — models take it 16 times in 140.

```
Route through dr-change-orchestrator.

REQUEST: Reference fields in our contracts have no escape value, only an
instruction saying omission is legal. Measured over the whole committed
record, that instruction is ignored 255 times out of 257.

Evidence, all in experiments/2026-08-26-run-anatomy-program/W1-form-census/:
- COERCION_PROBE.json "coerced_fabrication": escape_legal 257,
  fabricated_handle 255, coerced_fabrication_rate 0.9922.
- COERCION_PROBE.json "escape_utilization_next_attempt": escape_taken_remove
  7, repaired_without_remove 78, still_invalid 35.
- COERCION_PROBE.json "enum_escape_audit": bridge.ledger.v3 claim_class
  offers `unknown` and it is used 6/85; bridge.ledger-batch.v1 10/55.
- EXEMPLARS.md quotes one such diagnostic and the response beside it.
- Prior art, cited not assumed:
  docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md recommendation 2
  ("Add insufficient_evidence to every enum, and then measure whether your
  seats take it"). This tranche is that measurement; the change is the
  recommendation.

SPEC the change as: give optional reference fields a first-class absent
value in the TYPE rather than in the prompt, and keep measuring CFR/EUR after
it ships. The comparison is already built: re-run coercion_probe.py.

Note the operator design law: formalism is an option, never an obligation.
An escape value may not become a penalty, a rank input, or an admission
condition -- it is a legible state, nothing more.
```

---

## P3 — the truncation flag is inert while the record reports truncation 52 times

**WHAT.** `attempt_trace[].truncated` is `false` on all 3 155 committed
attempts. The record's own diagnostics say "your output hit the length limit
and was CUT OFF mid-JSON" 52 times, and 11 attempts record
`natural_stop: false`. Truncation is being detected after the fact by
noticing the JSON does not close; the field that exists to report it never
fires.

```
Route through deepreason-orchestrator.

GOAL: Find out why attempt_trace[].truncated is false on every one of 3 155
committed provider attempts while the record's own diagnostics report a
length-limit cut-off 52 times.

Evidence, all in experiments/2026-08-26-run-anatomy-program/W1-form-census/:
- CENSUS_AGGREGATE.json: truncated_attempts 0, failure_classes
  TRUNCATED_MID_JSON 52, unnatural_stop_attempts 11.
- EXEMPLARS.md quotes one TRUNCATED_MID_JSON diagnostic with the attempt's
  tokens and max_tokens beside it.
- census/*.json rows carry truncated, natural_stop, tokens, max_tokens per
  attempt, so the population is already isolated.

Diagnose from the record BEFORE reading code (CLAUDE.md). The question to
settle first is whether `truncated` is meant to carry the provider's
finish_reason and is not being populated, or whether it means something
narrower and the 52 cases are legitimately outside it. Either answer is a
result; only the first is a defect.

Do not widen this into a completion-cap change. docs/ERRATA.md E42 records
that raising the cap was already the wrong remedy once.
```

---

## P4 — three named spellings still cost a repair grant after the lossless fix

**WHAT.** The 2026-08-22 lossless-spelling fix cut the class 94% (79
attempts before, 5 after). The five survivors fall into three shapes its
closed key set does not cover: an underscored container name
(`repair_patch_v1`), an echo field whose VALUE differs from what the harness
sent (`"contract": "repair.patch.v1"`, ×3), and a container that is present
but not alone in its dict (`{patch, version}`).

```
Route through dr-change-orchestrator.

REQUEST: The lossless patch-transport fix works -- the class is down 94% --
but three response shapes still cost a repair grant for a readable answer.

Evidence, all in experiments/2026-08-26-run-anatomy-program/W1-form-census/:
- CENSUS_AGGREGATE.json "lossless_spelling": before_fix_total 79,
  after_fix_total 5, cut at the fix COMMIT timestamp
  (97a964583, 2026-08-22T16:09:24Z), not at the day.
- EXEMPLARS.md quotes all five survivors whole.
- The prior tranche and its principle: experiments/2026-08-22-fix-repair-
  patch-transport/FIX.md -- "An echo is not information. The harness may
  discard from a patch response exactly those bytes it supplied itself ...
  It may not supply a value the model did not give."

SPEC the change against that principle, not around it. Two of the three
shapes are plainly within it (a container name is a container name whether or
not it is spelled with a dot; a container in a two-key dict is still a
container). The third is NOT: "contract": "repair.patch.v1" is a value the
harness did not send, and dropping it would be supplying a judgement about
intent. Recommend refusing that one and saying so.

Every added key must appear in a committed response, as the prior tranche
required: no name added speculatively.
```

---

## P5 — 15 attacks with no case, and a judge form with no third verdict

**WHAT.** `batch-critic.v2` lets `case` default to `""`, and 15 of 1 453
asserted attacks carry no case text at all. `JudgeRuling` declares
`verdict: [fail, pass]` with no abstention, and across 342 rulings none was
attempted.

```
Route through dr-change-orchestrator, but read the judge-audit evidence in
the committed record FIRST (CLAUDE.md: judge seats are suspect-by-default and
any design leaning on them must consult that evidence rather than assume
judges discriminate).

REQUEST: Two criticism-side forms record an outcome the seat may not have
been able to justify.

Evidence, all in experiments/2026-08-26-run-anatomy-program/W1-form-census/:
- COERCION_PROBE.json "forced_boolean_vs_sibling_prose": 1453 asserted
  attacks, attack_true_case_empty 15, attack_true_case_argued 1437.
- COERCION_PROBE.json "judge_form_filling": 342 rulings, fail 194, pass 148,
  declined_rate 0.0, and JudgeRuling declares enum [fail, pass].
- EXEMPLARS.md quotes one empty-case attack whole.

SPEC carefully and separately -- these are two different problems:
(a) an attack with an empty case is arguably already a defect in the
    contract's default, and is cheap to require;
(b) a third judge verdict is a DESIGN question the operator has standing
    views on, and touches adjudication. Do not bundle them.

Neither may be specced in a way that weights an outcome on conjecture KIND
(the formalism law) or lets a seat's prose skip criticism (the seats/evidence
guardrail).
```

---

## P6 — 46% of accepted responses ignore the declared output mode

**WHAT.** 1 254 of 2 743 valid arrivals are wrapped in a markdown ```json
fence, on seats configured `output_mode: json_object`. The harness tolerates
it, so it costs nothing today.

```
Route through dr-audit-orchestrator (or park indefinitely -- this is a
latent risk, not a live cost).

FINDING: 45.7% of currently-accepted provider responses are fenced markdown,
not the bare JSON their route's output_mode declares
(CENSUS_AGGREGATE.json "content"/"wire_shapes": bare_json 1484,
fenced_json 1254, prose_wrapped 5).

The audit question is narrow: is the fence tolerance a deliberate, documented
property of the wire reader, or an accident that a future stricter reader
would remove -- taking 46% of good traffic with it? If deliberate, it belongs
in docs/map/SUB-llm.md with a check. If accidental, it is a tripwire nobody
has armed.

Read-only. Do not change the reader.
```

---

## Not parked, deliberately

- **The P-C1 collinearity result is not a defect.** 126 of 133 constructions
  placing three points on a line is a fact about what the models produced on
  a hard instance, not a fault in the harness. It belongs to whatever
  successor asks how to make the conjecturer search rather than name; it is
  not a fix.
- **`conjecturer.turn.v6`'s scratch-reference failures (230 + 70 + 25)** are
  left to D1, the scratchpad dimension, which owns the scratch lifecycle.
  Counting them here without knowing what the scratch turn was trying to do
  would be the same mistake E42 records: a number joined to the wrong story.
