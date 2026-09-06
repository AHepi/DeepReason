#!/bin/bash
# The whole plan, in PREREG §10's order, detached:
#   setsid nohup experiments/2026-09-06-change-writers-room-organiser-testing/runs/chain.sh \
#     > experiments/2026-09-06-change-writers-room-organiser-testing/runs/chain.log 2>&1 & disown
# Soak first (offline; the launch configuration's SHAPE is `epoch3`: solo,
# attached evidence enabled — no committed case drives qwen3.5), then the
# attached-evidence home's battery, then ARM R, then ARM 0R (the bare model
# with the room pasted in). ARM H is DEFERRED (PREREG Amendment 3): its
# setup and arm lines were removed here, not from the tranche. Refuses to
# launch on a red soak or a missing key. The snapshot loop is armed alongside.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-06-change-writers-room-organiser-testing
[ -f $D/env ] || { echo "REFUSED: no $D/env (OLLAMA_API_KEY=...). Recreate it from the handover; chmod 600."; exit 8; }
git check-ignore -q $D/env || { echo "REFUSED: $D/env is not gitignored"; exit 9; }
mkdir -p $D/runs/armR $D/runs/arm0R
echo "=== chain started $(date -u +%FT%TZ) head=$(git rev-parse --short HEAD) ==="
echo "--- soak: cycle_soak --case epoch3 $(date -u +%FT%TZ) ---"
python -u scripts/cycle_soak.py --case epoch3 > $D/runs/soak.log 2>&1; SOAK=$?
echo "soak rc=$SOAK"; tail -5 $D/runs/soak.log
[ "$SOAK" -eq 0 ] || { echo "REFUSED: soak red; no live launch (CLAUDE.md, Live runs)."; exit 7; }
setsid nohup $D/runs/snapshot.sh > $D/runs/snapshot.log 2>&1 & disown
$D/runs/setup_and_qualify.sh $D/runs/home-r attached 2>&1 | tee $D/runs/armR/setup.log
$D/runs/armR.sh 2>&1 | tee $D/runs/armR/armR.log
$D/runs/arm0R.sh 2>&1 | tee $D/runs/arm0R/arm0R.log
touch $D/runs/STOP_SNAPSHOT
echo "=== chain finished $(date -u +%FT%TZ); next: tools/judge_organiser.py harvest | score | reveal, then tools/analyse_organiser.py ==="
