"""CLI entry point (spec §13).

Commands: frontier · focus <id> · expand · attack <id> · step ·
run --budget <spec> · why <id> · theory <id> · prose <id> · docket ·
rule <case-id> · schools · capture · reseed <school-id> · merge <path> ·
trace <id>.
"""

import argparse
import sys

COMMANDS = (
    "frontier", "focus", "expand", "attack", "step", "run", "why", "theory",
    "prose", "docket", "rule", "schools", "capture", "reseed", "merge", "trace",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deepreason",
        description="Conjecture-Criticism Harness (creativity-calculus spec v1.3)",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("frontier", help="show the problem frontier")
    sub.add_parser("focus", help="focus a problem/artifact").add_argument("id")
    sub.add_parser("expand", help="expand the focused node")
    sub.add_parser("attack", help="solicit criticism of an artifact").add_argument("id")
    sub.add_parser("step", help="apply one enabled rule under budget")
    run = sub.add_parser("run", help="run until budget exhaustion")
    run.add_argument("--budget", required=True)
    sub.add_parser("why", help="print the attack/defence chain justifying a status").add_argument("id")
    sub.add_parser("theory", help="render the theory view (spec 8)").add_argument("id")
    sub.add_parser("prose", help="render skeleton as narrative").add_argument("id")
    sub.add_parser("docket", help="disagreement-ranked user queue (spec 10.6)")
    sub.add_parser("rule", help="enter an appellate ruling").add_argument("case_id")
    sub.add_parser("schools", help="rosters, centroid distances, stance weights")
    sub.add_parser("capture", help="both-surface capture dashboard (spec 11)")
    sub.add_parser("reseed", help="manual school reseed (logged)").add_argument("school_id")
    sub.add_parser("merge", help="merge another saved graph (G-Set union)").add_argument("path")
    sub.add_parser("trace", help="replay an artifact's history").add_argument("id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command is None:
        build_parser().print_help()
        return 0
    print(f"deepreason {args.command}: not implemented yet (see docs/harness-spec-v1.3.md, spec 16 phases)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
