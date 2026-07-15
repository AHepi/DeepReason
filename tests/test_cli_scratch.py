"""C10 CLI coverage for bounded advisory scratch operations."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import pytest

from deepreason.cli.scratch import (
    MAX_INPUT_BYTES,
    MAX_INPUT_CHARS,
    MAX_RESULTS,
    dispatch_scratch,
    register_scratch_parser,
)
from deepreason.harness import Harness
from deepreason.scratch.errors import ScratchLinkPrefixAmbiguous
from deepreason.scratch.models import SimilarityHitV1
from deepreason.scratch.service import ScratchService
from deepreason.scratch.state import LinkState


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepreason")
    parser.add_argument("--root", default=".deepreason")
    parser.add_argument("--config", default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    register_scratch_parser(commands)
    return parser


def _invoke(root: Path, *arguments: str, stdin: str = ""):
    args = _parser().parse_args(["--root", str(root), "scratch", *arguments])
    stdout = io.StringIO()
    stderr = io.StringIO()
    status = dispatch_scratch(
        args,
        stdin=io.StringIO(stdin),
        stdout=stdout,
        stderr=stderr,
    )
    return status, stdout.getvalue(), stderr.getvalue()


def _json(root: Path, *arguments: str, stdin: str = "") -> dict:
    status, stdout, stderr = _invoke(root, *arguments, "--json", stdin=stdin)
    assert status == 0, stderr
    return json.loads(stdout)


def _snapshot(root: Path) -> dict[str, tuple]:
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        stat = path.stat()
        result[relative] = (
            path.is_dir(),
            stat.st_size,
            stat.st_mtime_ns,
            None if path.is_dir() else hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return result


def _create(root: Path, content: str):
    return ScratchService(root).create_block(
        {"content": content}, {"actor": "user", "origin": "test-fixture"}
    )


def test_parser_covers_every_planned_scratch_command():
    parser = _parser()
    cases = [
        ["scratch", "add", "--content", "x"],
        ["scratch", "revise", "abc", "--content", "x"],
        ["scratch", "link", "a", "b", "--relation", "may explain"],
        ["scratch", "retire-link", "a", "--reason", "superseded"],
        ["scratch", "cluster", "create", "--focus", "local puzzle"],
        ["scratch", "cluster", "add", "c", "b"],
        ["scratch", "cluster", "remove", "c", "b"],
        ["scratch", "show", "b", "--at-seq", "2"],
        ["scratch", "search", "query", "--at-seq", "2"],
        ["scratch", "related", "b", "--at-seq", "2"],
        ["scratch", "map", "--at-seq", "2"],
        ["scratch", "dormant", "--at-seq", "2"],
        ["scratch", "underexposed", "--at-seq", "2"],
        ["scratch", "sample", "--at-seq", "2"],
        ["scratch", "coverage", "--at-seq", "2"],
    ]
    for case in cases:
        parsed = parser.parse_args(case)
        assert parsed.command == "scratch"


def test_add_accepts_content_file_and_stdin_without_optional_field_repair(tmp_path):
    root = tmp_path / "run"
    minimal = _json(root, "add", "--content", "a loose thought")
    block = minimal["result"]
    assert block["id"].startswith("sha256:")
    assert block["body"] == {"content": "a loose thought"}
    assert block["provenance"] == {
        "actor": "user",
        "formal_artifact_refs": [],
        "origin": "cli:scratch-add",
        "source_refs": [],
    }

    source = tmp_path / "thought.txt"
    source.write_text("a file thought\n", encoding="utf-8")
    from_file = _json(
        root,
        "add",
        "--file",
        str(source),
        "--why-keep-this",
        "it tests another angle",
    )["result"]
    assert from_file["body"] == {
        "content": "a file thought\n",
        "why_keep_this": "it tests another angle",
    }

    piped = _json(root, "add", stdin="a piped thought")["result"]
    assert piped["body"] == {"content": "a piped thought"}
    assert set(ScratchService(root).state.blocks) == {
        block["id"],
        from_file["id"],
        piped["id"],
    }


def test_revisions_branch_and_scratch_mutation_does_not_change_formal_state(tmp_path):
    root = tmp_path / "run"
    parent = _json(root, "add", "--content", "parent")["result"]
    formal_before = Harness(root).state.model_dump_json()
    prefix = parent["id"][7:15]
    first = _json(root, "revise", prefix, "--content", "branch one")["result"]
    second = _json(root, "revise", prefix, "--content", "branch two")["result"]

    service = ScratchService(root)
    assert first["revision_of"] == parent["id"] == second["revision_of"]
    assert [item.id for item in service.revisions(parent["id"])] == sorted(
        [first["id"], second["id"]],
        key=lambda item: (service.state.blocks[item].instance.seq, item),
    )
    assert service.get_block(parent["id"]).body.content == "parent"
    assert service.get_block(first["id"]).provenance.origin == "cli:scratch-revise"
    assert Harness(root).state.model_dump_json() == formal_before


def test_links_use_human_phrases_short_prefixes_and_remain_historical(tmp_path):
    root = tmp_path / "run"
    first = _json(root, "add", "--content", "first idea")["result"]
    second = _json(root, "add", "--content", "second idea")["result"]
    first_link = _json(
        root,
        "link",
        first["id"][7:15],
        second["id"][7:15],
        "--relation",
        "may be a boundary case for",
        "--because",
        "the qualifications differ",
    )["result"]
    service = ScratchService(root)
    assert service.state.link_status[first_link["id"]] == LinkState.SUGGESTED

    replacement = _json(
        root,
        "link",
        first["id"][7:15],
        second["id"][7:15],
        "--relation",
        "qualifies",
        "--supersedes",
        first_link["id"][7:15],
    )["result"]
    service = ScratchService(root)
    assert service.state.link_status[first_link["id"]] == LinkState.SUPERSEDED
    replacement_seq = service.get_link(replacement["id"]).instance.seq

    retired = _json(
        root,
        "retire-link",
        replacement["id"][7:15],
        "--reason",
        "the relation was misleading",
    )["result"]
    assert retired["status"] == "retired"
    assert ScratchService(root).get_link(replacement["id"]).id == replacement["id"]
    historical = ScratchService(root, upto_seq=replacement_seq)
    assert historical.state.link_status[replacement["id"]] == LinkState.SUGGESTED


def test_link_prefix_ambiguity_has_a_stable_typed_error(tmp_path):
    service = ScratchService(tmp_path / "run")
    left = service.create_block({"content": "left"}, {"actor": "user"})
    right = service.create_block({"content": "right"}, {"actor": "user"})
    by_first: dict[str, list[str]] = {}
    ambiguous = None
    for index in range(128):
        link = service.create_link(
            {"from": left.id, "to": right.id, "relation_hint": f"relation {index}"},
            {"actor": "user"},
        )
        values = by_first.setdefault(link.id[7], [])
        values.append(link.id)
        if len(values) == 2:
            ambiguous = link.id[7]
            break
    assert ambiguous is not None
    with pytest.raises(ScratchLinkPrefixAmbiguous) as error:
        service.get_link(ambiguous)
    assert error.value.code == "SCRATCH_LINK_PREFIX_AMBIGUOUS"


def test_cluster_create_add_remove_and_bounded_map(tmp_path):
    root = tmp_path / "run"
    block = _json(root, "add", "--content", "cluster member")["result"]
    cluster = _json(
        root, "cluster", "create", "--focus", "ways to falsify the mechanism"
    )["result"]
    added = _json(
        root,
        "cluster",
        "add",
        cluster["id"][7:15],
        block["id"][7:15],
        "--reason",
        "same local question",
    )["result"]
    assert added["action"] == "add"
    mapped = _json(root, "map", "--limit", "1")["result"]
    assert mapped["clusters"][0]["cluster_id"] == cluster["id"]
    assert mapped["clusters"][0]["member_ids"] == [block["id"]]

    removed = _json(
        root,
        "cluster",
        "remove",
        cluster["id"][7:15],
        block["id"][7:15],
    )["result"]
    assert removed["action"] == "remove"
    assert _json(root, "map")["result"]["clusters"][0]["member_count"] == 0


def test_search_related_map_dormant_underexposed_sample_and_coverage_are_pure(tmp_path):
    root = tmp_path / "run"
    service = ScratchService(root)
    focus = service.create_block({"content": "alpha anchor"}, {"actor": "user"})
    linked = service.create_block({"content": "alpha linked"}, {"actor": "user"})
    semantic = service.create_block({"content": "remote wording"}, {"actor": "user"})
    service.create_link(
        {"from": focus.id, "to": linked.id, "relation_hint": "provisional neighbour"},
        {"actor": "user"},
    )
    cluster = service.create_cluster("local alpha map", {"actor": "user"})
    service.add_cluster_member(cluster.id, focus.id, None, {"actor": "user"})
    service.add_cluster_member(cluster.id, linked.id, None, {"actor": "user"})
    hit = SimilarityHitV1.create(
        block_a=min(focus.id, semantic.id),
        block_b=max(focus.id, semantic.id),
        embedder="scripted",
        embedder_version="1",
        score=0.91,
        threshold_used=0.7,
        input_body_hash_a=(
            focus.body_hash if focus.id < semantic.id else semantic.body_hash
        ),
        input_body_hash_b=(
            semantic.body_hash if focus.id < semantic.id else focus.body_hash
        ),
        output_ref="fixture-vector",
        instance=service._instance(),
    )
    service.record_similarity(hit)
    service.start_coverage_cycle()
    events_before = (root / "log.jsonl").read_bytes()

    search = _json(root, "search", "alpha", "--limit", "1")["result"]
    assert search["count"] == 1
    assert search["blocks"][0]["block_id"].startswith("sha256:")
    related = _json(root, "related", focus.id[7:15], "--limit", "3")["result"]
    assert {item["block_id"] for item in related["blocks"]} == {linked.id, semantic.id}
    assert related["similarity_observations"][0]["similarity_id"] == hit.id
    assert "retrieval-only" in related["advisory_warning"]
    assert _json(root, "map", "--limit", "1")["result"]["count"] == 1
    assert _json(
        root, "dormant", "--after-events", "0", "--limit", "2"
    )["result"]["count"] == 2
    assert _json(root, "underexposed", "--limit", "2")["result"]["count"] == 2
    first_sample = _json(root, "sample", "--seed", "19", "--limit", "2")["result"]
    second_sample = _json(root, "sample", "--seed", "19", "--limit", "2")["result"]
    assert first_sample == second_sample
    coverage = _json(root, "coverage", "--limit", "1")["result"]
    assert coverage["cycles"][0]["state"] == "active"
    assert coverage["cycles"][0]["pending_count"] == 3
    assert (root / "log.jsonl").read_bytes() == events_before


def test_human_output_uses_short_ids_and_neutralizes_terminal_controls(tmp_path):
    root = tmp_path / "run"
    status, stdout, stderr = _invoke(
        root, "add", "--content", "untrusted \x1b[31mred\x1b[0m thought"
    )
    assert status == 0 and not stderr
    assert "sha256:" not in stdout
    assert "\\u001b[31mred\\u001b[0m" in stdout
    assert "\x1b" not in stdout


def test_current_show_records_direct_open_visibility_but_historical_show_does_not(tmp_path):
    root = tmp_path / "run"
    block = _create(root, "open this block")
    log_before = (root / "log.jsonl").read_bytes()
    shown = _json(root, "show", block.id[7:15])["result"]
    assert shown["retrieval_receipt_id"].startswith("sha256:")
    current = ScratchService(root)
    visibility = current.state.visibility[block.id]
    assert visibility.render_count == 1
    assert [channel.value for channel in visibility.retrieval_channels_used] == [
        "direct_open"
    ]
    assert (root / "log.jsonl").read_bytes() != log_before

    before_historical = _snapshot(root)
    historical = _json(root, "show", block.id[7:15], "--at-seq", "0")["result"]
    assert historical["retrieval_receipt_id"] is None
    assert _snapshot(root) == before_historical


def test_historical_reads_are_physically_read_only_for_every_read_command(tmp_path):
    root = tmp_path / "run"
    service = ScratchService(root)
    first = service.create_block({"content": "first alpha"}, {"actor": "user"})
    service.create_block({"content": "later alpha"}, {"actor": "user"})
    before = _snapshot(root)
    commands = [
        ("show", first.id[7:15]),
        ("search", "alpha"),
        ("related", first.id[7:15]),
        ("map",),
        ("dormant", "--after-events", "0"),
        ("underexposed",),
        ("sample", "--seed", "1"),
        ("coverage",),
    ]
    for command in commands:
        status, _stdout, stderr = _invoke(
            root, *command, "--at-seq", "0", "--json"
        )
        assert status == 0, stderr
    assert _snapshot(root) == before


def test_read_errors_do_not_create_roots_and_json_errors_are_typed(tmp_path):
    missing = tmp_path / "missing"
    status, stdout, stderr = _invoke(missing, "search", "anything", "--json")
    assert status == 1 and not stdout
    error = json.loads(stderr)
    assert error["error"]["code"] == "SCRATCH_RUN_NOT_FOUND"
    assert not missing.exists()

    root = tmp_path / "run"
    _create(root, "one")
    status, _stdout, stderr = _invoke(
        root, "search", "one", "--limit", str(MAX_RESULTS + 1), "--json"
    )
    assert status == 1
    assert json.loads(stderr)["error"]["location"] == "/limit"
    status, _stdout, stderr = _invoke(
        root, "search", "one", "--at-seq", "-1", "--json"
    )
    assert status == 1
    assert json.loads(stderr)["error"]["location"] == "/at_seq"


def test_content_sources_reject_directories_non_utf8_and_oversized_payloads(tmp_path):
    root = tmp_path / "run"
    status, _stdout, stderr = _invoke(
        root, "add", "--file", str(tmp_path), "--json"
    )
    assert status == 1
    assert json.loads(stderr)["error"]["location"] == "/file"

    binary = tmp_path / "binary"
    binary.write_bytes(b"\xff\xfe")
    status, _stdout, stderr = _invoke(
        root, "add", "--file", str(binary), "--json"
    )
    assert status == 1
    assert "UTF-8" in json.loads(stderr)["error"]["message"]

    oversized = tmp_path / "oversized"
    oversized.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
    status, _stdout, stderr = _invoke(
        root, "add", "--file", str(oversized), "--json"
    )
    assert status == 1
    assert "exceeds" in json.loads(stderr)["error"]["message"]

    status, _stdout, stderr = _invoke(
        root, "add", "--json", stdin="x" * (MAX_INPUT_CHARS + 1)
    )
    assert status == 1
    assert json.loads(stderr)["error"]["location"] == "/content"
