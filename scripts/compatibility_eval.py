#!/usr/bin/env python3
"""Run or summarize the preregistered DeepReason compatibility matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from deepreason.compat_eval import (
    CompatibilityEvaluationError,
    aggregate_report,
    import_offline_observations,
    load_checkpoint,
    load_matrix,
    load_optional_report,
    run_live_matrix,
    save_checkpoint,
    write_report,
)


DEFAULT_MATRIX = Path("experiments/website_compat_matrix_v1.json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run live profile trials or aggregate explicitly offline/mock observations. "
            "Only complete live reports are eligible for A3-A10 verdicts."
        )
    )
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--phase", choices=("baseline", "candidate"), default="candidate")
    parser.add_argument("--frontier-baseline", type=Path)
    parser.add_argument("--verification", type=Path)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    live = subparsers.add_parser("live", help="invoke configured live providers")
    live.add_argument("--config", type=Path, required=True)
    live.add_argument("--work-dir", type=Path, required=True)
    live.add_argument("--single-model")
    live.add_argument("--profile", action="append", dest="profiles")
    live.add_argument("--prompt-id", action="append", dest="prompt_ids")
    live.add_argument(
        "--limit",
        type=int,
        help="shakedown only: run at most this many pending trials; coverage stays incomplete",
    )

    offline = subparsers.add_parser(
        "offline-mock", help="import fixtures without invoking a provider"
    )
    offline.add_argument("--observations", type=Path, required=True)

    subparsers.add_parser("report-only", help="regenerate a report from a checkpoint")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        matrix = load_matrix(args.matrix)
        evidence_class = "offline_mock" if args.mode == "offline-mock" else "live"
        if args.mode == "report-only":
            raw = json.loads(args.checkpoint.read_text(encoding="utf-8"))
            evidence_class = raw.get("evidence_class")
            if evidence_class not in ("live", "offline_mock"):
                raise CompatibilityEvaluationError(
                    "report-only checkpoint has no valid evidence_class"
                )
        checkpoint = load_checkpoint(
            args.checkpoint,
            matrix,
            phase=args.phase,
            evidence_class=evidence_class,
        )
        if args.mode == "live":
            if args.limit is not None and args.limit < 1:
                raise CompatibilityEvaluationError("--limit must be positive")
            checkpoint = run_live_matrix(
                matrix,
                checkpoint,
                checkpoint_path=args.checkpoint,
                config_path=args.config,
                work_dir=args.work_dir,
                profiles=args.profiles,
                prompt_ids=args.prompt_ids,
                single_model=args.single_model,
                limit=args.limit,
            )
        elif args.mode == "offline-mock":
            checkpoint = import_offline_observations(checkpoint, args.observations)
            save_checkpoint(args.checkpoint, checkpoint)

        baseline = load_optional_report(args.frontier_baseline)
        verification = load_optional_report(args.verification)
        report = aggregate_report(
            matrix,
            checkpoint,
            frontier_baseline=baseline,
            verification=verification,
        )
        write_report(args.report, report)
    except (CompatibilityEvaluationError, OSError, json.JSONDecodeError) as error:
        print(f"compatibility evaluation failed: {error}")
        return 2

    statuses = {
        criterion: verdict["status"]
        for criterion, verdict in report["acceptance"].items()
    }
    print(
        json.dumps(
            {
                "report": str(args.report),
                "evidence": report["evidence"]["class"],
                "coverage": {
                    profile: row["observed"] for profile, row in report["coverage"].items()
                },
                "acceptance": statuses,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
