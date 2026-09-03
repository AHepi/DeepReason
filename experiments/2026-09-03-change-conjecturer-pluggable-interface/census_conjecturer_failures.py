"""Census: why conjecturer replies fail, per model and per pack shape.

Read-only over committed roots. Answers Amendment 1's M8 obligation --
"failure is a measured, input-shaped quantity" -- from the typed record
rather than from anyone's impression, including the operator's study.

Every number this prints names the instrument that produced it (the object
schema and the field), because a number without its instrument is not a fact
(`dr-ask-the-right-question` sec 1).

    python experiments/2026-09-03-change-conjecturer-pluggable-interface/\
census_conjecturer_failures.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT_GLOB = "objects/workflow-provider-attempt-v1/*.json"
CONJECTURER_CONTRACTS = {
    "conjecturer.turn.v6",
    "conjecturer.turn.v7",
    "conjecturer.atomic-candidate.v1",
}


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())["data"]


def _objects(root: pathlib.Path, schema: str) -> dict[str, dict]:
    directory = root / "objects" / schema
    if not directory.is_dir():
        return {}
    out = {}
    for path in directory.glob("*.json"):
        data = _load(path)
        out[data["id"]] = data
    return out


def main() -> int:
    base = pathlib.Path("experiments")
    roots = sorted({p.parent.parent.parent for p in base.rglob(ROOT_GLOB)})

    attempts_total = 0
    conj_attempts = 0
    by_contract: collections.Counter = collections.Counter()
    by_model: collections.Counter = collections.Counter()
    # (contract, model) -> Counter of terminal status/reason
    terminal: dict[tuple[str, str], collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    admission: dict[str, collections.Counter] = collections.defaultdict(
        collections.Counter
    )
    # completion-token distribution, the "cut off at the cap" axis
    completions: dict[str, list[int]] = collections.defaultdict(list)
    plan_kinds: collections.Counter = collections.Counter()
    roots_with_conj = 0

    for root in roots:
        attempts = _objects(root, "workflow-provider-attempt-v1")
        if not attempts:
            continue
        terminals = _objects(root, "workflow-work-terminal-v1")
        admissions = _objects(root, "workflow-semantic-admission-v1")
        for plan in _objects(root, "workflow-context-pack-plan-v1").values():
            plan_kinds[plan.get("plan_kind")] += 1

        # index the two downstream records by the attempt they judge
        terminal_by_attempt = {
            t.get("provider_attempt_ref"): t for t in terminals.values()
        }
        admission_by_attempt = {
            a.get("provider_attempt_ref"): a for a in admissions.values()
        }

        seen_conj = False
        for attempt in attempts.values():
            attempts_total += 1
            contract = attempt.get("contract_id")
            if contract not in CONJECTURER_CONTRACTS:
                continue
            seen_conj = True
            conj_attempts += 1
            lease = attempt.get("route_lease") or {}
            model = lease.get("endpoint_id") or "(unknown endpoint)"
            by_contract[contract] += 1
            by_model[model] += 1
            completions[contract].append(int(attempt.get("completion_tokens") or 0))

            key = (contract, model)
            term = terminal_by_attempt.get(attempt["id"])
            if term is None:
                terminal[key]["(no work terminal for this attempt)"] += 1
            else:
                terminal[key][f"{term.get('status')}/{term.get('reason_code')}"] += 1
            adm = admission_by_attempt.get(attempt["id"])
            if adm is not None:
                label = str(adm.get("outcome"))
                if adm.get("diagnostic_refs"):
                    label += f" (+{len(adm['diagnostic_refs'])} diagnostics)"
                admission[contract][label] += 1
        if seen_conj:
            roots_with_conj += 1

    print("CENSUS_CONJECTURER_FAILURES_V1")
    print(f"roots scanned (carry workflow-provider-attempt-v1): {len(roots)}")
    print(f"roots carrying conjecturer-contract attempts:       {roots_with_conj}")
    print(f"provider attempts, all roles:                       {attempts_total}")
    print(f"provider attempts on a conjecturer contract:        {conj_attempts}")
    print()
    print("-- by contract (workflow-provider-attempt-v1.contract_id) --")
    for contract, count in by_contract.most_common():
        values = sorted(completions[contract])
        median = values[len(values) // 2] if values else 0
        print(
            f"  {contract:36s} {count:5d}   completion tokens:"
            f" min {values[0] if values else 0}, median {median},"
            f" max {values[-1] if values else 0}"
        )
    print()
    print("-- by endpoint (workflow-provider-attempt-v1.route_lease.endpoint_id) --")
    for model, count in by_model.most_common():
        print(f"  {model:36s} {count:5d}")
    print()
    print("-- terminal outcome (workflow-work-terminal-v1.status/reason_code) --")
    for (contract, model), counter in sorted(terminal.items()):
        print(f"  {contract} @ {model}")
        for label, count in counter.most_common():
            print(f"      {count:5d}  {label}")
    print()
    print("-- semantic admission (workflow-semantic-admission-v1.outcome) --")
    for contract, counter in sorted(admission.items()):
        print(f"  {contract}")
        for label, count in counter.most_common():
            print(f"      {count:5d}  {label}")
    print()
    print("-- pack plans in the record (workflow-context-pack-plan-v1.plan_kind) --")
    for kind, count in plan_kinds.most_common():
        print(f"  {count:6d}  {kind}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
