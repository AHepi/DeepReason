"""Block A audit: refutation rate, criticism calls/tokens per accepted
artifact, survival (stop_reason), and criticism-coverage debt at
natural stop -- all from the typed record only (run-status.json,
verify_root, Harness log/objects). Model prose is never evidence here.

Usage: python3 block_a_audit.py ROOT CELL Q_IDX SEED_IDX
"""

import json
import sys
from pathlib import Path

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.ontology.event import Rule
from deepreason.ontology.state import Status

root = Path(sys.argv[1])
cell = sys.argv[2]
q_idx = sys.argv[3]
seed_idx = sys.argv[4]
out = {"root": str(root), "cell": cell, "q_idx": q_idx, "seed_idx": seed_idx}

status_json = json.loads((root / "run-status.json").read_text())
out["state"] = status_json.get("state")
out["stop_reason"] = status_json.get("stop_reason")

verdict = verify_root(root)
out["verify_violations"] = [v["check"] for v in verdict["violations"]]
out["replay_valid"] = not verdict["violations"]

harness = Harness(root, read_only=True)
events = list(harness.log.read())

# -- refutation rate (Status enum: ACCEPTED, REFUTED, SUSPENDED, SUSPENDED_UNSUPPORTED) --
status_counts = {}
for aid, s in harness.state.status.items():
    status_counts[s.value] = status_counts.get(s.value, 0) + 1
out["artifact_status_counts"] = status_counts
out["artifact_total"] = len(harness.state.artifacts)
accepted = status_counts.get(Status.ACCEPTED.value, 0)
refuted = status_counts.get(Status.REFUTED.value, 0)
out["refutation_rate"] = (refuted / (accepted + refuted)) if (accepted + refuted) else None
accepted_ids = {aid for aid, s in harness.state.status.items() if s == Status.ACCEPTED}

# -- criticism calls: role == argumentative_critic --
crit_calls_by_seq = {}
for e in events:
    if e.llm is not None and e.llm.role == "argumentative_critic":
        crit_calls_by_seq[e.seq] = e.llm

# -- link criticism calls to targets via CriticismAttemptV1 objects --
attempts = []
for e in events:
    if e.rule == Rule.MEASURE and e.inputs and e.inputs[0] == "criticism.attempt.v1":
        _, obj = harness.objects.get(e.outputs[0], "criticism-attempt-v1")
        attempts.append(obj)

calls_per_accepted = {aid: 0 for aid in accepted_ids}
tokens_per_accepted = {aid: 0 for aid in accepted_ids}
for att in attempts:
    if att.target_id not in accepted_ids:
        continue
    call = crit_calls_by_seq.get(att.source_call_seq)
    calls_per_accepted[att.target_id] += 1
    if call is not None:
        tokens_per_accepted[att.target_id] += call.tokens

n_accepted = len(accepted_ids) or 1
out["criticism_calls_per_accepted_artifact_mean"] = sum(calls_per_accepted.values()) / n_accepted
out["criticism_tokens_per_accepted_artifact_mean"] = sum(tokens_per_accepted.values()) / n_accepted
out["criticism_call_count_total"] = len(crit_calls_by_seq)
out["criticism_token_total"] = sum(c.tokens for c in crit_calls_by_seq.values())

# -- coverage debt at natural stop: terminal record per target_id --
debt_by_target = {}
for e in events:
    if e.rule == Rule.MEASURE and e.inputs and e.inputs[0] == "criticism.coverage-debt.v1":
        _, obj = harness.objects.get(e.outputs[0], "criticism-coverage-debt-v1")
        debt_by_target[obj.target_id] = (e.seq, obj)  # last write per target wins

outstanding_total = 0
completed_total = 0
targets_with_outstanding = 0
for target_id, (seq, obj) in debt_by_target.items():
    outstanding_total += len(obj.outstanding_school_ids)
    completed_total += len(obj.completed_school_ids)
    if obj.outstanding_school_ids:
        targets_with_outstanding += 1

out["coverage_debt_targets"] = len(debt_by_target)
out["coverage_debt_outstanding_total"] = outstanding_total
out["coverage_debt_completed_total"] = completed_total
out["coverage_debt_targets_with_outstanding"] = targets_with_outstanding
# In CROSS cell every criticism obligation is definitionally foreign
# (conjecture is seat-bound off the default critic model); in SELF
# cell every obligation is definitionally self. PREREG.yaml records
# this operationalization -- no per-call model attribution needed to
# label the cell's debt as foreign vs self, only the cell identity.
out["foreign_criticism_debt_at_natural_stop"] = outstanding_total if cell == "cross" else None
out["self_criticism_debt_at_natural_stop"] = outstanding_total if cell == "self" else None

out["events_total"] = len(events)

print(json.dumps(out, indent=2, sort_keys=True))
