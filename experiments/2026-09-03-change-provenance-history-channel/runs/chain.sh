#!/bin/bash
# FULLY SERIAL chain, one deepreason process at a time, M1 before M3.
#
# IDEMPOTENT BY DESIGN. Run identity is deterministic, so re-running an arm
# whose root already exists fails RUN_ALREADY_STARTED -- which is what happened
# when this chain was restarted after the H1 injection fix and tried to redo
# the already-finished H0. Each stage therefore SKIPS if its home already holds
# a usable root and runs only the arms actually missing, which also makes the
# chain safe to restart after any interruption.
#
# SERIAL, not merely under the cap. Two arms were lost to provider rate
# limiting when five workloads shared one endpoint: M3-C0 qualified shallow
# (17/300 ENDPOINT_HTTP_429) and M1-H0 died operational_failure mid-reasoning
# (7/71 attempts transport_failure). Serial removes the cause instead of
# hoping a lower number is low enough. The operator's cap is 3; this uses 1.
set -u
cd /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
A=/home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
P=experiments/2026-09-03-change-provenance-history-channel/runs

idle () {
  while [ "$(ps -eo args 2>/dev/null | grep -c '[d]eepreason')" -gt 0 ]; do sleep 20; done
}

# A root counts only if it terminated WITHOUT an operational failure. A root
# that died mid-run is not a control, and seeding a treatment arm from one
# would produce two arms that are not comparable.
good_root () {
  local r
  r=$(ls -dt "$1"/runs/run-* 2>/dev/null | head -1)
  [ -z "$r" ] && return 1
  python3 - "$r" <<'PY' || return 1
import json, sys, pathlib
d = json.loads((pathlib.Path(sys.argv[1]) / "progress.jsonl").read_text().strip().split("\n")[-1])
sys.exit(0 if d.get("stop_reason") != "operational_failure" and d.get("state") != "failed" else 1)
PY
  echo "$r"
}

# stage <home> <label> <logname> <mode> [src-root]
stage () {
  local home="$1" label="$2" logname="$3" mode="$4" src="${5:-}"
  local existing
  if existing=$(good_root "$home"); then
    echo "### $label SKIPPED -- usable root already present" >&2
    echo "$existing"
    return 0
  fi
  idle
  echo "### $label starting $(date -u +%FT%TZ)" >&2
  if [ -n "$src" ]; then
    ./arm.sh "$P/$(basename "$home")" "$label" "$mode" "$src" > "$logname" 2>&1
  else
    ./arm.sh "$P/$(basename "$home")" "$label" "$mode" > "$logname" 2>&1
  fi
  echo "### $label rc=$? $(date -u +%FT%TZ)" >&2
  good_root "$home"
}

echo "### chain start $(date -u +%FT%TZ)"

H0=$(stage home-default M1-H0 m1_h0.log none) || { echo "### H0 unusable -- STOP"; exit 1; }
echo "### H0 root=$H0"

H1=$(stage home-h1 M1-H1 m1_h1.log conjecturer "$A/$H0") || echo "### H1 produced no usable root"
echo "### H1 root=${H1:-none}"
echo "### M1 COMPLETE $(date -u +%FT%TZ)"

C0=$(stage home-c0 M3-C0 m3_c0.log none) || { echo "### C0 unusable -- STOP after M1"; exit 1; }
echo "### C0 root=$C0"

C1=$(stage home-c1 M3-C1 m3_c1.log critic "$A/$C0") || echo "### C1 produced no usable root"
echo "### C1 root=${C1:-none}"
echo "### M3 COMPLETE -- chain finished $(date -u +%FT%TZ)"
