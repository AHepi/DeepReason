#!/usr/bin/env python3
"""Refuse the P-A2 launch unless every PREREG §7 gate actually holds.

P-A1's preflight, carried forward with ONE SECTION ADDED: the four
corrections this tranche exists to make (§3 C1-C4) plus the model-profile
registry. Everything P-A1 gated is still gated, because P-A2 must re-run
P-A1's shape and a gate silently dropped is a difference nobody wrote down.

This runs AFTER the root is built and BEFORE the qualification battery, which
is the only window in which refusing is cheap. Its whole purpose is that the
expensive failure modes of this configuration are SILENT ones: a compiled
manifest that looks complete and has an empty grant list, a switch the config
echo dropped and nothing restored, a channel that says ON and cannot reach the
capability it enables. Every one of those produces a run that burns its budget
and reads, afterwards, exactly like "the models had nothing to say".

Each check names the requirement it stands for (PREREG §3/§4) and the evidence it
reads. Nothing here is an opinion: every assertion is against a field of the
compiled manifest, the runtime Config rebuilt from it, or the harness's own
evaluator.

Usage:  python preflight_pa2.py <root> [--catalogue]

`--catalogue` adds the one check that needs the network: that every seat names
a model the provider actually lists. The ladder passes it; an offline
rehearsal does not.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

import build_manifest_pa2 as builder  # noqa: E402
import criteria as criteria_module  # noqa: E402
from question import QUESTION  # noqa: E402

import deepreason.allocation as allocation  # noqa: E402
from deepreason.ontology import Artifact  # noqa: E402
from deepreason.ontology.artifact import Provenance, ProvenanceRole  # noqa: E402
from deepreason.preparation import _question_digest  # noqa: E402
from deepreason.programs import _validate_predicate, evaluate  # noqa: E402
from deepreason.run_manifest import RunManifest, config_from_run_manifest  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def check(requirement: str, name: str, ok: bool, detail: object = "") -> None:
    global CHECKS
    CHECKS += 1
    status = "ok  " if ok else "FAIL"
    line = f"[{status}] {requirement:4s} {name}"
    if detail != "":
        line += f"  -- {detail}"
    print(line)
    if not ok:
        FAILURES.append(f"{requirement} {name}: {detail}")


class _InlineBlobs:
    """`content_text` reads `inline:` refs without touching a store."""

    def get(self, ref):  # pragma: no cover - never reached for inline refs
        raise KeyError(ref)


def _verdicts(text: str) -> dict[str, str]:
    artifact = Artifact(
        id="a" * 64,
        codec="text",
        content_ref="inline:" + text,
        provenance=Provenance(role=ProvenanceRole.CONJECTURER),
    )
    return {c.id: evaluate(c, artifact, _InlineBlobs())[0] for c in criteria_module.CRITERIA}


# The discrimination table PREREG §2 froze. A battery that passes everything
# prices nothing, and a battery that fails everything is a typo.
ON_TARGET = (
    "Claim: the probability of reaching unanimous consensus tends to a "
    "constant strictly between 0 and 1 as n grows. The obstruction is a "
    "locally stable mixed configuration: an induced subgraph in which every "
    "vertex already agrees with two of its three neighbours, so no "
    "single-vertex update changes anything -- the dynamics is trapped. The "
    "smallest such structure is a short cycle whose vertices are "
    "monochromatic within the cycle. Quantitatively, the expected number of "
    "such structures converges to a Poisson limit: it scales like a constant "
    "independent of n, so the consensus probability approaches exp(-lambda)."
)
OFF_TARGET = {
    "verdict+structure, no law": (
        "As n grows the probability of consensus tends to 1, because the "
        "dynamics is trapped only in locally stable configurations where "
        "every vertex agrees with a majority of its neighbours, and such "
        "frozen structures are rare.",
        "pa1-scaling-law@v1",
    ),
    "verdict+law, no structure": (
        "As n grows the probability of consensus tends to 0. The expected "
        "number of blockers scales like log n, so consensus becomes "
        "unlikely.",
        "pa1-obstruction-structure@v1",
    ),
    "generic waffle": (
        "Majority dynamics on sparse graphs is an interesting problem "
        "studied by many researchers. Simulation would help clarify the "
        "behaviour of the system.",
        None,  # must fail ALL three
    ),
    "empty": ("", None),
}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_catalogue = "--catalogue" in sys.argv[1:]
    if len(args) != 1:
        print("usage: preflight_pa1.py <root> [--catalogue]", file=sys.stderr)
        return 2
    root = Path(args[0])

    manifest = RunManifest.model_validate_json((root / "run-manifest.json").read_text())
    runtime = config_from_run_manifest(manifest)
    ic = manifest.inquiry_capability_policy

    # ---- §2 the question and the battery ---------------------------------
    check(
        "§2",
        "question bytes match the frozen digest",
        _question_digest(QUESTION) == builder.QUESTION_SHA256,
        _question_digest(QUESTION),
    )
    for c in criteria_module.CRITERIA:
        kind, _, arg = c.eval.partition(":")
        ok = True
        try:
            _validate_predicate(arg)
        except Exception as error:  # noqa: BLE001
            ok, arg = False, str(error)
        check("§2", f"predicate is sandbox-legal: {c.id}", ok, "" if ok else arg)

    on = _verdicts(ON_TARGET)
    check(
        "§2",
        "the on-target answer passes all three criteria",
        all(v == "pass" for v in on.values()),
        on,
    )
    for label, (text, must_fail) in OFF_TARGET.items():
        got = _verdicts(text)
        if must_fail is None:
            ok = all(v == "fail" for v in got.values())
        else:
            ok = got.get(must_fail) == "fail" and sum(
                1 for v in got.values() if v == "pass"
            ) == len(got) - 1
        check("§2", f"discrimination: {label}", ok, got)

    # ---- R1 defended trials ----------------------------------------------
    policy = manifest.criticism_policy
    check("R1", "a criticism policy is STORED on the manifest", policy is not None)
    if policy is not None:
        check(
            "R1",
            "stored authority is defended_trial",
            policy.authority == "defended_trial",
            policy.authority,
        )
        check(
            "R1",
            "one binding per seeded school",
            len(policy.bindings) == runtime.N_SCHOOLS,
            f"{len(policy.bindings)} bindings / N_SCHOOLS={runtime.N_SCHOOLS}",
        )

    # ---- R4 the trial contract grants (and therefore hv/reach) -----------
    plan = manifest.route_seat_behavioral_capability_plan
    grants = {
        (entry.role, entry.seat): sorted(g.contract_id for g in entry.contracts)
        for entry in (plan.entries if plan is not None else ())
    }
    for role in ("defender", "judge", "variator"):
        seats = [k for k in grants if k[0] == role]
        check(
            "R4",
            f"{role} seats hold a non-empty behavioural contract grant",
            bool(seats) and all(grants[k] for k in seats),
            {f"{r}[{s}]": grants[(r, s)] for r, s in seats},
        )
    check(
        "R4",
        "PARETO_AXES still names hv, reach and coverage",
        list(runtime.PARETO_AXES) == ["hv", "reach", "coverage"],
        runtime.PARETO_AXES,
    )

    # ---- R2 the two evidence channels ------------------------------------
    check("R2", "simulation capability enabled", ic.simulation.enabled)
    check(
        "R2",
        "simulation runs the CONTAINED runner",
        ic.simulation.runner_profile == "simulation.container.v1",
        ic.simulation.runner_profile,
    )
    from deepreason.verification.contained import ContainedSimulationBackend

    check(
        "R2",
        "this host can actually create the containment namespace",
        ContainedSimulationBackend.containment_available(),
        "a contained policy on a host without it refuses EVERY execution",
    )
    check(
        "R2",
        "the containment envelope is the audited one",
        (
            ic.simulation.network_policy == "forbidden"
            and ic.simulation.filesystem_policy == "isolated_no_filesystem"
            and ic.simulation.maximum_wall_ms == 20000
            and ic.simulation.maximum_memory_bytes == 536870912
            and ic.simulation.maximum_steps == 2000000
            and ic.simulation.maximum_samples == 64
            and ic.simulation.maximum_generated_code_bytes == 65536
        ),
        "only the request/execution COUNTS were raised (PREREG §4 R2)",
    )
    check(
        "R2",
        "the raised simulation budget is in force",
        ic.simulation.maximum_simulation_requests == 12
        and ic.simulation.maximum_simulation_executions == 12,
        f"{ic.simulation.maximum_simulation_requests} requests / "
        f"{ic.simulation.maximum_simulation_executions} executions",
    )
    check("R2", "research capability enabled", ic.research.enabled)
    check(
        "R2",
        "research carries a non-empty domain allowlist",
        bool(ic.research.domain_allowlist),
        ic.research.domain_allowlist,
    )
    check(
        "R2",
        "the config referee is armed",
        ic.config_referee is not None and ic.config_referee.enabled,
        None if ic.config_referee is None else ic.config_referee.cadence_cycles,
    )

    # ---- R3 the bridge ----------------------------------------------------
    bridge = manifest.bridge_policy
    check(
        "R3",
        "bridge mode is grounded_two_stage",
        bridge.mode == "grounded_two_stage",
        bridge.mode,
    )
    check("R3", "grounding review is on", bridge.grounding_review)
    check(
        "R3",
        "the reviewer seat is the grounding_reviewer, not a judge",
        bridge.reviewer_role == "grounding_reviewer",
        bridge.reviewer_role,
    )
    check(
        "R3",
        "the rebuilt runtime Config agrees about the bridge mode",
        runtime.bridge.mode == "grounded_two_stage",
        runtime.bridge.mode,
    )

    # ---- R5 the near-duplicate gate ---------------------------------------
    check(
        "R5",
        "NEAR_DUP_EPS is armed at the calibrated value",
        runtime.NEAR_DUP_EPS == 0.2608,
        runtime.NEAR_DUP_EPS,
    )
    check(
        "R5",
        "RESEED_DIST_MIN is armed at the calibrated value",
        runtime.RESEED_DIST_MIN == 0.0401,
        runtime.RESEED_DIST_MIN,
    )
    check(
        "R5",
        "the embedder those thresholds were calibrated for is the one configured",
        runtime.EMBEDDER_MODEL == "nomic-ai/nomic-embed-text-v1.5",
        runtime.EMBEDDER_MODEL,
    )

    # ---- R6 scratchpad, dossier channel, successor questions --------------
    check("R6", "the scratch workspace is enabled", manifest.scratch_policy.enabled)
    check("R6", "the runtime Config agrees", runtime.scratchpad.enabled)
    check(
        "R6",
        "the attached-evidence channel is open",
        ic.attached_evidence.enabled,
        f"maximum_sources={ic.attached_evidence.maximum_sources}",
    )
    check(
        "R6",
        "successor-question routing is at its default destination",
        runtime.SUCCESSOR_QUESTION_DESTINATION == "scratchpad.v1",
        runtime.SUCCESSOR_QUESTION_DESTINATION,
    )
    check(
        "R6",
        "successor MINTING is OFF (an operator launch-time choice)",
        runtime.SUCCESSOR_MINTING_ENABLED is False,
        runtime.SUCCESSOR_MINTING_ENABLED,
    )

    # ---- R7 the signal census --------------------------------------------
    bound_roles = tuple(role for role, routes in manifest.roles.items() if routes)
    open_loops = tuple(allocation.open_loop_notices(bound_roles))
    check(
        "R7",
        "no policy signal is open-loop on this topology",
        open_loops == (),
        [n.message for n in open_loops],
    )
    check(
        "R7",
        "all seven policy signals are accounted for",
        len(allocation.POLICY_SIGNALS) == 7,
        allocation.POLICY_SIGNALS,
    )

    # ---- the carriage notices (the P10 repair, working) -------------------
    # P-A1's six, plus P-A2's seventh. The EXACT-match assertion below is the
    # valuable half of this gate and is preserved: a switch that quietly
    # stopped being carried, or one carried that nobody asked for, still
    # fails. What moved is the expectation, because P-A2 genuinely sets one
    # more dropped field than P-A1 did.
    #
    # SPLIT_BUDGET_SEAT_PROTOCOL is the C3 correction, and its presence HERE
    # is the mechanism by which it arrives: the field is popped from the
    # engine-config echo (run_manifest.py:2469), so the carriage notice is
    # the only road from run-config.yaml to the Config the run reconstructs.
    # P-A1 has no notice for it because P-A1 never set it -- an unset field
    # is not dropped, it is simply absent, and the runtime takes the "auto"
    # default. That is precisely the difference this run is making.
    expected_carriage = {
        "ADJUDICATION_STATUS_AUTHORITY_ENABLED": True,
        "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
        "JUDGE_SEATS_ENABLED": True,
        "JUDGE_SUMMONS_PER_CYCLE": 2,
        "LEGACY_CRITICISM_ENABLED": False,
        "SCHOOL_SEATS_ENABLED": True,
        "SPLIT_BUDGET_SEAT_PROTOCOL": "off",
    }
    carried = {
        n.pointer.rsplit("/", 1)[-1]
        for n in (manifest.compile_notices or ())
        if n.code == "ENGINE_CONFIG_FIELD_NOT_CARRIED"
    }
    check(
        "P10",
        "every dropped switch has a carriage notice",
        carried == set(expected_carriage),
        sorted(carried ^ set(expected_carriage)) or "exact match",
    )
    for field, want in expected_carriage.items():
        got = getattr(runtime, field)
        check("P10", f"runtime Config restored {field}", got == want, f"{got!r}")

    # ---- seats ------------------------------------------------------------
    conjecturer = manifest.roles.get("conjecturer", ())
    check(
        "§3",
        "the conjecturer role carries TWO seat instances",
        len(conjecturer) == 2,
        [r.model_id for r in conjecturer],
    )
    judges = manifest.roles.get("judge", ())
    families = {r.family for r in judges}
    check(
        "§3",
        "the judge ensemble is >=2 seats across >=2 families",
        len(judges) >= 2 and len(families) >= 2,
        f"{[r.model_id for r in judges]} families={sorted(families)}",
    )
    check(
        "§3",
        "every generation-side seat sits on a model the operator named",
        all(
            route.model_id in {"deepseek-v4-pro:0813", "glm-5.3"}
            for role, routes in manifest.roles.items()
            if role != "judge"
            for route in routes
        ),
        sorted({r.model_id for role, v in manifest.roles.items() if role != "judge" for r in v}),
    )
    school = manifest.control_plane_policy.school_execution
    seat_endpoints = {i: r.endpoint_id for i, r in enumerate(conjecturer)}
    check(
        "§4",
        "schools are ROUTE-BOUND across the conjecturer seats",
        school.mode == "route_bound"
        and len(school.bindings) == runtime.N_SCHOOLS
        and all(
            seat_endpoints.get(b.seat) == b.endpoint_id for b in school.bindings
        ),
        [(b.school_id, b.seat, b.endpoint_id) for b in school.bindings],
    )

    # ---- §3: THE FOUR CORRECTIONS, and only these ------------------------
    # This section is the whole reason P-A2 exists. Each gate reads the
    # COMPILED route or the REBUILT runtime Config, never run-config.yaml:
    # the YAML is what was asked for, and these are what the provider and the
    # adapter will actually see. The difference is not hypothetical -- C3's
    # field is popped from the manifest's engine-config echo, so its YAML line
    # and its delivered value are genuinely two different facts.
    glm_routes = [
        (role, seat, route)
        for role, routes in sorted(manifest.roles.items())
        for seat, route in enumerate(routes)
        if route.model_id == "glm-5.3"
    ]
    check(
        "§3",
        "every glm-5.3 seat is present (6 expected: conj-1, defender, "
        "summarizer, synthesizer, vision_critic, grounding_reviewer)",
        len(glm_routes) == 6,
        [(role, seat) for role, seat, _ in glm_routes],
    )
    # C1/C2. Omitted is not off: this model defaults to `max` effort, which is
    # what P-A1 ran and what crossed the ~300 s transport wall.
    check(
        "§3 C1",
        'every glm-5.3 seat carries reasoning "low" EXPLICITLY',
        bool(glm_routes) and all(r.reasoning == "low" for _, _, r in glm_routes),
        sorted({str(r.reasoning) for _, _, r in glm_routes}),
    )
    # `none` is not in this model's documented set and moves the trace into
    # the content rather than stopping it (P-S1: 0/8 clean). Gated explicitly
    # so a future edit cannot reintroduce it quietly.
    check(
        "§3 C1",
        'no seat anywhere requests reasoning "none"',
        all(
            route.reasoning != "none"
            for routes in manifest.roles.values()
            for route in routes
        ),
        "checked every seat, not only glm",
    )
    # C4. The P-C2b-measured ceiling, not P-A1's extrapolated 49152.
    check(
        "§3 C4",
        "every glm-5.3 seat caps completion at 32768",
        bool(glm_routes) and all(r.max_tokens == 32768 for _, _, r in glm_routes),
        sorted({r.max_tokens for _, _, r in glm_routes}),
    )
    # The control half of the comparison: P-A2 moves the glm seats and NOTHING
    # else, so a deepseek seat that drifted would spoil the before/after just
    # as surely as a glm seat that did not move.
    deepseek_routes = [
        route
        for routes in manifest.roles.values()
        for route in routes
        if route.model_id == "deepseek-v4-pro:0813"
    ]
    check(
        "§3",
        "deepseek seats are UNCHANGED from P-A1 (49152, reasoning unset)",
        bool(deepseek_routes)
        and all(
            r.max_tokens == 49152 and r.reasoning is None for r in deepseek_routes
        ),
        f"{len(deepseek_routes)} seats",
    )
    judge_routes = manifest.roles.get("judge", ())
    check(
        "§3",
        "judge seats are UNCHANGED from P-A1 (32768, reasoning unset)",
        len(judge_routes) == 2
        and all(r.max_tokens == 32768 and r.reasoning is None for r in judge_routes),
        [(r.model_id, r.max_tokens) for r in judge_routes],
    )
    # C3. THE GATE THAT CANNOT BE READ OFF THE YAML. run_manifest.py:2469 pops
    # this field from the engine-config echo; only the carriage notice puts it
    # back into the Config the run reconstructs. If this reads "auto", the
    # split protocol is armed, every glm seat becomes two legs, and P2's
    # zero-token count stops being comparable to P-A1's.
    check(
        "§3 C3",
        'SPLIT_BUDGET_SEAT_PROTOCOL survives the config-echo POP as "off"',
        runtime.SPLIT_BUDGET_SEAT_PROTOCOL == "off",
        repr(runtime.SPLIT_BUDGET_SEAT_PROTOCOL),
    )

    # ---- the model-profile registry (a zero stamp is a STOP) -------------
    # Nothing ships (docs/model-profiles/README.md: "Home directory only,
    # nothing ships"), so ZERO is the designed state of a home nobody staged.
    # That is exactly why this is read from the registry function the
    # scheduler itself stamps with, against the SAME DEEPREASON_HOME the
    # ladder exports -- a docs/ directory full of profiles proves nothing
    # about what this run will know.
    from deepreason.model_profiles import profiles_root, registry_fingerprint

    registry = registry_fingerprint()
    check(
        "§3",
        "the model-profile registry stamps FIVE profiles, not zero",
        registry["count"] == 5,
        f"count={registry['count']} at {profiles_root()} "
        f"-- {[row['model_id'] for row in registry['profiles']]}",
    )
    check(
        "§3",
        "every model this run seats has a profile document",
        {r.model_id for routes in manifest.roles.values() for r in routes}
        <= {row["model_id"] for row in registry["profiles"]},
        sorted(
            {r.model_id for routes in manifest.roles.values() for r in routes}
            - {row["model_id"] for row in registry["profiles"]}
        )
        or "all seated models described",
    )
    check(
        "§3",
        "no profile document failed to load",
        registry["problem_count"] == 0,
        registry["problems"] or "0 unreadable",
    )

    # ---- the one network check -------------------------------------------
    if want_catalogue:
        import urllib.request

        with urllib.request.urlopen("https://ollama.com/v1/models", timeout=60) as fh:
            listed = {m["id"] for m in json.load(fh).get("data", ())}
        wanted = {r.model_id for routes in manifest.roles.values() for r in routes}
        check(
            "§3",
            "every seat names a model the provider lists",
            wanted <= listed,
            sorted(wanted - listed) or f"all {len(wanted)} present",
        )

    print()
    if FAILURES:
        print(f"PREFLIGHT FAILED: {len(FAILURES)} of {CHECKS} checks")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"PREFLIGHT OK: {CHECKS} checks, 0 failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
