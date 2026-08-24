#!/usr/bin/env python3
"""Hardened battery digest tool (grammar: zoo/batteries/FORMAT.md).

Usage:   battery_digest.py FILE --write      # fill digests; FAILS if zero rows written
         battery_digest.py FILE --verify     # strict; FAILS on any deviation
Acceptance command for battery tasks:
         python3 scripts/battery_digest.py FILE --write && \\
         python3 scripts/battery_digest.py FILE --verify

Hardened against (field report defects 10-13): vacuous verify when the
registry heading/columns are absent or renamed; silently skipped rows with
the wrong column count; "OK" reports when nothing was written; and the
PENDING-DIGEST catch-22 (--write before --verify is the designed order).
"""
import hashlib
import re
import sys
from pathlib import Path

HEAD = re.compile(r"^### ([PNB][0-9]+) - .+$")
REG_HEAD = "## Registry"
COLS = ["id", "kind", "partner", "digest"]


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def parse(text):
    lines = text.split("\n")
    if REG_HEAD not in lines:
        fail(f"registry heading {REG_HEAD!r} not found (defect-10 guard)")
    reg_at = lines.index(REG_HEAD)
    blocks, cur = {}, None
    for i, ln in enumerate(lines[:reg_at]):
        m = HEAD.match(ln)
        if m:
            cur = m.group(1)
            if cur in blocks:
                fail(f"duplicate instance id {cur}")
            blocks[cur] = []
        elif ln.startswith("### "):
            fail(f"unparseable heading (line {i+1}): {ln!r} -- see FORMAT.md")
        elif cur:
            blocks[cur].append(ln)
    if not blocks:
        fail("no instance headings found")
    rows, header_seen = [], False
    for i, ln in enumerate(lines[reg_at + 1:], reg_at + 2):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set(c.strip("- ") for c in cells) == {""}:
            continue
        if not header_seen:
            if [c.lower() for c in cells] != COLS:
                fail(f"registry columns {cells} != {COLS} (defect-10 guard)")
            header_seen = True
            continue
        if len(cells) != len(COLS):
            fail(f"registry row line {i} has {len(cells)} columns, need {len(COLS)} (defect-11 guard)")
        rows.append((i - 1, dict(zip(COLS, cells))))
    if not header_seen:
        fail("registry table header row not found")
    return lines, blocks, rows


def block_digest(block_lines):
    body = "\n".join(l.rstrip() for l in block_lines).strip("\n") + "\n"
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ("--write", "--verify"):
        print(__doc__)
        sys.exit(2)
    path, mode = Path(sys.argv[1]), sys.argv[2]
    lines, blocks, rows = parse(path.read_text(encoding="utf-8"))
    row_ids = [r["id"] for _, r in rows]
    if sorted(row_ids) != sorted(blocks):
        fail(f"registry ids {sorted(row_ids)} != instance ids {sorted(blocks)}")
    if mode == "--write":
        wrote = 0
        for ln_idx, r in rows:
            d = block_digest(blocks[r["id"]])
            if r["digest"] != d:
                r["digest"] = d
                lines[ln_idx] = "| " + " | ".join(r[c] for c in COLS) + " |"
                wrote += 1
        if wrote == 0:
            fail("zero rows rewritten (defect-12 guard: nothing to write is a failure "
                 "when placeholders were expected; if digests are already current, verify instead)")
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"OK: wrote {wrote} digest(s)")
        return
    bad = [r["id"] for _, r in rows
           if r["digest"] == "PENDING-DIGEST" or r["digest"] != block_digest(blocks[r["id"]])]
    if bad:
        fail(f"digest mismatch or PENDING for {bad} -- run --write first (designed order)")
    print(f"OK: verified {len(rows)} row(s)")


if __name__ == "__main__":
    main()
