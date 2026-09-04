# PREREG — STEP 1: hold the form, vary the brief

Tranche: `experiments/2026-09-03-change-conjecturer-pluggable-interface/`
Written: 2026-09-04, BEFORE any call on any arm.
Authority: `REQUEST.md` R9, R19; `SPEC.md` S12.0-S12.6.
Shape follows `experiments/2026-08-28-diversity-generation/PREREG.md`.

**THIS DOCUMENT IS AN INSTRUMENT, NOT A RESULT.** No arm has run. The live
experiment is its OWN tranche (`CHECKLIST.md` step 51): a multi-step programme
runs one step per tranche, and finishing this one early is not a reason to
start the next.

---

## §1 The sequence, and why this step is first

The operator's own ordering (`R19`, verbatim): *"after perfecting history
injections, change the artifact, then measure how it's behaviour changes with
respect to the epistemology."* History first, then the artifact, then measure.

STEP 1 (this document) holds the FORM constant and varies the BRIEF.
STEP 2 holds the winning brief and varies the FORM. Step 2 does not begin
until step 1's measurement is committed.

The order is also forced rather than chosen: you cannot hold a brief constant
while varying a form until the brief is a thing you can hold constant. That is
what this tranche built.

## §2 What success is

Not correctness, and not a finished answer. The operator's standing law
(2026-09-03): success is output MATERIALLY BETTER than what the same model
produces WITHOUT the harness on the same question, measured blind, against
criteria written before any output is read.

So every arm carries a NO-HARNESS BASELINE arm: the same model, the same
question, one call, no cycles. An arm that beats no baseline has not
succeeded, however finished it looks.

## §3 The arms

One parameter varies per arm; everything else is byte-identical, which the
tranche's goldens are what make possible.

| arm | what changes | selected by |
|---|---|---|
| `A0` | nothing — the shipped default | (no variable set) |
| `A1` | `dr.history.v1.include_refuted=true`, `refuted_n=3` | a registered layout |
| `A2` | `dr.active-properties.claim_chars=800` (from 200) | a registered layout |
| `A3` | the neighbourhood rendered by an operator `.tmpl` — same content, different format | a `.tmpl` in the plugin directory |
| `B0` | NO HARNESS: one call, same question, same model | — |

`A1` is the operator's own first interest ("History should be in evidence").
`A3` is the one that answers R9 directly: same information, different shape.

## §4 Frozen before any call

- The question set and its digests, committed to this directory before launch.
- The launch configuration, and a GREEN `python -u scripts/cycle_soak.py`
  on it (`CLAUDE.md`, Live runs — no live launch without one).
- The layout ids and the template file, committed.
- The budget per arm, and the stop rule: an arm that dies at cycle 0 is read
  from its diagnostic blob BEFORE anything is theorised about it.

## §5 What would falsify the premise

R14 says the input interface materially changes outputs. If A0, A1, A2 and A3
are indistinguishable on every measure in §6, that premise is not supported on
this record and the finding is recorded as negative. A negative result here is
a result: it would mean the brief's SHAPE matters less than the census
suggested, and the tranche's own instruments would be what showed it.

## §6 — Outcome measures (frozen before any call)

| measure | instrument | committed where |
|---|---|---|
| admission rate, per contract and per endpoint | `census_conjecturer_failures.py` re-run over the new roots | this directory |
| M1 — distinct-idea count per cell | `experiments/2026-08-28-diversity-generation/analyse.py` | that tranche |
| M2 — mean pairwise embedding distance | same | that tranche |
| M3 — yield per cell | same | that tranche |
| criticism outcomes | the run's own typed record: warrants, attack edges, status labels | each root |

No measure is invented here. `analyse_form_arms.py` in this directory CALLS
the committed diversity instrument rather than reimplementing it.

## §7 Two binding rules

**Blinding is STRUCTURAL, not prompt-level.** Any judged comparison renders
with provenance fields OMITTED ENTIRELY — not blanked.
`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` measured that a present-but-blank
slot draws more attention than a filled one. `layout_id`, `form_id` and
`shell_id` are provenance for this purpose.

**No self-reported number enters any metric, rank, filter or ordering.**
Typicality estimates are content, not measurement. Carried from the diversity
tranche's own PREREG.

Both are CHECKS rather than prose: `tests/test_form_experiment_binding.py`.

## §8 Status

**NOT RUN.** Nothing in this document has been executed. It is committed as an
instrument so that the later tranche cannot choose its measures after seeing
its outputs.
