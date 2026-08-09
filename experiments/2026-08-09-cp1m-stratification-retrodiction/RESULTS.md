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
