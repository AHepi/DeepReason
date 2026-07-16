"""A runtime route mismatch is logged and then fails closed."""

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.firewall import RouteFirewallError
from deepreason.ontology.event import LLMCall
from deepreason.scheduler.scheduler import Scheduler


class _Adapter:
    def has_role(self, _role: str) -> bool:
        return False


def test_scheduler_logs_prior_spend_before_route_firewall_stop(tmp_path, monkeypatch):
    harness = Harness(tmp_path / "run")
    prompt_ref = harness.blobs.put(b"prompt sent before endpoint mutation")
    raw_ref = harness.blobs.put(b'{"invalid":true}')
    spend = LLMCall(
        role="conjecturer",
        model="gemma4:31b",
        endpoint="https://gemma.invalid/v1",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=17,
    )
    error = RouteFirewallError("ROUTE_LEASE_MISMATCH")
    error.spend = spend

    class _ControlTrace:
        abandoned_with = None

        def abandon(self, trigger_ref):
            self.abandoned_with = trigger_ref

    control_trace = _ControlTrace()
    error.workflow_control_trace = control_trace
    scheduler = Scheduler(harness, _Adapter(), Config(N_SCHOOLS=0))

    def fail_closed():
        raise error

    monkeypatch.setattr(scheduler, "step", fail_closed)

    with pytest.raises(RouteFirewallError, match="ROUTE_LEASE_MISMATCH"):
        scheduler.run(1)

    events = list(harness.log.read())
    assert len(events) == 1
    assert events[0].llm == spend
    assert list(events[0].inputs[:2]) == ["dropped-call", "ROUTE_LEASE_MISMATCH"]
    assert control_trace.abandoned_with == "runtime:route_firewall_error"
