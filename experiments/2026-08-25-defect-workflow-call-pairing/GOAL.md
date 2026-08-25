# Goal: a transport-failure provider attempt must not make verify_root reject the run's own record

Class: defect

Observed: With the repair ladder reached (`python -u scripts/cycle_soak.py --case epoch3
--induce-repairs 2`), the run terminates typed and clean — `state='completed'`,
`stop_reason='budget_exhausted'`, cycle 8 of 8 — yet `verify_root` on its own root reports
`{'check': 'workflow-call-pairing', 'detail': 'event seq=31: provider result differs from its
authorized attempt'}`. Deterministic; parked as P1 in
`experiments/2026-08-23-change-cycle-soak-instrument/PARKED.md` with a byte-identical violation
across two prior recorded runs (there at seq=24, under that tranche's `--cycles 8` invocation).

Map ids (map preflight, per CLAUDE.md):
  - DR-SEAM-llm-x-workflow      (the seam that owns the one-bundle-one-request agreement)
  - DR-SUB-verification         (`verify_root`, the epistemic checks) — FROZEN, surface 3
  - DR-SUB-workflow             (`transaction.py`, `transaction_service.py`, `replay.py`)
  - DR-SUB-llm                  (`adapter.py`) — read only; the record decides before code
  - DR-INV-frozen-surfaces      (read before designing; surface 3 contact is possible here)
  - DR-SEAM-harness-x-verification (the second reader of the same six agreements)

Success criterion (machine-decidable):

    python -u scripts/cycle_soak.py --case epoch3 --induce-repairs 2 --out <tmp>
    exit 0, and the report's A3-verify-root-clean assertion PASSES with 0 violations

    python -m pytest tests/test_v6_transport_failure_pairing.py -q
    passes, and each of its assertions has been shown to FAIL on a mutated tree
    (mutation-proven in both directions: the fix removed, and the check's
    remaining five agreements broken one at a time)

    python -m pytest tests/ -q -n 4
    0 failed

In scope: `src/deepreason/invariants.py` (the `workflow-call-pairing` exact-pair comparison),
`scripts/cycle_soak.py` (EXPECTED_RED bookkeeping), `docs/` (map + AUDIT_BASELINES, same commit)

NOT in scope: `src/deepreason/llm/adapter.py`'s repair clamp (the `attempt != 0`
`WorkflowAuthorizationError` guard). PARKED.md P1 invites reading it as a suspect; it is the
nearest tempting neighbour and this tranche does not modify it. Also NOT in scope: P2, the
reservation-bound seam (`D4`), which belongs to its own window.

Budget: <=150 changed lines, 1 commit (plus phase-boundary artifact commits), ~3 hours
Stop conditions inherited from orchestrator: yes
