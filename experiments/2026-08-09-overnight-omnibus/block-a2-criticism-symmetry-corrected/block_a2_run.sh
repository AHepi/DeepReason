#!/usr/bin/env bash
# Block A-2 ladder: one cell (SELF or CROSS) of the corrected
# criticism-symmetry pilot (PREREG-A2.yaml, frozen before first
# call). Reuses Block A's own home directories for qualification
# cache reuse (same profile digests, same coder-profile.yaml file).
# Budget pinned at 10 cycles / 195000 tokens (S6-proven shape); every
# run goes through block_a2_converge.py's continue-until-valid loop
# (max 2 continues) instead of a single `reason` call.
#
# Usage: ./block_a2_run.sh self|cross
set -u
CELL="${1:?usage: block_a2_run.sh self|cross}"
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../env"; set +a
REPO="$(cd "$LIVE/../../.." && pwd)"
BLOCK_A_DIR="$REPO/experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry"

HOME_DIR="$BLOCK_A_DIR/home-$CELL"
LOG="$LIVE/block-a2-$CELL-driver.log"
export DEEPREASON_HOME="$HOME_DIR"

{
  echo "=== block-a2-$CELL start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) home=$HOME_DIR ==="

  SETUP_ARGS=(setup --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 16384 \
    --reasoning none --credential-env OLLAMA_API_KEY)

  if [ "$CELL" = "cross" ]; then
    SETUP_ARGS+=(--seat "conjecture=$BLOCK_A_DIR/coder-profile.yaml")
  fi

  timeout 300 deepreason "${SETUP_ARGS[@]}"
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  # (question, seed) pairs: baseline 2Qx3S always; CROSS also gets 4
  # extra Q1-only seeds (4-7) to size the refusal rate.
  PAIRS=(1,1 1,2 1,3 2,1 2,2 2,3)
  if [ "$CELL" = "cross" ]; then
    PAIRS+=(1,4 1,5 1,6 1,7)
  fi

  for pair in "${PAIRS[@]}"; do
    qidx="${pair%,*}"
    sidx="${pair#*,}"
    QUESTION=$(python3 "$LIVE/block_a2_questions.py" get "$qidx" "$sidx")
    TAG="q${qidx}s${sidx}"
    OUT_PREFIX="$LIVE/block-a2-$CELL-$TAG"

    r0=$SECONDS
    python3 "$LIVE/block_a2_converge.py" "$QUESTION" "$OUT_PREFIX" \
      > "$OUT_PREFIX-converge.json" 2> "$OUT_PREFIX-converge.err"
    echo "converge_rc=$? converge_seconds=$((SECONDS-r0)) tag=$TAG"

    run_id=$(python3 -c "import json;print(json.load(open('$OUT_PREFIX-converge.json')).get('run_id') or '')" 2>/dev/null)
    echo "run_id=$run_id tag=$TAG"
    root="$HOME_DIR/runs/$run_id"
    if [ -n "$run_id" ] && [ -d "$root" ]; then
      python3 "$LIVE/block_a2_audit.py" "$root" "$CELL" "$qidx" "$sidx" "$OUT_PREFIX-converge.json" \
        > "$OUT_PREFIX-audit.json" 2> "$OUT_PREFIX-audit.err"
      echo "audit_rc=$? tag=$TAG"
    else
      echo "audit_skipped=no_run_root tag=$TAG"
    fi
  done

  echo "=== block-a2-$CELL end $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
