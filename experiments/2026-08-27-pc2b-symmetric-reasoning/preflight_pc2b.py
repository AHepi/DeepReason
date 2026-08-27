#!/usr/bin/env python3
"""P-C2b's preflight: prove the two arms are SYMMETRIC before spending a token.

P-C2b's whole claim is that ARM H and ARM S differ in the machinery under
test and in NOTHING ELSE about how the model is called. That claim is worth
exactly as much as the checks that would catch it being false, so each one
below exists because a silent version of its failure has already happened in
this programme.

    S1  THE QUESTION HAS NOT DRIFTED. A rematch on a different question
        measures the question. Asserted by digest against P-C1's frozen value.

    S2  THE CONFIG DELTA FROM P-C1 IS EXACTLY WHAT P-C2b REGISTERED --
        `DISCHARGE_POLICY`, `reasoning` REMOVED, `timeout_s` raised -- and
        NOTHING ELSE. Fails on a superset as readily as on a mismatch. Note
        what is NOT in that list: `max_tokens` stays at P-C1's 32768, which
        is the symmetry with ARM S the operator's instruction requires.

    S3  THE DISCHARGE CHANNEL IS LIVE AT RUNTIME. P-C2's FINDING F-A: the
        policy is popped from the manifest's config echo, so a run reads the
        CODE DEFAULT and a YAML line naming it is inert. A P-C2b with the
        channel dark would be a different experiment wearing this one's name.

    S4  THE MODEL WILL ACTUALLY THINK. Built from the RECONSTRUCTED route via
        `providers.reasoning_body` -- the same call the adapter makes. ARM H2
        ran with thinking off and nothing typed said so; the confound was
        found by probing the endpoint afterwards.

    S5  THE SPLIT PROTOCOL ARMS, AND BOTH ARMS GET THE SAME LEGS. The
        operator's instruction: "The two arms must be SYMMETRIC in this: same
        model, same reasoning setting, same effective caps." This runs the
        SHIPPED planner against the reconstructed route and against
        `arm_s_split.py`'s own constants, and requires identical leg budgets.
        This is the check the tranche turns on.

Exit 0 = launch licensed by this file. Anything else = STOP.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
FRONTIER = REPO / "experiments" / "2026-08-25-change-constructive-frontier"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(FRONTIER))
sys.path.insert(0, str(TRANCHE))

QUESTION_SHA256 = "64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e"
DISCHARGE_FIELD = "DISCHARGE_POLICY"
P_C1_TIMEOUT_S = 180
PC2B_TIMEOUT_S = 900
P_C1_MAX_TOKENS = 32768  # UNCHANGED, deliberately: the symmetry with ARM S

_failures: list[str] = []
_report: dict = {"schema": "pc2b.preflight.v1", "checks": []}


def _check(cid: str, ok: bool, detail) -> None:
    _report["checks"].append({"id": cid, "ok": bool(ok), "detail": detail})
    print(f"[{'OK ' if ok else 'FAIL'}] {cid}: {detail}")
    if not ok:
        _failures.append(cid)


def s1_question() -> None:
    from deepreason.preparation import _question_digest
    from question import QUESTION

    digest = _question_digest(QUESTION)
    _check("S1-question-frozen", digest == QUESTION_SHA256,
           f"question_sha256={digest}")


def s2_config_delta() -> None:
    a = yaml.safe_load((FRONTIER / "run-config.yaml").read_text()) or {}
    b = yaml.safe_load((TRANCHE / "run-config.yaml").read_text()) or {}
    top = sorted(k for k in set(a) | set(b)
                 if a.get(k, "<absent>") != b.get(k, "<absent>"))
    seat = sorted({
        k
        for role in b.get("roles", {})
        for k in set(a["roles"][role]) | set(b["roles"][role])
        if a["roles"][role].get(k, "<absent>") != b["roles"][role].get(k, "<absent>")
    })
    thinking_on = all("reasoning" not in s for s in b.get("roles", {}).values())
    caps = {s.get("max_tokens") for s in b.get("roles", {}).values()}
    timeouts = {s.get("timeout_s") for s in b.get("roles", {}).values()}
    ok = (
        top == [DISCHARGE_FIELD, "roles"]
        and seat == ["reasoning", "timeout_s"]
        and thinking_on
        and caps == {P_C1_MAX_TOKENS}
        and timeouts == {PC2B_TIMEOUT_S}
        and b.get(DISCHARGE_FIELD) == "discharge-required.v1"
    )
    _check("S2-registered-delta-only", ok,
           f"top={top}; seat={seat}; thinking_on={thinking_on}; "
           f"caps={sorted(caps)} (must stay {P_C1_MAX_TOKENS}); "
           f"timeouts={sorted(timeouts)}; {DISCHARGE_FIELD}={b.get(DISCHARGE_FIELD)!r}")


def _runtime(root: Path):
    from deepreason.run_manifest import config_from_run_manifest, load_run_manifest

    return config_from_run_manifest(load_run_manifest(root / "run-manifest.json"))


def s3_channel_live(root: Path) -> None:
    from deepreason.discharge import resolve_policy

    runtime = _runtime(root)
    policy = resolve_policy(runtime)
    _check("S3-discharge-channel-live", bool(policy.enabled) and policy.handles_n > 0,
           f"runtime DISCHARGE_POLICY={runtime.DISCHARGE_POLICY!r} "
           f"enabled={policy.enabled} reask={policy.reask!r} handles_n={policy.handles_n}")


def _seat_specs(runtime) -> dict:
    out = {}
    for role, spec in runtime.roles.items():
        specs = spec if isinstance(spec, list) else [spec]
        for one in specs:
            out[role] = one if isinstance(one, dict) else json.loads(one.model_dump_json())
    return out


def s4_thinking_on(root: Path) -> None:
    from deepreason.llm.providers import reasoning_body

    specs = _seat_specs(_runtime(root))
    bodies = {r: reasoning_body(s.get("provider"), s.get("reasoning"))
              for r, s in specs.items()}
    _check("S4-thinking-ON-at-runtime",
           all(b == {} for b in bodies.values()) and len(bodies) == 11,
           f"{len(bodies)} seats; request-body reasoning field: "
           f"{sorted({json.dumps(b, sort_keys=True) for b in bodies.values()})} "
           f"(empty = no reasoning_effort sent = the model thinks)")


def s5_symmetric_split(root: Path) -> None:
    """THE CHECK THIS TRANCHE TURNS ON."""
    from deepreason.llm.split import plan_split

    import arm_s_split

    runtime = _runtime(root)
    specs = _seat_specs(runtime)
    mode = getattr(runtime, "SPLIT_BUDGET_SEAT_PROTOCOL", "auto")
    extraction = getattr(runtime, "SPLIT_BUDGET_EXTRACTION_TOKENS", 512)

    harness_plans = {
        role: plan_split(mode=mode, ceiling=spec.get("max_tokens"),
                         extraction_tokens=extraction,
                         provider=spec.get("provider"), reasoning=spec.get("reasoning"))
        for role, spec in specs.items()
    }
    sampler_plan = plan_split(
        mode="auto", ceiling=arm_s_split.CEILING,
        extraction_tokens=arm_s_split.EXTRACTION_TOKENS,
        provider="ollama", reasoning=None,
    )
    legs = {(p.armed, p.reason_max_tokens, p.extract_max_tokens, p.extract_reasoning)
            for p in harness_plans.values()}
    sampler_legs = (sampler_plan.armed, sampler_plan.reason_max_tokens,
                    sampler_plan.extract_max_tokens, sampler_plan.extract_reasoning)
    ok = (
        len(legs) == 1
        and sampler_plan.armed
        and legs == {sampler_legs}
        and arm_s_split.TIMEOUT_S == PC2B_TIMEOUT_S
    )
    _check("S5-arms-are-symmetric", ok,
           f"harness plan(s)={sorted(legs)}; sampler plan={sampler_legs}; "
           f"mode={mode!r} extraction={extraction}; "
           f"sampler timeout={arm_s_split.TIMEOUT_S} vs seat {PC2B_TIMEOUT_S}")
    _report["split"] = {
        "harness": sorted(str(x) for x in legs),
        "sampler": str(sampler_legs),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: preflight_pc2b.py <root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    s1_question()
    s2_config_delta()
    s3_channel_live(root)
    s4_thinking_on(root)
    s5_symmetric_split(root)
    (TRANCHE / "preflight_pc2b.json").write_text(
        json.dumps(_report, indent=1, sort_keys=True) + "\n")
    if _failures:
        print(f"\nPREFLIGHT FAILED: {_failures}", file=sys.stderr)
        return 1
    print("\nPREFLIGHT OK: the arms are symmetric and every organ under test is live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
