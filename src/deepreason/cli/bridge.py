"""Grounded final-output bridge commands.

The command surface deliberately exposes only one harness-owned workflow and
read-only views of its canonical records.  Models never receive paths, route
selectors, provider catalogs, or the complete scratch workspace.  Machine
output retains full stable IDs; the default human view uses short unique
prefixes and explicit epistemic labels.
"""

from __future__ import annotations

import json
import sys
import unicodedata

from pydantic import ValidationError

from deepreason.application.bridge import (
    DEFAULT_PAGE_LIMIT,
    GROUNDED_BRIDGE_SERVICE,
    MAX_PAGE_LIMIT,
    BridgeCLIStatusV1,
    GroundedBridgeBuildIntentV1,
    GroundedBridgeClaimsIntentV1,
    GroundedBridgeInspectIntentV1,
    GroundedBridgeResultIntentV1,
    GroundedBridgeSnapshotV1,
    GroundedBridgeStatusIntentV1,
    GroundedBridgeValidateIntentV1,
    _page_values,
    claims_payload,
    inspect_payload,
    load_snapshot,
    load_terminal,
    page_bounds,
    result_payload,
    status_payload,
    validate_payload,
)
from deepreason.bridge.models import BridgeResolution, RenderingMode
from deepreason.locking import ProcessLockError


_SHORT_ID_LENGTH = 12
_DEFAULT_PAGE_LIMIT = DEFAULT_PAGE_LIMIT
_MAX_PAGE_LIMIT = MAX_PAGE_LIMIT
_BridgeSnapshot = GroundedBridgeSnapshotV1
_load_terminal = load_terminal
_load_snapshot = load_snapshot
_page_bounds = page_bounds
_result_payload = result_payload
_claims_payload = claims_payload
_inspect_payload = inspect_payload
_validate_payload = validate_payload
_status_payload = status_payload


_MODE_LABELS = {
    RenderingMode.FACT: "Grounded fact",
    RenderingMode.OBSERVATION: "Recorded observation",
    RenderingMode.INFERENCE: "Supported inference",
    RenderingMode.CONJECTURE: "Surviving conjecture",
    RenderingMode.ASSUMPTION: "Explicit assumption",
    RenderingMode.UNKNOWN: "Unknown",
    RenderingMode.CONFLICT: "Conflicting evidence",
}

_CLAIM_LABELS = {
    "source_fact": "Grounded fact",
    "recorded_observation": "Recorded observation",
    "supported_inference": "Supported inference",
    "surviving_conjecture": "Surviving conjecture",
    "assumption": "Explicit assumption",
    "unknown": "Unknown",
    "conflict": "Conflicting evidence",
}

_RESOLUTION_LABELS = {
    BridgeResolution.ANSWERED: "Answered",
    BridgeResolution.PARTIALLY_ANSWERED: "Partially answered",
    BridgeResolution.UNDERDETERMINED: "Underdetermined",
    BridgeResolution.INSUFFICIENT_EVIDENCE: "Insufficient evidence",
    BridgeResolution.CONFLICTING_EVIDENCE: "Conflicting evidence",
    BridgeResolution.OUTSIDE_SCOPE: "Outside scope",
}


def register_bridge_commands(subparsers) -> None:
    """Register the non-breaking ``bridge`` command family on argparse."""

    bridge = subparsers.add_parser(
        "bridge", help="build and inspect grounded final outputs"
    )
    commands = bridge.add_subparsers(dest="bridge_command", required=True)

    build = commands.add_parser(
        "build", help="build a validated claim ledger, then compose the final output"
    )
    build.add_argument("problem", help="problem ID or unique prefix")
    build.add_argument(
        "--target", choices=("thesis", "summary", "answer"), default="answer"
    )
    build.add_argument(
        "--run-manifest",
        default=None,
        help="explicit schema-6 manifest matching the already-bound run root",
    )
    build.add_argument(
        "--derived-output",
        default=None,
        metavar="DIRECTORY",
        help="build from a historical source fence into a new V6 output directory",
    )
    build.add_argument(
        "--at-seq",
        type=int,
        default=None,
        metavar="SEQ",
        help="historical source event fence (requires --derived-output)",
    )
    build.add_argument(
        "--diagnostic-after-failure",
        action="store_true",
        help="build a labelled noncanonical derived view of a failed source run",
    )
    build.add_argument(
        "--focus-block", action="append", default=[], help="scratch block ID or prefix"
    )
    build.add_argument(
        "--focus-cluster",
        action="append",
        default=[],
        help="scratch cluster ID or prefix",
    )
    build.add_argument("--json", action="store_true", help="emit typed machine JSON")
    _add_page_arguments(build)

    for name, help_text in (
        ("status", "show bridge process status"),
        ("result", "show the latest grounded output"),
        ("inspect", "inspect validation and grounded-review records"),
        ("claims", "inspect the validated claim ledger"),
        ("validate", "re-run deterministic ledger and output validation"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument(
            "--json", action="store_true", help="emit typed machine JSON"
        )
        if name in {"result", "inspect", "claims", "validate"}:
            _add_page_arguments(command)


# Friendly aliases let the dispatcher refactor independently without
# proliferating command implementations.
add_bridge_parser = register_bridge_commands
register_parser = register_bridge_commands


def _add_page_arguments(parser) -> None:
    parser.add_argument(
        "--limit",
        type=int,
        default=_DEFAULT_PAGE_LIMIT,
        help=f"records per collection (default {_DEFAULT_PAGE_LIMIT}, max {_MAX_PAGE_LIMIT})",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="zero-based collection offset",
    )


def _safe_human(value: object, *, maximum: int = 4_096) -> str:
    """Bound untrusted terminal text and neutralize controls/ANSI escapes."""

    text = str(value)
    clipped = text[:maximum]
    rendered: list[str] = []
    for character in clipped:
        if character in "\r\n\t":
            rendered.append(" ")
        elif unicodedata.category(character).startswith("C"):
            rendered.append(f"\\u{ord(character):04x}")
        else:
            rendered.append(character)
    if len(text) > maximum:
        rendered.append("…")
    return "".join(rendered)


def _build_intent(args) -> GroundedBridgeBuildIntentV1:
    try:
        return GroundedBridgeBuildIntentV1(
            root=str(args.root),
            problem=args.problem,
            target=args.target,
            run_manifest_ref=args.run_manifest,
            focus_blocks=tuple(args.focus_block),
            focus_clusters=tuple(args.focus_cluster),
            derived_output=args.derived_output,
            at_seq=args.at_seq,
            diagnostic_after_failure=getattr(
                args, "diagnostic_after_failure", False
            ),
        )
    except ValidationError as error:
        for detail in error.errors(include_url=False):
            cause = detail.get("ctx", {}).get("error")
            if cause is not None and str(cause).startswith("BRIDGE_"):
                raise ValueError(str(cause)) from None
        raise


def _build(args) -> tuple[_BridgeSnapshot, int]:
    result = GROUNDED_BRIDGE_SERVICE.build(_build_intent(args))
    return result.snapshot, result.exit_code


def _unique_short_ids(values) -> dict[str, str]:
    """Return the shortest display prefixes that are unique in this view."""

    ordered = list(dict.fromkeys(value for value in values if value is not None))
    raw = {value: value.removeprefix("sha256:") for value in ordered}
    if not ordered:
        return {}
    maximum = max(len(value) for value in raw.values())
    for width in range(min(_SHORT_ID_LENGTH, maximum), maximum + 1):
        prefixes = {value: body[:width] for value, body in raw.items()}
        if len(set(prefixes.values())) == len(prefixes):
            return prefixes
    return raw


def _grounding_source_count(ledger) -> int:
    references: set[str] = set()
    for entry in ledger.entries:
        for field in (
            "source_refs",
            "evidence_refs",
            "event_refs",
            "trace_refs",
            "formal_observation_refs",
        ):
            references.update(getattr(entry, field) or ())
    return len(references)


def _render_result(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> str:
    limit, offset = _page_bounds(limit, offset)
    terminal = snapshot.terminal
    if terminal.process_status == "failure":
        return "\n".join(
            (
                "Bridge failed",
                f"Error: {terminal.error_code}",
                f"Detail: {_safe_human(terminal.error_message)}",
            )
        )
    output = snapshot.output
    ledger = snapshot.ledger
    sections, section_page = _page_values(
        output.sections, limit=limit, offset=offset
    )
    unresolved, unresolved_page = _page_values(
        output.unresolved_items, limit=limit, offset=offset
    )
    prefixes = _unique_short_ids(
        [ledger.id, *(entry.id for entry in ledger.entries)]
    )
    lines = [f"Resolution: {_RESOLUTION_LABELS[output.resolution]}", "", "Answer:"]
    if sections:
        for section in sections:
            refs = ",".join(prefixes[value] for value in section.ledger_entry_ids)
            lines.append(
                f"  [{_MODE_LABELS[section.rendering_mode]} {refs}] "
                f"{_safe_human(section.text)}"
            )
    elif not output.sections:
        lines.append("  [Unknown] No supported answer is available.")
    else:
        lines.append("  (no answer sections on this page)")
    lines.extend(("", "Unresolved items:"))
    if unresolved:
        for item in unresolved:
            suffix = f" — {_safe_human(item.reason)}" if item.reason else ""
            lines.append(f"  - {_safe_human(item.description)}{suffix}")
    elif output.unresolved_items:
        lines.append("  (no unresolved items on this page)")
    elif output.resolution == BridgeResolution.ANSWERED:
        lines.append("  (none)")
    else:
        lines.append(
            "  - "
            + _safe_human(
                output.resolution_reason or "The result remains unresolved."
            )
        )
    lines.extend(
        (
            "",
            f"Grounding sources: {_grounding_source_count(ledger)}",
            f"Claim ledger: {prefixes[ledger.id]}",
            "Inspect claim details with: deepreason --root RUN bridge claims",
            (
                f"Page: offset {offset}, limit {limit}; "
                f"answer sections {section_page['returned']}/{section_page['total']}, "
                f"unresolved items {unresolved_page['returned']}/{unresolved_page['total']}"
            ),
        )
    )
    return "\n".join(lines)


def _render_claims(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> str:
    limit, offset = _page_bounds(limit, offset)
    ledger = snapshot.ledger
    if ledger is None:
        raise ValueError("BRIDGE_RESULT_HAS_NO_LEDGER")
    entries, entries_page = _page_values(ledger.entries, limit=limit, offset=offset)
    uncovered, uncovered_page = _page_values(
        ledger.uncovered_requirements, limit=limit, offset=offset
    )
    conflicts, conflicts_page = _page_values(
        ledger.source_conflicts, limit=limit, offset=offset
    )
    prefixes = _unique_short_ids([ledger.id, *(entry.id for entry in entries)])
    lines = [
        f"Claim ledger: {prefixes[ledger.id]}",
        (
            f"Claims page: offset {offset}, limit {limit}; "
            f"showing {entries_page['returned']} of {entries_page['total']}"
        ),
    ]
    for entry in entries:
        label = _CLAIM_LABELS[entry.claim_class.value]
        lines.append(
            f"  [{label} {prefixes[entry.id]}] {_safe_human(entry.claim)}"
        )
        if entry.qualification:
            lines.append(f"    Qualification: {_safe_human(entry.qualification)}")
    if uncovered:
        lines.append("Uncovered requirements:")
        for item in uncovered:
            lines.append(f"  - {_safe_human(item.requirement)}")
    if conflicts:
        lines.append(
            f"Source conflicts on page: {conflicts_page['returned']} "
            f"of {conflicts_page['total']}"
        )
    if any(
        page["has_more"]
        for page in (entries_page, uncovered_page, conflicts_page)
    ):
        lines.append(f"More records are available; use --offset {offset + limit}.")
    return "\n".join(lines)


def _render_inspect(snapshot: _BridgeSnapshot) -> str:
    terminal = snapshot.terminal
    ids = _unique_short_ids(
        [
            terminal.evidence_pack_id,
            terminal.claim_ledger_id,
            terminal.bridge_output_id,
        ]
    )
    lines = [
        f"Process: {terminal.process_status}",
        f"Problem: {_safe_human(terminal.problem_id, maximum=512)}",
        f"Formal fence: {terminal.formal_seq}",
        f"Evidence pack: {ids.get(terminal.evidence_pack_id, '-')}",
        f"Claim ledger: {ids.get(terminal.claim_ledger_id, '-')}",
        f"Output: {ids.get(terminal.bridge_output_id, '-')}",
    ]
    if snapshot.validation_report is not None:
        lines.append(
            "Deterministic validation: "
            + ("valid" if snapshot.validation_report.valid else "invalid")
        )
    if snapshot.review is not None:
        lines.append(
            "Grounded review: " + ("passed" if snapshot.review.passed else "findings remain")
        )
    return "\n".join(lines)


def _handle_bridge_command(args) -> int:
    """Execute one already-admitted bridge subcommand."""

    try:
        command = args.bridge_command
        if command in {"build", "result", "inspect", "claims", "validate"}:
            page_limit, page_offset = _page_bounds(args.limit, args.offset)
        else:
            page_limit, page_offset = _DEFAULT_PAGE_LIMIT, 0
        if command == "build":
            snapshot, exit_code = _build(args)
            payload = _result_payload(
                snapshot, limit=page_limit, offset=page_offset
            )
            output = (
                json.dumps(payload, indent=2, sort_keys=True)
                if args.json
                else _render_result(
                    snapshot, limit=page_limit, offset=page_offset
                )
            )
        elif command == "status":
            result = GROUNDED_BRIDGE_SERVICE.status(
                GroundedBridgeStatusIntentV1(root=str(args.root))
            )
            payload = result.presentation_payload()
            if payload.get("state") == "not_started":
                raise ValueError("BRIDGE_RECORD_UNAVAILABLE: bridge-status.json")
            exit_code = result.exit_code
            if args.json:
                output = json.dumps(payload, indent=2, sort_keys=True)
            else:
                resolution = payload.get("resolution")
                resolution_text = (
                    f" — {_RESOLUTION_LABELS[BridgeResolution(resolution)]}"
                    if resolution
                    else ""
                )
                output = f"Bridge: {payload['state']}{resolution_text}"
                if payload.get("error_code"):
                    output += f"\nError: {payload['error_code']}"
        elif command == "result":
            result = GROUNDED_BRIDGE_SERVICE.result(
                GroundedBridgeResultIntentV1(
                    root=str(args.root),
                    limit=page_limit,
                    offset=page_offset,
                )
            )
            payload = result.presentation_payload()
            snapshot = result.snapshot
            if snapshot is None:
                output = (
                    json.dumps(payload, indent=2, sort_keys=True)
                    if args.json
                    else (
                        "Bridge worker failed (operational, non-epistemic)\n"
                        f"Error: {payload['error_code']}\n"
                        f"Type: {payload['error_type']}"
                    )
                )
            else:
                output = (
                    json.dumps(payload, indent=2, sort_keys=True)
                    if args.json
                    else _render_result(
                        snapshot, limit=page_limit, offset=page_offset
                    )
                )
            exit_code = result.exit_code
        elif command == "inspect":
            result = GROUNDED_BRIDGE_SERVICE.inspect(
                GroundedBridgeInspectIntentV1(
                    root=str(args.root),
                    limit=page_limit,
                    offset=page_offset,
                )
            )
            payload = result.presentation_payload()
            snapshot = result.snapshot
            assert snapshot is not None
            output = (
                json.dumps(payload, indent=2, sort_keys=True)
                if args.json
                else _render_inspect(snapshot)
            )
            exit_code = result.exit_code
        elif command == "claims":
            result = GROUNDED_BRIDGE_SERVICE.claims(
                GroundedBridgeClaimsIntentV1(
                    root=str(args.root),
                    limit=page_limit,
                    offset=page_offset,
                )
            )
            payload = result.presentation_payload()
            snapshot = result.snapshot
            assert snapshot is not None
            output = (
                json.dumps(payload, indent=2, sort_keys=True)
                if args.json
                else _render_claims(
                    snapshot, limit=page_limit, offset=page_offset
                )
            )
            exit_code = result.exit_code
        elif command == "validate":
            result = GROUNDED_BRIDGE_SERVICE.validate(
                GroundedBridgeValidateIntentV1(
                    root=str(args.root),
                    limit=page_limit,
                    offset=page_offset,
                )
            )
            payload = result.presentation_payload()
            output = (
                json.dumps(payload, indent=2, sort_keys=True)
                if args.json
                else (
                    "Bridge validation: valid"
                    if result.valid
                    else "Bridge validation: invalid"
                )
            )
            exit_code = result.exit_code
        else:  # pragma: no cover - argparse owns the finite command set
            raise ValueError(f"unknown bridge command: {command}")
        print(output)
        return exit_code
    except (KeyError, ProcessLockError, OSError, ValueError) as error:
        print(_safe_human(error, maximum=2_048), file=sys.stderr)
        return 1


def handle_bridge_command(args) -> int:
    """Admit one V6 root, then execute a parsed bridge subcommand."""

    try:
        from deepreason.cli.main import _admit_v6_root

        _admit_v6_root(args.root, operation=f"CLI bridge {args.bridge_command}")
        if (
            args.bridge_command == "build"
            and getattr(args, "derived_output", None) is not None
        ):
            _admit_v6_root(
                args.derived_output,
                operation="CLI bridge derived output",
            )
            if args.run_manifest is None:
                raise ValueError(
                    "V6_BRIDGE_DERIVED_MANIFEST_REQUIRED: pass the explicit "
                    "schema-6 manifest already bound to the derived output root"
                )
    except (OSError, ValueError) as error:
        print(_safe_human(error, maximum=2_048), file=sys.stderr)
        return 1
    return _handle_bridge_command(args)


dispatch_bridge = handle_bridge_command
run_command = handle_bridge_command


__all__ = [
    "BridgeCLIStatusV1",
    "add_bridge_parser",
    "dispatch_bridge",
    "handle_bridge_command",
    "register_parser",
    "register_bridge_commands",
    "run_command",
]
