#!/usr/bin/env bash
# Block C ladder: one completion-cap point (4096|8192|16384). One
# setup + one qualify (paying its own full battery -- a fresh cap is
# a fresh provider-profile digest), then 2 seeds (distinguishing
# leading sentence) of the SAME fixed hard question in the SAME home
# so the second seed's qualification cache-hits.
#
# Usage: ./block_c_run.sh 4096|8192|16384
set -u
CAP="${1:?usage: block_c_run.sh 4096|8192|16384}"
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../env"; set +a
REPO="$(cd "$LIVE/../../.." && pwd)"

HOME_DIR="$LIVE/home-$CAP"
LOG="$LIVE/block-c-$CAP-driver.log"
mkdir -p "$HOME_DIR"
export DEEPREASON_HOME="$HOME_DIR"

{
  echo "=== block-c-$CAP start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) ==="

  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens "$CAP" \
    --reasoning none --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3 \
    > "$LIVE/block-c-$CAP-qualify.json" 2> "$LIVE/block-c-$CAP-qualify.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  for sidx in 1 2; do
    QUESTION=$(python3 "$LIVE/block_c_question.py" get "$sidx")
    TAG="s${sidx}"
    r0=$SECONDS
    timeout 3600 deepreason reason "$QUESTION" --cycles 6 --token-budget 90000 --allow-partial \
      > "$LIVE/block-c-$CAP-$TAG.json" 2> "$LIVE/block-c-$CAP-$TAG.err"
    rc=$?
    echo "reason_rc=$rc reason_seconds=$((SECONDS-r0)) tag=$TAG"

    run_id=$(python3 -c "import json;print(json.load(open('$LIVE/block-c-$CAP-$TAG.json'))['run_id'])" 2>/dev/null)
    echo "run_id=$run_id tag=$TAG"
    root="$HOME_DIR/runs/$run_id"
    if [ -n "$run_id" ] && [ -d "$root" ]; then
      python3 "$LIVE/block_c_audit.py" "$root" "$CAP" "$sidx" "$LIVE/block-c-$CAP-qualify.json" \
        > "$LIVE/block-c-$CAP-$TAG-audit.json" 2> "$LIVE/block-c-$CAP-$TAG-audit.err"
      echo "audit_rc=$? tag=$TAG"
    else
      echo "audit_skipped=no_run_root tag=$TAG"
    fi
  done

  echo "=== block-c-$CAP end $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
