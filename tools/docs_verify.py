#!/usr/bin/env python3
"""Re-run every checkable claim in `docs/map/` and report the ones that rot.

A map document is authenticated by RE-DERIVATION, not by a signature: each
load-bearing claim carries a shell command that must still exit 0.  A signature
would prove who wrote a sentence; this proves the sentence is still true, which
is the property that actually decays.

Usage:
    python tools/docs_verify.py             # authoritative: every check, no cache
    python tools/docs_verify.py --fast      # iteration: skip checks whose files are unchanged
    python tools/docs_verify.py --failed    # re-run only what was not green last time
    python tools/docs_verify.py --stale     # list docs whose Owns: files moved
    python tools/docs_verify.py --audit     # flag checks that cannot fail
    python tools/docs_verify.py --links     # every DR- reference resolves
    python tools/docs_verify.py --coverage  # enforcement sites a seam omits
    python tools/docs_verify.py --ring      # list each document's test ring
    python tools/docs_verify.py --ring scratch   # run the scratch subsystem ring
    python tools/docs_verify.py --self-test # verify this tool's own parsing
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

MAP_DIR = Path(__file__).resolve().parents[1] / "docs" / "map"
REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / ".docs_verify_cache.json"

# Paths a check names. Checks are greps and pytest invocations over explicit
# paths, so the files a command reads are almost always spelled in it.
_PATHISH = re.compile(r"(?:src|tests|tools|docs)/[\w./-]+")

# A check rides its own line as an inline-code span, at COLUMN 0. The column
# rule is what lets SCHEMA.md show worked examples inside indented code blocks
# without the verifier trying to run them.
_CHECK = re.compile(r"^`check:\s*(?P<cmd>.+?)`\s*$")
# Every column-0 opener, parseable or not. The two patterns are deliberately
# split: _CHECK decides what RUNS, _CHECK_OPEN decides what must be ACCOUNTED
# FOR. An opener that matches only the second is a defect in the document, and
# reporting it is the whole point - a check the instrument cannot read used to
# fall through the parse loop with no branch to catch it, so a claim could
# carry a check that had never once been executed and read, in the document,
# exactly like a claim that had.
_CHECK_OPEN = re.compile(r"^`check:")
_HEADER = re.compile(r"^(?P<key>Verified-at|Verify|Owns|Seams|Seams-undocumented|Sides|Sweep|Depends-on):\s*(?P<val>.*)$")
_ID = re.compile(r"^<!--\s*(?P<id>DR-[A-Z]+-[a-z0-9\-]+|DR-[A-Z]+)\s*-->\s*$")

# Commands that pass no matter what the tree looks like. A check built only from
# these is worse than absent: it lends a claim credibility it has not earned.
_VACUOUS = re.compile(
    r"^\s*(true|:|echo\b|test\s+-[efd]\s+\S+\s*$|ls\s+\S+\s*$)", re.IGNORECASE
)


@dataclass
class Doc:
    path: Path
    doc_id: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    checks: list[tuple[int, str]] = field(default_factory=list)
    errors: list[tuple[int, str]] = field(default_factory=list)


def parse_text(text: str, path: Path | None = None) -> Doc:
    doc = Doc(path=path or Path("<memory>"))
    for number, line in enumerate(text.splitlines(), 1):
        if doc.doc_id is None and (m := _ID.match(line)):
            doc.doc_id = m.group("id")
            continue
        if m := _HEADER.match(line):
            doc.headers.setdefault(m.group("key"), m.group("val").strip())
            continue
        if m := _CHECK.match(line):
            doc.checks.append((number, m.group("cmd").strip()))
            continue
        if _CHECK_OPEN.match(line):
            doc.errors.append((
                number,
                "unparseable check: a column-0 `check: opener must close with "
                "a backtick at the end of the same line. "
                f"Opener reads: {line[:100]!r}",
            ))
    return doc


def parse(path: Path) -> Doc:
    return parse_text(path.read_text(encoding="utf-8"), path)


def documents() -> list[Doc]:
    return [parse(p) for p in sorted(MAP_DIR.glob("*.md"))]


def _fingerprint(cmd: str) -> str:
    """Identity of a check: its text, plus the content of every path it names.

    HEURISTIC, and its limit is the reason the cache is opt-in: a command that
    reads a file it does not name will be reused when it should have re-run.
    Every authoritative run - the gate, validation, delivery - uses the default
    full mode, which never reads the cache. --fast is for iteration only, where
    being wrong costs a re-run rather than a false green.
    """
    h = hashlib.sha256(cmd.encode())
    for token in sorted(set(_PATHISH.findall(cmd))):
        path = REPO / token.split("::")[0]
        if path.is_file():
            h.update(path.read_bytes())
        elif path.is_dir():
            for child in sorted(path.rglob("*.py")):
                h.update(child.read_bytes())
        else:
            h.update(b"<absent>")
    return h.hexdigest()


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True))
    except OSError:
        pass


# A check is meant to be cheap enough to run often. 300s is generous for the
# heaviest legitimate one (a focused pytest file) and short enough that a check
# which accidentally invokes the whole suite is reported as a defect in the
# check rather than silently costing fifteen minutes on every run.
CHECK_TIMEOUT_S = 300


def run(cmd: str) -> tuple[bool, str, float]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=REPO, capture_output=True, text=True,
            timeout=CHECK_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {CHECK_TIMEOUT_S}s - this check is too "\
                      "expensive; narrow it to the claim it actually tests", \
               time.monotonic() - started
    elapsed = time.monotonic() - started
    if proc.returncode == 0:
        return True, "", elapsed
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return False, " | ".join(tail[-3:])[:400], elapsed


def cmd_run(fast: bool = False, only_failed: bool = False, jobs: int = 0,
            slow: float = 0.0) -> int:
    docs = documents()
    if not docs:
        print("no documents in docs/map/", file=sys.stderr)
        return 1
    cache = _load_cache() if (fast or only_failed) else {}
    fresh = dict(cache)
    failures: list[str] = []
    reused = skipped = 0
    pending: list[tuple[str, int, str, str]] = []  # doc, line, cmd, key
    for doc in docs:
        if doc.doc_id is None:
            failures.append(f"{doc.path.name}: no `<!-- DR-... -->` id on the first line")
        for number, problem in doc.errors:
            failures.append(f"{doc.path.name}:{number}: {problem}")
        for number, cmd in doc.checks:
            key = _fingerprint(cmd)
            prior = cache.get(key)
            if only_failed and prior is not None and prior.get("ok"):
                skipped += 1
                continue
            if fast and prior is not None:
                reused += 1
                if not prior["ok"]:
                    failures.append(
                        f"{doc.path.name}:{number}: {cmd}\n      -> "
                        f"{prior.get('detail', '')} (cached)")
                continue
            pending.append((doc.path.name, number, cmd, key))

    total = len(pending) + reused
    # Checks are independent subprocesses, so they parallelise cleanly. Serially,
    # the 180-odd pytest checks in this map take over an hour and get killed;
    # that made the authoritative run - the only one a gate may trust - the one
    # nobody could complete.
    workers = jobs or min(16, (os.cpu_count() or 4))
    timings: list[tuple[float, str, int]] = []
    if pending:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run, item[2]): item for item in pending}
            for future in concurrent.futures.as_completed(futures):
                name, number, cmd, key = futures[future]
                ok, detail, elapsed = future.result()
                fresh[key] = {"ok": ok, "detail": detail, "cmd": cmd}
                timings.append((elapsed, name, number))
                if not ok:
                    failures.append(f"{name}:{number}: {cmd}\n      -> {detail}")
    _save_cache(fresh)
    if slow:
        for elapsed, name, number in sorted(timings, reverse=True):
            if elapsed >= slow:
                print(f"  SLOW {elapsed:6.1f}s  {name}:{number}")
    mode = "fast" if fast else ("failed-only" if only_failed else "full")
    note = f", {reused} reused" if reused else ""
    note += f", {skipped} skipped (green last run)" if skipped else ""
    note += f", {workers} workers" if pending else ""
    print(f"docs_verify [{mode}]: {len(docs)} documents, {total} checks{note}")
    for failure in failures:
        print(f"  FAIL {failure}")
    print(f"docs_verify: {len(failures)} failed")
    return 1 if failures else 0


def cmd_stale() -> int:
    """Report documents whose owned files changed after their Verified-at stamp.

    Advisory by design. Most source edits do not invalidate a description, so
    this ranks documents for a human re-read rather than failing a gate.
    """
    stale = 0
    for doc in documents():
        stamp = doc.headers.get("Verified-at", "").strip()
        owns = [o.strip() for o in doc.headers.get("Owns", "").split(",") if o.strip()]
        if not stamp or not owns:
            continue
        proc = subprocess.run(
            ["git", "log", "--oneline", f"{stamp}..HEAD", "--", *owns],
            cwd=REPO, capture_output=True, text=True,
        )
        moved = [line for line in proc.stdout.splitlines() if line.strip()]
        if moved:
            stale += 1
            print(f"{doc.path.name}: {len(moved)} commit(s) to owned files since {stamp}")
            for line in moved[:3]:
                print(f"    {line}")
    print(f"docs_verify --stale: {stale} document(s) worth re-reading")
    return 0


def cmd_ring(targets: list[str]) -> int:
    """Run the test ring a document declares, for iterating on that subsystem.

    This is what `Verify:` is FOR. A subsystem document already knows which
    test files guard its code; without this the reader either re-derives that
    list or reaches for the whole suite, which is how a fourteen-minute gate
    becomes a feedback loop.

    Naming no target lists every ring, so "what do I run for scratch?" is one
    command rather than a search.
    """
    docs = documents()
    if not targets:
        for doc in docs:
            ring = doc.headers.get("Verify", "").strip()
            if ring and "docs_verify" not in ring:
                print(f"{doc.path.stem}\n    {ring}")
        return 0
    status = 0
    for target in targets:
        match = [d for d in docs if target.lower() in d.path.stem.lower()]
        if not match:
            print(f"no map document matches {target!r}", file=sys.stderr)
            status = 1
            continue
        for doc in match:
            ring = doc.headers.get("Verify", "").strip()
            if not ring or "docs_verify" in ring:
                print(f"{doc.path.stem}: no test ring declared "
                      f"(its Verify: is the map checker, not a ring)")
                continue
            print(f"== {doc.path.stem} ==\n{ring}")
            proc = subprocess.run(ring, shell=True, cwd=REPO)
            status = status or proc.returncode
    return status


def cmd_coverage() -> int:
    """Completeness sweep: find enforcement sites a seam document omits.

    A check proves a listed site is real; nothing proves the list is whole —
    that is the one failure mode per-claim checks cannot catch, and it has
    already produced a real omission (a sixth school_id guard in harness.py,
    a frozen surface, while every check in the seam document passed).

    So the sweep that found it runs mechanically. A document declares, in one
    header line, the terms that identify its agreement:

        Sweep: school_id && conjecture_context|PlannedConjectureContext|scratch

    Left of `&&`: the FIELD the agreement moves (a regex). Right: the other
    side's symbols (a regex). A source file matching both is a candidate; a
    candidate that COMPARES or RAISES on the field is an enforcement site; an
    enforcement site not NAMED anywhere in the document is a finding.

    Naming is the dismissal mechanism, deliberately: a flagged file that
    belongs to a different seam is resolved by one sentence saying so. The
    rule is not "every site gets a table row"; it is "no enforcing site may
    be invisible to the reader".

    Documents without a Sweep: header are reported once and skipped — the
    header arrives when the document is next touched, per SCHEMA.md.
    """
    findings = missing = swept = 0
    src = REPO / "src" / "deepreason"
    sources = [
        (f, f.read_text(encoding="utf-8", errors="ignore"))
        for f in sorted(src.rglob("*.py"))
        if "__pycache__" not in str(f)
    ]
    for doc in documents():
        if not (doc.doc_id or "").startswith("DR-SEAM-"):
            continue
        spec = doc.headers.get("Sweep", "").strip()
        if not spec:
            missing += 1
            print(f"{doc.path.name}: no Sweep: header (add when next touched)")
            continue
        if "&&" not in spec:
            findings += 1
            print(f"{doc.path.name}: malformed Sweep: (need FIELD && OTHER_SIDE)")
            continue
        swept += 1
        field, other = (part.strip() for part in spec.split("&&", 1))
        try:
            field_re = re.compile(field)
            other_re = re.compile(other)
            enforce_re = re.compile(
                rf"(?:{field})\s*(?:!=|==)|(?:!=|==)\s*[\w.]*(?:{field})"
                rf"|raise[^\n]*(?:{field})"
            )
        except re.error as error:
            findings += 1
            print(f"{doc.path.name}: Sweep: regex error: {error}")
            continue
        body = doc.path.read_text(encoding="utf-8")
        for f, text in sources:
            if not (field_re.search(text) and other_re.search(text)):
                continue
            if not enforce_re.search(text):
                continue
            if f.name in body or str(f.relative_to(REPO)) in body:
                continue
            findings += 1
            print(f"{doc.path.name}: enforcement site not named: "
                  f"{f.relative_to(REPO)}")
    print(f"docs_verify --coverage: {swept} seam(s) swept, {missing} without a "
          f"Sweep: header, {findings} finding(s)")
    return 1 if findings else 0


def cmd_links() -> int:
    """Every DR- reference must resolve to a document that exists.

    A dangling reference is not a harmless TODO: SCHEMA.md tells the reader that
    an absent seam means the two sides do not interact. A reference to a
    document nobody wrote makes the map assert an interaction it cannot
    describe, which is worse than silence. Candidate-but-undocumented seams
    belong in INDEX.md's matrix, where they are labelled as such.
    """
    known = {parse(p).doc_id for p in MAP_DIR.glob("*.md")} - {None}
    ref = re.compile(r"DR-(?:SUB|CON|SEAM|INV|REC)-[a-z0-9][a-z0-9\-]*")
    dangling: dict[str, set[str]] = {}
    for path in sorted(MAP_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in ref.findall(text):
            if match not in known:
                dangling.setdefault(match, set()).add(path.name)
    for target in sorted(dangling):
        where = ", ".join(sorted(dangling[target]))
        print(f"dangling {target}  <- {where}")
    print(f"docs_verify --links: {len(dangling)} dangling reference(s), "
          f"{len(known)} document(s)")
    return 1 if dangling else 0


def cmd_audit() -> int:
    """Flag checks that cannot fail, and documents with no checks at all."""
    flagged = 0
    for doc in documents():
        if not doc.checks and doc.doc_id not in {"DR-SCHEMA", "DR-INDEX"}:
            print(f"{doc.path.name}: no checks — every claim in it is unverifiable")
            flagged += 1
        for number, problem in doc.errors:
            print(f"{doc.path.name}:{number}: {problem}")
            flagged += 1
        for number, cmd in doc.checks:
            if _VACUOUS.match(cmd):
                print(f"{doc.path.name}:{number}: vacuous check `{cmd}`")
                flagged += 1
    print(f"docs_verify --audit: {flagged} finding(s)")
    return 1 if flagged else 0


def cmd_self_test() -> int:
    """Prove the parser reads what the schema says it reads."""
    sample = """<!-- DR-SUB-example -->
Verified-at: deadbee
Verify: true
Owns: src/deepreason/example.py

A claim.
`check: test 1 -eq 1`
Prose mentioning `check: not-a-check` inline should not parse.
"""
    tmp = MAP_DIR / "_selftest.md"
    try:
        tmp.write_text(sample, encoding="utf-8")
        doc = parse(tmp)
        assert doc.doc_id == "DR-SUB-example", doc.doc_id
        assert doc.headers["Verified-at"] == "deadbee", doc.headers
        assert doc.headers["Owns"] == "src/deepreason/example.py", doc.headers
        assert len(doc.checks) == 1, doc.checks
        assert doc.checks[0][1] == "test 1 -eq 1", doc.checks
        assert doc.errors == [], doc.errors
        # An indented check is an EXAMPLE, not a claim, and must not parse.
        assert parse_text("    `check: false`").checks == []
        assert parse_text("    `check: false`").errors == []
        # A column-0 opener that does not close is an ERROR, never a skip.
        unclosed = parse_text("`check: python -c \"\nassert False\n\"`")
        assert unclosed.checks == [], unclosed.checks
        assert len(unclosed.errors) == 1, unclosed.errors
        assert "unparseable check" in unclosed.errors[0][1], unclosed.errors
        assert _VACUOUS.match("true") and not _VACUOUS.match("grep -q x y")
    finally:
        tmp.unlink(missing_ok=True)
    print("docs_verify --self-test: ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stale", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--links", action="store_true")
    parser.add_argument("--coverage", action="store_true",
                        help="flag enforcement sites a seam document omits")
    parser.add_argument("--fast", action="store_true",
                        help="reuse cached results whose named files are unchanged")
    parser.add_argument("--failed", action="store_true",
                        help="re-run only checks that were not green last run")
    parser.add_argument("--jobs", type=int, default=0,
                        help="parallel checks (default: min(16, cpus))")
    parser.add_argument("--slow", type=float, default=0.0, metavar="SECONDS",
                        help="report checks slower than SECONDS")
    parser.add_argument("--ring", nargs="*", metavar="DOC",
                        help="run the test ring a document declares; no arg lists all")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return cmd_self_test()
    if args.stale:
        return cmd_stale()
    if args.ring is not None:
        return cmd_ring(args.ring)
    if args.coverage:
        return cmd_coverage()
    if args.links:
        return cmd_links()
    if args.audit:
        return cmd_audit()
    return cmd_run(fast=args.fast, only_failed=args.failed, jobs=args.jobs,
                   slow=args.slow)


if __name__ == "__main__":
    raise SystemExit(main())
