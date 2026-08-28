#!/usr/bin/env python3
"""Q3 probe B -- how many cycles ever reached the wander cap at all.

`scheduler.py::_run_cycle` (2050-2062) is ordered:

    if self._simulation_capability_step():   # 2052
        self._cycles += 1                    # 2053   <-- denominator moves
        return                               # 2054   <-- returns BEFORE
    scan_spawns(...)                                  #      _select_problem
    problem = self._select_problem()         # 2056   <-- where wander.decide runs
    harness.record_measure(inputs=["cycle", ...])     # 2059  the heartbeat
    self._disclose_wander()                  # 2061   <-- where the reading is emitted

So a cycle taken by the simulation-capability step emits NO `cycle` heartbeat,
consults NO wander policy, and increments NO `_seed_cycles` -- while still
advancing `self._cycles`, which is the DENOMINATOR of the seed-lineage share.

This counts, per root: the terminal cycle count, the number of `cycle`
heartbeats actually emitted, and the number of seed-lineage-share readings.
The gap between the terminal cycle count and the heartbeat count is the number
of cycles that bypassed the cap.

Usage: q3_cycle_accounting.py <root> [<root> ...]
"""
import json
import pathlib
import sys
from collections import Counter


def report(root: pathlib.Path) -> dict:
    heartbeats = []
    shares = []
    throttles = 0
    capability_events = Counter()
    with (root / "log.jsonl").open() as fh:
        for line in fh:
            ev = json.loads(line)
            ins = [i for i in (ev.get("inputs") or []) if isinstance(i, str)]
            if ev.get("rule") == "Capability":
                capability_events[ins[0] if ins else "?"] += 1
            if not ins:
                continue
            if ins[0] == "cycle":
                heartbeats.append({"seq": ev["seq"], "cycle": ins[1], "problem": ins[2] if len(ins) > 2 else None})
            elif ins[0] == "allocation.seed-lineage-share.v1":
                shares.append({"seq": ev["seq"], "share": float(ins[1]), "floor": float(ins[2])})
            elif ins[0] == "allocation.wander-throttled.v1":
                throttles += 1
    status = json.loads((root / "run-status.json").read_text())
    terminal_cycle = status.get("cycle")
    seed_pid = None
    problem_hits = Counter(h["problem"] for h in heartbeats)
    for pid in problem_hits:
        if pid and pid.startswith("question-"):
            seed_pid = pid
    seed_hits = problem_hits.get(seed_pid, 0)
    return {
        "root": root.name,
        "terminal_cycle_in_status": terminal_cycle,
        "cycle_heartbeats_emitted": len(heartbeats),
        "cycles_that_bypassed_the_cap": (terminal_cycle - len(heartbeats))
        if isinstance(terminal_cycle, int) else None,
        "wander_readings": len(shares),
        "wander_throttles": throttles,
        "share_trajectory": [s["share"] for s in shares],
        "heartbeat_problem_counts": dict(problem_hits.most_common()),
        "seed_problem": seed_pid,
        "seed_share_of_heartbeat_cycles": round(seed_hits / len(heartbeats), 4) if heartbeats else None,
        "capability_event_counts": dict(capability_events.most_common()),
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2))
