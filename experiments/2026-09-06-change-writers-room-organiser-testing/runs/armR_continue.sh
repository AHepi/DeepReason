#!/bin/bash
# ARM R, continuation. PREREG Amendment 8: the operator ruled "Resume the run
# with more budget first" rather than judge a run the harness mislabelled.
# The sealed run stopped at cycle 3 of 4 with 495362 of 500000 spent; this adds
# ONE cycle -- the fourth the launch already sealed -- with a token ceiling
# generous enough that the cycle is not cut short again, so the terminal is
# reached by the cycle count rather than by the budget.
#   `--budget cycles=1` is safe under either reading of the flag: one further
#   cycle if it is additional, an immediate clean max_cycles stop if it is a
#   total. Neither exceeds the four cycles the launch sealed.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-06-change-writers-room-organiser-testing
export DEEPREASON_HOME="$PWD/$D/runs/home-r"
set -a; . $D/env; set +a
CFG="$D/runs/config.yaml"
ROOT="$DEEPREASON_HOME/runs/run-c3f3bf10bc57d63e224a9f1c68bf1057"
echo "=== ARM R continue started $(date -u +%FT%TZ) ==="
echo "--- the stop being resumed (typed, from the record) ---"
python -c "import json;d=json.load(open('$ROOT/run-status.json'));print({k:d[k] for k in ('state','stop_reason','cycle','token_spend','token_limit')})"
export DEEPREASON_SEAT_SHELL=conjecturer=seat.conjecturer.organiser-v1
export DEEPREASON_ROLE_PROMPT_TEMPLATE=role-prompt.organiser-v1
echo "selectors: DEEPREASON_SEAT_SHELL=$DEEPREASON_SEAT_SHELL DEEPREASON_ROLE_PROMPT_TEMPLATE=$DEEPREASON_ROLE_PROMPT_TEMPLATE"
echo "--- continue, 1 further cycle, 1200000 token ceiling $(date -u +%FT%TZ) ---"
deepreason --config "$CFG" --root "$ROOT" continue --budget cycles=1 --token-budget 1200000; echo "rc=$?"
echo "--- results (typed) ---"
deepreason results "$ROOT" --json --verify | tee $D/runs/armR/ARMR_RESULTS.json > /dev/null; echo "rc=$?"
python -c "import json;d=json.load(open('$ROOT/run-status.json'));print({k:d[k] for k in ('state','stop_reason','cycle','token_spend','token_limit')})"
python $D/tools/compose_result.py "$ROOT" --out $D/runs/armR/COMPOSED.txt --json $D/runs/armR/COMPOSED.json; echo "compose-rc=$?"
echo "--- did the organiser render? (the section plans name the plugin) ---"
grep -l 'dr.output-contract.organiser' "$ROOT"/objects/*section-plan*/*.json 2>/dev/null | wc -l
echo "=== ARM R continue finished $(date -u +%FT%TZ) ==="
