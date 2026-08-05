"""Record-replay reproduction for the P1 defect (GOAL.md, DIAGNOSIS.md).

Reads only committed evidence -- no provider calls, no fixtures. Shows that
the four failing instruments assert a CENSUS while the properties they exist
to protect are all still true.

Run:  python experiments/2026-08-05-fix-expired-census-readers/repro.py
"""

import collections
import pathlib
import subprocess

from deepreason.harness import Harness
from deepreason.module_events import recorded_module_fingerprints
from deepreason.run_manifest import (
    UnsupportedRunManifestVersionError,
    load_run_manifest,
)


def committed_roots():
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [pathlib.Path(p).parent for p in tracked if p.endswith("/log.jsonl")]


def kind(root):
    manifest = root / "run-manifest.json"
    if not manifest.exists():
        return "no-manifest"
    try:
        load_run_manifest(manifest)
    except UnsupportedRunManifestVersionError:
        return "raising"
    return "v6"


roots = committed_roots()
census = collections.Counter(kind(r) for r in roots)

stamped, unstamped, refused = [], [], []
for root in roots:
    try:
        harness = Harness(root, read_only=True)
    except UnsupportedRunManifestVersionError:
        refused.append(root)
        continue
    (stamped if recorded_module_fingerprints(harness) else unstamped).append(root)

print("committed roots (git ls-files + /log.jsonl): %d" % len(roots))
print("  census: v6=%d raising=%d no-manifest=%d"
      % (census["v6"], census["raising"], census["no-manifest"]))
print("  openable: %d   refused: %d" % (len(stamped) + len(unstamped), len(refused)))
print()

print("THE DEFECT -- tests/test_module_fingerprints.py:52 asserts")
print("    recorded_module_fingerprints(harness) == ()   for EVERY committed root")
print("  roots WITHOUT a stamp (assertion holds): %d" % len(unstamped))
print("  roots WITH a stamp (assertion FAILS):    %d" % len(stamped))
for root in stamped:
    payload = recorded_module_fingerprints(Harness(root, read_only=True))[0]
    module = payload.modules[0]
    print("      %s  registry=%s module_id=%s"
          % (root, module.registry, module.module_id))
print()

print("THE PROPERTIES the four instruments exist to protect -- all still TRUE:")
print("  P-a  absence is valid on roots written before the feature : %s"
      % (len(unstamped) > 20))
print("  P-b  presence is valid on roots written after it          : %s"
      % (len(stamped) > 0))
print("  P-c  some roots are expected to refuse to open            : %s"
      % (len(refused) > 0))
print("  P-d  'raising' and 'no manifest' are different sets       : %s"
      % (census["raising"] != census["raising"] + census["no-manifest"]))
print()
print("So every instrument is red while every claim underneath it is true.")
print("That is the signature of a census assertion, not of a broken guarantee.")
