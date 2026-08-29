# GOAL — a failed run reports the tokens it actually spent

Tranche: 2026-08-29-fix-failure-path-token-spend (DEFECT, P3 + amendment P3-A)
Branch: claude/text-runs-defect-p6-p3-peq3qd
Base: bd73155f4 (this window's Tranche 1, P6, delivered)

## The one goal, one sentence

The three failure-path terminals in `application/text_runs.py` stop asserting
a token spend of ZERO they never measured, and `deepreason results` stops
printing that zero for runs that spent most of their budget.

## Where the fix belongs, and the correction that decides it

P3's original prompt (branch `claude/spec-to-code-technique-k5209o`,
PARKED.md §P3) says *"the fix belongs in the READER, not in the record."*
Amendment **P3-A** (`experiments/2026-08-28-audit-run-problems/PARKED.md`)
CORRECTS that, and AUDIT_REPORT.md §F-E carries the chain end to end. Cited,
not re-litigated:

- `text_runs.py:1440-1458` — the SUCCESS terminal computes
  `token_spend=sum(event.llm.tokens for event in harness.log.read() if
  event.llm)`. Correct: it walks the log.
- `text_runs.py` — the THREE failure emits pass `token_limit` and **no
  `token_spend` at all**.
- `runtime/progress.py:55` — `token_spend: int = Field(default=0, ge=0)`.
  **Omitting the kwarg ASSERTS zero**; it does not leave a gap.
- `application/results.py:172` — reads `status.get("token_spend", _absent(...))`.
  The key IS present, so the absence sentinel never fires.

So the reader behaves correctly on a status file that states a false fact.
The primary fix is the WRITER.

## Both halves, and which is which

**(a) WRITER — stops NEW roots lying.** The three failure emits derive the
spend from the log, as the success path three lines away already does.

**(b) READER — recovers the truth for roots ALREADY committed.** For a root
whose status file says `0`, the reader cannot distinguish a false zero from a
real one — but the log can, and `_adjudication` in that same file already
derives its counts by walking the log rather than trusting a stored total.
The append-only log is the record; `run-status.json` is a derived sidecar.

## Explicitly NOT this tranche

- **No back-filling into a committed root.** A root is evidence and is never
  edited. Half (b) is a READER over unedited bytes.
- The absence sentinel is PRESERVED for genuinely absent keys: a root with no
  `run-status.json` still reports a typed absence, never a zero.
- P2's design question (is a denied reservation on an exhausted budget an
  operational failure at all?) is untouched.

## Falsifiable success criterion

1. A failure-path terminal carries the log-derived spend in
   `run-status.json`; mutation showing the old emit is RED.
2. `deepreason results` reports a spend consistent with the log on a
   committed root that reports `0`, without editing that root.
3. A root that genuinely spent zero still reports `0`, and a root with no
   status record still reports its typed absence.
4. Full gate 0 failed (baseline 4408 after Tranche 1); `docs_verify` at the
   4-failure baseline; map moved in the same commit.

## Map ids resolved (map preflight)

| id | why |
|---|---|
| `DR-INV-frozen-surfaces` | read FIRST. Forecast: no contact. Confirmed — `application/text_runs.py`, `application/results.py` and `runtime/progress.py` are none of the five frozen surfaces. |
| `DR-SUB-application` | owns `application/`, `runtime/` — the three failure emits, the progress model, the results reader. Its Traps already carry the shape-of-a-failed-result trap ("a `deepreason-run-result-v2` payload for a FAILED run carries `error`/`error_type` and NO `survivors`… counting the missing key as 0 states a result the record never held") — this defect is that exact mistake made by the WRITER instead of the reader. |

## Recurrence, named in the regression docstring

`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` organ 10: **18 of 54 roots report
`token_spend: 0`** while the log and the accounting agree on a real figure;
P-C1 ARM H — 702 789 tokens — prints zero on `deepreason results`. Rated
HARMFUL-AS-WIRED there, and parked as W6-P1.

## Frozen-surface forecast

NONE. Any frozen surface or committed digest pin moving is a STOP.
