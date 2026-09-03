#!/usr/bin/env python3
"""Compile P-A2's bound RunManifest v6: P-A1's shape, four fields corrected.

PREREG.md §3 is the design; this file executes it and judges nothing.

THIS FILE IS P-A1's build_manifest_pa1.py WITH THREE CHANGES, and the reason
it is a copy rather than an import is that P-A1's copy lives on another
branch and is READ-ONLY by the tranche instruction: importing across a branch
is not a thing a ladder can do. The three changes are:

  1. COMPILED_AT moves to this tranche's own frozen instant. Run identity is
     deterministic in question + config, and the config moved, so the run id
     differs from P-A1's by construction -- but a shared COMPILED_AT would
     still be a false claim about when this manifest was compiled.
  2. The reported summary gains TWO rows, both of them P-A2 gates that P-A1
     had no reason to carry: `runtime_split_budget_seat_protocol` (the value
     that survives the manifest's config-echo POP and the carriage notice,
     which is the only thing that decides whether C3 actually happened) and
     `model_profile_registry` (the count of model documents the run will
     stamp -- zero is a STOP per the tranche instruction).
  3. Nothing else. The two-pass compile, the explicit criticism policy, the
     engaged capability preset, the route-bound schools, the empty-but-open
     dossier and the pinned POLICY_ENVIRON are P-A1's, unchanged, because
     this tranche measures five merged fixes against P-A1's counts and a
     second difference in the builder would spoil that comparison.

WHAT IS IMPORTED, NEVER COPIED:

    QUESTION   question.py   (frozen by digest, asserted in preflight_pa1.py)
    CRITERIA   criteria.py   (discrimination table proven in preflight_pa1.py)

THREE THINGS THIS BUILDER DOES THAT ITS PREDECESSORS DID NOT, each of them a
requirement of the tranche instruction rather than a preference:

1. `single_model=None` and `rubric_policy="require_cross_family"`. Four
   distinct models across eleven roles; `single_model` would collapse the
   role matrix to the one route carrying that model and silently discard the
   operator's seat assignment.

2. `criticism_policy=` is passed EXPLICITLY. Omitting it now reaches the
   derivation the judge-canary tranche shipped
   (`v6_policy.configured_criticism_policy`, Road B, 2026-09-01), which
   would produce the same policy -- and the tranche instruction says not to
   rely on it. The explicit argument also makes the manifest's authority a
   property of THIS file rather than of a compiler branch, which is what
   P-S1 lost: its builder supplied the requesting Config and omitted the
   argument, so the manifest froze `criticism_policy: null`, the defended/
   judge/variator seats got EMPTY behavioural-contract grants, and 140
   criticisms were filed as scrutiny observations.

   The variator grant is the same grant. `_route_seat_behavioral_contract_
   assignments` adds defender/judge/variator contracts exactly when a STORED
   policy has `authority == "defended_trial"` -- so the null policy is also
   why P-S1's variator deferred `transaction-contract-unavailable` 171 times
   and hv/reach never measured. One fix, two requirements.

3. TWO-PASS COMPILE, for two independent reasons and neither is style. The
   criticism policy must name the argumentative_critic's RESOLVED
   `endpoint_id`, and the attached-evidence policy must be the compiler's
   OWN derived policy with one field moved (flipping `enabled` on a
   hand-assembled policy leaves the engaged bounds behind and the model
   refuses a disabled capability carrying non-zero bounds). Both facts are
   only available after a compile, so pass 1 is compiled and read, and pass
   2 is the manifest that is bound. Pass 1 dispatches no model call and
   writes nothing.

Usage:  python build_manifest_pa2.py <root>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

from criteria import CRITERIA  # noqa: E402
from question import QUESTION  # noqa: E402

from deepreason.config import load as load_config  # noqa: E402
from deepreason.evidence import (  # noqa: E402
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.preparation import _question_digest  # noqa: E402
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest  # noqa: E402
from deepreason.v6_policy import (  # noqa: E402
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
    engaged_inquiry_capability_policy,
    engaged_simulation_toolchain,
    route_bound_school_execution_policy,
)

CONFIG_PATH = TRANCHE / "run-config.yaml"

# Frozen, not read from the clock: re-running this script against an existing
# root must be idempotent, and `bind_run_manifest` requires byte-identical
# canonical bytes on a second call.
COMPILED_AT = "2026-09-02T00:00:00Z"

# The policy environment, pinned HERE rather than inherited from the shell.
#
# `engaged_inquiry_capability_policy` and `engaged_simulation_toolchain` both
# read environment variables. Leaving them to the caller's shell is how the
# SOAK and the LAUNCH silently drive different shapes -- the soak imports this
# builder precisely so that cannot happen, and an environment read would put
# the divergence back. So the mapping is a constant of this file and BOTH
# calls take it.
#
#   DEEPREASON_CONFIG_REFEREE = "6"  turns the config referee ON at a
#       six-cycle cadence (four firings across this run's 24 cycles). It ships
#       OFF -- `engaged_config_referee_policy` returns None on an unset
#       variable -- and it is the one capability the engaged preset
#       deliberately leaves operator-opted, on the ground that it is a judge
#       seat rather than an evidence channel. This run opts in: the amended
#       judge law (CLAUDE.md, 2026-08-28) replaced the blanket caution with
#       measurement, and judge use is now a per-run configuration choice.
#
#   DEEPREASON_SIMULATION_RUNNER is DELIBERATELY ABSENT: unset means the
#       CONTAINED runner, under which model-authored `sandboxed_python_v1`
#       programs actually execute. Containment was probed available on this
#       host (verification.contained.ContainedSimulationBackend.
#       containment_available() -> True) before the launch.
#
#   DEEPREASON_RESEARCH_ALLOWLIST is DELIBERATELY ABSENT: unset means
#       `channels.DEFAULT_RESEARCH_ALLOWLIST`, arxiv.org + en.wikipedia.org.
POLICY_ENVIRON: dict[str, str] = {"DEEPREASON_CONFIG_REFEREE": "6"}

# The simulation budget this run raises, and the bounds it does NOT touch.
#
# The engaged preset meters TWO PER RUN -- `maximum_simulation_requests=2`,
# `maximum_simulation_executions=2`, metered over the whole
# `capability_state`, not per cycle (capabilities/simulation.py:586,595). Over
# 24 cycles that is a smoke-test budget, and the tranche instruction asks for
# simulation "ON with real budgets" against a question deliberately built so
# that its simulations are cheap deterministic programs (small-n exhaustive
# checks, Monte Carlo on modest n).
#
# THE CONTAINMENT ENVELOPE DOES NOT MOVE. Every bound the 2026-08-27 safety
# verdict is about -- wall clock, memory, steps, samples, generated-code
# bytes, `network_policy: forbidden`, `filesystem_policy:
# isolated_no_filesystem`, the fixed seed set, the contained runner profile --
# stays exactly as the audited preset froze it. What moves is HOW MANY of the
# same audited operation the run may perform, which is a budget and not a
# safety property. The raise is recorded in PREREG.md §4 R2 and again in
# MODULE_COVERAGE.md, because a deviation nobody wrote down is a deviation
# nobody can check.
SIMULATION_BUDGET_RAISE: dict[str, int] = {
    "maximum_simulation_requests": 12,
    "maximum_simulation_executions": 12,
    "maximum_proposals_per_turn": 2,
}

# PREREG.md §2. The question bytes are frozen by DIGEST, not by copy.
QUESTION_SHA256 = "933313a5d9ca6dd86f3052aec6e1f05f395ad00586e08096bd40d1be733d7560"


def _conjecturer_seat_map(config) -> dict[str, tuple[int, str]]:
    """Alternate the seeded schools across the configured conjecturer seats.

    `engaged_control_plane_policy_v3` ships `school_execution` at
    `conditioning_only`, on the stated ground that routing diversity is a
    provider-topology question and not a public default. This run IS that
    topology question: the operator put two models in the conjecturer role
    and asked for the seat instances to be distributed, so the schools are
    bound round-robin across the seats that exist rather than all sharing
    seat 0.

    `SchoolRoleBindingV1` resolves by SEAT INDEX into `manifest.roles[
    "conjecturer"]`, not by endpoint_id string, so the endpoint_id here is
    the seat's own resolved id and the two must agree.
    """

    seats = _conjecturer_seat_specs(config)
    return {
        f"school-{index}": seats[index % len(seats)]
        for index in range(config.N_SCHOOLS)
    }


def _conjecturer_seat_specs(config) -> list[tuple[int, str]]:
    configured = config.roles.get("conjecturer")
    seats = configured if isinstance(configured, list) else [configured]
    resolved = [
        (index, str((spec.get("endpoint_id") if isinstance(spec, dict)
                     else getattr(spec, "endpoint_id", None)) or ""))
        for index, spec in enumerate(seats)
        if spec is not None
    ]
    if not resolved or any(not endpoint_id for _, endpoint_id in resolved):
        raise SystemExit(
            "EVERY conjecturer seat must carry an explicit endpoint_id: a "
            "route-bound school binding resolves by seat index and its "
            "endpoint_id must agree with the seat it names"
        )
    return resolved


def _route_bound_control_plane(config):
    """The engaged v3 control plane with schools actually ROUTED.

    One field moves. Everything else -- conjecture context, workflow retry,
    the frozen v6 contract versions, scratch authoring -- stays exactly as
    the public preset froze it, because a second difference here would be a
    second thing this tranche has to keep true.
    """

    seat_map = _conjecturer_seat_map(config)
    default_endpoint_id = seat_map["school-0"][1]
    return engaged_control_plane_policy_v3().model_copy(
        update={
            "school_execution": route_bound_school_execution_policy(
                default_endpoint_id, seat_map=seat_map
            )
        }
    )


def _assert_workload_matches(root: Path) -> None:
    """Refuse to hand the ladder a root `deepreason run` will reject.

    P-R1's first launch died at `_require_v6_workload_match` AFTER the
    qualification battery had been paid for. The CLI's own predicate is
    imported rather than reimplemented, so this guard cannot drift from the
    check it stands in for.
    """
    from deepreason.cli.main import _read_problem_file, _require_v6_workload_match
    from deepreason.evidence import load_evidence_dossier, load_run_input
    from deepreason.workloads.text import ReasoningWorkloadSpec

    payload = _read_problem_file(root / "problem.json")
    spec = ReasoningWorkloadSpec.model_validate(payload)
    _require_v6_workload_match(load_run_input(root), load_evidence_dossier(root), spec)


def _registry_summary() -> dict:
    """What `registry_fingerprint` will stamp, read where the run reads it.

    The tranche instruction makes a zero-profile stamp a STOP. Nothing ships
    (docs/model-profiles/README.md: "Home directory only, nothing ships"), so
    zero is the DESIGNED state of a home nobody staged -- which is exactly why
    it has to be read here rather than assumed from the presence of the files
    in docs/.
    """
    from deepreason.model_profiles import registry_fingerprint

    fingerprint = registry_fingerprint()
    return {
        "count": fingerprint["count"],
        "model_ids": [row["model_id"] for row in fingerprint["profiles"]],
        "problem_count": fingerprint["problem_count"],
        "problems": fingerprint["problems"],
        "root": str(__import__("deepreason.model_profiles", fromlist=["x"]).profiles_root()),
    }


def build(root: Path, *, config_path: Path | str | None = None) -> dict:
    # ``config_path`` exists for cycle_soak.py, which hands in a copy of this
    # tranche's config with every endpoint redirected to its local stub. The
    # soak must drive THIS shape; restating the shape there would let the
    # instrument and the launch drift apart.
    config = load_config(config_path or CONFIG_PATH)
    root = Path(root)

    if _question_digest(QUESTION) != QUESTION_SHA256:
        raise SystemExit(
            "QUESTION BYTES DRIFTED from the value PREREG.md §2 froze: "
            f"{_question_digest(QUESTION)} != {QUESTION_SHA256}"
        )

    problem_id = f"question-{_question_digest(QUESTION)[:32]}"

    # An EMPTY dossier, bound explicitly. The attached-evidence CHANNEL is
    # switched ON below -- that is the requirement -- but there is nothing
    # honest to put in it: the question is a self-contained mathematical one
    # and fabricating source documents to make a channel look busy would be
    # the opposite of evidence. So the channel is open and carries nothing,
    # and MODULE_COVERAGE.md records that as the typed reason rather than as
    # a firing.
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="P-A2 build_manifest_pa2.py",
            acquisition_method="no attached evidence",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=QUESTION, criteria=CRITERIA
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)

    common = dict(
        schema_version=6,
        workload_profile="text",
        # The judge ensemble is the point of this configuration, so the
        # rubric gate is REQUIRED rather than forbidden.
        rubric_policy="require_cross_family",
        # NOT single_model: four distinct models across eleven roles.
        single_model=None,
        # Provider rules (docs/OLLAMA_CLOUD_OPERATIONS.md, binding): explicit
        # concurrency everywhere, including qualification.
        concurrency=2,
        compiled_at=COMPILED_AT,
        control_plane_policy=_route_bound_control_plane(config),
        # An enabled simulation policy must bind exactly one frozen toolchain
        # or the manifest refuses V6_SIMULATION_TOOLCHAIN_REQUIRED. The
        # toolchain PAIRS with the runner the configuration names, so this is
        # read from the same choice rather than hardcoded: unset means the
        # CONTAINED runner, under which model-authored `sandboxed_python_v1`
        # programs actually execute. Containment was probed available on this
        # host before the launch (PREREG §4 R2).
        toolchains=(engaged_simulation_toolchain(POLICY_ENVIRON),),
        run_input_digest=run_input.run_input_digest,
    )

    # --- pass 1: resolve routes and the derived capability policy ----------
    probe = compile_run_manifest(config, **common)

    critic_routes = probe.roles.get("argumentative_critic", ())
    if not critic_routes:
        raise SystemExit(
            "NO argumentative_critic ROUTE: a defended-trial criticism policy "
            "has nothing to bind to (V6_ENGAGED_CRITICISM_ROUTE_REQUIRED)"
        )
    critic_endpoint_id = critic_routes[0].endpoint_id

    # The ENGAGED preset, not `probe.inquiry_capability_policy`. Compiling
    # without this argument derives an ALL-DISABLED capability policy: the
    # probe root's first build reported `simulation_enabled: false` and
    # `research_enabled: false` with every switch in run-config.yaml already
    # set, which is exactly the shape P-S1 ran in. `config=config` is what
    # makes CHANNELS_DISABLED reach the two channels, and
    # `attached_evidence=True` is the third channel's own opt-in.
    inquiry_policy = engaged_inquiry_capability_policy(
        POLICY_ENVIRON, attached_evidence=True, config=config
    )
    inquiry_policy = inquiry_policy.model_copy(
        update={
            "simulation": inquiry_policy.simulation.model_copy(
                update=SIMULATION_BUDGET_RAISE
            )
        }
    )

    # --- the explicit criticism policy (requirement R1) --------------------
    # Written out, not derived. `authority` is taken from the Config the
    # operator wrote rather than hardcoded, so a config that stopped asking
    # for defended trials could not silently keep them.
    criticism_policy = engaged_criticism_policy(
        critic_endpoint_id,
        authority=config.ENGAGED_CRITICISM_AUTHORITY,
        school_count=config.N_SCHOOLS,
    )
    if criticism_policy.authority != "defended_trial":
        raise SystemExit(
            "REFUSING TO BUILD: run-config.yaml does not request defended "
            f"trials (ENGAGED_CRITICISM_AUTHORITY={config.ENGAGED_CRITICISM_AUTHORITY!r})"
        )

    # --- pass 2: the manifest that is actually bound -----------------------
    manifest = compile_run_manifest(
        config,
        criticism_policy=criticism_policy,
        inquiry_capability_policy=inquiry_policy,
        **common,
    )
    bind_run_manifest(manifest, root)

    (root / "problem.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-text-workload-v1",
                "problem": {"id": problem_id, "description": QUESTION},
                "criteria": [json.loads(c.model_dump_json()) for c in CRITERIA],
                "sources": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    _assert_workload_matches(root)

    for notice in manifest.compile_notices or ():
        print(f"NOTICE {notice.code}: {notice.message}", file=sys.stderr)

    # The runtime Config the run will ACTUALLY see, reconstructed exactly as
    # `application/text_runs.py` reconstructs it. REPORTED here, never
    # asserted: `preflight_pa1.py` owns the decision to refuse, and it must
    # be able to refuse on a value this function reported honestly.
    from deepreason.run_manifest import config_from_run_manifest

    runtime = config_from_run_manifest(manifest)
    m_school_mode = manifest.control_plane_policy.school_execution.mode
    trial_plan = {
        entry.role: sorted(grant.contract_id for grant in entry.contracts)
        for entry in (
            manifest.route_seat_behavioral_capability_plan.entries
            if manifest.route_seat_behavioral_capability_plan is not None
            else ()
        )
    }

    return {
        "attached_evidence_enabled": (
            manifest.inquiry_capability_policy.attached_evidence.enabled
        ),
        "bridge_mode": manifest.bridge_policy.mode,
        "bridge_reviewer_role": manifest.bridge_policy.reviewer_role,
        "compile_notices": [
            {"code": n.code, "message": n.message, "pointer": n.pointer}
            for n in (manifest.compile_notices or ())
        ],
        "criteria": [c.id for c in CRITERIA],
        "criticism_authority": manifest.criticism_policy.authority,
        "criticism_bindings": len(manifest.criticism_policy.bindings),
        "dossier_sources": len(dossier.sources),
        "manifest_sha256": manifest.sha256,
        "problem_id": problem_id,
        "question_sha256": _question_digest(QUESTION),
        "research_enabled": manifest.inquiry_capability_policy.research.enabled,
        "roles": {r: len(v) for r, v in sorted(manifest.roles.items()) if v},
        "run_input_digest": run_input.run_input_digest,
        "runtime_adjudication_status_authority": (
            runtime.ADJUDICATION_STATUS_AUTHORITY_ENABLED
        ),
        "runtime_bridge_mode": runtime.bridge.mode,
        "runtime_judge_seats_enabled": runtime.JUDGE_SEATS_ENABLED,
        "runtime_judge_summons_per_cycle": runtime.JUDGE_SUMMONS_PER_CYCLE,
        "runtime_near_dup_eps": runtime.NEAR_DUP_EPS,
        "runtime_scratchpad_enabled": runtime.scratchpad.enabled,
        "runtime_successor_minting_enabled": runtime.SUCCESSOR_MINTING_ENABLED,
        "simulation_enabled": manifest.inquiry_capability_policy.simulation.enabled,
        "config_referee_cadence": (
            manifest.inquiry_capability_policy.config_referee.cadence_cycles
            if manifest.inquiry_capability_policy.config_referee is not None
            else None
        ),
        "school_execution_mode": m_school_mode,
        "simulation_budget": {
            "requests": manifest.inquiry_capability_policy.simulation.maximum_simulation_requests,
            "executions": manifest.inquiry_capability_policy.simulation.maximum_simulation_executions,
            "wall_ms": manifest.inquiry_capability_policy.simulation.maximum_wall_ms,
            "network_policy": manifest.inquiry_capability_policy.simulation.network_policy,
        },
        "simulation_toolchain": engaged_simulation_toolchain(POLICY_ENVIRON).id,
        # P-A2 GATE C3. This is the ONLY honest place to read whether
        # `SPLIT_BUDGET_SEAT_PROTOCOL: "off"` actually happened: the field is
        # popped from the manifest's engine-config echo, so the YAML line
        # proves nothing on its own and only the carriage notice delivers it
        # into the Config the run reconstructs. Reported, never asserted --
        # preflight_pa2.py owns the refusal.
        "runtime_split_budget_seat_protocol": runtime.SPLIT_BUDGET_SEAT_PROTOCOL,
        # P-A2 GATE: the model-document registry this run will stamp. Read
        # through the same function the scheduler stamps with, against the
        # SAME DEEPREASON_HOME the ladder exports, so a profile directory the
        # ladder forgot to stage cannot pass here and fail there.
        "model_profile_registry": _registry_summary(),
        "trial_contract_grants": {
            role: trial_plan.get(role, [])
            for role in ("defender", "judge", "variator")
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_manifest_pa2.py <root>", file=sys.stderr)
        return 2
    print(json.dumps(build(Path(sys.argv[1])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
