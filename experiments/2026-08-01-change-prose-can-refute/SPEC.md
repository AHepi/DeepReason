# Spec for: "Prose can refute"

Traces: every item cites R/C numbers from REQUEST.md (`ce893107`, amended
`14d9bac8`). Untraceable items are bugs.

## What the code already provides (established, cited)

- `authority.py:95-101` `trial_authority_for` computes
  `mode = text_authority_mode(config, surface)` then unconditionally returns
  `TrialAuthority.OBSERVE_ONLY` for text. The mode is discarded.
- `authority.py:65-70` `text_authority_mode` reads a per-surface config knob,
  defaulting to `OBSERVE_ONLY`. Surfaces: prose / rubric /
  infrastructure-review / pairwise.
- `authority.py:73-80` `argumentative_authority_mode` reads
  `ARGUMENTATIVE_AUTHORITY`, values `{"observe_only", "trial_required"}`.
- `rules/crit.py:1-14` docstring: `crit_argumentative` under that knob —
  `observe_only` records scrutiny evidence, `trial_required` "routes the case
  through the defended cross-family trial". And: **"No configuration may grant
  a self-certifying prose warrant."** Demonstrative outcomes remain
  status-changing under every mode.
- `programs.evaluable(commitment)` (`programs.py:331-335`) is `predicate:` or a
  known `program:` — the existing formal/informal line.
- `adjudication/edges.py:94-113`: attack edges derive from WARRANTS. No warrant,
  no edge, no `REFUTED`.
- `llm/packs.py:806+` `render_crit_pack` gives the critic: problem-context,
  target-commitments, machine-evaluation-boundary, standing-attacks (heads
  only, droppable), and the target's own text **excerpted to budget**
  (`_document_excerpt`, `packs.py:245`). It does NOT give `Interface.refs`, the
  declared support chain (`ontology/artifact.py:31-35`), and it does not give
  scratch.

## Items

S1 (R1) — `src/deepreason/authority.py` `trial_authority_for`
  before: returns `OBSERVE_ONLY` for every text workload, discarding `mode`.
  after: returns the authority the computed `mode` designates.
  accept: `trial_authority_for(cfg, "text", surface)` varies with the config
  knob for every surface in `AuthoritySurface`; non-text workloads still return
  `STATUS` unchanged.

S2 (R2) — the prose-refutation path becomes reachable
  before: unreachable — no text run can mint a warrant, so `state.att` is empty
  in 26 of 42 roots.
  after: a prose criticism can produce a warrant and therefore an attack edge.
  accept: an offline run with the enabling config produces `len(state.att) >= 1`
  and at least one artifact at `Status.REFUTED`, from a criticism whose target
  carries NO evaluable commitment.

S3 (R3, R5, R6) — `llm/packs.py` `render_crit_pack`
  before: target text excerpted to a char budget; support chain absent.
  after: the refuting endpoint receives the full argument — the target's
  complete text and its declared `Interface.refs` support chain.
  **Scratch is excluded by R5/R6 and this item must not add it.**
  accept: for a target whose text exceeds the budget, the rendered pack
  contains the whole text and no `HARNESS PACK EXCERPT` marker; the pack names
  every id in `target.interface.refs`; and the pack contains no scratch block
  id, no `SCR_` handle, and no scratch advisory section.

S4 (R4) — the formal/informal boundary
  before: `execution_backed` / demonstrative outcomes are status-changing under
  every mode; everything else is advisory.
  after: a claim carrying an evaluable commitment still requires formal
  refutation; a claim that does not may be refuted by prose.
  accept: prose refutation of a target with an evaluable commitment is refused
  with a typed reason; prose refutation of a target with none succeeds.

S5 (R5, R6) — the separation is asserted, not assumed
  before: `rules/crit.py` happens not to import scratch; nothing pins it.
  after: a test pins that the criticism/adjudication authority chain contains
  no scratch object.
  accept: a test asserts no scratch id appears in any warrant, attack edge, or
  crit pack, and that `rules/crit.py` imports nothing from `deepreason.scratch`.

S6 (C3, C2) — nothing retroactive
  accept: verdict sweep over all 42 roots before and after — no root's `valid`
  changes, and no root's `state.att` changes; full gate 0 failed.

## Assumptions (operator may override)

A1 (Q4→R4): "formal claims in formal prose" is read as
`programs.evaluable(commitment)` — the codebase's existing line. Smallest
reading: it introduces no new classifier.

A2 (Q6→C3): the change is prospective only. Existing roots are interpreted
exactly as before; S6 measures this.

A3 (Q3a→R3): "the full argument" is the target's complete text plus its
declared support chain (`Interface.refs`), because those are the two things the
critic provably lacks today and both are properties of the argument itself.
Explicitly NOT scratch (R5/R6).

## Questions for operator (STOP — non-empty)

**One decision, and it is the whole shape of the change.**

`rules/crit.py` states a rule this request is in tension with: *"No
configuration may grant a self-certifying prose warrant."* The existing prose
path (`ARGUMENTATIVE_AUTHORITY = "trial_required"`) honours that by routing a
prose case **through the defended cross-family trial** — a second, different
model family must sustain the case before it becomes a warrant.

R2 says "Prose can refute." Two readings, materially different:

  **(a) Enable the built path.** Prose refutes by winning the defended trial.
  Nothing self-certifies; the safeguard stays. Smaller diff, and it is what the
  code was designed for.

  **(b) Remove the trial too.** A prose critic's own verdict mints the warrant
  directly. This is what "get rid of that requirement" reads like if "that
  requirement" extends past the `OBSERVE_ONLY` hard-return — but it deletes the
  cross-family check, and one model then both writes and adjudicates the case.

Q-A: (a) or (b)?

Q-B (Q1): does R1 also remove the calibration-receipt precondition
(`authority.py:96-99` refuses `calibrated_status` "until a receipt verifier
exists")? Under (a) it is untouched; under (b) it is the next thing in the way.

Q-C (Q5): R1-R4 are stated for refutation. May prose also ACCEPT — mint a
supporting warrant — or attack only? Attack-only is the smaller reading and I
will assume it absent an answer.

I have NOT chosen, because (a) and (b) differ in which safeguard survives, and
choosing (b) silently would delete a cross-family check the codebase installed
deliberately.

## Out of scope (explicit)

- The scratchpad, in every direction. R5/R6. Not requested, and now forbidden.
- `MIN_ATTACKS_FOR_RITUAL` and the four discarded detection flags — parked in
  the previous tranche, not requested here.
- Retroactive reinterpretation of the 26 `OBSERVE_ONLY` roots. A2.

## Budget

~120 lines under reading (a); ~180 and a second sub-tranche under (b).
1 commit under (a). Frozen surfaces touched: none — no state digest, no event
application, no replay format, no manifest schema, no qualification subject.
S6 proves existing roots do not move.

---

# EXTENSION for R7-R17 — the single-family path

S1-S6 above are unchanged and remain specified under reading (a). Everything
below is additional.

## What the record and the code establish (cited, not re-derived)

- The prose trial is unreachable in a single-family run by construction.
  `llm/firewall.py:261-279` `require_cross_family_judge_ensemble` raises unless
  there are **>=2 judge seats from >=2 distinct route families**. One family
  means `JudgeEnsemblePolicyError`, so `ARGUMENTATIVE_AUTHORITY="trial_required"`
  can never complete. This is exactly the blocker R13/R15 name.
- Every recorded run bound all schools to ONE model on ONE seat, so no run has
  ever instantiated genuine cross-family criticism. The independence the current
  rule appears to protect has never existed in practice (FEASIBILITY.md).
- The chooser already looks up the author's school in order to EXCLUDE it, and
  the critic is already routed by school and stamped with its own school. So
  R14's "a critic isn't from the same school" is already true today and needs
  no new enforcement — only preservation.
- Authority modes live on `Config` (`config.py:373` `ARGUMENTATIVE_AUTHORITY`,
  read via `authority.py:73-80`), NOT on the run manifest.
  `require_distinct_families` by contrast IS a manifest field
  (`run_manifest.py:495`) and governs the PROPOSING side only.

## Items

S7 (R13, R15, R16) — a single-family predicate
  files: `src/deepreason/llm/firewall.py`
  before: family counting exists only inside the cross-family judge check.
  after: a named predicate reports whether the run's route families number
  exactly one, derived from immutable leases exactly as the existing check does.
  accept: the predicate returns True for a lease set of one family, False for
  two or more, and False for an empty set (fails closed).

S8 (R14, R15, R8) — a cross-SCHOOL judge ensemble, reachable only in a
single-family run
  files: `src/deepreason/llm/firewall.py`
  before: `require_cross_family_judge_ensemble` is the only ensemble gate.
  after: a sibling `require_cross_school_judge_ensemble` requires >=2 judge
  seats from >=2 distinct SCHOOLS, and is selectable ONLY when S7's predicate
  is True. The cross-family gate is untouched and remains the gate whenever
  more than one family is present.
  accept: with two families present the cross-school gate is not selected even
  if configured; with one family and two schools it accepts; with one family and
  one school it raises; the existing cross-family gate's own tests are unchanged
  and still pass.

S9 (R7-intent, R14) — the author's own school stays excluded
  files: none (assertion only)
  before: the chooser subtracts the author's school by construction.
  after: unchanged, and pinned.
  accept: a test asserts no criticism assignment is ever produced whose critic
  school equals its target's school, under the new mode as well as the old.

S10 (R9, second reading) — nothing new is shown at the model boundary
  files: none (assertion only)
  before: the crit prompt never names the author; targets arrive under blank
  aliases.
  after: unchanged.
  accept: for identical inputs, the rendered criticism and judge prompts are
  byte-identical with the new mode enabled and disabled; no author or school
  label appears in either.

S11 (R15, C3, C2) — off by default, and existing roots do not move
  files: `src/deepreason/config.py`, `src/deepreason/authority.py`
  before: `ARGUMENTATIVE_AUTHORITY` is a closed pair
  `{"observe_only", "trial_required"}`.
  after: one additional value selecting the single-family path. Default
  unchanged at `observe_only`. **No manifest field is added** — authority modes
  live on `Config`, per the precedent above — so no manifest schema, no
  qualification subject digest, and no replay record format is touched.
  accept: a 42-root verdict sweep before and after shows no root changing
  `valid`, and no root changing `state.att`; full gate 0 failed.

S12 (R5, R6) — the scratchpad stays out of this entirely
  files: `tests/`
  accept: S5's assertion extended to the new path — no scratch object appears
  in any warrant, attack edge, criticism pack or judge pack under the new mode.

## Assumptions (operator may override)

A4 (R7/R14 contradiction): R14 supersedes R7's literal sense; the vehicle is
the schools architecture and the independence guarantee is cross-school. Stated
at length in REQUEST.md's amendment 3. **This is the load-bearing assumption of
the whole extension** — if the operator did mean literal same-school criticism,
S8/S9 invert.

A5 (R15): "a single model is running the entire harness" is read as ONE ROUTE
FAMILY across the run's leases, not one model id and not one seat. Smallest
reading consistent with R13's "single family runs" and with how
`require_cross_family_judge_ensemble` already counts.

A6 (R8): "mint criticisms" is read as making the EXISTING argumentative-warrant
path completable in a single-family run, not as inventing a new warrant kind.
Smallest reading; no new record type, so C1/C3 hold trivially.

A7: the mechanical-checking channel that already mints defeats blind to
authorship (FEASIBILITY.md risk 6) is left exactly as it is. Not requested.

## Questions for operator

None. A4 is recorded as an assumption with its reasoning rather than a
question, per C8 ("Do not ask for permission to do anything unless it is out of
scope") — it is an interpretation, and the operator can overturn it in one word.

## Out of scope (explicit)

- The scratchpad, in every direction (R5/R6).
- The mechanical-checking defeat channel (A7).
- `require_distinct_families` on the proposing side — it is a manifest field
  governing school bindings, and nothing in R7-R17 asks for it.
- Making the schools genuinely different models. FEASIBILITY.md notes a mode
  for this exists and has never run; not requested.

---

# EXTENSION 2 for R18-R20 — expose it, and put the guarantee where the
# operator keeps pointing

S1-S12 and the S1 amendment stand. This extension corrects two things about
S7/S8 and adds the exposure R20 demands.

## What the code establishes (checked, not assumed)

- **A judge cannot carry a school through the manifest.**
  `run_manifest.py:2751` — `_validate_v4_criticism_policy` raises
  `V4_CRITICISM_ROLE_UNSUPPORTED: bindings must name argumentative_critic` for
  any binding whose role is not `argumentative_critic`. The Pydantic model
  permits `role="judge"`; the validator does not. **Step 6 recorded the
  opposite and was wrong** — it read the model and not the validator. So Q9 has
  no answer that leaves manifests untouched: there is no manifest-authored
  judge-school binding, and adding one changes a manifest validator.
- `resolve_school_role_lease` (`firewall.py:379`) supports exactly two roles,
  `conjecturer` and `argumentative_critic`. Judges are not school-routed
  anywhere.
- The trial already carries `critic_school_id` end to end
  (`trial.py:553,599,671,684`) and stamps it on the validity node and the
  critic. The target's author school is `target.provenance.school`.
  **Both schools are already in hand at the moment a warrant is minted.**
- The school roster is a run-level fact, not a manifest binding:
  `config.N_SCHOOLS` (default 4) and `schools.init_schools`
  (`scheduler.py:272`).

## The correction (Q8, Q9 resolved; Q7 resolved)

**R18/R20 say "cross school CRITICISM", and that is what the substitute
guarantee should be — not a cross-school judge ensemble.**

The operator has now written "criticism" three times across messages 4 and 5
("same school criticisms", "as long as a critic isn't from the same school",
"It should be cross school criticism") and has never written "judge". S8 built
a cross-school JUDGE ensemble because the blocker was a JUDGE gate
(`require_cross_family_judge_ensemble`). That was reasoning from the obstacle
rather than from the requirement.

Reading the requirement instead: in a single-model run the independence that
cross-family judging was standing in for is supplied by **the critic being from
a different school than the author** — which is R14 verbatim, already true, and
already enforced at four layers (S9). Nothing needs to bind a school to a judge
seat, so Q9 dissolves rather than being answered, and no manifest validator is
touched.

This also resolves the tension the judge-ensemble reading would have created
with S10: conditioning judge seats by school would change judge prompts, and
S10 requires them byte-identical across modes.

Q7 — **model, not family.** R19 and R20 say "single model runs" and "a single
model is occupying all positions". Keyed on model identity, which is strictly
narrower than family and therefore fails closed: two different glm models share
a family and are not one model. A5's family reading is superseded for this gate.

Q8 — **automatic.** "exposed whenever" is read as: no configuration selects it;
the run's route topology does.

## Items

S13 (R19, Q7) — a single-MODEL predicate
  files: `src/deepreason/llm/firewall.py`
  after: `is_single_model_run(leases)` is True iff exactly one distinct model
  identity occupies every leased seat of every role.
  accept: True for one model across all roles; False for two models sharing one
  family; False for an empty lease set. `is_single_family_run` is unchanged and
  still passes its own tests.

S14 (R18, R20) — the substitute guarantee is cross-school CRITICISM
  files: `src/deepreason/informal/trial.py`
  before: `_argument_trial_steps` calls `adapter.require_cross_family_judges()`,
  which is unsatisfiable in a single-model run.
  after: in a single-model run the trial requires instead (a) >=2 frozen judge
  seats, and (b) a critic school that is present and differs from the target's
  `provenance.school`. Outside a single-model run the cross-family gate governs
  exactly as today.
  accept: a single-model run with critic school != author school completes and
  mints an ARGUMENTATIVE warrant; the same run with critic school == author
  school is refused with a typed reason; the same run with no critic school is
  refused with a typed reason; a two-model run still raises
  `SECOND_JUDGE_FAMILY_REQUIRED`.

S15 (R20) — exposure, with nothing to configure
  files: `src/deepreason/llm/adapter.py`
  before: `school_judge_bindings` is a constructor opt-in that the only
  production adapter construction (`adapter.py:1467`) never passes, so
  `_select_judge_ensemble` always falls back to cross-family.
  after: selection keys on S13's predicate alone. No constructor argument, no
  Config value, no manifest field is required for a qualifying run to get the
  substitute guarantee.
  accept: an adapter built exactly as `build_adapter` builds it, with one model
  on every seat, selects the substitute path; with two models it does not.

S16 (R20, C3, C2) — still nothing retroactive
  accept: 42-root sweep before and after unchanged; full gate 0 failed.

## Assumptions (operator may override)

A8 (Q7): "a single model is occupying all positions" is model IDENTITY across
every leased seat of every role. Narrower than A5's family reading, and
narrower fails closed.

A9 (R18): the substitute guarantee is cross-school CRITICISM, not a cross-school
judge ensemble. **Load-bearing.** Grounds: the operator's word is "criticism"
in all three statements; the guarantee is already enforced and already recorded
on the artifact a warrant hangs from; and the judge-ensemble route cannot be
supplied without changing a manifest validator.

A10 (S14): `require_cross_school_judge_ensemble` and `school_judge_bindings`
are RETAINED, not deleted — they remain correct for a manifest that does author
judge bindings, and deleting tested, working code to tidy up is not what was
asked. They simply stop being the mechanism R20 exposes.

## Out of scope

- The S4/A1 formal-boundary question. Still unanswered by the operator, carried
  in VALIDATION.md, and untouched here.
- Making the schools genuinely different models.
- Widening `_validate_v4_criticism_policy` to admit judge bindings — A9 removes
  the need, and it is a manifest validator.

## Budget

~90 lines across 3 source files plus tests. Frozen surfaces touched: **none**.
No manifest schema, no manifest validator, no state digest, no event
application, no replay record format, no qualification subject.

---

# AMENDMENT to S1, made at step 10 execution (append-only)

**S1's acceptance clause as written contradicts the operator's own answer to
Q-B, and the operator's answer wins.**

S1 accepts on: "`trial_authority_for(cfg, "text", surface)` varies with the
config knob for every surface". Implemented literally, `calibrated_status`
returns `TrialAuthority.STATUS`. That deletes the calibration-receipt
precondition — and Q-B asked exactly whether R1 removes it, with this spec
answering "Under (a) it is untouched." The operator chose (a).

The collision is not theoretical. `ops.py:141` `review_infrastructure` and
`scheduler.py:1022,1761` call `trial_authority_for` on the DIRECT-HELPER path,
with no manifest in play, so `text_status_authority_issues` — the preflight
that refuses an unverified receipt — never runs for them. The unconditional
return was the only gate there. `tests/test_text_authority_policy.py:166`
`test_unverified_calibrated_infrastructure_review_is_observe_only` pins this,
and failed under the literal implementation.

**S1 as executed:** the computed mode is honoured and is no longer discarded,
and `calibrated_status` is refused by a named, isolated predicate
`calibration_receipt_is_verified(config)` which returns False until a receipt
verifier exists. Behaviour is unchanged; what changes is that the block is one
identified gate with one attachment point instead of a computation thrown away.

**S1 accept, corrected:** `trial_authority_for` reads the knob for every
surface in `AuthoritySurface` and routes on it; `calibrated_status` yields
`STATUS` only when the receipt is verified, and no verifier exists, so today it
yields `OBSERVE_ONLY` for every surface; non-text still returns `STATUS`.

Overturning this needs one word from the operator, and it is a separate
decision from R1-R4: it would grant status authority to an unverified
reference string on a path with no preflight.

## Budget

~130 lines across 3 source files plus tests, 1 commit, on top of S1-S6's ~120.
Frozen surfaces touched: **none**. No manifest schema (authority stays on
`Config`), no state digest, no event application, no replay record format, no
qualification subject. S11 measures the no-movement claim rather than asserting
it.

