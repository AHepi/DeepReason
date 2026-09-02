"""A split leg is not a repair attempt -- the record, and the reading of it.

Regression (soak case `split-legs`; the P-C2b STOP's `--case pc2b`): the
split-budget seat protocol wrote its two provider LEGS into
``LLMCall.attempt_trace``, which ``invariants.py::verify_root`` reads as a
REPAIR LADDER.  Every thinking-ON run was therefore replay-invalid -- 260
violations across four unrelated checks on a run that CONVERGED -- plus an
``LLMAttempt.prompt_ref=None`` operational failure on the stand-down path.

The legs now live on the ONE attempt they jointly produced, as declared
``LLMSplitLegV1`` records, and `verify_root` reads that shape with a
`split-legs` family of its own.

Every limb below is mutation-proven in BOTH directions: it fires on a record
that violates it, and is silent on the record that does not.  A check that
cannot fail is not a check, and `verify_root` findings have no auditor of
their own the way map `check:` lines do (`docs_verify --audit`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.llm.split import (
    NOTICE_NO_HEADROOM,
    SPLIT_LEG_EXTRACT,
    SPLIT_LEG_REASON,
)
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.ontology.event import LLMAttempt, LLMSplitLegV1
from deepreason import model_profiles
from deepreason.rules.conj import conj
from deepreason.run_manifest import Route, RunManifest, persist_run_manifest
from tests.test_process_metadata import _patch_legacy_manifest_consumers

VALID = json.dumps({"candidates": [{"content": "keep", "typicality": 0.5}]})
# Well-formed JSON that satisfies no closed wire schema: what the adapter's
# validator rejects into a repair prompt.
INVALID = '{"candidates":[{"content":"keep","typicality":2}]}'
TRACE = "Working the problem. The load-bearing support is the second, because"




# Both endpoints below name glm-5.2, and since 2026-09-01 what a model does
# with a reasoning value is read from that model's own document rather than
# decided by a constant.  Without a document the protocol correctly stands
# down, and these tests would be recording the unknown-model path instead of
# the split they exist to record (`DR-CON-model-profiles`).
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
    model_profiles.register(GLM_52_DOCUMENT)
    try:
        yield
    finally:
        model_profiles.unregister("glm-5.2")

def _manifest(endpoint):
    route = Route(
        endpoint_id="thinking-seat",
        base_url=endpoint.name,
        model_id=endpoint.model,
        # A reasoning knob plus an UNSET reasoning value is the whole of the
        # wiring: `auto` splits exactly the seats whose route says they think,
        # and unset is NOT off.
        provider="ollama",
        family="glm",
        max_tokens=endpoint.max_tokens,
    )
    return RunManifest(
        engine_profile="full",
        model_profile="compact",
        roles={"conjecturer": (route,)},
        rubric_policy="forbid",
        concurrency=1,
        pack_profile="compact",
        output_profile="compact",
        source_config_hash="0" * 64,
        compiled_at="2026-08-27T00:00:00Z",
        engine_config_json="{}",
    )


def _split_run(root, monkeypatch, responses, *, mode="auto"):
    """One conjecturer call through the managed rule, split armed."""

    endpoint = MockEndpoint(
        responses,
        name="https://ollama.com/v1",
        model="glm-5.2",
        max_tokens=4096,
        reasoning_traces=[TRACE],
    )
    endpoint.provider = "ollama"
    manifest = _manifest(endpoint)
    persist_run_manifest(manifest, root)
    _patch_legacy_manifest_consumers(monkeypatch, root, manifest)
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="pi-1",
            description="a problem",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=2,
        model_profile="compact",
        leases=leases_from_manifest(manifest),
        split_budget_mode=mode,
        split_extraction_tokens=512,
    )
    conj(harness, "pi-1", adapter, Config(VS_K=1, NEAR_DUP_EPS=None))
    return harness, endpoint


def _llm_events(root):
    out = []
    for line in (Path(root) / "log.jsonl").read_text().splitlines():
        event = json.loads(line)
        if event.get("llm"):
            out.append(event)
    return out


def _mutate(root, mutation):
    """Rewrite the root's log with one llm event's trace mutated.

    This constructs a HYPOTHETICAL bad record to prove a check can fail.  It
    never touches a committed run root -- `root` is always a tmp_path.
    """

    log = Path(root) / "log.jsonl"
    lines = log.read_text().splitlines()
    done = False
    for index, line in enumerate(lines):
        event = json.loads(line)
        trace = (event.get("llm") or {}).get("attempt_trace") or []
        if not done and any(a.get("split_legs") for a in trace):
            mutation(event)
            lines[index] = json.dumps(event, sort_keys=True)
            done = True
    assert done, "no split-carrying event to mutate"
    log.write_text("\n".join(lines) + "\n")


def _checks(root):
    return sorted({v["check"] for v in verify_root(root)["violations"]})


# --- the shape ---------------------------------------------------------------


def test_a_split_call_records_two_legs_on_one_attempt(tmp_path, monkeypatch):
    """The defect, stated positively: ONE attempt, TWO legs, no ladder entry.

    Before the fix this call left two entries in `attempt_trace`, both with
    `attempt=0`, and `attempts` read 2 -- which is how a leg came to be read
    as a repair.
    """

    root = tmp_path / "run"
    harness, endpoint = _split_run(root, monkeypatch, [TRACE, VALID])
    assert len(endpoint.calls) == 2, "the split did not arm"

    event = _llm_events(root)[0]
    trace = event["llm"]["attempt_trace"]
    assert len(trace) == 1
    assert event["llm"]["attempts"] == 1
    assert trace[0]["attempt"] == 0
    assert trace[0]["valid"] is True

    legs = trace[0]["split_legs"]
    assert [leg["leg"] for leg in legs] == [SPLIT_LEG_REASON, SPLIT_LEG_EXTRACT]
    # The legs account for the attempt EXACTLY. Double-counting -- the trace
    # summing leg one twice -- was the defect's own signature.
    assert sum(leg["tokens"] for leg in legs) == trace[0]["tokens"]
    # B_a is taken OUT of the ceiling, never added to it.
    assert sum(leg["max_tokens"] for leg in legs) <= trace[0]["max_tokens"]
    # The emission leg serialized the deliberation that preceded it. Blob refs
    # are content addresses, so this is proof rather than a claim.
    assert legs[1]["trace_ref"] == legs[0]["trace_ref"]
    # The attempt keeps the SEAT's own request; each leg's synthesized
    # envelope is reachable through the leg, not in place of it.
    assert legs[0]["prompt_ref"] != trace[0]["prompt_ref"]
    assert harness.blobs.get(legs[0]["prompt_ref"]).startswith(
        harness.blobs.get(trace[0]["prompt_ref"])
    )


def test_verify_root_accepts_a_thinking_on_record(tmp_path, monkeypatch):
    """The regression the defect broke: a split run is replay-VALID.

    Mutation proof is the whole rest of this file -- every limb below fires on
    a record this one does not violate.
    """

    root = tmp_path / "run"
    _split_run(root, monkeypatch, [TRACE, VALID])
    assert verify_root(root)["violations"] == []


def test_an_undivided_call_records_no_legs(tmp_path, monkeypatch):
    """A seat that never splits is untouched, and still verifies clean."""

    root = tmp_path / "run"
    _split_run(root, monkeypatch, [VALID], mode="off")
    trace = _llm_events(root)[0]["llm"]["attempt_trace"]
    assert [a["split_legs"] for a in trace] == [[]]
    assert verify_root(root)["violations"] == []


# --- the two shapes coexist ---------------------------------------------------


def test_a_split_call_and_a_genuine_repair_coexist(tmp_path, monkeypatch):
    """Legs AND a real repair on one call -- the case that proves neither
    displaces the other.

    A repair turn never splits (`_split_plan`: it is extraction-shaped by
    construction), so the shape is attempt 0 split and rejected, attempt 1 an
    ordinary undivided repair.  The repair ladder's OWN semantics have to be
    unchanged through that: `attempts` counts attempts and not legs, and the
    diagnostic the ladder requires is where the ladder looks for it.
    """

    root = tmp_path / "run"
    harness, _endpoint = _split_run(root, monkeypatch, [TRACE, INVALID, VALID])
    event = _llm_events(root)[0]
    trace = event["llm"]["attempt_trace"]

    # Two attempts, one repair -- legs did not inflate the count.
    assert event["llm"]["attempts"] == 2
    assert [a["attempt"] for a in trace] == [0, 1]
    assert [a["valid"] for a in trace] == [False, True]

    # The split is on attempt 0 and only there.
    assert len(trace[0]["split_legs"]) == 2
    assert trace[1]["split_legs"] == []
    # The rejected attempt carries a real validation diagnostic. Its legs are
    # not that: the reason leg is invalid by design and never had one, which
    # is exactly what `attempt-blobs` used to demand of it.
    assert trace[0]["diagnostic_ref"]

    # The repair ladder is unchanged: the diagnostic is in the CALL's final
    # prompt, which is the seat's own repair request -- not the extraction
    # envelope the emission leg put on the wire.
    final_prompt = harness.blobs.get(event["llm"]["prompt_ref"]).decode()
    assert "DIAGNOSTIC:" in final_prompt
    assert "complete corrected JSON value" in final_prompt

    assert verify_root(root)["violations"] == []


# --- mutation proofs: each limb fires ----------------------------------------


def _first_split(event):
    for attempt in event["llm"]["attempt_trace"]:
        if attempt.get("split_legs"):
            return attempt
    raise AssertionError("no split attempt")


@pytest.mark.parametrize(
    "name,mutation",
    [
        # L1 shape -- a pair in any other shape is not the protocol that ran.
        (
            "shape",
            lambda e: _first_split(e)["split_legs"].pop(),
        ),
        (
            "order",
            lambda e: _first_split(e)["split_legs"].reverse(),
        ),
        # L2 accounting -- the legs stop accounting for the attempt.
        (
            "accounting",
            lambda e: _first_split(e)["split_legs"][0].__setitem__(
                "tokens", _first_split(e)["split_legs"][0]["tokens"] + 7
            ),
        ),
        # L3 envelope -- the pair escapes the authorized ceiling.
        (
            "envelope",
            lambda e: _first_split(e)["split_legs"][0].__setitem__(
                "max_tokens", _first_split(e)["max_tokens"] + 1
            ),
        ),
        # L4 continuity -- the emission leg names a deliberation the reason
        # leg never produced, and carries no notice explaining why.
        (
            "continuity",
            lambda e: _first_split(e)["split_legs"][1].__setitem__(
                "trace_ref", _first_split(e)["split_legs"][1]["prompt_ref"]
            ),
        ),
        # L5 blobs -- a leg's evidence is unreachable.
        (
            "blobs",
            lambda e: _first_split(e)["split_legs"][0].__setitem__(
                "raw_ref", "sha256:" + "0" * 64
            ),
        ),
        # L6 provenance -- the deliberation leg did not carry the attempt's
        # own request, so whatever the ladder requires in the final prompt
        # never reached the provider.
        (
            "provenance",
            lambda e: _first_split(e)["split_legs"][0].__setitem__(
                "prompt_ref", _first_split(e)["split_legs"][1]["prompt_ref"]
            ),
        ),
    ],
)
def test_each_split_legs_limb_fires_on_a_record_that_violates_it(
    tmp_path, monkeypatch, name, mutation
):
    root = tmp_path / "run"
    _split_run(root, monkeypatch, [TRACE, VALID])
    assert verify_root(root)["violations"] == [], "the base record must be clean"

    _mutate(root, mutation)
    checks = _checks(root)
    assert "split-legs" in checks, (name, checks)


def test_a_leg_is_never_read_as_a_repair_attempt(tmp_path, monkeypatch):
    """The defect's own four checks stay silent on a thinking-ON record.

    Named individually rather than asserting an empty list, because the point
    is not "clean" but "clean IN THESE FOUR PLACES" -- each one fired on this
    exact shape before the fix.
    """

    root = tmp_path / "run"
    _split_run(root, monkeypatch, [TRACE, VALID])
    fired = _checks(root)
    for check in (
        "attempt-accounting",
        "attempt-order",
        "attempt-blobs",
        "repair-metadata",
    ):
        assert check not in fired


# --- defect B: the stand-down path -------------------------------------------


def test_a_stand_down_at_dispatch_never_writes_a_null_prompt_ref(tmp_path):
    """Regression: an armed plan that stands down at dispatch used to write
    `prompt_ref=None` and kill the run with a typed operational failure.

    The meter is exhausted before the emission leg can be booked, which is the
    NOTICE_NO_HEADROOM stand-down -- the path `cycle_soak --case split-legs
    --token-budget 200000` died on at cycle 2, byte-identically to the P-C2b
    soak.  The call must fall back to an ordinary undivided dispatch and
    record why.
    """

    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.contracts import ProseOutput
    from deepreason.storage.blobs import BlobStore

    endpoint = MockEndpoint(
        [json.dumps({"prose": "an answer"})],
        name="https://ollama.com/v1",
        model="glm-5.2",
        max_tokens=4096,
    )
    endpoint.provider = "ollama"
    endpoint.reasoning = "high"
    adapter = LLMAdapter(
        {"summarizer": endpoint},
        BlobStore(tmp_path / "blobs"),
        split_budget_mode="on",
        split_extraction_tokens=512,
        # Enough for the call itself, never enough for the emission leg's own
        # conservative bound booked on top of it.
        meter=TokenMeter(budget=6_000),
    )

    out, call = adapter.call("summarizer", "PACK", ProseOutput)
    assert out.prose == "an answer"
    assert len(call.attempt_trace) == 1
    attempt = call.attempt_trace[0]
    # The whole class of bug: `prompt_ref` is never assigned from a
    # stand-down's return, so there is nothing for it to be None from.
    assert isinstance(attempt.prompt_ref, str) and attempt.prompt_ref
    assert attempt.split_legs == ()
    # Named, not merely non-empty: a test that accepted any notice would pass
    # on a seat that never armed at all, which is not the path under test.
    assert attempt.split_notice == NOTICE_NO_HEADROOM
    assert len(endpoint.calls) == 1, "it fell back to ONE undivided call"


# --- the record shape's own boundaries ---------------------------------------


def test_the_leg_record_round_trips(tmp_path):
    leg = LLMSplitLegV1(
        leg="reason",
        prompt_ref="blob:p",
        raw_ref="blob:r",
        trace_ref="blob:t",
        max_tokens=32_256,
        tokens=9_712,
        ms=737_000,
        natural_stop=False,
    )
    assert (
        LLMSplitLegV1.model_validate(leg.model_dump(mode="python", by_alias=True))
        == leg
    )
    dumped = json.loads(leg.model_dump_json(by_alias=True))
    assert dumped["schema"] == "llm-split-leg.v1"
    assert "attempt" not in dumped
    # A leg carries no attempt index, and cannot be given one: it is not a
    # rung on the repair ladder and must not be able to claim it is.
    with pytest.raises(Exception):
        LLMSplitLegV1(
            leg="reason",
            prompt_ref="blob:p",
            raw_ref="blob:r",
            trace_ref="blob:t",
            max_tokens=1,
            attempt=0,
        )


def test_an_attempt_from_a_committed_root_deserialises_with_no_legs():
    """The removed fields cost no committed root its readability.

    `FrozenRecord` sets only `frozen=True`, so pydantic's `extra="ignore"`
    applies: the 717 committed attempts carrying `"split_leg": ""` still
    load, now with `split_legs == ()`.  Pinned against a REAL committed
    record rather than a fixture -- a fixture would only prove what this test
    wrote itself.
    """

    root = Path("experiments/2026-08-25-change-constructive-frontier/run")
    log = root / "log.jsonl"
    if not log.exists():  # pragma: no cover - shallow checkout
        pytest.skip("committed root not present in this checkout")

    seen = 0
    for line in log.read_text().splitlines():
        for stored in (json.loads(line).get("llm") or {}).get("attempt_trace") or []:
            assert "split_leg" in stored, "the probe must read the OLD shape"
            attempt = LLMAttempt.model_validate(stored)
            assert attempt.split_legs == ()
            seen += 1
    assert seen, "the probe found no attempts to read"


def test_the_split_legs_soak_config_differs_from_pc1_by_exactly_one_line():
    """The instrument is one deleted line, and stays that way.

    `run-config.yaml`'s own header says this; a comment is not a check.  If
    the two configs ever diverge further, a green `--case split-legs` stops
    being evidence about thinking alone.
    """

    tranche = Path("experiments/2026-08-27-defect-split-leg-recording")
    pc1 = Path("experiments/2026-08-25-change-constructive-frontier")
    mine = (tranche / "run-config.yaml").read_text().splitlines()
    theirs = (pc1 / "run-config.yaml").read_text().splitlines()

    # Drop this tranche's own header, which stops at the P-C1 header's start.
    start = mine.index("# P-C1 ARM H: SOLO source configuration, everything on, NO JUDGE.")
    body = mine[start:]
    removed = [line for line in theirs if line not in body]
    assert removed == ['    reasoning: "none"'], removed
    assert len(body) == len(theirs) - 1
