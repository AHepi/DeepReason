#!/usr/bin/env python3
"""Census: map `check:` lines docs_verify's parser silently drops.

tools/docs_verify.py:47 is `^`check:\\s*(?P<cmd>.+?)`\\s*$`, applied per LINE
(:75, `_CHECK.match(line)`). A check whose command does not close its
backtick on the same line therefore matches nothing, and is dropped with no
warning, no count, and no --audit complaint -- --audit can only refuse checks
it PARSED.

Read-only. Prints every column-0 `check: line the parser will not run.
"""
import pathlib, re

_CHECK = re.compile(r"^`check:\s*(?P<cmd>.+?)`\s*$")

opened = dropped = 0
docs = set()
print(f"{'doc':38} {'line':>5}  first 90 chars")
for p in sorted(pathlib.Path("docs/map").glob("*.md")):
    for n, line in enumerate(p.read_text().splitlines(), 1):
        if not line.startswith("`check:"):
            continue
        opened += 1
        if _CHECK.match(line):
            continue
        dropped += 1
        docs.add(p.name)
        print(f"{p.name:38} {n:>5}  {line[:90]}")
print()
print(f"column-0 `check: lines           : {opened}")
print(f"SILENTLY DROPPED by the parser   : {dropped}  across {len(docs)} documents")
print(f"actually run                     : {opened - dropped}")
