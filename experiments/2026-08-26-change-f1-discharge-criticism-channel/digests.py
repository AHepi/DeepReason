#!/usr/bin/env python3
"""The granted contact's acceptance check: the digests themselves.

Run identically BEFORE and AFTER `Config.DISCHARGE_POLICY` and its
versioned-source line; the pair must diff empty. A green suite is not the
check here. `DR-INV-frozen-surfaces`'s own Rung 8 precedent compares the
digest at EVERY schema version, because "no pinned test exists above v3" was
a false inference from an incomplete grep that the full gate then refuted
(the `ENGAGED_CRITICISM_AUTHORITY` trap, which the operator named as this
grant's ancestor).

Usage, from the repository root:

    python experiments/2026-08-26-change-f1-discharge-criticism-channel/digests.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from deepreason.config import Config                                # noqa: E402
from deepreason.qualification import qualification_subject_digest   # noqa: E402
from deepreason.run_manifest import source_config_hash              # noqa: E402
from tests.test_reusable_qualification import _manifest, _profile   # noqa: E402

print("source_config_hash(Config()) by schema version:")
for version in (1, 2, 3, 4, 5, 6):
    print(f"  v{version}  {source_config_hash(Config(), schema_version=version)}")

profile = _profile()
print("qualification_subject_digest(_manifest(_profile()), _profile()):")
print(f"  {qualification_subject_digest(_manifest(profile), profile)}")
