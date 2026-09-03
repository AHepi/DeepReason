#!/bin/bash
#   arm.sh <home-dir> <arm-label> <none|conjecturer|critic> [source-root]
#
# WHERE THE HISTORY GOES IN, and why it is not where it was.
# `deepreason scratch add` writes into a RUN ROOT, not into a home: called
# against a home with no run yet it fails MANIFEST_FILE_UNAVAILABLE at
# /run-manifest.json. So a treatment arm cannot be pre-seeded before its run
# starts. The first design did exactly that, the injection returned rc=1, and
# the run proceeded anyway -- a treatment arm that was silently the control.
# `deepreason --root <root> scratch add` DOES work (verified rc=0), so the run
# is launched in the background, the root is waited for, and the block is
# injected into it. The block therefore lands during cycle 0 and is available
# to the cycles after it, which is what the earlier cycle-by-cycle design was
# for before `continue` turned out to be refused (PARKED P1).
#
# TWO GUARDS, both because their absence already cost an arm:
#   * a treatment arm with no source root refuses (exit 4);
#   * a treatment arm whose rendered history has NO CONTENT refuses (exit 6).
# An empty section is the failure that is invisible in the numbers: the arm
# runs, costs a full battery and four cycles, and reports a null result that
# looks like evidence that history does not help.
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

HIST=""
if [ "$MODE" != "none" ]; then
  if [ -z "$SRC" ] || [ ! -f "$SRC/log.jsonl" ]; then
    echo "ARM INVALID: mode=$MODE needs a completed source root; got '$SRC'."; exit 4
  fi
  HIST="$DEEPREASON_HOME/history.txt"
  echo "--- render history from $SRC $(date -u +%FT%TZ) ---"
  python $D/render_history.py "$SRC" --mode "$MODE" --out "$HIST" || exit 5
  # GUARD: a section whose every limb is empty is not history.
  if grep -qE "^  \(nothing refuted yet\)" "$HIST" && grep -qE "^  \(no failed attacks yet\)|^  \(no objections recorded yet\)" "$HIST"; then
    echo "ARM INVALID: the rendered history has NO CONTENT --"
    sed -n '1,25p' "$HIST"
    echo "Refusing to spend a battery and four cycles on a treatment arm that is"
    echo "indistinguishable from the control. Fix the source root or the render."
    exit 6
  fi
  echo "--- injected block, verbatim, so the arm is auditable ---"; cat "$HIST"; echo "--- end injected block ---"
fi

echo "--- reason, 4 cycles $(date -u +%FT%TZ) ---"
deepreason reason --cycles 4 --token-budget 600000 "$Q" & REASON_PID=$!

if [ -n "$HIST" ]; then
  for i in $(seq 1 60); do
    ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
    [ -n "$ROOT" ] && [ -f "$ROOT/run-manifest.json" ] && break
    sleep 5
  done
  if [ -n "${ROOT:-}" ] && [ -f "$ROOT/run-manifest.json" ]; then
    echo "--- injecting into $ROOT $(date -u +%FT%TZ) ---"
    deepreason --root "$ROOT" scratch add --file "$HIST" \
      --why-keep-this "prior history on this problem (M1/M3 prototype arm)" --json
    echo "inject-rc=$?"
  else
    echo "INJECT FAILED: no run root appeared within 300s; this arm is NOT a treatment arm."
    kill $REASON_PID 2>/dev/null; exit 7
  fi
fi

wait $REASON_PID; echo "rc=$?"
ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "=== results $(date -u +%FT%TZ) ==="
deepreason results "$ROOT" --json --verify
echo "=== arm $LABEL finished $(date -u +%FT%TZ) ==="
