"""The seats/evidence law, attacked from every configuration Part A admits.

The law, verbatim from CLAUDE.md's "Operator design laws":

    Seats change how content is GENERATED, never what counts as
    EVIDENCE

and its binding clause, verbatim:

    no seat, mode, or package may let a generation seat's prose skip
    criticism.

Why this file exists. The 2026-08-13 audit
(`experiments/2026-08-13-audit/goal-trace.md`, row L2) rated the law
`partially-enforced`: the generation/criticism seat SEPARATION exists and is
tested, but no test pinned the invariant itself. Part A of this tranche then
made ~21 previously-refused configurations COMPILE, which is exactly the set
of shapes an attacker would reach for — a seat that cannot be refused at
compile time is a seat that must be stopped somewhere else. Every case below
takes one such shape, compiles it (it MUST compile now), and then shows the
law still holds at the point of use.

What these tests assert. The MECHANISM, never the prose: typed record
objects only — `harness.warrants`, attack edges, `Status`, the typed refusal
classes (`WellFormednessError`, `SchoolRouteResolutionError`,
`JudgeEnsemblePolicyError`, `RunManifestError`), and `compile_notices`. No
assertion in this file reads model output as evidence of anything.

The four load-bearing guards, located during Part A's downstream sweep:

1. `Harness._validate_warrant` — a warrant on a `rubric:` commitment MUST
   carry a `trace_ref` resolving to a conforming trial transcript, else
   `WellFormednessError`. Unbypassable, and on a FROZEN surface.
2. `require_cross_family_judge_ensemble` — the judge ensemble is checked
   against the IMMUTABLE LEASES before any judge call.
3. `informal/trial.py`'s `_block`/`_decline` — a missing critic, defender or
   judge role yields a typed logged no-op, never a warrant.
4. `resolve_school_role_lease` — a seat is reachable only through a
   manifest-frozen binding; nine typed refusal codes.

Mutation proof for this file is recorded in the tranche's VALIDATION.md:
guard 1 was disabled in a scratch copy, the file went RED, and the mutation
was discarded.

Tranche: experiments/2026-08-16-change-configs-complete-seats-test/
"""

from __future__ import annotations

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness, WellFormednessError
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import run_trial, transcript_blob
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import (
    EndpointLease,
    JudgeEnsemblePolicyError,
    SchoolRouteResolutionError,
    require_cross_family_judge_ensemble,
    resolve_school_role_lease,
)
from deepreason.ontology import (
    Commitment,
    Interface,
    Provenance,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.run_manifest import (
    CriticismPolicyV1,
    RunManifest,
    RunManifestError,
    SchoolRoleBindingV1,
    compile_run_manifest,
    preflight_payload,
    resolve_route_seat_behavioral_capability,
)
from deepreason.seat_bindings import (
    CRITICISM_SEAT_BINDINGS_FILENAME,
    SEAT_BINDINGS_FILENAME,
    criticism_seat_bindings_path,
    resolve_criticism_seats,
    seat_bindings_path,
)
from tests.conftest import art
from tests.test_run_manifest_v4 import (
    _binding,
    _compile_v4,
    _control_policy,
    _route,
    _school_execution,
)

STAMP = "2026-07-16T00:00:00Z"

CASE = "the passage uses parallel fifths in bar 3, violating clause 2"
DEFENCE = "the fifths are an intentional echo of the cantus firmus"


def _codes(manifest: RunManifest) -> list[str]:
    return [notice.code for notice in (manifest.compile_notices or ())]


def _criticism(**overrides) -> CriticismPolicyV1:
    values = {
        "minimum_foreign_school_coverage": 1,
        "bindings": (),
        "max_batch_size": 8,
        "target_eligibility": "accepted_school_artifacts",
        "authority": "observe_only",
        "allow_shared": True,
    }
    values.update(overrides)
    return CriticismPolicyV1(**values)


def _critic_binding(school: int, seat: int, endpoint_id: str, role="argumentative_critic"):
    return SchoolRoleBindingV1(
        school_id=f"school-{school}", role=role, seat=seat, endpoint_id=endpoint_id
    )


def _compile_with_criticism(config: Config, criticism, control=None) -> RunManifest:
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control or _control_policy(),
        criticism_policy=criticism,
    )


def _leases(manifest: RunManifest) -> dict[str, tuple[EndpointLease, ...]]:
    """Runtime leases derived from the manifest's own frozen routes — the
    honest case, where nothing has been tampered with between compile and
    dispatch. Any refusal below is therefore about the CONFIGURATION, not
    about a lease/manifest disagreement."""

    return {
        role: tuple(
            EndpointLease(role=role, seat=seat, route=route)
            for seat, route in enumerate(routes)
        )
        for role, routes in manifest.roles.items()
        if routes
    }


def _rubric_target(harness: Harness) -> tuple[str, Commitment]:
    register_standard(harness, "std-1", "clause 2: no parallel fifths", mode="absolute")
    kappa = Commitment(id="kappa-taste", eval="rubric:std-1")
    harness.register_commitment(kappa)
    target = art(
        harness,
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=["kappa-taste"]),
    )
    return target.id, kappa


# ===================================================================== B9/B10
# The frozen guard: prose cannot become evidence without the trial.


def test_b9_rubric_input_under_forbid_compiles_but_cannot_yield_a_warrant(tmp_path):
    """B9. Part A made a rubric payload under `rubric_policy="forbid"` compile
    with a notice instead of refusing. That notice buys the caller NOTHING at
    the evidence layer: a rubric-derived warrant with no conforming trial
    transcript is still refused by the harness's own well-formedness guard,
    and no warrant, attack edge, or status change survives the attempt."""

    manifest = compile_run_manifest(
        Config(roles={"conjecturer": _route("route-a")}),
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    payload = {
        "problem": {"description": "judge prose"},
        "commitments": [{"id": "kappa-taste", "eval": "rubric:std-1"}],
    }
    # Part A's promise: it compiles and discloses.
    assert "RUBRIC_INPUT_FORBIDDEN" in [
        n.code for n in preflight_payload(manifest, payload)
    ]

    # The law's promise: it still cannot become evidence.
    harness = Harness(tmp_path / "run")
    target_id, _ = _rubric_target(harness)
    nu = art(harness, "nu: a generation seat asserting its own soundness")
    bare = Warrant(
        id="w-generation-seat",
        target=target_id,
        type=WarrantType.DEMONSTRATIVE,
        commitment="kappa-taste",
        verdict="fail",
        trace_ref="inline:the-seat-said-so",
        validity_node=nu.id,
    )
    with pytest.raises(WellFormednessError):
        harness.create_artifact(
            "critic: a generation seat's prose, dressed as a ruling",
            provenance=Provenance(role="critic"),
            warrants=[bare],
        )

    assert not [w for w in harness.warrants.values() if w.target == target_id]
    assert harness.state.status.get(target_id) != Status.REFUTED


def test_b9b_the_same_warrant_registers_once_it_carries_a_real_transcript(tmp_path):
    """The discriminating half of B9. If `_validate_warrant` refused
    everything, B9 would prove nothing. The SAME warrant, differing only in
    that its `trace_ref` resolves to a conforming trial transcript, registers
    and moves the status. The guard discriminates on the transcript, which is
    the criticism machinery's own output — that is the law's mechanism."""

    harness = Harness(tmp_path / "run")
    target_id, _ = _rubric_target(harness)
    nu = art(harness, "nu: the attack is sound and relevant")
    trace = transcript_blob(
        harness,
        case=CASE,
        answer=DEFENCE,
        decisive_point="parallel fifths in bar 3",
        checks={"paraphrase": {"n": 0, "flips": 0}},
    )
    backed = Warrant(
        id="w-trial-backed",
        target=target_id,
        type=WarrantType.DEMONSTRATIVE,
        commitment="kappa-taste",
        verdict="fail",
        trace_ref=trace,
        validity_node=nu.id,
    )
    harness.create_artifact(
        "critic: a ruling that went through the trial",
        provenance=Provenance(role="critic"),
        warrants=[backed],
    )
    assert [w.id for w in harness.warrants.values() if w.target == target_id] == [
        "w-trial-backed"
    ]


def test_b10_single_family_judge_matrix_compiles_and_still_cannot_rule():
    """B10. A rubric input with fewer than two judge families compiles with a
    notice (Part A). The ensemble guard reads the IMMUTABLE LEASES, not the
    notice, and refuses before any judge call."""

    manifest = compile_run_manifest(
        Config(
            roles={
                "conjecturer": _route("route-a"),
                "judge": [
                    _route("judge-a", model="m1", family="fam", endpoint="https://a.invalid/v1"),
                    _route("judge-b", model="m2", family="fam", endpoint="https://b.invalid/v1"),
                ],
            }
        ),
        rubric_policy="require_cross_family",
        compiled_at=STAMP,
    )
    assert preflight_payload(manifest, {"standard": "rubric-standard"}) != ()

    with pytest.raises(JudgeEnsemblePolicyError):
        require_cross_family_judge_ensemble(_leases(manifest))


# ======================================================================== B7
# A generation-heavy topology cannot conjure a defence or a ruling.


def test_b7_defended_trial_without_a_defender_compiles_and_produces_no_warrant(tmp_path):
    """B7. `authority="defended_trial"` with no defender route compiles with a
    notice (Part A). At the point of use the trial DECLINES — typed, logged —
    and the target keeps its status. A missing seat cannot be substituted by
    the conjecturer's own prose."""

    manifest = _compile_with_criticism(
        Config(
            N_SCHOOLS=2,
            roles={
                "conjecturer": _route("route-a"),
                "argumentative_critic": _route("route-a"),
            },
        ),
        _criticism(
            bindings=(_critic_binding(0, 0, "route-a"), _critic_binding(1, 0, "route-a")),
            authority="defended_trial",
        ),
    )
    assert "V4_CRITICISM_DEFENDER_REQUIRED" in _codes(manifest)
    assert not manifest.roles.get("defender")

    harness = Harness(tmp_path / "run")
    target_id, kappa = _rubric_target(harness)
    # An adapter with a critic and judges but NO defender seat: exactly the
    # topology the manifest above authorizes.
    adapter = LLMAdapter(
        {
            "argumentative_critic": MockEndpoint(
                [json.dumps({"attack": True, "case": CASE})]
            ),
            "judge": [
                MockEndpoint(
                    [json.dumps({"verdict": "fail", "decisive_point": "parallel fifths in bar 3"})],
                    name="mock://judge-gemma",
                    model="gemma-test",
                ),
                MockEndpoint(
                    [json.dumps({"verdict": "fail", "decisive_point": "parallel fifths in bar 3"})],
                    name="mock://judge-qwen",
                    model="qwen-test",
                ),
            ],
        },
        harness.blobs,
        retry_max=2,
    )

    assert run_trial(harness, target_id, kappa, adapter, Config(), authority="status") is None
    assert not [w for w in harness.warrants.values() if w.target == target_id]
    assert harness.state.status[target_id] == Status.ACCEPTED
    blocked = [
        entry
        for entry in harness.log.read()
        if any("no-defender-role" in str(item) for item in entry.inputs)
    ]
    assert blocked, "the decline must be RECORDED, not merely silent"


# ==================================================================== B1/B2/B6
# School routing: a seat is reachable only through a frozen binding.


@pytest.mark.parametrize(
    ("label", "school_id", "expected_code"),
    (
        ("B2 unbound school", "school-1", "SCHOOL_ROUTE_BINDING_MISSING"),
        ("B1 unknown school", "school-9", "SCHOOL_ROUTE_SCHOOL_UNKNOWN"),
    ),
)
def test_b1_b2_a_school_without_a_frozen_binding_cannot_reach_a_seat(
    label: str, school_id: str, expected_code: str
):
    """B1/B2. An incomplete school roster compiles with a notice (Part A).
    Dispatch still refuses TYPED for any school the frozen bindings do not
    name — a generation seat cannot acquire a school's authority by being the
    only seat available."""

    config = Config(
        N_SCHOOLS=2,
        roles={
            "conjecturer": [
                _route("route-a", endpoint="https://a.invalid/v1"),
                _route("route-b", endpoint="https://b.invalid/v1"),
            ]
        },
    )
    manifest = _compile_v4(
        config,
        _control_policy(
            _school_execution(mode="route_bound", bindings=(_binding(0, 0, "route-a"),))
        ),
    )
    assert "V4_SCHOOL_BINDING_INCOMPLETE" in _codes(manifest)

    # The bound school still resolves — the guard is selective, not blanket.
    bound = resolve_school_role_lease(
        manifest, _leases(manifest), school_id="school-0", role="conjecturer"
    )
    assert bound.route.endpoint_id == "route-a"

    with pytest.raises(SchoolRouteResolutionError) as raised:
        resolve_school_role_lease(
            manifest, _leases(manifest), school_id=school_id, role="conjecturer"
        )
    assert raised.value.code == expected_code


def test_b6_a_criticism_binding_naming_a_generation_role_cannot_dispatch():
    """B6. A criticism binding naming `conjecturer` compiles with a notice
    (Part A). School routing supports exactly two roles, and a generation role
    is not one a criticism binding can reach."""

    manifest = _compile_with_criticism(
        Config(
            N_SCHOOLS=2,
            roles={
                "conjecturer": _route("route-a"),
                "argumentative_critic": _route("route-a"),
            },
        ),
        _criticism(
            bindings=(
                _critic_binding(0, 0, "route-a", role="conjecturer"),
                _critic_binding(1, 0, "route-a", role="conjecturer"),
            )
        ),
    )
    assert "V4_CRITICISM_ROLE_UNSUPPORTED" in _codes(manifest)

    with pytest.raises(SchoolRouteResolutionError) as raised:
        resolve_school_role_lease(
            manifest,
            _leases(manifest),
            school_id="school-0",
            role="argumentative_critic",
        )
    # The binding names `conjecturer`, so no critic binding covers school-0.
    assert raised.value.code == "SCHOOL_ROUTE_BINDING_MISSING"


def test_b3_two_schools_sharing_one_seat_resolve_to_the_same_lease():
    """B3. `allow_shared=False` overridden by explicit bindings compiles with a
    notice (Part A). The disclosure is accurate and the law is not dented: the
    two schools resolve to ONE lease. A single seat cannot present itself as
    two independent critics — it is the same route, and the record says so."""

    manifest = _compile_with_criticism(
        Config(
            N_SCHOOLS=2,
            roles={
                "conjecturer": _route("route-a"),
                "argumentative_critic": _route("route-a"),
            },
        ),
        _criticism(
            bindings=(_critic_binding(0, 0, "route-a"), _critic_binding(1, 0, "route-a")),
            allow_shared=False,
        ),
    )
    assert "V4_CRITICISM_SHARED_SEAT_FORBIDDEN" in _codes(manifest)

    leases = _leases(manifest)
    first = resolve_school_role_lease(
        manifest, leases, school_id="school-0", role="argumentative_critic"
    )
    second = resolve_school_role_lease(
        manifest, leases, school_id="school-1", role="argumentative_critic"
    )
    assert first.seat == second.seat == 0
    assert first.route == second.route


# ======================================================================= B12
# Scratch is declared advisory and stays advisory.


def test_b12_clamped_scratch_still_declares_itself_non_grounding():
    """B12. Over-claimed attention fractions clamp instead of refusing (Part
    A). Clamping changes how much a scratch seat may put in front of the
    conjecturer — GENERATION — and changes nothing about what its output
    counts as: the policy's epistemic boundary is a one-value Literal."""

    manifest = compile_run_manifest(
        Config(
            roles={"conjecturer": _route("route-a")},
            scratchpad={
                "enabled": True,
                "exploratory_fraction": 0.7,
                "underexposed_fraction": 0.7,
            },
        ),
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    policy = manifest.scratch_policy
    assert policy.exploratory_fraction + policy.underexposed_fraction == 1.0

    # The boundary is not a knob any configuration can turn: it is a
    # single-valued Literal on the authoring policy, and the proposal layer
    # stamps the identical constant on every scratch record.
    import typing

    from deepreason.run_manifest import ScratchAuthoringPolicyV1
    from deepreason.scratch.proposals import SCRATCH_EPISTEMIC_BOUNDARY

    assert typing.get_args(
        ScratchAuthoringPolicyV1.model_fields["epistemic_boundary"].annotation
    ) == ("advisory_non_grounding",)
    assert SCRATCH_EPISTEMIC_BOUNDARY == "advisory_non_grounding"
    assert ScratchAuthoringPolicyV1().epistemic_boundary == SCRATCH_EPISTEMIC_BOUNDARY


# ======================================================================= B13
# A grant that was skipped at compile is a grant no seat holds.


def test_b13_a_seat_with_no_frozen_route_holds_no_behavioral_authority():
    """B13. Part A made a grounded bridge with unbound stage roles compile
    (it used to crash untyped). The skipped grants are disclosed, and the
    dispatch resolver refuses typed: an unbound seat holds no authority to
    act on the contract, so nothing it could emit reaches the record."""

    from tests.test_run_input_v6_commitments import _config as v6_config
    from tests.test_run_input_v6_commitments import _control

    data = v6_config().model_dump(mode="json")
    data["bridge"] = {"mode": "grounded_two_stage"}
    manifest = compile_run_manifest(
        Config(**data),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(6),
        run_input_digest="a" * 64,
    )
    assert "V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED" in _codes(manifest)

    with pytest.raises(RunManifestError):
        resolve_route_seat_behavioral_capability(
            manifest,
            role=manifest.bridge_policy.ledger_role,
            seat=0,
            endpoint_id="anything",
            route_sha256="0" * 64,
        )


# ==================================================================== B14/B15
# The audit's L2 shapes: a generation seat binding is not a criticism seat.


def test_b14_b15_generation_seat_bindings_never_supply_a_criticism_seat(
    tmp_path, monkeypatch
):
    """B14/B15. The shapes `experiments/2026-08-13-audit/proof/goal-L2.txt`
    names: `resolve_seat_bindings` (generation side) and
    `resolve_criticism_seats` (criticism side) read DIFFERENT persisted
    files. Part A's seat-binding conversions resolve conflicts on the
    generation side; this proves that resolution cannot leak across.

    A generation-side binding file, however it resolves, leaves the criticism
    side EMPTY — so no amount of seat configuration can hand a generation
    seat the criticism side's authority."""

    home = tmp_path / "home"
    monkeypatch.setenv("DEEPREASON_HOME", str(home))
    environ = {"DEEPREASON_HOME": str(home)}

    generation = seat_bindings_path(environ=environ)
    criticism = criticism_seat_bindings_path(environ=environ)
    generation.parent.mkdir(parents=True, exist_ok=True)

    # The two levers are distinct files by construction, not by convention.
    assert generation.name == SEAT_BINDINGS_FILENAME
    assert criticism.name == CRITICISM_SEAT_BINDINGS_FILENAME
    assert generation != criticism

    # Write a generation-side binding for every group that claims a
    # generation role, including the conjecture/scratch overlap whose
    # conflict Part A's sibling tranche resolved by precedence.
    generation.write_text(
        "conjecture: /nonexistent/profile-a.json\n"
        "scratch: /nonexistent/profile-b.json\n"
    )
    assert generation.exists()

    # No criticism file was written, so the criticism side is empty. A
    # generation binding cannot populate it.
    assert resolve_criticism_seats(environ=environ) == {}
    assert not criticism.exists()


# --- natural-stop: recorded, never consumed ---------------------------------
#
# Q7's split-budget finding (docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md) hands
# the harness a free ~99% PPV correctness oracle: a completion that ends on its
# own is very likely right. The two-call seat protocol tranche RECORDS it and
# stops there, because acting on it would make a seat's generation behaviour
# decide what counts as evidence — exactly what the seats/evidence law forbids.
# The operator's own words for the scope: "Recorded, not acted on — no gate or
# label may consume it (seats/evidence law)." These two tests are what make
# that a mechanism rather than an intention.


def test_natural_stop_is_recorded_and_never_consumed():
    """Implements R7: no gate or label may consume LLMAttempt.natural_stop.

    A reference census, not a behavioural probe, because the claim is a
    NEGATIVE over the whole engine: the only way to show nothing consumes a
    field is to show nothing but its writers can even name it. Anchored to the
    module that owns the record and the package allowed to write it, so a
    rename inside those files keeps the test green and a new reader anywhere
    else turns it red.
    """

    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1] / "src" / "deepreason"
    allowed = {
        # Owns the record shape.
        root / "ontology" / "event.py",
        # The only package that speaks to a provider, and therefore the only
        # one that can observe a finish reason at all.
        root / "llm" / "adapter.py",
        root / "llm" / "split.py",
    }
    readers = {
        path
        for path in root.rglob("*.py")
        if "natural_stop" in path.read_text(encoding="utf-8")
    }
    assert readers <= allowed, sorted(str(p) for p in readers - allowed)

    # The census would be vacuous if the name never appeared at all: pin that
    # the writer side really does carry it, so deleting the field cannot make
    # this test pass.
    from deepreason.ontology.event import LLMAttempt

    assert "natural_stop" in LLMAttempt.model_fields
    assert LLMAttempt(prompt_ref="blob:p").natural_stop is None


def test_flipping_natural_stop_moves_no_typed_outcome(tmp_path, monkeypatch):
    """Implements R7: the field is inert in replay, not merely unread.

    The census above proves no module names the field. This proves the
    stronger property the law actually cares about: two runs identical except
    for natural_stop replay to the same state and the same verify_root
    verdict, so the signal cannot leak into a status, a label or a violation
    through any path a census could miss.
    """

    from deepreason.invariants import verify_root
    from deepreason.llm.firewall import route_fingerprint
    from deepreason.ontology.event import LLMAttempt, LLMCall
    from deepreason.run_manifest import persist_run_manifest
    from tests.test_process_metadata import (
        _manifest as _process_manifest,
        _patch_legacy_manifest_consumers,
    )

    def _root(name: str, natural_stop: bool | None):
        root = tmp_path / name
        endpoint = MockEndpoint([], name="mock://natural-stop", model="model-1")
        manifest = _process_manifest(endpoint)
        persist_run_manifest(manifest, root)
        _patch_legacy_manifest_consumers(monkeypatch, root, manifest)
        route = manifest.roles["conjecturer"][0]
        harness = Harness(root)
        prompt_ref = harness.blobs.put(b"natural stop prompt")
        raw_ref = harness.blobs.put(b"{}")
        harness.record_measure(
            inputs=["natural-stop-test"],
            llm=LLMCall(
                role="conjecturer",
                model=route.model_id,
                endpoint=route.base_url,
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                attempt_trace=[LLMAttempt(
                    prompt_ref=prompt_ref,
                    raw_ref=raw_ref,
                    contract_id="conjecturer.direct.v1",
                    endpoint_id=route.endpoint_id,
                    route_sha256=route_fingerprint(route),
                    model_profile=manifest.model_profile,
                    transport_profile=manifest.model_profile,
                    max_tokens=route.max_tokens,
                    timeout_s=route.timeout_s,
                    valid=True,
                    output_mechanism=route.output_mechanism,
                    natural_stop=natural_stop,
                )],
            ),
        )
        return root, harness

    stopped_root, stopped = _root("stopped", True)
    truncated_root, truncated = _root("truncated", False)

    # The applied view is the thing every status and label is computed from.
    assert stopped.state.model_dump_json() == truncated.state.model_dump_json()

    # And the replay verdict, which is what a run is judged by.
    def _verdict(root):
        report = verify_root(root)
        return (
            sorted(v["check"] for v in report["violations"]),
            json.dumps(report["stats"], sort_keys=True),
        )

    assert _verdict(stopped_root) == _verdict(truncated_root)

    # Mutation guard: the two roots must genuinely differ in the field, or the
    # equalities above are comparing a run against itself.
    def _stops(harness):
        return [
            attempt.natural_stop
            for event in harness.recent_events(1000)
            if getattr(event, "llm", None) is not None
            for attempt in event.llm.attempt_trace
        ]

    assert _stops(stopped) == [True]
    assert _stops(truncated) == [False]
