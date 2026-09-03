#!/bin/bash
# One M2 pack-budget rung: 2 cycles at a given PACK_TOKEN_BUDGET.
#
#   m2_rung.sh <home-dir> <budget>
#
# THE KNOB IS SET BY `--config <partial YAML>`, NOT BY AN ENVIRONMENT
# VARIABLE. The first version of this script exported
# DEEPREASON_PACK_TOKEN_BUDGET, which reaches nothing: Config carries no env
# reader, so `Config().PACK_TOKEN_BUDGET` stayed 2500 with the variable set to
# 12345. All four rungs would have run at the shipped default and the sweep
# would have reported four identical arms as a flat quality curve -- which is
# also the result the prereg PREDICTS, so it would have looked like a
# confirmation. Checked before launch rather than after; the guard below keeps
# it checkable in every rung's own log.
#
# Each rung needs its own home, and that is forced rather than chosen:
# PACK_TOKEN_BUDGET MOVES the qualification subject digest (measured -- the
# canonical fixture goes 02ee7e09... at the default to 8016fd1f... at 12000),
# so no two rungs can share a cached qualification. Each rung pays one battery
# (~6.5 min measured here, against CLAUDE.md's documented ~14).
set -u
cd /home/user/DeepReason
D=experiments/2026-09-03-change-provenance-history-channel
HOME_DIR="$1"; BUDGET="$2"
CFG="$D/runs/configs/pack-$BUDGET.yaml"
export DEEPREASON_HOME="$PWD/$HOME_DIR"
set -a; . $D/env; set +a
mkdir -p "$DEEPREASON_HOME"
Q="$(cat $D/QUESTION.txt)"

echo "=== M2 rung budget=$BUDGET started $(date -u +%FT%TZ) ==="
echo "--- GUARD: does the run agree the knob is $BUDGET? ---"
SEEN="$(deepreason --config "$CFG" config 2>/dev/null | grep -i '^PACK_TOKEN_BUDGET:' | awk '{print $2}')"
echo "config echo: PACK_TOKEN_BUDGET=$SEEN (requested $BUDGET)"
if [ "$SEEN" != "$BUDGET" ]; then
  echo "RUNG INVALID: the knob did not land. Refusing to spend tokens on an arm that is secretly the control."
  exit 3
fi
echo "--- setup ---"
deepreason --config "$CFG" setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"
echo "--- qualify ---"
deepreason --config "$CFG" qualify --yes; echo "rc=$?"
echo "--- reason, 2 cycles $(date -u +%FT%TZ) ---"
deepreason --config "$CFG" reason --cycles 2 --token-budget 400000 "$Q"; echo "rc=$?"
ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "=== results $(date -u +%FT%TZ) ==="
deepreason results "$ROOT" --json --verify
echo "=== M2 rung budget=$BUDGET finished $(date -u +%FT%TZ) ==="
