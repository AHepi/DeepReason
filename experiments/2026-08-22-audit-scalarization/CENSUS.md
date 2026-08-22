# The scalarization census — every downstream consumption of an adjudication result

Tranche: `experiments/2026-08-22-audit-scalarization/` · GOAL.md is the authority.
Read-only on `src/` and `tests/`. No sampling, no cap: every enumerated site is
in the table below or in the excluded-with-reason ledger (§6), and §7 proves it
mechanically.

Motivating claim, from `docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md` §2(A)
(operator-supplied, external, unverified here — design intelligence, never
evidence): holding judge, pool, prompts and budget fixed and moving ONLY the
decision rule's position took the same judge from **-10.0 EM below majority
vote** (unconstrained scalar ranking, frozen-rule split, n=30) to **+16.7 EM
above its unconstrained self** (evidence-locked non-compensatory gate). The
note's directed audit: "the moment anything downstream consumes the
adjudication as a ranking, a confidence, or a weighted score, you have rebuilt
the version that scored -10pp."

## 1. The producer boundary, closed by re-derivation

Two commands, both already committed as checks in `docs/map/SUB-adjudication.md`,
fix what the census must cover. Both exit 0 at `2a744325f`:

```
python -c "import pathlib; imp=sorted(str(p) for p in pathlib.Path('src').rglob('*.py') if 'from deepreason.adjudication' in p.read_text() and 'deepreason/adjudication/' not in str(p)); assert imp==['src/deepreason/harness.py','src/deepreason/invariants.py'], imp"
[ "$(grep -rc 'self.state.status = ' src/deepreason/harness.py)" = 1 ]
```

Exactly two modules call the adjudication package, and `Harness._adjudicate`
(`harness.py:2178-2192`) is the sole writer of `state.status`. It writes four
durable fields and nothing else:

| Field | What it is | Adjudication-derived? |
|---|---|---|
| `state.att` | attack edges, `build_att` fixpoint | yes |
| `state.dep` | support edges, `build_dep` | yes (structure, not labels) |
| `state.status` | the four-cell **partition** (`final_labels`) | yes — this IS the verdict |
| `state.conn` | `conn_map(dep, status)` — an int per artifact | yes, and it is the **one scalar the harness itself derives from the partition** |

Every downstream consumption therefore reaches adjudication through one of
those four fields, the `Status` enum, a direct call to an entry point, or the
record wire aliases (`att+`, `dep+`, `status_changed`). Those seven channels are
what `census_sites.py` enumerates.

Two fields that look adjacent and are NOT adjudication output:
`state.hv` — `measures/hv.py` contains no reference to `Status` or `state.status`
at all; and `state.reach` — `measures/reach.py` is *gated* by
`status == ACCEPTED` but its value counts foreign problems whose criteria the
artifact passes, i.e. program verdicts, not labels.

## 2. Scale

```
$ python experiments/2026-08-22-audit-scalarization/census_sites.py --counts
total candidate sites: 261      (a line matching two channels counts twice)
distinct files: 51
distinct (file, line) pairs: 193
```

193 distinct lines, grouped into **110 census rows** below. Zero omitted.

## 3. Verdict per class

| Class | Rows | Verdict |
|---|---|---|
| PRODUCER (excluded from the consumption verdicts, §6) | 8 | — |
| **EVIDENCE/LABEL FEEDBACK** | **0** | **ZERO, as expected by construction.** See §5 for the proof and for the four near-misses, each recorded rather than waved past. |
| **SELECTION-BY-SCORE** | **1** | One finding: `bridge/evidence_pack.py`. See §4. |
| ATTENTION/SCHEDULE | 75 | Lawful (efficiency never evidence). Nine sites convert a label set into a scalar; every one is a **threshold or a conjunctive gate**, except `informal/appellate.py`, which is a compensatory weighted sum and is written up in full. |
| RENDER | 26 | Lawful. No scalar is presented as a verdict anywhere; the display layer actively works against that reading (`status_display.py` renames ACCEPTED to "unrefuted", `views/why.py` tells the operator a status is computed and cannot be set). |

**The claim "grounded is consumed as a partition" survives the census, with one
named exception and four recorded near-misses.** It is now a checked statement
rather than a belief — §7 says how to keep it one.

## 4. FINDING 1 — the delivered evidence pack ranks survivors by a scalar and truncates

`src/deepreason/bridge/evidence_pack.py:744-766`

```python
    for artifact_ref in dict.fromkeys(addressed):
        ...
        status = state.status.get(artifact_ref)
        if status == Status.ACCEPTED:
            accepted.append(artifact_ref)
        elif status == Status.REFUTED:
            refuted.append(artifact_ref)
    accepted.sort(key=lambda ref: (-(state.hv.get(ref, -1.0)), rank[ref]))     # 757
    ...
    for artifact_ref in accepted[:MAX_EVIDENCE_PACK_ITEMS]:                    # 766
```

**What it is.** The ACCEPTED partition is ordered by `hv` — a scalar — and then
truncated. When the survivor count exceeds `MAX_EVIDENCE_PACK_ITEMS`, WHICH
survivors reach the delivered grounded-application evidence pack is decided by a
scalar, not by partition membership plus a typed tie-break.

**What it is NOT, stated first because it is the bigger half.** This is not the
-10pp configuration in its literal form. `hv` is adjudication-INDEPENDENT
(`measures/hv.py` never reads a label), so no adjudication result is being
scalarised here; and the ranking cannot promote across strata — a REFUTED
artifact can never enter the pack at any `hv`. By the source paper's own
criterion ("auxiliary scores rank candidates *within* a feasibility stratum and
can never promote across strata") this ordering is the LAWFUL kind.

**Why it is still a finding.** The truncation is what converts a lawful ordering
into a selection. Three consequences, all mechanical:

1. The `-1.0` default means an **unmeasured survivor sorts below an `hv = 0.0`
   one**. `hv` is a lazy spot-check — `Scheduler._lazy_hv` measures at most one
   artifact per cycle, and only when the run has a `variator` role at all. So a
   survivor's presence in the delivered pack can turn on whether the spot-check
   happened to reach it, which is an attention fact, not an epistemic one.
2. On a run with **no variator seat**, every survivor defaults to `-1.0`, the
   sort degenerates to `rank[ref]` (registration order), and the cap silently
   keeps the earliest-registered survivors. That is a typed tie-break and is
   fine — but it is fine by accident of the measure being absent, not by design.
3. Nothing in the record says a truncation happened. `refuted[:MAX…]` at line 849
   has the same shape.

**Severity: MEDIUM.** It touches what an answer *shows*, never what the record
*says*. The partition is intact in `state.status`, in `findings.py`, in
`run-result.json` and in `verify_root`; only the bridge's pack is affected.

Parked prompt: `PARKED.md` §P1.

## 5. EVIDENCE/LABEL FEEDBACK — count ZERO, and why

**Structural proof.** `docs/map/SUB-adjudication.md` carries two committed checks
that between them close this off: the package's entire import surface is
`deepreason.ontology` plus itself, and no `provenance|school|pareto|novelty|hv|
reach|measure` word appears anywhere in `edges.py`, `grounded.py`, `support.py`.
Labels are a pure function of `(artifacts, warrants, commitments, carries)`. No
scalar can enter label computation directly.

**The remaining route** would be a scalar steering **warrant minting**. Seven
modules construct a `Warrant(`; exactly three of them also read adjudication
output:

| Warrant-minting module | Reads adjudication? | Shape of the read |
|---|---|---|
| `imports.py`, `informal/trial.py`, `ontology/warrant.py`, `rules/warrants.py` | **no** — zero enumerated sites | — |
| `rules/experiment.py` | yes | partition membership as a filter and as a BOOLEAN sort key (row 302) |
| `rules/relatedness.py` | yes | partition membership of a *different* artifact (row 78) |
| `rules/vision.py` | yes | partition membership excluding refuted screenshots (row 38) |

Notably `rules/crit.py` — the criticism source, `DR-CON-criticism-source`, the
module that mints argumentative attacks — has **zero** enumerated sites. It
never reads a label.

**FEEDBACK-PROXIMITY ledger.** Four sites where adjudication output reaches
admission, protection or verdict authority. Each is recorded because "no scalar"
is the reason each stays lawful, and that reason is exactly what a future change
could remove:

| # | Site | Reaches | Shape | Why it is not a hit |
|---|---|---|---|---|
| N1 | `rules/relatedness.py:78` | prose-immunity for a commitment (`formally_backed`) | partition membership of the relatedness-CLAIM artifact | A label, not a number, and never the conjecture's own label — "the shield falls, the artifact doesn't" (R43). Refuting the claim removes the shield by derivation, which is reinstatement working correctly. |
| N2 | `rules/experiment.py:302` | promotion of a proposed property to a criterion with kill authority | boolean sort key `status != ACCEPTED`, then `[:8]` | The ordering decides which carriers are executed to find a witness; the witness itself is a real sandbox run. A label orders the search, it never substitutes for the verdict. The cap of 8 is what makes the order matter. |
| N3 | `rules/vision.py:38` | the images a vision critic sees before minting a warrant | `status == REFUTED` exclusion | Evidence selection: a refuted screenshot is not evidence. Oldest-first, capped, no score. |
| N4 | `rules/guards/anti_relapse.py:293-389` | ADMISSION of a candidate | `status == REFUTED` (hash block); standing-refuter set from `att` + `status` | Blocks only relapse onto refuted-equivalents (§0), and the escape hatch is a typed warrant against the prior's refuter — not a higher score. |

**Verdict: 0 EVIDENCE/LABEL FEEDBACK sites.** The forbidden shape does not occur.

## 5b. The scalar conversions inside ATTENTION/SCHEDULE, listed in full

The directive asked that every site converting a label set into a scalar be
noted even when lawful. There are nine. Eight are thresholds or conjunctions;
one is a compensatory sum.

| Site | Scalar built from labels | How it is consumed | Compensatory? |
|---|---|---|---|
| `scheduler/scheduler.py:1078` → `1134` | `survivors_by_problem` count → binary weight 1.0 / 0.3 | multiplied into `-(age*weight)`, the first element of the LIVENESS_QUEUE rank key | **yes** — an older solved problem can outrank a younger unsolved one. Only membership enters, never the count. The operator-seed guarantee is at key position 2, i.e. a tie-break under this product, exactly as `CON-scheduler-ranking.md` states. The round-robin path (`1150`) is the same guarantee with no scalar at all. |
| `scheduler/scheduler.py:2749` | `status_churn` (labels that moved this cycle) | `stop.py:165` `<= status_churn_max`, ANDed with `frontier_delta`, `new_problems`, `new_admissions`, `criticism_debt` | no — five independent thresholds, conjunctive |
| `scheduler/scheduler.py:2745` | `new_admissions` count | `stop.py:167` `<= new_admission_max` | no |
| `capture/detection.py:166-189` | `criticism_debt` ratio | `stop.py:172` `<= criticism_debt_max` | no |
| `capture/detection.py:189` | `validity_attack_rate`, `reinstatement_rate` | report only | n/a |
| `measures/attention.py:35` | `attack_target_entropy` | a scheduler diagnostic line and reports | n/a |
| `unification/isolation.py:57` → `71` → `rules/spawn.py:154` | `conn` count → `iso` | `iso(...) > 0` → spawn a CONNECTION problem | no — threshold |
| `premises.py:463` | count of REFUTED artifacts on a problem | `refuted >= after` → raise the question-the-problem prompt | no — threshold |
| `compat_eval.py:335` | `attack_validity_rate` | `threshold_verdict` per metric, four-state, no composite total | no |
| `informal/appellate.py:43` | `+2` per unresolved rivalry (≥2 ACCEPTED rivals) | **added** to ensemble-split 3, audit-hit 2, guard-block 1 → `sorted(-score, case)` → `[:USER_RULINGS_BUDGET]` | **yes** |

**`informal/appellate.py::docket` is the closest thing in this codebase to the
-10pp shape** and deserves its paragraph. A label-derived term is summed with
non-adjudication terms into one total that decides which cases reach the user's
scarce ruling budget — a compensatory scalar over a set that includes an
adjudication result. It stays lawful for three reasons, all of which a future
change could remove: the docket allocates ATTENTION only; the user's ruling is
an independent input that registers as an ordinary attackable artifact whose
"pack ordering is the only authority a user ruling has (N1: never status
privilege)" (`informal/standards.py:88-91`); and its sole caller is
`cli/main.py:1238`, an operator-facing queue, not an autonomous loop. Recorded
as a finding-grade note, not a FINDING. Parked prompt: `PARKED.md` §P2.

## 5c. What the census confirms, positively

Four claims that were assumed and are now checked:

1. **The allocation signal contract holds from the consumer side.**
   `controller.py` contains **zero** references to `Status` or `state.status`; it
   reaches the graph only through two BOOLEAN readers,
   `allocation.policy_is_authorized` / `policy_is_contested`
   (`controller.py:348,508,556`). Interface-only consumption, verified where it
   matters — at the consumer. `INV-signal-contract`'s "allocation touches
   EFFICIENCY NEVER EVIDENCE" is upheld and no scalar crosses that boundary.
2. **The results surface's best-candidate selection is the lawful model.**
   `easy.py::pick_survivor` (live at `workflows/website.py:1324,1351,1652,1728`)
   picks the promoted stage artifact by partition membership plus a purely typed
   tie-break `(event_seq, aid)` — earliest wins, "the longest-standing survivor
   has faced the most re-criticism sweeps". No score of any kind. This is what
   the operator's seed tie-break law looks like applied to artifacts.
3. **The Pareto frontier cannot scalarise.** `run_report` builds `survivors` from
   the partition FIRST, then `capture/pareto.py::frontier` applies strict
   domination over (hv, reach, coverage) — no axis is summed, so no measure can
   promote a REFUTED artifact into the frontier. Partition, then within-stratum
   ordering that cannot cross strata: the paper's own lawful configuration.
4. **The findings surface refuses to name a winner.** `findings.py:119-126`
   emits, verbatim: "Where they answer the same question differently they are
   unresolved rivals: the record deliberately preserves the disagreement rather
   than merging it."

## 6. Excluded, with reason (nothing is silently dropped)

Eight rows are marked PRODUCER and carry no consumption verdict: the three
adjudication logic modules (they build the graph and the labels), the four
`harness.py` groups that call them and write / diff the result, and
`ontology/event.py`'s `StateDiff` wire aliases (a record format, not a reader).
`unification/isolation.py:57-68` (`conn_map`) is producer-side too: it is called
by `Harness._adjudicate` itself. They are listed in the table so the exclusion is
visible rather than a filter.

No other exclusion exists. There is no sampling, no top-N, no "representative
files".

## 7. Closure, checkable

```
python experiments/2026-08-22-audit-scalarization/census_sites.py --check
```

Re-runs the enumerator and reconciles it line-by-line against the table in this
file: every distinct `(file, line)` the enumerator flags must be cited by exactly
one row, and no row may cite the same line twice. Exit 0 means the census still
covers everything the producer channels reach. It is the instrument that makes
"no sampling" a checked statement rather than an assurance.

**Where a regression test could pin the claim.** The census is a snapshot; the
property it establishes is not self-maintaining. The cheapest pin, in order of
value:

1. A test asserting `src/deepreason/controller.py` contains no `Status` /
   `state.status` reference — pins §5c(1) directly, one grep, cannot pass
   vacuously.
2. A test asserting `rules/crit.py` has zero adjudication reads — pins the
   central "criticism does not read labels" property.
3. A test over `capture/pareto.py::frontier` asserting no axis combination can
   place a non-survivor in the frontier — pins §5c(3).
4. Running `census_sites.py --check` in the gate would pin the whole census, at
   the cost of a table that must be edited whenever a status read is added. That
   is a real maintenance tax and is offered as an option, not a recommendation.

None of these are written by this tranche: it is read-only on `src/` and
`tests/` by operator instruction.

## 8. The census table

Ordered: PRODUCER, then EVIDENCE/LABEL FEEDBACK (empty), then
SELECTION-BY-SCORE, then ATTENTION/SCHEDULE, then RENDER.

| # | Site (`src/deepreason/…`) | Lines | What is consumed | What it becomes downstream | Class | Note |
|---|---|---|---|---|---|---|
| 1 | `adjudication/edges.py` | 46,56,81 | artifacts/warrants/commitments/carries | the `att` and `dep` edge sets, and the toposort order | **PRODUCER** | Produces the graph. Not a consumption site. |
| 2 | `adjudication/grounded.py` | 13,26,29 | nodes + `att` | the grounded extension and the three pass-1 strings | **PRODUCER** | Kleene fixpoint. The partition is born here. |
| 3 | `adjudication/support.py` | 15,25,26,28,30,32,34 | pass-1 strings + `dep` | the four `Status` values | **PRODUCER** | The only producer of `Status` in the codebase (SUB-adjudication.md). |
| 4 | `harness.py` | 516 | candidate artifacts | `WellFormednessError` if `dep` is not a DAG | **PRODUCER** | Pre-adjudication well-formedness refusal at `register_batch`; no label exists yet. |
| 5 | `harness.py` | 2056,2057,2058 | `state.att`/`dep`/`status` before the event | the per-event `StateDiff` baseline | **PRODUCER** | Snapshot taken inside `_apply_event` for the diff it will emit. |
| 6 | `harness.py` | 2161,2162,2166,2180,2186,2187,2188,2189,2191,2192 | the freshly computed graph and labels | `state.att`/`dep`/`status`/`conn` and the `att+`/`dep+`/`status_changed` log keys | **PRODUCER** | `Harness._adjudicate` — the sole writer of `state.status`; the durable trace. |
| 7 | `ontology/event.py` | 319,320,346 | the `StateDiff` field names | the wire aliases `att+`, `dep+`, `status_changed` on every log line | **PRODUCER** | Record format, not a reader. Frozen surface. |
| 8 | `unification/isolation.py` | 57,65 | `dep` edges + `status` | `conn`: an int per artifact, written by `_adjudicate` | **PRODUCER** | `conn_map` is called by `Harness._adjudicate`; the ONE scalar the harness itself derives from the partition. |
| 9 | `bridge/evidence_pack.py` | 757-766 (no enumerated line; reached from 755) | the ACCEPTED list built at 752-755 | `accepted.sort(key=(-hv, registration_rank))` then `accepted[:MAX_EVIDENCE_PACK_ITEMS]` -> `survivor_candidates` -> the delivered evidence pack | **SELECTION-BY-SCORE** | **FINDING 1.** See CENSUS.md section 4. |
| 10 | `allocation.py` | 16,31 | the spelling of contestation (`REFUTED`, `SUSPENDED_UNSUPPORTED`) | `_CONTESTED`, and the module docstring's statement of the signal contract | **ATTENTION/SCHEDULE** | This is where the signal contract localises the graph vocabulary so `controller.py` never learns it. |
| 11 | `allocation.py` | 197,208 | `status` of the controller's OWN policy artifact | two BOOLEAN signals: `allocation.policy-authorized.v1`, `allocation.policy-contested.v1` | **ATTENTION/SCHEDULE** | **Signal-contract claim VERIFIED from the consumer side**: `controller.py` contains ZERO references to `Status` or `state.status` and reaches the graph only through these two booleans (`controller.py:348,508,556`). Interface-only consumption holds. No scalar crosses the boundary. |
| 12 | `calculus/separation.py` | 81 | `state.att` + `state.dep` as one edge list | the connected component `Comp_L(x)` (Def 7.1) | **ATTENTION/SCHEDULE** | Graph structure read as structure; no label value enters. |
| 13 | `calculus/standing.py` | 156,163 | `status is not ACCEPTED` on a frame assertion | `Consultability(False, …)` — the assertion stops being consulted | **ATTENTION/SCHEDULE** | 'final(fa) = unrefuted. This one clause is the whole of revocation' — derivation, no revocation path and no score. |
| 14 | `calculus/views.py` | 76 | `status` of a problem's subject artifact | the typed diagnostic `problem_subject_status` | **ATTENTION/SCHEDULE** | A label handed through unchanged. |
| 15 | `capture/atlas.py` | 27,28 | `status == REFUTED` | the RefutedIndex the relapse gate embeds against | **ATTENTION/SCHEDULE** | Membership filter; `nearest` ranks by embedding distance (adjudication-independent) with a deterministic tie-break. |
| 16 | `capture/detection.py` | 166,167,189 | `status == ACCEPTED`; `state.att` vs validity nodes | `criticism_debt` ratio, `validity_attack_rate`, `attack_target_entropy`, churn/reinstatement counts | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted. `criticism_debt` alone reaches a decision: `StopMetrics.criticism_debt` -> `stop.py:172` `<= criticism_debt_max`, conjunctive with the others. The rest are report-only (see RENDER rows). |
| 17 | `capture/detection.py` | 247 | `status == REFUTED` | excluded from the observation-grounding coverage ratio | **ATTENTION/SCHEDULE** | Gate inside a diagnostic; docstring: 'Diagnostic / attention only — never a status input (§0).' |
| 18 | `capture/ladder.py` | 51,52 | `status == ACCEPTED` and carries commitments | which artifacts the adjudication-ritual debt sweep re-criticises | **ATTENTION/SCHEDULE** | Intervention targeting; the sweep runs real criticism, which is what decides labels. |
| 19 | `capture/schools.py` | 124 | `status == ACCEPTED` + foreign school | crossover exemplars shown to a reseeded school, top-k by newest event_seq | **ATTENTION/SCHEDULE** | Pack shaping. Docstring: 'Attention only — pack shaping, never status (D2).' Typed tie-break (`-event_seq, aid`); cap `k`. |
| 20 | `compat_eval.py` | 335,341 | `status == ACCEPTED` on warrant carriers and on addressed artifacts | `attack_validity_rate` (standing attackers / attackers) and `survivor_hv_mean` | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted: an adjudication-derived RATE gates provider/config eligibility. Non-compensatory — `threshold_verdict` is applied per metric with a four-state outcome, and no composite total exists. Selects a MODEL PROFILE, never a conjecture. |
| 21 | `easy.py` | 949 | `status == ACCEPTED` + role in (conjecturer, synthesizer) over a problem family | `pick_survivor` — the PROMOTED artifact for a website pipeline stage (`plan_id`, `design_id`, the repaired component) | **ATTENTION/SCHEDULE** | **The census's model of a lawful best-candidate selection.** Partition membership, then a purely typed tie-break `(event_seq, aid)` — earliest wins. No score of any kind. Live: `workflows/website.py:1324,1351,1652,1728`. |
| 22 | `informal/appellate.py` | 43 | count of `status == ACCEPTED` rivals on a DISCRIMINATION problem | `bump(problem.id, 'unresolved-rivalry', 2)` — +2 into a summed `score`, then `sorted(-score, case)` and truncated to `USER_RULINGS_BUDGET` | **ATTENTION/SCHEDULE** | **The sharpest scalar conversion in the census** and the closest thing to the -10pp shape. A label-derived term is ADDED to non-adjudication terms (ensemble-split 3, audit-hit 2, guard-block 1) in one compensatory total that decides which cases reach the user's scarce ruling budget. It stays lawful because the docket allocates ATTENTION only — the user's ruling is an independent input and registers as an ordinary attackable artifact whose 'pack ordering is the only authority' (informal/standards.py). Sole caller is `cli/main.py:1238` (an operator-facing queue), not an autonomous loop. Recorded as a finding-grade note, not a FINDING. |
| 23 | `informal/standards.py` | 94 | `status == ACCEPTED` on precedent artifacts | top-k precedent slice, user rulings ranked first | **ATTENTION/SCHEDULE** | Partition + typed order + cap `k`. Docstring: 'pack ordering is the only authority a user ruling has (N1: never status privilege).' |
| 24 | `jolts.py` | 278,288 | `status == REFUTED` (target) / `== ACCEPTED` (lineage) | typed refusal `JOLT_REFUTED_TARGET_REQUIRED`; the suppressible-exemplar set | **ATTENTION/SCHEDULE** | Partition membership as a typed precondition; suppression is pack shaping. |
| 25 | `jolts.py` | 310,316 | `status != REFUTED` / `!= ACCEPTED` | typed refusals `JOLT_REFUTED_TARGET_REQUIRED`, `JOLT_SUPPRESSED_EXEMPLAR_NOT_ACCEPTED` | **ATTENTION/SCHEDULE** | Validation of a jolt action; refusals, not scores. |
| 26 | `llm/packs.py` | 139 | `status == ACCEPTED` on `code:python-prop` artifacts | the ACTIVE PROPERTIES section of the conjecturer pack | **ATTENTION/SCHEDULE** | Generation content. 'presentation only (§9); the checkers still decide everything.' |
| 27 | `llm/packs.py` | 425,426 | `status == ACCEPTED`, minus suppressed exemplars | the neighbourhood section: lineage-first then state insertion order, sliced to `neighbourhood_n` | **ATTENTION/SCHEDULE** | Partition + positional slice. No score. Operator law: seats change how content is GENERATED, never what counts as EVIDENCE. |
| 28 | `llm/packs.py` | 634,638 | `sorted(state.att)` filtered to the target; `status` of each attacker | the STANDING ATTACKS block of the criticism pack, capped at `ATTACKERS_N` | **ATTENTION/SCHEDULE** | Lexical order + cap; the label is rendered as a label. |
| 29 | `llm/packs.py` | 914,918 | same, single-target variant | the STANDING ATTACKS suffix | **ATTENTION/SCHEDULE** | Same shape. |
| 30 | `loop.py` | 32 | `status != ACCEPTED` after program criticism | skip the argumentative call | **ATTENTION/SCHEDULE** | 'Budget triage (attention, never status §0)'. |
| 31 | `measures/attention.py` | 35 | `state.att` targets | `attack_target_entropy`, a dispersion scalar | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted. Consumers: a scheduler diagnostic line (2303) and reports. Never a rank key, never a gate. |
| 32 | `measures/reach.py` | 108,109 | `status == ACCEPTED` | gates which artifacts are swept for cross-problem survival; the resulting count becomes `state.reach` | **ATTENTION/SCHEDULE** | The partition gates the DOMAIN; the reach VALUE is the number of foreign problems whose criteria the artifact passes — program verdicts, not labels. Recorded via `record_measure`. |
| 33 | `ontology/problem.py` | 35 | the CONNECTION trigger's documented condition `iso(a) > 0` | the SpawnTrigger vocabulary | **ATTENTION/SCHEDULE** | Documentation of the gate. |
| 34 | `premises.py` | 191 | `status != ACCEPTED` on an attribution artifact | whether the attribution is CONSULTED | **ATTENTION/SCHEDULE** | Partition membership; a refuted attribution stops counting, which releases a problem by derivation. |
| 35 | `premises.py` | 208 | `status != ACCEPTED` on a resolution artifact | whether the resolution is CONSULTED | **ATTENTION/SCHEDULE** | Same shape; attacking a retirement returns its problem to the frontier (N1). |
| 36 | `premises.py` | 227,228,230 | `status` of a premise artifact (REFUTED / SUSPENDED_UNSUPPORTED) | the problem's premise MARK (refuted / unaccredited) | **ATTENTION/SCHEDULE** | A typed label -> a typed mark, derived lazily. No number in the path; a marked problem yields to unmarked work of the same age in `_select_problem`. |
| 37 | `premises.py` | 463 | count of `status == REFUTED` artifacts addressing a problem | `refuted >= after` -> raise the question-the-problem prompt | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted: a label COUNT thresholded. Docstring is explicit that 'nothing is ranked on whether an attribution exists.' |
| 38 | `research/backends.py` | 208 | `status == ACCEPTED` on evidence artifacts | whether a research problem is COVERED | **ATTENTION/SCHEDULE** | Partition membership decides coverage; refuted or orphaned evidence re-arms research by derivation. |
| 39 | `research/backends.py` | 217,218 | `status not in (REFUTED, SUSPENDED_UNSUPPORTED)` | whether research is scheduled-PENDING rather than failed | **ATTENTION/SCHEDULE** | Gate. |
| 40 | `rules/act.py` | 60 | `status == ACCEPTED` on a browser-evidence import | whether that evidence payload is read | **ATTENTION/SCHEDULE** | Gate. |
| 41 | `rules/experiment.py` | 92,96 | `status == ACCEPTED` (twice, around `_oracle_ready`) | the accepted-generator list for a property oracle | **ATTENTION/SCHEDULE** | Membership filter in state insertion order; the double read is deliberate (a retry can mint a fail warrant in between). |
| 42 | `rules/experiment.py` | 120 | `status != ACCEPTED` | the CANDIDATE heads shown to a directed experimenter, capped at `cap` | **ATTENTION/SCHEDULE** | Generation content. 'Presentation only (§9): the gate and checker still decide everything.' |
| 43 | `rules/experiment.py` | 172,174 | `status == ACCEPTED` after `crit_program` | whether a freshly minted generator counts as a survivor | **ATTENTION/SCHEDULE** | Gate. |
| 44 | `rules/experiment.py` | 202,206 | `status == ACCEPTED` | the ACTIVE-properties list | **ATTENTION/SCHEDULE** | Membership filter; a refuted property drops out and its verdicts collapse by the edges.py source-artifact closure — derivation, not bookkeeping. |
| 45 | `rules/experiment.py` | 256 | `{target for _,target in state.att}` | attack-survival term of the promotion test | **ATTENTION/SCHEDULE** | Graph structure read as a set-membership predicate, not a count. |
| 46 | `rules/experiment.py` | 302 | `status != ACCEPTED` as a BOOLEAN sort key | `accepted_first = sorted(carriers, key=…)`, then `accepted_first[:8]` are executed to find a promotion WITNESS | **ATTENTION/SCHEDULE** | FEEDBACK-PROXIMITY (see ledger). Partition membership orders which carriers are tried, and the cap of 8 makes that order consequential for whether a proposed property is PROMOTED to a criterion with kill authority. The key is a boolean, not a scalar, and the witness itself is a real sandbox execution — a label never substitutes for the verdict. |
| 47 | `rules/experiment.py` | 493,495 | `status != ACCEPTED` after `crit_program` | whether a proposed checker proceeds to the arrival crash probe | **ATTENTION/SCHEDULE** | Gate. |
| 48 | `rules/guards/anti_relapse.py` | 293,296 | `status == REFUTED` for the candidate id | stage-1 hash block: refuse relapse onto a refuted artifact | **ATTENTION/SCHEDULE** | Admission gate on partition membership. Blocks ONLY relapse (§0). |
| 49 | `rules/guards/anti_relapse.py` | 321,389 | `state.att` + `status == ACCEPTED` of a prior's attackers | the standing-refuter set a candidate must carry a warrant against to be admitted anyway | **ATTENTION/SCHEDULE** | Partition membership as an admission predicate; the escape hatch is a typed warrant, not a score. |
| 50 | `rules/relatedness.py` | 78 | `status == ACCEPTED` on a RELATEDNESS-CLAIM artifact | whether `formally_backed` still grants prose-immunity to a commitment | **ATTENTION/SCHEDULE** | FEEDBACK-PROXIMITY (see ledger): adjudication output reaches a PROTECTION decision. Shape is partition membership of a different artifact, adjudicated by the same rules — 'the shield falls, the artifact doesn't' (R43). No scalar, and never the conjecture's own label. |
| 51 | `rules/spawn.py` | 9,49 | the `status` map | the spawn sweep's local alias | **ATTENTION/SCHEDULE** | Agenda construction only; spawn mints problems, never labels. |
| 52 | `rules/spawn.py` | 74 | `status == ACCEPTED` per problem | `>=2 surviving rivals` -> a DISCRIMINATION problem | **ATTENTION/SCHEDULE** | Count thresholded to a gate; the rivals list is sorted lexically. |
| 53 | `rules/spawn.py` | 92 | `status == ACCEPTED` AND `hv < ra_floor` | a REMOVE_ARBITRARINESS problem | **ATTENTION/SCHEDULE** | Conjunctive gate. `hv` is adjudication-INDEPENDENT (`measures/hv.py` never reads a label). |
| 54 | `rules/spawn.py` | 109 | `status == ACCEPTED` AND `reach > 0` | an EXPLANATION_DEBT problem | **ATTENTION/SCHEDULE** | Conjunctive gate. `reach` is partition-GATED but not label-valued (see `measures/reach.py` row). |
| 55 | `rules/spawn.py` | 152,154 | `status == ACCEPTED` AND `iso(aid, conn, FLOOR) > 0` | a CONNECTION problem | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted: `conn` is the harness's own label-derived count and `iso` compares it to a fixed FLOOR. Threshold, never a rank. |
| 56 | `rules/spawn.py` | 180 | `status == REFUTED` | skip research spawn for a refuted artifact | **ATTENTION/SCHEDULE** | Gate. |
| 57 | `rules/spawn.py` | 197,198 | `status == ACCEPTED` over addressed artifacts | INTEGRATION problem candidates (pairwise, no declared relation) | **ATTENTION/SCHEDULE** | Membership filter; pair enumeration is positional. |
| 58 | `rules/vision.py` | 38 | `status == REFUTED` on a screenshot | exclude it from the images shown to the vision critic | **ATTENTION/SCHEDULE** | Evidence selection gated by the partition, oldest-first, capped at `_MAX_SCREENSHOTS`. The vision critic mints warrants; see the FEEDBACK-PROXIMITY ledger. |
| 59 | `scheduler/scheduler.py` | 1078 | `status == ACCEPTED` per addressed artifact, minus IMPORT-role records | `survivors_by_problem`: a COUNT per problem | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted per the directive. The count is built but never used as a magnitude — see the two rows below, which are its only readers. |
| 60 | `scheduler/scheduler.py` | 1134-part | `survivors_by_problem` truthiness (has any survivor / has none) | the aging weight 1.0 or 0.3, multiplied into `-(age*weight)` — the first element of the LIVENESS_QUEUE rank key | **ATTENTION/SCHEDULE** | The one site where an adjudication label set becomes a term in a COMPENSATORY scalar: an older solved problem can outrank a younger unsolved one. Lawful (efficiency, never evidence) and bounded — only membership enters, never the count. The operator-seed guarantee sits at key position 2, so it is a TIE-break under this product, exactly as `CON-scheduler-ranking.md` states. |
| 61 | `scheduler/scheduler.py` | 1150-part | `survivors_by_problem` truthiness | the round-robin pool: unsolved problems first, then a typed 3-tuple tie-break (seed, orphaned, reflexive) | **ATTENTION/SCHEDULE** | The LAWFUL twin of the row above: strict partition + typed tie-break, no scalar at all. Same guarantee, two shapes. |
| 62 | `scheduler/scheduler.py` | 1204 | `status(artifact) == ACCEPTED` after program criticism | whether the deterministic fuzz pass runs | **ATTENTION/SCHEDULE** | Budget triage gate. |
| 63 | `scheduler/scheduler.py` | 1236 | `status(target) != ACCEPTED` | skip the rubric trial for an already-felled target | **ATTENTION/SCHEDULE** | Budget triage gate; comment says so. |
| 64 | `scheduler/scheduler.py` | 1285 | `status != ACCEPTED or aid in attacked` | the standing-recriticism pool | **ATTENTION/SCHEDULE** | Membership filter; ordering within it is by execution-oracle carriage and state insertion order, not a score. |
| 65 | `scheduler/scheduler.py` | 1336 | `status != ACCEPTED` | argumentative-criticism eligibility | **ATTENTION/SCHEDULE** | Budget triage gate. |
| 66 | `scheduler/scheduler.py` | 1363 | `status != ACCEPTED` after fuzz | drop from the recrit pool | **ATTENTION/SCHEDULE** | Gate; the pool is rotated by a cursor, not ranked. |
| 67 | `scheduler/scheduler.py` | 1432 | `status != ACCEPTED` | foreign-criticism target eligibility | **ATTENTION/SCHEDULE** | Membership filter. |
| 68 | `scheduler/scheduler.py` | 1982 | `status(rival) == ACCEPTED` | the two rivals handed to a pairwise discrimination trial | **ATTENTION/SCHEDULE** | Partition membership then `[:2]` in `provenance.from_` order — a typed positional tie-break, no score. |
| 69 | `scheduler/scheduler.py` | 2394,2412 | `status != ACCEPTED` | fuzz-sweep eligibility and the `_fuzz_clean` cache | **ATTENTION/SCHEDULE** | Gate. |
| 70 | `scheduler/scheduler.py` | 2528 | `status != ACCEPTED` | browser-evidence eligibility | **ATTENTION/SCHEDULE** | Gate under `BROWSER_PER_CYCLE`. |
| 71 | `scheduler/scheduler.py` | 2564 | `status != ACCEPTED` | vision-criticism eligibility | **ATTENTION/SCHEDULE** | Gate under `VISION_CRIT_PER_CYCLE`. |
| 72 | `scheduler/scheduler.py` | 2682,2684 | `status == ACCEPTED` and unmeasured | which artifact gets the one HV spot-check this cycle | **ATTENTION/SCHEDULE** | Gate; first match in state insertion order wins. Explicitly 'attention-only machinery, so skipping is legal'. |
| 73 | `scheduler/scheduler.py` | 2745 | `status == ACCEPTED` over addressed artifacts | `_stop_snapshot()['admissions']` | **ATTENTION/SCHEDULE** | Feeds the stop controller (next row). |
| 74 | `scheduler/scheduler.py` | 2749 | `dict(state.status)` verbatim | `_stop_snapshot()['statuses']`, differenced across a cycle into `status_churn` | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted. `status_churn` = count of artifacts whose label moved; with `frontier_delta` and `new_admissions` it reaches `runtime/stop.py`. Each is compared against its OWN threshold, conjunctively (`stop.py:164-172`, `197-200`) — a non-compensatory gate, never a weighted sum. A quiet churn cannot be compensated by a busy frontier. |
| 75 | `skills/distill.py` | 73 | `status == REFUTED` (or critic role) | the negative n-gram set a distillation must avoid | **ATTENTION/SCHEDULE** | Membership filter over refuted content. |
| 76 | `skills/validate.py` | 48,152 | `status != ACCEPTED` on the distillation source and its dependency closure | `DistillationSourceError` — a typed refusal | **ATTENTION/SCHEDULE** | Admission gate on partition membership; refuses rather than downweights. |
| 77 | `unification/isolation.py` | 4,6 | docstring statement of `conn`/`iso` | the §7 L2 contract | **ATTENTION/SCHEDULE** | Documentation of the gate, not a site. |
| 78 | `unification/isolation.py` | 71 | `conn` (label-derived count) | `iso = max(0, FLOOR - conn)`, read only as `> 0` by `rules/spawn.py` | **ATTENTION/SCHEDULE** | SCALAR CONVERSION, noted. Its sole consumer thresholds it; nothing ranks on `iso`. |
| 79 | `unification/isolation.py` | 90 | `status == ACCEPTED` | the candidate pool for `rank_neighbours`, then top-K by overlap | **ATTENTION/SCHEDULE** | Partition gates the pool; the ranking scalar (shared problem > shared refs > lexical overlap) is adjudication-INDEPENDENT. Selects a problem's neighbourhood, never a winner. Cap: `config.K`, declared. |
| 80 | `verification/report.py` | 1074 | `state.att` emptiness | the `adjudication-blindness` epistemic finding | **ATTENTION/SCHEDULE** | A detector the adjudication package structurally cannot host. Advisory: it does not gate `valid`. |
| 81 | `views/jolt_signals.py` | 458 | `status(target) == REFUTED` | the `refuted_attractor_present` boolean in the hard-orbit trigger | **ATTENTION/SCHEDULE** | Enters a pure conjunction (`sufficient and blocks>=… and concentration>=… and refuted and not improvements`) — no weight, no sum. |
| 82 | `workflows/website.py` | 457 | `status != ACCEPTED` on referenced checkpoint artifacts | `WebsiteCheckpointError('CHECKPOINT_FOUNDATION_INVALID')` | **ATTENTION/SCHEDULE** | Typed refusal on partition membership. |
| 83 | `workflows/website.py` | 1254,1273 | `status == ACCEPTED` after criticism | whether the compact-path artifact is returned at all (else `None`) | **ATTENTION/SCHEDULE** | Gate. |
| 84 | `workflows/website.py` | 1630 | `status(design_id) == REFUTED` | which typed terminal code is emitted (`IMPORT_PLAN_REFUTED` vs `IMPORT_RESOLUTION_DEFERRED`) | **ATTENTION/SCHEDULE** | A label selects a diagnostic code. |
| 85 | `application/results.py` | 10 | (docstring) the composition rule | `deepreason results` delegates status counts to `findings_summary` rather than walking `state.status` twice | **RENDER** | The one typed-outcome reader; writes nothing. `survivor_count` is a COUNT, never a pick. |
| 86 | `application/text_runs.py` | 378 | `display_status_counts(harness, manifest)` | the `display.status_counts` block of `run-result.json` | **RENDER** | Counts. |
| 87 | `application/text_runs.py` | 1386 | `state.status.values()` | per-cycle progress counts | **RENDER** | Counts. |
| 88 | `bridge/evidence_pack.py` | 626 | `status == ACCEPTED` on evidence artifacts addressing the family | admission of an evidence item (plus its source lineage) to the catalog | **RENDER** | Partition membership; 'neither role nor a reference silently upgrades their status.' |
| 89 | `bridge/evidence_pack.py` | 741,752,753,755 | `state.att`; `status` ACCEPTED / REFUTED over addressed conjecturer/synthesizer artifacts | the survivor / refutation / open-rivalry sections of the grounded-application evidence pack | **RENDER** | See the SELECTION row below for the ordering that follows — the partition itself is rendered whole (rivalries are emitted as rivalries, `>=2` accepted rivals, unresolved). |
| 90 | `cli/main.py` | 1276 | `status` of a freshly submitted evidence artifact | the console line '(accepted) … coverage is derived under criticism' | **RENDER** | Rendering. |
| 91 | `findings.py` | 109,110,112 | `status` ACCEPTED / REFUTED per claim-bearing artifact | the 'Positions the record accepts' / 'refuted' sections of FINDINGS.md | **RENDER** | **Rivals are preserved, not merged**: 'Where they answer the same question differently they are unresolved rivals: the record deliberately preserves the disagreement rather than merging it.' No winner is named. |
| 92 | `findings.py` | 305,312,314,316 | `status` per artifact | `findings_summary()['positions']` bucketed by label, plus `rivalries` | **RENDER** | A partition rendered as a partition; rivalries are reported with a `rival_count`, never resolved. |
| 93 | `findings.py` | 336 | `state.att` | the refutation-attribution list (who attacked what) | **RENDER** | Edges rendered as edges. |
| 94 | `harness.py` | 1961,1965 | `shadow.state.status` before/after each event | `Harness.transitions()` — the (seq, artifact, old, new) label-transition stream | **RENDER** | The incremental shadow that makes churn/reinstatement readable without a quadratic rewalk. Consumed by `capture/detection.py` as counts. |
| 95 | `invariants.py` | 4041 | `status != ACCEPTED` | which artifacts the foreign-criticism coverage check applies to | **RENDER** | Verification scope, re-derived read-only. |
| 96 | `invariants.py` | 4070,4074,4081 | `state.att` endpoints; `build_dep`/`toposort` re-derivation | `att-endpoints` and `dep-dag` replay-validation failures | **RENDER** | `verify_root` re-derives rather than trusting the recorded graph. |
| 97 | `invariants.py` | 4148,4149 | `status.values()` | the `accepted` / `refuted` counts in the replay-validation stats block | **RENDER** | Counts. |
| 98 | `loop.py` | 43 | `status == ACCEPTED` over addressed artifacts | the minimal loop's `survivors` list, then `scored=[(aid,{})]` -> `frontier` | **RENDER** | With empty score dicts every survivor is non-dominated, so the frontier degenerates to the survivor set — the comment says so (P1). Partition preserved exactly. |
| 99 | `report.py` | 347,354 | `status == ACCEPTED` on warrant carriers and addressed artifacts | `attack_validity_rate`; the survivor HV / reach DISTRIBUTIONS | **RENDER** | Report-only; distributions, not a pick. Same rate as the compat_eval row, here with no consumer. |
| 100 | `scheduler/scheduler.py` | 205 | `status == ACCEPTED` over addressed artifacts | `run_report()['survivors']`, and the `scored` input to the Pareto frontier | **RENDER** | **Partition FIRST, then a non-compensatory frontier within it.** `frontier()` (`capture/pareto.py`) is strict Pareto domination over (hv, reach, coverage) — no axis is summed, so no score can promote a REFUTED artifact into the frontier. This is the paper's own lawful shape: auxiliary scores rank within a feasibility stratum and can never promote across strata. |
| 101 | `scheduler/scheduler.py` | 2815,2816,2818 | `state.status.values()` | the accepted/refuted/suspended counts on every progress heartbeat | **RENDER** | Counts presented as counts. |
| 102 | `status_display.py` | 25,28,31,32,33 | the four `Status` values | display vocabulary and glosses ('unrefuted', 'survival, not endorsement') | **RENDER** | **Deliberately anti-scalar**: the display layer renames ACCEPTED to 'unrefuted' so a reader cannot mistake a partition cell for an endorsement score. |
| 103 | `status_display.py` | 84 | `state.status.values()` | `display_status_counts` — a Counter | **RENDER** | Counts. |
| 104 | `views/basin.py` | 96,97 | `status(a.id).value` | a column in the basin diagnostic table | **RENDER** | One field among many; the table is not ranked on it. |
| 105 | `views/basin.py` | 155 | `status == ACCEPTED` | `n_accepted` and `diversity_accepted` | **RENDER** | Diagnostic aggregate. |
| 106 | `views/evidence.py` | 16,166 | `status` of an artifact and of its dependencies | the evidence view's status strings | **RENDER** | Rendering. |
| 107 | `views/export.py` | 54,81 | `status == ACCEPTED` + role | which artifacts are written to an export directory, and the README status line | **RENDER** | Partition membership selects the export SET (all of it), not a best member. `artifact_id` overrides when given. |
| 108 | `views/theory.py` | 33,48,49 | `status` of each node and attacker | the theory view's per-node labels | **RENDER** | Labels rendered as labels. |
| 109 | `views/why.py` | 43,54,61,73,74,82,89 | `status` of the artifact, its attackers, and each warrant's validity node | the explain-a-status trace | **RENDER** | **Anti-scalar by design**: on a REFUTED artifact it prints 'you cannot set a status… If that attack survives adjudication the target is REINSTATED, computed — never granted.' |
| 110 | `workflows/website.py` | 768,769 | count of `status == REFUTED` | `critic_refutations` in the website checkpoint record | **RENDER** | A count written to a checkpoint; nothing branches on it. |