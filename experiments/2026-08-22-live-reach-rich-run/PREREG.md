# PREREG — minting a reach-rich root

Frozen **before any provider call**. Everything recorded here was settled
offline; the only step this document does not cover is the launch itself,
which waits on the operator's credential file.

Map preflight (CLAUDE.md, "Which workflow to use"):
DR-SUB-measures (`measures/reach.py`), DR-SUB-rules (`rules/spawn.py`,
`rules/conj.py`), DR-SUB-workloads (`workloads/text.py`),
DR-CON-warrants-and-attacks (substantive vs structural),
DR-INV-frozen-surfaces (read before designing; nothing here touches one).
Seam read before the subsystems: DR-SEAM-measures-x-rules where it exists;
where it does not, `INDEX.md`'s matrix says so and the two subsystem
documents were read in its place.

## 1. The registered hypothesis

From `experiments/2026-08-21-measure-reach-firing/DIAGNOSIS.md`, verbatim:

> a run whose problems carry at least one subject-substantive
> machine-evaluable criterion that the candidate conjecturer is NOT
> instructed to satisfy will move pairs out of `E4` and produce non-zero
> `reach_set` events.

This tranche tests exactly that and nothing else. The alternatives the
diagnosis already ruled out — thresholds, coverage, the structural filter,
reader resolution, the sweep never being called — are not re-litigated, and
no threshold is lowered anywhere in this tranche.

## 2. What the offline dress rehearsal established BEFORE launch

`rehearsal.py` / `rehearsal.json` (committed 2fc083bb3) put ten
(artifact, foreign problem) shapes through the REAL
`measures/reach.py::reach_sweep`, on real `Harness` roots, with interfaces
compiled by the production `workloads/models.py::compile_interface`. The
result changes what this run can be expected to show, so it is registered
here rather than discovered afterwards.

| scenario | shape | exit |
|---|---|---|
| S1 | seed vs `ra:` — identical criteria | `E3 no-novel` |
| S2 | prose candidate vs wf-carrying seed | `E4 criterion-fail` |
| S3 | two problems, both wf, different subject predicates | **HIT**, 1 `reach_set` |
| S4 | as S3, foreign predicate unsatisfied (control) | `E4` |
| S5 | envelope vs `integ:` `[relation-form]` | `E4` |
| S6 | envelope vs `conn:` (coverage 1/3) | `E4` |
| S7 | envelope vs `disc:` (no criteria) | `E1` |
| S8a | prose `conn:` candidate vs seed, **as shipped** | `E4` |
| S8b | prose `conn:` candidate vs seed, **parked fix P1 applied** | **HIT**, 1 `reach_set` |
| S8c | as S8b, on-form but OFF-SUBJECT candidate (control) | `E4` |

Two structural facts follow, and both are properties of the code, not of
any model's behaviour:

1. **Every problem in a single-seed text run that mints ENVELOPE artifacts
   carries the seed's exact battery.** `rules/conj.py:1462` sets the
   envelope path from whether the problem's own criteria contain
   `reasoning-envelope-wf`; only the seed and the `ra:` problems that copy
   `criteria=parent.criteria` (`rules/spawn.py:104`) do. So for those pairs
   `qualifying - carried` is always empty (S1).
2. **Every other problem in the run mints PROSE, and prose cannot pass
   `reasoning-envelope-wf`.** `conn:`/`integ:`/`disc:` candidates are prose,
   and `reasoning-envelope-wf` sits in the seed problem's QUALIFYING set —
   `programs.PROGRAMS` declares it `class_="structural"`, but
   `measures/reach.py::_STRUCTURAL_PROGRAMS` does not list it, so
   `_substantive` returns True for it. It therefore rejects every prose
   candidate before a single subject criterion is read (S2, S8a).

**Consequence, registered as a prediction of this tranche's own design:**
as the code stands, this run will record ZERO `reach_set` events no matter
how good its subject criteria are. That is not a refutation of the
hypothesis; it is the hypothesis's precondition failing. S8b shows the
hypothesis's condition firing on the first attempt once the *already
parked* defect P1 is applied — and P1 is a TIGHTENING (it stops a
well-formedness gate counting as substantive), never a loosening.

This tranche is READ-ONLY on `src/` and `tests/` by operator instruction,
so P1 is not fixed here. It is reported, with the rehearsal as its
measurement.

## 3. Design, frozen

**Question** (one seed problem, `deepreason-text-workload-v1`):

> Why does the air in a large city stay several degrees warmer than the
> surrounding countryside on a clear, calm night, and what single mechanism
> best explains why that night-time gap is larger in some cities than in
> others?

Chosen because its subject has a tight, checkable vocabulary (the urban
surface energy balance), because a good answer decomposes into overlapping
sub-accounts that the connection/integration cascade will relate, and
because it needs no attached evidence — no dossier is bound, so nothing in
this run depends on a document the model might not read.

**Criteria** — three subject-substantive, machine-evaluable `predicate:`
commitments, plus the `reasoning-envelope-wf` gate `seed_reasoning_workload`
pins unconditionally. Four criteria in total, so qualifying coverage is
1.00 as shipped and 0.75 with P1 applied; both clear `REACH_COVERAGE_MIN`
(0.5), which is left untouched.

| id | what it checks about the SUBJECT |
|---|---|
| `uhi-energy-balance@v1` | names >= 2 distinct terms of the urban surface energy balance (albedo, thermal mass, heat capacity, evapotranspiration, longwave, sky view, anthropogenic heat, latent/sensible heat, emissivity, impervious) |
| `uhi-nocturnal-release@v1` | commits to the diurnal store-and-release asymmetry: says something about NIGHT and about storage/release/retention |
| `uhi-cross-city-modulator@v1` | names a variable that modulates the gap BETWEEN cities and states a direction for it |

These are about the subject, not the artifact's shape. The census's
anti-pattern — `relation_form_commitment()`, a form gate over a corpus-wide
constant expression — is deliberately not imitated: none of the three can be
satisfied by a well-formed document that says nothing about cities, and
`rehearsal.json` S4/S8c are the committed controls for exactly that.

**The experimental condition.** The conjecturer answering the SEED problem
is shown these three predicates verbatim (`llm/packs.py:383` renders
`- <id>: <eval>` for the problem being addressed). The conjecturer answering
any `conn:`/`integ:`/`disc:` problem is shown only that problem's own
criteria and **is never instructed to satisfy the seed's**. That
non-instruction is structural — it is a property of which pack each seat
receives, not of prompt wording — and it is what makes the novelty condition
satisfiable at all.

**Provider.** The committed glm-5.2 profile on Ollama Cloud, solo: every
role on one route, `JUDGE_SEATS_ENABLED: false`, no school seats, no
criticism policy, research backend off. Nothing here needs status-changing
criticism, and the measure is what is under test. Completion cap is raised
to 32 768 tokens against the ledgered known fact that glm-5.2 can burn a
whole cap on hidden reasoning and emit nothing (a typed seat failure, to be
answered by raising the cap, never by diagnosis).

**Budget.** `cycles=24`, `--token-budget 400000`. This is an existence
proof, not an endurance run.

## 4. How this run will be judged — typed outcomes only

Model prose is not evidence. The admissible record is `run-status.json`,
`run-stop.json`, `progress.jsonl`, `log.jsonl`, `verify_root`, and the reach
census.

- **SUCCESS** — the run reaches a typed terminal, `verify_root` reports no
  violations, and the reach census shows `reach_set` Measure events > 0.
  The root is committed and named as Rung 5's gate fixture in RESULTS.md.
- **ZERO reach on one run is NOT a refutation.** Capability-channel and
  spawn behaviour is stochastic across identical runs (ledgered known
  fact). **One repeat is pre-authorised here**, launched from a retired
  root (`git mv run-<id> failed-epoch1-run-<id>`, rename committed FIRST).
- **Zero on both** — the prediction is recorded UNSUPPORTED, both roots are
  committed, and the tranche STOPS. That outcome reopens the Rung 5 design
  question, and the decision is the operator's.
- **Zero attributable to §2** — if the census shows the pairs sitting at
  `E4` with `reasoning-envelope-wf` as the failing criterion, the outcome is
  recorded as PRECONDITION-BLOCKED, distinct from UNSUPPORTED: the
  hypothesis was never exercised, and the P1 tranche is the next step.

The census is the committed tooling from
`experiments/2026-08-21-measure-reach-firing/census.py`, imported rather
than rewritten (`census_new_root.py` is an import shim, not a second
reader).

## 5. Scope

No changes to `src/` or `tests/`. `git diff --stat` against `origin/main`
proves it at delivery. A defect found mid-run is PARKED with a ready-to-send
prompt, never fixed here. No pytest gate is owed for an untouched tree;
`tools/docs_verify.py` runs only if a map document moves, and none should.
