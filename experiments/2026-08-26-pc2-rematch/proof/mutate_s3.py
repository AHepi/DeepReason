"""Mutation proof for preflight_pc2.py's S3 check.

S3 is the check that stands between this tranche and a silent repeat of
P-C1: it refuses the launch if the discharge channel will be OFF at runtime.
A check that cannot fail is not a check, so this drives it with deviation D1
REMOVED -- the code default restored to "off" -- and asserts it goes RED.

The default is patched in memory, never on disk: an edit-and-revert can be
interrupted and leave the tree wrong, and this proof runs beside a launch.
"""
import sys
from pathlib import Path

REPO = Path("/home/user/DeepReason")
TRANCHE = REPO / "experiments" / "2026-08-26-pc2-rematch"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

from deepreason.config import Config

Config.model_fields["DISCHARGE_POLICY"].default = "off"
Config.model_rebuild(force=True)
assert Config().DISCHARGE_POLICY == "off", "the mutation did not take"
print("MUTATION APPLIED: Config.DISCHARGE_POLICY default restored to 'off' (D1 removed)")

import preflight_pc2

root = Path(sys.argv[1])
preflight_pc2.s3_channel_live(root)
if "S3-discharge-channel-live-at-runtime" in preflight_pc2._failures:
    print("\nMUTATION PROOF OK: S3 goes RED when deviation D1 is absent.")
    raise SystemExit(0)
print("\nMUTATION PROOF FAILED: S3 stayed GREEN with the channel off at runtime.",
      file=sys.stderr)
raise SystemExit(1)
