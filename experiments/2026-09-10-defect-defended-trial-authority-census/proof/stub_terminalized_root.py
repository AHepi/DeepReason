"""The same stub, taken all the way to a published terminal.

Why this exists beside `stub_defended_trial_root.py`: the defect does not stop
at the derived finding. When a run reaches its terminal, `terminalize_text_run`
asks the same reader for a verification summary and FREEZES the answer into
`run-result.json`. So a completed defended-trial run stores
`security_valid: false` about itself, and the report then re-reports that stored
answer as a second, separate `run-result-verification` security finding.

That is why the fix cannot make an ALREADY-COMMITTED completed run report
`valid: true`: the record is law, the stored summary was written by the
defective reader, and it must not be edited. What the fix must make true is
that a run completed on the fixed code stores `security_valid: true`. This
script is that proof, and it is the one the goal's headline is about.

    python .../stub_terminalized_root.py <tmpdir>
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import stub_defended_trial_root as stub  # noqa: E402


def build_terminalized(root: pathlib.Path, cycles: int = 1) -> dict:
    from deepreason.application.text_runs import terminalize_text_run
    from deepreason.harness import Harness
    from deepreason.run_manifest import load_run_manifest

    stub.build(root, cycles)
    harness = Harness(root)
    manifest = load_run_manifest(root / "run-manifest.json")
    return terminalize_text_run(
        harness,
        manifest,
        root=root,
        result={"frontier": [], "survivors": []},
        accounting={"logged_tokens": 0},
        problem_id=stub.PROBLEM_ID,
        cancelled=False,
        latest_cycle=cycles,
    )


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1])
    payload = build_terminalized(target, int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    out = stub.report(target)
    out["state"] = payload.get("state")
    out["stored_run_result_verification"] = payload.get("verification")
    print(json.dumps(out, indent=2, sort_keys=True))
