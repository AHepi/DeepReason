"""Installed command-line interface for campaign coordination and audit.

The input plan is a ``campaign.plan.v2`` JSON document. Relative run roots
and working directories are resolved relative to the plan file. Omit a
command to audit an already-existing root without launching it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from deepreason.experiments.campaign import (
    CampaignCoordinator,
    load_campaign_plan,
    write_campaign_index,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run and dimensionally audit an autonomous-inquiry campaign"
    )
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="maximum concurrent roots within a wave (default: all roots)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.jobs is not None and args.jobs < 1:
        print("--jobs must be at least 1", file=sys.stderr)
        return 1
    try:
        plan = load_campaign_plan(args.plan)
        index = CampaignCoordinator(max_workers=args.jobs).run(plan)
        write_campaign_index(args.out, index)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"campaign configuration failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(index.to_dict(), indent=2, sort_keys=True))
    # A completed evidence package is produced even when the campaign stops
    # for a systemic finding; the index, not process status, carries that fact.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
