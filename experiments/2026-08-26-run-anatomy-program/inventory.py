"""Root inventory for the RUN ANATOMY PROGRAM.

Enumerates every committed run root on main and records the facts the
program's three windows route on: run id, dates, terminal, and the
configuration shape (seats, roles, capability opt-ins, policies).

A "root" is a directory carrying BOTH run-status.json and log.jsonl.
run-status.json alone is not a root: 2026-08-21-fix-wheel-smoke-reason-stage
commits a bare status file as smoke evidence, and it is listed as excluded
rather than silently dropped.

Read-only. Writes ROOT_INVENTORY.json beside itself.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


def tracked_status_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [p for p in out if p.endswith("run-status.json")]


def first_and_last(path: str) -> tuple[str | None, str | None, int]:
    first = last = None
    n = 0
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n += 1
            if first is None:
                first = json.loads(line).get("ts")
            last = line
    return first, (json.loads(last).get("ts") if last else None), n


def config_shape(root: str) -> dict:
    """Configuration shape from the run manifest, if the root carries one.

    `roles` maps a role name to a LIST of endpoint specs — one per seat — so
    seat count is the list length, and the models a role may reach are that
    list's model_ids. Capability opt-ins are nested policy objects each
    carrying their own `enabled` flag; a policy present but disabled is not
    an opt-in.
    """
    mp = os.path.join(root, "run-manifest.json")
    if not os.path.exists(mp):
        return {"manifest": False}
    m = json.load(open(mp))

    roles = m.get("roles") or {}
    seats, role_models = [], {}
    if isinstance(roles, dict):
        for role, spec in sorted(roles.items()):
            specs = spec if isinstance(spec, list) else [spec]
            seats.append(f"{role}x{len(specs)}")
            role_models[role] = sorted(
                {s.get("model_id") for s in specs if isinstance(s, dict) and s.get("model_id")}
            )

    cap = m.get("inquiry_capability_policy") or {}
    enabled = []
    if isinstance(cap, dict):
        for name, policy in sorted(cap.items()):
            if isinstance(policy, dict) and policy.get("enabled") is True:
                enabled.append(name)

    repair = m.get("contract_schema_repair_policy") or {}
    grants = {}
    for g in (repair.get("grants") or []) if isinstance(repair, dict) else []:
        grants[g.get("contract_id")] = {
            "maximum_provider_calls": g.get("maximum_provider_calls"),
            "maximum_schema_repairs": g.get("maximum_schema_repairs"),
        }

    decomp = m.get("route_seat_contract_decomposition_plan") or {}
    ladders = {}
    for e in (decomp.get("entries") or []) if isinstance(decomp, dict) else []:
        ladders[e.get("source_contract_id")] = e.get("atomic_contract_id")

    return {
        "manifest": True,
        "schema_version": m.get("schema_version"),
        "engine_profile": m.get("engine_profile"),
        "model_profile": m.get("model_profile"),
        "pack_profile": m.get("pack_profile"),
        "seats": seats,
        "role_models": role_models,
        "capability_opt_ins": enabled,
        "repair_grants": grants,
        "decomposition_ladders": ladders,
    }


def endpoints_and_contracts(root: str) -> dict:
    """Which models and which form contracts this root actually exercised."""
    models: dict[str, int] = {}
    contracts: dict[str, int] = {}
    roles: dict[str, int] = {}
    attempts = 0
    with open(os.path.join(root, "log.jsonl")) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            llm = json.loads(line).get("llm")
            if not llm:
                continue
            models[llm.get("model") or "?"] = models.get(llm.get("model") or "?", 0) + 1
            roles[llm.get("role") or "?"] = roles.get(llm.get("role") or "?", 0) + 1
            for t in llm.get("attempt_trace") or []:
                attempts += 1
                cid = t.get("contract_id") or "?"
                contracts[cid] = contracts.get(cid, 0) + 1
    return {
        "provider_attempts": attempts,
        "models": dict(sorted(models.items())),
        "roles": dict(sorted(roles.items())),
        "contracts": dict(sorted(contracts.items())),
    }


def main() -> int:
    roots, excluded = [], []
    for status in sorted(tracked_status_files()):
        root = status[: -len("/run-status.json")]
        abs_root = os.path.join(REPO, root)
        log = os.path.join(abs_root, "log.jsonl")
        if not os.path.isdir(abs_root) or not os.path.exists(log):
            excluded.append({"path": status, "why": "no log.jsonl beside run-status.json"})
            continue
        st = json.load(open(os.path.join(abs_root, "run-status.json")))
        first, last, nlog = first_and_last(log)
        rec = {
            "root": root,
            "run_id": st.get("run_id"),
            "state": st.get("state"),
            "stop_reason": st.get("stop_reason"),
            "cycles_reached": st.get("cycle"),
            "token_spend": st.get("token_spend"),
            "token_limit": st.get("token_limit"),
            "first_ts": first,
            "last_ts": last,
            "log_events": nlog,
            "config_shape": config_shape(abs_root),
        }
        rec.update(endpoints_and_contracts(abs_root))
        roots.append(rec)

    doc = {
        "schema": "run-anatomy.root-inventory.v1",
        "generated_from": "git ls-files '*run-status.json' on the checked-out tree",
        "root_count": len(roots),
        "excluded": excluded,
        "roots": roots,
    }
    dest = os.path.join(HERE, "ROOT_INVENTORY.json")
    with open(dest, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"{len(roots)} roots, {len(excluded)} excluded -> {dest}")
    print(f"total provider attempts: {sum(r['provider_attempts'] for r in roots)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
