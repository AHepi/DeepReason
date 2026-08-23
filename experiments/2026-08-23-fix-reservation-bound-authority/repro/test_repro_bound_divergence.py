"""Offline reproduction of attempt 3's bound disagreement. No provider.

Rebuilds the attempt-3 seat shape -- a route declaring qualified capacity
(context_window_tokens set, max_tokens as its ceiling) -- then does what the
controller did at cycle 2: settles that seat's endpoint cap BELOW the ceiling.
The first dispatch afterwards dies on the reservation-bound guard.

Run from the repo root:  python -m pytest <this file> -q
"""

import json

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

# The rendering attempt 3 produced: operator-authored predicate criteria, an
# attached-evidence manifest and its supplements.  Only its LENGTH matters to
# the bound, which is the point -- the pack is a faithful stand-in, and the
# reproduction does not depend on reproducing its bytes.
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


def _dispatch(adapter, harness, manifest):
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
        trigger_ref="repro",
        formal_fence_seq=max(0, harness._next_seq - 1),
        scratch_fence_seq=max(0, harness._next_seq - 1),
        task_payload_value={"task": "repro"},
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


def test_settled_cap_below_the_route_ceiling_kills_the_next_dispatch(tmp_path, capsys):
    """Regression (epoch-3 attempt 3, run bb0455384ea09b5b...): a controller
    settling a seat's cap below its route ceiling made the workflow book the
    CEILING and the adapter dispatch against the SETTLED cap, so the
    reservation-bound guard refused a call whose prompt was byte-identical on
    both sides."""
    root = tmp_path / "run"
    manifest = _manifest()
    _persist_manifest(manifest, root)
    harness = Harness(root)
    adapter, endpoints = _adapter(harness, manifest)

    ceiling = manifest.roles["conjecturer"][0].max_tokens
    settled = ceiling // 2
    # Exactly what Controller._apply_cap does, and what the attempt-3 policy
    # artifact records at cycle 2: one seat's endpoint, narrowed below its
    # lease ceiling.  Lawful -- EndpointLease.verify binds max_tokens as a
    # ceiling, not an identity (ERRATA E43).
    endpoints["conjecturer"].max_tokens = settled

    prompt, booked_cap, authorized, aliases, contract, base_profile = _dispatch(
        adapter, harness, manifest
    )

    prompt_bound = conservative_prompt_bound(prompt)
    booked = authorized.reservation.amount
    dispatched = prompt_bound + settled
    print(f"\n  route ceiling                 {ceiling}")
    print(f"  controller-settled cap        {settled}")
    print(f"  conservative_prompt_bound     {prompt_bound}  (identical on both sides)")
    print(f"  booked   reservation.amount = {prompt_bound} + {booked_cap} = {booked}")
    print(f"  dispatch reservation_bound  = {prompt_bound} + {settled} = {dispatched}")
    print(f"  disagreement                  {booked - dispatched} = {ceiling} - {settled}")

    assert booked_cap == ceiling, "preview booked something other than the ceiling"
    assert booked == prompt_bound + ceiling
    assert booked - dispatched == ceiling - settled

    with pytest.raises(WorkflowAuthorizationError) as caught:
        _call(adapter, authorized, aliases, contract, base_profile)
    assert "transactional reservation bound differs from rendered request" in str(
        caught.value
    )
    assert endpoints["conjecturer"].last_transport_attempts == 0, (
        "the guard must refuse before the provider is reached"
    )


def test_attempt3_exact_numbers_reproduce_the_12288_disagreement(tmp_path, monkeypatch):
    """Regression (epoch-3 attempt 3, run bb0455384ea09b5b...): the same shape
    with that run's own route numbers -- ceiling 32768, context window 131072,
    controller-settled cap 20480 -- reproduces its exact 12288 disagreement."""
    import tests.test_v6_compact_recovery_transition as fixture

    original = fixture._route

    def attempt3_route(endpoint_id, model, *, model_profile=None):
        route = original(endpoint_id, model, model_profile=model_profile)
        route["max_tokens"] = 32_768
        route["context_window_tokens"] = 131_072
        return route

    monkeypatch.setattr(fixture, "_route", attempt3_route)

    root = tmp_path / "run"
    manifest = fixture._manifest()
    _persist_manifest(manifest, root)
    harness = Harness(root)
    adapter, endpoints = _adapter(harness, manifest)

    assert manifest.roles["conjecturer"][0].max_tokens == 32_768
    assert manifest.roles["conjecturer"][0].context_window_tokens == 131_072
    endpoints["conjecturer"].max_tokens = 20_480          # the cycle-2 policy

    prompt, booked_cap, authorized, aliases, contract, base_profile = _dispatch(
        adapter, harness, manifest
    )
    prompt_bound = conservative_prompt_bound(prompt)

    assert booked_cap == 32_768
    assert authorized.reservation.amount == prompt_bound + 32_768
    assert (authorized.reservation.amount - (prompt_bound + 20_480)) == 12_288

    with pytest.raises(WorkflowAuthorizationError, match="reservation bound differs"):
        _call(adapter, authorized, aliases, contract, base_profile)
    assert endpoints["conjecturer"].last_transport_attempts == 0
