"""Phase 5: check whether a root is amendable, from the record --
never assumed from run-status.json's `state` field alone. Mirrors
amendment/apply.py's own _require_terminal_stop pattern exactly (load
the epoch-aware manifest, then derive_terminal_authority with it).

Usage: python3 phase5_check_amendable.py ROOT
Prints {"amendable": bool, "status": str, "terminal_status": str|null}
"""

import json
import sys
from pathlib import Path

from deepreason.amendment.apply import load_amendments, load_epoch_manifest
from deepreason.runtime.terminal_authority import derive_terminal_authority

root = Path(sys.argv[1])
out = {"root": str(root)}

try:
    committed = load_amendments(root)
    parent_epoch = len(committed)
    manifest = load_epoch_manifest(root, parent_epoch)
    authority = derive_terminal_authority(root, manifest=manifest)
    out["status"] = authority.status
    out["current_valid"] = authority.current_valid
    out["terminal_status"] = authority.terminal_status
    out["amendable"] = bool(
        authority.current_valid and authority.terminal_status in {"completed", "cancelled", "failed"}
    )
except Exception as exc:  # noqa: BLE001 -- a check failure is itself data
    out["amendable"] = False
    out["check_error"] = f"{type(exc).__name__}: {exc}"

print(json.dumps(out, indent=2, sort_keys=True))
