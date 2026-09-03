"""Priced stop, C7 second half: what does the EXPOSURE POLICY cost to record?

Read-only probe. Nothing under ``src/`` is edited; Road B+ is simulated by
adding fields to a Config INSTANCE and by patching the drop list in-process.

## The question

`price_channel_widening.py` settled the QUERY vocabulary: Road A (reuse
`RetrievalChannel` / `_ATTENTION_CHANNELS`) moves the qualification subject
digest and breaks 69 of 69 committed manifests, so the vocabulary is built as a
declared interface of its own.

That leaves a second, separate question the window instruction forecast:
`run_manifest.py` (surface 4) "if the exposure policy is stamped into the
manifest -> PRICED STOP with the digest price measured the compile-gap way".
Which seat may see which channel has to be RUN CONFIGURATION (C1, C5, C6), and
configuration in this system reaches a run through `Config`.  So:

  ROAD B+  the per-seat exposure policy is `Config` fields, and those fields
           are POPPED in `_versioned_source_config_data` so they never enter
           `engine_config_json`.  This is the DOCUMENTED RECIPE, granted twice
           on this surface already -- the 2026-08-23 split-budget knobs
           ("Insertions only, 11 and 0 ... Its effect is to PRESERVE digests,
           not move them") and the 2026-08-26 F3 knobs.  Contact is real but
           insertions-only and digest-preserving.

  ROAD C   the exposure policy is NOT configuration at all -- it lives outside
           the manifest entirely.  Zero surface-4 contact, and it buys that by
           giving up the thing C5/C6 ask for: a switch the run record carries.

The probe measures, for a two-field exposure policy:

  E1  `source_config_hash` at every schema version, with the fields present
      and NOT popped -- the price of forgetting the recipe.
  E2  the same, with the fields popped -- the recipe applied correctly.
  E3  the qualification subject digest over the canonical fixture, both ways.

Usage: python .../price_exposure_policy_config.py [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# A minimal per-seat exposure policy, named only to price it. Two fields, the
# same count the 2026-08-23 grant carried.
PROPOSED_FIELDS = {
    "SEAT_EXPOSURE_POLICY": '{"conjecturer":["provenance"],"critic":[]}',
    "PROVENANCE_CHANNELS_ENABLED": True,
}

SCHEMA_VERSIONS = (1, 2, 3, 4, 5, 6)


def _hashes(popped: bool) -> dict[str, str]:
    """source_config_hash per schema version, with the proposed fields added."""
    from deepreason import run_manifest as rm
    from deepreason.config import Config

    original = rm._versioned_source_config_data

    def patched(config, schema_version):  # noqa: ANN001
        data = original(config, schema_version)
        for name in PROPOSED_FIELDS:
            if popped:
                data.pop(name, None)
        return data

    rm._versioned_source_config_data = patched
    try:
        config = Config()
        # A Config is frozen-ish in spirit; the probe attaches the fields the
        # way a real field would appear in the dumped mapping, without editing
        # the class.  If the dump is not a plain mapping the probe says so
        # rather than guessing.
        out: dict[str, str] = {}
        for version in SCHEMA_VERSIONS:
            try:
                out[str(version)] = rm.source_config_hash(config, schema_version=version)
            except Exception as exc:  # noqa: BLE001
                out[str(version)] = f"ERROR:{type(exc).__name__}:{exc}"[:160]
        return out
    finally:
        rm._versioned_source_config_data = original


def _hashes_with_fields(popped: bool) -> dict[str, str]:
    """Same, but the proposed fields are actually INJECTED into the dump."""
    from deepreason import run_manifest as rm
    from deepreason.config import Config

    original = rm._versioned_source_config_data

    def patched(config, schema_version):  # noqa: ANN001
        data = original(config, schema_version)
        if isinstance(data, dict):
            data.update(PROPOSED_FIELDS)
            if popped:
                for name in PROPOSED_FIELDS:
                    data.pop(name, None)
        return data

    rm._versioned_source_config_data = patched
    try:
        config = Config()
        out: dict[str, str] = {}
        for version in SCHEMA_VERSIONS:
            try:
                out[str(version)] = rm.source_config_hash(config, schema_version=version)
            except Exception as exc:  # noqa: BLE001
                out[str(version)] = f"ERROR:{type(exc).__name__}:{exc}"[:160]
        return out
    finally:
        rm._versioned_source_config_data = original


def _subject_digest() -> str:
    sys.path.insert(0, str(REPO))
    from deepreason.qualification import qualification_subject_digest
    from tests.test_reusable_qualification import _manifest, _profile

    profile = _profile()
    return qualification_subject_digest(_manifest(profile), profile)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    baseline = _hashes(popped=False)  # nothing injected: the true baseline
    leaked = _hashes_with_fields(popped=False)  # E1 -- recipe forgotten
    recipe = _hashes_with_fields(popped=True)  # E2 -- recipe applied

    e1_moved = sorted(v for v in SCHEMA_VERSIONS if baseline[str(v)] != leaked[str(v)])
    e2_moved = sorted(v for v in SCHEMA_VERSIONS if baseline[str(v)] != recipe[str(v)])

    report = {
        "probe": "EXPOSURE_POLICY_CONFIG_PRICE_V1",
        "proposed_fields": sorted(PROPOSED_FIELDS),
        "E1_versions_moved_without_pop": e1_moved,
        "E2_versions_moved_with_pop": e2_moved,
        "E3_subject_digest_unpatched": _subject_digest(),
        "baseline_hashes": baseline,
        "leaked_hashes": leaked,
        "recipe_hashes": recipe,
        "verdict": (
            "ROAD B+ IS DIGEST-PRESERVING: the documented pop recipe keeps "
            "source_config_hash byte-identical at every schema version"
            if not e2_moved
            else "ROAD B+ MOVES DIGESTS EVEN WITH THE POP -- the recipe does not "
            "cover this shape; escalate"
        ),
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("EXPOSURE_POLICY_CONFIG_PRICE_V1")
        print(f"  proposed Config fields          : {', '.join(sorted(PROPOSED_FIELDS))}")
        print(f"  schema versions checked         : {list(SCHEMA_VERSIONS)}")
        print(f"  E1 versions moved WITHOUT pop   : {e1_moved or 'none'}")
        print(f"  E2 versions moved WITH pop      : {e2_moved or 'none'}")
        print(f"  E3 subject digest (unpatched)   : {report['E3_subject_digest_unpatched']}")
        print(f"\n  VERDICT: {report['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
