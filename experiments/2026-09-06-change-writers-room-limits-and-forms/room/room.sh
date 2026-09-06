#!/bin/bash
# The live room run. From the repo root, detached:
#   setsid nohup experiments/2026-09-06-change-writers-room-limits-and-forms/room/room.sh \
#       > experiments/2026-09-06-change-writers-room-limits-and-forms/room/room.log 2>&1 & disown
set -u
cd /home/user/DeepReason
T=experiments/2026-09-06-change-writers-room-limits-and-forms
export DEEPREASON_HOME="$PWD/$T/runs/home-room"
export DEEPREASON_MINI_FLOW=mini.flow.room.v1
set -a; . experiments/2026-09-05-change-mini-isolation-programme/env; set +a
mkdir -p "$DEEPREASON_HOME"
echo "=== room run started $(date -u +%FT%TZ) flow=$DEEPREASON_MINI_FLOW ==="
deepreason setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"; grep -n "model_profile" "$DEEPREASON_HOME/provider.yaml"
python -u $T/room/room_driver.py; echo "rc=$?"
echo "=== room run finished $(date -u +%FT%TZ) ==="
