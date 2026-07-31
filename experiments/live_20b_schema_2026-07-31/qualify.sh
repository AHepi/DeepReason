#!/usr/bin/env bash
# Qualification battery for gpt-oss:20b with thinking off, used to test the
# universal prose-into-schema rule on a small model. Profile values match the
# glm-5.2 profile exactly so the model is the only variable.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/../live_research_2026-07-29/env"; set +a
export DEEPREASON_HOME="$LIVE/home"
export DEEPREASON_RESEARCH_ALLOWLIST="en.wikipedia.org"
export DEEPREASON_SIMULATION_RUNNER="contained"
export DEEPREASON_CONFIG_REFEREE="2"
LABEL="${1:-run}"
{
  echo "=== 20b battery $LABEL start $(date -u +%FT%TZ) ==="
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model gpt-oss:20b --model-revision gpt-oss-20b --family gpt-oss \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --credential-env OLLAMA_API_KEY --reasoning none
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 6000 deepreason qualify --yes --json --concurrency 4 --attached-evidence \
    > "$LIVE/qual-$LABEL.json" 2> "$LIVE/qual-$LABEL.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  echo "=== 20b battery $LABEL end $(date -u +%FT%TZ) ==="
} >> "$LIVE/battery.log" 2>&1
