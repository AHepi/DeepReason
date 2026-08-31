# Diagnosis: neither `continue` nor `amend` consults ANY replay verdict, and the two obvious ways to make them consult one are each wrong in a different, measured way

Primary cause: `prepare_continuation`
(`src/deepreason/runtime/continuation.py:372-471`) and `_amend_locked`
(`src/deepreason/amendment/apply.py:397-565`) run their full precondition
chains — twelve `CONTINUE_*` checks and the `AMEND_*` chain respectively —
without ever re-deriving, or even reading, the record's replay verdict. Nothing
in either file references `verify_root`; the CON-run-identity tripwire at
`docs/map/CON-run-identity.md:289` exists precisely to assert that absence and
is GREEN on today's HEAD. Terminal authority is not a substitute: it is
computed from the record's own published projection, so a record and its
verdict can be forged together and `derive_terminal_authority` still reports
`current_valid_committed`. The result is that a one-byte forgery buys the whole
operator sequence — `amend` commits epoch 1, then `continue` accepts `seq=0`.

Evidence (record and measurement first; code second):

  - `experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.json`
    -> on committed root `experiments/2026-08-27-pc2b-symmetric-reasoning/run`,
    the forged arm reads `amend: "ACCEPTED epoch=1"`, `continue: "ACCEPTED
    seq=0"`, `verify_root_violations: ["attempt-route","frozen-route"]`,
    `stored_replay_valid: true`, `jailbreak_open: true`. The intact arm is
    identical except for an empty violation set — i.e. the two verbs cannot
    tell the two roots apart.
  - The same root's own `REPLAY_VALIDATION.json` still publishes `valid: true`
    AFTER the forgery -> the stored verdict is not a usable fallback; whatever
    the gate reads, it must RE-DERIVE.
  - `docs/map/CON-run-identity.md:261-288` (Traps) -> this failure is already a
    recorded trap, closing "STILL OPEN: the integrity gate the 2026-08-29 law
    asks for is NOT shipped", with the collision list in the prior tranche's
    `proof/`. Its `check:` at :289 asserts `verify_root` appears in NEITHER
    `continuation.py` NOR `apply.py`, and instructs that the entry be REWRITTEN
    (never deleted) when the gate lands.
  - `experiments/2026-08-30-change-checkpoint-hardening/proof/census.json` ->
    16 of 59 committed roots pass amend's entire precondition chain while their
    own `REPLAY_VALIDATION.json` publishes `valid: false`.
  - `git diff 5fccb1e91 HEAD --stat -- src/deepreason/runtime/continuation.py`
    -> `1 file changed, 46 deletions(-)`; `git show 2650d3c87 --stat` ->
    `apply.py 0/14`, `continuation.py 0/46`. Today's HEAD carries zero
    occurrences of `CONTINUE_RECORD_NOT_VERIFIED`, `AMEND_RECORD_NOT_VERIFIED`
    or `record_verification_refusal` under `src/`, `tests/` or `docs/`.

Implicated code (max 3 sites):
  - `src/deepreason/runtime/continuation.py:372-471` — `prepare_continuation`;
    twelve preconditions, first record-content write at :437.
  - `src/deepreason/amendment/apply.py:397-565` — `_amend_locked`;
    `AMEND_PENDING_CONFLICT` at :518, `_stage_epoch_documents` at :527.
  - `src/deepreason/application/results.py:484-529` — `_terminal`, which builds
    `amend_ready` from the STORED replay dict and therefore reports
    `amend_ready: yes` on a root whose own `--verify` block, printed on the
    same screen, reads `security=2`.

## The secondary cause the first attempt hit, and why BOTH obvious roads are wrong

The 2026-08-30 tranche did not fail because gating is impossible; it failed
because `verify_root`'s FULL violation set answers a broader question than the
law's. This tranche re-measured the two candidate narrowings rather than
choosing one on reading, and each is wrong in a different, independently
measured way:

**Road A — `verify_root_report(root).security_valid` (the public accessor).**
Rejected BY MEASUREMENT, on two independent grounds.
  1. It refuses a LAWFUL committed root. On
     `experiments/2026-08-12-live-grounded-extension-expansion/run` (12,991
     events) `verify_root` reports ZERO violations while
     `verify_root_report` reports 860 findings of which ~495 are on the
     SECURITY channel — they come from the report's DERIVED/TERMINAL streams,
     not the legacy replay stream. A gate on `security_valid` refuses that
     root. That is the "right but breaks lawful continues" failure mode the
     goal names as a stop condition.
  2. It costs 2x. Measured on the same root: `verify_root` 356.76 s,
     `verify_root_report` 668.26 s. The report form runs the whole legacy
     verifier first (`verification/report.py:1148`) and then adds its own
     passes, so narrowing the QUESTION to one channel buys zero compute on
     this road.

**Road B — `verify_root(root)["violations"]` filtered to `_SECURITY_CHECKS`.**
This is the road the evidence supports. `_SECURITY_CHECKS`
(`verification/report.py:119-129`, seven names) is exactly the membership
`_legacy_channel` (:143-158) uses to classify the legacy violation stream —
which IS `verify_root`'s violation list. Measured:
  - it FIRES on the forgery: the one-byte endpoint flip yields
    `attempt-route` + `frozen-route`, both members;
  - it does NOT fire on any of the eight 2026-08-30 collisions: with a
    security-only gate enforced at both verbs, the eight named node ids run
    `8 passed in 1469.92s`, gate reached 34 times, zero security findings; the
    union of checks observed is `{amendment-chain, attached-evidence,
    attempt-validity, foreign-criticism, open, run-input, run-manifest-hash,
    terminal-authority}` — seven `integrity`, one `completion`, none
    `security`. Independently re-measured on the amend side alone: the three
    amend-path files run `65 passed`, gate evaluated 48 times, refused 0;
  - it does NOT fire on the 12,991-event lawful root (zero legacy violations);
  - it costs 1x, not 2x.

Reading `_SECURITY_CHECKS` by import is a READ of frozen surface 3, which
PARKED.md F9 blesses explicitly ("Consuming the membership by import is a read,
not an edit; ADDING to it is not"), and which has precedent inside `src/`
(`src/deepreason/signals_read.py:47` imports `_deferred_model_phase_findings`
from the same module). Nothing in `invariants.py` or `verification/` is
modified.

Falsifiable prediction (what dr-reproduce must show if this diagnosis is right):

    python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.py
      -> jailbreak_open: True on today's HEAD, with the forged arm's
         verify_root_violations exactly ["attempt-route","frozen-route"]

    a security-channel predicate over verify_root's violations, evaluated on
    the eight 2026-08-30 collision roots and on the 12,991-event root
      -> empty on all of them; non-empty ONLY on the forged copy

Ruled out: **the stored verdict as the gate's input.** It is the cheapest
possible road (zero compute — `REPLAY_VALIDATION.json` is already on disk) and
it does not work: the forged root's stored verdict still reads `valid: true`
(`forge_amend_ready.json`, `arms.forged.stored_replay_valid`), and the prior
tranche measured that on 4 of 16 witnesses a canonical forge of `valid: true`
is undetected because `derive_terminal_authority` skips
`_validate_result_projection_binding` when the published result equals the
fail-closed pending projection. Any gate that reads rather than re-derives is
defeated by editing one more file.
