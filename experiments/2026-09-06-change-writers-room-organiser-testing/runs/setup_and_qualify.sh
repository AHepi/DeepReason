#!/bin/bash
# Setup + qualification for ONE home. PREREG §0/§2/§3.
#   setup_and_qualify.sh <home-dir> <attached|plain>
# `attached` qualifies the attached-evidence subject that `reason --attach`
# runs bind (the qualify opt-in must match the reason opt-in: CLAUDE.md,
# "Live runs"); `plain` qualifies the question-only subject. One home per
# arm, because PACK_TOKEN_BUDGET in runs/config.yaml moves the subject digest
# and the two arms' subjects differ in the attached-evidence envelope anyway.
# --concurrency 2 on qualification: the history tranche's 429 storm (its
# PARKED P3/P4) was five arms at the default 4.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-06-change-writers-room-organiser-testing
HOME_DIR="$1"; MODE="$2"
export DEEPREASON_HOME="$PWD/$HOME_DIR"
set -a; . $D/env; set +a
mkdir -p "$DEEPREASON_HOME"
CFG="$D/runs/config.yaml"
echo "=== setup+qualify home=$HOME_DIR mode=$MODE $(date -u +%FT%TZ) ==="
echo "--- GUARD: the knob must land (m2_rung.sh's lesson: an env var reaches nothing) ---"
SEEN="$(deepreason --config "$CFG" config 2>/dev/null | grep -i '^PACK_TOKEN_BUDGET:' | awk '{print $2}')"
echo "config echo: PACK_TOKEN_BUDGET=$SEEN (requested 24000)"
if [ "$SEEN" != "24000" ]; then echo "INVALID: the knob did not land; refusing to spend a battery."; exit 3; fi
echo "--- embedder warmup ---"
deepreason embedder-warmup; echo "rc=$?"
echo "--- setup ---"
deepreason --config "$CFG" setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"
echo "--- qualify ($MODE subject, concurrency 2) $(date -u +%FT%TZ) ---"
if [ "$MODE" = "attached" ]; then
  deepreason --config "$CFG" qualify --yes --attached-evidence --concurrency 2; echo "rc=$?"
else
  deepreason --config "$CFG" qualify --yes --concurrency 2; echo "rc=$?"
fi
deepreason --config "$CFG" status --json
echo "=== setup+qualify finished $(date -u +%FT%TZ) ==="
