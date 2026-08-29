# GOAL — the terminal record tells the truth about its own lifecycle refusal

Tranche: 2026-08-28-fix-swallowed-terminal-lifecycle-refusal (DEFECT, P6)
Branch: claude/text-runs-defect-p6-p3-peq3qd
Base: 90b1347f4

## The one goal, one sentence

When `build_stopped_lifecycle` refuses to record a STOPPED transition, the
refusal becomes a TYPED exception, is RECORDED on the terminal, and
`deepreason results` stops claiming a continuation that `deepreason
continue` will refuse.

## Explicitly NOT this tranche

- Whether outstanding workflow authority *should* block continuation. That is
  P2's design question and belongs to the operator. This tranche makes the
  CURRENT behaviour visible, not different: no run that terminates today
  changes its `state`, its `stop_reason`, or whether `continue` succeeds.
- P5 (`amend` accepting what `continue` refuses) — the amend gate itself is
  untouched. Only the READER's composite claim changes.
- Back-filling anything into a committed root. A root is evidence.

## Falsifiable success criterion

On a root whose STOPPED transition was refused:

1. `build_stopped_lifecycle` raises `UnfinishedWorkflowAuthorityError`
   (a `ValueError` subclass) carrying the outstanding-work and
   unconsumed-bound-call counts — not a bare `ValueError`.
2. `application/text_runs.py` catches that type SPECIFICALLY, and records a
   typed refusal in `run-result.json` and in the terminal progress event.
3. `deepreason results <root>` reports
   `ready for amend / continue: no`, and names WHY.
4. A control root that DOES carry its terminal lifecycle decision still
   reports `yes` and still continues.
5. Full gate 0 failed; `docs_verify` at baseline; the regression is
   mutation-proven RED on the unfixed tree.

## Map ids resolved (map preflight, per CLAUDE.md)

| id | why |
|---|---|
| `DR-INV-frozen-surfaces` | read FIRST. Forecast: no contact. Confirmed — none of `application/text_runs.py`, `application/results.py`, `workflow/lifecycle.py`, `runtime/progress.py` is one of the five frozen surfaces (`capabilities/state.py`, `harness.py`, `invariants.py`+`verification/`, `run_manifest.py`, `qualification.py`), nor the frozen-adjacent `route_fingerprint`. |
| `DR-SUB-application` | owns `application/`, `cli/`, `runtime/` — the terminal writer, the results reader, the progress sink. Its `Traps` carry the ONE-RUN-PATH trap (run `8e22d0431fd2b98d`), which is this defect's ancestor: a lifecycle step written in one place and unreachable from a surface. |
| `DR-SUB-workflow` | owns `workflow/lifecycle.py` — `build_stopped_lifecycle`, `RESUMABLE_STOP_REASONS`. |
| application × workflow | **seam NOT YET WRITTEN** (`INDEX.md` lists it under `SUB-application.md`'s `Seams-undocumented`). This defect lives exactly on it: the writer refuses, the reader never hears. Recorded as a finding, per `dr-drive-harness` §4 step 5. |

## Frozen-surface forecast

NONE. Stated in advance, per the tranche instruction. Any frozen surface or
committed digest pin moving is a STOP.
