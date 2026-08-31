# Goal: a committed run root whose record fails SECURITY-channel replay validation is refused by `continue` and by `amend`, with a typed reason the operator can read in `results`

Class: defect

Observed: forging ONE byte of a committed, `amend_ready` root's `log.jsonl`
(the first recorded provider endpoint, same length) makes `verify_root`
report two SECURITY-channel violations — `attempt-route` and `frozen-route` —
while BOTH `amend` and `continue` still ACCEPT the root, and the root's own
published `REPLAY_VALIDATION.json` still says `valid: true`. Measured
2026-08-30, not re-derived here:
`experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.json`
(`jailbreak_open: true`; `arms.forged.amend = "ACCEPTED epoch=1"`,
`arms.forged.continue = "ACCEPTED seq=0"`, `arms.forged.stored_replay_valid =
true`) over root `experiments/2026-08-27-pc2b-symmetric-reasoning/run`.

This contradicts a documented guarantee in the operator's own words, ledgered
in CLAUDE.md as the 2026-08-29 P2 law: "checkpoints need to be hardned. I
don't want a jailbroken run to be continuable", read there as "`continue`
/`amend` are gated on the record verifying intact ... tampering with a record
must not buy a resumable run. Security boundary, not a convenience." The
2026-08-30 tranche states plainly that it did not satisfy this clause
(`proof/gate_collisions.md`, closing line).

Map ids resolved before design (map preflight, CLAUDE.md / dr-drive-harness §4):

| id | document | why it is in the reading |
|---|---|---|
| DR-INV-frozen-surfaces | `docs/map/INV-frozen-surfaces.md` | read FIRST; surface 3 (`invariants.py`, `verification/`) is CONSUMED here, never edited |
| DR-CON-run-identity | `docs/map/CON-run-identity.md` | owns the continue/amend lifecycle Traps entry this tranche must rewrite |
| DR-SUB-amendment | `docs/map/SUB-amendment.md` | `amend`'s refusal codes and their order |
| DR-SUB-verification | `docs/map/SUB-verification.md` | the channel taxonomy the gate's question is narrowed to |

Success criterion (machine-decidable):

    python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.py
        jailbreak_open: False
        and, in forge_amend_ready.json, arms.forged.amend and
        arms.forged.continue BOTH start with "REFUSED", while
        arms.intact.amend and arms.intact.continue BOTH still start with
        "ACCEPTED"  (the intact arm is half the criterion: a gate that
        refuses everything is not a gate)

    python -m pytest tests/ -q -n 4
        0 failed   (baseline 4590 passed; no lifecycle assertion weakened,
                    no test skipped, no test root exempted)

    python tools/docs_verify.py
        no failure beyond the list recorded in docs/AUDIT_BASELINES.md
        for this container class

In scope:
  - the `continue` precondition chain and the `amend` precondition chain
    (one shared typed-refusal definition serving both verbs)
  - `src/deepreason/application/results.py` — the typed reason surfaced
    to the operator
  - tests + `docs/map/` (moving in the same commits) + this tranche dir

NOT in scope: `src/deepreason/invariants.py` and `src/deepreason/verification/`
— the replay machinery is CONSUMED by import, never modified. Membership of
`_SECURITY_CHECKS` is READ; adding to it is a frozen-surface edit and a hard
STOP. Also NOT in scope: widening or repairing any of the `integrity`-channel
findings the 2026-08-30 tranche collided with (`amendment-chain`,
`attached-evidence`, `run-input`, `run-manifest-hash`, `terminal-authority`,
`open`) — those describe records that are incomplete or mid-repair, not
tampered with, and the roads that repair them stay open.

Budget: <=150 changed lines of production code, phase-boundary commits, one
session.

Stop conditions inherited from orchestrator: yes. Named additions for this
tranche:
  - `invariants.py` or `verification/` needing an EDIT -> STOP, park a brief.
  - the narrowed gate colliding with ANY lifecycle test -> STOP with the
    priced fork; never weaken an assertion, never exempt a test root
    (the 2026-08-30 tranche's own pre-registered rule P-FIX-3).
  - the per-`continue` cost of re-derivation proving unaffordable on the
    largest committed root -> STOP with the priced fork rather than shipping
    a gate that is right but unaffordable.
