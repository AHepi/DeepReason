# Validation for: Rung 5 — promotion problems and their criteria as programs

Verdict: **PENDING** until the full gate and the full `docs_verify` lines below
are pasted. Every other section is complete and its output is real.

## Acceptance checks (SPEC.md item order, every one re-run in this phase)

**S1 (R1, R2) — nomination as a measure-rule.**

    $ python -m pytest tests/test_calculus_nomination.py -q
    15 passed in 1.65s

    $ python -c "<the no-decide source assertion, SPEC.md S1>"
    exit 0 - the measure cannot decide

PASS. The structural half asserts no adjudication/warrant/LLM/trial import and
no assignment into `state.status`/`state.hv`/`state.reach`; the behavioural half
is `test_nomination_changes_no_label_and_no_measure`, which asserts every
pre-existing label byte-identical across a FIRING nomination.

**S2 (R3) — `K_FRAME` on `Config`, with its versioned-source line.**

    $ python -c "<engine_config_json leak check, SPEC.md S2>"
    exit 0 - no knob reaches engine_config_json

PASS. Measured, not argued: with the two `data.pop` lines neither `K_FRAME` nor
`PROMOTION_ENVIRONMENT_MAX` reaches `engine_config_json`, so no qualification
subject digest moves. This is the `ENGAGED_CRITICISM_AUTHORITY` trap R3 named.

**S3 (R1) — the coherent candidate scope and the reach certificate.**

    $ python -c "<decode a poietic.reach-certificate.v1 body, SPEC.md S3>"
    exit 0 - the declared name has a producer

PASS. `poietic.reach-certificate.v1` was in the CLOSED schema set with no
producer and was refused by `decode`; it now has one. The other four declared
names are still refused with `claim-schema-not-implemented`, which a map check
now pins.

**S4 (R4, R8) — subject-demarcation, including §12.2's closing clause.**

    $ python -m pytest tests/test_promotion_criteria.py -q -k demarcation
    2 passed, 14 deselected in 0.17s

PASS. The empirical clause's own test does not carry "demarcation" in its name
and is counted in the file total below; `python -m pytest
tests/test_promotion_criteria.py -q` → `16 passed`.

**S5 (R4) — reach-integrity against the log's own timestamps.**

    $ python -m pytest tests/test_promotion_criteria.py -q -k integrity
    4 passed, 12 deselected in 0.31s

PASS.

**S6 (R4) — scope-determinism.**

    $ python -m pytest tests/test_promotion_criteria.py -q -k determinism
    2 passed, 14 deselected in 0.18s

PASS.

**S7 (R4) — compatibility; rivals never co-frame.**

    $ python -m pytest tests/test_promotion_criteria.py -q -k compatibility
    1 passed, 15 deselected in 0.13s

PASS.

**S8 (R5, R6, R10) — accounts-for, the STRONG relation.**

    $ python -m pytest tests/test_promotion_succession.py -q
    11 passed in 0.06s

PASS, and the four refusals R10 names are present by name:
`test_a_rival_that_only_recovers_is_not_a_successor`,
`test_a_rival_that_loses_an_explicandum_is_refused_on_recovery`,
`test_an_easier_to_vary_rival_is_refused_on_rigidity`,
`test_a_rival_with_an_excisable_idle_part_is_refused_on_non_immunization`.

**S9 (R7, R12) — Remark 9.5's default-consult closure.**

    $ python -m pytest tests/test_promotion_closure.py -q
    6 passed in 0.41s

PASS.

**S10 (R9) — the knowledge view.**

    $ python -c "<KNOWLEDGE_LABEL assertion, SPEC.md S10>"
    exit 0

PASS. `KNOWLEDGE_LABEL == "knowledge (unrefuted ∧ active ∧ reach > 0)"`, and
three tests in `tests/test_calculus_standing.py` pin that the CLI never emits a
line containing "knowledge" without the definition on it.

**S11 (R11, R15) — M-4 both halves, the live root the negative one.**

    $ python -m pytest tests/test_promotion_nomination_live.py -q
    5 passed in 7.15s

PASS. Positive half in `tests/test_calculus_nomination.py`
(`..._fires_at_the_K_frame_threshold`, `..._does_not_fire_one_lineage_short`).

**S12 (R13) — Prop 12.1, every criterion inside its declared budget.**

    $ python -m pytest tests/test_promotion_criteria.py -q -k budget
    1 passed, 15 deselected in 0.12s

PASS. That test drives all five criteria to `overrun` on a zero-step budget and
asserts `reason == "budget-exhausted"` for each.

**S13 (R14) — L-3, the whole path on a solo configuration.**

    $ python -m pytest tests/test_promotion_solo.py -q
    4 passed in 0.18s

PASS.

**S14 (R16) — the axiom ledger.** See Map, below.

**S15 (C3) — the map moves in the same commits.** See Map, below.

## Mutation proofs (both required by SPEC.md; both pasted in CHECKLIST.md)

**S11's live negative half.** With `problem_parents` truncated to stop at
artifact sources, THREE tests go red and the third is the proof:

    FAILED ...::test_nomination_does_not_fire_on_the_committed_live_root
    E   deepreason.harness.ReadOnlyHarnessError: time-travel harness is read-only

Under the truncated walk the committed live root spans TWO lineages and
nomination TRIES TO FIRE; only the read-only open stopped it writing a promotion
problem into the evidence. Restored: `20 passed`, `git diff --stat src/` empty.

**S8's first refusal.** With the strictness-witness clause replaced by an
unconditional pass — the WEAK reading R6 forbids building — EXACTLY ONE test
goes red:

    FAILED ...::test_a_rival_that_only_recovers_is_not_a_successor
    1 failed, 10 passed in 0.07s

That is the test R10 names. The other ten staying green is the second half of
the proof: the strictness witness does this one job and is not propping up the
other three clauses. Restored: `33 passed`, no residue.

## Record-behavior preservation

    experiments/2026-08-22-change-epoch3-second-lineage/run  -> 0 violations
    experiments/live_engaged_2026-07-27/run-f4fa6663...       -> 6 violations
                                                                (all foreign-criticism)

The six on the second root are PRE-EXISTING and are not this tranche's. The
proof offered is stronger than a re-run and cheaper: every reader that could
move a verdict has a ZERO-LINE diff.

    $ git diff --stat ade214037..HEAD -- src/deepreason/invariants.py \
        src/deepreason/verification/ src/deepreason/adjudication/ \
        src/deepreason/harness.py
    (empty)

A first attempt at this used `git stash` to re-run at the base; the tree was
already clean so the stash was a no-op and the "AT BASE" figure was the CURRENT
tree's. Recorded rather than quietly replaced — the number was right and the
method was not, and the diff above is what actually establishes it.

## Frozen-surface diff

    $ git diff --stat ade214037..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
     src/deepreason/run_manifest.py | 12 ++++++++++++
     1 file changed, 12 insertions(+)

NON-EMPTY, and the operator's words authorizing this exact surface are quoted in
REQUEST.md R3 and C1: "K_frame ships as a Config knob with its
_versioned_source_config_data line for EVERY schema version" / "new knobs on
Config only, each with its versioned-source line". The twelve lines are ten of
comment and two `data.pop` calls; no schema and no validator changed. Surfaces
1, 2, 3 and 5: empty.

`tools/blast_radius.py`'s computed verdict at spec time, pasted in SPEC.md
verbatim, forecast exactly this and nothing else:

    "frozen_surface_contacts": [{"surface": "manifest schemas and validators (run_manifest.py)", "tier": "DIRECT", ...}]
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CONTACT"

## Packaging surface

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas
    [exit 0]

    $ python -u scripts/wheel_operational_smoke.py
    wheel operational smoke passed: installed setup, explicit qualification (80
    qualification calls; 418 total calls), readiness, question-only reasoning,
    replay-verified terminal retrieval, cache reuse, opaque MCP restart, budget
    ceiling, and pre-V6 fail-closed admission
    [exit 0]

Both run although neither was owed — the ladder requires them only at rungs that
change the public surface, and C1 says this one does not. They are the proof of
that claim rather than a formality: the knowledge view ships as a section of the
EXISTING `standing` command's text output, `standing_view`'s dict is unchanged
so the `run_standing` MCP tool renders exactly what it rendered before, and no
entry point, tool name or schema hash moved.

## Map

(filled below with the full-mode run)

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 nomination as a measure-rule | S1, S3, S11 |
| R2 detects, never decides | S1 both halves; axiom A8's two checks |
| R3 `K_FRAME` on Config + versioned-source line | S2, and the frozen-surface diff |
| R4 five criteria as programs | S4, S5, S6, S7, S8 |
| R5 the STRONG relation, four parts | S8, and `_succeeds_one`'s four reasons |
| R6 the weak form is FORBIDDEN | S8's mutation proof — dropping strictness reds exactly the rival-that-only-recovers test |
| R7 Remark 9.5's closure | S9 |
| R8 §12.2's closing empirical clause | S4 (`test_an_empirical_scope_needs_an_observation_valued_commitment`), plus the `declared-only` abstention |
| R9 the knowledge view, definition inline | S10 |
| R10 four refusals + mutation proof | S8 |
| R11 M-4 both halves, live root negative | S11 |
| R12 Remark 9.5 both ways | S9 |
| R13 Prop 12.1 budgets | S12 |
| R14 L-3 solo | S13 |
| R15 L-6 measured on the committed root | S11 |
| R16 A8 proved; A4 and Genesis Inertness preserved | Map, `INV-axiom-basis.md` |
| R17 R-by-R delivery with pasted proof | DELIVERY.md |

No R is deferred and none is unproven.

## Assumptions carried to delivery (SPEC.md A1–A10)

A1 problem lineage (settled by measurement against the live root, not by
choice) · A2 the candidate scope is an enumeration nomination derives · A3 the
criteria read a frozen certificate through the existing `BLOB_PROGRAMS`
widening, never live graph state · **A4 a DEVIATION from Rider 5 clause (4):
one certificate rather than four artifacts, no capture window** · A5 the frozen
candidate pool bounds what is checkable; a later subject answers `overrun` ·
A6 `X(e)` reuses `reach_sweep`'s all-qualifying-pass test · A7 the knowledge
view is not a new public surface · A8 warrants fire through
`register_fail_warrant` · A9 a row-number mismatch in R8's citation, reported
not resolved · A10 the six programs are `structural` and dual-registered.

## Constraint compliance

C1 frozen surfaces — surface 4 contacted under the operator's own grant,
measured harmless; 1, 2, 3, 5 untouched; no new LLM role; public surface
unchanged, both smokes green. **C2 SIZE — EXCEEDED**: 4 503 insertions against
a ledgered 1 900, 1 442 in `src/` against a 686-line plan; itemized in
REQUEST.md Amendment 1. C3 gate discipline — ring while iterating, full gate and
full `docs_verify` at the boundary, map in the same commits, pushed at every
phase boundary. C4 routed through `dr-change-orchestrator` throughout. C5 no
treadle path was touched. C6 the cycle soak was not run and is not owed — this
rung launches nothing.
