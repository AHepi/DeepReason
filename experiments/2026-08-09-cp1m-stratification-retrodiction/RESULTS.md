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
