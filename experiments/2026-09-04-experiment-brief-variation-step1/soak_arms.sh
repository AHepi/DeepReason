#!/bin/bash
# R20 — a green soak on the EXACT launch configuration, per arm.
#
# `reach-rich` is the committed case whose shape is closest to these arms: a
# SOLO model across the canonical roles with attached evidence disabled, which
# is what `deepreason reason` compiles here. The soak drives
# TextRunApplicationService -- the one run path -- for 8 cycles against the
# deterministic stub, so what it proves is that the arm's LAYOUT survives a
# deep managed run, which is the only thing the arms change.
#
# One soak per arm, because a layout that resolves at cycle 0 can still refuse
# at cycle 6 when the section it names first has content to render.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-04-experiment-brief-variation-step1
export PYTHONPATH="$PWD/$D/rig:${PYTHONPATH:-}"
for ARM in A1 A1P A2 A3; do
  export DR_ARM="$ARM"
  export DEEPREASON_HOME="$PWD/$D/soak/home-$ARM"
  mkdir -p "$DEEPREASON_HOME"
  if [ "$ARM" = "A3" ]; then
    python -c "
import sys, pathlib, os
sys.path.insert(0, os.environ['PYTHONPATH'].split(':')[0])
import armrig
print('template ->', armrig.write_template(pathlib.Path(os.environ['DEEPREASON_HOME']) / 'seat_plugins'))
"
  fi
  echo "### soak $ARM start $(date -u +%FT%TZ)"
  python -u scripts/cycle_soak.py --case reach-rich > "$D/soak/$ARM.log" 2>&1
  echo "### soak $ARM exit=$? $(date -u +%FT%TZ)"
done
