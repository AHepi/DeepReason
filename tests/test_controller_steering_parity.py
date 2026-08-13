"""Regression (grounded-extension run-8e22d0431fd2b98d): the token-steering
controller must actually steer a compiled-config run, and must say so when
it cannot.

That root recorded 12,991 events across two epochs with ZERO steering
artifacts — `cap:`, `envelope`, `steer`, `policy_eval` and `knob` each occur
0 times in its `log.jsonl` — despite `config.CONTROLLER=True` and
`ops.run_scheduler` constructing the controller. The controller WAS attached
and WAS stepped; every knob it could have moved was skipped in silence,
because the static `ENVELOPES` table named six roles while the manifest bound
eleven, and pinned a widest ceiling of 5,000 while every bound role carried
`max_tokens=16384`.

Two properties are pinned here, and the second is the one that makes the
first hard to lose again:

  1. every role a manifest binds is inside a control barrier that contains
     the cap the run assigned it, so the steering loop fires; and
  2. an assigned limit is OPTIONAL, and a role the controller may not steer
     is RECORDED with its typed reason rather than skipped — silence is the
     defect shape, not the absence of movement.

The replay half matters as much: a steered cap only survives `verify_root`
if replay validation re-derives the same anchored barrier the controller
wrote against. Both directions are asserted, so a reader that drifts back to
the static table fails here rather than in a live run.
"""

import json

import pytest

from deepreason.controller import (
    DEFAULT_CAP_ENVELOPE,
    ENVELOPES,
    TRIBUNAL_LEDGER,
    Controller,
    cap_envelope,
    is_generator_knob,
)
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
)
from deepreason.ontology.event import LLMAttempt, LLMCall
from deepreason.run_manifest import persist_run_manifest
from tests.test_process_metadata import (
    _manifest,
    _patch_legacy_manifest_consumers,
)

# The eleven roles the grounded manifest binds, and the cap it pins on every
# one of them. Read off run-manifest.json, not invented: five of these roles
# appear in no static envelope, and 16384 exceeds every static ceiling.
GROUNDED_ROLES = (
    "argumentative_critic",
    "conjecturer",
    "defender",
    "grounding_reviewer",
    "judge",
    "property_designer",
    "summarizer",
    "synthesizer",
    "thesis",
    "variator",
    "vision_critic",
)
GROUNDED_CAP = 16384

# Roles the committed log shows actually calling a provider.
CALLING_ROLES = ("judge", "argumentative_critic", "defender", "conjecturer",
                 "variator")


class _Endpoint:
    """An endpoint carrying only what the controller reads: a completion cap
    and a read timeout. `max_tokens=None` models a role the operator bound
    without assigning a limit."""

    def __init__(self, cap=GROUNDED_CAP):
        self.name = "ep"
        self.model = "m"
        self.max_tokens = cap
        self.timeout_s = 120
        self.last_finish_reason = None
        self.last_usage = None
        self.last_mean_surprisal = None


def _harness(root) -> Harness:
    h = Harness(root)
    h.register_commitment(Commitment(id="k", eval="predicate:'x' in content"))
    h.register_problem(
        Problem(
            id="p", description="d", criteria=["k"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    return h


def _clean_calls(h: Harness, role: str, n: int) -> None:
    """The signal the grounded log carries: never truncated, never repaired.
    All 666 of its `event.llm` records have truncated=False, attempts=1."""
    for _ in range(n):
        h._commit(
            Rule.CONJ, inputs=["p"], outputs=[],
            llm=LLMCall(
                role=role, model="m", endpoint="e",
                prompt_ref="inline:p", raw_ref="inline:r",
                truncated=False, attempts=1,
            ),
        )


def _authority_records(h: Harness) -> list[list[str]]:
    return [
        list(e.inputs)
        for e in h.log.read()
        if e.inputs and e.inputs[0] == "controller-authority"
    ]


def _policies(h: Harness) -> list[dict]:
    bodies = []
    for event in h.log.read():
        if event.rule != Rule.REFL:
            continue
        for aid in event.outputs:
            artifact = h.state.artifacts.get(aid)
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


# --- 1. the barrier covers every bound role, anchored to its assigned cap - #


def test_every_manifest_bound_role_gets_a_barrier_containing_its_cap(tmp_path):
    h = _harness(tmp_path / "cover")
    adapter = LLMAdapter(
        {role: _Endpoint() for role in GROUNDED_ROLES}, h.blobs
    )

    controller = Controller(h, adapter)

    for role in GROUNDED_ROLES:
        knob = f"cap:{role}"
        envelope = controller.envelopes.get(knob)
        assert envelope is not None, f"{role} has no control barrier"
        assert envelope["min"] <= GROUNDED_CAP <= envelope["max"], (
            f"{role}: assigned cap {GROUNDED_CAP} is outside its barrier "
            f"[{envelope['min']}, {envelope['max']}] — _propose would skip it"
        )
    # The five roles the static table never named are covered by derivation,
    # not by a longer hardcoded list: that is what stops the defect recurring
    # when a manifest binds a twelfth role.
    assert {r for r in GROUNDED_ROLES if f"cap:{r}" not in ENVELOPES} == {
        "grounding_reviewer", "property_designer", "summarizer", "thesis",
        "vision_critic",
    }


def test_a_configured_cap_may_only_widen_a_barrier_never_narrow_it():
    static = ENVELOPES["cap:conjecturer"]

    generous = cap_envelope("cap:conjecturer", GROUNDED_CAP)
    assert generous["max"] == GROUNDED_CAP and generous["min"] == static["min"]

    frugal = cap_envelope("cap:conjecturer", 100)
    assert frugal["min"] == 100 and frugal["max"] == static["max"]

    # An assigned limit is optional; without one the barrier is the static
    # shape, unanchored.
    assert cap_envelope("cap:conjecturer", None) == dict(static)
    # A role the static table never named inherits the default shape.
    assert cap_envelope("cap:vision_critic", None) == dict(DEFAULT_CAP_ENVELOPE)
    # A non-cap knob with no static envelope has no barrier to derive, so it
    # stays unauthorizable rather than picking up a default.
    assert "VS_K" not in ENVELOPES
    assert cap_envelope("VS_K", 4096) is None


def test_no_tribunal_knob_can_pass_as_a_generator_cap():
    for knob in TRIBUNAL_LEDGER:
        assert not is_generator_knob(knob), f"{knob} is tribunal-ledger"
        assert cap_envelope(knob, 4096) is None, (
            f"{knob} must not acquire a control barrier"
        )
    # A bare prefix names no role and is not a knob.
    assert not is_generator_knob("cap:")
    assert is_generator_knob("cap:grounding_reviewer")


# --- 2. the loop actually fires on the grounded configuration ------------ #


def test_the_grounded_configuration_steers_instead_of_sitting_inert(tmp_path):
    h = _harness(tmp_path / "steer")
    endpoints = {role: _Endpoint() for role in GROUNDED_ROLES}
    adapter = LLMAdapter(dict(endpoints), h.blobs)
    for role in CALLING_ROLES:
        _clean_calls(h, role, 6)

    controller = Controller(h, adapter)
    proposals = [controller.step() for _ in range(4)]

    moved = [p for p in proposals if p]
    assert moved, (
        "controller proposed nothing across four cycles on the exact "
        "configuration the grounded root ran — this is run-8e22d0431fd2b98d"
    )
    assert _policies(h), "a steering decision left no replayable policy"
    # Every move stays inside the operator's own assigned cap.
    for role in GROUNDED_ROLES:
        assert endpoints[role].max_tokens <= GROUNDED_CAP
    # Only roles with signal move; a bound role that never called stays put.
    assert endpoints["thesis"].max_tokens == GROUNDED_CAP


def test_a_bound_role_is_never_widened_past_the_cap_the_operator_assigned(
    tmp_path,
):
    h = _harness(tmp_path / "ceiling")
    endpoint = _Endpoint(cap=GROUNDED_CAP)
    adapter = LLMAdapter({"conjecturer": endpoint}, h.blobs)
    controller = Controller(h, adapter)
    for _ in range(12):
        h._commit(
            Rule.CONJ, inputs=["p"], outputs=[],
            llm=LLMCall(
                role="conjecturer", model="m", endpoint="e",
                prompt_ref="inline:p", raw_ref="inline:r",
                truncated=True, attempts=1,
            ),
        )
        controller.step()

    assert endpoint.max_tokens == GROUNDED_CAP, (
        "persistent truncation widened a cap past the operator's setting"
    )


# --- 3. an unsteerable role is recorded, never silently skipped ---------- #


def test_a_controller_with_nothing_to_steer_records_that_it_has_nothing(
    tmp_path,
):
    """Role-assigned limits are optional (operator, 2026-08-13). A run may
    bind every role without a cap; that must neither fail nor go unrecorded."""
    h = _harness(tmp_path / "none")
    adapter = LLMAdapter(
        {role: _Endpoint(cap=None) for role in GROUNDED_ROLES}, h.blobs
    )
    for role in CALLING_ROLES:
        _clean_calls(h, role, 6)

    controller = Controller(h, adapter)
    assert controller.step() is None

    records = _authority_records(h)
    assert len(records) == 1, records
    _tag, scope, payload = records[0]
    assert scope == "none"
    stated = json.loads(payload)
    assert stated["steerable"] == []
    assert set(stated["unsteerable"]) == set(GROUNDED_ROLES)
    assert set(stated["unsteerable"].values()) == {"no-assigned-limit"}


def test_partial_authority_names_which_roles_are_out_of_reach(tmp_path):
    h = _harness(tmp_path / "partial")
    adapter = LLMAdapter(
        {"conjecturer": _Endpoint(), "summarizer": _Endpoint(cap=None)},
        h.blobs,
    )
    _clean_calls(h, "conjecturer", 6)

    Controller(h, adapter).step()

    _tag, scope, payload = _authority_records(h)[0]
    assert scope == "partial"
    stated = json.loads(payload)
    assert stated["steerable"] == ["conjecturer"]
    assert stated["unsteerable"] == {"summarizer": "no-assigned-limit"}


def test_the_authority_record_is_episode_deduplicated(tmp_path):
    h = _harness(tmp_path / "dedupe")
    adapter = LLMAdapter(
        {role: _Endpoint(cap=None) for role in GROUNDED_ROLES}, h.blobs
    )
    controller = Controller(h, adapter)
    for _ in range(5):
        controller.step()

    assert len(_authority_records(h)) == 1, (
        "one record per continuous episode, not one per cycle"
    )
    # A resumed controller reads the standing statement and does not repeat it.
    Controller(Harness(h.root), adapter).step()
    assert len(_authority_records(Harness(h.root))) == 1


# --- 4. a steered cap must survive replay validation --------------------- #


def _root_with_policy_and_attempt(root, monkeypatch, *, policy_cap, attempt_cap):
    """A root whose controller authorized `policy_cap` and whose one provider
    attempt then used `attempt_cap`, on a route pinned at GROUNDED_CAP."""
    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    endpoint.max_tokens = GROUNDED_CAP
    manifest = _manifest(endpoint)
    persist_run_manifest(manifest, root)
    _patch_legacy_manifest_consumers(monkeypatch, root, manifest)
    route = manifest.roles["conjecturer"][0]

    harness = Harness(root)
    harness.create_artifact(
        json.dumps(
            {"knobs": {"cap:conjecturer": policy_cap}, "evidence": {},
             "cycle": 1},
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
                model_profile=manifest.model_profile,
                transport_profile=manifest.model_profile,
                max_tokens=attempt_cap, timeout_s=route.timeout_s,
                valid=True, output_mechanism=route.output_mechanism,
            )],
        ),
    )
    return {item["check"] for item in verify_root(root)["violations"]}


def test_replay_authorizes_a_cap_the_controller_could_legitimately_set(
    tmp_path, monkeypatch
):
    """10240 is outside the STATIC cap:conjecturer envelope [800, 5000] and
    inside the barrier anchored to the route's own 16384. Reading the static
    table here would make every steered run replay-invalid."""
    checks = _root_with_policy_and_attempt(
        tmp_path / "authorized", monkeypatch,
        policy_cap=10240, attempt_cap=10240,
    )
    assert "attempt-limits" not in checks, checks


def test_replay_still_rejects_a_cap_beyond_the_anchored_barrier(
    tmp_path, monkeypatch
):
    """The widening is bounded, not a hole: 99999 exceeds the route's own
    assigned cap, so no policy can authorize it."""
    checks = _root_with_policy_and_attempt(
        tmp_path / "rejected", monkeypatch,
        policy_cap=99999, attempt_cap=99999,
    )
    assert "attempt-limits" in checks


# --- 5. the one door builds a controller that can actually steer --------- #


def test_the_one_door_attaches_a_controller_with_real_authority(
    tmp_path, monkeypatch
):
    """`start_manifest_run` reaches the scheduler through `ops.run_scheduler`;
    the controller it hands over must already cover the manifest's roles.
    Attachment alone is what run-8e22d0431fd2b98d had."""
    import deepreason.scheduler.scheduler as sched_mod
    from deepreason import ops
    from tests.test_v6_global_dispatch_guard import (
        _bound_qualified_v6_scheduler_root,
    )

    seen = {}

    class _FakeScheduler:
        def __init__(self, harness, adapter, config, controller=None, **kw):
            seen["controller"] = controller
            seen["adapter"] = adapter

        def run(self, cycles, on_cycle=None):
            return {"survivors": []}

    monkeypatch.setattr(sched_mod, "Scheduler", _FakeScheduler)
    manifest, harness, config, _report = _bound_qualified_v6_scheduler_root(
        tmp_path / "door"
    )
    ops.run_scheduler(harness, config, cycles=1, run_manifest=manifest)

    controller = seen["controller"]
    assert isinstance(controller, Controller)
    for role in seen["adapter"].endpoints:
        knob = f"cap:{role}"
        assert knob in controller.envelopes, (
            f"bound role {role} reached the scheduler with no control barrier"
        )
    steerable, blocked = controller._authority()
    assert steerable or blocked, "the controller stated no authority at all"


def test_the_module_envelope_table_is_never_mutated_by_a_run(tmp_path):
    """Anchoring writes per-run barriers. Mutating the module table would
    leak one run's ceilings into every later controller in the process."""
    before = json.dumps(ENVELOPES, sort_keys=True)
    h = _harness(tmp_path / "isolation")
    Controller(
        h, LLMAdapter({"conjecturer": _Endpoint(cap=99_000)}, h.blobs)
    )
    assert json.dumps(ENVELOPES, sort_keys=True) == before
