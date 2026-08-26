# PARKED — found during F2, deliberately not done here

Append-only. Each entry: one line of WHAT, then a ready-to-send prompt so
the follow-up costs the operator a paste, not an authoring session.

---

## P1 — The judge form has no way to say "I don't know"

**What.** W1 §4: `JudgeRuling` declares `verdict` as `enum: [fail, pass]`
and `decisive_point` with `min_length: 1`. 342 rulings, 194 fail, 148 pass,
**zero abstentions, because there is no value for one**, and not one
`decisive_point` contains a phrase in which the judge declines. The same
shape sits on `batch-critic.v2`: a required boolean `attack` with no third
value, and `case` defaulting to the empty string — 15 of 1 453 asserted
attacks carry no case text at all. F2 could not touch this: R8 forbids wire
schema shape changes, and an abstention value IS a schema change.

**Why it is not F2's.** R8, verbatim: "SCOPE: prompt rendering + validation
sourcing only. NO wire schema shape changes."

```
Change tranche: give the judge and critic forms an abstention outcome.
Route through dr-change-orchestrator.

AUTHORITY: W1's form census, experiments/2026-08-26-run-anatomy-program/
W1-form-census/RESULTS.md §4 — JudgeRuling declares verdict as
enum: [fail, pass] with decisive_point min_length: 1, and across 342
committed rulings there are ZERO abstentions because the form has no
value for one. The same shape on batch-critic.v2: a required boolean
`attack` with no third value, and 15 of 1 453 asserted attacks carry no
case text at all — a form that records an attack nobody argued.

The contrast that prices the fix, from the same census §3: claim_class on
the bridge ledger contracts offers `unknown` IN THE ENUM and models take
it (6 of 85 on bridge.ledger.v3, 10 of 55 on bridge.ledger-batch.v1).
Where the escape lives in the vocabulary it gets taken; where it lives
only in instruction text it does not (EUR 5.8%).

External context: docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md
recommendations 2 and 3 — add an escape value to every enum, and adopt
structured refusal as a first-class outcome.

THIS IS A WIRE SCHEMA CHANGE. Expect the four pins (IntakeFormV1, the MCP
tool set + schema sha, wheel layout, console entry points) to move; update
all four and re-run both wheel smokes in the same commit. Read the
operator's standing position on judges first (CLAUDE.md, operator design
laws, 2026-08-09) — judges are suspect-by-default and this tranche must
not be read as strengthening them.

Downstream: adjudication reads verdicts. An abstention must reach a typed
non-outcome, never a silent `pass`.
```

---

## P2 — Measure CFR and EUR after the menu lands

**What.** F2 ships the menu and measures nothing. W1's CFR (99.2%) and EUR
(5.8%) are the before-numbers; nobody has taken the after-numbers.

**Why it is not F2's.** R7, verbatim: "Measure nothing here; the rematch
measures it."

```
Measurement tranche: re-run W1's CFR and EUR measures against roots
written AFTER the F2 reference menu landed, and report the delta.

AUTHORITY: R7 of experiments/2026-08-26-change-f2-reference-menu/
REQUEST.md — "Measure nothing here; the rematch measures it."

The before-numbers, from experiments/2026-08-26-run-anatomy-program/
W1-form-census/RESULTS.md: CFR 99.2% (255 invented handles in 257
diagnostics that announced omission was legal); EUR 5.8% (7 of 120
ladders took the escape); 62.6% of field-attributed diagnostics are an
invented reference handle (737 of 1 178).

The instruments are already committed and re-derivable — census.py,
aggregate.py, coercion_probe.py in that directory. Do NOT rewrite them;
run them over the new roots and table the delta against the old.

Read RESULTS.md's Residue §2 before claiming a CFR movement: CFR is
measured only where the record ANNOUNCED the escape, so a menu that
prevents the rejection also removes the diagnostic the measure counts.
A drop in CFR's DENOMINATOR is the expected first-order effect and is not
by itself evidence the fabrication stopped. State which of the two moved.
```

---

## P3 — `attempt_trace[].truncated` is inert

**What.** W1 §8: the transport-level truncation flag is `false` on all
3 155 attempts, while the record's own diagnostics say the output was cut
off mid-JSON 52 times, and 11 attempts record `natural_stop: false`.
Truncation is detected semantically, after the fact, by noticing the JSON
does not close; the flag that exists to report it never fires.

**Why it is not F2's.** A defect, not a change. CLAUDE.md's cross-routing
rule: a defect found mid-change is PARKED, not fixed.

```
Defect: the transport truncation flag never fires.
Route through deepreason-orchestrator (dr-set-goal first).

SYMPTOM, from the typed record: experiments/2026-08-26-run-anatomy-program/
W1-form-census/RESULTS.md §8 — attempt_trace[].truncated is false on ALL
3 155 provider attempts across 54 committed roots, while the record's own
diagnostics report "your output hit the length limit and was CUT OFF
mid-JSON" 52 times, and 11 attempts (all glm-5.2) record
natural_stop: false.

Diagnose from the record BEFORE reading code (CLAUDE.md): the 52
diagnostics and the 11 natural_stop:false attempts are the evidence; find
where `truncated` is written and what it is written from.

The cost this defect imposes: truncation is currently detected only
semantically, after a wasted attempt, by noticing the JSON does not close.
P-C1 (run 1950b3d0ee228113) shows what that buys — 42 of its 77
diagnostics are the JSON not arriving whole, and it died of
V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY.

W1 parked this as a finding and did not diagnose it. Do not assume the
flag is simply unset; establish what writes it.
```

---

## P4 — An `insufficient_evidence` value for the reference fields themselves

**What.** F2's omission entry is index 0 of a prompt menu. The coercion
research's recommendation 2 is stronger: put the escape IN THE VOCABULARY,
because §3's `claim_class` contrast shows that is the version models take.
For a reference field, that would mean a legal sentinel handle rather than
absence.

**Why it is not F2's.** R8 forbids schema changes; deleted from SPEC.md by
the anti-invention pass. It is also the right thing to decide only AFTER
P2 measures whether the menu's omission entry was enough.

```
Design question (DESIGN-AND-STOP): should reference fields carry a legal
sentinel handle rather than relying on omission?

DO NOT RUN THIS BEFORE P2 REPORTS. Its whole point is to be decided on
the after-numbers, not before them.

AUTHORITY: docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md
recommendation 2, against experiments/2026-08-26-run-anatomy-program/
W1-form-census/RESULTS.md §3 — where an escape lives in the enum
vocabulary models take it (claim_class `unknown`: 6/85 and 10/55); where
it lives in instruction text they do not (EUR 5.8%).

F2 (experiments/2026-08-26-change-f2-reference-menu/) put the omission
form at index 0 of a prompt menu — the escape as a SELECTABLE ITEM, which
is between the two. P2's EUR is the number that says whether that was
enough. If EUR moved materially, this tranche is not needed and should be
recorded as such.

If it is needed: this is a wire schema change (all four pins, same
commit), and the sentinel must never resolve to a real reference — a
sentinel that compiles into a CandidateRef would be a fabricated citation
with the harness's own blessing.
```
