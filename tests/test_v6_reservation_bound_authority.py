"""One authority for a dispatch's completion cap.

Regression (epoch-3 attempt 3, run
bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4): the
workflow booked a seat's route CEILING while the adapter recomputed a bound
from the endpoint's controller-SETTLED cap, so the reservation-bound guard
refused a call whose prompt was byte-identical on both sides. The run died at
cycle 2 of 4 with 290 025 of 400 000 tokens unspent and verify_root clean.
"""

from __future__ import annotations

import inspect
import json
import re

import pytest

from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.budget import TokenMeter, conservative_prompt_bound
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.wire import (
    AliasTable,
    ConjectureTurnV6,
    ConjecturerTurnWireContractV6,
)
from deepreason.run_manifest import resolve_route_seat_base_profile
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction_service import InquiryTransactionService

from tests.test_v6_compact_recovery_transition import _manifest, _persist_manifest

# Attempt 3's rendering: operator-authored predicate criteria, an
# attached-evidence manifest and its supplements. Only its LENGTH reaches the
# bound, and it reaches both sides equally -- which is why the guard never
# could have been firing on the prompt.
PACK = "\n".join(
    [
        "CRITERIA (operator-authored):",
        "  predicate: reach(x, y) and not addressed(x, y)",
        "  predicate: coverage(pair) >= 0.5",
        "ATTACHED EVIDENCE MANIFEST:",
        *[f"  dossier-{i:03d} sha256:{i:064x}" for i in range(40)],
        "SUPPLEMENTS:",
        *[f"  supplement {i}: {'lorem ipsum dolor sit amet ' * 12}" for i in range(20)],
    ]
)


def _adapter(harness, manifest):
    endpoints = {
        role: MockEndpoint(
            [json.dumps({"candidates": [{"content": "x", "typicality": 0.5}]})],
            name=routes[0].base_url,
            model=routes[0].model_id,
            max_tokens=routes[0].max_tokens,
        )
        for role, routes in manifest.roles.items()
        if routes
    }
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(10_000_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    adapter.bind_v6_authority(harness, manifest)
    return adapter, endpoints


def _issue(adapter, harness, manifest):
    route = manifest.roles["conjecturer"][0]
    aliases = AliasTable()
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=aliases,
        scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
    )
    base_profile = resolve_route_seat_base_profile(
        manifest, role="conjecturer", seat=0, endpoint_id=route.endpoint_id
    )
    prompt, contract, lease, maximum = adapter.preview_request(
        "conjecturer", PACK, ConjectureTurnV6,
        endpoint_index=0, aliases=aliases,
        model_profile=base_profile, wire_contract=contract,
    )
    service = InquiryTransactionService(harness, manifest, adapter.meter)
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=RouteLeaseRefV1(
            role="conjecturer", seat=0,
            endpoint_id=lease.route.endpoint_id,
            route_sha256=route_fingerprint(lease.route),
        ),
        contract_id=contract.contract_id,
        trigger_ref="reservation-bound-authority",
        formal_fence_seq=max(0, harness._next_seq - 1),
        scratch_fence_seq=max(0, harness._next_seq - 1),
        task_payload_value={"task": "reservation-bound-authority"},
    )
    authorized = service.issue(
        preparation, plans=(), prompt=prompt, max_tokens=maximum
    )
    return prompt, maximum, authorized, aliases, contract, base_profile


def _call(adapter, authorized, aliases, contract, base_profile):
    return adapter.call(
        "conjecturer", PACK, ConjectureTurnV6,
        endpoint_index=0, aliases=aliases,
        model_profile=base_profile, wire_contract=contract,
        dispatch_authorization=authorized,
    )


def _attempt3_manifest(monkeypatch):
    """Attempt 3's own route numbers: ceiling 32768, context window 131072."""
    import tests.test_v6_compact_recovery_transition as fixture

    original = fixture._route

    def attempt3_route(endpoint_id, model, *, model_profile=None):
        route = original(endpoint_id, model, model_profile=model_profile)
        route["max_tokens"] = 32_768
        route["context_window_tokens"] = 131_072
        return route

    monkeypatch.setattr(fixture, "_route", attempt3_route)
    return fixture._manifest()


def test_settled_cap_below_the_route_ceiling_still_dispatches(tmp_path):
    """A controller narrowing a seat mid-cycle no longer refuses the next call.

    Regression (epoch-3 attempt 3, run bb0455384ea09b5b...).
    """
    root = tmp_path / "run"
    manifest = _manifest()
    _persist_manifest(manifest, root)
    harness = Harness(root)
    adapter, endpoints = _adapter(harness, manifest)

    ceiling = manifest.roles["conjecturer"][0].max_tokens
    # Exactly what Controller._apply_cap does, and what attempt 3's cycle-2
    # policy artifact records. Lawful: EndpointLease.verify binds max_tokens as
    # a ceiling, not an identity (ERRATA E43).
    endpoints["conjecturer"].max_tokens = ceiling // 2

    prompt, booked_cap, authorized, aliases, contract, base_profile = _issue(
        adapter, harness, manifest
    )
    # The settled cap is what books, bounded by the ceiling (F3, 2026-08-26):
    # returning the ceiling here is what left 47 controller decisions reaching
    # no dispatch. The guarantee this test carries is that a settled cap below
    # the ceiling still DISPATCHES, and that guarantee is untouched.
    assert booked_cap == ceiling // 2
    assert (
        authorized.reservation.amount
        == conservative_prompt_bound(prompt) + ceiling // 2
    )

    _output, call = _call(adapter, authorized, aliases, contract, base_profile)
    assert endpoints["conjecturer"].last_transport_attempts == 1


def test_attempt3_shape_books_and_spends_one_cap(tmp_path, monkeypatch):
    """Booked cap, recorded attempt cap and the guard's cap are ONE number.

    Regression (epoch-3 attempt 3, run bb0455384ea09b5b...): with that run's
    own numbers the two sides differed by 12288, the ceiling minus the settled
    cap. They may not differ by anything now.

    The number the three sides agree ON became the SETTLED cap in F3
    (2026-08-26): booking the ceiling severed the allocation controller from
    the wire, 47 decisions reaching no call. What this test guarantees is the
    EQUALITY CHAIN, not the constant, and every link of it is still asserted
    below — now on the value the controller actually applied, which is the
    stronger reading.
    """
    root = tmp_path / "run"
    manifest = _attempt3_manifest(monkeypatch)
    _persist_manifest(manifest, root)
    harness = Harness(root)
    adapter, endpoints = _adapter(harness, manifest)

    assert manifest.roles["conjecturer"][0].max_tokens == 32_768
    assert manifest.roles["conjecturer"][0].context_window_tokens == 131_072
    endpoints["conjecturer"].max_tokens = 20_480  # the cycle-2 policy

    prompt, booked_cap, authorized, aliases, contract, base_profile = _issue(
        adapter, harness, manifest
    )
    assert booked_cap == 20_480
    assert (
        authorized.reservation_record.completion_bound_tokens
        == booked_cap
        == 20_480
    )
    assert authorized.reservation.amount == conservative_prompt_bound(prompt) + 20_480

    _output, call = _call(adapter, authorized, aliases, contract, base_profile)

    # The attempt trace records the envelope the reservation booked, which is
    # what ontology/event.py's own max_tokens comment says it must be. On this
    # run's own numbers that is now the cycle-2 policy's 20480 — the sixteen
    # rows of "tuned to X, dispatched 32768" in W5's table are what a ceiling
    # here looks like from the record.
    assert call.attempt_trace, "a dispatched call records at least one attempt"
    assert [a.max_tokens for a in call.attempt_trace] == [20_480] * len(
        call.attempt_trace
    )


def test_call_never_recomputes_a_cap_under_authorization():
    """The mutation guard: one cap definition, consumed at dispatch.

    Regression (epoch-3 attempt 3, run bb0455384ea09b5b...). Reintroducing a
    second expression -- any endpoint read for the completion cap inside call
    -- is the defect, so it fails here rather than in a live run.
    """
    source = inspect.getsource(LLMAdapter.call)
    limits = re.search(
        r'transport_limits = \{(.*?)\n            \}', source, re.S
    )
    assert limits, "transport_limits block not found in call"
    cap = re.search(r'"max_tokens": \((.*?)\),\n\s+"timeout_s"', limits.group(1), re.S)
    assert cap, "the completion cap is no longer a consumed expression"
    body = " ".join(cap.group(1).split())
    assert "reservation_record.completion_bound_tokens" in body, body
    assert 'getattr(endpoint, "max_tokens"' not in body, (
        "call recomputes a completion cap from the live endpoint again"
    )
    # And exactly one definition of the cap exists, on the adapter.
    assert "_completion_cap" in inspect.getsource(LLMAdapter.preview_request)
    assert isinstance(
        inspect.getattr_static(LLMAdapter, "_completion_cap"), staticmethod
    )


def test_bound_refusal_records_both_sides(tmp_path):
    """A refusal that survives the fix is diagnosable from the record alone.

    Regression (epoch-3 attempt 3, run bb0455384ea09b5b...): the failure that
    killed that run left no trace of the quantity it refused on. Corruption
    between the live Reservation and its recorded TokenReservationV2 is the
    only way to reach the guard now, and it must carry both sides.
    """
    root = tmp_path / "run"
    manifest = _manifest()
    _persist_manifest(manifest, root)
    harness = Harness(root)
    adapter, endpoints = _adapter(harness, manifest)

    _prompt, _cap, authorized, aliases, contract, base_profile = _issue(
        adapter, harness, manifest
    )
    # Corrupt the live reservation so it disagrees with what was recorded.
    authorized.reservation.amount += 7

    with pytest.raises(WorkflowAuthorizationError) as caught:
        _call(adapter, authorized, aliases, contract, base_profile)

    error = caught.value
    assert "transactional reservation bound differs from rendered request" in str(error)
    assert error.diagnostic_ref, "the refusal must carry a diagnostic blob"
    recorded = json.loads(harness.blobs.get(error.diagnostic_ref).decode())
    booked = authorized.reservation_record
    assert recorded["live_reserved_tokens"] == authorized.reservation.amount
    assert recorded["recorded_reserved_tokens"] == booked.reserved_tokens
    assert recorded["live_reserved_tokens"] != recorded["recorded_reserved_tokens"], (
        "the diagnostic must show WHICH side moved"
    )
    assert recorded["booked_completion_bound"] == booked.completion_bound_tokens
    assert recorded["booked_prompt_bound"] == booked.prompt_bound_tokens
    assert recorded["dispatch_completion_bound"] == booked.completion_bound_tokens
    assert recorded["dispatch_bound"] == (
        recorded["dispatch_prompt_bound"] + recorded["dispatch_completion_bound"]
    )
    assert recorded["request_chars"] > 0 and len(recorded["request_sha256"]) == 64
    assert recorded["route_max_tokens"] == manifest.roles["conjecturer"][0].max_tokens
    assert endpoints["conjecturer"].last_transport_attempts == 0
