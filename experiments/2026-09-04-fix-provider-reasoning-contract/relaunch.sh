#!/bin/bash
# GOAL.md clause 3: does a run relaunched from the committed launch config
# reach its first seat result?
#
# The provider profile below is the committed launch config's own, field for
# field, from
# experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/provider.yaml
# -- solo qwen3.5:397b, `--reasoning none`, 131072 window, 8192 completion cap.
# `reasoning none` is the whole point: it is the value the alarm said the
# provider would refuse.
#
# A FRESH home, not the committed one. Run identity is deterministic and the
# committed root is evidence: reusing that home would either collide
# (RUN_ALREADY_STARTED) or invite editing a committed root, which is forbidden.
# A fresh home also means qualification runs its full battery rather than
# hitting the cache, which is the point -- the battery is itself ~1160 live
# seat calls carrying this reasoning value.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-04-fix-provider-reasoning-contract
export DEEPREASON_HOME="$PWD/$D/relaunch-home"
set -a; . $D/env; set +a
mkdir -p "$DEEPREASON_HOME"

echo "=== embedder warmup $(date -u +%FT%TZ) ==="
deepreason embedder-warmup; echo "rc=$?"

echo "=== setup $(date -u +%FT%TZ) ==="
deepreason setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"

echo "=== qualify $(date -u +%FT%TZ) ==="
deepreason qualify --yes; echo "rc=$?"

echo "=== status $(date -u +%FT%TZ) ==="
deepreason status --json

echo "=== reason $(date -u +%FT%TZ) ==="
deepreason reason "Does a bounded harness produce better surviving conjectures than one model call?" \
  --cycles 1 --token-budget 120000
echo "rc=$?"

echo "=== results $(date -u +%FT%TZ) ==="
deepreason results "$DEEPREASON_HOME" --json
echo "=== finished $(date -u +%FT%TZ) ==="
