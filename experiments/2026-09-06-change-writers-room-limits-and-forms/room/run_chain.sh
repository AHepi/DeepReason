#!/bin/bash
# Soak first (no live launch without a green soak on the box), then the room.
set -u
cd /home/user/DeepReason
T=experiments/2026-09-06-change-writers-room-limits-and-forms
echo "=== soak started $(date -u +%FT%TZ) ==="
python -u scripts/cycle_soak.py --case epoch3 > $T/room/soak.log 2>&1; rc=$?; echo "soak rc=$rc"
grep -E "^\[soak\] exit|\[PASS\]|\[FAIL\]" $T/room/soak.log | tail -12
if [ "$rc" -ne 0 ]; then echo "SOAK RED -- room run NOT launched"; exit 2; fi
echo "=== room started $(date -u +%FT%TZ) ==="
$T/room/room.sh > $T/room/room.log 2>&1; echo "room rc=$?"
echo "=== chain finished $(date -u +%FT%TZ) ==="
