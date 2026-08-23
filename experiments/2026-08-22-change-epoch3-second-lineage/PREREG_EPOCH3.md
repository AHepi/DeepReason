# PREREG — epoch 3: a second problem lineage, then reach

Frozen **before any provider call**. Everything here was settled offline and
is measured in SPEC.md (M1-M11); the only step this document does not cover
is the launch itself, which waits on the operator's credential file.

Map preflight (CLAUDE.md; ids resolved in SPEC.md's header):
DR-SUB-amendment, DR-SUB-application, DR-SUB-workloads, DR-SUB-measures,
DR-CON-run-identity, DR-INV-frozen-surfaces. The seam document for the pair
this design turns on — amendment × application — does not exist; the two
subsystem documents were read in its place and the gap is PARKED
(PARKED.md P3-epoch3).

## 1. The registered hypothesis

Inherited verbatim from `experiments/2026-08-21-measure-reach-firing/
DIAGNOSIS.md`, unchanged since the reach-rich tranche registered it:

> a run whose problems carry at least one subject-substantive
> machine-evaluable criterion that the candidate conjecturer is NOT
> instructed to satisfy will move pairs out of `E4` and produce non-zero
> `reach_set` events.

Epoch 3 tests exactly that and nothing else. No threshold is lowered, no
qualifying vocabulary is widened, and no predicate is reclassified anywhere
in this tranche.

## 2. What epoch 3 changes against the reach-rich design, and why

The reach-rich epochs 1 and 2 both died at cycle 2 of 24 on unrelated typed
operational failures, before the connection/integration cascade produced a
single accepted candidate addressed to a spawned problem. Both causes are
fixed on `main` — E42 (the repair-patch transport reading) and E43 (the
route lease vs controller-tuned `max_tokens` ceiling) — so epoch 3 cannot
die either recorded way. Two things change:

**(a) A second problem lineage.** An amendment epoch registers the reshaped
question as a `trigger="seed"` problem beside the original, so the root
holds TWO seed lineages (SPEC.md M1, measured on a scratch copy: 105 → 106
problems, the new one carrying the three subject predicates). This is the
operator's stated goal for the tranche.

**(b) One manifest field.** `inquiry_capability_policy.attached_evidence`
is enabled. This is not a design preference; it is forced. Every amendment
`deepreason continue` accepts must carry `--attach` (M4: a question-only
amendment leaves the epoch dossier's `problem_ref` on the SUPERSEDED
problem and the continuation refuses with `RUN_INPUT_MISMATCH`), and
`--attach` is gated on that flag (M5). The behavior diff against the
reach-rich manifest is exactly the five `attached_evidence` fields and no
other line (M8).

Nothing else moves: the question, the three predicates, the solo glm-5.2
configuration, the policy preset and the frozen compile timestamp are
IMPORTED from the reach-rich builder rather than restated. The resulting
manifest compiles clean with zero notices at `bb0455384ea09b5b…` (M7).

## 3. Declared deviations from the operator's brief

Recorded here as predictions, not discovered afterwards.

**D1 — the lineage lands in a NEW root.** The brief names the existing
terminal root `40e713b30a147dfc…`. That root is refused three independent
ways: `deepreason results` reports `amend_ready false` because
`operational_failure` is not in
`RESUMABLE_STOP_REASONS = {"converged", "budget_exhausted"}` (M3); a
question-only amendment on a copy of it produces a root `continue` refuses
(M4); and `--attach` on it is refused `AMEND_EVIDENCE_NOT_AUTHORIZED` (M5).
None is fixable inside this tranche's read-only scope. Epoch 3's root is
`bb0455384ea09b5b…`; the reach-rich roots are neither renamed nor touched.

**D2 — the second lineage's criteria are inherited, not distinct.** The
brief asks for a second seed "carrying its OWN subject-substantive criteria
(distinct predicates)". No amend surface can do that: `apply.py` builds the
successor run input with `criteria=parent_input.problem.criteria`, and
`ReasoningWorkloadSpec` holds one problem and one criteria tuple (M2, M6).
The reach path is unaffected, because `reach_sweep` measures novelty against
`carried = artifact.interface.commitments` — the ARTIFACT's own battery —
not against its problem's criteria (`reach.py:126`).

**D3 — the brief's stated blocker is re-measured, not assumed.** P4-reach
and the brief say a single-seed run puts every accepted artifact on the
seed's own problem, so the seed is never foreign. That is true of the
reach-rich epochs and is a property of their TRUNCATION at cycle 2, not of
single-seed runs: a committed single-seed text root that reached cycle 8
(`experiments/2026-08-12-live-grounded-extension-expansion/run`) carries 262
addressed artifacts, 202 of them addressed to `succ:`/`conn:` problems and
186 of those ACCEPTED (M9). For every one of those the seed problem IS
foreign. Epoch 3 therefore has TWO independent routes to a carrier — phase
1's own cascade and phase 2's second lineage — and the tranche predicts the
first will produce candidates before the second exists.

## 4. Design, frozen

**Phase 1.** `deepreason run --run-manifest` against the epoch-3 manifest,
`--budget cycles=12 --token-budget 200000`. Seed question, three predicates
and configuration exactly as the reach-rich PREREG §3 froze them. The seed
dossier is EMPTY: nothing in phase 1 depends on a document.

**The amendment.** `deepreason amend --attach
supplement-nocturnal-collapse.md --reshape-question <sibling question>`,
run only if phase 1's `run-stop.json` reason is `converged` or
`budget_exhausted`. The sibling question stays in the urban-heat-island
family and asks about the COLLAPSE of the night-time gap under wind and
cloud, so lineage-2 artifacts are plausibly on-subject for the seed's
predicates while answering a different question.

**The attachment control.** `preflight_supplement.py` proves offline that
the supplement's own bytes pass NONE of the three subject predicates. This
closes the mirror of the census's `relation_form_commitment` anti-pattern:
there a criterion was satisfiable without saying anything about the subject;
here a SOURCE could have satisfied the criteria without the model reasoning
at all. Measured before launch: all three FAIL.

**Phase 2.** `deepreason continue --budget cycles=12 --token-budget 200000`.

**Budget.** 12 + 12 = 24 cycles, 200 000 + 200 000 = 400 000 tokens — the
reach-rich PREREG's frozen bound SPLIT across the phases, never added to.

**Qualification.** The subject digest moves (M8), so the full production
battery (~14 min, ~1160 calls) runs once. Priced and accepted; it is the
cost of the second lineage and of nothing else.

## 5. How epoch 3 will be judged — typed outcomes only

Model prose is not evidence. The admissible record is `run-status.json`,
`run-stop.json`, `progress.jsonl`, `log.jsonl`, `verify_root`, and the
committed census tooling (`experiments/2026-08-21-measure-reach-firing/
census.py`, imported by the shim, never rewritten).

- **SUCCESS** — a typed terminal, `verify_root` reporting no violations, and
  the census showing `reach_set` Measure events > 0. The root is committed
  and named as Rung 5's gate fixture.
- **UNSUPPORTED** — the run reached its cycle budget with the carrier
  present (accepted artifacts addressed to problems other than the one whose
  criteria are on the foreign side) and still recorded zero `reach_set`.
  The prediction was tested and not borne out.
- **PRECONDITION-BLOCKED** — the census shows pairs sitting at `E4` with
  `reasoning-envelope-wf` as the failing criterion. The P1-reach fix makes
  this signature unexpected; if it reappears, the fix regressed.
- **TRUNCATED-BEFORE-CARRIER** — the run ended before any accepted artifact
  was addressed to a non-seed problem. The hypothesis was never exercised.
  This is the label the reach-rich tranche had to invent after the fact; it
  is registered here in advance so epoch 3 never has to.
- **AMEND-BLOCKED** — phase 1 reached a terminal whose stop reason does not
  authorize continuation, so the second lineage never existed. Phase 1 is
  still judged on its own by the four labels above.

Zero reach on one run is NOT a refutation: capability-channel and spawn
behaviour is stochastic across identical runs. **One repeat is
pre-authorised**, launched from a retired root (`git mv run
failed-epochN-run-<id>`, rename committed FIRST). Zero on both — the verdict
is recorded, both roots are committed, and the tranche STOPS; the decision
returns to the operator.

**Reporting the P5 rulings** (now codified on `main`,
`experiments/2026-08-22-change-reach-p5-rulings`): the census vocabulary
knows exit **E0**, the empty-own-battery exit — an artifact declaring no
commitments of its own forbids nothing and every pair it appears in takes
that exit. Any E0 event, and any reach event landing at coverage EXACTLY
0.500 (a FULL hit, because a floor means "at least"), is reported as
observed rather than reinterpreted. If neither occurs, that is stated too.

## 6. Scope

No changes to `src/` or `tests/`. `git diff --stat origin/main -- src/
tests/` proves it at every phase boundary. A defect found mid-run is PARKED
with a ready-to-send prompt, never fixed here. No pytest gate is owed for an
untouched tree; `tools/docs_verify.py` runs because the tranche commits, not
because a map document moved — none does.


---

# PREREG AMENDMENT 1 — 2026-08-23, after attempt 2

Sections 1-6 above are FROZEN and are not rewritten. This amendment records
what changed, on whose authority, and what it predicts — appended, so the
original registration and the revision can both be read.

**Authority.** REQUEST.md Amendment 2 / R17, the operator's answer to a fork
put after attempt 2's typed failure: *"Single phase, full 400k, cycles=4
(recommended)"*.

**What changes against §4.** The budget is no longer split. Epoch 3 runs as
ONE phase, `--budget cycles=4 --token-budget 400000`. The registered bound of
400 000 tokens is unchanged; only its division is. The amendment step and
phase 2 are DISABLED for this attempt (`SECOND_LINEAGE=0`), so the second
problem lineage is deferred and R1 is not delivered by this run.

**What does NOT change.** The question, the three subject predicates, the
solo glm-5.2 configuration, the manifest (`bb0455384ea09b5b…`, still with
attached evidence enabled so a later amendment remains possible), the
supplement and its control, and every judgement label in §5.

**Registered prediction, made before launch.** The measured burn rate
(165 466 tokens across 56 calls, ~2 955 per call, cycle 0 not finished)
predicts that 400 000 tokens buy roughly 124 calls — on the order of two
cycles, not four. The token budget is therefore expected to bind before the
cycle budget, which under P5-epoch3 yields `operational_failure` rather than
`budget_exhausted`. The run is expected to be UNRESUMABLE. This is
registered rather than discovered so that outcome cannot later be presented
as a surprise.

**What the prediction does not threaten.** §5's SUCCESS is a typed terminal,
`verify_root` with no violations, and `reach_set > 0`. None requires a
resumable stop reason. If the run produces an accepted artifact addressed to
a spawned problem and that artifact passes the seed's three predicates, the
hypothesis is exercised whatever the stop reason.

**The label to watch.** If the run again dies before any accepted artifact is
addressed to a non-seed problem, the outcome is TRUNCATED-BEFORE-CARRIER for
the second time, and the honest reading shifts: twice is no longer an
accident of one budget, and the question becomes whether this question and
configuration can reach the carrier at all inside any bound the operator
wants to spend. That judgement is the operator's and is not pre-empted here.

**AMEND-BLOCKED** remains defined in §5 and simply does not apply to this
attempt: the amendment is not attempted, so it cannot be blocked.
