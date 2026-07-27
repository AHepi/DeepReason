"""Offline replay of the first live engaged-run robustness failures.

A live engaged-preset run (mistral-large-3:675b) failed
V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at cycle 0 despite semantically sound
content, for two mechanical reasons replayed here:

1. Transport: the model wrapped an otherwise-valid JSON value in one markdown
   fence between explanation prose ("Here's the corrected JSON ... ```json
   {...} ``` <explanation>"), which the normalizer rejected as trailing
   content.  One unambiguous fenced value is now accepted at consume time;
   every ambiguous shape still fails.

2. Grant arithmetic: one conjecturer.turn.v6 output carried four independent
   handle-pattern mistakes (scratch links and unresolved questions, pattern
   ``^(?:SCR|NEW)_[0-9]{3,}$``).  The v6 patch protocol repairs one pointer
   per attempt, so the old two-repair grant was structurally doomed even
   though every individual repair succeeded.  The conjecture family now
   grants four repairs and the whole chain converges.
"""

from __future__ import annotations

import json

import pytest

from deepreason.harness import Harness
from deepreason.llm.repair import parse_one_json_value
from deepreason.rules.conj import conj
from deepreason.run_manifest import ScratchAuthoringPolicyV1
from deepreason.scratch.service import ScratchService
from deepreason.workflow.models import WorkflowTaskKind
from tests.test_v6_transaction_qualification import (
    _config,
    _live_adapter,
    _manifest,
    _seed_live_conjecture,
)


def _fenced(value: dict, *, lead: str, tail: str) -> str:
    return f"{lead}\n```json\n{json.dumps(value, indent=2)}\n```\n{tail}"


LIVE_LEAD = (
    "Here's the corrected JSON value with only one top-level object "
    "(removing the trailing content and multiple JSON values):"
)
LIVE_TAIL = (
    "This version keeps every unrelated value exactly as it was and fixes "
    "only the reported contract error."
)


def test_live_prose_fence_prose_shapes_parse_to_the_fenced_value():
    candidate = {
        "candidate": {
            "content": "A crash during result publication leaves a gap.",
            "typicality": 0.4,
            "neighbours": [],
        }
    }
    patch = {
        "schema": "repair.patch.v1",
        "op": "replace",
        "path": "/scratch_proposal/links/1/to_ref",
        "value": "SCR_002",
    }
    for value in (candidate, patch):
        parsed = parse_one_json_value(_fenced(value, lead=LIVE_LEAD, tail=LIVE_TAIL))
        assert parsed.value == value

    # Ambiguity stays rejected: two fences, or a bare value beside the fence,
    # or trailing content that itself parses as JSON.
    fenced = _fenced(candidate, lead=LIVE_LEAD, tail="")
    for ambiguous in (
        fenced + "\n```json\n{}\n```",
        json.dumps(candidate) + "\n" + fenced,
        fenced + "\n" + json.dumps(patch),
    ):
        with pytest.raises(ValueError):
            parse_one_json_value(ambiguous)


def test_prose_wrapped_fenced_turn_response_consumes_no_repair(tmp_path):
    manifest = _manifest()
    harness = ScratchService(tmp_path / "prose-fence-turn").harness
    _seed_live_conjecture(harness)
    turn = {
        "candidates": [
            {"content": "A valid provisional mechanism.", "typicality": 0.4}
        ]
    }
    adapter, _endpoint = _live_adapter(
        harness,
        manifest,
        [_fenced(turn, lead=LIVE_LEAD, tail=LIVE_TAIL)],
    )

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        _config(),
        workload_profile="text",
        run_manifest=manifest,
    )

    (artifact,) = registered
    assert artifact.content_ref == "inline:A valid provisional mechanism."
    (work,) = harness.workflow_state.transaction_work.values()
    assert work.terminal.status == "completed"
    assert adapter.meter.calls == 1

    # Replay materializes the identical state from the durable log, so the
    # verify path normalizes the prose-wrapped raw exactly like the live path.
    (replayed,) = Harness(harness.root).workflow_state.transaction_work.values()
    assert replayed.terminal.status == "completed"
    assert replayed.preparation.id == work.preparation.id


def _scratch_policy() -> ScratchAuthoringPolicyV1:
    return ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=4,
        maximum_revisions_per_turn=4,
        maximum_links_per_turn=4,
        maximum_unresolved_questions_per_turn=4,
        maximum_cluster_suggestions_per_turn=4,
        maximum_total_bytes=128 * 1024,
    )


def _block(key: str, content: str) -> dict:
    return {"local_key": key, "body": {"content": content}}


def _patch(path: str, value) -> str:
    return json.dumps(
        {"schema": "repair.patch.v1", "op": "replace", "path": path, "value": value}
    )


def test_four_handle_pattern_failures_converge_within_the_grant(tmp_path):
    """The live shape: four bad scratch handles, one authorized patch each."""

    manifest = _manifest(scratch_authoring=_scratch_policy())
    grant = next(
        item
        for item in manifest.contract_schema_repair_policy.grants
        if item.contract_id == "conjecturer.turn.v6"
    )
    assert grant.maximum_schema_repairs == 4
    assert grant.maximum_provider_calls == 5

    harness = ScratchService(tmp_path / "four-handle-mistakes").harness
    _seed_live_conjecture(harness)
    invalid_turn = {
        "candidates": [
            {"content": "A semantically sound mechanism.", "typicality": 0.4}
        ],
        "scratch_proposal": {
            "new_blocks": [
                _block("NEW_001", "speculative mechanism sketch"),
                _block("NEW_002", "counterexample fragment"),
            ],
            # Four independent handle-pattern mistakes, exactly as observed
            # live: none match ^(?:SCR|NEW)_[0-9]{3,}$.
            "links": [
                {
                    "from_ref": "scratch-block-1",
                    "to_ref": "NEW_002",
                    "relation_hint": "supports",
                },
                {
                    "from_ref": "NEW_002",
                    "to_ref": "block2",
                    "relation_hint": "contradicts",
                },
            ],
            "unresolved_questions": [
                {"question": "Does the gap survive replays?", "related_refs": ["scratch-3"]},
                {"question": "Which fence closes first?", "related_refs": ["new-block-4"]},
            ],
        },
    }
    responses = [
        json.dumps(invalid_turn),
        # One valid single-operation patch per authorized pointer, per turn.
        _patch("/scratch_proposal/links/0/from_ref", "NEW_001"),
        _patch("/scratch_proposal/links/1/to_ref", "NEW_001"),
        _patch("/scratch_proposal/unresolved_questions/0/related_refs", ["NEW_001"]),
        _patch("/scratch_proposal/unresolved_questions/1/related_refs", ["NEW_002"]),
    ]
    adapter, endpoint = _live_adapter(harness, manifest, responses)

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        _config(),
        workload_profile="text",
        run_manifest=manifest,
    )

    (artifact,) = registered
    assert artifact.content_ref == "inline:A semantically sound mechanism."
    assert endpoint._responses == []
    assert adapter.meter.calls == 5

    work = list(harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.CONJECTURE,
        *([WorkflowTaskKind.REPAIR] * 4),
    ]
    assert [item.terminal.status for item in work] == [
        *(["rejected"] * 4),
        "completed",
    ]
    assert all(
        item.preparation.task_payload_value["mode"] == "patch" for item in work[1:]
    )
    # Every repair was independently authorized work on the same route.
    assert len({item.preparation.id for item in work}) == 5
    assert all(
        item.preparation.route_lease == work[0].preparation.route_lease
        for item in work
    )
    # The repaired advisory scratch proposal landed: the two new blocks plus
    # the two unresolved questions are stored as advisory scratch blocks.
    assert len(ScratchService(harness).state.blocks) == 4

    # Replay of the durable log reproduces the exact five-transaction chain.
    replayed = list(Harness(harness.root).workflow_state.transaction_work.values())
    assert [item.terminal.status for item in replayed] == [
        *(["rejected"] * 4),
        "completed",
    ]
