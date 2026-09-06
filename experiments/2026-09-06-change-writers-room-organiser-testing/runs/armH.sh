#!/bin/bash
# ARM H: the full harness alone, default shells, no attachment. PREREG §2.
# Same model, same config, same cycles and token budget as ARM R; the only
# things absent are the room and the organiser pairing.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-06-change-writers-room-organiser-testing
export DEEPREASON_HOME="$PWD/$D/runs/home-h"
set -a; . $D/env; set +a
CFG="$D/runs/config.yaml"
Q="$(python -c "import json;print(json.load(open('experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8/run-input.json'))['problem']['description'])")"
echo "=== ARM H started $(date -u +%FT%TZ) home=$DEEPREASON_HOME ==="
echo "question sha256: $(printf '%s' "$Q" | sha256sum | cut -c1-64)"
unset DEEPREASON_SEAT_SHELL DEEPREASON_ROLE_PROMPT_TEMPLATE
echo "--- reason, 4 cycles, 800000 token ceiling $(date -u +%FT%TZ) ---"
deepreason --config "$CFG" reason --cycles 4 --token-budget 800000 "$Q"; echo "rc=$?"
ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "root=$ROOT"
echo "--- results (typed) ---"
deepreason results "$ROOT" --json --verify | tee $D/runs/armH/ARMH_RESULTS.json; echo "rc=$?"
python $D/tools/compose_result.py "$ROOT" --out $D/runs/armH/COMPOSED.txt --json $D/runs/armH/COMPOSED.json; echo "compose-rc=$?"
echo "=== ARM H finished $(date -u +%FT%TZ) ==="
