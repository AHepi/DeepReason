#!/bin/bash
#   resume.sh <arm>
#
# The container restarts roughly every two hours and an arm takes thirty to
# forty-five minutes, so across six arms a mid-arm kill is expected rather
# than exceptional. The operator's instruction is explicit: CONTINUE a killed
# run, never relaunch it. Relaunching would refuse RUN_ALREADY_STARTED anyway,
# and retiring the root to get past that would throw away the epistemic state
# the run had already paid for.
#
# `deepreason continue` needs a budget, and the budget it needs is what is
# LEFT. The original arm asks for 4 cycles and 600,000 tokens, so this reads
# what the root has already spent from its own typed status and asks for the
# remainder -- never a fresh 4 and 600,000, which would let a resumed arm
# outspend an uninterrupted one and make the spend table meaningless.
#
# It also refuses to resume a run that is not resumable. A record that fails
# replay validation is REFUSED continuation by design (the 2026-08-29 law:
# "I don't want a jailbroken run to be continuable"), and a run that reached a
# clean terminal is finished, not stalled.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-04-experiment-brief-variation-step1
ARM="${1:?usage: resume.sh <A0|A1|A1P|A2|A3>}"

export DEEPREASON_HOME="$PWD/$D/runs/home-step1"
export PYTHONPATH="$PWD/$D/rig:${PYTHONPATH:-}"
export DR_ARM="$ARM"
[ -s "$D/env" ] || { echo "RESUME INVALID: $D/env missing"; exit 4; }
set -a; . "$D/env"; set +a

ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
[ -n "${ROOT:-}" ] || { echo "RESUME INVALID: no run root in the home"; exit 4; }
echo "=== resume $ARM into $ROOT $(date -u +%FT%TZ) ==="

read -r CYCLES TOKENS STATE < <(python - "$ROOT" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.loads((root / "run-status.json").read_text())

def find(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            got = find(value, key)
            if got is not None:
                return got
    elif isinstance(node, list):
        for item in node:
            got = find(item, key)
            if got is not None:
                return got
    return None

# The key names this script was written against are NOT the ones this
# version's run-status.json carries: `cycles_completed`, `metered_tokens`
# and `logged_tokens_this_run` are all absent, and `cycle` / `token_spend`
# are what the record actually writes. Measured on arm A0's own root,
# 2026-09-09: the old reading returned "4 cycles left, 600000 tokens left"
# for a run that had already completed 4 cycles and spent 417,053 -- a
# resumed arm would have been granted a full fresh budget, which is the one
# thing this script's own header forbids.
#
# So the record's own names are read FIRST, the old ones stay as fallbacks,
# and a status that answers neither REFUSES rather than defaulting: a silent
# full budget is the failure, not the missing key.
done = find(status, "cycle")
if done is None:
    done = find(status, "cycles_completed")
spent = find(status, "token_spend")
if spent is None:
    spent = find(status, "metered_tokens") or find(status, "logged_tokens_this_run")
state = find(status, "state") or "unknown"
if done is None or spent is None:
    print("REFUSE REFUSE", state)
    raise SystemExit(0)
print(max(0, 4 - int(done)), max(0, 600000 - int(spent)), state)
PY
)
echo "already spent: state=$STATE  cycles left=$CYCLES  tokens left=$TOKENS"
if [ "$CYCLES" = "REFUSE" ]; then
  echo "RESUME INVALID: this root's run-status.json carries neither the"
  echo "record's cycle/token_spend nor the older names, so what is LEFT of"
  echo "the budget cannot be read. Resuming on a guessed budget would let a"
  echo "resumed arm outspend an uninterrupted one; read the root by hand."
  exit 4
fi
if [ "$CYCLES" -le 0 ] || [ "$TOKENS" -le 0 ]; then
  echo "nothing left to resume; this arm is budget-complete."
  exit 0
fi

echo "--- verify before resuming (a record that fails replay is REFUSED) ---"
deepreason results "$ROOT" --json --verify | tail -20

deepreason continue --budget "cycles=$CYCLES" --token-budget "$TOKENS"
echo "rc=$?"
echo "=== resume $ARM finished $(date -u +%FT%TZ) ==="
