# Delivered: "Prose can refute" + cross-school criticism for single-model runs

Branch: `claude/amendment-epochs-om0ztb` (pushed, tree clean)
28 commits, `fbe0ebb0`..`366592cd`. VALIDATION.md round 2: **PASS**.

## What changed

Before this tranche, no text run in DeepReason could ever refute anything by
argument. `authority.py` computed a text-authority mode and then returned
`OBSERVE_ONLY` regardless, so a prose criticism could never mint a warrant, and
without a warrant there is no attack edge and no `REFUTED`. Measured against the
recorded corpus: 26 of 42 roots had executed criticism and produced zero
attacks, every artifact vacuously accepted.

Prose can now refute. `informal/trial.py` mints an ARGUMENTATIVE warrant from a
sustained prose case, and the offline demonstration produces `len(state.att)=1`
with the target at `REFUTED` — the first attack edge a prose case has produced
in this codebase.

The trial's precondition was a cross-family judge ensemble, which a run served
by one model can never satisfy, so the path was unreachable rather than strict.
In a single-MODEL run the trial now requires instead two frozen judge seats plus
a critic whose school differs from the target author's school — cross-school
criticism standing in for cross-family judging, and only where cross-family is
unobtainable. It is selected by route topology alone: `llm/adapter.py`'s
production factory needs no constructor argument, no `Config` value and no
manifest field, and nothing in the path reads configuration at all.

The refuting endpoint now receives the whole argument. `llm/packs.py` sends the
target's complete text instead of a head/tail excerpt, plus its declared
`Interface.refs` support chain. The scratchpad is excluded, and that exclusion
is pinned by tests rather than left to habit.

Formal claims keep formal refutation. `rules/warrants.py` gains
`formally_backed`: a target carrying a passing evaluable AND SUBSTANTIVE
commitment cannot be refuted by prose. Substantive is load-bearing — safe
skeleton compilation lets a conjecturer author `program:` commitments on its own
artifact, so mere evaluability would let a candidate attach `program:json-wf`,
which passes for anything well-formed, and immunise itself against criticism.

Files: `authority.py`, `config.py`, `informal/trial.py`, `llm/adapter.py`,
`llm/firewall.py`, `llm/packs.py`, `rules/crit.py`, `rules/warrants.py`; tests in
`test_prose_refutation_boundaries.py` (new, 44 assertions) and
`test_pack_prefix.py`.

Proof: full gate **3287 passed, 7 skipped, 0 failed** (3243 at tranche start).
Two byte-identical 42-root verdict sweeps, the second taken after the formal
line widened and the ensemble precondition changed shape — no recorded root
changes `valid`, `att`, or its epistemic checks. `capabilities/state.py`,
`harness.py`, `run_manifest.py` and `invariants.py` are UNTOUCHED.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Get rid of that requirement." | done-with-assumption (S1 amendment) | `845fec28`, VALIDATION S1 |
| R2 | "Prose can refute." | done | `d66c9c30`, VALIDATION S2 |
| R3 | "the endpoint ... needs access to the full argument" | done-with-assumption A3 | `cacd8bef`, VALIDATION S3 |
| R4 | "only formal claims in formal prose ... require formal refutation" | done (via R21) | `20d83aef`, VALIDATION round 2 S4 |
| R5 | "scratchpad authority chain ... completely separate" | done | `fbe0ebb0`, VALIDATION S5 |
| R6 | "They shouldn't exist together." | done | `fbe0ebb0`, VALIDATION S5/S12 |
| R7 | "add an experimental path for same school criticisms" | superseded by R14, confirmed by R18 | REQUEST.md contradiction section |
| R8 | "Leverage the schools architecture to create and mint criticisms." | done-with-assumption A6 | `de3c5d26`, VALIDATION S14 |
| R9 | "stateless endpoints don't have access to who created the ... artifact" | done | `610afa27`, VALIDATION S10 |
| R10 | "figure out what actually exists ... feasibility and risks" | done | FEASIBILITY.md |
| R11 | "report must be returned without technical terms" | done | FEASIBILITY.md |
| R12 | "Use subagents" | done | feasibility survey |
| R13 | "designed for single family runs" | done, narrowed by R19 | `c1cfb891`, `5c4a15b6` |
| R14 | "as long as a critic isn't from the same school, it's fine" | done | `70333abf`, `de3c5d26`, VALIDATION S9/S14 |
| R15 | "only make it active if a single model is running the entire harness" | done | `4b4e06ca`, `de3c5d26`, VALIDATION S14 |
| R16 | "The architecture to distinguish ... should already exist" | done (confirmed) | REQUEST.md, R16 confirmation |
| R17 | "Read claude.md before running." | done | amendment 4 |
| R18 | "It should be cross school criticism." | done | `de3c5d26`, VALIDATION S14 |
| R19 | "It should only work for single model runs." | done-with-assumption A8 | `5c4a15b6`, VALIDATION S13 |
| R20 | "exposed whenever a single model is occupying all positions" | done | `b3347f88`, VALIDATION S15 |
| R21 | "they are both formal." | done-with-assumption A11 | `7c17fb48`, `20d83aef`, VALIDATION S4 |
| R22 | "a conjecture endpoint might not fill out the form properly" | done | `7c17fb48`, `20d83aef`, VALIDATION S17/S19 |

Constraints: C1 (never touch run-root records or replay validation) — held,
frozen-surface audit above. C2 (gate 0 failed, no assertion weakened) — held;
one existing assertion changed anywhere in the tranche and it asserts strictly
more. C3 (no replay-valid root invalidated) — held; 0 of 42 roots moved, twice.
C4/C8 (don't ask permission unless out of scope) — held. C5/C6 (route through
the skills, re-read CLAUDE.md) — held. C7 — FEASIBILITY.md. C9 — see below.

## On C9

"you didn't listen. I didn't ask for same school criticism." The failure was
mine and it was specific: A4 recorded that the guarantee is cross-SCHOOL, the
operator settled that in message 4, and the round-1 delivery report raised it
again as an open choice. R18 states it back. **A4 is closed: the guarantee is
cross-school, it is what was built, and it is not a question.** REQUEST.md
records the rule this produced — a confirmed assumption is reported as a fact,
never re-surfaced as a decision.

## Assumptions the operator may override

- **A3**: "the full argument" = the target's complete text plus its declared
  `Interface.refs` support chain, and explicitly not the scratchpad.
- **A6**: "mint criticisms" = make the existing warrant path completable, not a
  new warrant kind. No new record type.
- **A8**: "a single model is occupying all positions" = one `(provider,
  model_id)` across every leased seat of every role. Narrower than family.
- **A9**: the substitute guarantee is cross-school CRITICISM, not a cross-school
  judge ensemble. **Load-bearing.** Grounds: the operator's word is "criticism"
  in all three statements; the guarantee is already stamped on the artifact a
  warrant hangs from; and `run_manifest.py:2751` rejects any criticism binding
  whose role is not `argumentative_critic`, so a judge cannot carry a school
  through the manifest at all.
- **A10**: `require_cross_school_judge_ensemble` and `school_judge_bindings` are
  retained though superseded — correct for a manifest that authors judge
  bindings, which the validator does not currently permit.
- **A11**: "they are both formal" = evaluable AND substantive. Inverts if
  structural well-formedness programs should also immunise.
- **S1 amendment**: `trial_authority_for` reads its knob for every surface but
  `calibrated_status` still yields `OBSERVE_ONLY`, because no receipt verifier
  exists. Implementing the clause literally deletes the calibration-receipt
  precondition the operator kept under Q-B, on a path (`ops.py:141`,
  `scheduler.py:1022,1761`) that has no manifest preflight behind it.

## Parked (not done, not promised)

1. **`ARGUMENTATIVE_AUTHORITY=single_family_trial` is dead weight.** It cannot
   complete a trial: the `Config` direct-helper path passes no
   `critic_school_id`, a school can only arrive through the v4 envelope, and
   that envelope demands a manifest-bound authority value. R20 also makes it
   redundant in principle — if route topology decides, an authority value for
   the same thing is a knob for something that should not have one. Cost of
   removing: reverts part of steps 10-11 across `authority.py`, `config.py`,
   `crit.py`, plus the tests that name it. Small and clean.
2. **148 of 1279 recorded artifacts become prose-immune** under R21
   (100.0% -> 88.4% refutable; one root goes 79 -> 31). This is the price of
   "they are both formal", not a defect. Cost of changing it: A11 inverts.
3. **`render_batch_crit_pack` still prefix-clips** (`llm/packs.py:594`), so R3
   is unmet on the batch criticism path. S3 named `render_crit_pack` alone.
   `_document_excerpt` is retained with no caller because it is the right tool
   for that path.
4. Earlier parked items carried forward: `trial_authority_for`'s
   compute-then-discard shape as a defect class worth sweeping for; and
   everything in `experiments/2026-08-01-fix-adjudication-blindness/PARKED.md`.

## One process failure, recorded

The full gate's first run failed 2 of 3286, on tests written earlier in this
tranche. Cause: step 21 changed trial behaviour and only the assertions step 21
added were re-run, not the whole file. Both failures shared one reason —
`no-critic-school` — and neither was resolved by weakening an assertion; they
were rewired to the path that carries a critic school, keeping every assertion
they made. The gate caught what the step should have, and the failure is what
exposed parked item 1.
