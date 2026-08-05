"""Reproduction for the section-blind entry-point reader (GOAL.md, DIAGNOSIS.md).

Parses the SAME entry_points.txt bytes two ways -- the way
scripts/wheel_smoke.py does today (no section state) and the way it must
(sections honoured) -- and shows the first yields four entries where two are
required. Reads a built wheel if one is given, else the committed pyproject's
declared groups rendered in entry_points.txt form.

Run:  python experiments/2026-08-05-fix-smoke-entry-point-reader/repro.py [wheel]
"""

import sys
import zipfile

REQUIRED_CONSOLE = {
    "deepreason = deepreason.cli.main:main",
    "deepreason-mcp = deepreason.mcp_server:main",
}

SAMPLE = """[console_scripts]
deepreason = deepreason.cli.main:main
deepreason-mcp = deepreason.mcp_server:main

[deepreason.admission.adapters]
epub = deepreason.admission.adapters_epub:MANIFEST
pdf = deepreason.admission.adapters_pdf:MANIFEST
"""


def flat_parse(text):
    """What scripts/wheel_smoke.py does today: headers skipped, not honoured."""
    return {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.startswith("[")
    }


def sectioned_parse(text):
    """What it must do: attribute every entry to the group it was declared in."""
    groups, current = {}, None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1]
            groups.setdefault(current, set())
            continue
        if current is not None:
            groups[current].add(stripped)
    return groups


if len(sys.argv) > 1:
    archive = zipfile.ZipFile(sys.argv[1])
    name = [n for n in archive.namelist() if n.endswith(".dist-info/entry_points.txt")][0]
    text = archive.read(name).decode("utf-8")
    print("source: %s" % sys.argv[1])
else:
    text = SAMPLE
    print("source: the committed pyproject's declared groups")

flat = flat_parse(text)
groups = sectioned_parse(text)

print()
print("FLAT parse (today's reader):")
print("  entries: %d" % len(flat))
print("  equals the 2 required console scripts? %s" % (flat == REQUIRED_CONSOLE))
print("  -> this is the AssertionError the smoke raises")
print()
print("SECTIONED parse:")
for group in sorted(groups):
    print("  [%s] -> %d entry/entries" % (group, len(groups[group])))
print("  console_scripts equals the 2 required? %s"
      % (groups.get("console_scripts") == REQUIRED_CONSOLE))
print()
print("adapters group present and non-empty? %s"
      % bool(groups.get("deepreason.admission.adapters")))
print("  (today's reader asserts NOTHING about this group, so it would go")
print("   green if 4940b5f7's adapters silently vanished -- DIAGNOSIS.md's")
print("   second finding)")
