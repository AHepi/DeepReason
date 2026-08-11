#!/usr/bin/env python3
"""Blast-radius disclosure gate (Rung G6): given a proposed change's
declared target files/symbols, compute frozen-surface contacts,
reachability changes, consumers, and a plain-language disclosure
summary -- mechanically, so an authorization request never has to be
hand-summarized from memory.

Recorded failure this closes: seven cases (experiments/2026-08-10-
change-blast-radius-analysis/CENSUS.md, Part B) of an authorized change
hiding or disconnecting architecture the request never disclosed --
most directly docs/ERRATA_EXECUTOR.md's 2026-08-09 entry, where a
tranche's own SPEC.md had already found a frozen-surface contact in
prose and the STOP that finding should have forced did not happen
before the commit landed. Every fact this gate reports was, in every
one of those seven cases, statically derivable from the tree at grant
time -- this gate is that derivation, run mechanically instead of by
memory.

Usage:
    python tools/blast_radius.py --files PATH [PATH ...]
                                  [--symbols NAME [NAME ...]]
                                  [--against REF]
    python tools/blast_radius.py --self-test

At least one of --files/--symbols is required unless --self-test.
--against REF additionally diffs the reachability computation between
REF's tree and the current working tree, flagging symbols that cross
the reachable/unreachable boundary. Without --against, reachability is
a snapshot of the working tree only.

Honesty limits, stated here because the disclosure summary states them
again for the operator, per this repo's own "counts are claims" rule
(docs/map/SCHEMA.md):

  - Frozen-surface SYMBOL_INDIRECT contact is a grep-based reference,
    not proof of semantic contact -- report it as plausible, not
    confirmed.
  - Reachability is SYNTACTIC: a call path exists from a known entry
    point. It does NOT prove the path is ever actually exercised --
    a symbol can be syntactically reachable and still never fire
    because of a runtime precondition this gate does not evaluate
    (the exact shape of the property_designer incident this gate's own
    census names, CENSUS.md B4 -- a syntactic call graph would have
    called it "reachable"; the actual defect was that its own
    precondition can never be satisfied by any public path). UNKNOWN is
    reported, never silently folded into REACHABLE or UNREACHABLE, for
    any symbol name the static walk cannot resolve to a definition, and
    for anything reached only through dynamic dispatch (string-keyed
    lookups) the entry-point registry cannot see through.
  - The entry-point registry (ENTRY_POINT_FILES below) is hand-
    maintained, the same way docs/map/INV-frozen-surfaces.md's own
    Owns: lists are hand-maintained but check-verified. A newly-added
    entry point not yet listed here can cause a false UNREACHABLE.

Emits one BLAST_RADIUS_RESULT_V1 JSON object to stdout on success:

    {
      "result_type": "BLAST_RADIUS_RESULT_V1",
      "targets": {"files": [...], "symbols": [...]},
      "base": "<ref or null>",
      "frozen_surface_contacts": [
        {"surface": "...", "tier": "DIRECT"|"SYMBOL_INDIRECT",
         "target": "...", "detail": "..."}
      ],
      "frozen_adjacent_contacts": [ ...same shape... ],
      "reachability": [
        {"symbol": "...", "status_current": "REACHABLE"|"UNREACHABLE"|"UNKNOWN",
         "status_base": "..."|null, "direction": "newly_dead"|"newly_live"|"unchanged"|null}
      ],
      "consumers": {
        "tests": [{"target": "...", "hits": ["<file:line>", ...]}],
        "map_checks": [{"target": "...", "hits": [...]}],
        "qualification_digest": [{"target": "...", "tier": "CONFIRMED"|"PLAUSIBLE"}],
        "wheel_smoke_pins": [{"target": "...", "tier": "CONFIRMED"|"PLAUSIBLE", "pin": "..."}]
      },
      "disclosure_summary": "<plain-language paragraph>",
      "frozen_surface_verdict": "CONTACT" | "CLEAR"
    }

`frozen_surface_verdict` is the only scalar verdict field, deliberately
narrow: a gate reports facts, the owning skill decides policy
(docs/proposals/DETERMINISTIC_GATES_PREPLAN.md's own shape rule).
Reachability and consumer findings are reported as lists for the
calling skill to classify (EXPECTED TO MOVE / MUST NOT MOVE), never
collapsed into a single pass/fail this gate has no standing to declare.

Exit classes -- semantic verdicts live INSIDE the JSON, never in the
exit code:
    0  result emitted       -- JSON printed; frozen_surface_verdict may
                                be CONTACT
    2  invalid invocation   -- neither --files nor --symbols given (and
                                not --self-test); no JSON printed
    3  evidence unavailable -- a declared file does not exist in the
                                tree, or --against names a ref that does
                                not resolve; no JSON printed
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

RESULT_TYPE = "BLAST_RADIUS_RESULT_V1"

# The five frozen surfaces, verbatim from docs/map/INV-frozen-surfaces.md.
FROZEN_SURFACES = [
    {
        "surface": "capabilities/state.py digests and event application",
        "path": "src/deepreason/capabilities/state.py",
    },
    {
        "surface": "harness.py event application and well-formedness",
        "path": "src/deepreason/harness.py",
    },
    {
        "surface": "replay-validation record formats (invariants.py)",
        "path": "src/deepreason/invariants.py",
    },
    {
        "surface": "manifest schemas and validators (run_manifest.py)",
        "path": "src/deepreason/run_manifest.py",
    },
    {
        "surface": "qualification subject digests (qualification.py)",
        "path": "src/deepreason/qualification.py",
    },
]
FROZEN_ADJACENT = [
    {
        "surface": "route_fingerprint serialization (llm/firewall.py)",
        "path": "src/deepreason/llm/firewall.py",
    },
]

# Hand-maintained entry-point registry -- see the module docstring's
# "Honesty limits" section. Every top-level def in one of these files is
# treated as a BFS root (not just a single "main"), so argparse-style
# subcommand dispatch inside a CLI file does not need special-casing.
ENTRY_POINT_FILES = [
    "src/deepreason/cli/main.py",
    "src/deepreason/mcp_server.py",
    "src/deepreason/scheduler/scheduler.py",
]

QUALIFICATION_SOURCE_FILES = [
    "src/deepreason/qualification.py",
    "src/deepreason/run_manifest.py",
]
WHEEL_SMOKE_SOURCE_FILES = [
    "scripts/wheel_smoke.py",
    "scripts/wheel_operational_smoke.py",
]


class InvalidInvocation(Exception):
    pass


class EvidenceUnavailable(Exception):
    pass


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _run_git(args: list[str], cwd: Path) -> str:
    try:
        proc = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    except FileNotFoundError as error:
        raise EvidenceUnavailable(f"git not available: {error}") from error
    if proc.returncode != 0:
        raise EvidenceUnavailable(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


# ---------------------------------------------------------------------
# Computation 1: frozen-surface contacts
# ---------------------------------------------------------------------


def _symbol_referenced(path: Path, symbol: str) -> bool:
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return False
    return re.search(rf"\b{re.escape(symbol)}\b", text) is not None


def _frozen_contacts(files: list[str], symbols: list[str], root: Path, registry: list[dict]) -> list[dict]:
    contacts = []
    normed_files = {_norm(f) for f in files}
    for entry in registry:
        if entry["path"] in normed_files:
            contacts.append(
                {
                    "surface": entry["surface"],
                    "tier": "DIRECT",
                    "target": entry["path"],
                    "detail": f"target file is surface path {entry['path']}",
                }
            )
    for entry in registry:
        path = root / entry["path"]
        if not path.exists():
            continue
        for symbol in symbols:
            if _symbol_referenced(path, symbol):
                contacts.append(
                    {
                        "surface": entry["surface"],
                        "tier": "SYMBOL_INDIRECT",
                        "target": symbol,
                        "detail": f"'{symbol}' referenced in {entry['path']} (grep-based; not proof of semantic contact)",
                    }
                )
    return contacts


# ---------------------------------------------------------------------
# Computation 2: reachability
# ---------------------------------------------------------------------


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _index_source(
    relpath: str,
    source: str,
    name_index: dict[str, list[str]],
    edges: dict[str, set[str]],
    entry_roots: set[str],
    is_entry_file: bool,
) -> None:
    try:
        tree = ast.parse(source, filename=relpath)
    except SyntaxError:
        return

    stack: list[str] = []

    def handle_func(node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualname = f"{relpath}::{'.'.join(stack + [node.name])}"
        name_index.setdefault(node.name, []).append(qualname)
        calls: set[str] = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                name = _call_name(sub.func)
                if name:
                    calls.add(name)
        edges[qualname] = calls
        if is_entry_file:
            entry_roots.add(qualname)
        stack.append(node.name)
        walk(node)
        stack.pop()

    def walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                stack.append(child.name)
                walk(child)
                stack.pop()
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                handle_func(child)
            else:
                walk(child)

    walk(tree)


def _read_source_snapshot(root: Path, ref: str | None) -> dict[str, str]:
    """relative-path -> source text for every .py file under
    src/deepreason/. ref=None reads the working tree from disk
    (including uncommitted edits); a ref reads that commit via git."""
    if ref is None:
        base = root / "src" / "deepreason"
        if not base.exists():
            return {}
        snapshot = {}
        for path in sorted(base.rglob("*.py")):
            try:
                snapshot[_norm(str(path.relative_to(root)))] = path.read_text()
            except (OSError, UnicodeDecodeError):
                continue
        return snapshot
    listing = _run_git(["ls-tree", "-r", "--name-only", ref, "--", "src/deepreason"], cwd=root)
    files = sorted(line for line in listing.splitlines() if line.endswith(".py"))
    snapshot = {}
    for relpath in files:
        try:
            snapshot[relpath] = _run_git(["show", f"{ref}:{relpath}"], cwd=root)
        except EvidenceUnavailable:
            continue
    return snapshot


def _build_graph(snapshot: dict[str, str]) -> tuple[dict[str, list[str]], dict[str, set[str]], set[str]]:
    name_index: dict[str, list[str]] = {}
    edges: dict[str, set[str]] = {}
    entry_roots: set[str] = set()
    entry_files = set(ENTRY_POINT_FILES)
    for relpath, source in snapshot.items():
        _index_source(relpath, source, name_index, edges, entry_roots, relpath in entry_files)
    return name_index, edges, entry_roots


def _bfs_reachable(entry_roots: set[str], edges: dict[str, set[str]], name_index: dict[str, list[str]]) -> set[str]:
    reachable = set(entry_roots)
    queue = list(entry_roots)
    while queue:
        qualname = queue.pop()
        for called_name in edges.get(qualname, ()):
            for candidate in name_index.get(called_name, ()):
                if candidate not in reachable:
                    reachable.add(candidate)
                    queue.append(candidate)
    return reachable


def _status_for_symbol(symbol: str, name_index: dict[str, list[str]], reachable: set[str]) -> str:
    candidates = name_index.get(symbol)
    if not candidates:
        return "UNKNOWN"
    if any(candidate in reachable for candidate in candidates):
        return "REACHABLE"
    return "UNREACHABLE"


def _reachability(symbols: list[str], root: Path, against: str | None) -> list[dict]:
    if not symbols:
        return []
    current_snapshot = _read_source_snapshot(root, None)
    current_index, current_edges, current_roots = _build_graph(current_snapshot)
    current_reachable = _bfs_reachable(current_roots, current_edges, current_index)

    base_index: dict[str, list[str]] = {}
    base_reachable: set[str] = set()
    if against is not None:
        base_snapshot = _read_source_snapshot(root, against)
        base_index, base_edges, base_roots = _build_graph(base_snapshot)
        base_reachable = _bfs_reachable(base_roots, base_edges, base_index)

    results = []
    for symbol in symbols:
        status_current = _status_for_symbol(symbol, current_index, current_reachable)
        status_base = None
        direction = None
        if against is not None:
            status_base = _status_for_symbol(symbol, base_index, base_reachable)
            if status_base == "REACHABLE" and status_current == "UNREACHABLE":
                direction = "newly_dead"
            elif status_base == "UNREACHABLE" and status_current == "REACHABLE":
                direction = "newly_live"
            elif "UNKNOWN" not in (status_base, status_current):
                direction = "unchanged"
        results.append(
            {
                "symbol": symbol,
                "status_current": status_current,
                "status_base": status_base,
                "direction": direction,
            }
        )
    return results


# ---------------------------------------------------------------------
# Computation 3: consumers
# ---------------------------------------------------------------------


def _grep_dir(directory: Path, root: Path, target: str) -> list[str]:
    if not directory.exists():
        return []
    pattern = re.compile(rf"\b{re.escape(target)}\b")
    hits = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        try:
            lines = path.read_text().splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(lines, start=1):
            if pattern.search(line):
                hits.append(f"{path.relative_to(root)}:{lineno}")
    return hits


def _manifest_field_names(root: Path) -> set[str]:
    """AnnAssign target names inside class bodies in run_manifest.py --
    the fields qualification_subject_payload's manifest.model_dump()
    hashes whole (CENSUS.md/SPEC.md M2)."""
    path = root / "src" / "deepreason" / "run_manifest.py"
    if not path.exists():
        return set()
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return set()
    fields: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    fields.add(stmt.target.id)
    return fields


def _qualification_digest_consumers(files: list[str], symbols: list[str], root: Path) -> list[dict]:
    entries = []
    normed_files = {_norm(f) for f in files}
    for source_path in QUALIFICATION_SOURCE_FILES:
        if source_path in normed_files:
            entries.append(
                {
                    "target": source_path,
                    "tier": "CONFIRMED",
                    "detail": "target file is part of the manifest/qualification surface itself",
                }
            )
    manifest_fields = _manifest_field_names(root)
    for symbol in symbols:
        if symbol in manifest_fields:
            entries.append(
                {
                    "target": symbol,
                    "tier": "CONFIRMED",
                    "detail": "resolves to a RunManifest field; qualification_subject_payload hashes the whole manifest dump",
                }
            )
            continue
        for source_path in QUALIFICATION_SOURCE_FILES:
            path = root / source_path
            if path.exists() and _symbol_referenced(path, symbol):
                entries.append({"target": symbol, "tier": "PLAUSIBLE", "detail": f"referenced in {source_path}"})
                break
    return entries


def _console_script_funcnames(root: Path) -> set[str]:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return set()
    try:
        import tomllib

        data = tomllib.loads(pyproject.read_text())
    except (OSError, UnicodeDecodeError, ValueError):
        return set()
    scripts = data.get("project", {}).get("scripts", {})
    names = set()
    for target in scripts.values():
        if ":" in target:
            names.add(target.rsplit(":", 1)[1])
    return names


def _mcp_tool_names(root: Path) -> set[str]:
    path = root / "scripts" / "wheel_smoke.py"
    if not path.exists():
        return set()
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXPECTED_MCP_TOOLS" for target in node.targets
        ):
            names = set()
            for elt in getattr(node.value, "elts", []):
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    names.add(elt.value)
            return names
    return set()


def _wheel_smoke_consumers(symbols: list[str], root: Path) -> list[dict]:
    entries = []
    console_names = _console_script_funcnames(root)
    mcp_names = _mcp_tool_names(root)
    for symbol in symbols:
        if symbol in console_names:
            entries.append({"target": symbol, "tier": "CONFIRMED", "pin": "CONSOLE_ENTRY_POINT"})
            continue
        if symbol in mcp_names:
            entries.append({"target": symbol, "tier": "CONFIRMED", "pin": "MCP_TOOLS"})
            continue
        for source_path in WHEEL_SMOKE_SOURCE_FILES:
            path = root / source_path
            if path.exists() and _symbol_referenced(path, symbol):
                entries.append({"target": symbol, "tier": "PLAUSIBLE", "pin": source_path})
                break
    return entries


def _consumers(files: list[str], symbols: list[str], root: Path) -> dict:
    targets = list(dict.fromkeys(files + symbols))
    tests = []
    map_checks = []
    for target in targets:
        test_hits = _grep_dir(root / "tests", root, target)
        if test_hits:
            tests.append({"target": target, "hits": test_hits})
        map_hits = _grep_dir(root / "docs" / "map", root, target)
        if map_hits:
            map_checks.append({"target": target, "hits": map_hits})
    return {
        "tests": tests,
        "map_checks": map_checks,
        "qualification_digest": _qualification_digest_consumers(files, symbols, root),
        "wheel_smoke_pins": _wheel_smoke_consumers(symbols, root),
    }


# ---------------------------------------------------------------------
# Computation 4: disclosure summary
# ---------------------------------------------------------------------


def _disclosure_summary(
    frozen_surface_contacts: list[dict],
    frozen_adjacent_contacts: list[dict],
    reachability: list[dict],
    consumers: dict,
) -> str:
    surfaces_touched = sorted({c["surface"] for c in frozen_surface_contacts})
    adjacent_touched = sorted({c["surface"] for c in frozen_adjacent_contacts})
    newly_live = [r["symbol"] for r in reachability if r["direction"] == "newly_live"]
    newly_dead = [r["symbol"] for r in reachability if r["direction"] == "newly_dead"]
    unreachable_now = [r["symbol"] for r in reachability if r["status_current"] == "UNREACHABLE"]
    test_count = len(consumers["tests"])
    map_count = len(consumers["map_checks"])

    parts = []
    if surfaces_touched:
        parts.append(
            "This change touches "
            + str(len(surfaces_touched))
            + " of the five frozen surfaces (locked-down files that a change can silently "
            "corrupt old, already-recorded runs by touching): "
            + "; ".join(surfaces_touched)
            + "."
        )
    else:
        parts.append("This change touches none of the five frozen surfaces.")
    if adjacent_touched:
        parts.append("It also touches frozen-adjacent ground: " + "; ".join(adjacent_touched) + ".")
    if newly_live:
        parts.append(
            str(len(newly_live)) + " symbol(s) would become newly reachable: " + ", ".join(newly_live) + "."
        )
    if newly_dead:
        parts.append(
            str(len(newly_dead))
            + " symbol(s) would become newly dead (no longer reachable from any known entry point): "
            + ", ".join(newly_dead)
            + "."
        )
    if unreachable_now and not newly_dead:
        parts.append(
            str(len(unreachable_now))
            + " declared symbol(s) already have no live call path today, independent of this change: "
            + ", ".join(unreachable_now)
            + "."
        )
    parts.append(
        str(test_count) + " test file(s) and " + str(map_count) + " map document(s) assert on the touched targets today."
    )
    if reachability:
        parts.append(
            "Reachability here means a syntactic call path exists from a known entry point; it does "
            "not prove the path is ever actually exercised at runtime -- a symbol can be syntactically "
            "reachable and still never fire because of a runtime precondition this gate does not evaluate."
        )
    return " ".join(parts)


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------


def compute(files: list[str], symbols: list[str], against: str | None, root: Path) -> dict:
    for f in files:
        if not (root / f).exists():
            raise EvidenceUnavailable(f"declared file does not exist: {f}")
    if against is not None:
        _run_git(["rev-parse", "--verify", against], cwd=root)

    frozen_surface_contacts = _frozen_contacts(files, symbols, root, FROZEN_SURFACES)
    frozen_adjacent_contacts = _frozen_contacts(files, symbols, root, FROZEN_ADJACENT)
    reachability = _reachability(symbols, root, against)
    consumers = _consumers(files, symbols, root)
    disclosure_summary = _disclosure_summary(frozen_surface_contacts, frozen_adjacent_contacts, reachability, consumers)
    verdict = "CONTACT" if (frozen_surface_contacts or frozen_adjacent_contacts) else "CLEAR"

    return {
        "result_type": RESULT_TYPE,
        "targets": {"files": files, "symbols": symbols},
        "base": against,
        "frozen_surface_contacts": frozen_surface_contacts,
        "frozen_adjacent_contacts": frozen_adjacent_contacts,
        "reachability": reachability,
        "consumers": consumers,
        "disclosure_summary": disclosure_summary,
        "frozen_surface_verdict": verdict,
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="blast_radius.py",
        description="Blast-radius disclosure gate: frozen-surface contacts, reachability, consumers.",
    )
    parser.add_argument("--files", nargs="*", default=[], help="declared target file paths")
    parser.add_argument("--symbols", nargs="*", default=[], help="declared target symbol names")
    parser.add_argument("--against", default=None, help="ref to diff reachability against")
    parser.add_argument("--self-test", action="store_true", help="run the fixture self-test and exit")
    namespace = parser.parse_args(argv)
    if not namespace.self_test and not namespace.files and not namespace.symbols:
        raise InvalidInvocation("at least one of --files/--symbols is required")
    return namespace


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--self-test" in argv:
        return _self_test()
    try:
        namespace = _parse_args(argv)
    except InvalidInvocation as error:
        print(f"invalid invocation: {error}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return 2 if code != 0 else 0
    try:
        result = compute(namespace.files, namespace.symbols, namespace.against, Path.cwd())
    except EvidenceUnavailable as error:
        print(f"evidence unavailable: {error}", file=sys.stderr)
        return 3
    print(json.dumps(result))
    return 0


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)

        def git(*args: str) -> None:
            subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

        def run(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), *args],
                cwd=repo,
                capture_output=True,
                text=True,
            )

        git("init", "-q")
        git("config", "user.email", "test@example.com")
        git("config", "user.name", "Test")

        # Fixture layout: one frozen-surface stand-in, one entry-point
        # file, one module with a live and a dead function, one test
        # file referencing the live function.
        (repo / "src" / "deepreason" / "cli").mkdir(parents=True)
        (repo / "src" / "deepreason" / "rules").mkdir(parents=True)
        (repo / "tests").mkdir()
        (repo / "src" / "deepreason" / "harness.py").write_text("class Harness:\n    pass\n")
        (repo / "src" / "deepreason" / "unrelated.py").write_text("VALUE = 1\n")
        (repo / "src" / "deepreason" / "cli" / "main.py").write_text(
            "from deepreason.rules.experiment import live_func\n\n\ndef main():\n    live_func()\n"
        )
        (repo / "src" / "deepreason" / "rules" / "experiment.py").write_text(
            "def live_func():\n    return 1\n\n\ndef dead_func():\n    return 2\n"
        )
        (repo / "tests" / "test_experiment.py").write_text("from deepreason.rules.experiment import live_func\n")
        git("add", "-A")
        git("commit", "-q", "-m", "base")
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
        ).stdout.strip()

        # Proof 1: frozen-surface DIRECT tier flips on target file identity.
        result = run("--files", "src/deepreason/harness.py")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["frozen_surface_verdict"] == "CONTACT", data
        assert any(c["tier"] == "DIRECT" for c in data["frozen_surface_contacts"]), data

        result = run("--files", "src/deepreason/unrelated.py")
        data = json.loads(result.stdout)
        assert data["frozen_surface_verdict"] == "CLEAR", data
        assert data["frozen_surface_contacts"] == [], data

        # Proof 2: reachability flips UNREACHABLE -> REACHABLE when a
        # call site is added from a registered entry-point file.
        result = run("--symbols", "live_func", "dead_func")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        by_symbol = {r["symbol"]: r for r in data["reachability"]}
        assert by_symbol["live_func"]["status_current"] == "REACHABLE", data
        assert by_symbol["dead_func"]["status_current"] == "UNREACHABLE", data

        (repo / "src" / "deepreason" / "cli" / "main.py").write_text(
            "from deepreason.rules.experiment import live_func, dead_func\n\n\n"
            "def main():\n    live_func()\n    dead_func()\n"
        )
        result = run("--symbols", "dead_func", "--against", base)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        by_symbol = {r["symbol"]: r for r in data["reachability"]}
        assert by_symbol["dead_func"]["status_current"] == "REACHABLE", data
        assert by_symbol["dead_func"]["status_base"] == "UNREACHABLE", data
        assert by_symbol["dead_func"]["direction"] == "newly_live", data
        # restore
        (repo / "src" / "deepreason" / "cli" / "main.py").write_text(
            "from deepreason.rules.experiment import live_func\n\n\ndef main():\n    live_func()\n"
        )
        result = run("--symbols", "dead_func")
        data = json.loads(result.stdout)
        assert data["reachability"][0]["status_current"] == "UNREACHABLE", data

        # Proof 3: a consumer hit appears and disappears with the file.
        result = run("--symbols", "live_func")
        data = json.loads(result.stdout)
        assert any(t["target"] == "live_func" for t in data["consumers"]["tests"]), data

        (repo / "tests" / "test_experiment.py").unlink()
        result = run("--symbols", "live_func")
        data = json.loads(result.stdout)
        assert data["consumers"]["tests"] == [], data

        # Unresolvable symbol name -> UNKNOWN, never guessed.
        result = run("--symbols", "no_such_symbol_anywhere")
        data = json.loads(result.stdout)
        assert data["reachability"][0]["status_current"] == "UNKNOWN", data

        # Exit classes.
        result = run()
        assert result.returncode == 2, result.stderr

        result = run("--files", "src/deepreason/does_not_exist.py")
        assert result.returncode == 3, result.stderr

        result = run("--symbols", "live_func", "--against", "not-a-real-ref")
        assert result.returncode == 3, result.stderr

    print("SELF-TEST PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
