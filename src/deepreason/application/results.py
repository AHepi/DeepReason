"""The one typed-outcome reader behind `deepreason results`.

Purely a READ surface over a finished (or unfinished) run root: durable
sidecars, the append-only log, and the amendment chain. It writes nothing —
a committed root is evidence, and a reader that repaired it would destroy the
thing it was asked to report on.

Composition, not duplication: `findings.findings_summary` already derives the
question and the replay-derived status counts, so this module calls it rather
than walking `state.status` a second time. What it adds is the four facts no
reader surfaced before — run identity, the stored `verify_root` verdict,
adjudication counts, and amendment/terminal readiness.

Every fact is either a value or a typed ABSENCE (`{"absent": True, "reason":
<code>}`). No key is ever omitted, because a caller cannot tell an omitted key
from a fact that happens to be false, and 20 of the 107 committed roots carry
no `run-status.json` at all.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Closed vocabulary: every reason a fact can be missing. Tests assert the
# emitted reasons are a subset, so a new reason cannot enter undeclared.
ABSENCE_REASONS = frozenset(
    {
        "AMENDMENT_CHAIN_UNREADABLE",
        "NO_CYCLE_RECORD",
        "NO_EMBEDDER_RECORD",
        "NO_FINDING_FAMILIES",
        "NO_FRONTIER_RECORD",
        "NO_REPLAY_VALIDATION_JSON",
        "NO_RUN_IDENTITY_RECORD",
        "NO_RUN_INPUT",
        "NO_RUN_MANIFEST",
        "NO_RUN_RESULT_JSON",
        "NO_RUN_STATUS_JSON",
        "NO_STOP_RECORD",
        "NO_SURVIVOR_RECORD",
        "NO_TERMINAL_BINDING",
        "REPLAY_STATE_UNREADABLE",
    }
)

RESULTS_SCHEMA = "deepreason-results.v1"

_FRONTIER_PREVIEW = 5


class ResultsError(ValueError):
    """A typed, catalogued reason a run's results cannot be located."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def _absent(reason: str) -> dict[str, Any]:
    return {"absent": True, "reason": reason}


def _is_absent(value: Any) -> bool:
    return isinstance(value, dict) and value.get("absent") is True


def _read_json(path: Path) -> dict | None:
    """Return a root sidecar's payload, or None when it is absent or unusable.

    Unreadable is folded into absent on purpose: this reader's job is to report
    what a root carries, and a half-written sidecar carries no fact. The
    integrity question belongs to `verify_root`, which has its own channel here.
    """

    try:
        if not path.is_file():
            return None
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def resolve_results_root(path: Path | str) -> tuple[Path, str]:
    """Resolve `<root-or-home>` to one run root and how it was found.

    A directory holding `log.jsonl` IS the root. Otherwise a `runs/` directory
    holding exactly one run root identifies it. Several candidates refuse by
    NAMING them all, so the caller's next command is a copy-paste rather than
    another guess — which is the whole defect this command exists to remove.
    """

    base = Path(path).expanduser()
    if (base / "log.jsonl").is_file():
        return base.resolve(), "root"

    runs = base / "runs"
    candidates: list[Path] = []
    if runs.is_dir():
        candidates = sorted(
            entry for entry in runs.iterdir()
            if entry.is_dir() and (entry / "log.jsonl").is_file()
        )
    if len(candidates) == 1:
        return candidates[0].resolve(), "home"
    if candidates:
        listed = "\n".join(f"  {entry}" for entry in candidates)
        raise ResultsError(
            "RESULTS_HOME_AMBIGUOUS",
            f"{base} holds {len(candidates)} run roots; name one:\n{listed}",
        )
    raise ResultsError(
        "RESULTS_ROOT_NOT_FOUND",
        f"{base} is neither a run root (no log.jsonl) nor a home holding one",
    )


def _identity(root: Path, status: dict | None, replay: dict | None) -> dict[str, Any]:
    run_id: Any = _absent("NO_RUN_IDENTITY_RECORD")
    if status and status.get("run_id"):
        run_id = status["run_id"]
    elif replay:
        binding = replay.get("terminal_binding")
        if isinstance(binding, dict) and binding.get("run_id"):
            run_id = binding["run_id"]

    manifest = _read_json(root / "run-manifest.json")
    return {
        "run_id": run_id,
        "manifest_present": manifest is not None,
        "manifest_schema_version": (
            manifest.get("schema_version", _absent("NO_RUN_MANIFEST"))
            if manifest
            else _absent("NO_RUN_MANIFEST")
        ),
    }


def _run(status: dict | None, stop: dict | None) -> dict[str, Any]:
    stop_reason: Any = _absent("NO_STOP_RECORD")
    if status and status.get("stop_reason"):
        stop_reason = status["stop_reason"]
    elif stop and stop.get("reason"):
        stop_reason = stop["reason"]

    cycles: Any = _absent("NO_CYCLE_RECORD")
    if status and status.get("cycle") is not None:
        cycles = status["cycle"]
    elif stop and isinstance(stop.get("metrics"), dict):
        if stop["metrics"].get("cycle") is not None:
            cycles = stop["metrics"]["cycle"]

    if status is None:
        missing = _absent("NO_RUN_STATUS_JSON")
        return {
            "state": missing,
            "stop_reason": stop_reason,
            "message": missing,
            "cycles_completed": cycles,
            "token_spend": missing,
            "token_limit": missing,
        }
    # A null limit is a recorded fact (no ceiling), not an unknown one.
    limit = status.get("token_limit")
    return {
        "state": status.get("state", _absent("NO_RUN_STATUS_JSON")),
        "stop_reason": stop_reason,
        "message": status.get("message", ""),
        "cycles_completed": cycles,
        "token_spend": status.get("token_spend", _absent("NO_RUN_STATUS_JSON")),
        "token_limit": "unlimited" if limit is None else limit,
    }


def _artifacts(
    positions: dict[str, list] | None,
    status: dict | None,
    result: dict | None,
) -> dict[str, Any]:
    counts: dict[str, Any] = {}
    for label in ("accepted", "refuted", "suspended"):
        counts[label] = (
            len(positions.get(label, ()))
            if positions is not None
            else _absent("REPLAY_STATE_UNREADABLE")
        )

    # A failed run publishes a `deepreason-run-result-v2` payload carrying
    # `error`/`error_type` and NO survivor or frontier set at all. Counting a
    # missing key as zero would state a result the record never held.
    if result is None:
        missing = _absent("NO_RUN_RESULT_JSON")
        frontier: dict[str, Any] = {"count": missing, "artifact_ids": missing}
        survivors: Any = missing
    elif "frontier" not in result:
        no_frontier = _absent("NO_FRONTIER_RECORD")
        frontier = {"count": no_frontier, "artifact_ids": no_frontier}
        survivors = (
            len(result["survivors"])
            if "survivors" in result
            else _absent("NO_SURVIVOR_RECORD")
        )
    else:
        listed = list(result["frontier"] or ())
        frontier = {"count": len(listed), "artifact_ids": listed}
        survivors = (
            len(result["survivors"])
            if "survivors" in result
            else _absent("NO_SURVIVOR_RECORD")
        )
    frontier["problem_id"] = (
        status.get("problem_id", _absent("NO_RUN_STATUS_JSON"))
        if status
        else _absent("NO_RUN_STATUS_JSON")
    )
    counts["survivor_count"] = survivors
    counts["frontier"] = frontier
    return counts


def _adjudication(harness) -> dict[str, Any]:
    """Defended-trial verdicts and judge calls, counted from the log itself.

    The record separates neither by a dedicated object type: verdicts ride
    Measure events whose first input is the signal, and a judge call is an
    `LLMCall` whose role is `judge`. Absence is a typed ZERO here rather than
    an absence object — "no trial ran" is a fact worth stating, not a gap.
    """

    observations: dict[str, int] = {}
    declined: dict[str, int] = {}
    blocked: dict[str, int] = {}
    judge_calls = 0
    for event in harness.log.read():
        if event.llm is not None and event.llm.role == "judge":
            judge_calls += 1
        inputs = [str(value) for value in (event.inputs or ())]
        if not inputs:
            continue
        signal = inputs[0]
        if signal == "trial-observation":
            outcome = inputs[3] if len(inputs) > 3 else "unrecorded"
            observations[outcome] = observations.get(outcome, 0) + 1
        elif signal == "trial-declined":
            reason = inputs[2] if len(inputs) > 2 else "unrecorded"
            declined[reason] = declined.get(reason, 0) + 1
        elif signal.startswith("trial-blocked:"):
            reason = signal.split(":", 1)[1] or "unrecorded"
            blocked[reason] = blocked.get(reason, 0) + 1
    total = judge_calls + sum(observations.values()) + sum(declined.values())
    return {
        "ran": bool(total or blocked),
        "judge_calls": judge_calls,
        "trial_observations": dict(sorted(observations.items())),
        "trial_declined": dict(sorted(declined.items())),
        "trial_blocked": dict(sorted(blocked.items())),
    }


def embedder_summary(harness) -> dict[str, Any]:
    """Which embedder the run ACTUALLY measured with, and whether it is the
    one the run asked for.

    Both facts already ride Measure events the scheduler stamps — the
    `embedder` identity once per run (model, version, sentinel) and an
    `embedder-fallback` whenever a configured backend could not be built. The
    pair was typed, recorded, replayable, and read by nobody: a run could
    configure neural geometry, measure with `hashing-128` for 24 cycles, and
    publish results that never said so. Deriving it here puts it on the one
    surface an operator already opens.

    The LAST stamp wins. An amended run continues into a new epoch and stamps
    again, so a root can carry several; the run's final geometry is the one
    its final cycles used.
    """

    configured: Any = None
    reason: Any = None
    fell_back = False
    stamp: list[str] | None = None
    for event in harness.log.read():
        inputs = [str(value) for value in (event.inputs or ())]
        if not inputs:
            continue
        if inputs[0] == "embedder" and len(inputs) >= 2:
            stamp = inputs
        elif inputs[0] == "embedder-fallback":
            fell_back = True
            configured = inputs[1] if len(inputs) > 1 else None
            reason = inputs[2] if len(inputs) > 2 else None
    if stamp is None:
        return _absent("NO_EMBEDDER_RECORD")

    model = stamp[1]
    return {
        # `hashing-128` is the one model id the deterministic backend ever
        # reports, so the backend label is derived from it rather than from a
        # separate signal that could disagree with the stamp.
        "backend": "hashing" if model.startswith("hashing") else "neural",
        "model": model,
        "version": stamp[2] if len(stamp) > 2 else None,
        "fingerprint": stamp[3] if len(stamp) > 3 else None,
        "fallback": fell_back,
        "configured_model": configured,
        "fallback_reason": reason,
    }


def embedder_summary_for_root(root: Path | str) -> dict[str, Any]:
    """`embedder_summary` for a root PATH, opened read-only here.

    The path-taking entry point exists so CLI and MCP clients can report a
    run's geometry without constructing a `Harness` themselves: those clients
    are thin service dispatch by design, and
    `test_clients_have_only_thin_service_dispatch_and_one_registry` enforces
    it by asserting `Harness(` never appears in their source. Opening the
    root belongs to this layer, which already does it for `results_summary`.
    """

    from deepreason.harness import Harness

    return embedder_summary(Harness(Path(root), read_only=True))


def _verification(
    root: Path, replay: dict | None, result: dict | None, *, verify: bool
) -> dict[str, Any]:
    """The `verify_root` verdict: stored by default, re-derived only on demand.

    Re-deriving replays the whole log, which is O(run length); the stored
    record is the run's own published verdict and is what every other reader
    already compares against.

    The two halves live in different files, which is why both are read. The
    violation LIST and the overall verdict are `REPLAY_VALIDATION.json`'s
    (`verification.violations` is empty in exactly the roots whose `valid` is
    true — checked across all 86 committed roots carrying the file); the
    five-channel FAMILY breakdown is `run-result.json`'s
    `verification.finding_counts`, the `verification.summary.v2` shape. On the
    re-derived path both come from one report, and `violations` keeps its
    meaning: integrity plus security findings are exactly what `valid` denies.
    """

    if verify:
        # The `invariants` re-export drops the keyword, and an older root with
        # no published terminal must still be verifiable on demand.
        from deepreason.verification.report import verify_root_report

        report = verify_root_report(root, allow_missing_terminal=True)
        summary = report.summary_payload()
        return {
            "source": "rederived",
            "valid": summary["valid"],
            "violations": len(report.integrity) + len(report.security),
            "families": dict(sorted(summary["finding_counts"].items())),
        }

    if replay is None:
        missing = _absent("NO_REPLAY_VALIDATION_JSON")
        return {
            "source": missing,
            "valid": missing,
            "violations": missing,
            "families": missing,
        }

    stored = replay.get("verification")
    violations: Any = _absent("NO_REPLAY_VALIDATION_JSON")
    if isinstance(stored, dict) and isinstance(stored.get("violations"), list):
        violations = len(stored["violations"])

    published = (result or {}).get("verification")
    families: Any = _absent("NO_FINDING_FAMILIES")
    if isinstance(published, dict) and isinstance(published.get("finding_counts"), dict):
        families = dict(sorted(published["finding_counts"].items()))

    return {
        "source": "stored",
        "valid": bool(replay.get("valid")),
        "violations": violations,
        "families": families,
    }


def _amendment(root: Path) -> dict[str, Any]:
    from deepreason.amendment.state import AmendmentError, load_amendments

    try:
        records = load_amendments(root)
    except AmendmentError:
        unreadable = _absent("AMENDMENT_CHAIN_UNREADABLE")
        return {"epochs": unreadable, "epoch_seqs": unreadable}
    return {"epochs": len(records), "epoch_seqs": [record.seq for record in records]}


def _terminal(replay: dict | None, stop: dict | None) -> dict[str, Any]:
    """Whether the root stands where `deepreason amend`/`continue` can act.

    Both halves are required and they answer different questions: the replay
    verdict says the record is sound, the stop reason says the run ended in a
    state the lifecycle will resume from.
    """

    from deepreason.workflow.lifecycle import RESUMABLE_STOP_REASONS

    binding = (replay or {}).get("terminal_binding")
    has_binding = isinstance(binding, dict)
    valid_terminal = bool(replay and replay.get("valid") and has_binding)

    if stop and stop.get("reason"):
        resumable: Any = stop["reason"] in RESUMABLE_STOP_REASONS
    else:
        resumable = _absent("NO_STOP_RECORD")

    return {
        "valid_typed_terminal": valid_terminal,
        "stop_reason_resumable": resumable,
        "amend_ready": bool(valid_terminal and resumable is True),
        "terminal_epoch": (
            binding.get("terminal_epoch", _absent("NO_TERMINAL_BINDING"))
            if has_binding
            else _absent("NO_REPLAY_VALIDATION_JSON")
        ),
    }


def _show(value: Any) -> str:
    """One fact, rendered so an absence reads as an absence rather than a zero."""

    if _is_absent(value):
        return f"— not recorded ({value['reason']})"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items()) if value else "none"
    return str(value)


def _embedder_line(embedder: dict[str, Any]) -> str:
    """One line naming the geometry, and saying plainly when it is not the
    one the run asked for.

    The fallback is spelled out rather than implied by a differing model id:
    a reader who does not already know that `hashing-128` is the degraded
    backend learns nothing from seeing it, which is how a typed, recorded
    substitution went unread through 24 live cycles.
    """

    if _is_absent(embedder):
        return "not recorded (this run predates the embedder stamp)"
    backend, model = embedder["backend"], embedder["model"]
    if not embedder["fallback"]:
        return f"{backend} ({model})"
    configured = embedder["configured_model"] or "a neural model"
    return (
        f"{backend} (fallback) — this run was configured for {configured} "
        f"but could not build it, so it measured with {model} instead; "
        f"distance readings are on the lexical scale, not the configured one"
    )


def render_results(summary: dict[str, Any]) -> str:
    """The summary as reader-facing text, every technical label glossed in place.

    The gloss is the point, not decoration: this command exists because a
    session confronted with scattered root files invents an interface instead
    of reading one. A label nobody can interpret sends them back to guessing.
    """

    run = summary["run"]
    artifacts = summary["artifacts"]
    verification = summary["verification"]
    terminal = summary["terminal"]
    adjudication = summary["adjudication"]

    lines = [
        f"# Results for {summary['root']}",
        f"  (resolved from a {summary['resolved_from']})",
        "",
        "## Question",
        f"  {_show(summary['question'])}",
        "",
        "## Run",
        f"  run id (the deterministic identity of this run): "
        f"{_show(summary['identity']['run_id'])}",
        f"  state: {_show(run['state'])}",
        f"  stop_reason (the typed reason it ended, never a crash): "
        f"{_show(run['stop_reason'])}",
        f"  cycles completed: {_show(run['cycles_completed'])}",
        f"  tokens spent vs budget: {_show(run['token_spend'])} / "
        f"{_show(run['token_limit'])}",
        f"  manifest (the compiled configuration the run carries) present: "
        f"{_show(summary['identity']['manifest_present'])}, schema version "
        f"{_show(summary['identity']['manifest_schema_version'])}",
        "",
        "## Artifacts",
        f"  accepted / refuted / suspended: {_show(artifacts['accepted'])} / "
        f"{_show(artifacts['refuted'])} / {_show(artifacts['suspended'])}",
        f"  survivors (positions still standing at the end): "
        f"{_show(artifacts['survivor_count'])}",
        f"  frontier (the open edge of the inquiry): "
        f"{_show(artifacts['frontier']['count'])} artifacts, problem "
        f"{_show(artifacts['frontier']['problem_id'])}",
    ]
    ids = artifacts["frontier"]["artifact_ids"]
    if isinstance(ids, list) and ids:
        preview = ", ".join(entry[:12] for entry in ids[:_FRONTIER_PREVIEW])
        more = len(ids) - _FRONTIER_PREVIEW
        lines.append(f"    {preview}" + (f" (+{more} more)" if more > 0 else ""))

    lines += [
        "",
        "## Adjudication (defended trials — a criticism argued and judged)",
        f"  ran: {_show(adjudication['ran'])}",
        f"  judge calls: {_show(adjudication['judge_calls'])}",
        f"  trial verdicts observed: {_show(adjudication['trial_observations'])}",
        f"  trials declined (the case did not sustain): "
        f"{_show(adjudication['trial_declined'])}",
        f"  trials blocked by a guard: {_show(adjudication['trial_blocked'])}",
        "",
        "## Measurement instrument",
        f"  embedder (the model that turned this run's text into vectors, so "
        f"its novelty, near-duplicate and school-distance readings are on "
        f"that model's scale): {_embedder_line(summary['embedder'])}",
        "",
        "## Verification",
        f"  verify_root verdict (the replay check that re-derives the whole run "
        f"from its log and confirms nothing in the record is corrupt or "
        f"altered): {_show(verification['valid'])}",
        f"  read from: {_show(verification['source'])} "
        f"(pass --verify to re-derive it instead of reading the stored verdict)",
        f"  violations: {_show(verification['violations'])}",
        f"  finding families: {_show(verification['families'])}",
        "",
        "## Amendment and terminal readiness",
        f"  amendment epochs (later question/evidence appended without editing "
        f"anything): {_show(summary['amendment']['epochs'])}",
        f"  stands at a valid typed terminal: "
        f"{_show(terminal['valid_typed_terminal'])} (terminal epoch "
        f"{_show(terminal['terminal_epoch'])})",
        f"  stop reason is resumable: {_show(terminal['stop_reason_resumable'])}",
        f"  ready for `deepreason amend` / `deepreason continue`: "
        f"{_show(terminal['amend_ready'])}",
    ]
    if summary["absences"]:
        lines += [
            "",
            "## Not recorded by this root",
            *(f"  {reason}" for reason in summary["absences"]),
        ]
    return "\n".join(lines)


def _collect_absences(value: Any, into: set[str]) -> None:
    if _is_absent(value):
        into.add(str(value.get("reason")))
        return
    if isinstance(value, dict):
        for inner in value.values():
            _collect_absences(inner, into)


def results_summary(path: Path | str, *, verify: bool = False) -> dict[str, Any]:
    """One run's typed outcome as a JSON-stable record. Reads only; never writes."""

    from deepreason.findings import findings_summary
    from deepreason.harness import Harness

    root, resolved_from = resolve_results_root(path)

    try:
        findings = findings_summary(root)
    except Exception:  # noqa: BLE001 - a legacy root may defeat the replay reader
        findings = {}
    positions = findings.get("positions") if isinstance(findings, dict) else None

    status = _read_json(root / "run-status.json")
    result = _read_json(root / "run-result.json")
    replay = _read_json(root / "REPLAY_VALIDATION.json")
    stop = _read_json(root / "run-stop.json")

    harness = Harness(root, read_only=True)
    summary: dict[str, Any] = {
        "schema": RESULTS_SCHEMA,
        "root": str(root),
        "resolved_from": resolved_from,
        "question": findings.get("question") or _absent("NO_RUN_INPUT"),
        "identity": _identity(root, status, replay),
        "run": _run(status, stop),
        "artifacts": _artifacts(positions, status, result),
        "adjudication": _adjudication(harness),
        "embedder": embedder_summary(harness),
        "verification": _verification(root, replay, result, verify=verify),
        "amendment": _amendment(root),
        "terminal": _terminal(replay, stop),
    }
    absences: set[str] = set()
    _collect_absences(summary, absences)
    summary["absences"] = sorted(absences)
    return summary
