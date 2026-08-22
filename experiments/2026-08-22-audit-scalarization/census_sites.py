#!/usr/bin/env python3
"""Enumerate every candidate consumption site of adjudication output in src/.

Closure instrument for the scalarization census
(experiments/2026-08-22-audit-scalarization/CENSUS.md).

The producer surface is fixed by re-derivation, not by judgement: exactly
two modules in src/ import `deepreason.adjudication`
(`harness.py`, `invariants.py`), and `Harness._adjudicate` is the sole
writer of `state.status`. So everything downstream reads adjudication
output through one of the four durable state fields it writes
(`att`, `dep`, `status`, `conn`), through the `Status` enum, through a
direct call to an adjudication entry point, or through the record wire
aliases those fields are serialized under.

Emitting the candidate set mechanically — one regex family per producer
channel, no sampling and no cap — is what lets CENSUS.md claim closure:
every line this prints is either a row in the census table or is listed
in CENSUS.md's excluded-with-reason ledger, and nothing else.

Usage:
    python experiments/2026-08-22-audit-scalarization/census_sites.py
    python experiments/2026-08-22-audit-scalarization/census_sites.py --counts
    python experiments/2026-08-22-audit-scalarization/census_sites.py --check
"""

from __future__ import annotations

import pathlib
import re
import sys

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "deepreason"

# One entry per producer channel. The key is the channel name recorded in
# CENSUS.md's "Producer channel" column.
CHANNELS: dict[str, re.Pattern[str]] = {
    # The partition itself, read off the materialized state.
    "status-field": re.compile(r"(?<![A-Za-z_])state\.status\b|\bstatus\s*=\s*[a-z_]*\.state\.status\b"),
    # The four labels, wherever a comparison or construction names one.
    "Status-enum": re.compile(r"(?<![A-Za-z_])Status\.[A-Z_]+"),
    # Attack / support graphs.
    "att-field": re.compile(r"(?<![A-Za-z_])state\.att\b"),
    "dep-field": re.compile(r"(?<![A-Za-z_])state\.dep\b"),
    # The one scalar the harness itself derives from the partition.
    "conn-field": re.compile(r"(?<![A-Za-z_])state\.conn\b"),
    # Direct calls to adjudication entry points and to the conn/iso helpers
    # that stand immediately downstream of them.
    "entry-point": re.compile(
        r"(?<![A-Za-z_])(build_att|build_dep|toposort|grounded_extension"
        r"|label0|compute_label0|final_labels|conn_map|iso)\s*\("
    ),
    # The record wire aliases the harness stamps on every log line, and the
    # JSON keys a reader picks the partition back up from.
    "wire-alias": re.compile(r"""["'](att\+|dep\+|status_changed|status_counts)["']"""),
}

# Producer-side files: they CREATE the output rather than consume it. Kept
# out of the consumption census but listed here so the exclusion is explicit
# and re-derivable rather than a silent filter.
PRODUCER_FILES = {
    "adjudication/edges.py",
    "adjudication/grounded.py",
    "adjudication/support.py",
    "adjudication/__init__.py",
}


def rel(path: pathlib.Path) -> str:
    return str(path.relative_to(SRC))


def sites() -> list[tuple[str, str, int, str]]:
    """(channel, relpath, lineno, source line) for every candidate site."""
    out: list[tuple[str, str, int, str]] = []
    for path in sorted(SRC.rglob("*.py")):
        relpath = rel(path)
        try:
            lines = path.read_text().splitlines()
        except UnicodeDecodeError:  # pragma: no cover - no such file today
            continue
        for lineno, line in enumerate(lines, start=1):
            for channel, pattern in CHANNELS.items():
                if pattern.search(line):
                    out.append((channel, relpath, lineno, line.strip()))
    return out


def check() -> int:
    """Reconcile the enumerator against CENSUS.md, line by line.

    This is what lets CENSUS.md claim "no sampling, no silent cap". A census
    that merely asserts completeness is an assurance; one that re-derives its
    own coverage is a checked statement, and the difference is the whole point
    of the exercise. Exit 0 means every distinct (file, line) the producer
    channels reach is cited by exactly one census row.
    """
    census = pathlib.Path(__file__).with_name("CENSUS.md")
    if not census.exists():
        print("CENSUS.md is missing beside this script")
        return 1
    cited: dict[tuple[str, int], int] = {}
    for line in census.read_text().splitlines():
        if not line.startswith("| ") or line.count("|") < 7:
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells[0] is the empty lead; the row shape is
        # | # | `path` | lines | consumed | becomes | class | note |
        path_cell, spec = cells[2], cells[3]
        if not (path_cell.startswith("`") and path_cell.endswith("`")):
            continue
        relpath = path_cell.strip("`")
        # Numbers after an opening parenthesis are prose pointers, not claims
        # of coverage (e.g. a line the enumerator does not flag).
        for token in re.findall(r"\d+", spec.split("(")[0]):
            key = (relpath, int(token))
            cited[key] = cited.get(key, 0) + 1

    enumerated = {(relpath, lineno) for _c, relpath, lineno, _l in sites()}
    missing = sorted(enumerated - set(cited))
    duplicated = sorted(key for key, n in cited.items() if n > 1)
    # A row may point at a line the enumerator does not flag (the sort/truncate
    # pair in the SELECTION finding, the two rank-key readers in the scheduler).
    # Those are prose pointers, reported but not failures.
    extra = sorted(key for key in cited if key not in enumerated)

    print(f"enumerated distinct (file, line): {len(enumerated)}")
    print(f"cited by CENSUS.md rows:          {len(cited)}")
    if extra:
        print(f"rows citing an unflagged line ({len(extra)}, informational):")
        for relpath, lineno in extra:
            print(f"  {relpath}:{lineno}")
    if missing:
        print(f"UNCOVERED ({len(missing)}) — the census is not closed:")
        for relpath, lineno in missing:
            print(f"  {relpath}:{lineno}")
    if duplicated:
        print(f"CITED TWICE ({len(duplicated)}) — a line has two classifications:")
        for relpath, lineno in duplicated:
            print(f"  {relpath}:{lineno}")
    if missing or duplicated:
        return 1
    print("CLOSED: every enumerated site is classified exactly once.")
    return 0


def main() -> int:
    if "--check" in sys.argv:
        return check()
    rows = sites()
    if "--counts" in sys.argv:
        by_file: dict[str, int] = {}
        by_channel: dict[str, int] = {}
        for channel, relpath, _lineno, _line in rows:
            producer = relpath in PRODUCER_FILES
            key = relpath + ("  [PRODUCER]" if producer else "")
            by_file[key] = by_file.get(key, 0) + 1
            by_channel[channel] = by_channel.get(channel, 0) + 1
        print(f"total candidate sites: {len(rows)}")
        print(f"distinct files: {len(by_file)}")
        print("\n-- by channel --")
        for channel in CHANNELS:
            print(f"{by_channel.get(channel, 0):5d}  {channel}")
        print("\n-- by file --")
        for key in sorted(by_file, key=lambda k: (-by_file[k], k)):
            print(f"{by_file[key]:5d}  {key}")
        return 0
    for channel, relpath, lineno, line in rows:
        tag = " [PRODUCER]" if relpath in PRODUCER_FILES else ""
        print(f"{relpath}:{lineno}\t{channel}{tag}\t{line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
