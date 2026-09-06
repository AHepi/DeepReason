#!/bin/bash
# The launch chain PREREG_D8.md §6 step 3 fixes: ARM 0 first, then ARM M.
# Detached from the repo root; the snapshot loop watches this script's name.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-05-change-mini-isolation-programme
set -a; . $D/env; set +a
echo "=== ARM 0 started $(date -u +%FT%TZ) ==="
python -u $D/d8/arm0.py > $D/d8/arm0.log 2>&1; echo "arm0 rc=$?"
echo "=== ARM M started $(date -u +%FT%TZ) ==="
$D/d8/armM.sh > $D/d8/armM.log 2>&1; echo "armM rc=$?"
echo "=== chain finished $(date -u +%FT%TZ) ==="
