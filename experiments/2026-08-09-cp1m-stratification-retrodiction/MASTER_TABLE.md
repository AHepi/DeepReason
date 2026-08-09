# CP1-M — master table: are the patrol's 1,941 candidates real contradictions?

Final deliverable of `experiments/2026-08-09-cp1m-stratification-retrodiction/`.
Every number below traces to a committed JSONL file in this directory;
`scripts/build_master_table.py` re-derives the primary aggregates from
those files (no hand-computation not shown in a script or an inline
command in `RESULTS.md`).

## Headline

**Of the patrol pilot's 1,941 candidate contradictions:**

| reading | count | share | what it means |
|---|---|---|---|
| **CONFIRMED, blended across all four methods** | **1,385** | **71.4%** | includes S-formal's 815, which carries an explicit permissiveness caveat (below) |
| **CONFIRMED, strong-evidence subset only** (sandboxed execution, known ground truth, or adversarial convergence — excludes S-formal's raw extraction count) | **570** | **29.4%** | the floor: what survives if you distrust S-formal's method entirely |
| Not confirmed / residue (both_fail, both_pass, compile/authoring failure, ground-truth-agrees, both-wrong, adversarial non-convergence) | 556 (blended) / 1,371 (strong-only) | 28.6% / 70.6% | real, typed, honestly-reported outcomes — never dropped from the denominator |

**Read this as a range, not a single number**: 1,941 patrol hits are
NOT all equally well-supported. Between 29.4% and 71.4% are CONFIRMED
depending on how much weight you put on S-formal's structured-extraction
method (which this tranche itself flags as possibly over-permissive,
see below). The two strata with the strongest, most independently
verifiable evidence (S-mech's sandboxed execution, S-truth's known
answers) land at **568/1,112 = 51.1%** CONFIRMED on their own — call
this the tranche's best single point estimate where it has genuinely
strong evidence.

## Per-stratum table

| Stratum | Population | Method | Confirmed | Rate | Evidence strength | Stability (flip rate) |
|---|---|---|---|---|---|---|
| **S-mech** | 960 | encoder-authored sandboxed checker (real D2/D3 contract), executed via `oracle.run_from_full_spec` | 468 | 48.75% | **Strong** — mechanical execution, independently reproducible from `s_mech_results.jsonl` | 17/90 (18.9%) |
| **S-truth** | 152 | direct comparison against `validation_questions*.json`'s known `accept` answer | 100 | 65.8% | **Strong** — ground truth is external, not model-derived | 1/15 (6.7%) |
| **S-formal** | 829 | structured (object,property) extraction + mechanical negation | 815 | 98.3% | **Moderate, flagged** — see caveat below | 0/83 (0.0%) |
| **S-judgment** (subset of S-formal's 14 `not_clean_shape`) | 14 | adversarial battery (order-swap, skeptic, 2 models), ≥4/6 convergence | 2 | 14.3% | **Weak population, strongest verification method** — most rigorous check, smallest N | 0 samples (population too small for the 10% seed to select any) |

Population check: 960 + 152 + 829 = 1,941. ✓ (S-judgment's 14 are a
subset already counted inside S-formal's 829, not additional.)

### Spot-check pointers (re-derive any row directly)

- S-mech: `s_mech_results.jsonl`, filter `call_variant=="primary"`,
  group by `outcome`.
- S-truth: `s_truth_results.jsonl`, same filter; `root_ground_truth.json`
  is the ground-truth source.
- S-formal: `s_formal_results.jsonl`, same filter; 50-hit validation
  sample reviewed in `RESULTS.md`'s "S-formal: 50-hit validation pass"
  segment.
- S-judgment: `s_judgment_results.jsonl`, grouped by `pair_key`.
- Full re-derivation: `python3 scripts/build_master_table.py` (writes
  `master_table_summary.json`, matches every number above).

## S-formal's honesty caveat, restated here because it bears directly on the headline

815/829 = 98.3% confirmed_negation is high enough to suspect the
extraction step is too permissive — finding *a* shared object/property
and *some* value difference for nearly any pair handed to it, not only
pairs with a genuinely clean disagreement. The pre-registered 50-hit
validation sample was read and found topically coherent (spot-checked
inline, `RESULTS.md`), and its own rate (46/50, 92%) is consistent with
the full run rather than a sudden jump — so the full run did not behave
differently from what was validated. But a 50-pair manual read does not
rule out systematic over-permissiveness across all 829 pairs, and no
independent second check (e.g., a blind second-model comparison of the
two extracted values alone) was run to test that. **This is why the
master table keeps a "strong-evidence-only" reading (570/1,941, 29.4%)
alongside the blended one (1,385/1,941, 71.4%) rather than reporting a
single number.**

## The dual-mode verdict — can models author working checkers for real historical claims?

**Yes, at a meaningful and usable rate, by both models tested**, subject
to two caveats that matter for the recommendation below.

| | gemma4:31b | glm-5.2 | combined |
|---|---|---|---|
| n | 480 | 480 | 960 |
| authoring-success (valid scalar JSON) | 96.0% | 94.2% | 95.1% |
| compile-pass (oracle sandbox AST guard accepts) | 89.0% | 84.8% | 86.9% |
| CONFIRMED (checker discriminates the pair) | 46.7% | 50.8% | 48.75% |

**Caveat 1 — non-determinism**: an identical checker-authoring call,
repeated, changed its final verdict 18.9% of the time (17/90 sampled
repeats). Any single live dispatch through this channel should be read
as one noisy sample, not a settled verdict — a real design consideration
for whatever consumes `program:candidate_checker` results once P-CEPP-1
is fixed (majority-of-N, not single-shot, if the consumer needs a
confident verdict).

**Caveat 2 — sandbox friction, not authoring failure**: 8.2% of pairs
failed to COMPILE, overwhelmingly on `**` (exponentiation, flagged as an
"int bomb" risk) or an `import` statement inside the checker body — both
real, intentional restrictions of the SAME whitelist sandbox
`exec_oracle`/`property_oracle` already use, unrelated to this tranche's
own code. A production dual-mode consumer would hit this same friction;
it is a property of the sandbox, not of the authoring prompt used here.

**Recommendation (decision is the operator's): fixing P-CEPP-1's wiring
looks worth it.** The channel produces genuine, sandboxed, mechanically-
verifiable evidence at a ~49% discrimination rate on REAL historical
claims the encoder never saw during any qualification battery — that is
a real signal, not a null result, and the two failure modes found here
(non-determinism, sandbox-guard friction) are both known, bounded, and
addressable by the CONSUMING code (majority voting; author-time guidance
about the guard's restrictions) rather than requiring a redesign of the
contract itself. P-CEPP-1's own fix (wiring `conjecturer.turn.v7` to a
real `ContractSchemaRepairGrantV1`) is unaffected by anything found here
— this tranche exercised the SAME downstream mechanics
(`candidate_checker_commitment`/`run_from_full_spec`) the live path
would use, just dispatched offline instead of through a v7 manifest.

## Artifact-type + depth-0/depth-k first count (CP3/CP4 seed data)

Computed offline, zero live calls (`scripts/artifact_depth_breakdown.py`,
committed as `artifact_depth_breakdown.json`), over all 1,941 hits'
3,882 artifacts:

- **Type**: 3,871 `conjecturer`-provenance (99.7%), 11 `import`-provenance
  (0.3%) — essentially every patrol hit is a pair of CONJECTURED claims,
  not seed/import material.
- **Depth** (hops via `Interface.refs` `DEPENDENCE` edges back to an
  artifact with no such ref of its own, per-root): **3,355 depth-0
  (86.4%), 527 depth-1 (13.6%), zero depth-2 or deeper, zero
  unresolved/cyclic.**

This is the FIRST such count over this corpus. It seeds CP3/CP4 by
establishing that this corpus slice's candidate-contradiction material
sits at most one derivation hop from a root claim — a future program
chasing DEEPER derivation chains needs either a different corpus (more
multi-cycle, deeply-nested reasoning) or a design that deliberately
grows one; this corpus, as it stands, will not supply depth-2+ examples.

## 150 non-hit controls: the patrol's own false-negative rate

Same priority-ordered routing applied to 150 non-hits sampled from the
7,336-row non-hit pool (`scripts/controls_check.py`, `controls_150.jsonl`,
`controls_check_results.jsonl`):

| Stratum (routed) | n | flagged (would be a contradiction under this tranche's methods) | rate |
|---|---|---|---|
| S-mech-routed | 67 | 19 | 28.4% |
| S-truth-routed | 13 | 1 | 7.7% |
| S-formal-routed | 70 | 52 | 74.3% |
| **Overall** | **150** | **72** | **48.0%** |

**Read this with the SAME caveat as the headline**: the blended 48.0%
false-negative rate is dominated by S-formal-routed controls (74.3%
flagged) — consistent with the same over-permissiveness concern already
raised for S-formal's confirmed_negation rate on the actual hits. The
S-mech-routed and S-truth-routed subsets (28.4% and 7.7% respectively)
use the tranche's strong-evidence methods and are far more trustworthy:
they say the patrol's 0.6-confidence threshold DID miss some real
signal (over a quarter of S-mech-eligible non-hits would flag under
sandboxed execution), but nowhere near the scale the raw blended number
suggests. **This tranche does not resolve which reading is closer to
true** — it reports both, honestly, as the pre-registered check
committed to.

## Honest residue (what this tranche does NOT prove)

- **S-formal's 98.3%/74.3% figures may be inflated by extraction
  over-permissiveness** — flagged above, not resolved. A follow-up would
  need an independent blind second-model check on the extracted values
  alone.
- **S-truth's 34 `ground_truth_agrees` pairs (22.4% of that stratum)
  directly disagree with the original patrol call** — both claims are
  consistent with the KNOWN answer, yet the patrol flagged the pair as a
  contradiction. Not re-examined by a second method this tranche
  (`PREREG.md` named this as intended residue, not chased for budget
  reasons).
- **S-truth's 18 `both_contradict_ground_truth` pairs** are NOT proven to
  be mutually contradictory (both being wrong against ground truth does
  not itself prove they disagree with each other) — reported separately,
  not folded into CONFIRMED.
- **S-judgment's 14-pair population is too small to generalize from** —
  its 14.3% confirm rate is a genuine, striking finding for THESE 14
  pairs, not a corpus-wide claim about "hard" pairs in general.
- **The controls false-negative check used a simplified pipeline**
  (no full S-judgment adversarial battery for controls whose extraction
  came back `not_clean_shape` — recorded in `controls_check.py`'s own
  docstring) — a deliberate scope simplification for a 150-pair check
  whose only job was one flagged/not-flagged number, not a second full
  master table.
- **Every model-judgment step's stability was measured on a 10% SAMPLE,
  never the full population** — the flip rates (18.9% / 6.7% / 0.0% /
  no data) are themselves estimates with their own sampling uncertainty
  at these small repeat-counts (90 / 15 / 83 / 0 samples respectively).
- **Generalization beyond this corpus slice is not claimed** — same
  scope limit the patrol pilot itself named for its own 1,941-hit count.
