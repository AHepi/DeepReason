# Goal: the installed-wheel operational smoke's `reason` stage fails its terminal-verification assertion on an unmodified tree, intermittently

Class: defect

Observed: `python -u scripts/wheel_operational_smoke.py` on a clean tree at
`d52c739ff` (and reproduced at `c7e605553`) fails with
`AssertionError: terminal verification is incomplete`, raised by
`_assert_resumable_terminal` at `scripts/wheel_operational_smoke.py:2061`.
The emitted failure envelope carries `"stage":"reason"`,
`"failure_kind":"assertion_failed"`, `"mcp_liveness":"exited"`, and every
terminalization phase counter at 0. Evidence pointer:
`experiments/2026-08-16-change-embedder-auto-install/` CHECKLIST step 21
(established 2026-08-16; the failure predates that tranche). The stage is
FLAKY: three observations on one container gave pass, fail, fail.

The assertion requires ALL FIVE of:
  1. `verification.completion_satisfied`
  2. `verification.epistemic_checks_passed`
  3. `verification.operational_checks_passed`
  4. `completion_status == "satisfied"`
  5. `stop.reason == "converged"`

Success criterion (machine-decidable):

    python -u scripts/wheel_operational_smoke.py   # repeated N>=5 times
    echo $?                                        # 0 every time

    python -m pytest tests/ -q -n 4                # 0 failed
    python tools/docs_verify.py                    # baseline failures only
    python scripts/wheel_smoke.py                  # exit 0

plus, if the instrument is the defective side, a MUTATION PROOF: the narrowed
assertion must still fail when the condition it exists to catch is broken.

In scope (max 3):
  - `scripts/wheel_operational_smoke.py` (the instrument)
  - `src/deepreason/application/text_runs.py` (`terminalize_text_run`, the ONE
    stop-to-published path — `DR-SUB-application`)
  - `docs/AUDIT_BASELINES.md` wheel-smoke entry

NOT in scope: the pre-existing, baseline-listed wheel-smoke failures naming
MCP schema sha / tool-set pins (docs/AUDIT_BASELINES.md line 42-47), and the
three pre-existing `CON-run-identity.md` shallow-clone docs_verify failures.
Also NOT in scope: `verify_root` / replay-validation record FORMATS
(`DR-INV-frozen-surfaces` surface 3) — readers may be fixed, formats may not.

Budget: <=150 changed lines, 1 commit, a few hours.
Stop conditions inherited from orchestrator: yes

## Map preflight (ids resolved before designing)

- `DR-SUB-application` — `docs/map/SUB-application.md`. Owns
  `terminalize_text_run`, "the ONE stop-to-published-... path" (line 78), and
  the row "What ANY finished run writes at stop ... `terminalize_text_run`"
  (line 207).
- `DR-CON-run-identity` — `docs/map/CON-run-identity.md` line 55: "The one
  route to a terminal, for the one launch path ... `terminalize_text_run`
  (called by `_worker` and by `finalize_stopped_root`)".
- `DR-SUB-verification` — `docs/map/SUB-verification.md`: `verify_root`,
  replay validation, epistemic checks. **Frozen** (surface 3).
- `DR-INV-frozen-surfaces` — read before designing. Surface 3 (replay-
  validation record formats) is the one this tranche can touch by accident;
  surfaces 1, 2, 4, 5 are not near this work.
- `DR-SEAM-periphery-x-verification` — read; it governs attached-evidence
  records, NOT terminal completion/epistemic/operational verification, so it
  is adjacent rather than covering.
- GAP: no map document covers the wheel smokes as an instrument. `INV-frozen-
  surfaces.md` §"The instruments that prove you did not break anything" names
  the gate and the sweep; `dr-drive-harness` §4 names the smokes as the third
  instrument that "NO gate runs for you". If the fix lands in the instrument,
  writing that coverage is part of this tranche.

## Flakiness is part of the goal

A stage that passes sometimes means either (a) a real race in terminalization
(harness defect) or (b) an assertion on a value legitimately allowed to vary
(instrument defect). These have OPPOSITE fixes. The diagnosis must name one,
with a repeat count behind it, before any fix is proposed.
