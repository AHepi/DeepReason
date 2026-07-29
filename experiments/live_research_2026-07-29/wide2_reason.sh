#!/usr/bin/env bash
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
export DEEPREASON_HOME="$LIVE/wide"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org,www.rfc-editor.org"
QUESTION="Deterministic replay in an append-only reasoning system depends on retried operations being safe to repeat. Drawing on published definitions, what precisely distinguishes an idempotent operation from a safe one, and which of the two properties does an append-only event log actually require of its writers to survive at-least-once delivery? You may propose directed research fetches of specific https pages; this run's frozen domain allowlist permits en.wikipedia.org and www.rfc-editor.org (RFC 9110 defines both terms). Fetched pages become citable evidence blocks."
{
  echo "=== wide2 start $(date -u +%FT%TZ) ==="
  r0=$SECONDS
  timeout 7200 deepreason reason "$QUESTION" > "$LIVE/wide2-reason.json" 2> "$LIVE/wide2-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/wide2-reason.json'))['run_id'])" 2>/dev/null)
  problem_id=$(python3 -c "import json;print(json.load(open('$LIVE/wide2-reason.json'))['problem_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/wide2-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id problem_id=$problem_id state=$state"
  python3 "$LIVE/research_audit.py" "$DEEPREASON_HOME" "$run_id" \
    > "$LIVE/wide2-research-audit.json" 2> "$LIVE/wide2-research-audit.err"
  echo "audit_rc=$?"
  if [ "$state" = "completed" ]; then
    timeout 7200 python3 "$LIVE/bridge_trio.py" "$DEEPREASON_HOME" "$run_id" "$problem_id" \
      > "$LIVE/wide2-bridge.txt" 2> "$LIVE/wide2-bridge.err"
    echo "bridge_rc=$?"
  fi
  echo "=== wide2 end $(date -u +%FT%TZ) ==="
} >> "$LIVE/wide2.log" 2>&1
