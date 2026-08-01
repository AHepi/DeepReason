---
name: dr-verify-outcome
description: Prove a DeepReason fix against its GOAL.md success criterion, optionally with one guarded live run, and record the honest outcome in VERIFY.md. Use after dr-implement-fix.
---

# Verify the outcome

Input: GOAL.md's machine-decidable success criterion + the pushed fix.
Output: VERIFY.md with verdict PASS or FAIL. You verify; you do not
patch. Any new code change belongs to a fresh cycle through the
orchestrator.

## Ladder of proof (ascend only as far as the goal requires)

1. **Criterion command.** Run GOAL.md's success command verbatim.
   Paste output.
2. **Historical roots.** If the fix changed a reader/validator, re-run
   `verify_root` against the committed roots that showed the defect
   AND one known-good root: the target violations must disappear,
   everything else must be unchanged. List remaining violations by
   class — do not summarize them away.
3. **Live run (only if GOAL.md demands live proof).** At most ONE
   attempt, fully guarded:
   - Preflight: env file present, `deepreason` importable, run
     identity free (retire + commit rename first if occupied).
   - Launch detached from the ladder's own directory:
     `setsid nohup ./<ladder>.sh & disown`.
   - Arm rollback insurance: the snapshot loop (commit+push the
     experiment dir every ~5 min) and a monitor on `progress.jsonl`
     state/phase + the driver log's `rc=` lines, alerting on both
     success AND failure signatures.
   - Judge only typed outcomes: run state, stop_reason, audit JSON,
     `verify_root`, FINDINGS.md. Model prose is not verification.
4. **Know what a live run can and cannot prove.** Model behavior is
   stochastic across identically-configured runs (a capability channel
   used in one attempt may go unused in the next). A live attempt that
   never reaches the fixed path is INCONCLUSIVE for that path — say
   so; the offline regression remains the proof of correctness. Do not
   burn repeated live attempts chasing a stochastic path: one relaunch
   maximum, then record the residue.

## VERIFY.md template

    # Verification
    Criterion command + output: <pasted>
    Historical roots re-checked: <root -> before/after violation classes>
    Live attempt (if any): <run id, typed stop, tokens, one-line audit>
    Verdict: PASS | FAIL | PASS-offline/INCONCLUSIVE-live
    Residue (honest): <what remains unproven or parked, or "none">

## Closing the tranche (on PASS)

- Append a dated segment to the experiment's RESULTS.md: what was
  observed, what was fixed, what the record now shows, and the honest
  residue. "Accepted does not mean true"; never claim more than the
  record shows.
- Commit and push everything; confirm `git status` is clean and the
  branch head is on the remote.
- Report: verdict, evidence pointers, PARKED.md contents as candidate
  next tranches.

On FAIL: append the failure evidence to DIAGNOSIS.md, commit, and
return to the orchestrator (route: dr-diagnose). Never patch from
inside this skill.
