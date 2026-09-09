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
# THE SOAK OWNS THE HOME, so the caller cannot choose it and the arm must
# follow. `cycle_soak.py` resolves its working directory from `--out` (else a
# fresh temp dir) and sets DEEPREASON_HOME to `<workdir>/home` inside its own
# `main()` -- which runs AFTER `sitecustomize` has already installed the arm at
# interpreter start. So A3, whose rig reads the operator plugin directory out
# of DEEPREASON_HOME before `main()` exists, looks in the caller's home while
# the soak looks in its own.
#
# SOAK.md records this as the second of A3's two 2026-09-04 failures and names
# the fix -- "`--out` plus an exported home, so both agree before the
# interpreter starts" -- and the script did not carry it, so the committed gate
# could not reproduce the green A3 that document reports. Re-running it on
# 2026-09-09 reproduced the refusal in two seconds (`ARM RIG REFUSED: arm A3
# needs 'op.neighbourhood.v1' ... loaded=[]`). The fix is carried here now:
# one workdir per arm, the home derived from it exactly as the soak derives it,
# exported before the interpreter starts, and the template written into that
# same home.
for ARM in A1 A1P A2 A3; do
  export DR_ARM="$ARM"
  WORKDIR="$PWD/$D/soak/work-$ARM"
  rm -rf "$WORKDIR"
  export DEEPREASON_HOME="$WORKDIR/home"
  mkdir -p "$DEEPREASON_HOME"
  if [ "$ARM" = "A3" ]; then
    env -u DR_ARM python -c "
import sys, pathlib, os
sys.path.insert(0, os.environ['PYTHONPATH'].split(':')[0])
import armrig
print('template ->', armrig.write_template(pathlib.Path(os.environ['DEEPREASON_HOME']) / 'seat_plugins'))
"
  fi
  echo "### soak $ARM start $(date -u +%FT%TZ)"
  python -u scripts/cycle_soak.py --case reach-rich --out "$WORKDIR" --keep \
    > "$D/soak/$ARM.log" 2>&1
  echo "### soak $ARM exit=$? $(date -u +%FT%TZ)"
done
