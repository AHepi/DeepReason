# Delivered: automatic blast-radius analysis in the skills workflow
Branch: `claude/blast-radius-analysis-design-3avwew` @ `b9150230c` (pushed,
tree clean before this closing commit)

## What changed

DeepReason now has a mechanical blast-radius disclosure gate,
`tools/blast_radius.py` (Rung G6, `docs/map/INV-frozen-surfaces.md`).
Given a proposed change's declared target files/symbols, it computes:
which of the five frozen (never-touch-without-approval) files it
contacts, whether any symbol's live-call reachability would change
(with an honest "can't tell" bucket for anything it cannot statically
resolve), which tests/map documents/qualification digest/wheel-smoke
pins consume the touched symbols, and a plain-language summary of all
of it. It is wired into three points in the change workflow: the
design phase's census becomes tool-backed instead of hand-run;
whenever the operator is asked to approve a frozen-surface or scope
grant, the tool's own computed contact list must be pasted into that
ask, never summarized from memory; and every commit re-checks
actual-touch against what was promised, stopping on drift the same way
the existing line-budget gate already does.

The evidence base behind this design is `CENSUS.md`: what disclosure
tooling already existed (one real gate, for line counts only; two
manual, easy-to-forget checklist steps for everything else) and seven
real, recorded incidents where an approved change quietly touched or
broke something the approval request never mentioned — including the
exact incident that started this work (`docs/ERRATA_EXECUTOR.md`'s
2026-08-09 entry) and a harness role that was wired into a seat binding
while structurally unable to ever run. `docs/HIDDEN_LEGACY_INVENTORY.md`
consolidates those findings into one standing page (promoted from the
tranche's own folder to a permanent spot next to the two existing
error ledgers) so future decisions about reconnecting old, buried
functionality don't require re-doing the detective work each time.

Everything above was designed first (`SPEC.md`, committed and pushed
before any code, per the operator's own "no code this window"
instruction) and built only after the operator's explicit "Go"
approved every recommendation on the resulting decision sheet.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "an automatic blast radius analysis in skills workflow" | done | `tools/blast_radius.py` (commit `b4a96ead7`), wired into three skills (commits `9d4caa6c6`, `0effd7fe0`); VALIDATION.md S1/S2 |
| R2 | design premise: system computes/discloses, operator not the calculator | done | SPEC.md Item 2 "Design premise, applied"; the grant-request checkpoint's "MUST embed... verbatim" text, live in `dr-spec-change` and `dr-ask-the-right-question`; VALIDATION.md S3 |
| R3 | Part 1 — census of existing practice and failure cases | done | `CENSUS.md`, commit `7e6e2693f`; VALIDATION.md S4 |
| R4 | Part 2 — the automatic blast-radius design | done | Designed in SPEC.md Items 1-2 (commit `7e6e2693f`), built in CHECKLIST.md steps 1-7 (commits `b4a96ead7`, `9d4caa6c6`, `0effd7fe0`); VALIDATION.md S1/S2, full gate |
| R5 | Part 3 — the hidden-legacy inventory | done | `docs/HIDDEN_LEGACY_INVENTORY.md`, commits `8d3c24620`/`43b251eec`; VALIDATION.md S5 |
| R6 | "Go" (approval of SPEC.md's Decision sheet) | done | REQUEST.md Amendment 1 (commit `e1c81f8ee`); SPEC.md's five forks marked RESOLVED (same commit); this entire delivered CHECKLIST.md |

Every requirement done; none deferred.

**Standing constraints (C1-C7):** all satisfied — see VALIDATION.md's
own "Standing constraints... swept alongside" paragraph for the C3
transition (SPEC-AND-STOP's own window closed cleanly at R6, which is
new, explicit authorization to continue, not a rule violation) and the
C4/C6/C7 confirmations.

## Assumptions the operator may override

A1: the PARKED/ERRATA sweep for "any others" (R3) is bounded to all 17
`docs/ERRATA.md` entries, all 37 tranche `PARKED.md` files, and two
named leads traced to ground — stated explicitly, not left unbounded.

A2: tool CLI shape (`--files`/`--symbols`/`--against`/`--self-test`),
result name (`BLAST_RADIUS_RESULT_V1`), exit classes, and map placement
(a new subsection of `INV-frozen-surfaces.md`) — fully specified and
built as specified.

A3: tool input is dual-granularity (files AND symbols), matching
existing manual-census practice rather than narrowing it.

A4: `HIDDEN_LEGACY_INVENTORY.md` promoted to `docs/` (superseding its
own tranche-local starting point) — anticipated in writing by SPEC.md's
own Decision sheet (Fork F4), operator-approved via R6.

A5: Part 2 moved from design-only to a full build — superseded by the
operator's own later words (R6, "Go"), not by drift from what was
originally scoped.

## Map delta

**Changed:** `docs/map/INV-frozen-surfaces.md` (new "Blast-radius gate
(Rung G6)" subsection, one backfilled Traps entry for the 2026-08-09
incident this tranche's own origin cites). **Created:** none (no new
`SUB-`/`CON-`/`SEAM-` document; this tranche's work lives entirely in
`tools/`, `.claude/skills/`, and `docs/proposals/`, outside the map's
own subsystem domain). **New checks:** 3 (`ast.parse` on
`tools/blast_radius.py`, and two `grep -q` checks pinning its result
type and its verdict field). **Left stale:** `SEAM-harness-x-
verification.md` — flagged by `docs_verify --stale` for a commit
(`15ba06b34`, 2026-08-09) that predates this tranche's own base
(`25686797`, verified by `git merge-base --is-ancestor`) and touches a
seam this tranche never does; not this tranche's to fix.

## Errata

**E18 added** (`docs/ERRATA.md`, same commit as this document):
`docs/proposals/GATES_AND_PACKAGES_PREPLAN.md` cites a tranche
directory (`experiments/2026-08-09-change-adjudication-judge-seats-
optins/`) as authority that does not exist in the committed tree — the
cited tranche was planned but never opened. Found while tracing the
operator's own "Road E" shorthand during CENSUS.md's research (which
itself resolves to no literal document — a compressed reference to
substance, not a citation). Not corrected in the preplan itself (still
`PROPOSED`, no live rung depends on it); recorded so a future reader
does not go looking for a directory that was never created.

## Parked (not done, not promised)

**P1** (`PARKED.md`): `tests/test_bronze_report.py::
test_census_totals_internally_consistent` fails on every full-gate run
in this environment (`159 == 165`, a gate_blocked/gate_measures
mismatch), verified pre-existing — reproduced identically in an
isolated `git worktree` at this tranche's own base commit, before any
of this tranche's changes. Ready-to-send prompt for a future tranche:
*"Diagnose why `experiments/bronze_flat_2026-07-13/`'s bronze census
totals don't reconcile (`gate_blocked` 159 vs `gate_measures` 165) —
check first whether the retained-data directory is fully present in a
fresh shallow clone, the same class of gap `CON-run-identity.md`'s own
pre-existing failures show for git history depth."*

**Recommended next:** P1 — it is the one loose thread this tranche's
own full-gate run surfaced, cheap to scope (a single failing assertion,
already isolated to one file), and worth closing before the next
tranche that touches `scripts/bronze_census.py` or the retained bronze
data has to re-discover it.

Tranche closed. Further work — implementing P1's fix, extending
Checkpoint 2 to more skills, deciding `property_designer`'s or the
unwired judge-audit functions' fate from `docs/HIDDEN_LEGACY_
INVENTORY.md` — starts a fresh tranche via `dr-change-orchestrator`.
