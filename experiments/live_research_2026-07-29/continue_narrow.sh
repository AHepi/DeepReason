#!/usr/bin/env bash
# Popper calibration: continue the narrow run past its typed
# budget_exhausted stop with the allowance controller live, then compose a
# superseding bridge at the advanced fence.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
export DEEPREASON_HOME="$LIVE/narrow"
RUN=run-7d8723fbe8626c71db880826c244d332
ROOT="$LIVE/narrow/runs/$RUN"
{
  echo "=== narrow-continue start $(date -u +%FT%TZ) ==="
  c0=$SECONDS
  timeout 7200 deepreason --root "$ROOT" continue --budget cycles=6 --token-budget 80000 \
    > "$LIVE/narrow-continue.json" 2> "$LIVE/narrow-continue.err"
  echo "continue_rc=$? continue_seconds=$((SECONDS-c0))"
  state=$(python3 -c "import json;print(json.load(open('$LIVE/narrow-continue.json'))['state'])" 2>/dev/null)
  echo "state=$state"
  python3 "$LIVE/research_audit.py" "$DEEPREASON_HOME" "$RUN" \
    > "$LIVE/narrow-continue-research-audit.json" 2> "$LIVE/narrow-continue-research-audit.err"
  echo "audit_rc=$?"
  if [ "$state" = "completed" ]; then
    b0=$SECONDS
    timeout 7200 python3 "$LIVE/bridge_trio.py" "$DEEPREASON_HOME" "$RUN" "question-27633c5a9c5c7a55f009bf27b0b8c744" \
      > "$LIVE/narrow-continue-bridge.txt" 2> "$LIVE/narrow-continue-bridge.err"
    echo "bridge_rc=$? bridge_seconds=$((SECONDS-b0))"
  fi
  echo "=== narrow-continue end $(date -u +%FT%TZ) ==="
} >> "$LIVE/narrow-continue.log" 2>&1
