#!/bin/bash
# The live solo road. ONE model in every seat, ONE judge seat, criticism
# school-routed, ARGUMENTATIVE_AUTHORITY=single_family_trial.
#
# What this is for: everything in VERIFY.md is from deterministic stubs. This
# is the one thing a stub cannot show -- that the road survives a real
# provider, a real qualification battery, and a real question.
#
# SOAK: skipped on the operator's explicit instruction, 2026-09-09: "Soak is
# only for when tokens are sparse. I'd rather get results faster with real
# tests." Recorded because CLAUDE.md's ladder rule otherwise requires one.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-09-fix-solo-criticism-authority
export DEEPREASON_HOME="$PWD/$D/runs/home-solo"
set -a; . $D/env; set +a
CFG="$D/runs/config.yaml"
Q='Should a small team building a research tool write its own experiment tracker, or adopt an existing one?'

echo "=== solo road $(date -u +%FT%TZ) ==="

echo "--- GUARD: every knob must land before a battery is spent ---"
for kv in "ADJUDICATION_STATUS_AUTHORITY_ENABLED:true" \
          "ARGUMENTATIVE_AUTHORITY:single_family_trial" \
          "LEGACY_CRITICISM_ENABLED:false" \
          "N_SCHOOLS:2" \
          "SINGLE_JUDGE_SEAT_PERMITTED:true"; do
  k="${kv%%:*}"; want="${kv#*:}"
  got="$(deepreason --config "$CFG" config 2>/dev/null | grep -i "^$k:" | awk '{print $2}')"
  echo "config echo: $k=$got (requested $want)"
  if [ "$got" != "$want" ]; then echo "INVALID: $k did not land; refusing to spend."; exit 3; fi
done

echo "--- embedder warmup ---"
deepreason embedder-warmup; echo "rc=$?"

echo "--- setup $(date -u +%FT%TZ) ---"
mkdir -p "$DEEPREASON_HOME"
deepreason --config "$CFG" setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"

echo "--- qualify (concurrency 2) $(date -u +%FT%TZ) ---"
deepreason --config "$CFG" qualify --yes --concurrency 2; echo "rc=$?"
deepreason --config "$CFG" status --json

echo "--- reason $(date -u +%FT%TZ) ---"
deepreason --config "$CFG" reason "$Q" --cycles 6 --token-budget 400000
echo "rc=$?"

echo "--- results $(date -u +%FT%TZ) ---"
deepreason --config "$CFG" results --json --verify
echo "rc=$?"
echo "=== solo road finished $(date -u +%FT%TZ) ==="
