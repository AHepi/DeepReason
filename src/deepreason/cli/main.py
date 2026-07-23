"""Public V6 command-line facade and advanced bound-root operations."""

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
    parser.add_argument(
        "--config", default=None,
        help="partial YAML profile (default: built-in typed defaults)",
    )
    parser.add_argument(
        "--provider-profile",
        default=None,
        help="explicit secret-free provider profile (overrides DEEPREASON_PROFILE)",
    )
    sub = parser.add_subparsers(dest="command")
    from deepreason.cli.bridge import register_bridge_commands
    from deepreason.cli.scratch import register_scratch_parser

    register_scratch_parser(sub)
    register_bridge_commands(sub)
    setup_cmd = sub.add_parser(
        "setup", help="configure one trusted provider profile and credential reference"
    )
    setup_cmd.add_argument("--provider", default=None)
    setup_cmd.add_argument("--endpoint", default=None)
    setup_cmd.add_argument("--model", default=None)
    setup_cmd.add_argument("--model-revision", default=None)
    setup_cmd.add_argument("--family", default=None)
    setup_cmd.add_argument("--context-window-tokens", type=int, default=None)
    setup_cmd.add_argument("--maximum-completion-tokens", type=int, default=None)
    setup_cmd.add_argument("--credential-env", default=None)
    qualify_cmd = sub.add_parser(
        "qualify", help="explicitly qualify the configured V6 provider contract"
    )
    qualify_cmd.add_argument(
        "--yes",
        action="store_true",
        help="confirm the provider/model and announced maximum call count",
    )
    qualify_cmd.add_argument("--json", action="store_true")
    status_cmd = sub.add_parser("status", help="show provider and V6 qualification readiness")
    status_cmd.add_argument("--json", action="store_true")
    config_cmd = sub.add_parser(
        "config", help="print source config, or compile/inspect a frozen RunManifest"
    )
    config_sub = config_cmd.add_subparsers(dest="config_command")
    compile_cmd = config_sub.add_parser(
        "compile", help="resolve source configuration into a canonical RunManifest"
    )
    compile_cmd.add_argument("--single-model", default=None,
                             help="assign this exact concrete model route to every active role")
    compile_cmd.add_argument("--judge-family", default=None,
                             help="configured endpoint id, model id, URL, or family for seat 2")
    compile_cmd.add_argument("--profile", choices=("compact", "standard", "frontier"),
                             default=None, help="model-facing presentation profile "
                             "(default: explicit config, then doctor recommendation)")
    compile_cmd.add_argument("--engine-profile", choices=("mini", "full"), default="full")
    compile_cmd.add_argument(
        "--workload-profile", choices=("text", "code", "formal", "website"), default=None
    )
    compile_cmd.add_argument("--pack-profile", default=None)
    compile_cmd.add_argument("--output-profile", default=None)
    compile_cmd.add_argument(
        "--control-plane-policy",
        default=None,
        help="complete ControlPlanePolicyV3 JSON file required by RunManifest v6",
    )
    compile_cmd.add_argument(
        "--run-input-digest",
        default=None,
        help="exact frozen RunInputManifestV2 digest required by RunManifest v6",
    )
    compile_cmd.add_argument(
        "--rubric-policy", choices=("forbid", "require_cross_family"),
        default="require_cross_family",
    )
    compile_cmd.add_argument("--concurrency", type=int, default=None)
    compile_cmd.add_argument("--out", required=True, help="canonical manifest output path")
    compile_cmd.add_argument("--dry-run", action="store_true",
                             help="print the resolved matrix without writing it")
    inspect_cmd = config_sub.add_parser(
        "inspect", help="verify and print a compiled RunManifest"
    )
    inspect_cmd.add_argument("--run-manifest", required=True)
    input_cmd = sub.add_parser(
        "input", help="freeze a typed problem and its criteria before manifest compilation"
    )
    input_sub = input_cmd.add_subparsers(dest="input_command", required=True)
    freeze_cmd = input_sub.add_parser(
        "freeze", help="bind an immutable RunInputManifestV2 to --root"
    )
    freeze_cmd.add_argument(
        "--problem", required=True, help="deepreason-text-workload-v1 YAML/JSON"
    )
    freeze_cmd.add_argument(
        "--dossier",
        default=None,
        help="optional canonical evidence-dossier.v1 JSON already staged under --root",
    )
    doctor_cmd = sub.add_parser(
        "doctor", help="preflight one exact endpoint/model and run deterministic capability probes"
    )
    doctor_cmd.add_argument("--endpoint", default=None,
                            help="endpoint URL, endpoint_id, or configured role name")
    doctor_cmd.add_argument("--model", default=None, help="exact concrete model id")
    doctor_cmd.add_argument("--provider", default=None)
    doctor_cmd.add_argument("--family", default=None)
    doctor_cmd.add_argument("--api-key-env", default=None)
    doctor_cmd.add_argument("--revision", default=None,
                            help="exact provider model revision when available")
    doctor_cmd.add_argument("--dry-run", action="store_true",
                            help="validate identity without contacting /models")
    doctor_cmd.add_argument(
        "--run-manifest",
        default=None,
        help="exact RunManifest v6 to qualify (requires --production-contracts)",
    )
    doctor_cmd.add_argument(
        "--production-contracts",
        action="store_true",
        help="exercise every frozen v6 production route/contract pair",
    )
    doctor_cmd.add_argument(
        "--out",
        default=None,
        help="deterministic production-contract qualification report path",
    )
    reason_cmd = sub.add_parser(
        "reason", help="prepare and reason over one normal question"
    )
    reason_cmd.add_argument("question", help="the question DeepReason should examine")
    reason_cmd.add_argument("--cycles", type=int, default=None)
    reason_cmd.add_argument("--token-budget", type=int, default=None)
    sub.add_parser(
        "mcp-registration",
        help="print generic secret-free MCP stdio registration JSON",
    )
    skills_cmd = sub.add_parser(
        "skills", help="snapshot and retrieve from explicit advisory skill capsules"
    )
    skills_cmd.add_argument("--capsule", action="append", required=True)
    skills_cmd.add_argument("--query", required=True)
    skills_cmd.add_argument("--school", action="append", default=[])
    skills_cmd.add_argument("--top-k", type=int, default=12)
    distill_cmd = sub.add_parser(
        "distill", help="distill one verified accepted source into a positive skill capsule"
    )
    distill_cmd.add_argument("--source", required=True, help="source run root")
    distill_cmd.add_argument("--seq", required=True, type=int, help="source event fence")
    distill_cmd.add_argument("--artifact", required=True, help="accepted source artifact id")
    distill_cmd.add_argument("--draft", required=True, help="positive capsule draft JSON/YAML")
    distill_cmd.add_argument("--out", required=True, help="capsule JSON output")
    brain_cmd = sub.add_parser("brain", help="manage an explicit local advisory-memory store")
    brain_sub = brain_cmd.add_subparsers(dest="brain_command", required=True)
    brain_sub.add_parser("init").add_argument("path")
    brain_ingest = brain_sub.add_parser("ingest")
    brain_ingest.add_argument("path")
    brain_ingest.add_argument("files", nargs="+")
    brain_distill = brain_sub.add_parser("distill-run")
    brain_distill.add_argument("path")
    brain_distill.add_argument("--source", required=True)
    brain_distill.add_argument("--seq", required=True, type=int)
    brain_distill.add_argument("--artifact", required=True)
    brain_distill.add_argument("--lesson", required=True, help="constructive lesson JSON/YAML")
    brain_query = brain_sub.add_parser("query")
    brain_query.add_argument("path")
    brain_query.add_argument("query")
    brain_query.add_argument("--day", default=None, help="fixed retrieval day (YYYY-MM-DD)")
    brain_inspect = brain_sub.add_parser("inspect")
    brain_inspect.add_argument("path")
    brain_inspect.add_argument("id", nargs="?")
    for command_name in ("reinforce", "pin", "unpin"):
        brain_record = brain_sub.add_parser(command_name)
        brain_record.add_argument("path")
        brain_record.add_argument("id")
        if command_name == "pin":
            brain_record.add_argument("--floor", type=float, default=1.0)
    brain_sub.add_parser("reindex").add_argument("path")
    continue_cmd = sub.add_parser(
        "continue", help="continue a stopped run under its bound immutable manifest"
    )
    continue_cmd.add_argument(
        "--budget", required=True, help="cycles=<N>|unlimited"
    )
    continue_cmd.add_argument(
        "--token-budget", default="unlimited", help="positive integer or unlimited"
    )
    continue_cmd.add_argument("--expected-manifest-digest", default=None)
    watch_cmd = sub.add_parser("watch", help="watch read-only structured run progress")
    watch_cmd.add_argument("--once", action="store_true", help="render one snapshot and exit")
    watch_cmd.add_argument("--interval", type=float, default=0.25)
    sub.add_parser(
        "cancel", help="request cancellation at the next completed-cycle boundary"
    )
    sub.add_parser("frontier", help="show the problem frontier")
    run = sub.add_parser("run", help="run the full scheduler (Conj->Crit->Adj, schools, capture)")
    run.add_argument("--budget", required=True, help="cycles=<N> or plain <N>")
    run.add_argument("--problem", default=None, help="problem file (json/yaml) to register first")
    run.add_argument("--token-budget", type=int, default=None,
                     help="hard prompt+completion token ceiling (graceful stop)")
    run.add_argument("--run-manifest", default=None,
                     help="precompiled immutable role matrix")
    run.add_argument("--dry-run", action="store_true",
                     help="resolve and print the exact role matrix; make no model call")
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
    sub.add_parser("research", help="open evidence requests awaiting retrieval (spec 12)")
    submit_cmd = sub.add_parser(
        "submit-evidence",
        help="register CANDIDATE evidence for a research problem (coverage "
             "is derived under criticism, never granted by submission)")
    submit_cmd.add_argument("problem_id")
    submit_cmd.add_argument("--source", required=True, help="source identifier or URL")
    submit_cmd.add_argument("--file", required=True, help="file holding the retrieved text")
    submit_cmd.add_argument("--retrieved-at", default=None,
                            help="claimed retrieval time (stored as claim metadata only)")
    submit_cmd.add_argument("--title", default=None)
    submit_cmd.add_argument("--user", action="store_true",
                            help="the evidence was genuinely supplied by the human user "
                                 "(default provenance is 'import' for agent material)")
    fail_cmd = sub.add_parser(
        "report-research-failure",
        help="record a failed retrieval attempt (operational event, never evidence)")
    fail_cmd.add_argument("problem_id")
    fail_cmd.add_argument("--source", required=True, help="attempted source or query")
    fail_cmd.add_argument("--reason", required=True)
    fail_cmd.add_argument("--category", default="fetch-error")
    rule_cmd = sub.add_parser("rule", help="enter an appellate ruling")
    rule_cmd.add_argument("case_id")
    rule_cmd.add_argument("--holding", required=True, help="the one-line holding")
    rule_cmd.add_argument("--standard", required=True, help="spec id the ruling calibrates")
    sub.add_parser("schools", help="rosters, centroid distances, stance weights")
    calibrate_cmd = sub.add_parser(
        "calibrate", help="distance-threshold calibration for an embedder on this "
                          "corpus (planted duplicates vs siblings vs unrelated)"
    )
    calibrate_cmd.add_argument(
        "--model", default=None,
        help="fastembed model id (default: the config's EMBEDDER_MODEL, "
             "else the hashing embedder)")
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


_ROOT_ADMISSION_COMMANDS = frozenset(
    {
        "blob",
        "calibrate",
        "cancel",
        "capture",
        "continue",
        "docket",
        "evidence",
        "export",
        "frontier",
        "merge",
        "narrate",
        "prose",
        "report",
        "report-research-failure",
        "research",
        "reseed",
        "rule",
        "schools",
        "signals",
        "skills",
        "submit-evidence",
        "theory",
        "trace",
        "watch",
        "why",
    }
)


def _admit_v6_root(root: Path | str, *, operation: str):
    """Load only the immutable V6 authority records for one existing run root."""

    from deepreason.evidence import (
        RunInputManifestV2,
        load_evidence_dossier,
        load_run_input,
        verify_run_input,
    )
    from deepreason.run_manifest import MANIFEST_NAME, RunManifestError, load_run_manifest
    from deepreason.runtime.launch_policy import V6_RUN_MANIFEST_REQUIRED

    root_path = Path(root)
    manifest = load_run_manifest(root_path / MANIFEST_NAME)
    if manifest.schema_version != 6:
        raise RunManifestError(
            V6_RUN_MANIFEST_REQUIRED,
            f"{operation} requires RunManifest schema version 6",
            "/schema_version",
        )
    run_input = load_run_input(root_path)
    if not isinstance(run_input, RunInputManifestV2):
        raise RunManifestError(
            "RUN_INPUT_SCHEMA_MISMATCH",
            "RunManifest v6 requires run-input manifest v2",
            "/run-input.json/schema",
        )
    if run_input.run_input_digest != manifest.run_input_digest:
        raise RunManifestError(
            "RUN_INPUT_MISMATCH",
            "bound run input digest differs from RunManifest v6",
            "/run_input_digest",
        )
    dossier = load_evidence_dossier(root_path)
    if (
        dossier.dossier_digest != run_input.evidence_dossier_digest
        or dossier.problem_ref != run_input.problem.id
    ):
        raise RunManifestError(
            "RUN_INPUT_DOSSIER_MISMATCH",
            "bound V6 run input and evidence dossier disagree",
            "/evidence-dossier.json",
        )
    verified = verify_run_input(root_path)
    if verified.get("input_schema_version") != 2:
        raise RunManifestError(
            "RUN_INPUT_SCHEMA_MISMATCH",
            "RunManifest v6 requires run-input manifest v2",
            "/run-input.json/schema",
        )
    return manifest, run_input, dossier


def _require_v6_workload_match(run_input, dossier, spec) -> None:
    """Require one CLI workload to equal the complete frozen V6 input."""

    from deepreason.evidence.models import RunInputCommitmentV1
    from deepreason.run_manifest import RunManifestError

    expected_criteria = tuple(
        RunInputCommitmentV1.from_commitment(item) for item in spec.criteria
    )
    dossier_sources = tuple(source.id for source in dossier.sources)
    if (
        run_input.problem.id != spec.problem.id
        or run_input.problem.description != spec.problem.description
        or run_input.problem.criteria != expected_criteria
        or tuple(spec.sources) != dossier_sources
    ):
        raise RunManifestError(
            "RUN_INPUT_MISMATCH",
            "CLI workload differs from the frozen V6 run input or dossier",
            "/run-input.json",
        )


def main(argv: list[str] | None = None) -> int:
    """Entry point: _main wrapped so piping into `head`/`less` (which closes
    stdout early) exits quietly instead of tracebacking on BrokenPipeError."""
    try:
        return _main(argv)
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except Exception:  # noqa: BLE001 - already broken; nothing to save
            pass
        return 0


def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from deepreason import easy

    easy.load_credentials()  # stored keys reach every command; env vars win

    if args.command is None:
        return _cmd_status(args)

    if args.command == "setup":
        try:
            easy.setup_wizard(
                provider=args.provider,
                endpoint=args.endpoint,
                model=args.model,
                model_revision=args.model_revision,
                family=args.family,
                context_window_tokens=args.context_window_tokens,
                maximum_completion_tokens=args.maximum_completion_tokens,
                credential_env=args.credential_env,
            )
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
        print("Next action: deepreason qualify")
        return 0

    if args.command == "status":
        return _cmd_status(args)

    if args.command == "qualify":
        return _cmd_qualify(args)

    if args.command == "mcp-registration":
        from deepreason.mcp_registration import MCPRegistrationError, registration_json

        try:
            print(registration_json())
        except MCPRegistrationError as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0

    if args.command == "scratch":
        from deepreason.cli.scratch import dispatch_scratch

        return dispatch_scratch(args)

    if args.command == "bridge":
        from deepreason.cli.bridge import handle_bridge_command

        return handle_bridge_command(args)

    if args.command == "config" and args.config_command is None:
        import yaml

        from deepreason.config import load as load_config

        configured = load_config(Path(args.config) if args.config else None)
        print(yaml.safe_dump(configured.model_dump(mode="json"), sort_keys=False), end="")
        return 0

    if args.command == "config" and args.config_command == "compile":
        from deepreason.config import load as load_config
        from deepreason.llm.capabilities import CapabilityCache
        from deepreason.run_manifest import (
            ControlPlanePolicyV3,
            RunManifestError,
            compile_run_manifest,
            render_role_matrix,
            write_run_manifest,
        )

        configured = load_config(Path(args.config) if args.config else None)
        missing = [
            flag
            for flag, value in (
                ("--workload-profile", args.workload_profile),
                ("--control-plane-policy", args.control_plane_policy),
                ("--run-input-digest", args.run_input_digest),
            )
            if not value
        ]
        if missing:
            print(
                "V6_COMPILE_INPUTS_REQUIRED: pass " + ", ".join(missing),
                file=sys.stderr,
            )
            return 1
        control_plane_policy = None
        try:
            control_plane_policy = ControlPlanePolicyV3.model_validate_json(
                Path(args.control_plane_policy).read_bytes()
            )
        except (OSError, ValueError) as error:
            print(f"invalid control-plane policy: {error}", file=sys.stderr)
            return 1
        try:
            manifest = compile_run_manifest(
                configured,
                engine_profile=args.engine_profile,
                model_profile=args.profile,
                single_model=args.single_model,
                judge_family=args.judge_family,
                rubric_policy=args.rubric_policy,
                concurrency=args.concurrency,
                capability_cache=CapabilityCache(Path(args.root) / "capabilities.json"),
                schema_version=6,
                workload_profile=args.workload_profile,
                pack_profile=args.pack_profile,
                output_profile=args.output_profile,
                control_plane_policy=control_plane_policy,
                run_input_digest=args.run_input_digest,
            )
        except (RunManifestError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(render_role_matrix(manifest))
        print(f"sha256={manifest.sha256}")
        if not args.dry_run:
            target, digest = write_run_manifest(manifest, args.out)
            print(f"wrote {target} and {digest}")
        return 0

    if args.command == "config" and args.config_command == "inspect":
        from deepreason.run_manifest import load_run_manifest, render_role_matrix

        try:
            manifest = load_run_manifest(args.run_manifest)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
        print(render_role_matrix(manifest))
        print(f"sha256={manifest.sha256}")
        print(json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True))
        return 0

    if args.command == "input":
        return _cmd_input(args)
    if args.command == "doctor":
        return _cmd_doctor(args)

    if args.command in _ROOT_ADMISSION_COMMANDS:
        try:
            _admit_v6_root(args.root, operation=f"CLI {args.command}")
            if args.command == "merge":
                _admit_v6_root(args.path, operation="CLI merge source")
        except (OSError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1

    if args.command == "reason":
        return _cmd_reason(args)

    if args.command == "skills":
        return _cmd_skills(args)

    if args.command == "distill":
        return _cmd_distill(args)

    if args.command == "brain":
        return _cmd_brain(args)

    if args.command == "continue":
        return _cmd_continue(args)

    if args.command == "watch":
        from deepreason.application import TEXT_RUN_SERVICE, WatchTextRunIntentV1
        from deepreason.ui.terminal import render_terminal_status

        try:
            for pulse, snapshot in enumerate(
                TEXT_RUN_SERVICE.watch(
                    WatchTextRunIntentV1(
                        root=str(args.root), interval=args.interval, once=args.once
                    )
                )
            ):
                print(render_terminal_status(snapshot.presentation_payload(), pulse=pulse))
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0

    if args.command == "cancel":
        return _cmd_cancel(args)

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
        public_signals = {
            name: meaning
            for name, meaning in SIGNALS.items()
            if not name.startswith("jolt-")
        }
        public_prefixes = {
            key: meaning
            for key, meaning in PREFIXES.items()
            if not key.startswith("jolt-")
        }
        for name, meaning in {
            **public_signals,
            **{k + "*": v for k, v in public_prefixes.items()},
        }.items():
            print(f"{counts.get(name, 0):6}  {name}: {meaning}")
        unregistered = {k: n for k, n in counts.items()
                        if not k.startswith("jolt-")
                        and k not in SIGNALS and not k.endswith("*")}
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

    if args.command == "calibrate":
        from deepreason.config import load as load_config
        from deepreason.llm.embedder import EmbedderUnavailable, build_embedder
        from deepreason.views.basin import threshold_calibration

        harness = Harness(Path(args.root))
        config = load_config(Path(args.config) if args.config else None)
        try:
            embedder = build_embedder(args.model or config.EMBEDDER_MODEL)
        except EmbedderUnavailable as e:
            print(str(e), file=sys.stderr)
            return 1
        print(json.dumps(threshold_calibration(harness, embedder),
                         indent=2, sort_keys=True))
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

    if args.command == "research":
        from deepreason.config import load as load_config
        from deepreason.ops import research_docket

        harness = Harness(Path(args.root))
        config = load_config(Path(args.config) if args.config else None)
        entries = research_docket(harness, config)
        if not entries:
            print("(no open research problems)")
        for entry in entries:
            state = ("internal-exhausted" if entry["internal_exhausted"]
                     else f"attempts={entry['failed_internal_attempts']}")
            print(f"{entry['problem']}  [{entry['backend_mode']}]  {state}  "
                  f"{entry['claim'][:100]}")
        return 0

    if args.command == "submit-evidence":
        from deepreason.ops import submit_evidence
        from deepreason.research.backends import covered

        harness = Harness(Path(args.root))
        metadata = {k: v for k, v in (
            ("retrieved_at", args.retrieved_at), ("title", args.title)) if v}
        evidence = submit_evidence(
            harness, args.problem_id, args.source,
            Path(args.file).read_text(),
            role="user" if args.user else "import",
            metadata=metadata or None,
        )
        status = harness.state.status.get(evidence.id).value
        state = "covered" if covered(harness, args.problem_id) else "still open"
        print(f"candidate evidence {evidence.id[:12]} registered ({status}); "
              f"problem {state} — coverage is derived under criticism")
        return 0

    if args.command == "report-research-failure":
        from deepreason.ops import report_research_failure

        report_research_failure(
            Harness(Path(args.root)), args.problem_id, args.source,
            args.reason, category=args.category,
        )
        print(f"failure recorded for {args.problem_id} — the request stays open")
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


def _read_problem_file(path: Path) -> dict:
    """Parse one seed payload without mutating the harness (preflight seam)."""
    if path.suffix in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(path.read_text())
    else:
        data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("problem file must contain an object")
    return data


def _cmd_input(args) -> int:
    """Freeze one problem and its complete criteria for V6 compilation."""

    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        EvidenceDossierV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )
    from deepreason.workloads.text import ReasoningWorkloadSpec

    if args.input_command != "freeze":
        return 2
    try:
        spec = ReasoningWorkloadSpec.model_validate(
            _read_problem_file(Path(args.problem))
        )
        root = Path(args.root)
        if args.dossier:
            dossier = EvidenceDossierV1.model_validate(
                _read_problem_file(Path(args.dossier))
            )
        else:
            if spec.sources:
                raise ValueError(
                    "INPUT_DOSSIER_REQUIRED: workload sources require --dossier"
                )
            dossier = EvidenceDossierV1.create(
                problem_ref=spec.problem.id,
                sources=(),
                total_byte_count=0,
                creation_provenance=AttachedSourceProvenanceV1(
                    supplied_by="operator workload",
                    acquisition_method="deepreason input freeze",
                ),
            )
        if dossier.problem_ref != spec.problem.id:
            raise ValueError(
                "RUN_INPUT_PROBLEM_MISMATCH: dossier and workload name different problems"
            )
        dossier_ids = tuple(source.id for source in dossier.sources)
        if spec.sources and tuple(spec.sources) != dossier_ids:
            raise ValueError(
                "RUN_INPUT_SOURCE_MISMATCH: workload sources must exactly equal "
                "the dossier's canonical source IDs"
            )
        run_input = RunInputManifestV2.create(
            problem=RunInputProblemV2.from_commitments(
                id=spec.problem.id,
                description=spec.problem.description,
                criteria=spec.criteria,
            ),
            evidence_dossier_digest=dossier.dossier_digest,
        )
        bind_run_input(run_input, dossier, root)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "schema": "deepreason-input-freeze-result-v1",
                "input_schema_version": run_input.input_schema_version,
                "run_input_digest": run_input.run_input_digest,
                "evidence_dossier_digest": dossier.dossier_digest,
                "root": str(root.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


def _doctor_role_seats(configured, role: str) -> dict:
    """Report one source role without resolving, probing, or exposing secrets."""

    value = configured.roles.get(role)
    seats = value if isinstance(value, list) else ([] if value is None else [value])
    concrete = 0
    for seat in seats:
        if hasattr(seat, "model_dump"):
            seat = seat.model_dump(mode="json")
        if not isinstance(seat, dict):
            continue
        endpoint = str(seat.get("endpoint") or "").strip()
        model = str(seat.get("model") or "").strip()
        if endpoint and model and model not in {"auto", "auto-alt"}:
            concrete += 1
    return {
        "role": role,
        "configured_seats": len(seats),
        "concrete_seats": concrete,
        "ready": concrete > 0,
    }


def _doctor_policy_readiness(configured) -> dict:
    """Describe v3 scratch/bridge readiness without runtime route selection.

    This is setup-time diagnostics only. It neither compiles a manifest nor
    imports/initializes a neural model, so optional-package state cannot enter
    canonical run identity.
    """

    import importlib.util

    scratch = getattr(configured, "scratchpad", None)
    bridge = getattr(configured, "bridge", None)

    scratch_roles = {
        "block": str(getattr(scratch, "block_role", "conjecturer")),
        "link": str(getattr(scratch, "link_role", "synthesizer")),
        "guide": str(getattr(scratch, "guide_role", "summarizer")),
    }
    bridge_roles = {
        "ledger": str(getattr(bridge, "ledger_role", "summarizer")),
        "composer": str(getattr(bridge, "composer_role", "thesis")),
        "reviewer": str(getattr(bridge, "reviewer_role", "judge")),
    }
    grounding_review = bool(getattr(bridge, "grounding_review", True))
    bridge_mode = getattr(bridge, "mode", "legacy_thesis")
    bridge_mode = str(getattr(bridge_mode, "value", bridge_mode))
    scratch_enabled = bool(getattr(scratch, "enabled", False))
    bridge_enabled = bridge_mode == "grounded_two_stage"

    authoring_roles = list(dict.fromkeys(scratch_roles.values()))
    required_bridge_functions = ["ledger", "composer"]
    if grounding_review:
        required_bridge_functions.append("reviewer")
    required_bridge = (
        list(dict.fromkeys(bridge_roles[name] for name in required_bridge_functions))
        if bridge_enabled
        else []
    )
    all_roles = list(dict.fromkeys([*scratch_roles.values(), *bridge_roles.values()]))
    role_status = {role: _doctor_role_seats(configured, role) for role in all_roles}
    missing_authoring = [
        role for role in authoring_roles if not role_status[role]["ready"]
    ]
    missing_bridge = [role for role in required_bridge if not role_status[role]["ready"]]

    try:
        dependency_available = importlib.util.find_spec("fastembed") is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        dependency_available = False
    embedder_model = getattr(configured, "EMBEDDER_MODEL", None)
    failure_policy = str(getattr(configured, "EMBEDDER_FAILURE_POLICY", "fallback"))
    configured_backend = (
        "configured_neural" if embedder_model else "deterministic_hashing"
    )
    fallback_active = bool(
        embedder_model and not dependency_available and failure_policy == "fallback"
    )
    embedder_ready = bool(
        not embedder_model or dependency_available or failure_policy == "fallback"
    )
    semantic_retrieval = bool(getattr(scratch, "semantic_retrieval", False))
    # Manual/deterministic scratch operation needs no LLM route. Authoring
    # readiness is reported separately so missing content-authoring roles do
    # not incorrectly disable the canonical scratch service.
    scratch_ready = not scratch_enabled or not semantic_retrieval or embedder_ready
    bridge_ready = not bridge_enabled or not missing_bridge

    return {
        "required_roles": {
            "scratch": scratch_roles,
            "bridge": {
                **bridge_roles,
                "reviewer_required": grounding_review,
            },
        },
        "role_readiness": role_status,
        "scratch_readiness": {
            "enabled": scratch_enabled,
            "ready": scratch_ready,
            "authoring_ready": not missing_authoring,
            "missing_authoring_roles": missing_authoring,
            "semantic_retrieval": semantic_retrieval,
        },
        "bridge_readiness": {
            "mode": bridge_mode,
            "enabled": bridge_enabled,
            "ready": bridge_ready,
            "missing_roles": missing_bridge,
            "grounding_review": grounding_review,
        },
        "embedder": {
            "configured_backend": configured_backend,
            "model": embedder_model,
            "failure_policy": failure_policy,
            "fallback_backend": "deterministic_hashing",
            "dependency_available": dependency_available,
            "fallback_active": fallback_active,
            "ready": embedder_ready,
        },
    }


def _cmd_doctor(args) -> int:
    """Validate identity, inventory, then measure transport capabilities."""
    import os
    from dataclasses import asdict

    production_mode = bool(
        args.run_manifest or args.production_contracts or args.out
    )
    if production_mode:
        if not (args.run_manifest and args.production_contracts and args.out):
            print(
                "DOCTOR_PRODUCTION_ARGUMENTS_REQUIRED: pass --run-manifest, "
                "--production-contracts, and --out together",
                file=sys.stderr,
            )
            return 1
        legacy_values = (
            args.endpoint,
            args.model,
            args.provider,
            args.family,
            args.api_key_env,
            args.revision,
        )
        if any(value is not None for value in legacy_values) or args.dry_run:
            print(
                "DOCTOR_MODE_CONFLICT: production-contract qualification cannot "
                "be combined with endpoint-doctor arguments",
                file=sys.stderr,
            )
            return 1
        from deepreason.cli.doctor import run_production_contract_doctor_cli

        try:
            report = run_production_contract_doctor_cli(
                run_manifest=args.run_manifest,
                output=args.out,
            )
        except (OSError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(
            json.dumps(
                report.model_dump(mode="json", by_alias=True, exclude_none=True),
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if report.summary.qualified else 1

    if not args.endpoint or not args.model:
        print(
            "DOCTOR_ENDPOINT_MODEL_REQUIRED: pass --endpoint and --model, or use "
            "--run-manifest with --production-contracts and --out",
            file=sys.stderr,
        )
        return 1

    from deepreason.config import load as load_config
    from deepreason.llm.adapter import _endpoint_from_spec
    from deepreason.llm.capabilities import CapabilityCache, probe_capabilities
    from deepreason.llm.endpoints import EndpointError, list_models
    from deepreason.llm.profiles import select_profile
    from deepreason.llm.repair import select_output_mechanism
    from deepreason.llm.providers import infer_provider
    from deepreason.run_manifest import (
        RouteSecretError,
        infer_model_family,
        validate_route_base_url,
    )

    if args.model in ("auto", "auto-alt"):
        print("DOCTOR_MODEL_MUST_BE_CONCRETE: --model cannot be auto or auto-alt",
              file=sys.stderr)
        return 1
    configured = load_config(Path(args.config) if args.config else None)
    selected = None
    for role, value in configured.roles.items():
        seats = value if isinstance(value, list) else [value]
        for seat in seats:
            if not isinstance(seat, dict):
                continue
            if args.endpoint in {
                role, str(seat.get("endpoint_id") or ""), str(seat.get("endpoint") or "")
            }:
                selected = dict(seat)
                break
        if selected is not None:
            break
    if selected is None:
        if not (args.endpoint.startswith("http://") or args.endpoint.startswith("https://")):
            print(
                f"DOCTOR_ENDPOINT_NOT_FOUND: {args.endpoint!r} is not a URL, endpoint_id, "
                "or configured role",
                file=sys.stderr,
            )
            return 1
        selected = {"endpoint": args.endpoint}
    endpoint = str(selected.get("endpoint") or "")
    try:
        validate_route_base_url(endpoint)
    except RouteSecretError as error:
        # The validator deliberately carries no rejected URL, so neither the
        # doctor result nor stderr can echo embedded credential material.
        print(str(error), file=sys.stderr)
        return 1
    provider = str(args.provider or selected.get("provider") or infer_provider(endpoint))
    family = str(args.family or selected.get("family")
                 or infer_model_family(args.model, provider))
    key_env = args.api_key_env or selected.get("api_key_env")
    revision = args.revision or selected.get("model_revision") or ""
    key = os.environ.get(key_env) if key_env else None
    if key_env and not key:
        print(f"DOCTOR_API_KEY_MISSING: environment variable {key_env} is unset",
              file=sys.stderr)
        return 1
    result = {
        "endpoint_id": selected.get("endpoint_id") or endpoint,
        "base_url": endpoint,
        "model_id": args.model,
        "provider": provider,
        "family": family,
        "model_revision": revision or None,
        "credential_env": key_env,
        "credential_present": bool(key),
        "contacted": False,
        "recommended_model_profile": None,
        "compact_profile_recommended": None,
        "output_mechanism_support": {
            "measured": False,
            "selected": selected.get("output_mechanism"),
            "native_json_schema": None,
            "grammar": None,
            "json_text": True,
        },
        **_doctor_policy_readiness(configured),
    }
    if not args.dry_run:
        try:
            available = list_models(endpoint, key)
        except EndpointError as error:
            print(f"DOCTOR_ENDPOINT_FAILED: {error}", file=sys.stderr)
            return 1
        result["contacted"] = True
        result["model_available"] = args.model in available
        result["available_models"] = available
        if not result["model_available"]:
            print(json.dumps(result, indent=2, sort_keys=True))
            print(f"DOCTOR_MODEL_NOT_FOUND: {args.model!r} was not returned by /models",
                  file=sys.stderr)
            return 1
        probe_spec = dict(selected)
        probe_spec.update(
            endpoint=endpoint,
            model=args.model,
            provider=provider,
            family=family,
            model_revision=revision or None,
            api_key_env=key_env,
            # Capability probes measure contract transport, not the source
            # role's creative sampling policy. Freeze deterministic decoding
            # with enough output headroom for the 4096-token length probe.
            temperature=0.0,
            reasoning="none",
            max_tokens=5000,
            logprobs=False,
            json_mode=False,
        )
        probe_endpoint = _endpoint_from_spec(probe_spec)
        cache = CapabilityCache(Path(args.root) / "capabilities.json")
        capabilities = probe_capabilities(
            probe_endpoint, revision=revision, cache=cache
        )
        result["capabilities"] = asdict(capabilities)
        recommended_profile = select_profile(capabilities).name.value
        selected_mechanism = select_output_mechanism(capabilities).value
        result["recommended_model_profile"] = recommended_profile
        result["compact_profile_recommended"] = recommended_profile == "compact"
        result["selected_output_mechanism"] = selected_mechanism
        result["output_mechanism_support"] = {
            "measured": True,
            "selected": selected_mechanism,
            "native_json_schema": capabilities.native_json_schema,
            "grammar": capabilities.grammar,
            "json_text": True,
        }
        result["capability_cache"] = str(cache.path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _load_problem_file(harness: Harness, path: Path) -> str:
    from deepreason.ops import seed_problem_payload

    return seed_problem_payload(harness, _read_problem_file(path)).id


def _cmd_status(args) -> int:
    from deepreason.readiness import get_readiness, readiness_json, readiness_text

    readiness = get_readiness(getattr(args, "provider_profile", None))
    print(readiness_json(readiness) if getattr(args, "json", False) else readiness_text(readiness))
    return 0 if readiness.ready else 1


def _cmd_qualify(args) -> int:
    from deepreason.preparation import qualification_subject_manifest
    from deepreason.provider_profile import credential_present, provider_state_dir, resolve_provider_profile
    from deepreason.qualification import (
        QualificationError,
        default_qualification_executor,
        load_completed_qualification,
        production_qualification_maximum_provider_calls,
        qualification_subject_digest,
        resolve_completed_qualification,
    )

    try:
        resolved = resolve_provider_profile(args.provider_profile)
        profile = resolved.profile
        if not credential_present(profile):
            raise QualificationError(
                "PROVIDER_CREDENTIAL_MISSING", "configured provider credential is absent"
            )
        manifest = qualification_subject_manifest(profile)
        cache_dir = provider_state_dir() / "qualification-cache"
        subject = qualification_subject_digest(manifest, profile)
        try:
            bundle = load_completed_qualification(cache_dir, subject)
            maximum_calls = 0
            state = "ready"
            reused = True
        except QualificationError as error:
            if error.code != "QUALIFICATION_NOT_CONFIGURED":
                raise
            maximum_calls = production_qualification_maximum_provider_calls(manifest)
            notice = (
                f"Qualification will test {profile.provider}/{profile.model_id}; "
                f"maximum expected provider calls: {maximum_calls}."
            )
            print(notice, file=sys.stderr, flush=True)
            if not args.yes and sys.stdin.isatty():
                confirmed = input("Proceed with qualification? [y/N]: ").strip().casefold()
                if confirmed not in {"y", "yes"}:
                    print("QUALIFICATION_CANCELLED: no provider calls were made", file=sys.stderr)
                    return 1
            bundle = resolve_completed_qualification(
                manifest,
                profile,
                cache_dir=cache_dir,
                executor=default_qualification_executor,
            )
            state = "ready"
            reused = False
        payload = {
            "schema": "deepreason-qualification-result.v1",
            "provider": profile.provider,
            "model_id": profile.model_id,
            "profile_source": resolved.source,
            "qualification_state": state,
            "cache_reused": reused,
            "maximum_expected_provider_calls": maximum_calls,
            "qualification_subject_digest": bundle.subject_digest,
            "next_action": 'deepreason reason "YOUR QUESTION"',
        }
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(f"Qualified: {payload['provider']}/{payload['model_id']}")
        print(f"Qualification state: {payload['qualification_state']}")
        print(f"Next action: {payload['next_action']}")
    return 0


def _cmd_reason(args) -> int:
    """Prepare one question and execute it through the shared V6 application."""

    from deepreason.application import InspectTextRunIntentV1, TEXT_RUN_SERVICE
    from deepreason.application.intents import start_text_run_intent
    from deepreason.preparation import (
        PUBLIC_DEFAULT_CYCLES,
        PUBLIC_DEFAULT_TOKEN_BUDGET,
        RunPreparationRequestV1,
        RunPreparationService,
    )

    if args.root != ".deepreason":
        print("PUBLIC_REASON_ROOT_FORBIDDEN: managed run paths are host-owned", file=sys.stderr)
        return 1
    cycles = args.cycles if args.cycles is not None else PUBLIC_DEFAULT_CYCLES
    tokens = (
        args.token_budget
        if args.token_budget is not None
        else PUBLIC_DEFAULT_TOKEN_BUDGET
    )
    try:
        prepared = RunPreparationService().prepare(
            RunPreparationRequestV1(
                question=args.question,
                budget={"cycles": cycles, "token_budget": tokens},
                profile_path=args.provider_profile,
            )
        )
        accepted = TEXT_RUN_SERVICE.start(
            start_text_run_intent(
                root=prepared.root,
                workload=prepared.workload,
                run_manifest_ref=prepared.run_manifest_ref,
                cycles=prepared.budget.cycles,
                token_budget=prepared.budget.token_budget,
            )
        )
        TEXT_RUN_SERVICE.wait(accepted.root)
        terminal = TEXT_RUN_SERVICE.result(
            InspectTextRunIntentV1(root=accepted.root)
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 6 if str(error).startswith(("RUN_RESULT_INVALID", "RUN_RESULT_NOT_READY")) else 1
    payload = terminal.presentation_payload()
    payload["run_id"] = prepared.managed_run_id
    print(json.dumps(payload, indent=2, sort_keys=True))
    return terminal.exit_code()

def _cmd_skills(args) -> int:
    """Snapshot explicit capsules and emit a replayable retrieval receipt."""

    from deepreason.skills.models import SkillCapsule
    from deepreason.skills.retrieve import retrieve_skills
    from deepreason.skills.snapshot import snapshot_library

    try:
        capsules = tuple(
            SkillCapsule.model_validate_json(Path(path).read_bytes())
            for path in args.capsule
        )
        if not args.school:
            raise ValueError("skills retrieval requires at least one explicit --school")
        harness = Harness(Path(args.root))
        snapshot = snapshot_library(capsules, harness.blobs, library_id="cli-explicit")
        receipt = retrieve_skills(
            snapshot,
            args.query,
            args.school,
            harness.blobs,
            problem_id=args.query,
            top_k=args.top_k,
            harness=harness,
        )
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(receipt.model_dump(mode="json", by_alias=True), indent=2, sort_keys=True))
    return 0


def _cmd_distill(args) -> int:
    """Create a capsule only after accepted-source time-travel validation."""

    from deepreason.canonical import canonical_json
    from deepreason.skills.distill import distill_capsule
    from deepreason.skills.models import CapsuleDraft
    from deepreason.skills.validate import validate_distillation_source

    try:
        _admit_v6_root(args.source, operation="CLI distill source")
        draft = CapsuleDraft.model_validate(_read_problem_file(Path(args.draft)))
        source = validate_distillation_source(
            args.source,
            source_event_seq=args.seq,
            accepted_artifact_id=args.artifact,
            distiller_version="cli-v1",
        )
        capsule = distill_capsule(source, draft)
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(canonical_json(capsule.model_dump(mode="json", by_alias=True)))
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"wrote {target} ({capsule.id})")
    return 0


def _cmd_brain(args) -> int:
    """Operate only on the brain root and files explicitly supplied by the user."""

    from datetime import date

    from deepreason.brain import BrainStore, ingest_files, retrieve

    try:
        if args.brain_command == "distill-run":
            _admit_v6_root(args.source, operation="CLI brain distill source")
        if args.brain_command == "init":
            store = BrainStore.init(args.path)
            print(json.dumps(store.manifest.model_dump(mode="json", by_alias=True), indent=2))
            return 0

        store = BrainStore(args.path)
        if args.brain_command == "ingest":
            ids = ingest_files(store, args.files)
            print(json.dumps({"record_ids": ids}, indent=2))
            return 0
        if args.brain_command == "query":
            query_day = date.fromisoformat(args.day) if args.day else date.today()
            result = retrieve(store, args.query, query_day=query_day)
            payload = {
                "receipt": result.receipt.model_dump(mode="json", by_alias=True),
                "cards": [item.model_dump(mode="json", by_alias=True) for item in result.cards],
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.brain_command == "inspect":
            if args.id:
                payload = store.get_memory(args.id).model_dump(mode="json", by_alias=True)
            else:
                payload = {
                    "manifest": store.manifest.model_dump(mode="json", by_alias=True),
                    "record_count": len(store.record_ids()),
                    "event_count": len(store.events),
                }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.brain_command == "reinforce":
            event = store.reinforce(args.id)
        elif args.brain_command == "pin":
            event = store.pin(args.id, floor=args.floor)
        elif args.brain_command == "unpin":
            event = store.unpin(args.id)
        elif args.brain_command == "reindex":
            from deepreason.brain.index import build_index

            projection = build_index(store, force=True)
            print(json.dumps({"projection": str(projection)}, indent=2))
            return 0
        elif args.brain_command == "distill-run":
            from deepreason.brain.distill import distill_lesson
            from deepreason.brain.models import LessonRecord
            from deepreason.skills.validate import validate_distillation_source

            lesson = LessonRecord.model_validate(_read_problem_file(Path(args.lesson)))
            source = validate_distillation_source(
                args.source,
                source_event_seq=args.seq,
                accepted_artifact_id=args.artifact,
                distiller_version="brain-cli-v1",
            )
            record_id = distill_lesson(
                store,
                lesson,
                source_ref=(
                    f"run:{source.source_snapshot_digest}:"
                    f"{source.accepted_artifact_id}@{source.source_event_seq}"
                ),
            )
            print(json.dumps({"record_id": record_id}, indent=2))
            return 0
        else:  # pragma: no cover - argparse owns the finite command set
            raise ValueError(f"unknown brain command: {args.brain_command}")
        print(event.model_dump_json(by_alias=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


def _cmd_continue(args) -> int:
    from deepreason.application import (
        InspectTextRunIntentV1,
        TEXT_RUN_SERVICE,
        continue_text_run_intent,
    )

    try:
        raw_cycles = str(args.budget).strip()
        if raw_cycles.startswith("cycles="):
            raw_cycles = raw_cycles.partition("=")[2]
        accepted = TEXT_RUN_SERVICE.continue_run(
            continue_text_run_intent(
                root=str(args.root),
                cycles=raw_cycles,
                token_budget=args.token_budget,
                expected_manifest_digest=args.expected_manifest_digest,
            )
        )
        TEXT_RUN_SERVICE.wait(accepted.root)
        terminal = TEXT_RUN_SERVICE.result(
            InspectTextRunIntentV1(root=accepted.root)
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 6 if str(error).startswith(("RUN_RESULT_INVALID", "RUN_RESULT_NOT_READY")) else 1
    payload = terminal.presentation_payload()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return terminal.exit_code()


def _cmd_cancel(args) -> int:
    from deepreason.application import (
        CancelTextRunIntentV1,
        TEXT_RUN_SERVICE,
    )

    try:
        payload = TEXT_RUN_SERVICE.cancel(
            CancelTextRunIntentV1(root=str(args.root))
        ).presentation_payload()
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_check_proof(args) -> int:
    from deepreason.runtime.progress import _atomic_json
    from deepreason.run_manifest import (
        MANIFEST_NAME,
        RunManifestError,
        bind_run_manifest,
        load_run_manifest,
    )
    from deepreason.verification.lean import LeanBackend
    from deepreason.verification.models import VerificationRequest

    root = Path(args.root)
    bound_path = root / MANIFEST_NAME
    try:
        if bound_path.exists():
            manifest = load_run_manifest(bound_path)
            if args.run_manifest:
                requested = load_run_manifest(args.run_manifest)
                if requested.canonical_bytes() != manifest.canonical_bytes():
                    raise RunManifestError(
                        "RUN_MANIFEST_CONFLICT",
                        "run root is already bound to a different manifest",
                        f"/{MANIFEST_NAME}",
                    )
        elif args.run_manifest:
            manifest = load_run_manifest(args.run_manifest)
        else:
            raise ValueError("PROOF_MANIFEST_REQUIRED: pass --run-manifest or use a bound root")
        if manifest.schema_version not in {2, 3, 4, 5} or manifest.workload_profile != "formal":
            raise ValueError(
                "PROOF_MANIFEST_WORKLOAD_MISMATCH: expected v2+ formal manifest"
            )
        candidates = [
            item
            for item in manifest.toolchains
            if item.id.startswith("lean4@") and "lean_kernel" in item.allowed_programs
        ]
        if len(candidates) != 1:
            raise ValueError("PROOF_TOOLCHAIN_REQUIRED: manifest must pin one Lean kernel")
        toolchain = candidates[0]
        if toolchain.runner != "local":
            raise ValueError("PROOF_RUNNER_UNSUPPORTED: this command requires a local Lean kernel")
        if args.max_heartbeats <= 0 or args.max_rec_depth <= 0:
            raise ValueError("proof operation limits must be finite and positive")
        source = Path(args.source).read_bytes()
        bind_run_manifest(manifest, root)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1

    harness = Harness(root)
    source_ref = harness.blobs.put(source)
    backend = LeanBackend(
        harness.blobs,
        executable=toolchain.executable,
        toolchain_id=toolchain.id,
    )
    fingerprint = backend.fingerprint()
    if fingerprint.get("version_output_sha256") != toolchain.version_output_sha256:
        print("PROOF_TOOLCHAIN_FINGERPRINT_MISMATCH", file=sys.stderr)
        return 1
    request = VerificationRequest(
        backend="lean4",
        toolchain_id=toolchain.id,
        source_ref=source_ref,
        imports_lock_ref=toolchain.lock_digest,
        max_heartbeats=args.max_heartbeats,
        max_rec_depth=args.max_rec_depth,
        allow_sorry=False,
        allowed_axioms=[],
        target_theorems=args.theorem,
    )
    result = backend.verify(request)
    payload = result.model_dump(mode="json")
    payload["claim"] = (
        "kernel acceptance under pinned imports and axioms; not informal or empirical truth"
    )
    payload["schema"] = "deepreason-proof-result-v1"
    _atomic_json(root / "proof-result.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.verdict == "pass" else 1


def _bind_cli_manifest(root: Path, requested_path: str, *, workload: str):
    from deepreason.run_manifest import MANIFEST_NAME, RunManifestError
    from deepreason.run_manifest import bind_run_manifest, load_run_manifest

    requested = load_run_manifest(requested_path)
    bound = root / MANIFEST_NAME
    if bound.exists():
        manifest = load_run_manifest(bound)
        if requested.canonical_bytes() != manifest.canonical_bytes():
            raise RunManifestError(
                "RUN_MANIFEST_CONFLICT",
                "run root is already bound to a different manifest",
                f"/{MANIFEST_NAME}",
            )
    else:
        manifest = requested
    if manifest.schema_version not in {2, 3, 4, 5} or manifest.workload_profile != workload:
        raise ValueError(
            f"{workload.upper()}_MANIFEST_WORKLOAD_MISMATCH: "
            f"expected v2+ {workload} manifest"
        )
    bind_run_manifest(manifest, root)
    return manifest


def _cmd_code(args) -> int:
    from deepreason.runtime.progress import _atomic_json
    from deepreason.verification.code import verify_code_patch
    from deepreason.workloads.code import (
        CodePatch,
        CodeWorkloadSpec,
        snapshot_workspace,
    )

    root = Path(args.root)
    try:
        manifest = _bind_cli_manifest(root, args.run_manifest, workload="code")
        workload = CodeWorkloadSpec.model_validate(_read_problem_file(Path(args.workload)))
        patch = CodePatch.model_validate(_read_problem_file(Path(args.patch)))
        if not any(
            "repo_test" in toolchain.allowed_programs
            for toolchain in manifest.toolchains
        ):
            raise ValueError("CODE_TOOLCHAIN_REQUIRED: manifest must allow repo_test")
        harness = Harness(root)
        snapshot = snapshot_workspace(workload.workspace, blobs=harness.blobs)
        result = verify_code_patch(
            workload,
            snapshot,
            patch,
            blobs=harness.blobs,
        )
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    payload = result.model_dump(mode="json")
    payload["schema"] = "deepreason-code-result-v1"
    _atomic_json(root / "code-result.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.verdict == "pass" else 1


def _cmd_simulate(args) -> int:
    from deepreason.runtime.progress import _atomic_json
    from deepreason.verification.simulation import (
        SimulationBackend,
        SimulationRequest,
    )
    from deepreason.workloads.code import CodeWorkloadSpec

    root = Path(args.root)
    try:
        manifest = _bind_cli_manifest(root, args.run_manifest, workload="code")
        workload = CodeWorkloadSpec.model_validate(_read_problem_file(Path(args.workload)))
        if args.simulation_index < 0 or args.simulation_index >= len(workload.simulations):
            raise ValueError("SIMULATION_INDEX_INVALID")
        spec = workload.simulations[args.simulation_index]
        candidates = [
            item
            for item in manifest.toolchains
            if item.id == spec.toolchain_id
            and "simulation_oracle" in item.allowed_programs
        ]
        if len(candidates) != 1 or candidates[0].runner != "local":
            raise ValueError(
                "SIMULATION_TOOLCHAIN_REQUIRED: manifest must pin the declared local oracle"
            )
        harness = Harness(root)
        source_ref = harness.blobs.put(Path(args.source).read_bytes())
        inputs_ref = harness.blobs.put(Path(args.inputs).read_bytes())
        checker_ref = harness.blobs.put(Path(args.checker).read_bytes())
        if inputs_ref != spec.inputs_ref or checker_ref != spec.checker_ref:
            raise ValueError("SIMULATION_INPUT_DIGEST_MISMATCH")
        backend = SimulationBackend(toolchain_id=spec.toolchain_id)
        fingerprint = backend.fingerprint()
        toolchain = candidates[0]
        if (
            fingerprint["executable"] != str(Path(toolchain.executable).resolve())
            or fingerprint["version_output_sha256"] != toolchain.version_output_sha256
        ):
            raise ValueError("SIMULATION_TOOLCHAIN_FINGERPRINT_MISMATCH")
        result = backend.verify(
            SimulationRequest(source_ref=source_ref, spec=spec),
            harness.blobs,
        )
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    payload = result.model_dump(mode="json")
    payload["schema"] = "deepreason-simulation-result-v1"
    payload["claim"] = "checker result for the pinned model and inputs, not the world"
    _atomic_json(root / "simulation-result.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.verdict == "pass" else 1


def _cmd_run(args) -> int:
    from deepreason.locking import ProcessLockBusy, ProcessLockError, operator_locks
    from deepreason.ops import require_full_engine
    from deepreason.runtime.launch_policy import (
        require_v6_launch_allowed,
        require_v6_production_qualification,
    )
    from deepreason.run_manifest import (
        RunManifestError,
        config_from_run_manifest,
        load_run_manifest,
        preflight_payload,
        render_role_matrix,
    )
    from deepreason.workloads.text import ReasoningWorkloadSpec

    run_root = Path(args.root)
    operator_lock = None
    try:
        cycles = (
            int(args.budget.split("=", 1)[1])
            if "=" in args.budget
            else int(args.budget)
        )
        if cycles < 1:
            raise ValueError("run --budget must be a positive cycle count")
        manifest, run_input, dossier = _admit_v6_root(
            run_root, operation="CLI run"
        )
        if args.run_manifest:
            requested = load_run_manifest(args.run_manifest)
            if requested.canonical_bytes() != manifest.canonical_bytes():
                raise RunManifestError(
                    "RUN_MANIFEST_CONFLICT",
                    "run root is already bound to a different manifest",
                    "/run-manifest.json",
                )
        if manifest.workload_profile != "text":
            raise RunManifestError(
                "WORKLOAD_PROFILE_MISMATCH",
                f"run requires text, got {manifest.workload_profile}",
                "/workload_profile",
            )
        config = config_from_run_manifest(manifest)
        if not args.dry_run:
            require_v6_launch_allowed(manifest, operation="full scheduler")
        require_full_engine(manifest, workload="full scheduler")
        if args.problem:
            payload = _read_problem_file(Path(args.problem))
            spec = ReasoningWorkloadSpec.model_validate(payload)
            _require_v6_workload_match(run_input, dossier, spec)
            preflight_payload(manifest, payload)
        if not args.dry_run:
            require_v6_production_qualification(
                manifest,
                root=run_root,
                operation="full scheduler",
            )
            try:
                operator_lock = operator_locks(
                    run_root, owner="run", blocking=False
                )
            except ProcessLockBusy as error:
                raise ValueError(
                    "RUN_ALREADY_RUNNING: another operator owns this run root"
                ) from error
    except (ProcessLockError, ValueError) as error:
        if operator_lock is not None:
            operator_lock.release()
        print(str(error), file=sys.stderr)
        return 1
    if args.dry_run:
        print(render_role_matrix(manifest))
        print(f"sha256={manifest.sha256}")
        return 0
    try:
        return _execute_bound_run(args, manifest, config, run_root, cycles)
    finally:
        assert operator_lock is not None
        operator_lock.release()


def _execute_bound_run(args, manifest, config, run_root: Path, cycles: int) -> int:
    """Execute a preflighted run while its caller retains operator locks."""

    from deepreason.runtime.launch_policy import require_v6_launch_allowed

    try:
        require_v6_launch_allowed(manifest, operation="full scheduler")
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    from deepreason.ops import run_scheduler
    from deepreason.run_manifest import preflight_payload

    harness = Harness(run_root)
    if args.problem:
        _load_problem_file(harness, Path(args.problem))
    elif manifest.rubric_policy == "forbid":
        # A resumed root can already contain rubric criteria. Detect the
        # conflict before an adapter/model call rather than midway through.
        rubric_commitments = [
            commitment.model_dump(mode="json")
            for commitment in harness.commitments.values()
            if commitment.eval.startswith("rubric:")
        ]
        if rubric_commitments:
            try:
                preflight_payload(manifest, {"commitments": rubric_commitments})
            except ValueError as error:
                print(str(error), file=sys.stderr)
                return 1
    if not harness.state.problems:
        print("no problem on the frontier; pass --problem <file>", file=sys.stderr)
        return 1
    try:
        result, meter, accounting = run_scheduler(
            harness, config, cycles, args.token_budget, run_manifest=manifest
        )
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
