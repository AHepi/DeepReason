# Working notes — forensic audit of the P-T1 technique run

Read-only audit. Write cone: this directory only. No `src/`, `tests/`, `docs/`
or committed run root is modified by this tranche.

## Roots read (branch `claude/spec-to-code-technique-k5209o`, never written)

| epoch | root dir | state / stop_reason | cycles | token_spend in status |
|---|---|---|---|---|
| 0 | `failed-epoch0-run-19c2ff74...` | failed / operational_failure | 2 | **0** (log: 580 016) |
| 1 | `completed-epoch1-run-92e63dcb...` | completed / budget_exhausted | 12 | 413 631 |
| 5 | `failed-epoch5-run-456885c5...` | failed / operational_failure | 2 | **0** |
| 6 | `run/` | completed / budget_exhausted | 24 | 772 482 |

Epoch 3 (`83454d42...`) and epoch 4 (`3d0eb792...`) roots are NOT committed on
that branch — they ran on a second credential and only their RESULTS_*.md were
carried back. Every count below is therefore over four roots, and any claim
about epochs 3-4 is quoted from their RESULTS file, never re-derived.

## Probes

- `probes/q1_citation_census.py` — citation Measure counts, log-only reader.
- `probes/q1_invite_gate.py` — refuted-per-problem against the invitation gate.
- `probes/q1_prompt_surface.py` — what each critic dispatch was shown.
- `probes/q1_invited_replies.py` — what the seat returned when it WAS shown.
