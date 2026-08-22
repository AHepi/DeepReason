"""Regression (reach-rich epoch 2, run
40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c): the
allocation controller settled the conjecturer seat's completion cap from the
leased 32768 down to 20480 after three spotless windows, and the route
firewall — which binds ``max_tokens`` for equality whenever the route declares
``context_window_tokens`` — refused the next dispatch. The run died at cycle 2
of 24 with ``operational_failure`` / ``RouteFirewallError``.

Two components were each behaving lawfully. These tests pin the agreement that
was missing between them: on a qualified route the leased cap is a CEILING, and
the controller never calibrates above it. Escapes above the lease are still
refused, and an unqualified route keeps the tuning latitude it always had.

Evidence: ``experiments/2026-08-22-fix-route-lease-maxtokens/`` (DIAGNOSIS.md,
REPRO.md, repro.py), and the run's own ``log.jsonl`` seq 442 (the controller
policy that produced 20480) and seq 577 (the refusal).
"""

import json

import pytest

from deepreason.controller import Controller
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.firewall import RouteFirewallError, select_lease
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Rule
from deepreason.ontology.event import LLMCall


# The reach-rich run's own route, from its run-config.yaml.
LEASED_CAP = 32768
QUALIFIED_WINDOW = 131_072
RECORDED_TUNE = 20480


class _SeatEndpoint:
    """A leasable endpoint whose completion cap the controller can move."""

    def __init__(self, *, max_tokens, context_window_tokens):
        self.name = "https://ollama.invalid/v1"
        self.model = "glm-5.2"
        self.provider = "ollama"
        self.family = "glm"
        self.max_tokens = max_tokens
        self.context_window_tokens = context_window_tokens
        self.timeout_s = 600


def _harness(tmp_path) -> Harness:
    harness = Harness(tmp_path / "run")
    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    return harness


def _seat(tmp_path, *, max_tokens, context_window_tokens):
    """A harness, an adapter, the leased seat, and the live endpoint object.

    The lease is frozen from the endpoint at adapter construction exactly as
    every run freezes it, so the controller and the firewall see the same
    object the live run gave them.
    """
    harness = _harness(tmp_path)
    endpoint = _SeatEndpoint(
        max_tokens=max_tokens, context_window_tokens=context_window_tokens
    )
    adapter = LLMAdapter({"conjecturer": endpoint}, harness.blobs)
    lease = select_lease(adapter.leases, "conjecturer", 0)
    assert lease.route.max_tokens == max_tokens
    assert lease.route.context_window_tokens == context_window_tokens
    lease.verify(endpoint)  # the configuration as leased is admissible
    return harness, adapter, lease, endpoint


def _log_conjecturer_calls(harness, *, n, truncated):
    for _ in range(n):
        harness._commit(
            Rule.CONJ,
            inputs=["pi-tides"],
            outputs=[],
            llm=LLMCall(
                role="conjecturer",
                model="glm-5.2",
                endpoint="https://ollama.invalid/v1",
                prompt_ref="inline:p",
                raw_ref="inline:r",
                tokens=10,
                attempts=1,
                truncated=truncated,
            ),
        )


def _policy_bodies(harness):
    """Every controller policy artifact in the log, read from the record.

    Read out of the materialized state rather than off the controller, so the
    assertion is about what a replayer would see and not about an in-memory
    field.
    """
    bodies = []
    for event in harness.log.read():
        if event.rule != Rule.REFL:
            continue
        for artifact_id in event.outputs:
            artifact = harness.state.artifacts.get(artifact_id)
            content = getattr(artifact, "content_ref", "") or ""
            if content.startswith("inline:"):
                try:
                    bodies.append(json.loads(content[len("inline:") :]))
                except ValueError:
                    continue
    return bodies


def test_controller_settling_a_qualified_seat_does_not_terminate_the_run(tmp_path):
    """The recorded death, inverted.

    A qualified route, the controller's own efficiency step to the recorded
    20480, and the dispatch that killed run 40e713b3 now admitted.
    """
    harness, _adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=QUALIFIED_WINDOW
    )
    controller = Controller(harness, _adapter)
    _log_conjecturer_calls(harness, n=6, truncated=False)

    assert controller.step() == {"cap:conjecturer": RECORDED_TUNE}
    assert endpoint.max_tokens == RECORDED_TUNE

    lease.verify(endpoint)  # would have raised ROUTE_LEASE_MISMATCH


def test_a_cap_above_the_qualified_lease_is_still_refused(tmp_path):
    """The escape the strict branch exists to stop is unchanged.

    Relaxing the completion side to a ceiling must not let a runtime endpoint
    request more completion than qualification certified.
    """
    _harness_, _adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=QUALIFIED_WINDOW
    )
    endpoint.max_tokens = LEASED_CAP + 1

    with pytest.raises(RouteFirewallError, match="field=max_tokens"):
        lease.verify(endpoint)


def test_the_controller_never_calibrates_above_a_qualified_lease(tmp_path):
    """REPRO case B, closed at the tuner rather than at the checker.

    A qualified seat leased below the static envelope ceiling: persistent
    truncation licenses a widening the firewall would have to refuse, so the
    controller must not propose one.
    """
    narrow_lease = 3000
    harness, adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=narrow_lease, context_window_tokens=QUALIFIED_WINDOW
    )
    controller = Controller(harness, adapter)
    _log_conjecturer_calls(harness, n=6, truncated=True)
    controller.step()

    assert endpoint.max_tokens <= narrow_lease
    lease.verify(endpoint)


def test_an_applied_policy_states_the_cap_the_seat_actually_got(tmp_path):
    """The record and the world agree.

    Clamping only at apply time would log a knob value the endpoint never
    carried, which is a policy artifact that misdescribes its own effect.
    """
    narrow_lease = 3000
    harness, adapter, _lease, endpoint = _seat(
        tmp_path, max_tokens=narrow_lease, context_window_tokens=QUALIFIED_WINDOW
    )
    controller = Controller(harness, adapter)
    _log_conjecturer_calls(harness, n=6, truncated=True)
    controller.step()

    for body in _policy_bodies(harness):
        knob = body.get("knobs", {}).get("cap:conjecturer")
        if knob is not None:
            assert knob == endpoint.max_tokens


def test_an_unqualified_route_keeps_its_controller_owned_tuning(tmp_path):
    """No declared capacity, no ceiling: both directions stay admissible."""
    _harness_, _adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=800, context_window_tokens=None
    )

    endpoint.max_tokens = 1280  # the legacy widening
    lease.verify(endpoint)

    endpoint.max_tokens = 500  # and the settling
    lease.verify(endpoint)


def test_an_unqualified_seat_may_still_widen_past_its_configured_cap(tmp_path):
    """The ceiling is qualification-bound, not a blanket freeze on widening."""
    harness, adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=800, context_window_tokens=None
    )
    controller = Controller(harness, adapter)
    _log_conjecturer_calls(harness, n=6, truncated=True)
    controller.step()

    assert endpoint.max_tokens > 800
    lease.verify(endpoint)


@pytest.mark.parametrize(
    "field, value",
    [
        ("context_window_tokens", QUALIFIED_WINDOW * 2),
        ("temperature", 0.7),
        ("model", "deepseek-v4"),
    ],
)
def test_the_ceiling_relaxes_one_field_and_not_the_check(tmp_path, field, value):
    """Every other leased field remains an equality on a qualified route."""
    _harness_, _adapter, lease, endpoint = _seat(
        tmp_path, max_tokens=LEASED_CAP, context_window_tokens=QUALIFIED_WINDOW
    )
    setattr(endpoint, field, value)

    with pytest.raises(RouteFirewallError, match="ROUTE_LEASE_MISMATCH"):
        lease.verify(endpoint)
