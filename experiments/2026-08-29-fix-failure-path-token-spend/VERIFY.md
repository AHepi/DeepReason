# VERIFY — measured against GOAL.md's four criteria

Every number below is a command's output, committed under `proof/`.

## Criterion 1 — a failure terminal carries the log-derived spend

`test_a_failed_run_reports_the_spend_its_own_log_carries`: a run driven
through the real `deepreason run` path logs 4 242 tokens across three
provider calls, then dies. `run-status.json` carries `state: failed`,
`stop_reason: operational_failure`, **`token_spend: 4242`** — and the log,
read back independently, sums to the same 4 242. **PASS**.

Mutation (restore the omission on the ordinary failure emit) → RED,
`proof/mutation1_red.txt`.

## Criterion 2 — `results` reports the truth for a committed root, unedited

Committed root
`experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`,
its bytes untouched:

```
its own run-status.json : {"state": "failed", "stop_reason": "operational_failure",
                           "token_spend": 0, "token_limit": null}
deepreason results BEFORE: tokens spent vs budget: 0 / unlimited
deepreason results AFTER : tokens spent vs budget: 140461 / unlimited
```

`test_the_reader_recovers_the_spend_of_a_committed_root_stating_zero`
asserts the reported figure equals the log's sum AND that
`run-status.json` is byte-identical after `results_summary` runs. It selects
its root by PROPERTY over `git ls-files`, never by path, so a legitimate
retire-by-rename cannot break it — and it fails loudly rather than vacuously
if the tree ever stops carrying such a root. **PASS**.

Mutation (reader trusts the sidecar unconditionally) → RED,
`proof/mutation2_red.txt`.

## Criterion 3 — a real zero stays zero; an absent record stays absent

- `test_a_run_that_genuinely_spent_nothing_still_reports_zero` — a run that
  made no provider call reports `0`. **PASS**.
- `test_a_root_without_a_status_record_still_reports_a_typed_absence` — no
  `run-status.json`, or the key genuinely missing, still yields
  `{"absent": true, "reason": "NO_RUN_STATUS_JSON"}`, never `0`. **PASS**.
- `test_a_nonzero_sidecar_figure_is_reported_as_recorded_and_not_re_derived`
  — the reader's scope stays narrow. **PASS**; mutation (derive from the log
  always) → RED, `proof/mutation3_red.txt`.

## Criterion 4 — the gate, the map, the record

- Full gate: `proof/gate.txt` — recorded below.
- `docs_verify` FULL: **4 failed**, exactly the session baseline (3
  shallow-clone `CON-run-identity.md` git-history checks, 1 pre-existing
  falsified census). `proof/docs_verify.txt`.
- Ring: **76 passed**, `proof/ring.txt`.
- Map moved in the same commit: `SUB-application.md` Traps, with a
  STRUCTURAL check — it parses `text_runs.py`, finds every terminal
  `progress.emit`, and asserts all four pass `token_spend`. Proven
  falsifiable rather than assumed: breaking it took `docs_verify` from 4
  failures to 5, and restoring it returned to 4.

## The population, before and after

`proof/committed_zero_spend_census.txt`, 59 committed roots each compared
against its own log:

| class | count | this tranche |
|---|---|---|
| sidecar agrees with the log | 30 | untouched |
| **sidecar says 0, log says otherwise** | **20** | **FIXED** — writer for new roots, reader for these |
| sidecar nonzero but smaller than the log | 9 | PARKED (PT2-A), deliberately not re-adjudicated |

## Residue — what this tranche did NOT prove

1. **Which token instrument is authoritative when two disagree by a real
   margin is still open** — the nine-root class, parked as PT2-A with a
   ready-to-send prompt. This tranche's reader is scoped so it does not
   answer that question by accident.
2. **The 66 silently-dropped map checks are NOT fixed** (PT2-B, reported by
   the operator mid-tranche and confirmed by census). `tools/docs_verify.py`
   is outside this window's cone. Consequence to hold in mind when reading
   any "docs_verify at baseline" claim in this window, including this one:
   the baseline is a baseline of the 1 142 checks that RUN.
3. **The phase order was broken.** FIX.md was written after the code, against
   the orchestrator's scope contract clause 3. The visible cost was a fixture
   update found at the ring instead of predicted. Recorded in FIX.md's own
   opening rather than left for a reader to infer.
4. **A test that could not fail was shipped and then caught.** The scope
   test's first version used a stand-in whose log raised; the reader falls
   back to the sidecar on any log error, so the test passed either way and
   mutation 3 came back GREEN. That green is the reason it was caught. It is
   also the argument for mutation-proving every regression rather than
   trusting a passing test: a test that passes proves nothing until you have
   seen it fail.
