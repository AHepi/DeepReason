# DIAGNOSIS — omitting a keyword argument ASSERTS a zero

Cause located by the audit (AUDIT_REPORT.md §F-E) and re-measured here over
the whole committed tree before any code was changed.

## The chain, end to end

| step | site | what it does |
|---|---|---|
| SUCCESS terminal | `application/text_runs.py` | passes `token_spend=sum(event.llm.tokens for event in harness.log.read() if event.llm)` — correct, it walks the log |
| THREE FAILURE terminals | `application/text_runs.py` | pass `token_limit` and **no `token_spend` at all** |
| the model | `runtime/progress.py:55` | `token_spend: int = Field(default=0, ge=0)` — **omitting the kwarg asserts 0**; it does not leave a gap |
| the write | `runtime/progress.py` | that event becomes `run-status.json` |
| the read | `application/results.py` | `status.get("token_spend", _absent(...))` — the key IS present, so the absence sentinel never fires |
| the surface | `application/results.py` | prints `tokens spent vs budget: 0 / 600000` |

The reader was behaving correctly on a status file that stated a false fact.
**P3's own prompt sends the fixer to the reader and says "the fix belongs in
the READER, not in the record"; P3-A corrects that**, and following P3 alone
would have left the defect in place.

## The population, measured over the committed tree

`proof/committed_zero_spend_census.txt` (59 roots with a `run-status.json`,
each compared against its own `log.jsonl`):

**20 of 59 roots report `token_spend: 0` while their own log carries a real
figure.** Largest instances:

| reported | log | calls | root |
|---|---|---|---|
| 0 | **1 193 009** | 135 | `experiments/2026-08-26-pc2-rematch/run` |
| 0 | **702 789** | 292 | `experiments/2026-08-25-change-constructive-frontier/run` |
| 0 | 493 364 | 84 | `.../void-inert-battery-run-6913328037a61ca6` |
| 0 | 192 230 | 40 | `.../selfstudy/runs/failed-epoch1-run-9175f0ec…` |

This is a RECURRENCE and the prior measurement is larger now, not smaller:
`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` organ 10 recorded 18 of 54 and
rated the organ HARMFUL-AS-WIRED. Three days later it is 20 of 59.

## A SECOND, DIFFERENT disagreement found by the same census — PARKED

Nine further roots carry a NONZERO `token_spend` that is smaller than their
own log's sum (`proof/nonzero_disagreements.txt`), e.g. 90 700 reported
against 119 659 logged. That is not this defect: the sidecar there holds a
real measurement that is merely stale, not an omission asserting zero.
Deciding which of two real instruments is authoritative is a different
question — the one `RUN_ANATOMY_SYNTHESIS` organ 10 calls "three token
instruments, 27 disagreements". It is PARKED (`PARKED.md`), and the fix's
reader half is deliberately scoped so it does not silently answer it.

## What is NOT the cause

- **A reader defect.** Refuted by the mechanism above: `results.py` reports
  exactly what the sidecar states, and the sidecar's key is present.
- **Terminal accounting never running.** True but not the cause: the success
  path does not use terminal accounting either — it walks the log, three
  lines from where the failure path omits the argument.
