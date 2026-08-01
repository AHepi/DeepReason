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
