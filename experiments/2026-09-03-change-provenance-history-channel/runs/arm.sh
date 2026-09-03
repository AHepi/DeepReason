#!/bin/bash
# One M1/M3 arm: 4 cycles in ONE `reason` call.
#
#   arm.sh <home-dir> <arm-label> <none|conjecturer|critic> [source-root]
#
# WHY NOT CYCLE-BY-CYCLE. The first version ran `reason --cycles 1` and then
# `continue --budget cycles=1` three times, injecting fresh history between
# each. It does not work: the 1-cycle run terminates `budget_exhausted` with
# `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` (2 outstanding work items),
# and every subsequent continue is refused `CONTINUE_TYPED_STOP_REQUIRED`.
# Measured on M1-H0 run-292f964edb58e58ef0e7d957f29bac55: cycle 1 completed
# with 18 admitted conjectures, then three continues returned rc=1 and the arm
# was a 1-cycle arm wearing a 4-cycle label. Parked as a defect (PARKED.md);
# NOT fixed here, because a defect found mid-change is parked rather than
# fixed, and because the harness is not what this tranche is measuring.
#
# The replacement is also closer to the window instruction's own words: H1 is
# "pack plus a prototype history section rendered OFFLINE from the record".
# The record is a COMPLETED control root, not the arm's own in-flight cycles.
# So a treatment arm seeds its scratchpad ONCE, before the run, from the
# control arm's finished record, and then runs the same single `--cycles 4`
# call the control ran. The two arms now differ in exactly one thing.
#
# Cycle 0 is no longer identical across arms -- the treatment sees history
# from the first cycle onward. That is a change from the earlier design and it
# makes the arms MORE comparable, not less: both are one uninterrupted 4-cycle
# run, and the injected material is fixed for the whole arm instead of growing
# under it.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-03-change-provenance-history-channel
HOME_DIR="$1"; LABEL="$2"; MODE="$3"; SRC="${4:-}"
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

if [ "$MODE" != "none" ]; then
  if [ -z "$SRC" ] || [ ! -f "$SRC/log.jsonl" ]; then
    echo "ARM INVALID: mode=$MODE needs a completed source root; got '$SRC'."
    echo "Refusing to run a treatment arm with nothing injected -- it would be"
    echo "the control wearing a treatment label, and would read as a null result."
    exit 4
  fi
  echo "--- render history from $SRC $(date -u +%FT%TZ) ---"
  python $D/render_history.py "$SRC" --mode "$MODE" \
    --out "$DEEPREASON_HOME/history.txt" || exit 5
  echo "--- injected block, verbatim, so the arm is auditable ---"
  cat "$DEEPREASON_HOME/history.txt"
  echo "--- end injected block ---"
  deepreason scratch add --file "$DEEPREASON_HOME/history.txt" \
    --why-keep-this "prior history on this problem (M1/M3 prototype arm)" --json
  echo "inject-rc=$?"
fi

echo "--- reason, 4 cycles $(date -u +%FT%TZ) ---"
deepreason reason --cycles 4 --token-budget 600000 "$Q"; echo "rc=$?"
ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "=== results $(date -u +%FT%TZ) ==="
deepreason results "$ROOT" --json --verify
echo "=== arm $LABEL finished $(date -u +%FT%TZ) ==="
