"""Census: what actually blocks the STOPPED receipt on the four cited roots.

Re-runnable from the repo root:

    python experiments/2026-09-03-defect-stopped-run-resumption/proof/outstanding_census.py

Reports, per root, the two disjuncts of the refusal predicate at
`workflow/lifecycle.py:236` separately, because the whole diagnosis turns on
which of them fires.  Roots are opened READ-ONLY: a writable open repairs, and
therefore destroys, the evidence.
"""

from __future__ import annotations

from pathlib import Path

from deepreason.harness import Harness

ROOTS = {
    "P-A1 4565139800 (failed terminal)":
        "experiments/2026-09-01-live-all-modules-p-a1/run",
    "P-A2 e4 63e48f5741 (killed, then finalized)":
        "experiments/2026-09-02-live-p-a2-corrected/run",
    "1-cycle 292f964edb (clean)":
        "experiments/2026-09-03-change-provenance-history-channel/runs/home-default"
        "/runs/retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55",
    "4-cycle fe00609058 (clean control)":
        "experiments/2026-09-03-change-provenance-history-channel/runs/home-default"
        "/runs/run-fe00609058e10605590206d51ab2b7a0",
}


def main() -> int:
    for label, path in ROOTS.items():
        root = Path(path)
        if not root.exists():
            print(f"{label}: ABSENT ({path})")
            continue
        state = Harness(root, read_only=True).workflow_state
        outstanding = list(state.outstanding_work_order_ids)
        consumed = {r.source_call_seq for r in state.proposal_receipts.values()}
        orphaned = sorted(set(state.calls_by_seq) - consumed)
        print(f"\n{label}")
        print(f"  outstanding work items      : {len(outstanding)}")
        print(f"  unconsumed provider calls   : {len(orphaned)}  {orphaned[:8]}")
        print(f"  terminal_lifecycle_decision : "
              f"{state.terminal_lifecycle_decision is not None}")
        for work_id in outstanding:
            item = state.transaction_work.get(work_id)
            if item is None:
                order = state.work_orders.get(work_id)
                status = (state.recovery_status(work_id).value
                          if order is not None else "NO AUTHORITY")
                print(f"    - {work_id[:14]} legacy work order, recovery={status}")
                continue
            index = item.preparation.attempt_index
            attempt = item.provider_attempts.get(index)
            print(f"    - {work_id[:14]} kind={item.preparation.task_kind.name} "
                  f"outcome={attempt.outcome if attempt else None} "
                  f"admissions={sorted(item.admissions)} terminal={item.terminal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
