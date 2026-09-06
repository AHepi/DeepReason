#!/bin/bash
# ARM 0R: the bare model with the room pasted in. PREREG Amendment 2.
# Three calls through runs/arm0R.py; the attachment's digests are checked
# first so the pasted room is byte-for-byte the room ARM R bound.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-06-change-writers-room-organiser-testing
set -a; . $D/env; set +a
echo "=== ARM 0R started $(date -u +%FT%TZ) ==="
(cd $D/attachment && sha256sum -c ATTACHMENT.sha256) || { echo "ARM INVALID: attachment digests do not match"; exit 6; }
python -u $D/runs/arm0R.py --dry-run
python -u $D/runs/arm0R.py; echo "rc=$?"
echo "=== ARM 0R finished $(date -u +%FT%TZ) ==="
