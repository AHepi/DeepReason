#!/bin/bash
#   arm.sh <arm>          arm in {A0,A1,A1P,A2,A3}
#
# ONE ARM, DETACHED, ON THE MANAGED PATH. The only difference between an arm
# and an ordinary `deepreason reason` is which conjecturer layout id resolves,
# and that is installed by `rig/sitecustomize.py` at interpreter start from
# DR_ARM. Nothing under src/ moves.
#
# ONE HOME FOR EVERY ARM, and that is not a convenience. Qualification caches
# by subject digest against the HOME (CLAUDE.md, Live runs), so a home per arm
# would re-run the full ~14-minute battery five times over. The layout is
# NEITHER a Config field nor a manifest field (llm/packs.py:761), so every arm
# compiles the SAME run identity from the same question and config -- which is
# why each arm's root must be moved out of the home before the next arm
# launches, or the next launch refuses RUN_ALREADY_STARTED. The move happens
# here, at the END of the arm that produced the root, so a crash never leaves
# the next arm to discover it.
#
# THREE GUARDS, each because its absence has already cost an arm somewhere in
# this tree:
#   exit 4  the credential file is missing or carries no key
#   exit 5  the arm rig did not install (a silent fallback to A0 would report
#           the control's numbers under the treatment's name)
#   exit 6  the arm's brief is byte-identical to A0's AND PREREG.md does not
#           name it as an identical-brief arm
set -u
cd /home/user/DeepReason
D=experiments/2026-09-04-experiment-brief-variation-step1
ARM="${1:?usage: arm.sh <A0|A1|A1P|A2|A3>}"

export DEEPREASON_HOME="$PWD/$D/runs/home-step1"
export PYTHONPATH="$PWD/$D/rig:${PYTHONPATH:-}"
export DR_ARM="$ARM"
mkdir -p "$DEEPREASON_HOME" "$D/roots"

# The key is read from the gitignored file and never printed. `set -a` exports
# it; nothing echoes it, and the shell's xtrace is never on in this script.
[ -s "$D/env" ] || { echo "ARM INVALID: $D/env missing or empty"; exit 4; }
set -a; . "$D/env"; set +a
[ -n "${OLLAMA_API_KEY:-}" ] || { echo "ARM INVALID: no OLLAMA_API_KEY in $D/env"; exit 4; }

Q="$(cat $D/QUESTION.txt)"
echo "=== arm $ARM started $(date -u +%FT%TZ) ==="

# A3's template must exist in the home before the rig loads it. The home is
# shared by every arm, so the file is written by the arm that needs it rather
# than left lying in the directory for arms that do not -- only A3's rig ever
# calls the loader, but a stray file in a shared home is how a control quietly
# becomes a treatment.
if [ "$ARM" = "A3" ]; then
  env -u DR_ARM python -c "
import os, pathlib, sys
sys.path.insert(0, os.environ['PYTHONPATH'].split(':')[0])
import armrig
print('template ->', armrig.write_template(pathlib.Path(os.environ['DEEPREASON_HOME']) / 'seat_plugins'))
" || exit 5
fi

# The arm rig, proved in THIS process before the run spends anything.
python - <<'PY' || exit 5
import os, sys, json
sys.path.insert(0, os.environ["PYTHONPATH"].split(":")[0])
import armrig
receipt = armrig.install()
print("ARM RIG RECEIPT " + json.dumps(receipt, sort_keys=True))
assert receipt["installed"], receipt
PY

echo "--- setup ---"
deepreason setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"
echo "--- qualify (concurrency 2; four at once is what produced the 429 storm) ---"
deepreason qualify --yes --concurrency 2; echo "rc=$?"

echo "--- reason, 4 cycles $(date -u +%FT%TZ) ---"
deepreason reason --cycles 4 --token-budget 600000 "$Q"; echo "rc=$?"

ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "=== results $(date -u +%FT%TZ) ==="
deepreason results "$ROOT" --json --verify

# Move the root out of the home so the next arm's identical run identity is
# free. Never edited, only moved, and moved before anything is committed.
if [ -n "${ROOT:-}" ]; then
  DEST="$D/roots/$ARM-$(basename "$ROOT")"
  mv "$ROOT" "$DEST" && echo "retired root -> $DEST"
fi
echo "=== arm $ARM finished $(date -u +%FT%TZ) ==="
