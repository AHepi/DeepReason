#!/usr/bin/env python3
"""Cross-document claim agreement (field report FR-14).

Usage:   consistency_packet.py [CLAIMS.json] --write    # rebuild the packet
         consistency_packet.py [CLAIMS.json] --verify   # FAIL if stale
Acceptance command:
         python3 consistency_packet.py --write && \
         python3 consistency_packet.py --verify

WHY. Reviews read one document at a time; none can see whether documents
AGREE with each other, and corrections propagate across them by hand. A
missed propagation is the likeliest defect and the one nothing watches. The
packet extracts the claims that should agree into one small file; --verify
fails when a source document changes a quoted claim, which is the signal to
re-run whatever cross-reads the packet (a reviewer, or you) and check the
documents still agree.

WHY AN EXTRACT (FR-15). Whole documents overran a reviewer's budget and
returned nothing. The packet must stay inside what a reader can finish, so a
size ceiling is enforced, matches are context-windowed, and overlapping
matches are merged so one paragraph is never sent twice.

CLAIMS SCHEMA (JSON, default ./claims.json, else argv[1]):
{
  "packet": "path/to/CONSISTENCY_PACKET.md",
  "window": 220,                # context chars each side of a match
  "max_chars": 24000,           # hard ceiling on the built packet
  "claims": [
    {"label": "DOC-A", "path": "docs/a.md", "patterns": ["case 12", "regex too"]}
  ]
}

REFUSALS ARE THE POINT: a pattern matching nothing FAILS (a renamed claim
must not silently stop being checked); a missing document FAILS; a packet
over the ceiling FAILS with the remedy named (split claims, do not raise the
ceiling first).
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HEADER = """# Extracted claims, for cross-document consistency audit

Built by consistency_packet.py from the claims file beside it. Each excerpt
is a claim that appears in more than one document, or that a correction has
touched. The audit question is not whether each claim is right, but whether
they AGREE WITH EACH OTHER. Ellipses mark cuts.
"""


def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)


def load_config(root, path):
    config_path = root / path
    if not config_path.exists():
        fail(f"claims file {path} not found (schema in this file's docstring)")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"claims file is not valid JSON: {exc}")
    for key in ("packet", "claims"):
        if key not in config:
            fail(f"claims file missing required key {key!r}")
    if not config["claims"]:
        fail("claims list is empty; a vacuous packet checks nothing")
    return config


def build(root, config):
    window = int(config.get("window", 220))
    parts = [HEADER]
    for claim in config["claims"]:
        label, rel = claim["label"], claim["path"]
        path = root / rel
        if not path.exists():
            fail(f"{rel} is missing; a claims row names a document that is gone")
        text = path.read_text(encoding="utf-8")
        spans = []
        for pattern in claim["patterns"]:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                spans.append((max(0, match.start() - window),
                              min(len(text), match.end() + window)))
        if not spans:
            fail(f"no pattern matched in {rel}; a claim was renamed or removed "
                 "and this packet would silently stop checking it")
        merged = []
        for start, end in sorted(spans):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        for start, end in merged:
            excerpt = " ".join(text[start:end].split())
            parts.append(f"**[{label}]** …{excerpt}…\n")
    built = "\n".join(parts)
    ceiling = int(config.get("max_chars", 24000))
    if len(built) > ceiling:
        fail(f"packet is {len(built)} chars against a {ceiling} ceiling. "
             "Shrink the claims (tighter patterns, smaller window, split into "
             "two packets); do not raise the ceiling first (FR-15)")
    return built


def main():
    args = [a for a in sys.argv[1:]]
    mode = None
    claims_path = "claims.json"
    for a in args:
        if a in ("--write", "--verify"):
            mode = a
        else:
            claims_path = a
    if mode is None:
        fail("usage: consistency_packet.py [CLAIMS.json] --write | --verify")
    root = Path.cwd()
    config = load_config(root, claims_path)
    packet = root / config["packet"]
    built = build(root, config)
    if mode == "--write":
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(built, encoding="utf-8")
        digest = hashlib.sha256(built.encode()).hexdigest()[:16]
        print(f"OK: wrote {config['packet']} ({len(built)} chars, {digest})")
        return
    if not packet.exists():
        fail(f"{config['packet']} does not exist; run --write")
    if packet.read_text(encoding="utf-8") != built:
        fail(f"{config['packet']} is stale: a source document changed a quoted "
             "claim. Run --write, then re-check that the documents still agree "
             "-- the staleness is the signal, not the problem")
    print(f"OK: packet current ({len(built)} chars)")


if __name__ == "__main__":
    main()
