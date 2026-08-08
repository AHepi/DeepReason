#!/usr/bin/env bash
# Block B ladder: one setup + one qualify (paying the ~14-minute
# battery once, --attached-evidence to match the --attach opt-in used
# by every `reason` call), then 10 seeds (distinguishing leading
# sentence) of the SAME fixed simulation-friendly question in the SAME
# home so qualification cache-hits for seeds 2-10.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../env"; set +a
REPO="$(cd "$LIVE/../../.." && pwd)"

HOME_DIR="$LIVE/home-b"
LOG="$LIVE/block-b-driver.log"
mkdir -p "$HOME_DIR"
export DEEPREASON_HOME="$HOME_DIR"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"

{
  echo "=== block-b start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) ==="

  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --reasoning none --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3 --attached-evidence \
    > "$LIVE/block-b-qualify.json" 2> "$LIVE/block-b-qualify.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  for sidx in $(seq 1 10); do
    QUESTION=$(python3 "$LIVE/block_b_question.py" get "$sidx")
    TAG="s${sidx}"
    r0=$SECONDS
    timeout 3600 deepreason reason "$QUESTION" --cycles 6 --token-budget 90000 --allow-partial \
      --attach "$LIVE/dossier/CAPABILITY_CONTRACT.md" \
      > "$LIVE/block-b-$TAG.json" 2> "$LIVE/block-b-$TAG.err"
    rc=$?
    echo "reason_rc=$rc reason_seconds=$((SECONDS-r0)) tag=$TAG"

    run_id=$(python3 -c "import json;print(json.load(open('$LIVE/block-b-$TAG.json'))['run_id'])" 2>/dev/null)
    echo "run_id=$run_id tag=$TAG"
    root="$HOME_DIR/runs/$run_id"
    if [ -n "$run_id" ] && [ -d "$root" ]; then
      python3 "$LIVE/block_b_audit.py" "$root" "$sidx" \
        > "$LIVE/block-b-$TAG-audit.json" 2> "$LIVE/block-b-$TAG-audit.err"
      echo "audit_rc=$? tag=$TAG"
    else
      echo "audit_skipped=no_run_root tag=$TAG"
    fi
  done

  echo "=== block-b end $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
