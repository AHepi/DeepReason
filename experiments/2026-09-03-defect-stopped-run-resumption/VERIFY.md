# Verification

Verdict: **PASS (offline; live proof not required by GOAL.md and not attempted)**

## 1. Criterion command + output

GOAL.md's success criterion, run verbatim.

    python -m pytest tests/test_stopped_run_resumption.py -q
    8 passed in 7.26s

    python -m pytest tests/ -q -n 4
    4720 passed, 6 skipped in 1209.44s (0:20:09)

Raw: `proof/GATE_after_fix.txt`. **0 failed.** No assertion was weakened and no
test was skipped to reach it.

## 2. The three shapes — RED before, GREEN after

`python proof/three_shapes.py --workdir <dir>`, the same script both times,
against the deterministic stub with no provider and no network.

| | RED (before) | GREEN (after) |
|---|---|---|
| **clean** — completed / budget_exhausted | refusal `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`, no receipt, `continue rc=1 CONTINUE_TYPED_STOP_REQUIRED`, cycle 8 → 8 | refusal **None**, receipt **taken**, `continue rc=0`, cycle **8 → 10** |
| **failed** — failed / operational_failure | refusal `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`, no receipt, `continue rc=1`, cycle 1 → 1 | refusal **None**, receipt **taken**, `continue rc=0`, cycle **1 → 3** |
| **killed** — SIGKILL, then `finalize` | state stayed `running` after a successful finalize, no stop_reason, `continue rc=1`, cycle 2 → 2 | state **completed**, stop_reason `budget_exhausted`, receipt **taken**, `continue rc=0`, cycle **3 → 5** |

Every green root reports `record_verification_refusal: None` — the record
verifies intact — and `terminal_lifecycle_decision: True`. Outstanding work is
still present and still recorded (31 / 3 / 8 items) with **0 unconsumed
provider calls**; it no longer vetoes the receipt, and the resumed scheduler's
own recovery closed it, because `continue` reached later cycles rather than
dying on `"transaction recovery left unfinished authority"`. That was
REPRO.md's forecast condition for a partial green being mistaken for a full
one, and it did not occur.

Raw: `proof/RED_three_shapes.txt` / `proof/GREEN_three_shapes.txt` and the
`.json` verdicts beside them.

## 3. The control — the security gate is untouched

`python proof/mutate_one_byte.py <root> <copy>`, one byte of `log.jsonl`
altered on a copy of the clean root:

    BEFORE: record_verification_refusal -> the record does not verify on the
            security channel: attempt-route, frozen-route
            continue rc= 1 | CONTINUE_RECORD_NOT_VERIFIED: ... attempt-route, frozen-route

    AFTER:  record_verification_refusal -> the record does not verify on the
            security channel: attempt-route, frozen-route
            continue rc= 1 | CONTINUE_RECORD_NOT_VERIFIED: ... attempt-route, frozen-route

Identical apart from the stub's ephemeral port, which is assigned per run. The
LIFECYCLE refusal is gone; the SECURITY refusal is exactly as the jailbreak
tranche left it. Both halves of GOAL.md's criterion hold together, which is the
whole point: a run whose record verifies resumes, a run whose record was
tampered with does not.

## 4. Historical roots re-checked

The fix changed predicates, so every root that showed the defect was
re-derived on a COPY (a writable open repairs, and so destroys, the evidence):

| root | stored verdict | re-derived now | `continue` |
|---|---|---|---|
| P-A1 `4565139800…` | 0 violations | 0 violations | CONTINUE_TYPED_STOP_REQUIRED |
| P-A2 e4 `63e48f5741…` | 1 (`foreign-criticism`) | 1 (`foreign-criticism`) | CONTINUE_TYPED_STOP_REQUIRED |
| 1-cycle `292f964edb…` | 0 violations | 0 violations | CONTINUE_TYPED_STOP_REQUIRED |
| 4-cycle `fe00609058…` | 0 violations | 0 violations | CONTINUE_TYPED_STOP_REQUIRED |

**No verdict moved.** Every root's re-derived violations equal its stored
violations, by class and by count.

**They still refuse `continue`, and that is correct, not a partial fix.** Their
logs were written before this tranche and contain no STOPPED receipt; the fix
does not write one into a committed root, and nothing may
(`experiments/.../` roots are append-only evidence, and old runs owe the future
nothing — operator law 2026-08-14). They are now the WITNESS SET for
`CONTINUE_TYPED_STOP_REQUIRED` in `tests/test_continuation.py`, which selects
10 such roots by their recorded refusal.

## 5. Live attempt

**None.** GOAL.md's criterion is explicitly offline and the window instruction
made the live check optional ("Optional single live check if cheap"). No
provider key was requested and none was used. Nothing in this tranche's verdict
rests on a live run.

## Residue — stated honestly, not summarized away

1. **The one sub-shape the stub cannot produce.** P-A2 epoch 4 carries a
   CRITICISM work order that was ISSUED with NO provider attempt (the kill
   landed between dispatch and the atomic attempt append). Every outstanding
   item on all three stub shapes is result-bearing, so the end-to-end proof
   never exercised it. It is covered at unit level —
   `test_outstanding_work_with_no_unread_result_takes_the_receipt[False]`
   asserts such an item takes the receipt, since it holds no unread result —
   but **that a resume actually COMPLETES on a root carrying one is not
   demonstrated**. `Scheduler._recover_workflow_prefixes` cannot close it
   (there is no result to admit), so it would reach that method's own
   `"transaction recovery left unfinished authority"` assertion. Whether that
   is the right behaviour (a loud typed failure) or needs a typed abandonment
   road is UNANSWERED by this tranche. Parked as P5.

2. **Two instruments disagree about P-A2 epoch 4, and both readings are
   recorded.** `deepreason stop-report` section 5 reports
   `verify_root: {"checks": [], "source": "stored", "violations": 0}`, while
   `REPLAY_VALIDATION.json` and a fresh `verify_root` both report **1**
   violation (`foreign-criticism`). Cited with the instrument, per
   `dr-drive-harness` §5. It does not affect this tranche's verdict in either
   reading: `foreign-criticism` is not a SECURITY-channel finding, the
   continuation gate returns `None` on that root, and the refusal it actually
   receives is a lifecycle one. Parked as P6 — it is a reporting question about
   `stop-report`, not about resumption.

3. **Exposure to the jailbreak tranche's parked P2 is wider.** Roads that were
   closed for lifecycle reasons now reach the SECURITY gate, which becomes
   their sole guard. The residue itself is unchanged in size — the same records
   pass and fail as before — but more traffic meets it. This is the correct
   architecture under the operator's own clause and was declared in FIX.md
   before the first edit. Owner: `experiments/2026-08-31-defect-jailbreak-gate-closure/`
   PARKED P2; this tranche's PARKED P3 records the changed exposure.

4. **Known-not-mine baselines.** `docs_verify` reports 6 failures. The
   identical 6 were re-run on the stashed clean tree, so **zero were introduced
   by this tranche**: `SEAM-llm-x-rules.md:54` (an unparseable check opener);
   three `CON-run-identity.md` git-history checks naming revisions absent from
   this container's clone; and two `INV-frozen-surfaces.md` checks, one needing
   a branch this container does not have. The two failures this tranche DID
   cause (`SUB-application.md:435` and `:533`, both naming symbols the fix
   removed or renamed) were repaired and re-derived in the fix commit.

5. **The practical stake is relieved but not measured.** P-A2's F8 priced the
   problem: ~22 min/cycle × 24 cycles ≈ 9 h against a container that restarts
   roughly every 2 h, so no full-length run could complete here. Resumption now
   works offline across all three shapes; that a long LIVE run can actually be
   carried across container restarts by repeated `continue` is a plausible
   consequence, **not something this tranche measured**. The first long live
   run is the test of it.

## Errata

`docs/ERRATA.md` **E61** — "failure terminals stay non-resumable" was a design
decision the operator later reversed, and three committed documents plus one
gate test still stated it as settled. Added in the fix commit.
