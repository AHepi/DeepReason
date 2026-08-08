# Delivered: pipeline census — Rung D1 of the dual-mode conjecture program
Branch: claude/pipeline-census-d1-c9h41d @ d8dc18e3 (pushed, tree clean)

## What changed

This tranche measured, and changed no code. `experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md`
is the measured census: every path by which a conjectured artifact
acquires an executable commitment today (four live/dead paths found,
one adjacent-but-out-of-scope surface reported); exactly how criticism
dispatch, refutation, and the two prose-immunity guards
(`execution_backed`/`formally_backed`) behave per kind; a deliberate
attempt to REFUTE the operator's own "protection-only, no penalty"
design law (R-g) across scheduler ranking, pack rendering, and
acceptance criteria — which survived the attempt, with one genuine
kind-conditional scheduling term found and reported rather than
absorbed; a 54-row load-knob inventory across two structurally distinct
families (26 read live, 28 frozen into the manifest at mint time); and
the full historical record of executable-authoring encoding failures
this repository has ever committed (n=3 — one from the committed-root
corpus, plus turmite and jolt by name — all three failed on encoding,
none on content). `docs/map/CON-conjecture-kinds.md` is the new,
permanent map document distilling this into runnable checks, indexed in
`docs/map/INDEX.md`. Two pre-existing, unrelated test failures were
found while running the full gate and are recorded in this tranche's
own `PARKED.md`, not fixed.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "MEASURE ONLY — src/, tests/, tools/ stay byte-untouched" | done | `git diff --stat` empty, VALIDATION.md S1 |
| R2 | "verify its head is 371e84d7" | done | this session's opening verification |
| R3 | "Run the session preflight" | done | `pip install -e .` this session's opening |
| R4 | "Route through dr-change-orchestrator, starting with dr-capture-request" | done | REQUEST.md, commit `fbb5608c` |
| R5 | "Map preflight per the skill" | done | SPEC.md's map preflight section, VALIDATION.md S4 |
| R6 | "Every path by which an artifact acquires an executable commitment" | done | CENSUS.md §1 (M1-M5), VALIDATION.md S5 |
| R7 | "Criticism dispatch per kind" | done | CENSUS.md §2 (M6-M9), VALIDATION.md S6 |
| R8 | "Refutation semantics per kind" | done | CENSUS.md §3 (M10-M12), VALIDATION.md S7 |
| R9 | "The R-g audit... try to REFUTE that" | done | CENSUS.md §4, VALIDATION.md S8 — CONFIRMS, one exception named |
| R10 | "The load-knob inventory" | done | CENSUS.md §5 (54 knobs), VALIDATION.md S9 |
| R11 | "Historical encoding-failure evidence" | done | CENSUS.md §6 (M13-M14), VALIDATION.md S10 |
| R12 | "Deliverables: ...plus docs/map/CON-conjecture-kinds.md" | done | `docs/map/CON-conjecture-kinds.md`, commit `d618a58b` |
| R13 | "Accept: every census row has its pasted command; docs_verify ...; full pytest gate" | done-with-assumption A5 | VALIDATION.md Map + Full gate sections |
| R14 | "Anything broken you notice is PARKED" | done | PARKED.md, 2 entries |
| R15 | "Commit and push at every phase boundary with retry" | done | this tranche's own commit history, every push confirmed on origin |
| R16 | "Deliver through dr-validate-change and dr-deliver-change, then stop" | done | VALIDATION.md (PASS), this document |
| R17 | "Load dr-explain-to-operator... follow it for every message" | done | every message this session, this document |

## Assumptions the operator may override

A1: S6 PARKED P1's diagnosis chain reused verbatim for the dead
property-oracle path, re-verified line-for-line against the current
tree rather than re-derived from scratch.
A2: the bounded "any path these miss" search used
exec/eval/compile/subprocess/ast.parse/`Commitment(eval=)` as the
smallest reasonable pattern set; it found one adjacent surface
(evidence-adapter execution) correctly classified out of scope.
A3: the R-g audit's three sub-searches were the ones R-g's own text
names (scheduler ranking, pack rendering, acceptance criteria).
A4: the encoding-failure corpus is every committed `experiments/**/log.jsonl`
root plus turmite/jolt by name (not `runs/`, which holds no committed
roots) — the whole evidenced population is n=3, reported as exactly
that, not inflated into a rate.
A5, CORRECTED mid-tranche and carried into VALIDATION.md: "P1/P3" in
the task's acceptance line refers to the operator's own established
shorthand for `test_module_fingerprints.py`'s double-stamp defect
(tracked identically across four prior tranches' `PARKED.md` files),
not S6's own PARKED numbering as this tranche first assumed. The
correction is recorded in SPEC.md rather than silently fixed.

## Map delta

Changed: `docs/map/INDEX.md` (one new row in the concept table,
`Verified-at` advanced since its `--links` check was re-run). Created:
`docs/map/CON-conjecture-kinds.md` (14 new `check:` lines, every one
individually run and confirmed passing before commit). Left stale:
none newly caused by this tranche — `docs_verify --stale` lists 19
pre-existing stale documents, every one stale from OTHER tranches'
`src/` commits (seat-bindings wiring, module-fingerprint writers,
school-population registry migration); this tranche touched none of
their owned files, so re-verifying them is out of this tranche's scope
and is not offered as a parked item (they are prior tranches'
responsibility, already visible to `docs_verify --stale` on its own).

## Parked (not done, not promised)

**P1** — `tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails (`ValueError: too many values to unpack`) on a continued root
carrying 2 `module_fingerprints` payloads. This is the operator's own
named "P1/P3" — independently reproduced and tracked across
S1/S3/S4/S5's own `PARKED.md` files, never fixed. Ready-to-send prompt
in `PARKED.md`.

**P2** — `tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`
fails because committed root `failed-epoch1-run-8c77c6588485304d1f73416318c62949`
(S6's own `PARKED.md` P3 reproduction fixture) is refused continuation
for a different typed reason than this test expects from every
non-resumable stop. Pre-existing (S6 committed the root before this
session), but newly connected to this specific gate test here — not
previously noted in S6's own `PARKED.md`. Ready-to-send prompt in
`PARKED.md`.

**Recommended next:** P1 — it is the older, more independently-confirmed
defect (four prior tranches, now five, all hitting it without a fix),
and `experiments/2026-08-07-change-seats-in-record-s5/PARKED.md`
already carries fresh candidate-root-cause evidence for whoever picks
it up. P2 is smaller in scope but depends on a design decision (does
`continue`'s typed-refusal vocabulary need a second legitimate reason,
or is `CONTINUE_RESUME_RECOVERY_MISMATCH` itself evidence of S6 P3's
unresolved defect) that is better made after P1's older, better-
evidenced defect is resolved.

This tranche is closed. Rung D2 (dual-mode design) is a fresh tranche,
not a continuation of this one.
