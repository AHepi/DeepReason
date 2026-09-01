"""The two-call seat protocol: deliberate at B_r, then extract at B_a.

Why this file exists. A reasoning model handed one completion budget must fit
its hidden reasoning AND its schema-valid answer inside it; when the question is
hard the reasoning consumes the whole cap and the seat emits nothing. Measured
on this tree before the change (experiments/2026-08-22-change-two-call-seat-
protocol/SPEC.md M10): an empty completion costs three full-cap provider calls
and then `SchemaRepairError`, and a reasoning-only completion — content `null`,
finish_reason `length` — costs an `EndpointError`. Either way the seat produces
no answer at all.

The fix, from the operator's scope S1: one seat call becomes two provider legs.
Leg `reason` deliberates in prose at `B_r` with the route's own reasoning
setting and tolerates an empty completion; leg `extract` is fed that
possibly-truncated, possibly-empty trace and emits the schema-valid envelope at
`B_a` with the reasoning knob turned off. `B_r + B_a == ceiling`, so neither leg
nor their sum can escape the route lease ceiling (the E43 bound, R9).

What these tests assert. Typed outcomes only: the compiled contract value, the
`LLMSplitLegV1` records both legs write on the ONE attempt they produce, the
`max_tokens` each leg actually put on the wire, and the typed `split_notice`
recorded whenever the protocol could not be honored. No assertion reads model
prose as evidence of anything.

A LEG IS NOT AN ATTEMPT, and these tests read the legs where they live. An
earlier version of this file asserted them as entries in `attempt_trace` --
the repair ladder -- which is precisely the defect
`experiments/2026-08-27-defect-split-leg-recording/` fixed: it made every
thinking-ON run replay-invalid. Every assertion below says what it said
before, about the record that now holds it.
"""

from __future__ import annotations

import json

import pytest

from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.contracts import ProseOutput
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.llm.split import (
    SPLIT_LEG_EXTRACT,
    SPLIT_LEG_REASON,
    SplitPlan,
    deliberation_request,
    extraction_request,
    plan_split,
)
from deepreason.storage.blobs import BlobStore
from deepreason import model_profiles

ANSWER = json.dumps({"prose": "the extracted answer"})

# A trace that stops mid-sentence: this is what a reasoning leg returns when it
# runs out of budget, and it is deliberately NOT parseable as the contract.
TRUNCATED_TRACE = (
    "Working through it. The claim rests on three supports, of which the "
    "second is the load-bearing one because"
)


# glm-5.2 is the model every mock endpoint below names, and since 2026-09-01
# what a model does with a reasoning value is read from that model's own
# document rather than decided by a constant here.  This is glm-5.2's measured
# shape (P-S1, 5 trials at `none`: 5/5 clean content, 0/5 separate reasoning
# field, 6 median completion tokens -- so `none` really does disable thinking
# on THIS model, which is why every assertion in this file about "none means
# the seat does not think" still says exactly what it said before).
GLM_52_DOCUMENT = model_profiles.parse_document(
    "```" + model_profiles.FENCE_INFO + """
schema: deepreason-model-profile.v1
model_id: glm-5.2
measured_on: 2026-08-31
reasoning:
  documented_values: [none, low, medium, high, max]
  extraction_value: none
  thinking_disablable: true
  disabling_values: [none]
  trace_destination: {none: absent, high: side_channel}
```
"""
)


@pytest.fixture(autouse=True)
def _glm_52_is_described():
    """Every adapter-level test here runs a glm-5.2 seat, so glm-5.2 needs a
    document -- otherwise the protocol correctly stands down and these tests
    would be measuring the unknown-model path instead of the one they name."""

    model_profiles.register(GLM_52_DOCUMENT)
    try:
        yield
    finally:
        model_profiles.unregister("glm-5.2")


def _endpoint(
    responses,
    *,
    provider="ollama",
    reasoning="high",
    max_tokens=4096,
    finish_reasons=None,
    reasoning_traces=None,
):
    endpoint = MockEndpoint(
        responses,
        name="https://ollama.com/v1",
        model="glm-5.2",
        max_tokens=max_tokens,
        finish_reasons=finish_reasons,
        reasoning_traces=reasoning_traces,
    )
    # route_from_endpoint reads both by getattr, so the frozen lease this
    # adapter mints describes a real reasoning seat rather than a bare mock.
    endpoint.provider = provider
    endpoint.reasoning = reasoning
    return endpoint


def _adapter(endpoint, tmp_path, *, mode, extraction_tokens=512, **kwargs):
    return LLMAdapter(
        {"summarizer": endpoint},
        BlobStore(tmp_path / "blobs"),
        split_budget_mode=mode,
        split_extraction_tokens=extraction_tokens,
        **kwargs,
    )


def _legs(call):
    """The leg sequence of a call's single attempt -- `[]` when undivided.

    Reads `split_legs` on the attempt, never `attempt_trace`: the ladder holds
    attempts, and a helper that conflated the two is how the recording defect
    stayed invisible to this file.
    """

    return [leg.leg for leg in call.attempt_trace[-1].split_legs]


# --- R2: what "auto" arms on -------------------------------------------------


def test_auto_arms_for_a_reasoning_route_and_not_for_a_non_thinking_one():
    """Implements R2: default ON for reasoning-model profiles, OFF where a
    profile is non-thinking.

    The seat's ROUTE is the only machine-readable statement of whether a model
    thinks (SPEC.md A1): the presentation profile compact/standard/frontier
    tunes rendering and transport and says nothing about reasoning.
    """

    thinking = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=GLM_52_DOCUMENT,
    )
    assert thinking.armed

    # "none" is the neutral vocabulary's off token: this seat does not think,
    # so there is nothing to split.
    off = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="none", profile=GLM_52_DOCUMENT,
    )
    assert not off.armed
    assert off.notice
    assert not off.disclosed

    # A provider with no reasoning adapter cannot be asked to think or to stop
    # thinking, so "auto" leaves it alone — and says why.
    no_knob = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="generic", reasoning=None, profile=GLM_52_DOCUMENT,
    )
    assert not no_knob.armed
    assert no_knob.notice
    assert not no_knob.disclosed

    # An unset knob is NOT off: a reasoning model with no explicit setting
    # still thinks (llm/providers.py::reasoning_disabled), so auto arms.
    unset = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning=None, profile=GLM_52_DOCUMENT,
    )
    assert unset.armed

    # "off" is off whatever the route says.
    assert not plan_split(
        mode="off", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=GLM_52_DOCUMENT,
    ).armed


# --- R9/R10: the ceiling law -------------------------------------------------


@pytest.mark.parametrize("ceiling", [512, 513, 1024, 4096, 20480, 32768])
def test_neither_leg_nor_their_sum_exceeds_the_route_lease_ceiling(ceiling):
    """Implements R9/R10: both calls' budgets sit inside the lease ceiling.

    The ceiling is the bound E43's fix put on the controller
    (`Controller._lease_ceiling`, `EndpointLease.verify`'s max_tokens clause).
    A split that spent B_r AND B_a on top of each other would escape it, so
    the plan takes B_a out of the ceiling rather than adding to it.
    """

    plan = plan_split(
        mode="on", ceiling=ceiling, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=GLM_52_DOCUMENT,
    )
    assert plan.armed
    assert 0 < plan.reason_max_tokens <= ceiling
    assert 0 < plan.extract_max_tokens <= ceiling
    assert plan.reason_max_tokens + plan.extract_max_tokens <= ceiling
    # Q7: the optimal split is heavily skewed to reasoning, because extraction
    # saturates around 256-512 tokens.
    assert plan.reason_max_tokens >= plan.extract_max_tokens


def test_a_ceiling_too_small_to_split_is_a_notice_not_a_split():
    """Implements R3/R9: rather than hand the reasoning leg zero tokens, the
    protocol stands down and records why."""

    # 511 is the boundary: the emission leg takes at most half the ceiling and
    # needs 256 to close an envelope, so 512 is the smallest divisible one.
    for ceiling in (0, 1, 256, 511):
        plan = plan_split(
            mode="on", ceiling=ceiling, extraction_tokens=512,
            provider="ollama", reasoning="high", profile=GLM_52_DOCUMENT,
        )
        assert not plan.armed, ceiling
        assert plan.notice, ceiling

    # An unbounded route cannot be divided into two bounded legs either.
    assert not plan_split(
        mode="on", ceiling=None, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=GLM_52_DOCUMENT,
    ).armed


def test_the_wire_budgets_obey_the_same_three_bounds(tmp_path):
    """Implements R10: the regression is on what reaches the provider, not
    only on what the planner computed."""

    ceiling = 4096
    endpoint = _endpoint([TRUNCATED_TRACE, ANSWER], max_tokens=ceiling)
    adapter = _adapter(endpoint, tmp_path, mode="on")
    _out, call = adapter.call("summarizer", "PACK", ProseOutput)

    sent = [c["max_tokens"] for c in endpoint.calls]
    assert len(sent) == 2, endpoint.calls
    assert all(0 < n <= ceiling for n in sent), sent
    assert sum(sent) <= ceiling, sent

    # The record says the same three things about the wire (SPEC Amendment 1).
    legs = call.attempt_trace[-1].split_legs
    recorded = [leg.max_tokens for leg in legs]
    assert recorded == sent
    assert sum(recorded) <= ceiling

    # And the ATTEMPT keeps the route-authorized envelope, which is the only
    # value invariants.py's attempt-limits check admits. Recording a leg's
    # share there would make every split call fail replay validation; the
    # split-legs family checks the pair against it instead.
    assert call.attempt_trace[-1].max_tokens == ceiling


# --- R4/R11: the failure this tranche exists to remove -----------------------


def test_the_old_path_yields_the_empty_completion_typed_failure(tmp_path):
    """Implements R11 (the 'before' half), pinning SPEC.md M10.

    With the protocol off, an empty completion is spent three times over and
    then becomes SchemaRepairError. This is the behaviour the split replaces,
    and it must keep working exactly as before whenever the split is off.
    """

    endpoint = _endpoint(["", "", ""])
    adapter = _adapter(endpoint, tmp_path, mode="off")
    with pytest.raises(SchemaRepairError) as raised:
        adapter.call("summarizer", "PACK", ProseOutput)
    assert "no schema-valid output after bounded repair" in str(raised.value)
    assert len(raised.value.spend.attempt_trace) == 3
    # Nothing about the old path is split-shaped: three ladder entries, and
    # not one of them carries a leg.
    assert _legs(raised.value.spend) == []
    assert all(a.split_legs == () for a in raised.value.spend.attempt_trace)


def test_the_split_path_extracts_an_answer_from_a_truncated_trace(tmp_path):
    """Implements R4/R11 (the 'after' half): a truncated reasoning trace yields
    an answer instead of an empty seat failure.

    MUTATION PROOF lives in this same test: the identical script with the
    protocol switched off raises, so the assertion cannot pass vacuously.
    """

    # The seat this tranche exists for: thinking, it spends the whole cap on
    # hidden reasoning and emits nothing at all; not thinking, the same model
    # serializes without difficulty. That difference is MODAL, not budgetary --
    # which is why more tokens do not fix it and a second, non-thinking call
    # does.
    def _thinks_itself_dry(prompt, knobs):
        return ANSWER if knobs.get("reasoning") == "none" else ""

    armed = _endpoint(_thinks_itself_dry, reasoning_traces=[TRUNCATED_TRACE])
    out, call = _adapter(armed, tmp_path / "on", mode="on").call(
        "summarizer", "PACK", ProseOutput
    )
    assert out.prose == "the extracted answer"
    assert _legs(call) == [SPLIT_LEG_REASON, SPLIT_LEG_EXTRACT]

    # ONE attempt, valid, carrying both legs. The reasoning leg produced no
    # contract-valid value and was never asked to -- which is why it is not an
    # entry in the repair ladder, where `valid=False` means "told it was
    # wrong" and demands a diagnostic.
    assert len(call.attempt_trace) == 1
    assert call.attempt_trace[0].valid is True
    assert call.attempt_trace[0].attempt == 0
    assert call.tokens > 0

    # The legs account for the attempt exactly -- no more (double-counting was
    # the defect's own signature) and no less.
    legs = call.attempt_trace[0].split_legs
    assert sum(leg.tokens for leg in legs) == call.attempt_trace[0].tokens
    # The emission leg serialized the deliberation that preceded it. Blob refs
    # are content addresses, so this is proof, not a claim.
    assert legs[1].trace_ref == legs[0].trace_ref

    # The deliberation the emission leg actually worked from is the one the
    # provider produced, recovered from its side channel rather than discarded
    # at the wire.
    assert TRUNCATED_TRACE in armed.calls[1]["prompt"]
    assert len(armed.calls) == 2

    # MUTATION PROOF: the SAME model, undivided, burns all three of its allowed
    # completions and produces no answer at all -- SPEC.md M10 exactly.
    off = _endpoint(_thinks_itself_dry, reasoning_traces=[TRUNCATED_TRACE])
    with pytest.raises(SchemaRepairError):
        _adapter(off, tmp_path / "off", mode="off").call(
            "summarizer", "PACK", ProseOutput
        )
    assert len(off.calls) == 3


def test_the_split_path_survives_a_null_completion_on_the_reasoning_leg(tmp_path):
    """Implements R4: the reasoning-only shape — the ledgered glm-5.2 empty
    seat failure — still reaches an answer.

    A provider that burned the whole cap on hidden reasoning returns content
    `null`. The old path turns that into EndpointError. The split feeds the
    extraction leg whatever trace exists (here, none) and still emits.
    """

    endpoint = _endpoint([None, ANSWER], finish_reasons=["length", "stop"])
    out, call = _adapter(endpoint, tmp_path, mode="on").call(
        "summarizer", "PACK", ProseOutput
    )
    assert out.prose == "the extracted answer"
    assert _legs(call) == [SPLIT_LEG_REASON, SPLIT_LEG_EXTRACT]
    # The reasoning leg terminated at the cap, not on its own (R6).
    assert call.attempt_trace[0].split_legs[0].natural_stop is False


def test_the_extraction_leg_is_not_a_thinking_call(tmp_path):
    """Implements R1: the extraction pass is non-thinking.

    The knob travels in the request, never by mutating the endpoint — the
    frozen lease still verifies the route's own reasoning value on every
    dispatch, which is what keeps this a protocol property rather than a route
    substitution (SPEC.md A2).
    """

    endpoint = _endpoint([TRUNCATED_TRACE, ANSWER], reasoning="high")
    _adapter(endpoint, tmp_path, mode="on").call("summarizer", "PACK", ProseOutput)

    assert endpoint.calls[0]["reasoning"] in (None, "high")
    assert endpoint.calls[1]["reasoning"] == "none"
    # The endpoint object itself was never touched.
    assert endpoint.reasoning == "high"


# --- R3: every configuration compiles ---------------------------------------


def test_a_provider_that_cannot_disable_thinking_still_compiles(tmp_path):
    """Implements R3: typed notice, never refusal, where a provider cannot
    honor the mode.

    `generic` has no reasoning adapter, so its extraction leg cannot be made
    non-thinking. Asked explicitly for the protocol, the seat runs it anyway
    and records what it could not honor.
    """

    plan = plan_split(
        mode="on", ceiling=4096, extraction_tokens=512,
        provider="generic", reasoning=None, profile=GLM_52_DOCUMENT,
    )
    assert plan.armed
    assert plan.notice
    assert plan.disclosed
    assert plan.extract_reasoning is None

    endpoint = _endpoint([TRUNCATED_TRACE, ANSWER], provider="generic", reasoning=None)
    out, call = _adapter(endpoint, tmp_path, mode="on").call(
        "summarizer", "PACK", ProseOutput
    )
    assert out.prose == "the extracted answer"
    assert call.attempt_trace[-1].split_notice == plan.notice
    assert call.attempt_trace[-1].split_legs[-1].notice == plan.notice
    # No reasoning field was forced onto a provider that cannot carry one.
    assert endpoint.calls[1]["reasoning"] is None


def test_a_seat_that_cannot_split_records_a_notice_and_behaves_as_before(tmp_path):
    """Implements R3: standing down is recorded, and costs nothing else."""

    # The protocol was asked for and the ceiling cannot carry two legs.
    endpoint = _endpoint([ANSWER], max_tokens=256)
    out, call = _adapter(endpoint, tmp_path, mode="on").call(
        "summarizer", "PACK", ProseOutput
    )
    assert out.prose == "the extracted answer"
    assert _legs(call) == []
    assert call.attempt_trace[0].split_notice
    assert call.attempt_trace[0].split_legs == ()


def test_auto_says_nothing_about_a_seat_that_was_never_a_candidate(tmp_path):
    """Implements SPEC Amendment 1: a notice discloses an intent the run could
    not honor, and under `auto` a non-reasoning seat expresses no such intent.

    This is what keeps the blast-radius census honest. Recording a notice here
    would stamp a constant string onto every attempt of every non-reasoning run
    in the append-only record while saying nothing at all.
    """

    endpoint = _endpoint([ANSWER], reasoning="none")
    _out, call = _adapter(endpoint, tmp_path, mode="auto").call(
        "summarizer", "PACK", ProseOutput
    )
    assert _legs(call) == []
    assert call.attempt_trace[0].split_notice == ""

    # The planner still knows why, for a caller that asks.
    plan = plan_split(
        mode="auto", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="none", profile=GLM_52_DOCUMENT,
    )
    assert plan.notice and not plan.disclosed


# --- R8: the emission schema stays light ------------------------------------


def test_the_extraction_request_is_the_minimal_envelope():
    """Implements R8: the extraction call's schema is the minimal envelope; do
    not move deliberation constraints into it.

    The dose-response on schema weight is steep, so the emission call carries
    the contract schema and the trace and nothing else. Asserted as an explicit
    ABSENCE, because the failure mode here is accretion.
    """

    schema = json.dumps({"type": "object", "properties": {"prose": {}}})
    deliberation = deliberation_request("PACK BODY")
    extraction = extraction_request(schema=schema, trace=TRUNCATED_TRACE)

    assert schema in extraction
    assert TRUNCATED_TRACE in extraction

    # Whatever the deliberation leg says to make the model think, the emission
    # leg must not repeat: its whole job is to serialize.
    added_by_deliberation = deliberation.replace("PACK BODY", "").strip()
    assert added_by_deliberation
    assert added_by_deliberation not in extraction

    # And the emission request is genuinely small next to the deliberation one.
    assert len(extraction) < len(deliberation) + len(schema) + len(TRUNCATED_TRACE)


def test_an_empty_trace_still_produces_a_well_formed_extraction_request():
    """Implements R4: 'possibly-truncated' includes 'entirely absent'."""

    schema = json.dumps({"type": "object"})
    request = extraction_request(schema=schema, trace="")
    assert schema in request
    assert request.strip()


# --- R18: the operator's authorization guard --------------------------------


def test_the_plan_is_a_frozen_value():
    """A plan is computed once per attempt and then only read; nothing
    downstream may retune a budget after the ceiling was divided."""

    plan = plan_split(
        mode="on", ceiling=4096, extraction_tokens=512,
        provider="ollama", reasoning="high", profile=GLM_52_DOCUMENT,
    )
    assert isinstance(plan, SplitPlan)
    with pytest.raises(Exception):
        plan.reason_max_tokens = 1


# --- the mechanism, pinned where it can actually regress -------------------


def test_the_deliberation_leg_is_genuinely_unconstrained(tmp_path):
    """Implements R1, and pins the ONE thing that makes the split work.

    The tax that empties a seat is paid for constraining the DELIBERATION, so
    a first leg that still had to emit JSON would buy nothing at all. This
    caught a real defect: the guard originally stood the protocol down on any
    `json_object` route, and every profile `deepreason setup` mints is
    `json_object` by default -- so the feature would have shipped and never
    once fired.
    """

    endpoint = _endpoint([TRUNCATED_TRACE, ANSWER])
    endpoint.json_mode = True  # what a json_object route gives a real endpoint
    _adapter(endpoint, tmp_path, mode="on").call("summarizer", "PACK", ProseOutput)

    deliberation, emission = endpoint.calls
    assert deliberation["kwargs"].get("json_mode") is False
    assert "response_schema" not in deliberation["kwargs"]
    assert "output_mechanism" not in deliberation["kwargs"]

    # The emission leg carries the route's own output mode in full: the
    # override is per request and never mutates the endpoint.
    assert "json_mode" not in emission["kwargs"]
    assert endpoint.json_mode is True


def test_a_route_enforced_at_the_sampler_stands_down(tmp_path):
    """Implements R3: a grammar or native schema constrains every completion at
    the sampler, so no leg of it could be free and the split buys nothing.
    Standing down is recorded, never refused."""

    from deepreason.llm.split import NOTICE_OUTPUT_MECHANISM, stand_down

    assert stand_down(NOTICE_OUTPUT_MECHANISM).notice == NOTICE_OUTPUT_MECHANISM
    assert stand_down(NOTICE_OUTPUT_MECHANISM).disclosed
    assert not stand_down(NOTICE_OUTPUT_MECHANISM).armed


def test_the_shipped_glm_seat_actually_arms():
    """Implements R2, end to end on a REAL profile rather than a hand-made one.

    R2 names glm-5.2 by name, so the regression that matters is whether the
    seat a `deepreason setup` profile actually compiles to arms under the
    shipped default. Pinned because the answer was NO until the deliberation
    leg was allowed to be unconstrained.
    """

    from deepreason.preparation import build_preparation_manifest
    from deepreason.provider_profile import ProviderProfileV1

    profile = ProviderProfileV1.create(
        provider="ollama",
        endpoint="https://ollama.com/v1",
        model_id="glm-5.2",
        model_revision="r1",
        family="glm",
        context_window_tokens=131_072,
        maximum_completion_tokens=32_768,
        credential_env="OLLAMA_API_KEY",
    )
    manifest = build_preparation_manifest(
        profile, question="q", compiled_at="2026-07-11T00:00:00Z"
    )
    route = manifest.roles["conjecturer"][0]
    plan = plan_split(
        mode="auto",
        ceiling=route.max_tokens,
        extraction_tokens=512,
        provider=route.provider,
        reasoning=route.reasoning,
        profile=GLM_52_DOCUMENT,
    )
    assert plan.armed, (route.provider, route.reasoning, route.output_mode)
    assert plan.extract_reasoning == "none"
    assert plan.reason_max_tokens + plan.extract_max_tokens == route.max_tokens
