"""Which committed run-config.yaml files set which CLASS of Config field?

    PYTHONPATH=src:mini python \
      experiments/2026-08-29-defect-managed-path-config-read/probe/profile_owned_fields.py

Three classes decide the whole design: PROFILE-OWNED (the seven
`preparation._config_for_profile` derives from the provider profile),
ECHO-DROPPED (absent from `engine_config_json`, so carriage can never reach the
run -- disclosure is the only limb), and ECHOED (carried into the run, and
therefore priced). Exit code 0 always: a measurement, not a test.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from deepreason.config import Config, load as load_config  # noqa: E402
from deepreason.run_manifest import (  # noqa: E402
    _unconditionally_dropped_config_fields,
)

PROFILE_DERIVED = (
    "engine_profile", "model_profile", "scratchpad", "bridge",
    "EMBEDDER_MODEL", "CHANNELS_DISABLED", "roles",
)


def main() -> int:
    dropped = set(_unconditionally_dropped_config_fields())
    default = Config()
    rows = []
    for path in sorted(REPO.glob("experiments/*/run-config.yaml")):
        cfg = load_config(path)
        d = cfg.model_dump(mode="python")
        dd = default.model_dump(mode="python")
        set_fields = sorted(k for k in d if d[k] != dd[k])
        owned = [f for f in set_fields if f in PROFILE_DERIVED]
        drop = [f for f in set_fields if f in dropped and f not in PROFILE_DERIVED]
        echo = [f for f in set_fields if f not in dropped and f not in PROFILE_DERIVED]
        print(f"{path.parent.name}")
        print(f"  profile-owned set : {owned or '-'}")
        print(f"  echo-dropped set  : {drop or '-'}")
        print(f"  echoed set        : {echo or '-'}")
        rows.append((owned, drop, echo))
    print()
    print(f"configs setting a profile-owned field : {sum(1 for o, _, _ in rows if o)} of {len(rows)}")
    print(f"configs setting an echoed field       : {sum(1 for _, _, e in rows if e)} of {len(rows)}")
    print(f"configs setting an echo-dropped field : {sum(1 for _, dr, _ in rows if dr)} of {len(rows)}")
    print()
    print(f"dropped-field count: {len(dropped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
