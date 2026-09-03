#!/bin/bash
# FULLY SERIAL chain, one deepreason process at a time, M1 before M3.
#
# Two arms were already lost to ONE cause: provider rate limiting from running
# five workloads at once.
#   M3-C0  qualified shallow (17/300 cases ENDPOINT_HTTP_429) -> reasoning refused
#   M1-H0  operational_failure at cycle 3 ("atomic child is terminally failed"),
#          7 of 71 provider attempts transport_failure, 429 in 52 files of the root
# Neither is a code defect and neither is re-run hopefully: serial removes the
# cause. The operator's cap is 3; this uses 1.
#
# Each stage checks its predecessor produced a usable root before spending
# anything, so a failure stops the chain instead of cascading into arms that
# silently measure nothing.
set -u
cd /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
A=/home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
P=experiments/2026-09-03-change-provenance-history-channel/runs

idle () { while [ "$(ps -eo args 2>/dev/null | grep -cE '[d]eepreason (reason|qualify)')" -gt 0 ]; do sleep 20; done; }

# A root counts only if it terminated WITHOUT an operational failure. A root
# that died at cycle 3 is not a control, and seeding a treatment arm from one
# would produce two arms that are not comparable -- the exact mistake this
# chain exists to avoid repeating.
good_root () {
  local home="$1"
  local r; r=$(ls -dt "$home"/runs/run-* 2>/dev/null | head -1)
  [ -z "$r" ] && return 1
  python3 - "$r" <<'PY' || return 1
import json,sys,pathlib
p=pathlib.Path(sys.argv[1])/"progress.jsonl"
d=json.loads(p.read_text().strip().split("\n")[-1])
sys.exit(0 if d.get("stop_reason") != "operational_failure" and d.get("state") != "failed" else 1)
PY
  echo "$r"
}

echo "### chain start $(date -u +%FT%TZ)"

idle; echo "### H0 $(date -u +%FT%TZ)"
./arm.sh $P/home-default M1-H0 none > m1_h0.log 2>&1; echo "### H0 rc=$?"
H0=$(good_root home-default) || { echo "### H0 produced no usable root -- STOP"; exit 1; }
echo "### H0 OK root=$H0"

idle; echo "### H1 $(date -u +%FT%TZ)"
./arm.sh $P/home-h1 M1-H1 conjecturer "$A/$H0" > m1_h1.log 2>&1; echo "### H1 rc=$?"
echo "### M1 COMPLETE $(date -u +%FT%TZ)"

idle; echo "### C0 $(date -u +%FT%TZ)"
./arm.sh $P/home-c0 M3-C0 none > m3_c0.log 2>&1; echo "### C0 rc=$?"
C0=$(good_root home-c0) || { echo "### C0 produced no usable root -- STOP after M1"; exit 1; }
echo "### C0 OK root=$C0"

idle; echo "### C1 $(date -u +%FT%TZ)"
./arm.sh $P/home-c1 M3-C1 critic "$A/$C0" > m3_c1.log 2>&1; echo "### C1 rc=$?"
echo "### M3 COMPLETE -- chain finished $(date -u +%FT%TZ)"
