#!/bin/bash
# One M1/M3 arm: 4 cycles, driven ONE CYCLE AT A TIME.
#
#   arm.sh <home-dir> <arm-label> <none|conjecturer|critic>
#
# Both arms of a pair use the SAME 1 + continue x3 structure, so the only
# difference between H0 and H1 (or C0 and C1) is whether a history block is
# injected between cycles. Running the control as a single `--cycles 4` and
# the treatment as four steps would have confounded the injection with the
# launch path.
#
# History cannot exist before cycle 0 produces some, so cycle 0 is identical
# in both arms by construction and the injection can only affect cycles 1-3.
# That is a property of the design, not a defect, and RESULTS.md states it.
#
# Each arm gets its OWN home. That costs one qualification battery per arm and
# buys two things a shared home cannot: the deterministic run id is free
# without renaming, and the advisory scratchpad starts EMPTY, so a block
# injected for a treatment arm cannot reach its own control.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-03-change-provenance-history-channel
HOME_DIR="$1"; LABEL="$2"; MODE="$3"
export DEEPREASON_HOME="$PWD/$HOME_DIR"
set -a; . $D/env; set +a
mkdir -p "$DEEPREASON_HOME"
Q="$(cat $D/QUESTION.txt)"

echo "=== arm $LABEL (mode=$MODE) started $(date -u +%FT%TZ) ==="
echo "--- setup ---"
deepreason setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"
echo "--- qualify ---"
deepreason qualify --yes; echo "rc=$?"

echo "--- cycle 1 $(date -u +%FT%TZ) ---"
deepreason reason --cycles 1 --token-budget 400000 "$Q"; echo "rc=$?"

for c in 2 3 4; do
  ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
  if [ -z "$ROOT" ]; then echo "NO ROOT after cycle $((c-1)); stopping"; break; fi
  echo "--- root: $ROOT ---"
  if [ "$MODE" != "none" ]; then
    echo "--- render+inject history before cycle $c $(date -u +%FT%TZ) ---"
    python $D/render_history.py "$ROOT" --mode "$MODE" \
      --out "$DEEPREASON_HOME/history-cycle$c.txt"
    # The injected block is kept OUTSIDE the root: it is an input to the next
    # cycle, not a record of the last one, and writing into a root would be
    # editing evidence.
    deepreason scratch add --file "$DEEPREASON_HOME/history-cycle$c.txt" \
      --why-keep-this "prior history on this problem (M1/M3 prototype arm)" --json
    echo "inject-rc=$?"
  fi
  echo "--- cycle $c $(date -u +%FT%TZ) ---"
  deepreason --root "$ROOT" continue --budget cycles=1 --token-budget 400000
  echo "rc=$?"
done

ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "=== results $(date -u +%FT%TZ) ==="
deepreason results "$ROOT" --json --verify
echo "=== arm $LABEL finished $(date -u +%FT%TZ) ==="
