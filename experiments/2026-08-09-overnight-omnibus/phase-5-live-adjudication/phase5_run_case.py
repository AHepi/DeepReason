"""Phase 5: per-candidate procedure (PREREG-P5.yaml). Given a
validated hit's (root, artifact_a, artifact_b), this script:
  1. checks amendability on the ORIGINAL root (read-only, from the
     record -- see phase5_check_amendable.py's own logic, inlined here)
  2. if amendable: copies the root byte-for-byte into this phase's own
     directory (never amends the original, never mutates shared
     committed data)
  3. extracts both claims' verbatim text
  4. reshapes the question to surface the tension, quoting both claims
  5. runs `deepreason --root <copy> amend --reshape-question ...`
  6. runs `deepreason --root <copy> continue --budget cycles=10`
  7. audits: was a new attack edge minted, verdicts, replay_valid

No label is ever written by this script -- ordinary criticism (step 6)
is the only adjudicator, per O2's binding constraint.

Usage: python3 phase5_run_case.py CANDIDATE_INDEX ROOT ARTIFACT_A ARTIFACT_B OUT_DIR
Prints a JSON summary; non-amendable or refused candidates are
reported, not retried.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def check_amendable(root: Path) -> dict:
    from deepreason.amendment.apply import load_amendments, load_epoch_manifest
    from deepreason.runtime.terminal_authority import derive_terminal_authority

    try:
        committed = load_amendments(root)
        parent_epoch = len(committed)
        manifest = load_epoch_manifest(root, parent_epoch)
        authority = derive_terminal_authority(root, manifest=manifest)
        amendable = bool(
            authority.current_valid
            and authority.terminal_status in {"completed", "cancelled", "failed"}
        )
        return {
            "amendable": amendable,
            "status": authority.status,
            "terminal_status": authority.terminal_status,
        }
    except Exception as exc:  # noqa: BLE001
        return {"amendable": False, "check_error": f"{type(exc).__name__}: {exc}"}


def claim_text(root: Path, artifact_id: str) -> str:
    from deepreason.harness import Harness
    from deepreason.programs import content_text

    harness = Harness(root, read_only=True)
    return content_text(harness.state.artifacts[artifact_id], harness.blobs)


def run_cmd(args, out_path, err_path):
    with open(out_path, "w") as out, open(err_path, "w") as err:
        proc = subprocess.run(args, stdout=out, stderr=err)
    return proc.returncode


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:  # noqa: BLE001
        return {}


def attack_edges_against(root: Path, target_ids: set) -> list:
    from deepreason.harness import Harness

    harness = Harness(root, read_only=True)
    out = []
    for src, dst in harness.state.att:
        if dst in target_ids:
            out.append({"src": src, "dst": dst})
    return out


def main() -> None:
    idx = sys.argv[1]
    root = Path(sys.argv[2])
    artifact_a = sys.argv[3]
    artifact_b = sys.argv[4]
    out_dir = Path(sys.argv[5])
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {"candidate_index": idx, "original_root": str(root)}

    amendability = check_amendable(root)
    summary["amendability"] = amendability
    if not amendability["amendable"]:
        summary["outcome"] = "skipped_not_amendable"
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    claim_a = claim_text(root, artifact_a)
    claim_b = claim_text(root, artifact_b)
    summary["claim_a"] = claim_a
    summary["claim_b"] = claim_b

    copy_root = out_dir / f"candidate-{idx}-copy" / root.name
    copy_root.parent.mkdir(parents=True, exist_ok=True)
    if copy_root.exists():
        shutil.rmtree(copy_root)
    shutil.copytree(root, copy_root)
    summary["copy_root"] = str(copy_root)

    pre_attack_edges = attack_edges_against(copy_root, {artifact_a, artifact_b})
    summary["attack_edges_before"] = pre_attack_edges

    question = (
        "A prior measurement pass flagged a possible tension between two claims "
        "already accepted within this run's own record. Claim A states: "
        f"\"{claim_a}\" Claim B states: \"{claim_b}\" Determine, through ordinary "
        "criticism, whether these two claims can both be true together, or "
        "whether one must be refuted. If they are consistent, say what "
        "distinguishes the appearance of contradiction from a genuine one."
    )
    (out_dir / f"candidate-{idx}-question.txt").write_text(question)

    amend_rc = run_cmd(
        ["deepreason", "--root", str(copy_root), "amend", "--reshape-question", question, "--allow-partial"],
        out_dir / f"candidate-{idx}-amend.json",
        out_dir / f"candidate-{idx}-amend.err",
    )
    summary["amend_rc"] = amend_rc
    amend_out = read_json(out_dir / f"candidate-{idx}-amend.json")
    amend_err_text = (out_dir / f"candidate-{idx}-amend.err").read_text()
    if amend_rc != 0:
        summary["outcome"] = "amend_refused"
        summary["amend_refusal"] = amend_err_text.strip() or amend_out
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    continue_rc = run_cmd(
        ["deepreason", "--root", str(copy_root), "continue", "--budget", "cycles=10"],
        out_dir / f"candidate-{idx}-continue.json",
        out_dir / f"candidate-{idx}-continue.err",
    )
    summary["continue_rc"] = continue_rc

    from deepreason.invariants import verify_root

    status = read_json(copy_root / "run-status.json")
    summary["state"] = status.get("state")
    summary["stop_reason"] = status.get("stop_reason")
    verdict = verify_root(copy_root)
    summary["replay_valid"] = not verdict["violations"]
    summary["verify_violations"] = [v["check"] for v in verdict["violations"]]

    post_attack_edges = attack_edges_against(copy_root, {artifact_a, artifact_b})
    summary["attack_edges_after"] = post_attack_edges
    new_edges = [e for e in post_attack_edges if e not in pre_attack_edges]
    summary["new_attack_edges_minted"] = new_edges
    summary["refutation_occurred"] = bool(new_edges)
    summary["outcome"] = "adjudicated"

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
