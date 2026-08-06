# RESULTS — testphase live validation

## 2026-08-06 — the post-program head survives its first live contact: PASS, 6/6 criteria

What the record shows, against PLAN.md's pre-registered criteria, all
measured at head `f618a08a` (ladder start stamp) on root
`run-a518e33a75507207633f864ba6a864b1`:

1. setup rc=0; qualification **tier=full**, 300/300 cases, rc=0 in
   377s. The battery announced "maximum expected provider calls: 1140"
   — the exact number T1's derived-inventory arithmetic predicted,
   now confirmed against a live provider.
2. reason rc=0 (420s); typed stop **budget_exhausted** at cycle 4,
   89,487/100,000 tokens, 37 standing artifacts.
3. `verify_root`: **zero violations**, before AND after continuation.
4. Module-fingerprint stamp: exactly one,
   `school-population`/`default`, sha `9a6411e64ec1…` — rung 4's
   behaviour proven on an ordinary live run for the first time.
5. `deepreason continue --budget cycles=2`: rc=0. The exhausted run
   resumed cycle 4 → 6, standing 37 → 45, second typed
   budget_exhausted at 100,337 tokens; `continuations.jsonl` present;
   accounting delta 0 (no spend invisible to the log). Owner decision
   4a (2d4ca2e1) now has live end-to-end proof on both halves — this
   continuation here, the refusal in W1's gate test.
6. The 42-root sweep was not run, per the plan: new roots extend the
   population; the P1 partition tests in the gate are the reader-side
   proof.

Two misses by the monitor session, recorded not smoothed:

- **Attempt 1 died in 2s** on typed REASONING_MUST_BE_DISABLED — the
  driving manual's own documented ollama trap (unset is not off),
  omitted from the ladder's setup line. Fixed with `--reasoning none`;
  attempt-1 driver log retained (`testphase-driver.attempt1.log`).
- **The ladder's audit/continue block never ran in-script**: the
  reason JSON's `run_id` already carries the `run-` prefix and the
  ladder prepended a second one, so the root existence check failed
  and printed `audit_skipped=no_run_root` while the run sat there
  healthy. Audits and continuation were executed manually with the
  corrected path (this segment's numbers ARE those outputs);
  the ladder line is fixed in the same commit for the next user.

Residue: single live sample — capability-channel behaviour and
harder-question shapes remain stochastic and unprobed here (the
offline regressions stay the proof); the run's epistemic content
(45 standing artifacts on the pinned-count question) was not judged
for quality, only for typed validity — quality judgment was never a
criterion of this phase. Credential file remains gitignored under the
new `experiments/*/env` pattern (itself a gap this phase surfaced:
the enumerated ignore list missed the next directory by
construction).
