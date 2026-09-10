"""Census over every committed run manifest: which door compiled which geometry.

Read-only. Run from the repo root:  python -u <this file>
"""
from __future__ import annotations

import collections
import json
import pathlib

managed: collections.Counter = collections.Counter()
other: collections.Counter = collections.Counter()

for path in sorted(pathlib.Path("experiments").rglob("run-manifest.json")):
    root = path.parent
    # A managed root is one `preparation` wrote: it carries the preparation
    # record. A compiled `--run-manifest` root does not.
    is_managed = (root / "run-preparation.json").exists()
    try:
        manifest = json.loads(path.read_text())
    except Exception:
        continue
    policy = manifest.get("scratch_policy") or {}
    key = (policy.get("embedder_backend"), len(manifest.get("compile_notices") or []))
    (managed if is_managed else other)[key] += 1

print("MANAGED roots (run-preparation.json present):", sum(managed.values()))
for key, count in sorted(managed.items(), key=lambda kv: str(kv[0])):
    print(f"  embedder_backend={key[0]!r} compile_notices={key[1]} -> {count}")
print("OTHER roots (compiled --run-manifest, fixtures, soaks):", sum(other.values()))
for key, count in sorted(other.items(), key=lambda kv: str(kv[0])):
    print(f"  embedder_backend={key[0]!r} compile_notices={key[1]} -> {count}")
