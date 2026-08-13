---
name: dr-audit-orchestrator
description: Router for the code-audit family. Runs five read-only audit dimensions (broken, dead, docs-drift, spec-drift, goal-trace) over the repo and produces AUDIT_REPORT.md plus ready-to-send fix prompts. Use when the operator asks for an audit, a sweep, or "what is broken / unused / out of date". Findings only — fixes happen in later tranches.
---

# Audit orchestrator (router)

Rated for inexpensive models: every worker step is a command to run,
an output to paste, or a comparison against `docs/AUDIT_BASELINES.md`.
Pin the model actually used in the LEDGER header (L3).

## Artifacts (route on which is missing)

Tranche dir: `experiments/<UTC-date>-audit/`. Artifacts, in order:

| Artifact | Written by | Exists means |
|---|---|---|
| `LEDGER.md` | this router, at open | scope chosen, baselines copied in |
| `ACTIVATION.md` | this router, first run only | every GATE mutation-proven red once |
| `broken.md` | dr-audit-broken | instrument deltas tabled |
| `dead.md` | dr-audit-dead | per-package symbol census tabled |
| `docs-drift.md` | dr-audit-docs-drift | doc-check deltas + stale list tabled |
| `spec-drift.md` | dr-audit-spec-drift | both drift directions tabled |
| `goal-trace.md` | dr-audit-goal-trace | every law rowed with a verdict |
| `AUDIT_REPORT.md` + `PARKED.md` | this router, at close | audit complete |

Loop: open `LEDGER.md`; route to the first worker whose artifact is
missing; when all five exist, close (assemble report). One worker per
invocation.

## LEDGER format

Header: date, model id, HEAD sha, baselines-file sha
(`git rev-parse HEAD:docs/AUDIT_BASELINES.md`). Then one row per
finding, updated live as work happens (G5):

    | id | dimension | target | gate | verdict | proof file | disposition |

Verdict labels are fixed per worker (X3). Disposition is exactly one
of: `parked` (prompt written in PARKED.md), `baseline` (matches
AUDIT_BASELINES.md, no action), `activation` (planted, restored).
Workers write distilled rows and put raw command output in
`proof/<id>.txt` files (G7).

## PRECEDENCE (the one list for this family, S4)

1. Committed run roots are read, never written — GATE at close:
   `git status --porcelain -- experiments/ | grep -v <tranche-dir>`
   prints nothing.
2. `docs/AUDIT_BASELINES.md` decides expected-vs-finding, over memory
   and over any document's prose. A wrong baseline is itself a
   finding: row it, park a baseline-correction prompt.
3. PARK over fix: the audit edits nothing outside its tranche dir —
   GATE at close: `git diff --stat` names only the tranche dir.
4. A verdict row without a `proof/` file is unwritten work: the close
   gate counts rows vs proof files and refuses on mismatch (G1).
5. Baselines move only in a non-audit tranche, with this family's
   close gate re-run there.

## Activation (first run in a clone, or after any model change)

Each worker's GATE must be seen red once before its findings are
trusted (G6/L5). `ACTIVATION.md` rows one planted violation per
worker — the plant, the red output pasted, the restore proof
(`git status --porcelain` clean). The plants are named in each
worker's file. Skip activation only if `ACTIVATION.md` already exists
for the current model id.

## Close (all five worker artifacts exist)

1. Run PRECEDENCE gates 1, 3, 4; paste outputs into `AUDIT_REPORT.md`.
2. Assemble `AUDIT_REPORT.md`: per dimension, the worker table plus
   one count line (`N findings, M baseline, K parked`).
3. For every `parked` row, `PARKED.md` gets a ready-to-send prompt:
   route (`deepreason-orchestrator` for defects,
   `dr-change-orchestrator` for removals/doc fixes), one-goal
   statement, the proof-file pointer, end state. The operator's cost
   per fix is one paste.
4. Commit and push the tranche dir. Report to the operator: counts
   first, then the three highest-consequence findings in plain
   language, then where PARKED.md is.
