"""CLI entry point (spec §13).

Commands: frontier · focus <id> · expand · attack <id> · step ·
run --budget <spec> · why <id> · theory <id> · prose <id> · docket ·
rule <case-id> · schools · capture · reseed <school-id> · merge <path> ·
trace <id>.

P0 wires the inspect commands (frontier, why, trace) against a harness
directory; loop/scheduler commands land with P1/P2.
"""

import argparse
import json
import sys
from pathlib import Path

from deepreason.harness import Harness
from deepreason.views.theory import theory
from deepreason.views.why import why


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deepreason",
        description="Conjecture-Criticism Harness (creativity-calculus spec v1.3)",
    )
    parser.add_argument(
        "--root", default=".deepreason", help="harness state directory (blobs, objects, log)"
    )
    parser.add_argument("--config", default=None, help="knob file (default: config/default.yaml)")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("frontier", help="show the problem frontier")
    sub.add_parser("focus", help="focus a problem/artifact").add_argument("id")
    sub.add_parser("expand", help="expand the focused node")
    sub.add_parser("attack", help="solicit criticism of an artifact").add_argument("id")
    sub.add_parser("step", help="apply one enabled rule under budget")
    run = sub.add_parser("run", help="run the full scheduler (Conj->Crit->Adj, schools, capture)")
    run.add_argument("--budget", required=True, help="cycles=<N> or plain <N>")
    run.add_argument("--problem", default=None, help="problem file (json/yaml) to register first")
    run.add_argument("--token-budget", type=int, default=None,
                     help="hard prompt+completion token ceiling (graceful stop)")
    sub.add_parser("mcp", help="serve the harness as MCP tools over stdio (install in any agent harness)")
    sub.add_parser("why", help="print the attack/defence chain justifying a status").add_argument("id")
    sub.add_parser("theory", help="render the theory view (spec 8)").add_argument("id")
    sub.add_parser("prose", help="render skeleton as narrative").add_argument("id")
    sub.add_parser("docket", help="disagreement-ranked user queue (spec 10.6)")
    rule_cmd = sub.add_parser("rule", help="enter an appellate ruling")
    rule_cmd.add_argument("case_id")
    rule_cmd.add_argument("--holding", required=True, help="the one-line holding")
    rule_cmd.add_argument("--standard", required=True, help="spec id the ruling calibrates")
    sub.add_parser("schools", help="rosters, centroid distances, stance weights")
    sub.add_parser("capture", help="both-surface capture dashboard (spec 11)")
    sub.add_parser("report", help="P6 eval report (valid-JSON, attack validity, trial guard, ...)")
    sub.add_parser("reseed", help="manual school reseed (logged)").add_argument("school_id")
    sub.add_parser("merge", help="merge another saved graph (G-Set union)").add_argument("path")
    sub.add_parser("trace", help="print the events touching an id").add_argument("id")
    return parser


def _resolve(harness: Harness, prefix: str) -> str:
    matches = [i for i in harness.state.artifacts if i.startswith(prefix)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return prefix
    raise SystemExit(f"ambiguous id prefix {prefix!r}: {[m[:12] for m in matches]}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command is None:
        build_parser().print_help()
        return 0

    if args.command == "frontier":
        harness = Harness(Path(args.root))
        if not harness.state.problems:
            print("(no problems registered)")
        for pid, problem in harness.state.problems.items():
            print(f"{pid}  [{problem.provenance.trigger.value}]  {problem.description}")
        return 0

    if args.command == "why":
        harness = Harness(Path(args.root))
        print(why(_resolve(harness, args.id), harness.state))
        return 0

    if args.command == "trace":
        harness = Harness(Path(args.root))
        found = False
        for event in harness.log.read():
            ids = list(event.inputs) + list(event.outputs)
            if any(i.startswith(args.id) for i in ids):
                print(event.model_dump_json(by_alias=True))
                found = True
        if not found:
            print(f"(no events touching {args.id!r})")
        return 0

    if args.command == "theory":
        harness = Harness(Path(args.root))
        print(theory(_resolve(harness, args.id), harness.state, harness.blobs, log=harness.log))
        return 0

    if args.command == "run":
        return _cmd_run(args)

    if args.command == "mcp":
        from deepreason.mcp_server import main as mcp_main

        return mcp_main()

    if args.command == "schools":
        from deepreason.capture import schools as schools_mod
        from deepreason.config import load as load_config

        harness = Harness(Path(args.root))
        config = load_config(Path(args.config) if args.config else None)
        roster = schools_mod.roster(harness)
        if not roster:
            print("(no schools registered)")
        for school_id in sorted(roster):
            policy = roster[school_id]
            weight = schools_mod.stance_weight(harness, school_id, config)
            lineage = schools_mod.lineage_size(harness, school_id)
            print(
                f"{school_id}  stance={policy['stance']}  weight={weight:.2f}  "
                f"lineage={lineage}  policy={policy['artifact_id'][:12]}"
            )
        return 0

    if args.command == "capture":
        from deepreason.capture import detection
        from deepreason.config import load as load_config
        from deepreason.llm.embedder import HashingEmbedder

        harness = Harness(Path(args.root))
        config = load_config(Path(args.config) if args.config else None)
        embedder = HashingEmbedder()
        window = config.CAPTURE_W
        dashboard = {
            "generator": detection.generator_metrics(harness, embedder, window),
            "adjudicator": detection.adjudicator_metrics(harness, window),
            "lambda": detection.grounding_lambda(harness, window),
            "raw_flags": detection.raw_flags(harness, embedder, config),
        }
        print(json.dumps(dashboard, indent=2, sort_keys=True))
        return 0

    if args.command == "report":
        from deepreason.config import load as load_config
        from deepreason.report import eval_report

        harness = Harness(Path(args.root))
        config = load_config(Path(args.config) if args.config else None)
        print(json.dumps(eval_report(harness, config), indent=2, sort_keys=True))
        return 0

    if args.command == "docket":
        from deepreason.config import load as load_config
        from deepreason.informal.appellate import docket

        harness = Harness(Path(args.root))
        config = load_config(Path(args.config) if args.config else None)
        entries = docket(harness, config)
        if not entries:
            print("(docket is empty)")
        for entry in entries:
            print(f"{entry['case']}  score={entry['score']}  {', '.join(entry['kinds'])}")
        return 0

    if args.command == "rule":
        from deepreason.informal.appellate import rule as appellate_rule

        harness = Harness(Path(args.root))
        precedent = appellate_rule(harness, args.case_id, args.holding, args.standard)
        print(f"precedent registered: {precedent.id[:12]}")
        return 0

    if args.command == "prose":
        from deepreason.views.prose import prose as prose_view

        harness = Harness(Path(args.root))
        print(prose_view(_resolve(harness, args.id), harness.state, harness.blobs))
        return 0

    if args.command == "merge":
        from deepreason.storage.merge import merge

        harness = Harness(Path(args.root))
        stats = merge(harness, Path(args.path))
        print(json.dumps(stats, sort_keys=True))
        return 0

    if args.command == "reseed":
        from deepreason.capture import schools as schools_mod

        harness = Harness(Path(args.root))
        roster = schools_mod.roster(harness)
        if args.school_id not in roster:
            print(f"unknown school: {args.school_id}", file=sys.stderr)
            return 1
        policy = schools_mod.reseed(
            harness, args.school_id, roster[args.school_id], reason="manual"
        )
        print(f"{args.school_id} reseeded: stance={policy['stance']}")
        return 0

    print(
        f"deepreason {args.command}: not implemented yet "
        "(see docs/harness-spec-v1.3.md, spec 16 phases)"
    )
    return 1


def _load_problem_file(harness: Harness, path: Path) -> str:
    from deepreason.ontology import Commitment, Problem

    if path.suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(path.read_text())
    else:
        data = json.loads(path.read_text())
    if data.get("standard"):
        from deepreason.informal.standards import register_standard

        std = data["standard"]
        register_standard(harness, std["id"], rubric=std["rubric"], mode=std.get("mode", "absolute"))
    for c in data.get("commitments", []):
        harness.register_commitment(Commitment.model_validate(c))
    if "skeleton-wf" in data.get("problem", {}).get("criteria", []) and (
        "skeleton-wf" not in harness.commitments
    ):
        from deepreason.informal.skeleton import skeleton_wf_commitment

        harness.register_commitment(skeleton_wf_commitment())
    problem = Problem.model_validate(data["problem"])
    harness.register_problem(problem)
    return problem.id


def _cmd_run(args) -> int:
    from deepreason.config import load as load_config
    from deepreason.llm.adapter import build_adapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.scheduler.scheduler import Scheduler

    cycles = int(args.budget.split("=", 1)[1]) if "=" in args.budget else int(args.budget)
    config = load_config(Path(args.config) if args.config else None)
    harness = Harness(Path(args.root))
    if args.problem:
        _load_problem_file(harness, Path(args.problem))
    if not harness.state.problems:
        print("no problem on the frontier; pass --problem <file>", file=sys.stderr)
        return 1
    meter = TokenMeter(budget=args.token_budget) if args.token_budget is not None else None
    adapter = build_adapter(config, harness.blobs, meter=meter)
    if not adapter.has_role("conjecturer"):
        print(
            "no conjecturer endpoint configured — set roles.conjecturer in the "
            "config knob file (spec 15)",
            file=sys.stderr,
        )
        return 1
    result = Scheduler(harness, adapter, config).run(cycles)
    print(f"survivors ({len(result['survivors'])}):")
    for aid in result["frontier"]:
        print(f"  {aid[:12]}  {harness.state.artifacts[aid].content_ref[:80]}")
    for note in result["diagnostics"]:
        print(f"  [note] {note}")
    if meter is not None:
        print(json.dumps(meter.snapshot(), sort_keys=True))
    if result["frontier"]:
        print()
        print(theory(result["frontier"][0], harness.state, harness.blobs, log=harness.log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
