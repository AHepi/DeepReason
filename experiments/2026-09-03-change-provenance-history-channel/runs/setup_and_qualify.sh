#!/bin/bash
# Shared setup + qualification for every arm that runs at the DEFAULT
# PACK_TOKEN_BUDGET (M1 H0/H1, M3 C0/C1, and M2's 2500 rung).
#
# ONE home on purpose. Qualification caches by subject digest, so arms sharing
# a profile and a budget share one ~14-minute battery instead of paying it
# each. Run identity is deterministic, so the root is RENAMED between arms
# rather than the home being duplicated -- CLAUDE.md's documented retirement
# procedure, which is also what frees the run id for the next arm.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-03-change-provenance-history-channel
export DEEPREASON_HOME="$PWD/$D/runs/home-default"
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
echo "=== finished $(date -u +%FT%TZ) ==="
