"""Approachable CLI surface for the canonical advisory scratch workspace.

This module owns presentation and argv handling only. Canonical identities,
append-only events, replay, prefix resolution, and read-only enforcement stay
in :mod:`deepreason.scratch.service` and :mod:`deepreason.harness`.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TextIO

from deepreason.application.scratch import (
    SCRATCH_QUERY_SERVICE,
    ScratchMapQueryV1,
    ScratchOpenPreviewQueryV1,
    ScratchRecordDirectOpenQueryV1,
    ScratchRelatedQueryV1,
    ScratchSearchQueryV1,
)
from deepreason.harness import Harness
from deepreason.locking import ProcessLockBusy, ProcessLockError, operator_locks
from deepreason.scratch.errors import ScratchRootBusy, ScratchServiceError
from deepreason.scratch.models import ScratchProvenanceV1
from deepreason.scratch.service import ScratchService


MAX_INPUT_CHARS = 262_144
MAX_INPUT_BYTES = MAX_INPUT_CHARS * 4
MAX_RESULTS = 100
DEFAULT_RESULTS = 20
PREVIEW_CHARS = 320


class ScratchCliInputError(ValueError):
    """Stable validation error for CLI-only inputs."""

    code = "SCRATCH_INPUT_INVALID"

    def __init__(self, message: str, *, location: str = "") -> None:
        self.location = location
        super().__init__(message)


def _add_json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json", action="store_true", help="emit stable machine-readable JSON"
    )


def _add_limit(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_RESULTS,
        help=f"maximum results (default {DEFAULT_RESULTS}, maximum {MAX_RESULTS})",
    )


def _add_history(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--at-seq",
        type=int,
        default=None,
        help="open the append-only scratch history at this read-only event sequence",
    )


def _add_content_input(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--content", help="block content as text")
    source.add_argument("--file", help="read block content from this explicit file")
    parser.add_argument("--why-keep-this", default=None)
    parser.add_argument("--unfinished", default=None)
    parser.add_argument("--possible-next-move", default=None)


def register_scratch_parser(subparsers) -> argparse.ArgumentParser:
    """Register the ``scratch`` family under an existing argparse subparser."""

    scratch = subparsers.add_parser(
        "scratch", help="create and browse non-authoritative scratch material"
    )
    commands = scratch.add_subparsers(dest="scratch_command", required=True)

    add = commands.add_parser("add", help="add one immutable loose scratch block")
    _add_content_input(add)
    _add_json(add)

    revise = commands.add_parser(
        "revise", help="create an immutable revision branching from a block"
    )
    revise.add_argument("block")
    _add_content_input(revise)
    _add_json(revise)

    link = commands.add_parser("link", help="suggest a provisional human-readable link")
    link.add_argument("from_block")
    link.add_argument("to_block")
    link.add_argument("--relation", required=True, help="plain-language relation phrase")
    link.add_argument("--because", default=None)
    link.add_argument("--holds-when", default=None)
    link.add_argument("--weakens-when", default=None)
    link.add_argument("--direction", choices=("directed", "symmetric"), default=None)
    link.add_argument("--supersedes", default=None, help="link ID or unique prefix")
    _add_json(link)

    retire = commands.add_parser("retire-link", help="retire a provisional link")
    retire.add_argument("link")
    retire.add_argument("--reason", required=True)
    _add_json(retire)

    cluster = commands.add_parser("cluster", help="manage provisional navigation clusters")
    cluster_commands = cluster.add_subparsers(dest="cluster_command", required=True)
    create_cluster = cluster_commands.add_parser("create", help="create a cluster")
    create_cluster.add_argument("--focus", required=True, help="plain-language local focus")
    _add_json(create_cluster)
    for action in ("add", "remove"):
        membership = cluster_commands.add_parser(
            action, help=f"{action} one block {'to' if action == 'add' else 'from'} a cluster"
        )
        membership.add_argument("cluster")
        membership.add_argument("block")
        membership.add_argument("--reason", default=None)
        _add_json(membership)

    show = commands.add_parser("show", help="open one block by ID or unique prefix")
    show.add_argument("block")
    show.add_argument("--include-retired", action="store_true")
    _add_limit(show)
    _add_history(show)
    _add_json(show)

    search = commands.add_parser("search", help="deterministic literal scratch search")
    search.add_argument("query")
    _add_limit(search)
    _add_history(search)
    _add_json(search)

    related = commands.add_parser(
        "related", help="show explicit, clustered, and similarity neighbours"
    )
    related.add_argument("block")
    related.add_argument("--include-retired", action="store_true")
    _add_limit(related)
    _add_history(related)
    _add_json(related)

    cluster_map = commands.add_parser("map", help="bounded cluster navigation map")
    cluster_map.add_argument("--ordering", choices=("created", "id", "size"), default="created")
    _add_limit(cluster_map)
    _add_history(cluster_map)
    _add_json(cluster_map)

    dormant = commands.add_parser("dormant", help="blocks not rendered recently")
    dormant.add_argument(
        "--after-events",
        type=int,
        default=None,
        help="query override; default comes from the bound policy or typed config",
    )
    _add_limit(dormant)
    _add_history(dormant)
    _add_json(dormant)

    underexposed = commands.add_parser(
        "underexposed", help="blocks with the fewest rendering opportunities"
    )
    _add_limit(underexposed)
    _add_history(underexposed)
    _add_json(underexposed)

    sample = commands.add_parser(
        "sample", help="deterministic sample independent of semantic relevance"
    )
    sample.add_argument("--seed", type=int, default=0)
    _add_limit(sample)
    _add_history(sample)
    _add_json(sample)

    coverage = commands.add_parser(
        "coverage", help="show append-only anti-starvation coverage progress"
    )
    _add_limit(coverage)
    _add_history(coverage)
    _add_json(coverage)
    return scratch


def _canonical(model) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=True, exclude_none=True)


def _terminal_safe(value: str) -> str:
    """Neutralize terminal controls in untrusted scratch-authored text."""

    result: list[str] = []
    for character in value:
        if character in {"\n", "\t"}:
            result.append(character)
        elif unicodedata.category(character).startswith("C"):
            result.append(f"\\u{ord(character):04x}")
        else:
            result.append(character)
    return "".join(result)


def _preview(value: str, limit: int = PREVIEW_CHARS) -> str:
    normalized = " ".join(_terminal_safe(value).split())
    return normalized if len(normalized) <= limit else normalized[: limit - 1] + "…"


def _short_id(value: str, candidates: Iterable[str]) -> str:
    if not value.startswith("sha256:"):
        return _preview(value, 24)
    suffix = value[7:]
    others = [item[7:] for item in set(candidates) if item != value and item.startswith("sha256:")]
    for length in range(8, len(suffix) + 1):
        prefix = suffix[:length]
        if not any(other.startswith(prefix) for other in others):
            return prefix
    return suffix


def _label(service: ScratchService, kind: str, value: str) -> str:
    candidates = {
        "block": service.state.blocks,
        "link": service.state.links,
        "cluster": service.state.clusters,
        "coverage": service.state.coverage_cycles,
    }[kind]
    return f"{kind} {_short_id(value, candidates)}"


def _query_label(result, kind: str, value: str) -> str:
    candidates = {
        "block": result.identities.block_ids,
        "link": result.identities.link_ids,
        "cluster": result.identities.cluster_ids,
        "coverage": result.identities.coverage_ids,
    }[kind]
    return f"{kind} {_short_id(value, candidates)}"


def _bounded_limit(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_RESULTS:
        raise ScratchCliInputError(
            f"limit must be an integer from 1 through {MAX_RESULTS}", location="/limit"
        )
    return value


def _bounded_text(value: str, *, location: str, maximum: int = MAX_INPUT_CHARS) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScratchCliInputError("text must not be blank", location=location)
    if len(value) > maximum:
        raise ScratchCliInputError(
            f"text exceeds {maximum} characters", location=location
        )
    return value


def _read_explicit_file(value: str) -> str:
    try:
        path = Path(value)
        if not path.is_file():
            raise ScratchCliInputError(
                "--file must name a regular file", location="/file"
            )
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise ScratchCliInputError(
                f"input file exceeds {MAX_INPUT_BYTES} bytes", location="/file"
            )
        raw = path.read_bytes()
    except (OSError, ValueError) as error:
        if isinstance(error, ScratchCliInputError):
            raise
        raise ScratchCliInputError(str(error), location="/file") from error
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ScratchCliInputError("input file must be UTF-8 text", location="/file") from error


def _read_stdin(stdin: TextIO) -> str:
    if getattr(stdin, "isatty", lambda: False)():
        raise ScratchCliInputError(
            "pass --content, --file, or pipe UTF-8 text on stdin", location="/content"
        )
    buffer = getattr(stdin, "buffer", None)
    if buffer is not None:
        raw = buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ScratchCliInputError(
                f"stdin exceeds {MAX_INPUT_BYTES} bytes", location="/content"
            )
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ScratchCliInputError("stdin must be UTF-8 text", location="/content") from error
    value = stdin.read(MAX_INPUT_CHARS + 1)
    if len(value) > MAX_INPUT_CHARS:
        raise ScratchCliInputError(
            f"stdin exceeds {MAX_INPUT_CHARS} characters", location="/content"
        )
    return value


def _block_body(args, stdin: TextIO) -> dict[str, str]:
    if args.content is not None:
        content = args.content
    elif args.file is not None:
        content = _read_explicit_file(args.file)
    else:
        content = _read_stdin(stdin)
    body = {"content": _bounded_text(content, location="/content")}
    for name in ("why_keep_this", "unfinished", "possible_next_move"):
        value = getattr(args, name)
        if value is not None:
            body[name] = _bounded_text(value, location=f"/{name}")
    return body


def _provenance(operation: str) -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor="user", origin=f"cli:scratch-{operation}")


def _writable_service(args) -> ScratchService:
    return ScratchService(Harness(Path(args.root)))


def _read_service(args) -> ScratchService:
    sequence = getattr(args, "at_seq", None)
    if sequence is not None and sequence < 0:
        raise ScratchCliInputError(
            "historical sequence must be non-negative", location="/at_seq"
        )
    root = Path(args.root)
    harness = Harness.at(root, sequence) if sequence is not None else Harness(root, read_only=True)
    return ScratchService(harness)


def _query_sequence(args) -> int | None:
    sequence = getattr(args, "at_seq", None)
    if sequence is not None and sequence < 0:
        raise ScratchCliInputError(
            "historical sequence must be non-negative", location="/at_seq"
        )
    return sequence


def _block_summary(service: ScratchService, block) -> dict[str, Any]:
    visibility = service.state.visibility.get(block.id)
    result: dict[str, Any] = {
        "block_id": block.id,
        "content_preview": _preview(block.body.content),
        "created_seq": block.instance.seq,
        "render_count": visibility.render_count if visibility is not None else 0,
        "last_rendered_seq": (
            visibility.last_rendered_seq if visibility is not None else None
        ),
    }
    if block.revision_of is not None:
        result["revision_of"] = block.revision_of
    return result


def _link_summary(service: ScratchService, link) -> dict[str, Any]:
    return {
        "link_id": link.id,
        "from": link.body.from_,
        "to": link.body.to,
        "relation_hint": _preview(link.body.relation_hint),
        "status": service.state.link_status[link.id].value,
        **({"supersedes": link.body.supersedes} if link.body.supersedes else {}),
    }


def _emit(args, result: dict[str, Any], human: str, stdout: TextIO) -> int:
    if getattr(args, "json", False):
        payload = {
            "schema": "deepreason-cli-scratch-v1",
            "operation": (
                f"cluster.{args.cluster_command}"
                if args.scratch_command == "cluster"
                else args.scratch_command
            ),
            "at_seq": getattr(args, "at_seq", None),
            "result": result,
        }
        print(json.dumps(payload, indent=2, sort_keys=True), file=stdout)
    else:
        print(human, file=stdout)
    return 0


def _error_payload(error: Exception) -> dict[str, Any]:
    if isinstance(error, ScratchServiceError):
        return error.as_dict()
    if isinstance(error, ScratchCliInputError):
        return {
            "code": error.code,
            "message": str(error),
            "location": error.location,
        }
    code = "SCRATCH_RUN_NOT_FOUND" if isinstance(error, FileNotFoundError) else "SCRATCH_INPUT_INVALID"
    return {"code": code, "message": str(error)[:16_384], "location": ""}


def _emit_error(args, error: Exception, stderr: TextIO) -> int:
    payload = _error_payload(error)
    if getattr(args, "json", False):
        print(
            json.dumps(
                {"schema": "deepreason-cli-error-v1", "ok": False, "error": payload},
                indent=2,
                sort_keys=True,
            ),
            file=stderr,
        )
    else:
        location = f" at {payload['location']}" if payload["location"] else ""
        print(
            f"{payload['code']}{location}: {_terminal_safe(payload['message'])}",
            file=stderr,
        )
    return 1


def _add(args, stdin: TextIO) -> tuple[dict[str, Any], str]:
    service = _writable_service(args)
    block = service.create_block(_block_body(args, stdin), _provenance("add"))
    return _canonical(block), f"created {_label(service, 'block', block.id)}\n{_preview(block.body.content)}"


def _revise(args, stdin: TextIO) -> tuple[dict[str, Any], str]:
    service = _writable_service(args)
    block = service.revise_block(
        args.block, _block_body(args, stdin), _provenance("revise")
    )
    return _canonical(block), (
        f"created {_label(service, 'block', block.id)} as a revision of "
        f"{_label(service, 'block', block.revision_of)}\n{_preview(block.body.content)}"
    )


def _create_link(args) -> tuple[dict[str, Any], str]:
    service = _writable_service(args)
    from_id = service.get_block(args.from_block).id
    to_id = service.get_block(args.to_block).id
    body: dict[str, Any] = {
        "from": from_id,
        "to": to_id,
        "relation_hint": _bounded_text(args.relation, location="/relation"),
    }
    for argument, field in (
        ("because", "because"),
        ("holds_when", "holds_when"),
        ("weakens_when", "weakens_when"),
        ("direction", "direction"),
    ):
        value = getattr(args, argument)
        if value is not None:
            body[field] = value
    if args.supersedes is not None:
        body["supersedes"] = service.get_link(args.supersedes).id
    link = service.create_link(body, _provenance("link"))
    human = (
        f"suggested {_label(service, 'link', link.id)}: "
        f"{_label(service, 'block', from_id)} — {_preview(link.body.relation_hint)} → "
        f"{_label(service, 'block', to_id)}"
    )
    return _canonical(link), human


def _retire_link(args) -> tuple[dict[str, Any], str]:
    service = _writable_service(args)
    link = service.retire_link(
        args.link,
        _bounded_text(args.reason, location="/reason"),
        _provenance("retire-link"),
    )
    result = _link_summary(service, link)
    result["reason"] = args.reason
    return result, f"retired {_label(service, 'link', link.id)}: {_preview(args.reason)}"


def _cluster(args) -> tuple[dict[str, Any], str]:
    service = _writable_service(args)
    if args.cluster_command == "create":
        cluster = service.create_cluster(
            _bounded_text(args.focus, location="/focus"), _provenance("cluster-create")
        )
        return _canonical(cluster), (
            f"created {_label(service, 'cluster', cluster.id)}\n"
            f"focus: {_preview(cluster.seed_focus)}"
        )
    cluster = service.get_cluster(args.cluster)
    block = service.get_block(args.block)
    reason = (
        _bounded_text(args.reason, location="/reason")
        if args.reason is not None
        else None
    )
    method = (
        service.add_cluster_member
        if args.cluster_command == "add"
        else service.remove_cluster_member
    )
    record = method(
        cluster.id,
        block.id,
        reason,
        _provenance(f"cluster-{args.cluster_command}"),
    )
    verb = "added to" if args.cluster_command == "add" else "removed from"
    return _canonical(record), (
        f"{_label(service, 'block', block.id)} {verb} "
        f"{_label(service, 'cluster', cluster.id)}"
    )


def _show(args) -> tuple[dict[str, Any], str]:
    limit = _bounded_limit(args.limit)
    sequence = _query_sequence(args)
    if sequence is None:
        result = SCRATCH_QUERY_SERVICE.execute(
            ScratchRecordDirectOpenQueryV1(
                root=str(args.root),
                block=args.block,
                include_retired=args.include_retired,
                limit=limit,
            )
        )
    else:
        result = SCRATCH_QUERY_SERVICE.execute(
            ScratchOpenPreviewQueryV1(
                root=str(args.root),
                at_seq=sequence,
                block=args.block,
                include_retired=args.include_retired,
                limit=limit,
            )
        )
    block = result.block
    lines = [
        _query_label(result, "block", block.id),
        "",
        _terminal_safe(block.body.content),
    ]
    for title, value in (
        ("why keep this", block.body.why_keep_this),
        ("unfinished", block.body.unfinished),
        ("possible next move", block.body.possible_next_move),
    ):
        if value is not None:
            lines.extend(("", f"{title}: {_terminal_safe(value)}"))
    lines.append(
        f"\nlinks: {result.link_count} · clusters: {result.cluster_count} · "
        f"revisions: {result.revision_count}"
    )
    return result.presentation_payload(include_committed=False), "\n".join(lines)


def _search(args) -> tuple[dict[str, Any], str]:
    query = _bounded_text(args.query, location="/query", maximum=16_384)
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchSearchQueryV1(
            root=str(args.root),
            at_seq=_query_sequence(args),
            limit=_bounded_limit(args.limit),
            query=query,
        )
    )
    lines = [f"literal matches ({result.count}):"]
    lines.extend(
        f"  {_query_label(result, 'block', block.block_id)}  {block.content_preview}"
        for block in result.blocks
    )
    if not result.blocks:
        lines.append("  (none)")
    return result.presentation_payload(), "\n".join(lines)


def _related(args) -> tuple[dict[str, Any], str]:
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchRelatedQueryV1(
            root=str(args.root),
            at_seq=_query_sequence(args),
            limit=_bounded_limit(args.limit),
            block=args.block,
            include_retired=args.include_retired,
        )
    )
    lines = [
        f"related to {_query_label(result, 'block', result.focus_block_id)} ({result.count}):"
    ]
    for block in result.blocks:
        channels = ", ".join(block.channels)
        lines.append(
            f"  {_query_label(result, 'block', block.block_id)} [{channels}]  "
            f"{block.content_preview}"
        )
    if not result.blocks:
        lines.append("  (none)")
    lines.append(
        "similarity is retrieval-only; blocks remain separate immutable instances"
    )
    return result.presentation_payload(), "\n".join(lines)


def _map(args) -> tuple[dict[str, Any], str]:
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchMapQueryV1(
            root=str(args.root),
            at_seq=_query_sequence(args),
            limit=_bounded_limit(args.limit),
            ordering=args.ordering,
        )
    )
    lines = [f"scratch cluster map ({result.count}):"]
    for cluster in result.clusters:
        guide_label = f" · guide {cluster.guide_state}" if cluster.guide_state else ""
        lines.append(
            f"  {_query_label(result, 'cluster', cluster.cluster_id)} · "
            f"{cluster.member_count} blocks{guide_label}  {cluster.focus_preview}"
        )
    if not result.clusters:
        lines.append("  (none)")
    return result.presentation_payload(), "\n".join(lines)


def _dormant_threshold(args) -> int:
    if args.after_events is not None:
        value = args.after_events
    else:
        manifest_path = Path(args.root) / "run-manifest.json"
        if manifest_path.is_file():
            from deepreason.run_manifest import load_run_manifest

            manifest = load_run_manifest(manifest_path)
            policy = getattr(manifest, "scratch_policy", None)
            if policy is not None:
                value = policy.dormant_after_events
            else:
                value = None
        else:
            value = None
        if value is None:
            from deepreason.config import load as load_config

            configured = load_config(
                Path(args.config) if getattr(args, "config", None) else None
            )
            value = configured.scratchpad.dormant_after_events
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ScratchCliInputError(
            "after-events must be a non-negative integer", location="/after_events"
        )
    return value


def _dormant(args) -> tuple[dict[str, Any], str]:
    service = _read_service(args)
    limit = _bounded_limit(args.limit)
    threshold = _dormant_threshold(args)
    blocks = service.dormant_blocks(
        max(0, service.harness._next_seq - 1), threshold, limit
    )
    summaries = [_block_summary(service, block) for block in blocks]
    result = {"blocks": summaries, "count": len(summaries), "after_events": threshold}
    lines = [f"dormant blocks after {threshold} events ({len(blocks)}):"]
    lines.extend(
        f"  {_label(service, 'block', block.id)}  {_preview(block.body.content)}"
        for block in blocks
    )
    if not blocks:
        lines.append("  (none)")
    return result, "\n".join(lines)


def _underexposed(args) -> tuple[dict[str, Any], str]:
    service = _read_service(args)
    blocks = service.underexposed_blocks(_bounded_limit(args.limit))
    summaries = [_block_summary(service, block) for block in blocks]
    result = {"blocks": summaries, "count": len(summaries)}
    lines = [f"underexposed blocks ({len(blocks)}):"]
    lines.extend(
        f"  {_label(service, 'block', block.id)}  {_preview(block.body.content)}"
        for block in blocks
    )
    if not blocks:
        lines.append("  (none)")
    return result, "\n".join(lines)


def _sample(args) -> tuple[dict[str, Any], str]:
    service = _read_service(args)
    blocks = service.sample_without_semantic_relevance(
        args.seed, _bounded_limit(args.limit)
    )
    summaries = [_block_summary(service, block) for block in blocks]
    result = {"blocks": summaries, "count": len(summaries), "seed": args.seed}
    lines = [f"deterministic non-semantic sample seed={args.seed} ({len(blocks)}):"]
    lines.extend(
        f"  {_label(service, 'block', block.id)}  {_preview(block.body.content)}"
        for block in blocks
    )
    if not blocks:
        lines.append("  (none)")
    return result, "\n".join(lines)


def _coverage(args) -> tuple[dict[str, Any], str]:
    service = _read_service(args)
    limit = _bounded_limit(args.limit)
    cycles = sorted(
        service.state.coverage_cycles.values(),
        key=lambda item: (-item.cycle.instance.seq, item.cycle.id),
    )[:limit]
    results = []
    lines = [f"coverage cycles ({len(cycles)}):"]
    for progress in cycles:
        result = {
            "cycle_id": progress.cycle.id,
            "started_at_seq": progress.cycle.started_at_seq,
            "state": "completed" if progress.completed else "active",
            "pending_count": len(progress.pending_block_ids),
            "rendered_count": len(progress.rendered_block_ids),
            "pending_block_ids": progress.pending_block_ids[:limit],
            "rendered_block_ids": progress.rendered_block_ids[:limit],
            "blocks_truncated": (
                len(progress.pending_block_ids) > limit
                or len(progress.rendered_block_ids) > limit
            ),
        }
        results.append(result)
        lines.append(
            f"  {_label(service, 'coverage', progress.cycle.id)} · {result['state']} · "
            f"pending {result['pending_count']} · rendered {result['rendered_count']}"
        )
    if not cycles:
        lines.append("  (none active or completed)")
    return {"cycles": results, "count": len(results)}, "\n".join(lines)


def dispatch_scratch(
    args,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Execute one parsed scratch command and return a stable process status."""

    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    handlers = {
        "add": lambda: _add(args, stdin),
        "revise": lambda: _revise(args, stdin),
        "link": lambda: _create_link(args),
        "retire-link": lambda: _retire_link(args),
        "cluster": lambda: _cluster(args),
        "show": lambda: _show(args),
        "search": lambda: _search(args),
        "related": lambda: _related(args),
        "map": lambda: _map(args),
        "dormant": lambda: _dormant(args),
        "underexposed": lambda: _underexposed(args),
        "sample": lambda: _sample(args),
        "coverage": lambda: _coverage(args),
    }
    try:
        locks = None
        mutates = args.scratch_command in {
            "add",
            "revise",
            "link",
            "retire-link",
            "cluster",
        }
        try:
            if mutates:
                try:
                    locks = operator_locks(
                        Path(args.root),
                        owner=f"scratch-{args.scratch_command}",
                        blocking=False,
                    )
                except ProcessLockBusy as error:
                    raise ScratchRootBusy(
                        "another operator owns this run root"
                    ) from error
            result, human = handlers[args.scratch_command]()
        finally:
            if locks is not None:
                locks.release()
    except (
        ScratchServiceError,
        ScratchCliInputError,
        ProcessLockError,
        FileNotFoundError,
        OSError,
        ValueError,
    ) as error:
        return _emit_error(args, error, stderr)
    return _emit(args, result, human, stdout)


__all__ = [
    "DEFAULT_RESULTS",
    "MAX_INPUT_BYTES",
    "MAX_INPUT_CHARS",
    "MAX_RESULTS",
    "ScratchCliInputError",
    "dispatch_scratch",
    "register_scratch_parser",
]
