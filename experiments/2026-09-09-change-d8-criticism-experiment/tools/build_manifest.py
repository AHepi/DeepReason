#!/usr/bin/env python3
"""The three harness arms, compiled from ONE base configuration — SPEC S3/S5/A1.

    python build_manifest.py --arm {C,V,A} --root DIR [--critic-endpoint URL]
    python build_manifest.py --emit-configs        # write runs/config-{c,v,a}.yaml
    python build_manifest.py --route-identity      # ARM A vs ARM C, role by role

WHY THE CONFIGURATIONS ARE GENERATED AND NOT HAND-WRITTEN. R35 requires ARM A's
conjecturer and critic to be BYTE-IDENTICAL to ARM C's, and R7 requires ARM V
to differ from ARM C in the critic's endpoint and nothing else. Three
hand-maintained YAML files would meet that on the day they were written and
drift the first time one was edited. Here one base table is built once and each
arm is a NAMED DEVIATION from it, so the identity is a property of the code
rather than a promise about three files, and `--route-identity` re-proves it
against the compiled manifests.

THE THREE ARMS.

  ARM C  the harness as it ships. `ARGUMENTATIVE_AUTHORITY=observe_only`,
         stated explicitly rather than left to the default, because a
         configuration that does not say what it relies on cannot be read back.
  ARM V  ARM C with the `argumentative_critic` role bound to a local endpoint
         that answers from a fixed contentless bank. NOTHING else moves.
  ARM A  ARM C with authority GRANTED — `trial_required` plus the master gate
         `ADJUDICATION_STATUS_AUTHORITY_ENABLED` — and the `judge` role alone
         carrying a two-seat CROSS-FAMILY ensemble.

WHY ARM A's JUDGE SEATS ARE NOT THE ONE MODEL, and why that is disclosed rather
than hidden. A defended trial needs a judge ensemble whose independence the
firewall will accept. On a single-family run `require_cross_family_judge_ensemble`
raises, and the cross-SCHOOL substitute cannot be reached: `build_adapter`
never populates `school_judge_bindings`, the manifest validators refuse a
`role="judge"` school binding, and the runtime resolver refuses it again. So a
one-model ARM A would run, emit its typed notice and mint nothing — measuring
nothing about authority. The operator ruled Road A-cross on 2026-09-09: the
generating seats stay on one model and only the seats that ADJUDICATE differ.
The pairing is taken verbatim from the committed P-R1 configuration, not
invented. `PARKED.md` P1 keeps the unreachable solo road open as its own
defect; this arm routes around it and says so.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TRANCHE = HERE.parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "src"))

INPUT_D8 = (REPO / "experiments/2026-09-05-change-mini-isolation-programme"
            / "runs" / "input-d8")
CONFIGS = TRANCHE / "runs"
COMPILED_AT = "2026-09-09T00:00:00Z"

# The one profile every GENERATING seat runs, in every arm. Taken from the
# profile every committed live launch since 2026-09-03 uses; `reasoning: none`
# is load-bearing, not tidy — without it this model spends its completion cap
# on hidden reasoning and returns empty content.
BASE_ROUTE = {
    "endpoint": "https://ollama.com/v1",
    "endpoint_id": "ollama-qwen3.5-397b",
    "provider": "ollama",
    "model": "qwen3.5:397b",
    "model_revision": "qwen3.5:397b",
    "family": "qwen",
    "api_key_env": "OLLAMA_API_KEY",
    "context_window_tokens": 131072,
    "max_tokens": 8192,
    "reasoning": "none",
    "timeout_s": 180,
    "output_mode": "json_object",
}
# ARM A's SECOND judge seat, and the only place any arm leaves the one model.
# Verbatim from experiments/2026-08-25-poietics-program/run-config.yaml, which
# is also the shape `cycle_soak.py --case pr1` already drives.
JUDGE_SECOND_SEAT = dict(BASE_ROUTE, endpoint_id="ollama-glm-5.2",
                         model="glm-5.2", model_revision="glm-5.2", family="glm")

CANONICAL_ROLES = (
    "conjecturer", "argumentative_critic", "defender", "variator", "judge",
    "summarizer", "synthesizer", "vision_critic", "property_designer",
    "thesis", "grounding_reviewer",
)
# The DEFENDER stays on the one model deliberately. It writes a defence; it
# does not rule. R35 confines the deviation to "the seats that adjudicate",
# and the committed P-R1 configuration happens to put another family here,
# which is exactly why the reading is written down rather than assumed.
GENERATING_ROLES = tuple(r for r in CANONICAL_ROLES if r != "judge")


def base_config() -> dict:
    return {
        "roles": {role: copy.deepcopy(BASE_ROUTE) for role in CANONICAL_ROLES},
        # Stated explicitly in every arm so a reader can see what ARM C relies
        # on rather than inferring it from a default that may move.
        "ARGUMENTATIVE_AUTHORITY": "observe_only",
        "ADJUDICATION_STATUS_AUTHORITY_ENABLED": False,
        "LEGACY_CRITICISM_ENABLED": True,
        "JUDGE_SEATS_ENABLED": False,
    }


def arm_config(arm: str, critic_endpoint: str | None = None) -> dict:
    config = base_config()
    if arm == "C":
        return config
    if arm == "V":
        endpoint = critic_endpoint or "http://127.0.0.1:PORT/v1"
        config["roles"]["argumentative_critic"] = dict(
            BASE_ROUTE, endpoint=endpoint,
            endpoint_id="loopback-vacuous-critic",
            api_key_env="DEEPREASON_TEST_CREDENTIAL")
        return config
    if arm == "A":
        config["ARGUMENTATIVE_AUTHORITY"] = "trial_required"
        config["ADJUDICATION_STATUS_AUTHORITY_ENABLED"] = True
        config["JUDGE_SEATS_ENABLED"] = True
        config["roles"]["judge"] = [copy.deepcopy(BASE_ROUTE),
                                    copy.deepcopy(JUDGE_SECOND_SEAT)]
        return config
    raise SystemExit(f"unknown arm {arm!r}")


def compile_arm(arm: str):
    """Compile one arm's committed configuration to a frozen manifest.

    `single_model` is deliberately None. Passing it collapses the role matrix
    to the one route carrying that model, which would SILENTLY DELETE ARM A's
    second judge seat and leave an arm that looks configured for a trial and
    cannot hold one. The P-R1 tranche's own builder records the same trap in
    the same words ("the seats are cross-family, so single_model must be
    None"); it is repeated here because the failure is invisible — the compile
    succeeds either way.
    """
    from deepreason.config import load as load_config  # noqa: PLC0415
    from deepreason.run_manifest import compile_run_manifest  # noqa: PLC0415
    from deepreason.v6_policy import (  # noqa: PLC0415
        engaged_control_plane_policy_v3, engaged_inquiry_capability_policy,
        engaged_simulation_toolchain)

    config = load_config(CONFIGS / f"config-{arm.lower()}.yaml")
    return compile_run_manifest(
        config, schema_version=6, workload_profile="text",
        rubric_policy="forbid", single_model=None, concurrency=2,
        compiled_at=COMPILED_AT,
        control_plane_policy=engaged_control_plane_policy_v3(),
        toolchains=(engaged_simulation_toolchain(),),
        inquiry_capability_policy=engaged_inquiry_capability_policy(
            attached_evidence=False),
        run_input_digest="0" * 64)


def route_identity() -> dict:
    """Every generating role identical across the arms; only judge and the
    critic endpoint move — measured on the COMPILED manifests.

    Compared by route FINGERPRINT rather than by the YAML text or the config
    dicts: two files can differ in comments and whitespace while compiling to
    the same routes, and it is the compiled routes the seats actually receive.
    """
    from deepreason.run_manifest import config_from_run_manifest  # noqa: PLC0415
    from deepreason.llm.firewall import (  # noqa: PLC0415
        route_fingerprint, leases_from_manifest, is_single_family_run,
        require_cross_family_judge_ensemble, JudgeEnsemblePolicyError)
    from deepreason.rules.crit import _authority  # noqa: PLC0415

    mans = {arm: compile_arm(arm) for arm in "CVA"}
    rows, violations = [], []
    for role in sorted(mans["C"].roles):
        fp = {a: tuple(route_fingerprint(r)[:12] for r in mans[a].roles[role])
              for a in "CVA"}
        same_ca, same_cv = fp["C"] == fp["A"], fp["C"] == fp["V"]
        rows.append({"role": role, "C_equals_A": same_ca, "C_equals_V": same_cv})
        if role == "judge":
            if same_ca:
                violations.append("judge is IDENTICAL in C and A -- ARM A's "
                                  "ensemble did not land")
        elif role == "argumentative_critic":
            if not same_ca:
                violations.append("critic differs C vs A (R35)")
            if same_cv:
                violations.append("critic is IDENTICAL C vs V -- ARM V's stub "
                                  "did not land")
        else:
            if not same_ca:
                violations.append(f"{role} differs C vs A (R35 violation)")
            if not same_cv:
                violations.append(f"{role} differs C vs V (R7 violation)")

    authority, ensembles = {}, {}
    for arm in "CVA":
        rebuilt = config_from_run_manifest(mans[arm])
        authority[arm] = {
            "ARGUMENTATIVE_AUTHORITY": rebuilt.ARGUMENTATIVE_AUTHORITY,
            "ADJUDICATION_STATUS_AUTHORITY_ENABLED":
                rebuilt.ADJUDICATION_STATUS_AUTHORITY_ENABLED,
            "resolved_at_the_seat": _authority(rebuilt),
            "criticism_policy": mans[arm].criticism_policy,
        }
        leases = leases_from_manifest(mans[arm])
        try:
            seats = require_cross_family_judge_ensemble(leases)
            ensembles[arm] = {"obtained": True, "seats": len(seats),
                              "families": sorted({s.route.family for s in seats}),
                              "single_family_run": is_single_family_run(leases)}
        except JudgeEnsemblePolicyError:
            ensembles[arm] = {"obtained": False, "seats": 0, "families": [],
                              "single_family_run": is_single_family_run(leases)}

    # ARM A must be able to hold a trial; ARM C must NOT be able to, and its
    # refusal is the natural RED control for the check above. If ARM C ever
    # obtained an ensemble, this measurement would prove nothing about ARM A.
    if not ensembles["A"]["obtained"]:
        violations.append("ARM A cannot obtain a judge ensemble -- its granted "
                          "authority could mint nothing")
    if ensembles["C"]["obtained"]:
        violations.append("ARM C obtained a judge ensemble -- the ensemble "
                          "check cannot refuse, so ARM A's success is vacuous")
    if authority["A"]["resolved_at_the_seat"] != "trial_required":
        violations.append("ARM A's authority does not reach the seat")
    if authority["C"]["resolved_at_the_seat"] != "observe_only":
        violations.append("ARM C is not observe_only at the seat")

    return {
        "schema": "route-identity.v2",
        "rows": rows,
        "authority": authority,
        "judge_ensembles": ensembles,
        "manifest_sha256": {a: mans[a].sha256 for a in "CVA"},
        "generating_roles_identical": not violations,
        "violations": violations,
    }


def emit_configs() -> int:
    import yaml  # noqa: PLC0415

    CONFIGS.mkdir(parents=True, exist_ok=True)
    header = {
        "C": "# ARM C -- the harness as it ships. SPEC S3 / R6.\n",
        "V": ("# ARM V -- ARM C with a CONTENTLESS critic. SPEC S4 / R7.\n"
              "# The critic endpoint's port is written at launch by the ladder;\n"
              "# the PORT placeholder below is never used by a live run.\n"),
        "A": ("# ARM A -- ARM C with authority GRANTED. SPEC S5 / R34, R35.\n"
              "# Road A-cross, the operator's ruling of 2026-09-09: every\n"
              "# GENERATING seat stays on the one model and only the judge\n"
              "# role, which adjudicates, carries a second family.\n"),
    }
    for arm in "CVA":
        text = header[arm] + "# GENERATED by tools/build_manifest.py --emit-configs.\n" \
               "# Edit the generator, never this file: the arms' identity is a\n" \
               "# property of one base table, not a promise about three files.\n\n" \
               + yaml.safe_dump(arm_config(arm), sort_keys=True)
        (CONFIGS / f"config-{arm.lower()}.yaml").write_text(text, encoding="utf-8")
    print(f"wrote {CONFIGS}/config-{{c,v,a}}.yaml")
    return 0


def question() -> str:
    payload = json.loads((INPUT_D8 / "run-input.json").read_text(encoding="utf-8"))
    return payload["problem"]["description"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=("C", "V", "A"))
    ap.add_argument("--root")
    ap.add_argument("--critic-endpoint", default=None)
    ap.add_argument("--emit-configs", action="store_true")
    ap.add_argument("--route-identity", action="store_true")
    args = ap.parse_args()
    if args.emit_configs:
        return emit_configs()
    if args.route_identity:
        result = route_identity()
        print(json.dumps(result, indent=1, sort_keys=True))
        return 0 if result["generating_roles_identical"] else 1
    ap.error("--emit-configs or --route-identity (compilation lands at step 26b)")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
