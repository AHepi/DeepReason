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

---

## 2026-08-22 (appended by the P1 fix tranche) — the rehearsal was re-run in place

`experiments/2026-08-22-reach-structural-programs-fix` landed P1-reach, so
`rehearsal.py`'s `wf_structural` parameter — which simulated the fix by
rebinding `measures/reach.py::_STRUCTURAL_PROGRAMS` in-process — and its two
call sites are DELETED, and every scenario now runs against the shipped module
constant. `rehearsal.json` is regenerated in place.

The pre-fix results this tranche's narrative above describes are preserved
verbatim at
`experiments/2026-08-22-reach-structural-programs-fix/rehearsal-as-shipped.json`
(and in git at `29b0d9638`). The decisive delta: **S8a moved from
`E4 criterion-fail` / 0 reach events to `HIT full` / 1**, and is now identical
to S8b on every recorded field but its label; **S8c stayed
`E4 criterion-fail` / 0**, so the control still holds. S2 also moved to
`HIT full`, which this tranche's prediction did not name — recorded as
P5-reach in the fix tranche's PARKED.md.

`PREREG.md` §4's PRECONDITION-BLOCKED outcome is therefore discharged: the
precondition is cleared. Nothing else about this tranche's verdict changes,
and nothing live has still been run.

---

## 2026-08-22 — relaunch window: precondition re-confirmed against the shipped tree, launch pending the credential

**What the record shows.** `rehearsal.py` was re-run against the current
tree at `2a744325f` (`origin/main`) with no in-process rebind anywhere —
the `wf_structural` parameter is gone from the script, and the only
remaining mentions of it are the docstring lines that say so. The
regenerated `rehearsal.json` is **byte-identical** to the committed one
(`diff` clean), so this window reproduces the fix tranche's measurement
rather than re-deriving a new one:

    S8a prose conn: candidate vs seed (as shipped)   exit=HIT full   reach_events=1  cov=0.667
    S8b prose conn: candidate vs seed (P1 landed)    exit=HIT full   reach_events=1  cov=0.667
    S8c prose OFF-subject candidate vs seed          exit=E4 criterion-fail  reach_events=0

S8a is a HIT with no rebind, S8b is identical to it, and the off-subject
control S8c still exits `E4`. The shipped sets agree by construction:

    declared-minus-reach: []   reach-minus-declared: []

`PREREG.md` §4's PRECONDITION-BLOCKED outcome is therefore not the
expected result of this launch. The hypothesis is now exercisable.

**Offline ladder gates, dry-run before spending a token.** Both steps the
ladder runs before `qualify` were exercised against a throwaway root in the
session scratchpad (never in the repo), and both reproduce the committed
digests exactly:

- `build_manifest.py` → `manifest_sha256 40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`,
  `problem_id question-4dd62735b90864a75220e09b302500bc`,
  `run_input_digest 62e75cb5e85b0d477c1a42b2618a43ed0a66943cc520d31edc96a9ccb6a10f3a`,
  `compile_notices []`.
- `preflight_seed.py` → rc=0; all three subject predicates evaluable,
  passing an on-subject answer and failing an off-subject one;
  `preflight_seed.json` regenerated byte-identical to the committed file.

**Residue.** Nothing live has still been run. The `env` file carrying
`OLLAMA_API_KEY` is absent from this container (it is gitignored by
`.gitignore:48` and never survives a rollback), so the ladder's own first
guard would exit rc=1. The launch waits on it and on nothing else.

**Scope kept.** `git diff --stat` is empty for `src/` and `tests/`; the only
file this segment adds is this narrative.

---

## 2026-08-22 — the live run: two epochs, both terminated at cycle 2 of 24, zero reach, and the carrier never existed

**What the record shows.** The frozen design was executed unchanged, twice —
the second launch being the ONE repeat `PREREG.md` §4 pre-authorises. Both
epochs reached a typed terminal and both replay-validate clean. Neither
recorded a `reach_set` event, and neither reached a state in which one was
possible.

| | epoch 1 (`failed-epoch1-run-40e713b3…`) | epoch 2 (`run`, id `40e713b3…`) |
|---|---|---|
| state / stop_reason | `failed` / `operational_failure` | `failed` / `operational_failure` |
| cycles | 2 of 24 | 2 of 24 |
| `verify_root` violations | **0** | **0** |
| accepted / refuted | 42 / 4 | 55 / 1 |
| artifacts / problems | 50 / 58 | 60 / 105 |
| logged tokens | 117 017 | — (budget 400 000, untouched) |
| embedder | neural (`nomic-ai/nomic-embed-text-v1.5`) | neural (same) |
| `reach_set` events | **0** | **0** |
| typed failure | `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` | `ROUTE_LEASE_MISMATCH … max_tokens expected=32768 actual=20480` |

Run identity is deterministic, so both epochs carry the same run id
`40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`; epoch 1
was retired by rename with the rename committed first (`4cdf3a5a9`) before
epoch 2 was launched.

**The P1-reach fix held live, and that is a positive result.** `PREREG.md`
§2 predicted that as the code then stood, `reasoning-envelope-wf` would
reject every prose candidate before a single subject criterion was read, and
§4 named that outcome PRECONDITION-BLOCKED. **That signature is absent from
both records.** Each census reports `reasoning-envelope-wf` exactly once, in
`_crit_kinds`, classified `structural:` — it entered no qualifying set and
vetoed no pair. The offline rehearsal's claim now has a live counterpart:
the gate that blocked reach in every text run no longer does.

`verify_root` returning **0 violations on both roots** discharges a second
residue this tranche had carried since before launch: no root in the corpus
had ever carried operator-authored `predicate:` criteria on its seed problem,
and it was unknown whether replay validation would accept one. It does.

**Why reach is zero, established rather than inferred.** The census alone
does not say WHOSE criteria sat on the foreign side of each pair, and the
tranche's hypothesis is about one specific foreign side. `carrier_probe.py`
(committed here; opens each root READ-ONLY and walks `reach_sweep`'s own pair
construction, `measures/reach.py:108-124`) answers it directly:

    epoch 1   accepted 46   accepted-and-addressed 14
              artifacts_that_could_have_seed_as_foreign  0
    epoch 2   accepted 59   accepted-and-addressed 23
              artifacts_that_could_have_seed_as_foreign  0

**Every accepted, addressed artifact in both runs is addressed to the seed
problem itself.** `reach_sweep` skips a problem the artifact already
addresses, so the seed problem was never on the foreign side of any pair, in
either run. The candidate the hypothesis requires — a prose `conn:`/`integ:`
candidate, accepted, addressed elsewhere, meeting the seed's subject
predicates (rehearsal scenario S8a) — was never minted. Consistently, every
gate pair that did reach a verdict qualified on `relation-form@578e42df713e`
alone (196 pairs in epoch 1, 529 in epoch 2), at coverage 0.33, capped below
`REACH_COVERAGE_MIN` and therefore provisional at best. That is the P2-reach
form gate doing exactly what P2-reach says it does.

Nothing falls under **P5-reach**: with zero reach events in both roots, no
reach event involved an artifact with an empty own battery and none landed at
coverage exactly 0.500. Reported as required, not reinterpreted.

**The verdict, and the one judgement this tranche will not make for you.**
`PREREG.md` §4's literal branch for zero reach on both runs is UNSUPPORTED.
On this evidence that label would over-claim, and the honest ledger says so:
UNSUPPORTED means the prediction was tested and not borne out, and this
prediction was never tested. Both runs stopped at cycle 2 of 24, on two
UNRELATED typed operational failures, before the connection/integration
cascade produced a single accepted candidate addressed to a spawned problem.
`PREREG.md` created PRECONDITION-BLOCKED for exactly this distinction —
between a hypothesis that failed and a hypothesis that never ran — but
defined it narrowly, as the §2 `reasoning-envelope-wf` blockage, which is now
cleared. The outcome here is a third thing the pre-registration did not
anticipate: **TRUNCATED-BEFORE-CARRIER**. The pre-registration is frozen, so
this tranche records both readings and does not relabel §4 on its own
authority. Which label the record carries is the operator's call, and so is
whether the two operational failures are fixed before a third epoch.

**Residue — what remains unproven.**

- **The registered hypothesis is untested.** Whether a real `glm-5.2`
  connection candidate survives the seed problem's subject predicates is
  exactly as unknown as it was before launch. The rehearsal's S8a remains a
  hand-written stand-in, and the offline regression remains the only proof
  that the mechanism can fire at all.
- **Both failures are stochastic in kind and unquantified in rate.** Two runs
  of an identical configuration failed at the same cycle for two unrelated
  reasons. Whether either is reliable, intermittent, or a coincidence of this
  question's shape is not established by n=2.
- **`20480` has no established producer.** P9-reach records the negative
  result (absent from `src/` as a literal, absent from every token-reservation
  record in the root) so a fix tranche does not re-derive it, but the
  component that computed it is unidentified.
- **P4-reach is untouched and still bounds Rung 5.** Even a run that produced
  reach events would give one problem lineage plus its spawn cascade;
  nomination counts reach across DISTINCT lineages, and a text run still
  cannot seed a second problem with its own criteria.
- **No cycle-budget observation exists.** Neither run spent more than 117 017
  of its 400 000 tokens or got past cycle 2, so the frozen budget has never
  been exercised and nothing here says whether 24 cycles would have sufficed.
- **Accepted does not mean true**, and zero reach does not mean no artifact
  explains a foreign problem. It means no artifact was ever asked.

**Scope kept.** `git diff --stat origin/main -- src/ tests/` is empty; no
production code or test was touched. Three findings are PARKED with
ready-to-send prompts and none was fixed: **P7-reach** (the conjecturer seat
exhausts its repair budget by patching the sibling pointer of the authorized
one — with `epoch1-repair-census.json` establishing that the ledgered
glm-5.2 completion-cap burn did NOT occur: 0 of 41 provider attempts emitted
zero completion tokens), **P8-reach** (the ladder addresses `deepreason
results` with `--root` instead of positionally, so its committed audit
artifact was a path error), and **P9-reach** (the route-lease `max_tokens`
disagreement that ended epoch 2). New read-only tooling committed with the
tranche: `repair_census.py`, `carrier_probe.py`.
