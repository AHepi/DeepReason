"""Rung 1b-ii: the CONSUMPTION side of the signal contract.

The operator's design law (CLAUDE.md, 2026-08-14) keys signals by SEAT
INSTANCE, not role -- one conjecturer may sit in "multiple structurally
asymmetric seats that may need throttling independently". Rung 1b-i delivered
the declaration side; this suite pins what the allocation controller DOES with
a declared signal.

The first test here is a REGRESSION written before its fix, on the operator's
own case (REQUEST.md Amendment 1b condition 2): a per-seat cap knob whose seat
is bound to a 16,384-token route. Replay validation resolved such a knob's
anchoring cap by looking the whole string up as a ROLE, missed, and fell back
to the unanchored [500, 2500] default -- refusing a limit the route itself
authorized. A regression test first seen green proves nothing about the bug it
names, so this one was run RED on the unfixed tree and its failure is committed
alongside it (`proof/s12_red.txt`).
"""

import json

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology import Provenance, Rule
from deepreason.ontology.event import LLMAttempt, LLMCall
from deepreason.run_manifest import Route, RunManifest, persist_run_manifest
from tests.test_process_metadata import _patch_legacy_manifest_consumers

# The two seats. Same model and base_url -- one conjecturer -- but different
# endpoint ids and different assigned ceilings, which is what "structurally
# asymmetric seats" means in the dimension the controller steers.
NARROW_SEAT_CAP = 4096
WIDE_SEAT_CAP = 16384


def _two_seat_manifest(endpoint) -> RunManifest:
    """One role, two seats. Mirrors `tests/test_process_metadata._manifest`
    and adds the second route; nothing else differs."""

    def route(endpoint_id: str, cap: int) -> Route:
        return Route(
            endpoint_id=endpoint_id,
            base_url=endpoint.name,
            model_id=endpoint.model,
            provider="mock",
            family="mock-family",
            max_tokens=cap,
        )

    return RunManifest(
        engine_profile="full",
        model_profile="compact",
        roles={
            "conjecturer": (
                route("mock-seat-0", NARROW_SEAT_CAP),
                route("mock-seat-1", WIDE_SEAT_CAP),
            )
        },
        rubric_policy="forbid",
        concurrency=1,
        pack_profile="compact",
        output_profile="compact",
        source_config_hash="0" * 64,
        compiled_at="2026-07-11T00:00:00Z",
        engine_config_json="{}",
    )


def _root_with_seat_policy(root, monkeypatch, *, knob, policy_cap, seat,
                           attempt_cap):
    """A root whose controller authorized `policy_cap` under `knob`, and whose
    one provider attempt on `seat` then used `attempt_cap`."""
    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    endpoint.max_tokens = WIDE_SEAT_CAP
    manifest = _two_seat_manifest(endpoint)
    persist_run_manifest(manifest, root)
    _patch_legacy_manifest_consumers(monkeypatch, root, manifest)
    route = manifest.roles["conjecturer"][seat]

    harness = Harness(root)
    harness.create_artifact(
        json.dumps(
            {"knobs": {knob: policy_cap}, "evidence": {}, "cycle": 1},
            sort_keys=True,
        ),
        provenance=Provenance(role="controller"),
        rule=Rule.REFL,
    )
    prompt_ref = harness.blobs.put(b"prompt")
    raw_ref = harness.blobs.put(b"{}")
    harness.record_measure(
        inputs=["process-test"],
        llm=LLMCall(
            role="conjecturer", model=route.model_id, endpoint=route.base_url,
            prompt_ref=prompt_ref, raw_ref=raw_ref,
            attempt_trace=[LLMAttempt(
                prompt_ref=prompt_ref, raw_ref=raw_ref,
                contract_id="conjecturer.direct.v1",
                endpoint_id=route.endpoint_id,
                route_sha256=route_fingerprint(route),
                seat=seat,
                model_profile=manifest.model_profile,
                transport_profile=manifest.model_profile,
                max_tokens=attempt_cap, timeout_s=route.timeout_s,
                valid=True, output_mechanism=route.output_mechanism,
            )],
        ),
    )
    return {item["check"] for item in verify_root(root)["violations"]}


# --- S12 (R16): the seat-anchored ceiling regression --------------------- #


def test_a_seat_knob_anchors_to_its_own_route_ceiling(tmp_path, monkeypatch):
    """12,000 is outside the STATIC cap:conjecturer envelope [800, 5000] and
    outside the unanchored default [500, 2500], and INSIDE the barrier
    anchored to seat 1's own 16,384-token route.

    Resolving `cap:conjecturer#1` by looking the whole string up as a role
    misses, falls back to the unanchored default, and refuses a limit the
    route itself authorized -- which makes per-seat throttling unreplayable.
    """
    checks = _root_with_seat_policy(
        tmp_path / "seat-anchored", monkeypatch,
        knob="cap:conjecturer#1", policy_cap=12_000, seat=1,
        attempt_cap=12_000,
    )
    assert "attempt-limits" not in checks, (
        "a per-seat knob was refused a limit its own route assigned: "
        f"{sorted(checks)}"
    )


def test_a_seat_knob_is_still_bounded_by_its_own_route(tmp_path, monkeypatch):
    """The widening is per-seat, not a hole. The NARROW seat's 4,096 ceiling
    binds seat 0 even though seat 1 carries 16,384: a barrier anchored to the
    role's widest route would authorize 12,000 here, and must not."""
    checks = _root_with_seat_policy(
        tmp_path / "seat-bounded", monkeypatch,
        knob="cap:conjecturer#0", policy_cap=12_000, seat=0,
        attempt_cap=12_000,
    )
    assert "attempt-limits" in checks


# --- S11 (R15): the reader fix is reader-only ---------------------------- #


def _pre_seat_keying_anchor(roles, knob):
    """The anchoring rule EXACTLY as it stood before seat keying.

    Transcribed from the removed body of `invariants._configured_role_cap`, and
    it is the rule the map states in prose: "the widest cap the manifest
    assigned this knob's role ... None for a role with no assigned limit and
    for every non-cap knob". Kept here rather than fetched from git history
    because a test that greps a commit stops working the moment history is
    rewritten, while a transcribed rule keeps failing for the right reason as
    long as the rule is the claim.

    The empirical half of this proof is the 107-root before/after sweep; this
    is the analytic half, and it says WHY the sweep came back empty.
    """
    if not knob.startswith("cap:"):
        return None
    caps = [
        route.max_tokens
        for route in (roles.get(knob[len("cap:"):], ()) or ())
        if getattr(route, "max_tokens", None) is not None
    ]
    return max(caps) if caps else None


def test_a_role_keyed_knob_resolves_exactly_as_it_did_before_seat_keying():
    """Every knob spelling that a committed root could contain resolves
    byte-identically before and after the reader fix.

    This is the operator's condition on the granted frozen-surface contact
    (REQUEST.md Amendment 1b condition 1): the fix may only change what a
    SEAT-keyed knob resolves to, and nothing recorded uses that form yet, so
    zero verification verdicts may move.
    """
    from deepreason.allocation import route_cap_for_knob

    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    endpoint.max_tokens = WIDE_SEAT_CAP
    roles = dict(_two_seat_manifest(endpoint).roles)
    roles["judge"] = (
        Route(
            endpoint_id="judge-0", base_url=endpoint.name,
            model_id=endpoint.model, provider="mock", family="mock-family",
            max_tokens=2048,
        ),
    )
    roles["summarizer"] = (
        Route(
            endpoint_id="sum-0", base_url=endpoint.name,
            model_id=endpoint.model, provider="mock", family="mock-family",
        ),
    )

    unchanged = [
        # every bound role, including the multi-seat one and one with no
        # assigned limit
        "cap:conjecturer", "cap:judge", "cap:summarizer",
        # a cap knob naming a role this manifest does not bind
        "cap:vision_critic",
        # non-cap knobs, which are never anchored
        "VS_K", "PACK_TOKEN_BUDGET", "timeout:transport", "FLOOR", "HV_MIN",
        # the degenerate spellings
        "cap:", "not-a-knob", "",
    ]
    for knob in unchanged:
        assert route_cap_for_knob(roles, knob) == _pre_seat_keying_anchor(
            roles, knob
        ), f"{knob!r} resolves differently than it did before seat keying"


def test_only_the_seat_keyed_form_resolves_differently():
    """The other half of the same claim: the fix is not inert.

    `cap:conjecturer#0` and `cap:conjecturer#1` are the ONLY spellings whose
    answer moves, and they move to their own seat's route rather than to the
    role's widest one. Without this the previous test would pass on a fix that
    changed nothing at all.
    """
    from deepreason.allocation import route_cap_for_knob

    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    endpoint.max_tokens = WIDE_SEAT_CAP
    roles = _two_seat_manifest(endpoint).roles

    assert route_cap_for_knob(roles, "cap:conjecturer") == WIDE_SEAT_CAP
    assert route_cap_for_knob(roles, "cap:conjecturer#0") == NARROW_SEAT_CAP
    assert route_cap_for_knob(roles, "cap:conjecturer#1") == WIDE_SEAT_CAP
    # A seat the role does not have anchors to nothing rather than silently
    # borrowing the role's widest route.
    assert route_cap_for_knob(roles, "cap:conjecturer#9") is None
    # And the pre-seat-keying rule disagrees on exactly these, which is what
    # makes them the fix rather than a no-op.
    assert _pre_seat_keying_anchor(roles, "cap:conjecturer#1") is None


# --- shared fixtures for the live-controller half ------------------------ #

import pytest

from deepreason.allocation import open_loop_notices, open_loop_signals
from deepreason.config import Config
from deepreason.controller import Controller, is_generator_knob
from deepreason.llm.adapter import LLMAdapter
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.run_manifest import compile_run_manifest
from tests.test_run_manifest_v4 import _route as _config_route

STAMP = "2026-07-16T00:00:00Z"
CORE_ROLES = (
    "conjecturer", "argumentative_critic", "defender", "variator", "synthesizer",
)


class _SeatEndpoint:
    """One seat, carrying only what the controller reads."""

    def __init__(self, cap):
        self.name = "ep"
        self.model = "m"
        self.max_tokens = cap
        self.timeout_s = 120
        self.last_finish_reason = None
        self.last_usage = None
        self.last_mean_surprisal = None


def _live_harness(root) -> Harness:
    harness = Harness(root)
    harness.register_commitment(Commitment(id="k", eval="predicate:'x' in content"))
    harness.register_problem(
        Problem(
            id="p", description="d", criteria=["k"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    return harness


def _seat_calls(harness, role, seat, count, *, truncated):
    """Provider calls attributed to ONE seat, via the seat index the record
    already carries on every attempt."""
    for _ in range(count):
        harness._commit(
            Rule.CONJ, inputs=["p"], outputs=[],
            llm=LLMCall(
                role=role, model="m", endpoint="e",
                prompt_ref="inline:p", raw_ref="inline:r",
                truncated=truncated, attempts=1,
                attempt_trace=[LLMAttempt(
                    prompt_ref="inline:p", raw_ref="inline:r", seat=seat,
                )],
            ),
        )


def _authority_payloads(harness) -> list[dict]:
    return [
        json.loads(event.inputs[3] if len(event.inputs) > 3 else event.inputs[2])
        for event in harness.log.read()
        if event.inputs and event.inputs[0] == "controller-authority"
    ]


def _policy_bodies(harness) -> list[dict]:
    bodies = []
    for event in harness.log.read():
        if event.rule != Rule.REFL:
            continue
        for aid in event.outputs:
            artifact = harness.state.artifacts.get(aid)
            if (
                artifact is None
                or artifact.provenance.role.value != "controller"
                or not artifact.content_ref.startswith("inline:")
            ):
                continue
            body = json.loads(artifact.content_ref[len("inline:"):])
            if isinstance(body, dict) and isinstance(body.get("knobs"), dict):
                bodies.append(body)
    return bodies


# --- S1 (R1, R2): seat instances throttle independently ------------------ #


def test_two_asymmetric_seats_throttle_independently(tmp_path):
    """The operator's requirement, verbatim: one conjecturer sitting in
    "multiple structurally asymmetric seats that may need throttling
    independently".

    Seat 0 is roomy and never truncates; seat 1 is starved and truncates every
    call. Before seat keying both windows pooled under `cap:conjecturer` and
    `_apply_cap` wrote BOTH endpoints, so the two seats had exactly one
    throttle between them. Here they move in OPPOSITE directions in the same
    cycle, which no shared knob can do.
    """
    harness = _live_harness(tmp_path / "asymmetric")
    roomy, starved = _SeatEndpoint(4096), _SeatEndpoint(1000)
    adapter = LLMAdapter({"conjecturer": [roomy, starved]}, harness.blobs)
    _seat_calls(harness, "conjecturer", 0, 6, truncated=False)
    _seat_calls(harness, "conjecturer", 1, 6, truncated=True)

    controller = Controller(harness, adapter)
    controller.step()

    assert starved.max_tokens > 1000, (
        "the truncating seat was not widened; its signal pooled with its "
        "sibling's"
    )
    assert roomy.max_tokens < 4096, (
        "the clean seat was not settled down; the two seats share a throttle"
    )
    knobs = _policy_bodies(harness)[-1]["knobs"]
    assert set(knobs) == {"cap:conjecturer#0", "cap:conjecturer#1"}, knobs
    # The evidence is keyed the same way, so a reader of the log can tell
    # which seat justified which move.
    assert set(_policy_bodies(harness)[-1]["evidence"]) >= {
        "cap:conjecturer#0".removeprefix("cap:"),
        "cap:conjecturer#1".removeprefix("cap:"),
    }


def test_a_single_seat_role_keeps_the_bare_role_spelling(tmp_path):
    """C1: no existing name changes spelling.

    A role bound to one seat HAS one seat instance, and its canonical name is
    the bare role name. Every topology in a committed root is single-seat for
    the roles the controller steers, so nothing recorded is re-spelled.
    """
    harness = _live_harness(tmp_path / "single")
    endpoint = _SeatEndpoint(1000)
    adapter = LLMAdapter({"conjecturer": endpoint}, harness.blobs)
    _seat_calls(harness, "conjecturer", 0, 6, truncated=True)

    Controller(harness, adapter).step()

    knobs = _policy_bodies(harness)[-1]["knobs"]
    assert set(knobs) == {"cap:conjecturer"}, knobs
    assert not any("#" in knob for knob in knobs)


def test_seat_identity_is_read_from_the_attempt_trace(tmp_path):
    """No new role, and no new record field (R3).

    The seat index is `LLMAttempt.seat`, which every attempt has carried since
    before this rung and which `LLMCall._school_route_matches_attempts`
    already validates against the school-route receipt. An event with no trace
    predates the field and reads as seat 0.
    """
    harness = _live_harness(tmp_path / "identity")
    adapter = LLMAdapter(
        {"conjecturer": [_SeatEndpoint(1000), _SeatEndpoint(1000)]},
        harness.blobs,
    )
    _seat_calls(harness, "conjecturer", 1, 4, truncated=True)
    controller = Controller(harness, adapter)

    signals = controller._process_signals()

    assert set(signals) == {"cap:conjecturer#1".removeprefix("cap:")}
    assert signals["conjecturer#1"]["truncation_rate"] == 1.0


# --- S3 (R3): the qualification subject digest does not move ------------- #


def test_the_shipped_qualification_subject_digest_does_not_move():
    """No role was added, and no compile notice reaches the shipped path.

    The pin exists so an ACCIDENTAL digest move is loud: a role added
    anywhere, or a `compile_notices` entry appearing on the preparation
    manifest, costs a ~14-minute qualification battery per home, which is the
    whole reason R3 said "do NOT add a role".

    The value moved ONCE, deliberately, on 2026-08-26 (F3): the operator
    turned research on by default ("turning research and, simulation and
    coding permanently on"), so the compiled manifest now carries an enabled
    research policy with a frozen allowlist, and every subject built from the
    engaged preset is a different subject. That cost was measured before the
    code (that tranche's SPEC.md, M1) and priced in its DELIVERY.md rather
    than discovered here.

        d47cb2bf27021474aa17933bc3dcfeeb5dfb1c23b0cfe49452941aace39088dc  before
        f3bb65623852cf7c5387ba4ef745dc4ebeadb62ca3493416fecfb475c6d80f9e  after

    The two structural assertions are unchanged and are what this test is
    actually for; only the constant moved, and it moved for a recorded reason.
    """
    from deepreason.config import Config
    from deepreason.preparation import qualification_subject_manifest
    from deepreason.qualification import qualification_subject_digest
    from tests.test_public_v6_facade import _profile

    profile = _profile()
    manifest = qualification_subject_manifest(profile)
    assert manifest.compile_notices is None
    assert qualification_subject_digest(manifest, profile) == (
        "f3bb65623852cf7c5387ba4ef745dc4ebeadb62ca3493416fecfb475c6d80f9e"
    )
    # The three F3 Config knobs are dropped from the versioned source echo, so
    # THEY moved nothing: the digest above is the price of the research
    # default alone. Asserting it here keeps the two causes separable if the
    # value ever moves again.
    assert manifest.inquiry_capability_policy.research.enabled is True
    for knob in (
        "SEED_PROBLEM_BUDGET_FLOOR",
        "ATTENTION_ALLOCATION_POLICY",
        "CHANNELS_DISABLED",
    ):
        assert knob in type(Config()).model_fields, knob
        assert knob not in manifest.engine_config_json, knob


# --- S5 (R4): the compiled configuration matrix -------------------------- #


def _class_config(**overrides) -> Config:
    route = dict(_config_route("shared-endpoint"))
    route["max_tokens"] = 4096
    roles = overrides.pop("roles", {r: dict(route) for r in CORE_ROLES})
    return Config(roles=roles, **overrides)


def _compile_class(config, **kwargs):
    return compile_run_manifest(
        config, schema_version=3, workload_profile="text",
        rubric_policy="forbid", compiled_at=STAMP, **kwargs
    )


def _bound_roles(manifest) -> list[str]:
    """A role KEY with no routes is not a bound seat. The compiler emits every
    canonical key, so asking `manifest.roles` for membership would report a
    judge in a run that binds none."""
    return sorted(role for role, routes in manifest.roles.items() if routes)


CONFIGURATION_CLASSES = {
    "solo": ({}, {"single_model": "shared-model"}),
    "no-schools": ({"SCHOOL_SEATS_ENABLED": False}, {}),
    "judges-off": ({"JUDGE_SEATS_ENABLED": False}, {}),
    "legacy-on": ({"LEGACY_CRITICISM_ENABLED": True}, {}),
}


@pytest.mark.parametrize("name", sorted(CONFIGURATION_CLASSES))
def test_the_configuration_matrix_compiles_attaches_and_closes_every_loop(
    name, tmp_path
):
    """R4's three parts, per configuration class: it COMPILES, the CONTROLLER
    ATTACHES, and EVERY POLICY-REFERENCED SIGNAL HAS A PRODUCER.

    Topology-independence is the property being pinned. The allocation
    controller must not care which of these a run is -- it reads the signal
    interface, and the interface answers the same way in all four.
    """
    overrides, compile_kwargs = CONFIGURATION_CLASSES[name]
    manifest = _compile_class(_class_config(**overrides), **compile_kwargs)

    # (a) compiles
    bound = _bound_roles(manifest)
    assert bound, f"{name} bound no seat at all"

    # (b) the controller attaches, and states an authority over every seat
    harness = _live_harness(tmp_path / name)
    adapter = LLMAdapter(
        {
            role: [_SeatEndpoint(route.max_tokens) for route in manifest.roles[role]]
            for role in bound
        },
        harness.blobs,
    )
    controller = Controller(harness, adapter)
    controller.step()

    payload = _authority_payloads(harness)[0]
    stated = set(payload["steerable"]) | set(payload["unsteerable"])
    assert stated == set(bound), (
        f"{name}: the controller said nothing about "
        f"{set(bound) ^ stated} — silence is the defect shape (ERRATA E28)"
    )
    assert payload["steerable"], f"{name}: the controller can steer nothing"

    # (c) every policy-referenced signal has a producer
    assert open_loop_signals(bound) == (), (
        f"{name} cannot produce {open_loop_signals(bound)}"
    )
    assert payload["open_loop"] == []


# --- S6 (R5, R6, R7): disclose, never die -------------------------------- #


def test_a_critic_less_topology_compiles_with_a_typed_open_loop_notice():
    """The operator's clause (5): a topology that cannot produce a signal
    COMPILES, carrying a typed notice.

    Binding no `argumentative_critic` means nothing can ever attack a
    controller policy, so `allocation.policy-contested.v1` has no producer and
    fail-static can never fire. That is a real fact about the run worth
    disclosing -- and a disclosure, never a refusal (the all-configurations
    law).
    """
    route = dict(_config_route("shared-endpoint"))
    route["max_tokens"] = 4096
    manifest = _compile_class(
        _class_config(roles={r: dict(route) for r in ("conjecturer", "defender")})
    )

    bound = _bound_roles(manifest)
    assert "argumentative_critic" not in bound
    assert open_loop_signals(bound) == ("allocation.policy-contested.v1",)

    notices = open_loop_notices(bound)
    assert [n.code for n in notices] == ["ALLOCATION_OPEN_LOOP"]
    assert notices[0].message == (
        "allocation open-loop for signal allocation.policy-contested.v1"
    )
    # A notice that names no way to close the loop is a complaint, not a
    # disclosure.
    assert "argumentative_critic" in notices[0].resolution


def test_the_controller_authority_record_carries_the_open_loop(tmp_path):
    """R6: extend the `controller-authority` record the E28 fix established.

    E28's lesson was that a controller with authority over nothing said
    nothing. The same shape applies one level up: a controller whose
    fail-static branch can never fire must not be silent about it either.
    """
    harness = _live_harness(tmp_path / "openloop")
    adapter = LLMAdapter({"conjecturer": _SeatEndpoint(1000)}, harness.blobs)
    _seat_calls(harness, "conjecturer", 0, 6, truncated=True)

    Controller(harness, adapter).step()

    payload = _authority_payloads(harness)[0]
    assert payload["open_loop"] == ["allocation.policy-contested.v1"]
    # Nothing died: the controller still steered on this topology.
    assert payload["steerable"] == ["conjecturer"]
    assert _policy_bodies(harness), "the open loop stopped an otherwise fine run"


# --- S8 (R10): allocation touches EFFICIENCY, NEVER EVIDENCE ------------- #
#
# The row to be strictest about. Seat identity is provenance-shaped, and
# provenance reaching adjudication is the one thing the harness forbids by
# construction (spec §0, calculus C5; v0.1 Axiom 4.1, Genesis Inertness). Keying
# a signal by seat instance is exactly the kind of change that could smuggle it
# in, so the differential below is written to fail if it ever does.


def _scripted_epistemic_content(harness):
    """The same conjecture, the same attack on it, in both arms.

    A differential over an empty graph proves nothing -- every label would be
    trivially equal. This puts a real adjudication in front of the comparison:
    a conjecture, a critic's validity node, and an argumentative warrant
    targeting the conjecture.
    """
    from deepreason.ontology import Warrant, WarrantType

    conjecture = harness.create_artifact(
        "x: the tides follow the moon", provenance=Provenance(role="conjecturer")
    )
    nu = harness.create_artifact(
        "nu: the attack is sound", provenance=Provenance(role="critic")
    )
    harness.create_artifact(
        "critic: the mechanism is not load-bearing",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(
            id="w:attack:x", target=conjecture.id,
            type=WarrantType.ARGUMENTATIVE, validity_node=nu.id,
        )],
        rule=Rule.CRIT,
    )
    return conjecture.id


def _epistemic_state(harness) -> dict:
    """Everything adjudication owns, with allocation's OWN artifacts removed.

    A controller policy is an ordinary registered artifact and therefore has a
    status of its own -- that is the design (policy-as-attackable-artifact, P6),
    not a leak. The claim under test is that no OTHER artifact's label, and no
    edge, moves because allocation ran.
    """
    allocation_owned = {
        aid for aid, artifact in harness.state.artifacts.items()
        if artifact.provenance.role.value == "controller"
    }
    return {
        "status": {
            aid: status.value
            for aid, status in harness.state.status.items()
            if aid not in allocation_owned
        },
        "att": sorted(
            edge for edge in harness.state.att
            if not set(edge) & allocation_owned
        ),
        "dep": sorted(
            edge for edge in harness.state.dep
            if not set(edge) & allocation_owned
        ),
        "carries": sorted(
            pair for pair in harness.state.carries
            if not set(pair) & allocation_owned
        ),
        "artifacts": sorted(set(harness.state.artifacts) - allocation_owned),
    }


def test_evidence_is_identical_whether_or_not_allocation_ran(tmp_path):
    """The load-bearing guard: two arms, the same scripted record, one stepped
    by a controller whose seats are deliberately asymmetric.

    If a seat key -- or any allocation decision derived from one -- ever
    reaches a label, a warrant or an edge, the two arms diverge here. The
    asymmetry is not decoration: it makes the controller take DIFFERENT
    decisions for two seats of one role, so the seat key is demonstrably
    driving behaviour while the evidence stays fixed.
    """
    steered = _live_harness(tmp_path / "steered")
    bare = _live_harness(tmp_path / "bare")
    for harness in (steered, bare):
        _scripted_epistemic_content(harness)
        _seat_calls(harness, "conjecturer", 0, 6, truncated=False)
        _seat_calls(harness, "conjecturer", 1, 6, truncated=True)

    roomy, starved = _SeatEndpoint(4096), _SeatEndpoint(1000)
    controller = Controller(
        steered, LLMAdapter({"conjecturer": [roomy, starved]}, steered.blobs)
    )
    for _ in range(4):
        controller.step()

    # The controller really did steer, and really did split the two seats --
    # otherwise this test would pass by doing nothing.
    assert starved.max_tokens != 1000 and roomy.max_tokens != 4096
    assert _policy_bodies(steered)

    assert _epistemic_state(steered) == _epistemic_state(bare), (
        "an allocation decision changed the epistemic record: allocation "
        "touches efficiency, never evidence"
    )


def test_evidence_never_admits_a_tribunal_knob_from_a_policy_body(tmp_path):
    """The ledger half. A policy body is ordinary JSON in the log, so the
    values it names are attacker-controlled in the only sense that matters:
    nothing but this filter stands between a body and the endpoints.
    """
    harness = _live_harness(tmp_path / "ledger")
    controller = Controller(
        harness, LLMAdapter({"conjecturer": _SeatEndpoint(1000)}, harness.blobs)
    )

    admitted = controller._validated_policy_knobs({
        "knobs": {
            "cap:conjecturer": 1600,      # generator-ledger: admitted
            "FLOOR": 3,                   # tribunal-ledger: never
            "HV_MIN": 1,                  # tribunal-ledger: never
            "ARG_CRIT_PER_CYCLE": 9,      # tribunal-ledger: never
            "status": 1,                  # not a knob at all
        }
    })

    assert admitted == {"cap:conjecturer": 1600}, admitted
    for knob in ("FLOOR", "HV_MIN", "ARG_CRIT_PER_CYCLE", "status"):
        assert not is_generator_knob(knob), knob


def test_allocation_reaches_no_subsystem_and_writes_no_verdict():
    """The architecture half, applied to the NEW module.

    `test_the_allocation_controller_consumes_only_the_interface` pins
    `controller.py`; this pins `allocation.py`, which is now the only module
    on the allocation side that may name an adjudication status at all. It may
    READ one about its own artifact; it may never write one, nor mint a
    warrant or an edge.
    """
    import ast
    import pathlib

    import deepreason.allocation as allocation_module

    source = pathlib.Path(allocation_module.__file__).read_text()
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    reached = sorted(
        module for module in imported
        if module.startswith("deepreason.")
        and module.split(".")[1] in ("schools", "rules", "informal", "capture",
                                     "adjudication")
    )
    assert not reached, f"allocation.py reaches into {reached}"

    for writer in ("create_artifact", "record_warrant", "Warrant",
                   "att_add", "dep_add", "status ="):
        assert writer not in source, (
            f"allocation.py names {writer!r}; allocation may price attention "
            f"and may never write evidence"
        )
