#!/usr/bin/env python3
"""Q4 probe -- the three lifecycle surfaces, read off each committed root.

P5 says `amend` accepts what `continue` refuses. P6 says `results` promises a
continue that `continue` refuses. Both reduce to two independent predicates
disagreeing:

  results   `application/results.py` -- amend_ready from the STOP RECORD's
            reason against `workflow/lifecycle.py:28 RESUMABLE_STOP_REASONS`
            = {"converged", "budget_exhausted"}.
  continue  `runtime/continuation.py:364` -- raises CONTINUE_TYPED_STOP_REQUIRED
            in the else of `if terminal is not None ... elif current_resume is
            not None`, i.e. when the WORKFLOW STATE carries neither a terminal
            lifecycle decision nor a resume decision.

This reports both inputs per root, read-only, so the disagreement is a fact
about the record rather than about a CLI invocation.

Usage: q4_lifecycle_surfaces.py <root> [<root> ...]
"""
import json
import pathlib
import sys

sys.path.insert(0, "src")
from deepreason.harness import Harness  # noqa: E402
from deepreason.workflow.lifecycle import RESUMABLE_STOP_REASONS  # noqa: E402


def report(root: pathlib.Path) -> dict:
    status = json.loads((root / "run-status.json").read_text())
    stop_path = root / "run-stop.json"
    stop = json.loads(stop_path.read_text()) if stop_path.exists() else None
    ws = Harness(root, read_only=True).workflow_state
    terminal = ws.terminal_lifecycle_decision
    resume = getattr(ws, "current_resume_decision", None)
    reason = (stop or {}).get("reason")
    return {
        "root": root.name,
        "state": status.get("state"),
        "status_stop_reason": status.get("stop_reason"),
        "stop_record_reason": reason,
        "status_token_spend": status.get("token_spend"),
        # what `results` consults
        "reason_in_RESUMABLE_STOP_REASONS": reason in RESUMABLE_STOP_REASONS,
        # what `continue` consults
        "terminal_lifecycle_decision_present": terminal is not None,
        "lifecycle_decision_count": len(ws.lifecycle_decisions or {}),
        "current_resume_decision_present": resume is not None,
        "terminal_commitment_present": ws.current_terminal_commitment is not None,
        "continue_would_raise_CONTINUE_TYPED_STOP_REQUIRED":
            terminal is None and resume is None,
        "surfaces_disagree":
            bool(reason in RESUMABLE_STOP_REASONS) and (terminal is None and resume is None),
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2))
