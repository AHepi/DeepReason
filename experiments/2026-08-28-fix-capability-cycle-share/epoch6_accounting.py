#!/usr/bin/env python3
"""What epoch 6's 4-of-24 accounting becomes under the fix.

Reads the AUDIT's committed probe, not this tranche's own numbers:
`experiments/2026-08-28-audit-run-problems/probes/q3_cycle_accounting.json`.
Feeds the run's own cycle census through the SHIPPED policy
(`deepreason.wander`) three ways, and prints the three answers side by side.

The epoch-6 root itself is not on this branch -- it lives on the technique
branch, read-only evidence -- so the INTERLEAVING of its 20 capability cycles
among its 4 selection cycles is not re-derivable here. Nothing below needs it:
the governed denominator counts selection cycles, so the answer is the same for
every interleaving, and `test_the_denominator_is_order_independent` is the
proof of that rather than this script's assumption.

Usage: python experiments/2026-08-28-fix-capability-cycle-share/epoch6_accounting.py
"""
import json
import pathlib
import sys

sys.path.insert(0, "src")
from deepreason import wander  # noqa: E402
from deepreason.config import Config  # noqa: E402

PROBE = pathlib.Path(
    "experiments/2026-08-28-audit-run-problems/probes/q3_cycle_accounting.json"
)


def main() -> int:
    rows = json.loads(PROBE.read_text())
    epoch6 = next(r for r in rows if r["terminal_cycle_in_status"] == 24)
    census = epoch6["heartbeat_problem_counts"]
    seed_pid = epoch6["seed_problem"]

    capability = sum(
        n
        for pid, n in census.items()
        if pid.startswith(("simulation-result:", "simulation-request:", "simulation-interrupted:"))
    )
    cycles = epoch6["terminal_cycle_in_status"]
    selection = cycles - capability
    seed_worked = census.get(seed_pid, 0)

    print(f"probe:                {PROBE}")
    print(f"root:                 {epoch6['root']}")
    print(f"cycles:               {cycles}")
    print(f"  capability cycles:  {capability}")
    print(f"  selection cycles:   {selection}")
    print(f"  of those, seeded:   {seed_worked}")
    print(f"readings RECORDED:    {epoch6['wander_readings']}")
    print(f"throttles RECORDED:   {epoch6['wander_throttles']}")
    print(f"trajectory RECORDED:  {epoch6['share_trajectory']}")
    print()

    cfg = Config(SEED_PROBLEM_BUDGET_FLOOR=0.5)  # the defaults epoch 6 ran under
    fixed = wander.decide(
        cfg,
        wander.reading_from(
            cfg, cycles=cycles, seed_worked=seed_worked, capability_cycles=capability
        ),
    )
    diluted = wander.decide(
        cfg, wander.reading_from(cfg, cycles=cycles, seed_worked=seed_worked)
    )

    print("terminal reading, three ways")
    print(f"  as shipped (4 of 24 consulted): share {epoch6['share_trajectory'][-1]:.6f} "
          f"on 3 governed cycles, then 20 cycles UNRECORDED")
    print(f"  under the fix (capability out): share {fixed.share:.6f} "
          f"floor {fixed.floor:.6f} engaged={fixed.engaged}  "
          f"-- emitted on all {cycles} cycles")
    print(f"  consulted but diluted:          share {diluted.share:.6f} "
          f"floor {diluted.floor:.6f} engaged={diluted.engaged}")
    print()
    print(f"readings under the fix: {cycles} (one per cycle that advanced the counter)")
    print(f"  the {selection} on selection cycles: "
          f"{[f'{v:.6f}' for v in epoch6['share_trajectory']]} -- unchanged")
    print(f"  the {capability} on capability cycles: each repeats the reading current "
          f"at that point; after all {selection} selection cycles that is "
          f"{fixed.share:.6f}, at the floor")
    print(f"throttle records under the fix: 1 -- unchanged. Neither counter the "
          f"share is built from moves across a capability cycle, so the "
          f"engagement state cannot transition on one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
