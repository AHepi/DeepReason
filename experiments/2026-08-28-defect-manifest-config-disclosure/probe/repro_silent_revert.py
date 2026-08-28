#!/usr/bin/env python3
"""Smallest offline reproduction of P10 / AUDIT_REPORT.md F-A.

Compiles a manifest through `build_manifest_pt1.py`'s EXACT call shape --
schema 6, text, rubric_policy="require_cross_family", concurrency=2, an
engaged control plane, and NO `criticism_policy` argument -- from a Config
carrying P-T1's five "everything on" switches, then reconstructs the
run-time Config the single run path would use.

Run:  PYTHONPATH=. python experiments/.../probe/repro_silent_revert.py
Exit: 0 when the silent revert is present (the defect reproduces),
      1 when every configured switch survives or is disclosed.
"""
from __future__ import annotations

import sys

from deepreason.run_manifest import config_from_run_manifest
from tests.test_reusable_qualification import _manifest, _profile

PT1_SWITCHES = {
    "JUDGE_SEATS_ENABLED": True,
    "ADJUDICATION_STATUS_AUTHORITY_ENABLED": True,
    "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
    "LEGACY_CRITICISM_ENABLED": False,
    "SCHOOL_SEATS_ENABLED": True,
}


def main() -> int:
    profile = _profile()
    manifest = _manifest(
        profile,
        config_updates=PT1_SWITCHES,
        rubric_policy="require_cross_family",
        concurrency=2,
        # build_manifest_pt1.py:307-333 passes no criticism_policy at all.
        criticism_policy=None,
    )
    runtime = config_from_run_manifest(manifest)

    print("manifest.criticism_policy = %r" % (manifest.criticism_policy,))
    print("manifest.compile_notices  = %r" % (manifest.compile_notices,))
    print()
    reverted = []
    for field, configured in PT1_SWITCHES.items():
        effective = getattr(runtime, field)
        flag = "REVERTED" if effective != configured else "carried"
        if effective != configured:
            reverted.append(field)
        print("  %-8s %-40s configured=%-16r run time=%r"
              % (flag, field, configured, effective))

    disclosed = {
        field
        for notice in (manifest.compile_notices or ())
        for field in PT1_SWITCHES
        if field in notice.message or field in notice.pointer
    }
    print("\n  reverted: %d of %d" % (len(reverted), len(PT1_SWITCHES)))
    print("  disclosed in compile_notices: %d" % len(disclosed))

    undisclosed = [f for f in reverted if f not in disclosed]
    if undisclosed:
        print("\nDEFECT REPRODUCED: silently reverted with no notice: %s" % undisclosed)
        return 0
    print("\nNo silent revert: every reverted switch is disclosed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
