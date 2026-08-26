#!/usr/bin/env python3
"""P-C2's own preflight: prove the REMATCH is the rematch it registered.

P-C1's ladder already carries three preflights and this tranche re-runs all
of them unchanged (`preflight_criteria.py`, `mutation_proof.py`,
`preflight_models.py`).  This file adds the four checks that are specific to
P-C2, and every one of them exists because a SILENT version of the failure
it catches has already happened once in this program.

    S1  THE QUESTION HAS NOT DRIFTED.
        P-C2 is a rematch.  A rematch on a different question measures the
        question.  Asserted by digest against PREREG.md §2's frozen value.

    S2  THE CONFIG DIFFERS FROM P-C1's BY EXACTLY ONE FIELD.
        Same reason: any second field makes the comparison a comparison of
        two re-tuned launches.  Asserted by parsing both YAML files, not by
        reading a comment that claims it.

    S3  DEVIATION D1 IS IN FORCE -- THE DISCHARGE CHANNEL WILL ACTUALLY BE
        ON AT RUNTIME.
        This is the one that matters most, and it is the direct descendant
        of P-C1's killed run.  There, an in-run battery was INERT for
        eleven cycles and the record looked exactly like "the model could
        not do it".  Here the analogous silent failure is a discharge
        channel that is configured on, reads on in the YAML, and is OFF in
        the run -- which is the DEFAULT state of this tree (PREREG.md §3
        FINDING F-A).  A P-C2 that ran with the channel off would be a
        second P-C1 wearing P-C2's name, and nothing in the typed record
        would say so.  So the runtime Config is RECONSTRUCTED here exactly
        as `application/text_runs.py` reconstructs it, and the policy is
        asserted ENABLED.

    S4  THE MANIFEST DIFFERENCE FROM P-C1 IS FULLY ACCOUNTED FOR.
        Everything that moved must be a REBUILD tranche landing or a known
        provenance string.  An unexplained field is a stop: it would mean
        something other than the rebuild changed between the two runs, and
        the whole tranche rests on that not being true.

Exit 0 = launch is licensed by this file.  Any other exit = STOP.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
FRONTIER = REPO / "experiments" / "2026-08-25-change-constructive-frontier"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(FRONTIER))

QUESTION_SHA256 = "64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e"
THE_ONE_FIELD = "DISCHARGE_POLICY"
# PREREG Appendix A, Amendment 1 (operator, 2026-08-26: "pump to 100000").
ARM_H3_MAX_TOKENS = 100_000
# P-C1's cap, which ARM H2 also carried. Named so the accounting below asserts
# the change is FROM the registered old value, not merely TO the new one.
P_C1_MAX_TOKENS = 32_768
# Amendment 2 (operator, 2026-08-26: "Do it."). The field that was binding
# all along: 180s produced six stacked socket timeouts per call.
ARM_H3_TIMEOUT_S = 900
P_C1_TIMEOUT_S = 180


def _is_registered_seat_change(path: str, old_v, new_v) -> bool:
    """One manifest leaf that ARM H3's registered delta explains, or False.

    Whitelisting FIELD NAMES would admit any change to those fields. This
    asserts the whole transition -- which field, from what, to what -- so a
    cap that moved to some third number, or a `reasoning` that acquired a
    value instead of being removed, still fails.
    """
    if path.endswith("/reasoning"):
        return old_v == "none" and new_v is None
    if path.endswith("/max_tokens"):
        return old_v == P_C1_MAX_TOKENS and new_v == ARM_H3_MAX_TOKENS
    if path.endswith("/timeout_s"):
        return old_v == P_C1_TIMEOUT_S and new_v == ARM_H3_TIMEOUT_S
    return False

# S4's allowlist.  Each entry names the REBUILD tranche that owns the change,
# so an unexplained field cannot hide behind a vague "expected differences".
ACCOUNTED_MANIFEST_PATHS = {
    "/research/enabled": "REBUILD F3 -- research channel on by default",
    "/research/backend_identity": "REBUILD F3 -- research channel on by default",
    "/research/domain_allowlist": "REBUILD F3 -- the default frozen allowlist an enabled research channel requires",
    "/research/maximum_requests": "REBUILD F3 -- research channel on by default",
    "/research/maximum_sources": "REBUILD F3 -- research channel on by default",
    "/research/maximum_response_bytes": "REBUILD F3 -- research channel on by default",
}
ACCOUNTED_TOP_LEVEL = {
    "inquiry_capability_policy": "carrier of the F3 research rows above",
    "run_input_digest": "the empty dossier's creation_provenance names THIS builder",
}

_failures: list[str] = []
_report: dict = {"schema": "pc2.preflight.v1", "checks": []}


def _leaf_delta(x, y, path=""):
    """Every differing leaf between two JSON trees, as (path, old, new)."""
    out = []
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            out += _leaf_delta(x.get(k), y.get(k), f"{path}/{k}")
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        for i, (u, v) in enumerate(zip(x, y)):
            out += _leaf_delta(u, v, f"{path}[{i}]")
    elif x != y:
        out.append((path, x, y))
    return out


def _check(cid: str, ok: bool, detail) -> None:
    _report["checks"].append({"id": cid, "ok": bool(ok), "detail": detail})
    print(f"[{'OK ' if ok else 'FAIL'}] {cid}: {detail}")
    if not ok:
        _failures.append(cid)


def s1_question() -> None:
    from deepreason.preparation import _question_digest
    from question import QUESTION

    digest = _question_digest(QUESTION)
    _check(
        "S1-question-frozen",
        digest == QUESTION_SHA256,
        f"question_sha256={digest} (PREREG §2 froze {QUESTION_SHA256})",
    )


def s2_config_delta() -> None:
    """The delta from P-C1's config must be EXACTLY what the arm registered.

    ARM H2 (PREREG §4) registers ONE differing field. ARM H3 (Appendix A)
    registers TWO: the same one, plus `reasoning` REMOVED from every seat.
    Any third field means the rematch is comparing two re-tuned launches, so
    this fails on a superset as readily as on a mismatch.
    """
    import os

    config_name = os.environ.get("PC2_CONFIG", "run-config.yaml")
    arm = "H3" if "h3" in config_name else "H2"
    a = yaml.safe_load((FRONTIER / "run-config.yaml").read_text()) or {}
    b = yaml.safe_load((TRANCHE / config_name).read_text()) or {}
    delta = sorted(
        k for k in set(a) | set(b) if a.get(k, "<absent>") != b.get(k, "<absent>")
    )

    if arm == "H2":
        ok = delta == [THE_ONE_FIELD]
        detail = f"expected exactly [{THE_ONE_FIELD!r}]"
    else:
        # `reasoning` lives INSIDE each role, so the top-level delta is
        # `roles`. The seat-level delta is checked explicitly rather than
        # inferred from it: a `roles` difference could be anything.
        seat_delta = sorted(
            k
            for role in b.get("roles", {})
            for k in set(a["roles"][role]) | set(b["roles"][role])
            if a["roles"][role].get(k, "<absent>") != b["roles"][role].get(k, "<absent>")
        )
        thinking_on = all(
            "reasoning" not in spec for spec in b.get("roles", {}).values()
        )
        # Amendment 1 (operator, "pump to 100000") adds max_tokens to ARM H3's
        # registered delta. Both values are asserted, not just the field names:
        # a cap that drifted to some third number would be a third difference.
        caps = {spec.get("max_tokens") for spec in b.get("roles", {}).values()}
        timeouts = {spec.get("timeout_s") for spec in b.get("roles", {}).values()}
        ok = (
            delta == [THE_ONE_FIELD, "roles"]
            and set(seat_delta) == {"reasoning", "max_tokens", "timeout_s"}
            and thinking_on
            and caps == {ARM_H3_MAX_TOKENS}
            and timeouts == {ARM_H3_TIMEOUT_S}
        )
        detail = (
            f"expected [{THE_ONE_FIELD!r}, 'roles'] with the ONLY seat-level "
            f"deltas being `reasoning` REMOVED, `max_tokens` = "
            f"{ARM_H3_MAX_TOKENS} and `timeout_s` = {ARM_H3_TIMEOUT_S}; "
            f"seat delta={sorted(set(seat_delta))}, reasoning absent on every "
            f"seat={thinking_on}, caps={sorted(caps)}, timeouts={sorted(timeouts)}"
        )

    _check(
        "S2-registered-delta-only",
        bool(ok) and b.get(THE_ONE_FIELD) == "discharge-required.v1",
        f"ARM {arm} via {config_name}: fields differing from P-C1's config: "
        f"{delta}; {detail}; {THE_ONE_FIELD}={b.get(THE_ONE_FIELD)!r}",
    )


def s3_channel_live(root: Path) -> None:
    """The check P-C1's killed run bought."""
    from deepreason.discharge import resolve_policy
    from deepreason.run_manifest import config_from_run_manifest, load_run_manifest

    manifest = load_run_manifest(root / "run-manifest.json")
    runtime = config_from_run_manifest(manifest)
    policy = resolve_policy(runtime)
    _check(
        "S3-discharge-channel-live-at-runtime",
        bool(policy.enabled) and policy.handles_n > 0,
        f"runtime DISCHARGE_POLICY={runtime.DISCHARGE_POLICY!r} "
        f"enabled={policy.enabled} reask={policy.reask!r} "
        f"handles_n={policy.handles_n} "
        f"(deviation D1 absent would read 'off' here)",
    )


def s5_thinking_on(root: Path) -> None:
    """ARM H3 ONLY: prove the model will actually THINK.

    This is S3's sibling and it exists for the same reason. ARM H2 ran with
    `reasoning_effort: "none"` and nothing in its typed record said the model
    was not thinking -- the confound was found only by probing the endpoint
    afterwards. An ARM H3 that silently kept thinking off would be ARM H2
    wearing a new name, and no artifact would say so.

    Asserted where it actually bites: the body `providers.reasoning_body`
    builds from the RECONSTRUCTED runtime route, which is what the adapter
    sends. An empty body means no `reasoning_effort` field, which is what
    makes glm-5.2 think (measured: 9712 completion tokens vs 177).
    """
    from deepreason.llm.providers import reasoning_body
    from deepreason.run_manifest import config_from_run_manifest, load_run_manifest

    manifest = load_run_manifest(root / "run-manifest.json")
    runtime = config_from_run_manifest(manifest)
    bodies = {}
    for role, spec in runtime.roles.items():
        specs = spec if isinstance(spec, list) else [spec]
        for one in specs:
            data = one if isinstance(one, dict) else json.loads(one.model_dump_json())
            bodies[role] = reasoning_body(data.get("provider"), data.get("reasoning"))
    every_seat_thinks = all(body == {} for body in bodies.values())
    _check(
        "S5-thinking-ON-at-runtime",
        every_seat_thinks and len(bodies) == 11,
        f"{len(bodies)} seats; request-body reasoning field per seat: "
        f"{sorted({json.dumps(b, sort_keys=True) for b in bodies.values()})} "
        f"(an empty body = no reasoning_effort sent = the model thinks)",
    )


def s4_manifest_delta(root: Path) -> None:
    from deepreason.run_manifest import load_run_manifest

    a = load_run_manifest(FRONTIER / "run" / "run-manifest.json")
    b = load_run_manifest(root / "run-manifest.json")

    unexplained: list[str] = []

    ca, cb = json.loads(a.engine_config_json), json.loads(b.engine_config_json)
    echo_delta = sorted(
        k for k in set(ca) | set(cb) if ca.get(k, "<absent>") != cb.get(k, "<absent>")
    )
    unexplained += [f"engine_config_json:{k}" for k in echo_delta]

    da, db = json.loads(a.model_dump_json()), json.loads(b.model_dump_json())
    arm_h3 = "h3" in os.environ.get("PC2_CONFIG", "")
    for key in sorted(set(da) | set(db)):
        if key == "engine_config_json" or da.get(key) == db.get(key):
            continue
        if key in ACCOUNTED_TOP_LEVEL:
            continue
        # ARM H3's registered change is `reasoning` REMOVED from every seat.
        # That is accounted STRUCTURALLY, not by naming keys: each of the three
        # affected fields must differ ONLY in the leaf the change can reach, or
        # something else moved and this must still fail.
        if arm_h3 and key == "roles":
            leaves = _leaf_delta(da[key], db[key])
            if leaves and all(
                _is_registered_seat_change(path, old_v, new_v)
                for path, old_v, new_v in leaves
            ):
                _report["arm_h3_roles_delta"] = sorted(
                    {p.rsplit("/", 1)[-1] for p, _, _ in leaves}
                )
                continue
        if arm_h3 and key in (
            "route_seat_behavioral_capability_plan",
            "route_seat_contract_decomposition_plan",
        ):
            leaves = _leaf_delta(da[key], db[key])
            # Two kinds of leaf, and both are DERIVED from the registered seat
            # change rather than independent of it: the plan echoes the seat's
            # completion cap, and the route digest must move when the route
            # does. Every digest must move to the SAME new value, or the seats
            # have stopped sharing one route -- which would be a real finding.
            digests = {new_v for path, _, new_v in leaves if path.endswith("/route_sha256")}
            if leaves and all(
                path.endswith("/route_sha256")
                or (
                    path.endswith("/maximum_completion_tokens")
                    and old_v == P_C1_MAX_TOKENS
                    and new_v == ARM_H3_MAX_TOKENS
                )
                for path, old_v, new_v in leaves
            ) and len(digests) <= 1:
                continue
        if arm_h3 and key == "source_config_hash":
            continue  # the digest of the config file this arm registered
        unexplained.append(f"manifest:{key}")

    pa = json.loads(a.inquiry_capability_policy.model_dump_json())
    pb = json.loads(b.inquiry_capability_policy.model_dump_json())
    leaves: list[str] = []

    def walk(x, y, path=""):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                walk(x.get(k), y.get(k), f"{path}/{k}")
        elif x != y:
            leaves.append(path)

    walk(pa, pb)
    unexplained += [
        f"inquiry_capability_policy{p}"
        for p in leaves
        if p not in ACCOUNTED_MANIFEST_PATHS
    ]

    _check(
        "S4-manifest-delta-accounted",
        not unexplained,
        (
            f"accounted: {len(leaves)} policy leaf/leaves "
            f"+ {sorted(ACCOUNTED_TOP_LEVEL)}; unexplained: {unexplained or 'none'}"
        ),
    )
    _report["manifest_delta"] = {
        "pc1_sha256": a.sha256,
        "pc2_sha256": b.sha256,
        "inquiry_policy_leaves": {p: ACCOUNTED_MANIFEST_PATHS.get(p, "UNEXPLAINED") for p in leaves},
        "engine_config_echo_delta": echo_delta,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: preflight_pc2.py <root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])

    s1_question()
    s2_config_delta()
    s3_channel_live(root)
    if "h3" in os.environ.get("PC2_CONFIG", ""):
        s5_thinking_on(root)
    s4_manifest_delta(root)

    (TRANCHE / "preflight_pc2.json").write_text(
        json.dumps(_report, indent=1, sort_keys=True) + "\n"
    )
    if _failures:
        print(f"\nPREFLIGHT FAILED: {_failures}", file=sys.stderr)
        return 1
    print("\nPREFLIGHT OK: all four P-C2-specific checks hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
