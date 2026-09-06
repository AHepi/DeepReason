# Delivered: T7 — the measure (S12), and the programme
Sub-tranche T7 of the mini isolation programme, the last, run 2026-09-06 on
the operator's "go for it jack!" (REQUEST.md Amendment 3).
Branch: `claude/mini-isolation-t3-t5-7tsc6d` (pushed, tree clean; head in
the step-57 commit). Validation: `T7/VALIDATION.md`, PASS.

## What the measure found

**Mini's isolation flow did not beat one plain call, and the measure could
not say by how much.** Three single calls to the same model on the same
question scored a perfect 15 of 15 from every judge; the eight conjectures
mini generated in three cycles scored 5.6 on average and 10 at best, and mini
spent 7.6 times the tokens. The pre-registered verdict is INDISTINGUISHABLE,
because the rule's length control had nothing to stand on: essays of seven
and a half thousand characters against conjectures of five hundred, no
overlap, so "held constant" was an extrapolation. RESULTS.md records that
as a null result under the operator's success law — better NOT shown,
worse NOT shown either — and says why the measure, not the harness, is
what failed to discriminate: it scored one conjecture against one whole
answer on a rubric for whole answers, and the single call maxed that rubric.
One exploratory pass (labelled as such) scored mini's eight conjectures
composed into one text at 8 of 15.

**What the record shows the harness doing.** Every one of 19 calls landed
first time. The critic saw the conjecture and nothing else; 24 objections and
14 proposals were written about named conjectures and overturned nothing,
as ruled. Under the compact profile, "everything so far" was the newest
four entries — the retention rule withheld the rest and said so in the
brief every time — and ten briefs were still clipped by the call layer,
each written to the record with both sizes. The conjecturer returned four
candidates in cycle 1 and two in each later cycle.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1–R14, R-stored | the programme's requirements | done / honoured as T5 and T6 record | T5/DELIVERY.md; T6/VALIDATION.md |
| R-again, R-history | episodes; one more history experiment | deferred, operator's own ordering | window: "later"; operator: "But before that:" |
| R15 (Amdt 2) | "Do T6" | done | commit `c66aad16b` |
| R16 (Amdt 3) | "go for it jack!" | **done** — T7 steps 52–57 in this window | commits `f1b47d270` … the step-57 commit; RESULTS.md |
| C6 (success law) | "materially better than … without it" | **NOT demonstrated** for `mini.flow.isolation.v1` on the compact profile; recorded as null, not as failure of the harness | RESULTS.md §4, §8 |

## Assumptions the operator may override

- **The measure's unit was one conjecture.** PREREG §3 chose it because the
  copied rubric was written for answers to this question and a conjecture
  is an answer attempt; the panel's own lines say a 550-character conjecture
  cannot carry "both cases" or "the cost". P11 prices the alternatives.
- **Three cycles and the compact profile** were the launch shape, matching
  T6's offline run. Under it the everything-so-far section withheld most of
  the run. A larger profile is a configuration change, not a code change.
- **ARM M ran through the reasoning-field override.** Mini's transport never
  sends the profile's `reasoning` setting (P10, a defect for its own
  tranche); the override adds that one field and nothing else.

## Budget

T7 owes no code diff. The programme's reach into `src/` at delivery: one
file, 29 lines. Programme totals by the gate's count are in SPEC.md §Budget
and P7.

## Map delta

No map change: T7 changed no behaviour and no document. left stale: 22
documents, none of them this programme's (T6's count; nothing moved since).

## Errata

errata: none. No committed document was found to state something false.
CLAUDE.md's header names glm-5.2 as the current provider model while every
live launch since 2026-09-03, including this one, uses qwen3.5:397b; that is
a stale word, not a false claim, and PREREG §0 states the choice.

## Parked (not done, not promised)

Two new entries, both with ready-to-send prompts:

- **P10** — mini's transport drops the profile's `reasoning` setting. A
  defect for the defect workflow.
- **P11** — the next measure: a judged unit the rubric fits, a budget under
  which "everything so far" is everything, a rubric with headroom, and
  length overlap by construction.

P1–P7, P9 unchanged; P8 disposed at T5.

**recommended next: P11 (the measure that can answer C6), or the operator's
own "then testing on the full harness".** The programme's machinery is
delivered and proven offline and live; whether its content is worth anything
is the question it was built to make askable, and this measure shows what a
first attempt at asking it gets wrong.
