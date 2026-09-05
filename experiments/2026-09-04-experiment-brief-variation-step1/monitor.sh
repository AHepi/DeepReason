#!/usr/bin/env bash
# The monitor the ladder rules require: the newest root's progress.jsonl
# (state / phase / tokens) and the driver log's rc= lines, sampled every 60s.
# It alerts on FAILURE SIGNATURES, not only on success — a run that is quietly
# not advancing looks identical to a healthy one if you only watch for "done".
set -u
REPO="/home/user/DeepReason"
REL="experiments/2026-09-04-experiment-brief-variation-step1"
HOME_DIR="$REPO/$REL/runs/home-step1"
LOG="${1:?usage: monitor.sh <driver-log>}"
LAST_SEQ=""
while pgrep -f "arm.sh" >/dev/null 2>&1; do
  ROOT="$(ls -dt "$HOME_DIR"/runs/run-* 2>/dev/null | head -1)"
  STAMP="$(date -u +%FT%TZ)"
  if [ -n "${ROOT:-}" ] && [ -f "$ROOT/progress.jsonl" ]; then
    LINE="$(tail -1 "$ROOT/progress.jsonl")"
    [ "$LINE" != "$LAST_SEQ" ] && echo "$STAMP progress $LINE"
    LAST_SEQ="$LINE"
  else
    echo "$STAMP no root yet"
  fi
  grep -nE "^rc=[^0]|ARM INVALID|ARM RIG (FAILED|REFUSED)|RUN_ALREADY_STARTED|ENDPOINT_HTTP_429|operational_failure|Traceback" "$LOG" 2>/dev/null \
    | tail -3 | sed "s/^/$STAMP ALERT /"
  sleep 60
done
echo "$(date -u +%FT%TZ) monitor: no arm.sh running"
