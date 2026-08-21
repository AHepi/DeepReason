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
