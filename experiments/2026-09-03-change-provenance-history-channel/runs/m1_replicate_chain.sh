#!/bin/bash
# The two replicate pairs of PREREG.md Amendment 5, serial, control first in
# each pair for the reason Amendment 4 already gave: if the budget or the
# container ends the chain early, what survives is a control with a paired
# treatment or nothing, never a treatment with no baseline.
#
# Serial, not parallel: five concurrent arms at qualification concurrency 4 is
# what produced the rate-limit storm that destroyed two arms of this tranche
# (PARKED P3, P4). One arm at a time, concurrency 2.
set -u
B=/home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
cd "$B"
idle () { while [ "$(ps -eo args 2>/dev/null | grep -c '[d]eepreason')" -gt 0 ]; do sleep 20; done; }
echo "### M1 replication start $(date -u +%FT%TZ)"
for pair in r2 r3; do
  idle
  ./m1_replicate.sh "home-m1-$pair" "M1-H0P-$pair" "$B/history-placebo.txt" > "m1_h0p_$pair.log" 2>&1
  echo "### H0P-$pair rc=$? $(date -u +%FT%TZ)"
  idle
  ./m1_replicate.sh "home-m1-$pair" "M1-H1R-$pair" "$B/history-real.txt" > "m1_h1r_$pair.log" 2>&1
  echo "### H1R-$pair rc=$? $(date -u +%FT%TZ)"
done
echo "### M1 replication finished $(date -u +%FT%TZ)"
