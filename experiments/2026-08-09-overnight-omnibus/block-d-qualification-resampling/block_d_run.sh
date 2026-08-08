#!/usr/bin/env bash
# Block D ladder: one qualification-only sample at a perturbed cap
# (fresh subject digest per PREREG.yaml's documented +0/+1/+2/+3
# perturbation). setup + qualify only -- no `reason` call.
#
# Usage: ./block_d_run.sh CAP_POINT SAMPLE_IDX   (CAP_POINT in {8192,16384}, SAMPLE_IDX in {0,1,2,3})
set -u
CAP_POINT="${1:?usage: block_d_run.sh CAP_POINT SAMPLE_IDX}"
SAMPLE_IDX="${2:?usage: block_d_run.sh CAP_POINT SAMPLE_IDX}"
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../env"; set +a
REPO="$(cd "$LIVE/../../.." && pwd)"

PERTURBED_CAP=$((CAP_POINT + SAMPLE_IDX))
HOME_DIR="$LIVE/home-${CAP_POINT}-${SAMPLE_IDX}"
LOG="$LIVE/block-d-${CAP_POINT}-${SAMPLE_IDX}-driver.log"
mkdir -p "$HOME_DIR"
export DEEPREASON_HOME="$HOME_DIR"

{
  echo "=== block-d-$CAP_POINT-$SAMPLE_IDX start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) perturbed_cap=$PERTURBED_CAP ==="

  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens "$PERTURBED_CAP" \
    --reasoning none --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3 \
    > "$LIVE/block-d-${CAP_POINT}-${SAMPLE_IDX}-qualify.json" 2> "$LIVE/block-d-${CAP_POINT}-${SAMPLE_IDX}-qualify.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  python3 "$LIVE/block_d_audit.py" "$HOME_DIR" "$LIVE/block-d-${CAP_POINT}-${SAMPLE_IDX}-qualify.json" "$CAP_POINT" "$SAMPLE_IDX" \
    > "$LIVE/block-d-${CAP_POINT}-${SAMPLE_IDX}-audit.json" 2> "$LIVE/block-d-${CAP_POINT}-${SAMPLE_IDX}-audit.err"
  echo "audit_rc=$?"

  echo "=== block-d-$CAP_POINT-$SAMPLE_IDX end $(date -u +%FT%TZ) ==="
} >> "$LOG" 2>&1
