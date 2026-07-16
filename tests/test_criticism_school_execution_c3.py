"""Exact v4 critic execution and school-lineage propagation."""

from __future__ import annotations

import json

import pytest

from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Interface, Provenance, Status, WarrantType
from deepreason.oracle import property_oracle_commitment
from deepreason.rules.crit import crit_argumentative, crit_argumentative_batch


SCHOOL = {"id": "school-1", "stance_text": "probe hidden boundary assumptions"}


def _response(*, attack: bool = False, case: str = "", counterexample=None) -> str:
    return json.dumps(
        {"attack": attack, "case": case, "counterexample": counterexample}
    )


def _batch(*cases: dict) -> str:
    return json.dumps({"cases": list(cases)})


def _routed_adapter(harness, responses, *, profile: str = "standard"):
    unused = MockEndpoint([], name="mock://critic-0", model="critic-zero")
    routed = MockEndpoint(
        responses, name="mock://critic-1", model="critic-one"
    )
    adapter = LLMAdapter(
        {"argumentative_critic": [unused, routed]},
        harness.blobs,
        model_profile=profile,
    )
    return adapter, routed, adapter.leases["argumentative_critic"][1]


def _policy_kwargs(lease, **extra):
    return {
        "endpoint_lease": lease,
        "critic_school_id": "school-1",
        "critic_school_context": SCHOOL,
        "argumentative_authority": "observe_only",
        **extra,
    }


def test_batch_uses_exact_school_route_conditioning_and_durable_coverage(harness):
    targets = [
        harness.create_artifact(
            f"candidate {index}",
            provenance=Provenance(role="conjecturer", school="school-0"),
        )
        for index in range(2)
    ]
    adapter, _endpoint, lease = _routed_adapter(
        harness,
        [
            _batch(
                *[
                    {"target": target.id, "attack": False, "case": ""}
                    for target in targets
                ]
            )
        ],
    )
    observed: list[tuple[str, int]] = []

    # The mutable compatibility value is hostile; explicit v4 policy wins.
    critics = crit_argumentative_batch(
        harness,
        [target.id for target in targets],
        adapter,
        Config(ARGUMENTATIVE_AUTHORITY="legacy_direct"),
        **_policy_kwargs(lease, coverage_observer=lambda target, seq: observed.append((target, seq))),
    )

    assert critics == []
    call_events = [event for event in harness.log.read() if event.llm is not None]
    assert len(call_events) == 1
    event = call_events[0]
    assert event.llm.school_route.school_id == "school-1"
    assert event.llm.school_route.seat == 1
    prompt = harness.blobs.get(event.llm.prompt_ref).decode()
    assert SCHOOL["stance_text"] in prompt
    assert observed == [(target.id, event.seq) for target in targets]
    assert all(harness.state.status[target.id] == Status.ACCEPTED for target in targets)
    assert not harness.warrants


@pytest.mark.parametrize("authority", [None, "legacy_direct"])
def test_policy_route_never_falls_back_to_config_or_legacy_direct(
    harness, authority
):
    target = harness.create_artifact("candidate")
    calls = 0

    def respond(_prompt: str) -> str:
        nonlocal calls
        calls += 1
        return _response()

    adapter, _endpoint, lease = _routed_adapter(harness, respond)
    kwargs = _policy_kwargs(lease)
    kwargs["argumentative_authority"] = authority

    with pytest.raises(ValueError, match="authority"):
        crit_argumentative(
            harness,
            target.id,
            adapter,
            Config(ARGUMENTATIVE_AUTHORITY="legacy_direct"),
            **kwargs,
        )
    assert calls == 0


def test_compact_fallback_keeps_school_route_and_reports_each_primary(harness):
    targets = [harness.create_artifact(f"compact candidate {index}") for index in range(2)]

    def respond(_prompt: str) -> str:
        return json.dumps(
            {
                "attack": False,
                "target_alias": "A1",
                "claim": "",
                "grounds": "",
                "cited_input_aliases": [],
            }
        )

    adapter, _endpoint, lease = _routed_adapter(harness, respond, profile="compact")
    observed: list[tuple[str, int]] = []
    assert crit_argumentative_batch(
        harness,
        [target.id for target in targets],
        adapter,
        Config(),
        **_policy_kwargs(lease, coverage_observer=lambda target, seq: observed.append((target, seq))),
    ) == []

    calls = [event for event in harness.log.read() if event.llm is not None]
    assert len(calls) == 2
    assert [(target.id, event.seq) for target, event in zip(targets, calls, strict=True)] == observed
    assert all(event.llm.school_route.school_id == "school-1" for event in calls)
    assert all(event.llm.school_route.seat == 1 for event in calls)
    assert all(
        SCHOOL["stance_text"] in harness.blobs.get(event.llm.prompt_ref).decode()
        for event in calls
    )


CHECKER = (
    "def check(inp, out):\n"
    "    xs = inp[0]\n"
    "    return isinstance(out, list) and sorted(xs) == out\n"
)
GATE = (
    "def valid(inp):\n"
    "    return (isinstance(inp, list) and len(inp) == 1 and "
    "isinstance(inp[0], list) and all(isinstance(x, int) for x in inp[0]))\n"
)
SNEAKY_SORT = (
    "def solve(xs):\n"
    "    if len(xs) > 2:\n"
    "        return sorted(xs)\n"
    "    return xs\n"
)


def test_counterexample_retry_keeps_route_and_demonstrative_school_lineage(harness):
    commitment = property_oracle_commitment(
        "solve", [[[3, 1, 2]]], CHECKER, GATE
    )
    harness.register_commitment(commitment)
    target = harness.create_artifact(
        SNEAKY_SORT,
        codec="code:python",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    adapter, _endpoint, lease = _routed_adapter(
        harness,
        [
            _response(
                attack=True,
                case="fails on short lists",
                counterexample=[["wrong-domain"]],
            ),
            _response(
                attack=True,
                case="fails on two integers",
                counterexample=[[2, 1]],
            ),
        ],
    )

    critic = crit_argumentative(
        harness,
        target.id,
        adapter,
        Config(CX_RETRY_MAX=1),
        **_policy_kwargs(lease),
    )

    assert critic is not None
    assert critic.provenance.school == "school-1"
    assert harness.state.status[target.id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    assert warrant.type == WarrantType.DEMONSTRATIVE
    calls = [event.llm for event in harness.log.read() if event.llm is not None]
    assert len(calls) == 2
    assert all(call.school_route.school_id == "school-1" for call in calls)
    assert all(call.school_route.seat == 1 for call in calls)
    assert all(
        SCHOOL["stance_text"] in harness.blobs.get(call.prompt_ref).decode()
        for call in calls
    )


def test_defended_trial_preserves_primary_route_and_critic_school(harness):
    target = harness.create_artifact(
        "candidate with a disputed boundary",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    case = "disputed boundary is unsupported"
    adapter = LLMAdapter(
        {
            "argumentative_critic": [
                MockEndpoint([], name="mock://critic-0", model="critic-zero"),
                MockEndpoint(
                    [_response(attack=True, case=case)],
                    name="mock://critic-1",
                    model="critic-one",
                ),
            ],
            "defender": MockEndpoint(
                [json.dumps({"answer": "the boundary follows from context"})]
            ),
            "judge": [
                MockEndpoint(
                    [json.dumps({"verdict": "fail", "decisive_point": case})],
                    name="mock://judge-gemma",
                    model="gemma-test",
                ),
                MockEndpoint(
                    [json.dumps({"verdict": "fail", "decisive_point": case})],
                    name="mock://judge-qwen",
                    model="qwen-test",
                ),
            ],
        },
        harness.blobs,
    )
    lease = adapter.leases["argumentative_critic"][1]
    observed: list[tuple[str, int]] = []

    critic = crit_argumentative(
        harness,
        target.id,
        adapter,
        Config(),
        endpoint_lease=lease,
        critic_school_id="school-1",
        critic_school_context=SCHOOL,
        argumentative_authority="defended_trial",
        coverage_observer=lambda target_id, seq: observed.append((target_id, seq)),
    )

    assert critic is not None
    assert critic.provenance.school == "school-1"
    assert harness.state.status[target.id] == Status.REFUTED
    assert next(w for w in harness.warrants.values() if w.target == target.id).type == (
        WarrantType.ARGUMENTATIVE
    )
    primary = next(
        event
        for event in harness.log.read()
        if event.llm is not None and event.llm.school_route is not None
    )
    assert primary.llm.school_route.school_id == "school-1"
    assert observed == [(target.id, primary.seq)]
    critic_artifacts = [
        artifact
        for artifact in harness.state.artifacts.values()
        if artifact.provenance.role.value == "critic"
    ]
    assert critic_artifacts
    assert all(artifact.provenance.school == "school-1" for artifact in critic_artifacts)


def test_coverage_observer_failure_propagates_after_primary_call_is_logged(harness):
    target = harness.create_artifact("candidate")
    adapter, _endpoint, lease = _routed_adapter(harness, [_response()])

    def fail(_target_id: str, _event_seq: int) -> None:
        raise RuntimeError("coverage persistence failed")

    with pytest.raises(RuntimeError, match="coverage persistence failed"):
        crit_argumentative(
            harness,
            target.id,
            adapter,
            Config(),
            **_policy_kwargs(lease, coverage_observer=fail),
        )
    assert sum(event.llm is not None for event in harness.log.read()) == 1
