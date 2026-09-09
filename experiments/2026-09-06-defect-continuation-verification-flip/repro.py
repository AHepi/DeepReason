"""The reproduction: a work order abandoned in flight, then closed by a resume.

Three states of ONE canonical root, built through the real v6 machinery
(`tests/test_v6_controller3_replay_verification._canonical_root`), each
verified by `verify_root`:

  admitted   the root as the run wrote it -- both calls admitted
  abandoned  truncated right after the second provider result: the work order
             is open, exactly as ARM R's three were when it died
  closed     the abandoned root with the closure a no-op continuation writes:
             a semantic admission `schema_exhausted` and a work terminal
             naming the SAME attempt, appended after the old tail

Expected on the unfixed tree, and the defect:
  admitted   0 violations
  abandoned  0 violations, the work id in `outstanding_work_orders`
  closed     attempt-validity, "failed call must contain no valid attempt"

    python repro.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.storage.objects import ObjectStore  # noqa: E402
from deepreason.workflow.transaction import (  # noqa: E402
    CompactRecoveryTransitionV1,
    SemanticAdmissionV1,
    WorkLifecycleTransitionV1,
    WorkTerminalV1,
    WorkTransitionKind,
)
from tests.test_v6_controller3_replay_verification import (  # noqa: E402
    _canonical_root,
    _log_rows,
    _write_log,
)


def _second_provider_seq(rows: list[dict]) -> int:
    seqs = [r["seq"] for r in rows if (r.get("control") or {}).get("action") == "provider_result"]
    assert len(seqs) == 2, seqs
    return seqs[1]


def abandoned_root(base: pathlib.Path, target: pathlib.Path) -> pathlib.Path:
    """The run dies right after a provider result: no admission, no terminal."""
    import shutil

    shutil.copytree(base, target)
    rows = _log_rows(target)
    cut = _second_provider_seq(rows)
    _write_log(target, [r for r in rows if r["seq"] <= cut])
    return target


def closed_root(abandoned: pathlib.Path, target: pathlib.Path) -> pathlib.Path:
    """The no-op continuation: close the open work order as schema_exhausted,
    referencing the attempt the original run already recorded. No model call,
    no new attempt -- exactly what the resume wrote at seqs 1171/1172 of
    run-c3f3bf10bc57d63e224a9f1c68bf1057."""
    import shutil

    shutil.copytree(abandoned, target)
    harness = Harness(target, read_only=True)
    rows = _log_rows(target)
    last = rows[-1]
    attempt = next(
        record
        for schema, record in (harness.objects.get(oid) for oid in last["outputs"])
        if schema == "workflow-provider-attempt-v1"
    )
    store = ObjectStore(target / "objects")
    admission = SemanticAdmissionV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        provider_attempt_ref=attempt.id,
        outcome="schema_exhausted",
        admitted_refs=(),
        diagnostic_refs=(),
        authorized_pointers=(),
    )
    admission_transition = WorkLifecycleTransitionV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        transition_kind=WorkTransitionKind.SEMANTIC_ADMISSION,
        trigger_ref=admission.id,
    )
    manifest_digest = json.loads((target / "run-manifest.sha256").read_text().strip()
                                 if False else "null") if False else (
        (target / "run-manifest.sha256").read_text().strip()
    )
    recovery = CompactRecoveryTransitionV1.create(
        manifest_digest=manifest_digest,
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        route_lease=attempt.route_lease,
        source_profile="standard",
        semantic_admission_ref=admission.id,
    )
    store.put("workflow-compact-recovery-transition-v1", recovery)
    terminal = WorkTerminalV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        status="schema_exhausted",
        usage_status=attempt.usage_status,
        prompt_tokens=attempt.prompt_tokens,
        completion_tokens=attempt.completion_tokens,
        provider_attempt_ref=attempt.id,
        semantic_admission_ref=admission.id,
        reason_code="recovered_schema_exhausted",
        compact_recovery_transition_ref=recovery.id,
    )
    terminal_transition = WorkLifecycleTransitionV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        transition_kind=WorkTransitionKind.WORK_TERMINATED,
        trigger_ref=terminal.id,
    )
    store.put("workflow-semantic-admission-v1", admission)
    store.put("workflow-work-lifecycle-transition-v1", admission_transition)
    store.put("workflow-work-terminal-v1", terminal)
    store.put("workflow-work-lifecycle-transition-v1", terminal_transition)

    def control_row(seq, record, transition, extra=()):
        outputs = [*[item.id for item in extra], record.id, transition.id]
        return {
            "seq": seq,
            "ts": last["ts"],
            "rule": "Control",
            "inputs": [transition.work_id, transition.trigger_ref],
            "outputs": list(outputs),
            "llm": None,
            "state_diff": {"att+": [], "dep+": [], "A+": [], "Π+": [],
                           "status_changed": [], "hv_set": {}, "reach_set": {},
                           "addr+": [], "carry+": []},
            "control": {
                "schema": "control.event.v3",
                "action": "work_transition",
                "decision_ref": transition.id,
                "inputs": [transition.work_id, transition.trigger_ref],
                "outputs": list(outputs),
            },
        }

    seq = rows[-1]["seq"]
    rows.append(control_row(seq + 1, admission, admission_transition))
    rows.append(control_row(seq + 2, terminal, terminal_transition, extra=(recovery,)))
    _write_log(target, rows)
    return target


def report(name: str, root: pathlib.Path) -> dict:
    result = verify_root(root)
    violations = result.get("violations", [])
    stats = result.get("stats", {})
    print(f"{name:<10} violations={len(violations)}  "
          f"outstanding_work_orders={stats.get('outstanding_work_orders')}")
    for item in violations:
        print(f"           {item['check']}: {item['detail'][:96]}")
    return {"violations": violations, "stats": stats}


def main() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp())
    base = _canonical_root(tmp)
    admitted = report("admitted", base)
    abandoned = report("abandoned", abandoned_root(base, tmp / "abandoned"))
    closed = report("closed", closed_root(tmp / "abandoned", tmp / "closed"))

    checks = lambda r: {v["check"] for v in r["violations"]}  # noqa: E731
    ok = (
        not checks(admitted)
        and not checks(abandoned)
        and abandoned["stats"].get("outstanding_work_orders")
        and checks(closed) == {"attempt-validity"}
    )
    print()
    print("REPRODUCED" if ok else "NOT REPRODUCED",
          "- the same wire-valid call verifies clean while its work order is",
          "open and violates once the work order is honestly closed"
          if ok else "- see the rows above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
