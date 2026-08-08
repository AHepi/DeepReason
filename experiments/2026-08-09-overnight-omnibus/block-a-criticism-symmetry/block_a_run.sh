#!/usr/bin/env bash
# Block A ladder: one cell (SELF or CROSS) of the criticism-symmetry
# pilot (PREREG.yaml, frozen before first call). One setup + one
# qualify (paying the ~14-minute battery once), then 2 questions x 3
# seeds = 6 `reason` calls in the SAME home so qualification cache-hits
# for calls 2-6. No `continue` step -- Block A measures the natural
# stop, not continuation.
#
# Usage: ./block_a_run.sh self|cross
set -u
CELL="${1:?usage: block_a_run.sh self|cross}"
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../env"; set +a
REPO="$(cd "$LIVE/../../.." && pwd)"

HOME_DIR="$LIVE/home-$CELL"
LOG="$LIVE/block-a-$CELL-driver.log"
mkdir -p "$HOME_DIR"
export DEEPREASON_HOME="$HOME_DIR"

{
  echo "=== block-a-$CELL start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) ==="

  SETUP_ARGS=(setup --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 16384 \
    --reasoning none --credential-env OLLAMA_API_KEY)

  if [ "$CELL" = "cross" ]; then
    if [ ! -f "$LIVE/coder-profile.yaml" ]; then
      python3 "$LIVE/write_cross_profile.py" "$LIVE/coder-profile.yaml"
      echo "write_cross_profile_rc=$?"
    else
      echo "cross_profile_reused=$LIVE/coder-profile.yaml"
    fi
    SETUP_ARGS+=(--seat "conjecture=$LIVE/coder-profile.yaml")
  fi

  timeout 300 deepreason "${SETUP_ARGS[@]}"
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  for qidx in 1 2; do
    for sidx in 1 2 3; do
      QUESTION=$(python3 "$LIVE/block_a_questions.py" get "$qidx" "$sidx")
      TAG="q${qidx}s${sidx}"
      r0=$SECONDS
      timeout 3600 deepreason reason "$QUESTION" --cycles 6 --token-budget 90000 --allow-partial \
        > "$LIVE/block-a-$CELL-$TAG.json" 2> "$LIVE/block-a-$CELL-$TAG.err"
      rc=$?
      echo "reason_rc=$rc reason_seconds=$((SECONDS-r0)) tag=$TAG"

      run_id=$(python3 -c "import json;print(json.load(open('$LIVE/block-a-$CELL-$TAG.json'))['run_id'])" 2>/dev/null)
      echo "run_id=$run_id tag=$TAG"
      root="$HOME_DIR/runs/$run_id"
      if [ -n "$run_id" ] && [ -d "$root" ]; then
        python3 "$LIVE/block_a_audit.py" "$root" "$CELL" "$qidx" "$sidx" \
          > "$LIVE/block-a-$CELL-$TAG-audit.json" 2> "$LIVE/block-a-$CELL-$TAG-audit.err"
        echo "audit_rc=$? tag=$TAG"
      else
        echo "audit_skipped=no_run_root tag=$TAG"
      fi
    done
  done

  echo "=== block-a-$CELL end $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
