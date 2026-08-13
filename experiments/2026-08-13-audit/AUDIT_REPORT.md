# AUDIT_REPORT.md — 2026-08-13 audit

Date: 2026-08-13 (UTC). Model: claude-sonnet-5. First
`dr-audit-orchestrator` run in this clone. HEAD at open:
`51f16b92f`; baselines file: `docs/AUDIT_BASELINES.md` @
`16f9e569c`. Read-only: this tranche made no repo change outside
`experiments/2026-08-13-audit/`.

## PRECEDENCE gates (close)

1. **Committed run roots read-only** —
   `git status --porcelain -- experiments/ | grep -v
   experiments/2026-08-13-audit` → blank. **PASS**
   (`proof/close-gate1.txt`).
2. — (baselines-file authority; no baseline was edited this tranche —
   every finding that looked baseline-wrong was rowed and parked, see
   PARKED.md, never edited in place.)
3. **PARK over fix** — `git diff --stat origin/main -- . ':!experiments/
   2026-08-13-audit'` → blank. **PASS** (`proof/close-gate3.txt`).
4. **Rows vs proof files** — 124 LEDGER data rows, 189 distinct
   proof-file references, 0 missing on disk, 0 rows with an empty
   proof-file column, 1109 files under `proof/`. **PASS**
   (`proof/close-gate4.txt`).
5. — (baselines only move in a non-audit tranche; none moved here.)

## Activation

First run for this model id — no prior `ACTIVATION.md` under this
skill family existed. All 5 workers' GATEs proven red-once (or
blind-per-spec, for docs-drift's plant) before their findings were
trusted. Detail: `ACTIVATION.md`.

## Summary by dimension

| dimension | rows | baseline | parked | noted/other | file |
|---|---|---|---|---|---|
| activation | 5 | — | — | 5 (activation) | ACTIVATION.md |
| broken | 6 | 5 | 1 | — | broken.md |
| dead | 83 | 13 | 70 | — | dead.md |
| docs-drift | 9 | 6 | 2 | 1 (noted) | docs-drift.md |
| spec-drift | 16 | 3 | 13 | — | spec-drift.md |
| goal-trace | 5 | 3 | 2 | — | goal-trace.md |
| **total** | **124** | **36 baseline / 5 activation** | **82** | **1 noted** | |

## The three highest-consequence findings

1. **`dr-audit-dead`'s own methodology over-reports dead code by
   ~55x.** The mechanical "outside-file-only" reference scan flagged
   836 symbols as `candidate-dead` across 82 packages, but a follow-up
   same-file occurrence check shows 821 of those (98.2%) are actively
   called from elsewhere in their own file — real, wired code. Only 15
   symbols are genuinely unreferenced anywhere (three of them,
   `_cmd_check_proof`/`_cmd_code`/`_cmd_simulate` in `cli/main.py`,
   confirmed truly unwired — defined but never dispatched). Fixing the
   worker itself (P1 in `PARKED.md`) is worth more than reviewing any
   individual `candidate-dead` row, since it makes every future run of
   this dimension trustworthy at a glance instead of needing this same
   manual cross-check repeated by hand.

2. **The harness-spec document series is silent on ~75% of the
   shipped runtime surface** (203 of 272 CLI flags / config fields /
   typed refusal codes censused have no mention in
   `harness-spec-*.md`). Sampling shows this clusters almost entirely
   around the V6 RunManifest/policy-generation and wire-contract
   lineage that CLAUDE.md itself says lives in a *separate*
   documentation series from `harness-spec-*.md` — so this may be
   correct-by-design rather than a real gap. This audit could not
   determine that from the tree alone; it is parked as a single
   question (P12) rather than 118 individual amendment requests.

3. **Two of five standing operator design laws are only
   partially enforced.** "Seats change GENERATED, never EVIDENCE" has
   real seat-separation plumbing but no test proving the law's actual
   claim (no seat can skip criticism), and its own cited "packages"
   mechanism is still an unbuilt preplan. "All configurations should be
   allowed" converted ~13 of an identified ~33 compile-time-denial
   sites to typed disclosures — the remaining ~20 are already
   self-parked by the delivering tranche (2026-08-12) and simply
   haven't been picked up yet. Neither is a regression; both are
   honest half-finished states worth tracking to completion.

## Smaller findings worth a glance

- `root_sweep.py`'s actual CLI (requires an output-path argument)
  doesn't match `dr-audit-broken`'s documented invocation (stdout
  redirection) — a one-line skill or script fix (P3).
- Two `docs/*.md` header/Status claims are stale: `MINI_PLAN.md` cites
  two evidence files that don't exist in the tree (P4);
  `SMALL_MODEL_COMPATIBILITY.md` names a kernel identifier
  (`deepreason-small-model-compat-v1`) that appears nowhere in code
  (P5) — likely just renamed, not missing.
- Four SPEC→TREE `spec-orphan` terms worth a look: `ContextRequest` vs
  code's `ContextRequestV1` (P6), `codec:json` (P7), `novel-case` (P8),
  and a three-way spelling drift on
  `workflow-resume-decision`/`.v1` across spec and two different code
  sites that don't even agree with each other (P9).
- All 3 instruments in `dr-audit-broken` that were re-derivable
  matched baseline exactly (full pytest gate: same 1 pre-existing
  failure; `docs_verify`: same 3 pre-existing failures; both wheel
  smokes: clean exit 0). `root_sweep.py`'s census could not be
  re-derived (its known hang is still live), so the last committed
  sweep (2026-08-12, unchanged reader) stands per CLAUDE.md's own
  reader-immutability rule.

## Where the fixes are

Every `parked` finding above has a ready-to-paste prompt in
`PARKED.md`, each naming its route (`deepreason-orchestrator` for
defects, `dr-change-orchestrator` for changes/removals/doc fixes), its
proof pointer, and its end state. 13 prompts total (P1–P13), covering
82 `parked` LEDGER rows (the dead-code and spec-silent dimensions
batch many structurally-identical rows into one prompt each, per each
worker's own "batch by feature" instruction) — the operator's cost per
fix stays one paste, not one paste per row.
