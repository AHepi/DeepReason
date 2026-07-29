#!/usr/bin/env bash
# Segment 3: continue past the SECOND bridge (tail now includes two bridge
# epochs), with the citable-block legend live in packs — the citation
# conversion test — then compose the third-epoch superseding bridge.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
export DEEPREASON_HOME="$LIVE/narrow"
RUN=run-7d8723fbe8626c71db880826c244d332
ROOT="$LIVE/narrow/runs/$RUN"
{
  echo "=== narrow-continue3 start $(date -u +%FT%TZ) ==="
  c0=$SECONDS
  timeout 7200 deepreason --root "$ROOT" continue --budget cycles=6 --token-budget 80000 \
    > "$LIVE/narrow-continue3.json" 2> "$LIVE/narrow-continue3.err"
  echo "continue_rc=$? continue_seconds=$((SECONDS-c0))"
  state=$(python3 -c "import json;print(json.load(open('$LIVE/narrow-continue3.json'))['state'])" 2>/dev/null)
  echo "state=$state"
  python3 "$LIVE/research_audit.py" "$DEEPREASON_HOME" "$RUN" \
    > "$LIVE/narrow-continue3-research-audit.json" 2> "$LIVE/narrow-continue3-research-audit.err"
  echo "audit_rc=$?"
  if [ "$state" = "completed" ]; then
    b0=$SECONDS
    timeout 7200 deepreason --root "$ROOT" bridge build question-27633c5a9c5c7a55f009bf27b0b8c744 \
      --target answer --json > "$LIVE/narrow-bridge3.json" 2> "$LIVE/narrow-bridge3.err"
    echo "bridge_rc=$? bridge_seconds=$((SECONDS-b0))"
  fi
  echo "=== narrow-continue3 end $(date -u +%FT%TZ) ==="
} >> "$LIVE/narrow-continue3.log" 2>&1
