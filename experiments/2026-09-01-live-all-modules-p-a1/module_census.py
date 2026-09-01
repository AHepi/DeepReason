#!/usr/bin/env python3
"""The module-coverage census: what fired, proven from the typed record only.

MODULE_COVERAGE.md is this tranche's headline artifact, and this script is
what fills it. One row per module, and every row is either a count of typed
events with the event ids that carry them, or the typed REASON the module did
not fire. Nothing here reads model prose, and nothing here forms an opinion:
a module that did not fire is a recorded RESULT, not a failure to hide.

The evidence surfaces, in the order they are trusted:

  log.jsonl        the append-only record -- `rule`, `inputs[0]` (the signal
                   name), `llm.role`, and `state_diff` (`hv_set`, `reach_set`,
                   `status_changed`) -- which is the only place a claim about
                   what a run DID can come from
  run-status.json  state
  run-stop.json    the typed stop reason
  objects/         registered artifacts by type
  the bridge JSONs written by the ladder

Usage:  python module_census.py <root>
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent


def _load_events(root: Path) -> list[dict]:
    path = root / "log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:  # noqa: BLE001 - an absent or unreadable file is a typed absence
        return None


def census(root: Path) -> dict:
    events = _load_events(root)
    rules = collections.Counter(e.get("rule") for e in events)
    roles = collections.Counter(
        (e.get("llm") or {}).get("role") for e in events if e.get("llm")
    )
    signals = collections.Counter(
        str((e.get("inputs") or [""])[0]) for e in events if e.get("inputs")
    )
    seq_of: dict[str, list[int]] = collections.defaultdict(list)
    for e in events:
        ins = e.get("inputs") or []
        if ins:
            seq_of[str(ins[0])].append(e.get("seq"))

    hv_events = [e["seq"] for e in events if (e.get("state_diff") or {}).get("hv_set")]
    reach_events = [
        e["seq"] for e in events if (e.get("state_diff") or {}).get("reach_set")
    ]
    status_events = [
        e["seq"] for e in events if (e.get("state_diff") or {}).get("status_changed")
    ]
    scratch_events = [e["seq"] for e in events if e.get("scratch")]

    def prefixed(prefix: str) -> dict[str, int]:
        return {k: v for k, v in signals.items() if k.startswith(prefix)}

    def first_seqs(names, limit: int = 3) -> list[int]:
        out: list[int] = []
        for name in names:
            out.extend(seq_of.get(name, ())[:limit])
        return sorted(s for s in out if s is not None)[:limit]

    deferred = collections.Counter()
    for e in events:
        ins = e.get("inputs") or []
        if ins and ins[0] == "v6-model-phase-deferred.v1" and len(ins) >= 3:
            deferred[(ins[1], ins[2])] += 1

    split_legs = collections.Counter()
    for e in events:
        for trace in ((e.get("llm") or {}).get("attempt_trace") or ()):
            for leg in (trace.get("split_legs") or ()):
                split_legs[leg.get("leg") or "(unnamed)"] += 1

    objects = {}
    obj_dir = root / "objects"
    if obj_dir.is_dir():
        objects = {p.name: len(list(p.glob("*.json"))) for p in obj_dir.iterdir() if p.is_dir()}

    status = _read_json(root / "run-status.json") or {}
    stop = _read_json(root / "run-stop.json") or {}
    result = _read_json(root / "run-result.json") or {}

    rows: list[dict] = []

    def row(module: str, fired: bool, evidence, note: str = "") -> None:
        rows.append(
            {
                "module": module,
                "verdict": "FIRED" if fired else "did-not-fire",
                "evidence": evidence if fired else (note or evidence),
            }
        )

    row("conjecture (rules/conj)", rules.get("Conj", 0) > 0,
        f"Conj events={rules.get('Conj', 0)}, conjecturer calls={roles.get('conjecturer', 0)}")
    row("criticism (rules/crit)", rules.get("Crit", 0) > 0,
        f"Crit events={rules.get('Crit', 0)}, argumentative_critic calls={roles.get('argumentative_critic', 0)}")
    row("defender seat", roles.get("defender", 0) > 0,
        f"defender calls={roles.get('defender', 0)}",
        "no defender call in the record")
    row("judge ensemble", roles.get("judge", 0) > 0,
        f"judge calls={roles.get('judge', 0)}",
        "no judge call in the record")
    row("defended trial (status-changing criticism)",
        signals.get("scrutiny", 0) < rules.get("Crit", 0) and roles.get("judge", 0) > 0,
        f"judge calls={roles.get('judge', 0)}, scrutiny observations={signals.get('scrutiny', 0)}, "
        f"Crit events={rules.get('Crit', 0)}",
        f"every criticism filed as scrutiny (observe_only shape): scrutiny={signals.get('scrutiny', 0)}")
    row("adjudication / status authority", bool(status_events),
        f"{len(status_events)} events carry status_changed; first seqs {status_events[:3]}",
        "no event carries status_changed")
    row("variator / hv measurement", bool(hv_events),
        f"{len(hv_events)} events carry hv_set; first seqs {hv_events[:3]}; "
        f"variator calls={roles.get('variator', 0)}",
        f"NO hv_set in the record; variator calls={roles.get('variator', 0)}; "
        f"deferrals={sum(v for k, v in deferred.items() if k[1] == 'variator')}")
    row("reach measurement", bool(reach_events),
        f"{len(reach_events)} events carry reach_set; first seqs {reach_events[:3]}",
        "NO reach_set in the record")
    row("scratchpad (advisory workshop)", bool(scratch_events),
        f"{len(scratch_events)} events carry a scratch payload; "
        f"Scratch rule events={rules.get('Scratch', 0)}",
        "no event carries a scratch payload")
    row("successor questions", bool(prefixed("successor")),
        prefixed("successor"),
        "no successor-* signal in the record")
    row("simulation capability", "SIMULATION" in json.dumps(objects) or bool(prefixed("simulation")),
        {"signals": prefixed("simulation"), "objects": objects},
        f"no simulation-* signal; deferrals={dict(deferred)}")
    row("research capability", bool(prefixed("research")),
        prefixed("research"),
        "no research-* signal in the record")
    row("attached evidence / dossier", bool(prefixed("evidence-citation")),
        prefixed("evidence-citation"),
        "the channel is OPEN but the dossier is EMPTY by design (PREREG §4 R6): "
        "nothing to cite is the typed reason, not a malfunction")
    row("premise channel", bool(prefixed("premise")),
        prefixed("premise"),
        "no premise-* signal in the record")
    row("discharge channel", bool(prefixed("discharge")),
        prefixed("discharge"),
        "no discharge-* signal in the record")
    row("near-duplicate / anti-relapse gate",
        (root / "relapse.log.jsonl").exists() or bool(prefixed("relapse")),
        {"relapse.log.jsonl": (root / "relapse.log.jsonl").exists(),
         "signals": prefixed("relapse")},
        "no relapse receipt and no relapse-* signal")
    row("school convergence / reseed", bool(prefixed("school")) or bool(prefixed("reseed")),
        {**prefixed("school"), **prefixed("reseed")},
        "no school-convergence or reseed signal (the tripwires are armed and did not fire)")
    row("allocation controller / signals", bool(prefixed("controller")) or bool(prefixed("allocation")),
        {**prefixed("controller"), **prefixed("allocation")},
        "no controller-* or allocation-* signal")
    row("config referee", bool(prefixed("config-referee")) or "config-referee" in json.dumps(list(signals)),
        prefixed("config-referee"),
        "no config-referee signal in the record")
    row("split-budget seat protocol", bool(split_legs),
        dict(split_legs),
        "no attempt recorded a split_legs structure")
    row("capture / Pareto frontier", bool(prefixed("capture")),
        prefixed("capture"),
        "no capture-* signal in the record")

    bridge_build = _read_json(TRANCHE / "bridge-build.json")
    bridge_result = _read_json(TRANCHE / "bridge-result.json")
    row("grounded bridge (ledger + composition)",
        bool(bridge_build) and not (
            isinstance(bridge_build, dict) and bridge_build.get("error")
        ),
        {"build": bridge_build if isinstance(bridge_build, dict) else None,
         "result_present": bridge_result is not None,
         "ledger_role_calls": roles.get("summarizer", 0),
         "composer_role_calls": roles.get("thesis", 0),
         "grounding_reviewer_calls": roles.get("grounding_reviewer", 0)},
        "bridge build produced no readable JSON -- see bridge-build.stderr.log")

    verify = _read_json(TRANCHE / "verify_root.json")
    row("replay validation (verify_root)", verify is not None,
        {"violations": len(verify.get("violations", ())) if isinstance(verify, dict) else None}
        if isinstance(verify, dict) else verify,
        "verify_root produced no readable JSON")

    # --- the three known-open defects this tranche MEASURES ---------------
    frontier_members = []
    seed_problem = None
    problem = _read_json(root / "problem.json")
    if isinstance(problem, dict):
        seed_problem = (problem.get("problem") or {}).get("id")

    measured = {
        "D1_frontier_composition": {
            "note": "PREREG §6.1 -- how many frontier members answer the "
                    "operator's seed question vs a harness-minted problem",
            "seed_problem_id": seed_problem,
            "problems_spawned": rules.get("Spawn", 0),
            "frontier_txt": "see frontier.txt (the typed surface)",
            "members": frontier_members,
        },
        "D2_criticism_to_new_problem_trigger_rate": {
            "note": "PREREG §6.2 -- P-S1 measured 0 of 1,293",
            "criticisms": rules.get("Crit", 0),
            "successor_signals": prefixed("successor"),
            "spawn_events": rules.get("Spawn", 0),
        },
        "D3_premise_citation_rate": {
            "note": "PREREG §6.3 -- P-S1 measured 1 CITED against 122 DECLINED",
            "premise_signals": prefixed("premise"),
            "citation_signals": prefixed("premise-citation"),
        },
    }

    return {
        "root": str(root),
        "run_state": status.get("state") or result.get("state"),
        "stop_reason": stop.get("reason"),
        "events": len(events),
        "rules": dict(rules),
        "llm_calls_by_role": {k: v for k, v in roles.items() if k},
        "deferred_model_phases": {f"{k[0]}/{k[1]}": v for k, v in deferred.items()},
        "top_signals": dict(collections.Counter(signals).most_common(40)),
        "objects": objects,
        "modules": rows,
        "measured": measured,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: module_census.py <root>", file=sys.stderr)
        return 2
    print(json.dumps(census(Path(sys.argv[1])), indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
