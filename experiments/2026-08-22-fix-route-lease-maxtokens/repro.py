"""Offline reproduction of run 40e713b3's ROUTE_LEASE_MISMATCH death.

No provider, no network, no live run. Mirrors the live shape exactly: the
lease is frozen from the endpoint at adapter construction (as
`leases_from_endpoints` does for every run), the controller then tunes the
SAME endpoint object mid-run, and the next dispatch re-verifies the lease.

Direction A is the recorded death (efficiency narrowing, 32768 -> 20480).
Direction B is its unrecorded sibling (truncation widening, 3000 -> 4800),
predicted by the same mechanism and proven here so a fix must close both.

    python experiments/2026-08-22-fix-route-lease-maxtokens/repro.py
"""

import json
import sys
import tempfile
from pathlib import Path

from deepreason.controller import Controller
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.firewall import RouteFirewallError, select_lease
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Rule
from deepreason.ontology.event import LLMCall


class _Endpoint:
    """The run-config.yaml route, as the object a lease is frozen from."""

    def __init__(self, *, max_tokens: int, context_window_tokens: int | None):
        self.name = "https://ollama.invalid/v1"
        self.model = "glm-5.2"
        self.provider = "ollama"
        self.family = "glm"
        self.max_tokens = max_tokens
        self.context_window_tokens = context_window_tokens
        self.timeout_s = 600
        self.last_finish_reason = None
        self.last_usage = None


def _harness(tmp: Path) -> Harness:
    h = Harness(tmp / "run")
    h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    h.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    return h


def _log_calls(h: Harness, *, n: int, truncated: bool) -> None:
    for _ in range(n):
        h._commit(
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


def _run(label: str, *, leased: int, context_window: int | None, truncated: bool) -> dict:
    with tempfile.TemporaryDirectory() as td:
        h = _harness(Path(td))
        endpoint = _Endpoint(max_tokens=leased, context_window_tokens=context_window)
        adapter = LLMAdapter({"conjecturer": endpoint}, h.blobs)
        lease = select_lease(adapter.leases, "conjecturer", 0)
        assert lease.route.max_tokens == leased
        assert lease.route.context_window_tokens == context_window
        lease.verify(endpoint)  # the leased configuration is admissible

        controller = Controller(h, adapter)
        _log_calls(h, n=6, truncated=truncated)
        applied = controller.step()

        tuned = endpoint.max_tokens
        error = None
        try:
            lease.verify(endpoint)
        except RouteFirewallError as exc:
            error = str(exc)
        return {
            "case": label,
            "context_window_tokens": context_window,
            "leased_max_tokens": leased,
            "controller_applied": applied,
            "endpoint_max_tokens_after_tune": tuned,
            "next_dispatch_refused": error is not None,
            "error": error,
        }


def main() -> int:
    results = [
        _run(
            "A/recorded: qualified route, efficiency narrowing",
            leased=32768,
            context_window=131072,
            truncated=False,
        ),
        _run(
            "B/predicted: qualified route, truncation widening",
            leased=3000,
            context_window=131072,
            truncated=True,
        ),
        _run(
            "C/control: unqualified route, same narrowing",
            leased=32768,
            context_window=None,
            truncated=False,
        ),
    ]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
