# CP1-M — hit stratification + dual-mode retrodiction — RESULTS (living document)

Dated, honest-ledger segments per house convention. Updated incrementally
per phase boundary; earlier segments are never rewritten, only appended
to or corrected with a new dated note.

## 2026-08-09 — Map preflight, P-CEPP-1 re-verification, pre-registration

Map preflight done before any design decision: `docs/map/INDEX.md` →
`DR-INV-frozen-surfaces` → `DR-SUB-evaluation` / `DR-SUB-capabilities` /
`DR-CON-conjecture-kinds` / `DR-SUB-manifest` / `DR-SUB-verification`.
Table of what each covers and why it's read is in `PREREG.md`'s own
"Map preflight" section.

**P-CEPP-1 re-verified against this tranche's own checkout, not trusted
verbatim from the pilot's `PARKED.md`.** All three cited lines in
`src/deepreason/run_manifest.py` (658, 2473/2491, 1999) match byte-for-
byte. Verdict unchanged: `conjecturer.turn.v7` cannot validate any live
manifest today (`V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED`). Full detail in
`PREREG.md`.

**The real D2/D3 dual-mode contract shape** was read directly from
`src/deepreason/oracle.py` (`candidate_checker_commitment`,
`run_from_full_spec`) and `src/deepreason/programs.py` (the
`"candidate_checker"` program registry entry, `eval="execution"` class),
cross-checked against `tests/test_oracle.py`'s dual-mode section (lines
190-289, the tests D2's own `PARKED.md`/CHECKLIST.md point to as proof
the eval-kind mechanics work once a manifest can even compile). This is
the exact contract S-mech's checker-authoring calls target — confirmed
working end-to-end with hand-written checkers already; this tranche is
the first to feed it MODEL-authored checkers against REAL historical
claims.

**Searched for the task's referenced "patrol RESULTS.md's
non-determinism correction"** before designing the stability control: no
section titled that way exists in
`experiments/2026-08-08-corpus-enrichment-patrol-pilot/RESULTS.md` (the
file was read in full, all 378 lines, and its git history checked —
final commit `7a4053cba`, no later append). The closest recorded fact is
a JSON-list-ORDERING non-reproducibility note (Phase 3 overlay
comparison, Python's hash-randomized `set()` iteration), not a
model-judgment stability finding. Recorded here rather than silently
assumed: the task's stability-control requirement is implemented anyway
on its own independent merits (CLAUDE.md's capability-channel
stochasticity doctrine, and the plain fact that temperature=0.0 on a
hosted API is not a determinism guarantee) — see `PREREG.md`'s
"Stability control" section for the exact design (10%-sampled repeat
pass per model-judgment step, flip rate reported per step).

**Offline first-pass sizing** (`scripts/offline_stratify.py` — zero live
calls; opens committed roots read-only via the same
`Harness(root, read_only=True)` + `programs.content_text` loader
`phase2_patrol.py` used, matches text patterns only):

| | value |
|---|---|
| Hits (`patrol_hits.jsonl`) | 1,941 |
| Non-hit pool (`patrol_results.jsonl`, `is_hit=false, error=null`) | 7,336 |
| Non-hit controls sampled (seed `sha256("cp1m-control-sample-v1")[:8]`) | 150 |
| Hits with unresolved claim text | 0 |
| Controls with unresolved claim text | 0 |
| Distinct roots contributing hits | 43 |
| S-mech-eligible hits (heuristic: `Rule\s*\d+` OR digit+countable-noun regex) | 960/1941 (49.5%) |
| S-mech-eligible controls (same heuristic) | 67/150 (44.7%) |
| Hits whose `reason` mentions any `Rule NNN` | 97 |
| Of which Rule-184-family (the pilot's chunk-1 exemplars) | 43 |
| Hits inside Phase-1's 10 enriched (base/hard/hard2) roots — provisional S-truth ceiling before S-mech carve-out | 808/1941 (exactly the patrol's own "enriched half" count — cross-checked, matches) |

**This heuristic is a sizing aid only, explicitly not the final
per-pair stratum assignment** — `PREREG.md` names the real,
priority-ordered assignment rule (S-mech → S-truth → S-formal →
S-judgment, first-match), which requires the live checker-authoring /
extraction / adversarial-battery calls themselves to resolve per pair.
Output committed verbatim: `hits_with_claims.jsonl` (1,941 rows, patrol
hit fields + resolved claim text), `controls_150.jsonl` (150 rows, same
shape), `offline_stratification_summary.json`.

Pre-registration (`PREREG.md`) covers, before any live call: strata
definitions and priority order, the 150-control sample (already drawn,
committed), the checker-authoring contract (frozen prompt, model split,
key split), confirmation criteria per stratum, and the stability-control
design. Committed this phase boundary.

## 2026-08-09 — STOP: no live-call credentials in this container

Per CLAUDE.md's environment discipline ("The `env` file
(`OLLAMA_API_KEY=...`) is gitignored and never committed; recreate it
from the operator's handover if missing"), checked before spending any
live budget: `experiments/live_research_2026-07-29/env` does not exist
on disk, no `OLLAMA_API_KEY`-shaped environment variable is set in this
container, and no handover document in this session carries key
material. The task instruction names "two operator keys" but no key
values or retrieval pointer were provided in the task text itself.

This blocks every live-call phase this tranche's pre-registration
depends on: S-mech's encoder-authored checkers, S-truth's fallback
extraction calls, S-formal's extraction calls, and every S-judgment
adversarial-battery reading — all four strata's confirmation methods
need at least one live model call. The offline-only work above (map
preflight, P-CEPP-1 re-verification, contract-shape confirmation,
control sampling, heuristic sizing, and the full pre-registration) is
complete and committed; nothing further can proceed without the
operator supplying the two keys (or a pointer to where this container
can fetch them).

Per `dr-ask-the-right-question` (route to the cheapest authority; this
is a credential the record and the framework cannot supply — only the
operator can), this is raised to the operator now rather than guessed
at, fabricated, or silently skipped.

## 2026-08-09 — credentials received, verified, live phases underway

Two operator keys received. Written to a gitignored, `chmod 600` file
under this tranche's own directory (`env`; `git check-ignore -v`
confirmed it matches the existing `experiments/*/env` pattern before
anything was written — no gitignore edit was needed). **Never printed
in full in this record or any commit; only outcome (works/doesn't) is
logged.** Both keys smoke-tested with one bounded call each, both
models (`glm-5.2`, `gemma4:31b`) — all four combinations returned a
valid response. `≤3 concurrent per key` is enforced in-process by a
`threading.Semaphore(3)` per key in every phase script below; the four
live phases (S-mech, S-truth, S-formal, S-judgment) are run
SEQUENTIALLY, never concurrently with each other, so the 3-per-key cap
is never exceeded by two scripts running at once.

**S-mech deviation, recorded before spending the bulk of the stratum's
budget** (first ~6 calls only): `PREREG.md` originally specified one
checker per CLAIM. Redesigned to one COMBINED checker per PAIR — the
encoder is given both claims together, asked to compute the underlying
quantity from scratch (never to pick a side), and to state what each
claim asserts about it; the SAME compiled checker is then scored
against both claims' asserted values through the real dispatch path
(`candidate_checker_commitment` + `run_from_full_spec`, one commitment
per claim, same `source`/`entry`, different `tests[0].out`). Reason: a
per-claim checker risks being a tautological echo of its own claim (the
model just hardcodes what it was told) rather than an independent
computation; scoring the SAME checker against both claims makes it
impossible for the checker to win by construction. `scripts/s_mech_run.py`
implements this. A second, purely SYNTACTIC fix followed a 4-call smoke
test: both models, despite `json_mode=True`, sometimes wrapped output in
markdown code fences and used Python literal syntax (unquoted int dict
keys, capitalized `True`/`False`) instead of strict JSON — added a
two-tier parse (strict JSON first, then a repair pass that ONLY strips
fences and fixes Python-vs-JSON syntax, never touches semantic content)
and tightened the prompt to require `check()` return a single SCALAR
(number/string/bool), never a nested structure — the original prompt's
open-ended "value" invited multi-key dict returns that were both hard to
score and often not strict JSON.

**S-mech run launched** (harness-tracked background call, per the patrol
pilot's own lesson that a raw detached `setsid`/`nohup` process does not
reliably survive this container — CLAUDE.md's Environment section,
confirmed again by that pilot's Failure #3). Population: 960 pairs
(Rule-184-family's 43 first), ~1044 total tasks including the 10%
stability-repeat sample.

## 2026-08-09 — S-mech COMPLETE: 960/960 pairs

| | gemma4:31b | glm-5.2 | combined |
|---|---|---|---|
| n | 480 | 480 | 960 |
| authoring-success (valid scalar JSON) | 461 (96.0%) | 452 (94.2%) | 913 (95.1%) |
| compile-pass (sandbox AST guard accepts) | 427 (89.0%) | 407 (84.8%) | 834 (86.9%) |
| CONFIRMED (checker sides with A or B) | 224 (46.7%) | 244 (50.8%) | 468 (48.75%) |

(compile-pass and "executes to a verdict" are the SAME count in this
design — once the oracle sandbox accepts a checker's source, `run()`
always returns pass/fail, never an uncaught crash, so there is no
separate "compiled but didn't execute" bucket here; noted rather than
implied by two identical-looking columns.)

**Full outcome breakdown, 960 pairs:** `confirmed_a=252 (26.3%),
confirmed_b=216 (22.5%)` → **468/960 CONFIRMED (48.75%)**;
`both_fail=319 (33.2%)` — the checker's own computed value matched
NEITHER claim (discriminating-power evidence: either the checker is
wrong, or a third value is the truth, or the checker hit a step-limit
inside the sandbox); `both_pass=47 (4.9%)` — the checker matched both
claims (only possible if `claim_a_value`/`claim_b_value` came back equal
— an authoring/extraction slip, since the pair was flagged as a
contradiction by the original patrol call); `compile_fail=79 (8.2%)` —
rejected by the oracle sandbox's AST guard, overwhelmingly `**`
exponentiation ("int bomb" risk) or an `import` statement inside the
checker body, both REAL, intentional restrictions of the SAME whitelist
sandbox `exec_oracle`/`property_oracle` already use, not a defect in
this tranche's own code; `authoring_failed=50 (5.2%)` — the encoder
never returned a parseable, scalar-valued JSON object even after the
syntactic repair pass.

**Stability control (10%-sampled repeat pass, 90 pairs repeated):
17/90 flipped (18.9%)** — a call issued twice, identically, with
temperature=0.0, produced a DIFFERENT final classification (e.g.
confirmed_a on one call, both_fail on the repeat) roughly one time in
five. This is a real, load-bearing finding, not a rounding artifact:
temperature=0.0 on this hosted API is not a determinism guarantee (the
exact concern `PREREG.md`'s stability-control section flagged before any
call was spent). Every S-mech CONFIRMED count above should be read with
this ~19% single-call flip rate in mind — it bounds how much weight any
ONE checker-authoring call's verdict can bear on its own.

Committed verbatim: `s_mech_results.jsonl` (1,050 rows: 960 primary + 90
stability repeats).

## 2026-08-09 — S-truth COMPLETE: 152/152 pairs

One bounded classification call per pair (ground truth stated
explicitly; `scripts/s_truth_run.py`), split evenly across both models
and both keys, same 10%-sampled stability control as every other
stratum.

| outcome | count | share |
|---|---|---|
| `confirmed_b` (claim A contradicts the known answer, B stands) | 73 | 48.0% |
| `confirmed_a` (claim B contradicts the known answer, A stands) | 27 | 17.8% |
| **CONFIRMED total (clean polarity)** | **100** | **65.8%** |
| `both_contradict_ground_truth` (neither claim matches the known answer) | 18 | 11.8% |
| `ground_truth_agrees` (both claims consistent with the known answer) | 34 | 22.4% |

**`both_contradict_ground_truth` is reported separately, NOT folded into
CONFIRMED**: this method only checks each claim against the known
answer independently — it does not itself prove the two WRONG claims
disagree with EACH OTHER (they could, in principle, both assert the same
incorrect value, which would make them consistent with each other and
wrong together, not a contradiction). Flagged as residue, not chased
further this tranche (would need its own values-agree check, the same
mechanical comparison `S-formal` already performs elsewhere in this
pipeline).

**`ground_truth_agrees` (34/152, 22.4%) is the S-truth stratum's own
disagreement with the original patrol call**: the patrol's narrow
question flagged these as contradictions, but checked against the
KNOWN correct answer, both claims in the pair are consistent with it.
`PREREG.md` named this residue in advance ("routed to S-formal/
S-judgment for a second read rather than left unexamined") — not
re-run through a second live stratum this tranche for budget reasons
(recorded here as a deviation, not silently dropped): these 34 pairs
are carried into the master table as their own row rather than
re-classified.

**Stability control: 1/15 sampled repeats flipped (6.7%)** — markedly
lower than S-mech's 18.9%. Consistent with this being a genuinely easier
judgment task (the model is handed the correct answer and only has to
compare against it), not a fluke of sample size alone.

Committed verbatim: `s_truth_results.jsonl` (167 rows: 152 primary + 15
stability repeats).

## 2026-08-09 — S-formal: 50-hit validation pass, then full run launched

Population not claimed by S-mech or S-truth: 829 pairs. Per `PREREG.md`'s
pre-registered rule, ran the extraction call
(`scripts/s_formal_run.py --validate-only`) on 50 hits first and read the
raw `{object, property, value_a, value_b, clean_shape}` output side by
side with the claim text before trusting the stratum with its full
budget. Reviewed: object/property assignments were topically coherent
(e.g. pair [20] extracted `object="SRC_003 and SRC_004",
property="dependency relationship", value_a="SRC_004 inherits SRC_003",
value_b="SRC_003 depends on SRC_004"` — a genuine, meaningful
disagreement matching what the claim text actually says), and
`not_clean_shape` fired correctly on pairs whose two claims were about
different topics entirely (e.g. a "shares mechanism" claim paired
against an unrelated "contradicts the ranking schema" claim). A second
50-sample tally (fresh calls, same 1-key/1-model validation config):
46/50 `confirmed_negation`, 4/50 `not_clean_shape`, 0/50 `values_agree`
this time — the same qualitative split, though not identical counts to
the first pass (expected, given the stability-flip-rate finding already
established for this API: identical calls are not always
bit-identical). Validation accepted; full 829-pair run launched as a
harness-tracked background call.

## 2026-08-09 — S-formal COMPLETE: 829/829 pairs

| outcome | count | share |
|---|---|---|
| `confirmed_negation` (same object+property, mechanically differing values) | 815 | 98.3% |
| `not_clean_shape` (extraction declined — no shared object/property found) | 14 | 1.7% |
| `values_agree` / `extraction_parse_failed` | 0 | 0.0% |

**Stability control: 0/83 sampled repeats flipped (0.0%)** — a striking
contrast with S-mech (18.9%) and S-truth (6.7%). The extraction +
mechanical-negation task is far more constrained than either authoring
sandboxed code or free-form judgment, and this tranche's own repeat
data backs that up directly, not just by argument.

**Honesty caveat on the 98.3% figure, stated plainly rather than
presented as unqualified strength**: this rate is high enough to warrant
suspicion that the extraction step is too PERMISSIVE — i.e., that it
finds *a* shared object/property and *some* value difference for almost
any pair handed to it, rather than only pairs with a genuinely clean
same-topic disagreement. The 50-hit pre-registered validation sample
(above) was read and found topically coherent on spot inspection, and
that sample's own rate (46/50 = 92%, then 46/50 again on the fresh
validation-only tally) is consistent with the full run's 98.3% rather
than a sudden jump — so this is not a case where the full run behaved
differently from what was validated. But a 50-pair manual read is not
proof against systematic over-permissiveness across 829 pairs, and this
tranche did not run an independent second check (e.g. asking a second
model, blind to which claim said which, whether the two extracted
values actually look distinct) to rule it out. **Recorded
as residue: `S-formal`'s CONFIRMED count should be read as "structurally
matches the confirmed-negation shape," not as independently verified at
the same evidentiary strength as `S-mech`'s sandboxed execution or
`S-truth`'s known-answer check** — the master table keeps this
stratum's method column distinct for exactly this reason.

Committed verbatim: `s_formal_results.jsonl` (912 rows: 829 primary + 83
stability repeats).

## 2026-08-09 — S-judgment COMPLETE: 14/14 pairs (S-formal's `not_clean_shape` routed here)

Small population by construction: only S-formal's 14 `not_clean_shape`
pairs fall through to "the remainder." Adversarial battery run (2
models × 3 variants = up to 6 readings per pair: `baseline` verbatim,
`order_swap`, `skeptic`), convergence = readings agreeing with the
original patrol verdict (`contradiction=true`).

| pair (root) | agree/available | verdict |
|---|---|---|
| rung5 ab-home (`08fedf4d2716`) | 0/6, 1/6, 1/6 | not_confirmed ×3 |
| S6 (`run-79900e78...`) | 1/6, 3/6 | not_confirmed ×2 |
| live_research narrow (`run-7d8723fb...`) | 6/6 | **CONFIRMED** |
| selfstudy epoch3 | 1/6 | not_confirmed |
| selfstudy failed-epoch1 | 1/6, 5/6, 0/6 | not_confirmed, **CONFIRMED**, not_confirmed |
| selfstudy failed-epoch2 | 1/6, 3/6 | not_confirmed ×2 |
| selfstudy failed-epoch4 | 3/6 | not_confirmed |
| live_tri (`run-6dab80d6...`) | 0/6 | not_confirmed |

**2/14 CONFIRMED (14.3%), 12/14 not_confirmed (85.7%) by adversarial
convergence.** This is the most striking single number in the whole
tranche: the 14 pairs that fell through EVERY structured method (not
executable/countable, not on a known-answer question, and whose two
claims don't share a clean same-object/same-property shape) are also
the pairs where independent re-examination — order-swapped, skeptic-
framed, by both models — mostly does NOT reproduce the original
patrol's contradiction call. Read plainly: the harder a pair is to pin
down with ANY structured method, the less the original narrow-question
classification holds up under adversarial pressure. This is exactly the
kind of finding `S-judgment`'s design was meant to surface, not an
artifact of the small sample.

**Stability control: 0 sampled repeats** — the 10%-sample seed
(deterministic, content-hashed) happened to select none of these 14
specific pair keys; not a "0% flip rate," a genuine absence of data.
Recorded honestly rather than left implying stability was measured and
found perfect.

Committed verbatim: `s_judgment_results.jsonl` (84 rows: 14 pairs × up
to 6 readings each).

## 2026-08-09 — 150-control false-negative check complete

Same priority-ordered stratum routing applied to the 150 pre-drawn
non-hit controls (`scripts/controls_check.py`): 67 routed to S-mech
(28.4% flagged), 13 to S-truth (7.7% flagged), 70 to S-formal (74.3%
flagged) — **72/150 overall (48.0%)** would be flagged as a
contradiction under this tranche's stronger methods, despite the
original patrol call saying no. Read with the same caveat as the main
headline: the blended figure is dominated by S-formal's likely-
permissive method; the S-mech-routed and S-truth-routed subsets
(28.4%, 7.7%) are the trustworthy signal, and they still say the
patrol's 0.6-confidence threshold missed real material, just less of
it than 48.0% would suggest on its own.

## 2026-08-09 — DELIVERY: master table pushed, stop condition met

All four strata complete (S-mech 468/960, S-truth 100/152, S-formal
815/829 flagged with caveat, S-judgment 2/14), offline artifact-type/
depth-0/depth-k count complete, 150-control false-negative check
complete. Full master table, headline (1,385/1,941 blended / 570/1,941
strong-evidence-only), dual-mode verdict and recommendation, and
complete residue ledger are in `MASTER_TABLE.md` — the tranche's primary
deliverable, cross-referencing every committed JSONL file rather than
restating numbers that could drift from their source.

**Two-sentence answer to the operator's two priority questions:**
between 570 and 1,385 of the patrol's 1,941 candidates are CONFIRMED
contradictions depending on how much weight is placed on one
flagged-as-possibly-permissive method (S-formal), with the strongest
independently-verifiable evidence (sandboxed execution + known ground
truth) landing at 51.1% (568/1,112) on its own; and yes, models CAN
author working dual-mode checkers for real historical claims at a
~49% discrimination rate with ~87% sandbox compile-pass, subject to an
18.9% single-call non-determinism rate, making P-CEPP-1's wiring fix
look worth doing (operator's decision).

Stop condition met per the task instruction: master table complete,
committed, pushed.

**Ground-truth mapping for S-truth built and committed**
(`root_ground_truth.json`): each of Phase 1's 10 base/hard/hard2 roots
matched to its source question's `id` and `accept` list by seed-problem-
text prefix match against `experiments/validation_questions*.json` — all
10 matched cleanly (e.g. `run-fd071eaf...` → `q13`, `accept: ["12"]`).
152 of the 808 hits in these roots are NOT S-mech-eligible and so form
the S-truth population; the other 656 are claimed by S-mech's priority.

**Offline artifact-type + depth-0/depth-k first count** (zero live
calls, `scripts/artifact_depth_breakdown.py`, committed as
`artifact_depth_breakdown.json`): across the 1,941 hits' 3,882 artifacts
(all resolved; no unopenable root among hit-contributing roots), **3,871
are `conjecturer`-provenance and 11 are `import`-provenance** — every
patrol hit is, unsurprisingly, a pair of conjectured claims, not a
seed/import artifact. Depth (hops via `Interface.refs`
`RefRole.DEPENDENCE` edges back to an artifact with no such ref of its
own, computed per-root): **3,355 depth-0, 527 depth-1, zero depth-2+,
zero unresolved/cyclic**. This is the FIRST such count taken over this
corpus — it seeds CP3/CP4 by establishing that essentially all
candidate-contradiction material sits at most one derivation hop from a
root claim in this corpus slice; a program that wanted deeper chains
would need either a different corpus or a design that deliberately grows
one.
