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

from deepreason.harness import Harness
from deepreason.scratch.errors import ScratchServiceError
from deepreason.scratch.models import (
    AttentionReceiptV1,
    RetrievalChannel,
    ScratchProvenanceV1,
    domain_hash,
)
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
    if args.at_seq is None:
        root = Path(args.root)
        if not root.exists():
            raise FileNotFoundError(f"read-only harness root does not exist: {root}")
        service = ScratchService(Harness(root))
    else:
        service = _read_service(args)
    limit = _bounded_limit(args.limit)
    block = service.get_block(args.block)
    receipt = None
    if args.at_seq is None:
        state_seq = service.harness._next_seq - 1
        receipt = AttentionReceiptV1.create(
            state_seq=state_seq,
            request_hash=domain_hash(
                "scratch.cli.direct-open.request.v1",
                {"block_id": block.id, "state_seq": state_seq},
            ),
            selected_by_channel={RetrievalChannel.DIRECT_OPEN: [block.id]},
            final_order=[block.id],
            excluded_by_global_limit=[],
            excluded_by_channel={},
            deterministic_seed=0,
            instance=service._instance(),
        )
        service.record_attention_receipt(
            receipt, context_ref="cli:scratch-show"
        )
    revisions = service.revisions(block.id)
    links = service.links_for(block.id, include_retired=args.include_retired)
    cluster_ids = sorted(service.state.clusters_by_block.get(block.id, set()))
    visibility = service.state.visibility.get(block.id)
    result = {
        "block": _canonical(block),
        "revisions": [_block_summary(service, item) for item in revisions[:limit]],
        "revision_count": len(revisions),
        "links": [_link_summary(service, item) for item in links[:limit]],
        "link_count": len(links),
        "cluster_ids": cluster_ids[:limit],
        "cluster_count": len(cluster_ids),
        "visibility": _canonical(visibility) if visibility is not None else None,
        "retrieval_receipt_id": receipt.id if receipt is not None else None,
    }
    lines = [_label(service, "block", block.id), "", _terminal_safe(block.body.content)]
    for title, value in (
        ("why keep this", block.body.why_keep_this),
        ("unfinished", block.body.unfinished),
        ("possible next move", block.body.possible_next_move),
    ):
        if value is not None:
            lines.extend(("", f"{title}: {_terminal_safe(value)}"))
    lines.append(
        f"\nlinks: {len(links)} · clusters: {len(cluster_ids)} · revisions: {len(revisions)}"
    )
    return result, "\n".join(lines)


def _search(args) -> tuple[dict[str, Any], str]:
    service = _read_service(args)
    query = _bounded_text(args.query, location="/query", maximum=16_384)
    blocks = service.search_phrase(query, _bounded_limit(args.limit))
    summaries = [_block_summary(service, block) for block in blocks]
    result = {"query": query, "blocks": summaries, "count": len(summaries)}
    lines = [f"literal matches ({len(blocks)}):"]
    lines.extend(
        f"  {_label(service, 'block', block.id)}  {_preview(block.body.content)}"
        for block in blocks
    )
    if not blocks:
        lines.append("  (none)")
    return result, "\n".join(lines)


def _related(args) -> tuple[dict[str, Any], str]:
    service = _read_service(args)
    limit = _bounded_limit(args.limit)
    focus = service.get_block(args.block)
    neighbours: dict[str, list[str]] = {}
    link_records = service.links_for(focus.id, include_retired=args.include_retired)
    link_summaries: list[dict[str, Any]] = []
    for link in link_records[:limit]:
        other = link.body.to if link.body.from_ == focus.id else link.body.from_
        neighbours.setdefault(other, []).append("link")
        link_summaries.append(_link_summary(service, link))

    cluster_summaries: list[dict[str, Any]] = []
    for cluster_id in sorted(service.state.clusters_by_block.get(focus.id, set()))[:limit]:
        members = service.cluster_members(cluster_id)
        for block in members[: limit + 1]:
            if block.id != focus.id:
                neighbours.setdefault(block.id, []).append("cluster")
        cluster = service.get_cluster(cluster_id)
        cluster_summaries.append(
            {
                "cluster_id": cluster.id,
                "focus_preview": _preview(cluster.seed_focus),
                "member_count": len(members),
            }
        )

    similarity: list[tuple[float, str, str, Any]] = []
    for hit_id in service.state.similarity_by_block.get(focus.id, []):
        hit = service.state.similarity_hits[hit_id]
        other = hit.block_b if hit.block_a == focus.id else hit.block_a
        similarity.append((-hit.score, other, hit.id, hit))
    similarity.sort(key=lambda item: (item[0], item[1], item[2]))
    similarity_summaries: list[dict[str, Any]] = []
    for _negative_score, other, _hit_id, hit in similarity[:limit]:
        neighbours.setdefault(other, []).append("semantic_similarity")
        similarity_summaries.append(
            {
                "similarity_id": hit.id,
                "block_id": other,
                "score": hit.score,
                "threshold_used": hit.threshold_used,
                "embedder": hit.embedder,
                "embedder_version": hit.embedder_version,
            }
        )

    ordered_ids = list(neighbours)[:limit]
    blocks = [service.get_block(block_id) for block_id in ordered_ids]
    block_results = []
    for block in blocks:
        summary = _block_summary(service, block)
        summary["channels"] = list(dict.fromkeys(neighbours[block.id]))
        block_results.append(summary)
    result = {
        "focus_block_id": focus.id,
        "blocks": block_results,
        "links": link_summaries,
        "clusters": cluster_summaries,
        "similarity_observations": similarity_summaries,
        "count": len(block_results),
        "advisory_warning": (
            "Similarity is retrieval-only and does not establish identity, truth, "
            "support, attack, duplication, or deletion."
        ),
    }
    lines = [f"related to {_label(service, 'block', focus.id)} ({len(blocks)}):"]
    for block in blocks:
        channels = ", ".join(dict.fromkeys(neighbours[block.id]))
        lines.append(
            f"  {_label(service, 'block', block.id)} [{channels}]  "
            f"{_preview(block.body.content)}"
        )
    if not blocks:
        lines.append("  (none)")
    lines.append("similarity is retrieval-only; blocks remain separate immutable instances")
    return result, "\n".join(lines)


def _map(args) -> tuple[dict[str, Any], str]:
    service = _read_service(args)
    limit = _bounded_limit(args.limit)
    clusters = service.cluster_map(limit, ordering=args.ordering)
    results = []
    lines = [f"scratch cluster map ({len(clusters)}):"]
    for cluster in clusters:
        members = service.cluster_members(cluster.id)
        guides = service.state.guides_by_cluster.get(cluster.id, [])
        guide = max(guides, key=lambda item: (item.instance.seq, item.id)) if guides else None
        guide_state = service.state.guide_state(guide) if guide is not None else None
        results.append(
            {
                "cluster_id": cluster.id,
                "focus_preview": _preview(cluster.seed_focus),
                "member_count": len(members),
                "member_ids": [block.id for block in members[:limit]],
                "members_truncated": len(members) > limit,
                "guide_id": guide.id if guide is not None else None,
                "guide_state": guide_state,
            }
        )
        guide_label = f" · guide {guide_state}" if guide_state else ""
        lines.append(
            f"  {_label(service, 'cluster', cluster.id)} · {len(members)} blocks"
            f"{guide_label}  {_preview(cluster.seed_focus)}"
        )
    if not clusters:
        lines.append("  (none)")
    clustered = set().union(*service.state.current_memberships.values()) if service.state.current_memberships else set()
    result = {
        "clusters": results,
        "count": len(results),
        "ordering": args.ordering,
        "unclustered_block_count": len(set(service.state.blocks) - clustered),
    }
    return result, "\n".join(lines)


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
        result, human = handlers[args.scratch_command]()
    except (ScratchServiceError, ScratchCliInputError, FileNotFoundError, OSError, ValueError) as error:
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
