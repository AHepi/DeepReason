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
    sub.add_parser(
        "evidence", help="full dossier for an artifact: warrants, verdicts, "
                         "browser/vision evidence, LLM calls, dependencies"
    ).add_argument("id")
    blob_cmd = sub.add_parser("blob", help="dump a blob by ref (or unique prefix)")
    blob_cmd.add_argument("ref")
    blob_cmd.add_argument("--out", default=None,
                          help="write bytes to this file (required for binary blobs)")
    sub.add_parser("signals", help="list every log signal kind with meaning and count")
    export_cmd = sub.add_parser(
        "export", help="write surviving deliverables (app files, screenshots, README) to a directory"
    )
    export_cmd.add_argument("--out", required=True, help="output directory")
    export_cmd.add_argument("--id", default=None,
                            help="artifact id prefix (default: all surviving deliverables)")
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
    trace_cmd = sub.add_parser("trace", help="print the events touching an id")
    trace_cmd.add_argument("id")
    trace_cmd.add_argument("--json", action="store_true",
                           help="raw event JSON lines (legacy format)")
    narrate_cmd = sub.add_parser(
        "narrate", help="render the event log as chain-of-thought prose (view, spec 8)"
    )
    narrate_cmd.add_argument("--window", type=int, default=None,
                             help="only the last N events")
    narrate_cmd.add_argument("--upto", type=int, default=None,
                             help="only events up to seq N (time-travel narration)")
    return parser


def _resolve(harness: Harness, prefix: str) -> str:
    from deepreason.ops import resolve_prefix

    try:
        return resolve_prefix(harness, prefix)
    except ValueError as e:
        raise SystemExit(str(e)) from e


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
        print(why(_resolve(harness, args.id), harness.state, harness.warrants))
        return 0

    if args.command == "evidence":
        from deepreason.views.evidence import evidence

        harness = Harness(Path(args.root))
        print(evidence(harness, _resolve(harness, args.id)))
        return 0

    if args.command == "blob":
        harness = Harness(Path(args.root))
        try:
            ref = harness.blobs.resolve_prefix(args.ref)
        except (KeyError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 1
        data = harness.blobs.get(ref)
        if args.out:
            Path(args.out).write_bytes(data)
            print(f"wrote {len(data)} bytes to {args.out}")
            return 0
        kind = "image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else None
        if kind is None:
            try:
                print(data.decode("utf-8"))
                return 0
            except UnicodeDecodeError:
                kind = "binary"
        print(f"({kind}, {len(data)} bytes — pass --out FILE to write it)",
              file=sys.stderr)
        return 1

    if args.command == "signals":
        from collections import Counter

        from deepreason.signals import PREFIXES, SIGNALS, event_signal, family

        harness = Harness(Path(args.root))
        counts: Counter[str] = Counter()
        for event in harness.log.read():
            signal = event_signal(event)
            if signal is not None:
                counts[family(signal)] += 1
        for name, meaning in {**SIGNALS, **{k + "*": v for k, v in PREFIXES.items()}}.items():
            print(f"{counts.get(name, 0):6}  {name}: {meaning}")
        unregistered = {k: n for k, n in counts.items()
                        if k not in SIGNALS and not k.endswith("*")}
        for name, n in sorted(unregistered.items()):
            print(f"{n:6}  {name}: (unregistered signal)")
        return 0

    if args.command == "export":
        from deepreason.views.export import export_run, render_export_summary

        harness = Harness(Path(args.root))
        artifact_id = _resolve(harness, args.id) if args.id else None
        paths = export_run(harness, args.out, artifact_id)
        print(render_export_summary(paths))
        return 0

    if args.command == "trace":
        from deepreason.signals import describe, event_signal

        harness = Harness(Path(args.root))
        found = False
        for event in harness.log.read():
            ids = list(event.inputs) + list(event.outputs)
            if not any(i.startswith(args.id) for i in ids):
                continue
            found = True
            if args.json:
                print(event.model_dump_json(by_alias=True))
                continue
            signal = event_signal(event)
            what = (f"{signal} — {describe(signal)[:60]}" if signal
                    else f"{', '.join(i[:12] for i in event.inputs) or '-'} -> "
                         f"{', '.join(o[:12] for o in event.outputs) or '-'}")
            llm = (f"  [llm {event.llm.role}/{event.llm.model} "
                   f"tok={event.llm.tokens}]" if event.llm else "")
            print(f"#{event.seq:<5} {event.ts[:19]} {event.rule.value:<8} {what}{llm}")
        if not found:
            print(f"(no events touching {args.id!r})")
        return 0

    if args.command == "theory":
        harness = Harness(Path(args.root))
        print(theory(_resolve(harness, args.id), harness.state, harness.blobs, log=harness.log))
        return 0

    if args.command == "narrate":
        from deepreason.views.narrate import narrate

        harness = Harness(Path(args.root))
        print(narrate(harness, window=args.window, upto_seq=args.upto))
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
            "evidence_lambda": detection.evidence_lambda(harness),
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
            standards = ", ".join(entry["standards"]) or "none (appellate_rule not applicable)"
            print(f"{entry['case']}  score={entry['score']}  {', '.join(entry['kinds'])}  "
                  f"standards: {standards}")
        return 0

    if args.command == "rule":
        from deepreason.informal.appellate import rule as appellate_rule

        harness = Harness(Path(args.root))
        try:
            precedent = appellate_rule(harness, args.case_id, args.holding, args.standard)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1
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
    from deepreason.ops import seed_problem_payload

    if path.suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(path.read_text())
    else:
        data = json.loads(path.read_text())
    return seed_problem_payload(harness, data).id


def _cmd_run(args) -> int:
    from deepreason.config import load as load_config
    from deepreason.ops import run_scheduler

    cycles = int(args.budget.split("=", 1)[1]) if "=" in args.budget else int(args.budget)
    config = load_config(Path(args.config) if args.config else None)
    harness = Harness(Path(args.root))
    if args.problem:
        _load_problem_file(harness, Path(args.problem))
    if not harness.state.problems:
        print("no problem on the frontier; pass --problem <file>", file=sys.stderr)
        return 1
    try:
        result, meter, accounting = run_scheduler(harness, config, cycles, args.token_budget)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    if accounting["delta"]:
        print(f"[accounting] WARNING: {accounting['delta']} metered tokens are "
              "not on the log — investigate before trusting metrics", file=sys.stderr)
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
