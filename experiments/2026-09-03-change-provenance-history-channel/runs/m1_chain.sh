#!/bin/bash
# Serial M1 through the evidence channel: placebo control, then treatment.
# Control first so that if the budget ends mid-chain, what exists is a control
# and a measured baseline rather than a treatment arm with nothing to compare.
set -u
cd /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
idle () { while [ "$(ps -eo args 2>/dev/null | grep -c '[d]eepreason')" -gt 0 ]; do sleep 20; done; }
echo "### M1 evidence-channel chain start $(date -u +%FT%TZ)"
idle
./m1_attach.sh M1-H0P /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs/history-placebo.txt > m1_h0p.log 2>&1; echo "### H0P rc=$? $(date -u +%FT%TZ)"
idle
./m1_attach.sh M1-H1R /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs/history-real.txt > m1_h1r.log 2>&1; echo "### H1R rc=$? $(date -u +%FT%TZ)"
echo "### M1 chain finished $(date -u +%FT%TZ)"
