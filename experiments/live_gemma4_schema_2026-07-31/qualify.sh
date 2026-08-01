#!/usr/bin/env bash
# Qualification battery for gemma4:31b, run to test the universal
# prose-into-schema sweep against a model outside the glm/gpt-oss families.
#
# The operator asked for "Gemma 4 12B"; the provider offers only gemma4:31b.
#
# DEEPREASON_HOME is deliberately fresh and never reused. The qualification
# subject digest covers the manifest, pair inventory and provider profile but
# NOT the rendered schema bytes, so a home carrying a cached bundle would hit
# and report pre-sweep behaviour. A clean home is the only honest measurement.
#
# Profile values match the glm-5.2 and gpt-oss:20b profiles exactly, so the
# model is the only variable.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../live_research_2026-07-29/env"; set +a
export DEEPREASON_HOME="$LIVE/home"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
LABEL="${1:-run}"
{
  echo "=== gemma4 battery $LABEL start $(date -u +%FT%TZ) ==="
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model gemma4:31b --model-revision gemma4-31b --family gemma \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --credential-env OLLAMA_API_KEY --reasoning none
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 6000 deepreason qualify --yes --json --concurrency 4 --attached-evidence \
    > "$LIVE/qual-$LABEL.json" 2> "$LIVE/qual-$LABEL.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  echo "=== gemma4 battery $LABEL end $(date -u +%FT%TZ) ==="
} >> "$LIVE/battery.log" 2>&1
