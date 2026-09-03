#!/usr/bin/env python3
"""The stop report, replayed over the recorded failures it was built for.

R18-R20 of `../REQUEST.md`. Eight cases across three branches: each must
land in the box the record supports, with the evidence quoted.

The roots are NOT copied into this branch. Each case names the branch and
the path it came from, and `--extract` re-materialises all of them
read-only with `git archive`, so this proof is re-runnable from a clean
checkout without duplicating tens of megabytes of committed evidence into
a second place.

The NAIVE classifier at the bottom is the instrument this tranche exists
to replace: it reads the settings file and blames the seat named in the
stop message, which is what a window does when it writes the first
failure report by hand. It lives HERE, outside the module it judges --
the treadle lesson in CLAUDE.md: keep whatever judges the work outside
the cone it judges.

    python run_regression.py --extract        # fetch the roots (read-only)
    python run_regression.py                  # the shipped classifier
    python run_regression.py --naive          # the classifier it replaces
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

PA1 = "claude/live-reasoning-p-a1-bv65kl"
PA2 = "claude/executor-live-run-p-a2-84hyco"
PH1 = "claude/executor-window-phase-1-s5ex6w"

# (case, branch, path under the branch, required first box, evidence that
#  must appear somewhere in the rendered report)
CASES = [
    (
        "P-A1 — seat exhaustion behind a transport wall",
        PA1, "experiments/2026-09-01-live-all-modules-p-a1/run",
        "ENVIRONMENT",
        ["RemoteDisconnected on endpoint ollama-glm-5.3",
         "terminally exhausted",
         "passed qualification 20/20 first-pass on conjecturer.turn.v6"],
        {"MODEL": "SUPPORTED"},
    ),
    (
        "P-A1 — qualification vindication (R9's second sentence)",
        PA1, "experiments/2026-09-01-live-all-modules-p-a1/run",
        "ENVIRONMENT",
        ["passed qualification 20/20"],
        {},
    ),
    (
        "P-A2 epoch 1 — one seat x form refused, and the knob is named",
        PA2, "experiments/2026-09-02-live-p-a2-corrected/unqualified-epoch1-run-e958a37b",
        "MODEL",
        ["grounding_reviewer#0 failed qualification on "
         "groundingrepairwirev1.direct.v1",
         "reasoning 'low'"],
        {},
    ),
    (
        "P-A2 epoch 2 — account usage cap",
        PA2, "experiments/2026-09-02-live-p-a2-corrected/ratelimited-epoch2-run-1b89ed64",
        "ENVIRONMENT",
        ["ENDPOINT_HTTP_429"],
        {"MODEL": "RULED OUT"},
    ),
    (
        "P-A2 epoch 3 — the harness box, earned by ruling out the others",
        PA2, "experiments/2026-09-02-live-p-a2-corrected/failed-epoch3-run-1b89ed64e050c354",
        "HARNESS",
        ["v6 conjecture context must be planned after durable work preparation"],
        {"CONFIGURATION": "RULED OUT", "ENVIRONMENT": "RULED OUT",
         "MODEL": "RULED OUT", "HARNESS": "SUPPORTED"},
    ),
    (
        "Phase-1 429 root — self-inflicted concurrency cap",
        PH1, "experiments/2026-09-03-change-provenance-history-channel/runs/"
             "home-default/runs/failed-429-run-fe00609058e10605590206d51ab2b7a0",
        "ENVIRONMENT",
        ["HTTP Error 429: Too Many Requests"],
        {},
    ),
    (
        "Phase-1 M3-C0 — 429 during qualification, no run root at all",
        PH1, "experiments/2026-09-03-change-provenance-history-channel/evidence-429",
        "ENVIRONMENT",
        ["ENDPOINT_HTTP_429"],
        {},
    ),
    (
        "Phase-1 M1-H0 — a CLEAN terminal attributes no box",
        PH1, "experiments/2026-09-03-change-provenance-history-channel/runs/"
             "home-default/runs/run-fe00609058e10605590206d51ab2b7a0",
        None,
        ["STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY", "continue: **REFUSED**"],
        {"CONFIGURATION": "RULED OUT", "ENVIRONMENT": "RULED OUT",
         "MODEL": "RULED OUT", "HARNESS": "RULED OUT"},
    ),
]


def extract(destination: Path) -> None:
    """Re-materialise every case's root READ-ONLY from its own branch."""

    destination.mkdir(parents=True, exist_ok=True)
    for branch in (PA1, PA2, PH1):
        paths = sorted({path for _, b, path, *_ in CASES if b == branch})
        archive = subprocess.run(
            ["git", "archive", f"origin/{branch}", *paths],
            cwd=REPO, capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", str(destination)],
                       input=archive, check=True)
        print(f"  extracted {len(paths)} path(s) from origin/{branch}")


def _m3c0_home(base: Path) -> Path:
    """M3-C0 produced no run root: `deepreason reason` refused with
    QUALIFICATION_TIER_SHALLOW. Its qualification record was kept by copy
    under evidence-429/, so present it as the home it describes."""

    home = Path(tempfile.mkdtemp(prefix="m3c0-home-")) / "home-c0"
    (home / "qualification-cache").mkdir(parents=True)
    source = base / "c0-unqualified-doctor.json"
    payload = json.loads(source.read_text())
    payload.setdefault("subject_digest", "c0-unqualified-doctor")
    (home / "qualification-cache" / "c0-unqualified-doctor.json").write_text(
        json.dumps(payload))
    return home


def naive_report(root: Path) -> tuple[str | None, str]:
    """The classifier this tranche replaces.

    It reads the settings the operator WROTE (the manifest's echo of the
    engine config, standing in for the YAML a window would have on hand)
    and blames whichever seat the stop message names -- never opening the
    qualification record. This is not a straw man: it is the shape of
    reasoning that produced "a conjecturer seat kept failing to fill a
    form" for a seat that had passed 20/20.
    """

    status = root / "run-status.json"
    if not status.is_file():
        return None, "no run-status.json: the naive reader has nothing to read"
    message = json.loads(status.read_text()).get("message") or ""
    manifest_path = root / "run-manifest.json"
    roles = []
    if manifest_path.is_file():
        roles = sorted(json.loads(manifest_path.read_text()).get("roles") or {})
    for role in roles:
        if role in message:
            return "MODEL", f"the stop message names the {role} seat"
    if "seat" in message.lower() or "capability" in message.lower():
        return "MODEL", "the stop message is about a seat"
    if message:
        return "HARNESS", "the stop message is not about a seat"
    return "HARNESS", "no stop message"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", default=os.environ.get("STOP_REPORT_ROOTS", ""),
                        help="directory holding the extracted branches")
    parser.add_argument("--extract", action="store_true",
                        help="re-materialise the roots read-only, then run")
    parser.add_argument("--naive", action="store_true",
                        help="run the classifier this tranche replaces")
    args = parser.parse_args()

    base = Path(args.roots) if args.roots else Path(
        tempfile.mkdtemp(prefix="stop-report-roots-"))
    if args.extract or not args.roots:
        print(f"extracting into {base}")
        extract(base)

    from deepreason.application.stop_report import render_stop_report, stop_report

    which = "NAIVE" if args.naive else "SHIPPED"
    print(f"\n=== {which} classifier over {len(CASES)} recorded cases ===\n")
    misfiled = 0
    for name, branch, path, expected, evidence, verdicts in CASES:
        target = base / path
        if path.endswith("evidence-429"):
            target = _m3c0_home(target)
        try:
            if args.naive:
                actual, why = naive_report(target)
                rendered = why
                boxes = {}
            else:
                report = stop_report(target)
                classification = report["sections"]["classification"]
                actual = classification["ranked"][0]
                if classification.get("clean_stop"):
                    actual = None
                rendered = render_stop_report(report)
                boxes = {b: v["verdict"]
                         for b, v in classification["boxes"].items()}
        except Exception as error:  # noqa: BLE001 - a failure to read is a result
            print(f"FAIL  {name}\n        could not report: {error}")
            misfiled += 1
            continue

        problems = []
        if actual != expected:
            problems.append(f"first box {actual!r}, expected {expected!r}")
        if not args.naive:
            for quote in evidence:
                if quote not in rendered:
                    problems.append(f"missing evidence: {quote!r}")
            for box, verdict in verdicts.items():
                if boxes.get(box) != verdict:
                    problems.append(
                        f"{box} verdict {boxes.get(box)!r}, expected {verdict!r}")
        if problems:
            misfiled += 1
            print(f"FAIL  {name}")
            for problem in problems:
                print(f"        {problem}")
        else:
            print(f"PASS  {name}")
            print(f"        first box: {actual}")

    print(f"\n{which}: {len(CASES) - misfiled}/{len(CASES)} correct, "
          f"{misfiled} misfiled")
    return 1 if (misfiled and not args.naive) else 0


if __name__ == "__main__":
    raise SystemExit(main())
