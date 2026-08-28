"""One repair-`mode` vocabulary, shared by type, across writer and reader.

Regression (technique run-456885c569c0f4f7, epoch 5): the run died at cycle 2
with ``NonConjectureRecoveryAuthorityError("repair mode is invalid")`` because
the only writer of a ``repair.semantic-task.v1`` payload's ``mode``
(``workflow/repair_transaction.py``, copying ``V6RepairTurn.mode``) and the
authority that reads it back (``workflow/nonconjecture_recovery.py``) were
typed independently and intersected in ``patch`` alone.  The reader admitted
``full`` -- a name for the whole-object case that nothing has ever emitted --
and rejected ``whole_object_syntax``, which the producer emits whenever a
provider response cannot be parsed at all.  36 of the 56 repair payloads in the
three committed roots carry the rejected value
(``experiments/2026-08-28-audit-run-problems/probes/q5_repair_payloads.json``).

The two repair modes reach recovery by different provider responses, so both
are driven end to end here rather than asserted from a hand-built payload: an
unparseable first response leaves no JSON baseline and produces
``whole_object_syntax`` with no authorized pointers; a parseable-but-invalid
one leaves a baseline and produces ``patch`` with a canonical pointer list.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deepreason.harness import Harness
from deepreason.llm.budget import TokenMeter
from deepreason.llm.packs import aliases_for_pack
from deepreason.llm.repair import V6RepairTurn
from deepreason.llm.wire import AtomicConjectureWireContractV1
from deepreason.run_manifest import load_run_manifest
from deepreason.workflow.atomic_recovery import recover_atomic_child_output
from deepreason.workflow.transaction_service import InquiryTransactionService

from tests.test_v6_engaged_repair_verification import _engaged_root

REPAIRED_SLOT = 5


def _child_and_repair(harness: Harness, slot: int):
    """The decomposition child for ``slot`` and its repair descendant."""

    def payload(item):
        value = item.preparation.task_payload_value
        return value if hasattr(value, "get") else {}

    work = list(harness.workflow_state.transaction_work.values())
    child = next(
        item
        for item in work
        if payload(item).get("schema") == "contract-decomposition-child.v1"
        and payload(item).get("child_key") == f"candidate-slot-{slot:03d}"
    )
    repair = next(
        item
        for item in work
        if payload(item).get("schema") == "repair.semantic-task.v1"
        and payload(item).get("parent_work_id") == child.preparation.id
    )
    return child, payload(repair)


def _recover(root: Path, slot: int):
    """Drive one recorded decomposition child through the live recovery path.

    This is ``rules/conj.py``'s own re-entry: ``_v6_atomic_conjecture_fallback``
    finds a child whose preparation payload already matches and recovers its
    stored output instead of re-dispatching.
    """

    harness = Harness(root)
    manifest = load_run_manifest(root / "run-manifest.json")
    service = InquiryTransactionService(harness, manifest, TokenMeter(100_000))
    child, repair_payload = _child_and_repair(harness, slot)
    contract = AtomicConjectureWireContractV1(aliases_for_pack("", {}, prefix="A"))
    return (
        recover_atomic_child_output(harness, manifest, service, child, contract),
        repair_payload,
    )


@pytest.fixture(scope="module")
def whole_object_root(tmp_path_factory) -> Path:
    return _engaged_root(
        tmp_path_factory.mktemp("repair-mode-whole-object"),
        repair_child=REPAIRED_SLOT,
        repair_kind="whole_object",
    )


@pytest.fixture(scope="module")
def patch_root(tmp_path_factory) -> Path:
    return _engaged_root(
        tmp_path_factory.mktemp("repair-mode-patch"),
        repair_child=REPAIRED_SLOT,
        repair_kind="patch",
    )


def test_whole_object_syntax_repair_child_recovers_instead_of_killing_the_run(
    whole_object_root,
):
    """The exact shape epoch 5 died on, driven through the exact call site.

    Before the fix this raised
    ``NonConjectureRecoveryAuthorityError("repair mode is invalid")`` from
    ``atomic_recovery.py``'s ``_repair_authority`` call.
    """

    (output, call), repair_payload = _recover(whole_object_root, REPAIRED_SLOT)

    # The payload shape that killed the run, asserted before the outcome so a
    # fixture that stopped producing it cannot pass this test silently.
    assert repair_payload["mode"] == "whole_object_syntax"
    assert repair_payload["authorized_pointers"] == []
    assert repair_payload["repair_index"] == 1

    # A whole-object repair replaces the entire baseline, so the recovered
    # candidate is the repair's own raw response with no patch applied.
    assert call is not None
    assert output.candidates[0].content == f"atomic mechanism {REPAIRED_SLOT}"


def test_patch_repair_child_still_recovers_through_its_own_branch(patch_root):
    """The mode that always worked keeps working, and keeps applying the patch."""

    (output, call), repair_payload = _recover(patch_root, REPAIRED_SLOT)

    assert repair_payload["mode"] == "patch"
    assert repair_payload["authorized_pointers"] == ["/candidate/typicality"]
    assert call is not None
    assert output.candidates[0].content == f"atomic mechanism {REPAIRED_SLOT}"
    # Applied, not returned raw: the baseline carried typicality 2.0.
    assert output.candidates[0].typicality == pytest.approx(0.5)


def test_the_recovery_authority_admits_exactly_what_the_producer_can_write():
    """One vocabulary, shared by import — the defect's structural cause.

    Two hand-maintained sets are what drifted; asserting the reader's set
    equals a set DERIVED from the producer's own ``Literal`` is what keeps
    them from drifting again, because adding a mode to the producer without
    the reader now fails here rather than in a live run's cycle 2.
    """

    from typing import get_args, get_type_hints

    # Imported inside the test, not at module scope, so this file still
    # COLLECTS on a tree without the shared name and the behavioural
    # regression above fails on its own error rather than on an ImportError.
    from deepreason.llm.repair import V6_REPAIR_TASK_MODES

    producer = set(get_args(get_type_hints(V6RepairTurn)["mode"]))
    # ``initial`` is the pre-repair call, which writes no repair payload.
    assert producer == V6_REPAIR_TASK_MODES | {"initial"}
    assert V6_REPAIR_TASK_MODES == {"whole_object_syntax", "patch"}


def test_no_mode_name_survives_that_nothing_emits():
    """``full`` was accepted at an authority boundary and emitted nowhere."""

    import inspect

    from deepreason.workflow import nonconjecture_recovery

    source = inspect.getsource(nonconjecture_recovery)
    assert '"full"' not in source
    # The reader consumes the producer's type rather than restating it.
    assert "V6_REPAIR_TASK_MODES" in inspect.getsource(
        nonconjecture_recovery._repair_authority
    )
