# RESULTS — minting a reach-rich root

Honest ledger. Each segment says what the record shows and what remains
unproven. "Accepted does not mean true."

---

## 2026-08-22 — pre-launch: the briefed design cannot fire, and the obstacle is already on the parked list

**What the record shows.** `rehearsal.json` (10 scenarios, the real
`measures/reach.py::reach_sweep` over real `Harness` roots, real
`compile_interface`-compiled artifact batteries) settles the carrier
question the census tranche left open. The census proved reach fires on no
committed root and predicted that subject-substantive criteria would move
pairs out of `E4`. That prediction is about CRITERIA. It is silent on
whether a single-seed text run can produce a CANDIDATE that does not
already carry the foreign problem's battery. It cannot:

- **S1 `E3 no-novel`.** Every problem in a single-seed text run that mints
  ENVELOPE artifacts carries the seed's exact battery. `rules/conj.py:1462`
  selects the envelope output path from whether the problem's own criteria
  contain `reasoning-envelope-wf`, and only the seed problem and the `ra:`
  problems that copy `criteria=parent.criteria` (`rules/spawn.py:104`) do.
  `qualifying - carried` is empty for every such pair.
- **S2 / S8a `E4 criterion-fail`.** Every other problem — `conn:`,
  `integ:`, `disc:` — mints PROSE, and prose cannot pass
  `reasoning-envelope-wf`. That gate is in the seed problem's QUALIFYING
  set: `programs.PROGRAMS` declares it `class_="structural"`, but
  `measures/reach.py::_STRUCTURAL_PROGRAMS` does not list it, so
  `_substantive` returns True. It rejects every prose candidate before a
  single subject criterion is read.
- **S3 HIT (1 `reach_set` event).** Two problems that both carry
  `reasoning-envelope-wf` but differ in their subject predicates do fire.
  The mechanism is wired and works; nothing about `reach_sweep` is broken.
- **S8b HIT (1 `reach_set` event).** With the already-parked fix P1
  simulated in-process — `reasoning-envelope-wf` counted structural, as
  `programs.PROGRAMS` already declares it — a PROSE connection candidate
  reaches the seed problem on its subject criteria alone, at coverage 2/3.
  This is the registered hypothesis's condition, firing on the first
  attempt.
- **S4 / S8c `E4` (controls).** A subject predicate the candidate does not
  satisfy, and an on-form but off-SUBJECT relation, both stay out. The
  criteria are not vacuous and P1 does not manufacture hits.

`preflight_seed.json` adds the second half of the pre-launch evidence:
`seed_reasoning_workload` really does attach this tranche's three subject
criteria to the seeded problem, all three evaluate to a verdict rather than
an error, and all three PASS an on-subject answer while FAILING an
off-subject one. No committed root has ever carried a criterion of that
kind.

**What this changes.** The prediction the brief registered is not refuted —
it was never exercised. As the code stands, this run would record zero
`reach_set` events however good its criteria are, because the candidate
that carries novel subject criteria is prose and a well-formedness gate
rejects it first. PREREG.md §4 names that outcome
**PRECONDITION-BLOCKED**, deliberately distinct from UNSUPPORTED.

Note the direction. The unblocking change is P1, and P1 TIGHTENS the
substantive/structural boundary: it stops a well-formedness gate counting
as substantive. No threshold is lowered, `REACH_COVERAGE_MIN` is untouched,
and nothing is added to the qualifying vocabulary. The Bronze Age
discipline is not relaxed by this; it is applied more consistently. The
census already measured the blast radius on the committed corpus:
`probe_immunity.json` `backed_only_by_declared_structural = 0`, so no
committed root's `formally_backed` verdict moves.

**Residue — what remains unproven.**

- Nothing live has been run. No provider call has been made in this
  tranche; the credential file was absent at the launch boundary and the
  brief instructs stopping there.
- The rehearsal's prose candidate is a hand-written stand-in for what
  glm-5.2 would actually write for a `conn:` problem. It shows the pair CAN
  survive; it does not show how often a real connection candidate would.
  That frequency is exactly what a live run measures, and it stays unknown.
- S8b's coverage is 2/3 because the rehearsal's foreign problem carried two
  subject predicates. The frozen design carries three, giving 3/4 = 0.75
  after P1; both clear `REACH_COVERAGE_MIN`, but neither number has been
  observed live.
- Whether the run reaches a typed terminal, and whether `verify_root`
  returns clean on a root whose seed problem carries operator-authored
  `predicate:` criteria, are both untested. No root in the corpus has that
  shape.
- The parked findings P2 (a `predicate:` form gate is substantive by
  construction) and P3 (the `reach.py` docstring names three exits, the
  code takes five) are untouched and still open.

**Scope kept.** `src/` and `tests/` are unmodified; `git diff --stat`
against `origin/main` shows changes only under
`experiments/2026-08-22-live-reach-rich-run/`. No map document moved, so no
`docs_verify` run is owed. No threshold, program list, or criterion
classification was changed anywhere.
