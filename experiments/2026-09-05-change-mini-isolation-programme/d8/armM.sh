#!/bin/bash
# ARM M launcher. PREREG_D8.md §2. Run detached from the repo root:
#   setsid nohup experiments/2026-09-05-change-mini-isolation-programme/d8/armM.sh \
#       > experiments/2026-09-05-change-mini-isolation-programme/d8/armM.log 2>&1 & disown
set -u
cd /home/user/DeepReason
D=experiments/2026-09-05-change-mini-isolation-programme
export DEEPREASON_HOME="$PWD/$D/runs/home-m"
export DEEPREASON_MINI_FLOW=mini.flow.isolation.v1
set -a; . $D/env; set +a
mkdir -p "$DEEPREASON_HOME"
echo "=== ARM M started $(date -u +%FT%TZ) flow=$DEEPREASON_MINI_FLOW home=$DEEPREASON_HOME ==="
echo "--- setup ---"
deepreason setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"
echo "--- standard input (frozen once; a second freeze is refused) ---"
ls "$D/runs/input-d8/run-input.json" && sha256sum "$D/runs/input-d8/run-input.json"
echo "--- reason: mini.flow.isolation.v1, 3 cycles, 400000 token ceiling $(date -u +%FT%TZ) ---"
python -u $D/d8/armM_driver.py
echo "rc=$?"
ROOT="$(ls -dt $DEEPREASON_HOME/shallow-runs/shallow-* 2>/dev/null | head -1)"
echo "--- deepreason results on the mini root (typed absences expected; not the terminal) ---"
deepreason results "$ROOT"; echo "rc=$?"
echo "=== ARM M finished $(date -u +%FT%TZ) ==="
