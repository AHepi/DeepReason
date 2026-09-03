#!/bin/bash
# Serial M3 through the same evidence channel as M1: placebo control, then
# the target's rebuttal/discharge history. Control first, same reasoning as M1.
set -u
cd /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
A=/home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
idle () { while [ "$(ps -eo args 2>/dev/null | grep -c '[d]eepreason')" -gt 0 ]; do sleep 20; done; }
echo "### M3 chain start $(date -u +%FT%TZ)"
idle
./m3_attach.sh M3-C0P "$A/critic-placebo.txt" > m3_c0p.log 2>&1; echo "### C0P rc=$? $(date -u +%FT%TZ)"
idle
./m3_attach.sh M3-C1I "$A/critic-real.txt" > m3_c1i.log 2>&1; echo "### C1I rc=$? $(date -u +%FT%TZ)"
echo "### M3 chain finished $(date -u +%FT%TZ)"
