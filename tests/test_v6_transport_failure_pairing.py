"""Pairing a transport-failure attempt with the call that produced it.

Regression (cycle soak `--case epoch3 --induce-repairs 2`, parked as P1 in
`experiments/2026-08-23-change-cycle-soak-instrument/PARKED.md`): a run that
terminated typed and clean still failed `verify_root`'s `workflow-call-pairing`
check, because `ProviderAttemptV1.raw_ref` spells "no body" as ``None`` while
`LLMCall.raw_ref` spells it as ``""``.  The writer translates between the two
(`transaction_service.record_provider_attempt`, ``call.raw_ref or None``); so
does replay's copy of the same six agreements.  The verifier's copy did not.

The first test is the defect.  Every other test is the mutation proof that
fixing it did not make the check blind: each breaks exactly one of the six
agreements and requires the finding back.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.storage.objects import ObjectStore
from deepreason.workflow.transaction import (
    ProviderAttemptV1,
    WorkLifecycleTransitionV1,
    WorkTransitionKind,
)
from tests.test_v6_controller3_replay_verification import (
    _canonical_root,
    _log_rows,
    _provider_rows,
    _write_log,
)


def _transport_failure_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The canonical controller-v3 root, with the FIRST dispatch losing its
    transport.  Built through the real adapter, the real conj rule and the real
    transaction service, so the recorded shape is the live one rather than a
    hand-written fixture."""

    real_complete = MockEndpoint.complete
    seen = {"calls": 0}

    def failing_complete(self, prompt, images=None, **kwargs):
        seen["calls"] += 1
        if seen["calls"] == 1:
            raise EndpointError("HTTP-500: Internal Server Error")
        return real_complete(self, prompt, images=images, **kwargs)

    monkeypatch.setattr(MockEndpoint, "complete", failing_complete)

    # conj terminalizes the work item durably and then re-raises; the root it
    # leaves behind is the artifact under test.
    with pytest.raises(EndpointError):
        _canonical_root(tmp_path)
    return tmp_path / "canonical"


def _sole_provider_event(root: Path):
    harness = Harness(root, read_only=True)
    events = [event for event in harness.log.read() if event.llm is not None]
    assert len(events) == 1, [event.seq for event in events]
    return harness, events[0]


def _checks(root: Path) -> set[str]:
    return {item["check"] for item in verify_root(root)["violations"]}


def _copy(root: Path, tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(root, target)
    return target


def _rewrite_attempt(root: Path, **changes) -> None:
    """Replace the sole provider attempt with a mutated one, re-anchoring the
    lifecycle transition and the event outputs so that ONLY the mutated field
    differs.  Anything less would fail a different check and prove nothing."""

    harness, event = _sole_provider_event(root)
    attempt = next(
        record
        for schema, record in (harness.objects.get(oid) for oid in event.outputs)
        if schema == "workflow-provider-attempt-v1"
    )
    fields = attempt.model_dump(mode="python", by_alias=False)
    for key in ("schema", "id", "created_at", "kind"):
        fields.pop(key, None)
    fields.update(changes)
    mutated = ProviderAttemptV1.create(**fields)
    transition = WorkLifecycleTransitionV1.create(
        work_id=mutated.work_id,
        attempt_index=mutated.attempt_index,
        transition_kind=WorkTransitionKind.PROVIDER_RESULT,
        trigger_ref=mutated.id,
    )
    store = ObjectStore(root / "objects")
    store.put("workflow-provider-attempt-v1", mutated)
    store.put("workflow-work-lifecycle-transition-v1", transition)

    rows = _log_rows(root)
    row = _provider_rows(rows)[0]
    row["outputs"] = [mutated.id, transition.id]
    row["inputs"] = [transition.work_id, transition.trigger_ref]
    row["control"]["inputs"] = list(row["inputs"])
    row["control"]["outputs"] = list(row["outputs"])
    row["control"]["decision_ref"] = transition.id
    _write_log(root, rows)


def _rewrite_call(root: Path, **changes) -> None:
    rows = _log_rows(root)
    row = _provider_rows(rows)[0]
    row["llm"].update(changes)
    _write_log(root, rows)


# ---------------------------------------------------------------------------
# The defect
# ---------------------------------------------------------------------------


def test_a_transport_failure_attempt_pairs_with_the_call_that_produced_it(
    tmp_path, monkeypatch
):
    root = _transport_failure_root(tmp_path, monkeypatch)
    harness, event = _sole_provider_event(root)

    # The live shape, asserted rather than assumed: the call carries the empty
    # string, the durable attempt carries the typed absence, and the outcome is
    # the one the model validator permits a null raw_ref for.
    assert event.llm.raw_ref == ""
    attempt = next(
        record
        for schema, record in (harness.objects.get(oid) for oid in event.outputs)
        if schema == "workflow-provider-attempt-v1"
    )
    assert attempt.raw_ref is None
    assert attempt.outcome == "transport_failure"

    # ... and the other five agreements hold, so the pairing check has nothing
    # left to object to.
    assert attempt.authorization_bundle_ref == event.llm.dispatch_authorization_ref
    assert attempt.prompt_sha256 == event.llm.prompt_ref

    assert verify_root(root)["violations"] == []


# ---------------------------------------------------------------------------
# Mutation proof: each agreement, broken one at a time, must come back
# ---------------------------------------------------------------------------


def test_a_dropped_raw_blob_still_fails_closed(tmp_path, monkeypatch):
    """The call DID return a body and the durable attempt forgot it.  This is
    the case the normalization must not swallow: `None` is only equal to an
    ABSENT call raw, never to a present one."""

    root = _copy(
        _transport_failure_root(tmp_path, monkeypatch), tmp_path, "dropped-raw"
    )
    _rewrite_call(root, raw_ref="a" * 64)

    assert "workflow-call-pairing" in _checks(root)


def test_an_invented_raw_blob_still_fails_closed(tmp_path, monkeypatch):
    """The mirror image: the attempt claims a body the call never carried."""

    root = _copy(
        _transport_failure_root(tmp_path, monkeypatch), tmp_path, "invented-raw"
    )
    _rewrite_attempt(root, raw_ref="b" * 64, outcome="provider_result")

    assert "workflow-call-pairing" in _checks(root)


def test_a_mismatched_contract_still_fails_closed(tmp_path, monkeypatch):
    root = _copy(
        _transport_failure_root(tmp_path, monkeypatch), tmp_path, "wrong-contract"
    )
    _rewrite_attempt(root, contract_id="conjecturer.turn.v6.forged")

    assert "workflow-call-pairing" in _checks(root)


def test_a_mismatched_prompt_digest_still_fails_closed(tmp_path, monkeypatch):
    root = _copy(
        _transport_failure_root(tmp_path, monkeypatch), tmp_path, "wrong-prompt"
    )
    _rewrite_attempt(root, prompt_sha256="c" * 64)

    assert "workflow-call-pairing" in _checks(root)


def test_a_mismatched_authorization_bundle_still_fails_closed(tmp_path, monkeypatch):
    root = _copy(
        _transport_failure_root(tmp_path, monkeypatch), tmp_path, "wrong-bundle"
    )
    _rewrite_call(root, dispatch_authorization_ref=f"sha256:{'d' * 64}")

    assert "workflow-call-pairing" in _checks(root)


def test_a_call_bound_to_another_work_item_still_fails_closed(tmp_path, monkeypatch):
    root = _copy(
        _transport_failure_root(tmp_path, monkeypatch), tmp_path, "wrong-work"
    )
    _rewrite_call(root, work_order_id=f"sha256:{'e' * 64}")

    assert "workflow-call-pairing" in _checks(root)
