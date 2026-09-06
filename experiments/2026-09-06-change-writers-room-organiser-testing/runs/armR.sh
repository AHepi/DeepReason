#!/bin/bash
# ARM R: the full harness with the room attached and the organiser seat.
# PREREG §3. Identical to ARM H except: the three attachment files bound as
# the run's evidence, the organiser shell and wording selected for the
# conjecturer, and the evidence-blind shell for the critic. THE THREE FILES
# BY NAME, never the directory: `--attach <dir>` admits every file under it,
# and attachment/ also holds CONVERSION.json and ATTACHMENT.sha256
# (proof/DRY_ATTACH.txt measured 5 sources / 105 blocks for the directory
# form against 3 / 94 for the files).
set -u
cd /home/user/DeepReason
D=experiments/2026-09-06-change-writers-room-organiser-testing
export DEEPREASON_HOME="$PWD/$D/runs/home-r"
set -a; . $D/env; set +a
CFG="$D/runs/config.yaml"
A="$D/attachment"
Q="$(python -c "import json;print(json.load(open('experiments/2026-09-05-change-mini-isolation-programme/runs/input-d8/run-input.json'))['problem']['description'])")"
echo "=== ARM R started $(date -u +%FT%TZ) home=$DEEPREASON_HOME ==="
echo "question sha256: $(printf '%s' "$Q" | sha256sum | cut -c1-64)"
echo "--- the attachment, by digest (bytes are committed under $A) ---"
(cd $A && sha256sum -c ATTACHMENT.sha256) || { echo "ARM INVALID: attachment digests do not match"; exit 6; }
export DEEPREASON_SEAT_SHELL=conjecturer=seat.conjecturer.organiser-v1,argumentative_critic=seat.critic.evidence-blind-v1
export DEEPREASON_ROLE_PROMPT_TEMPLATE=role-prompt.organiser-v1
echo "selectors: DEEPREASON_SEAT_SHELL=$DEEPREASON_SEAT_SHELL DEEPREASON_ROLE_PROMPT_TEMPLATE=$DEEPREASON_ROLE_PROMPT_TEMPLATE"
echo "--- reason, 4 cycles, 800000 token ceiling, attached $(date -u +%FT%TZ) ---"
deepreason --config "$CFG" reason --cycles 4 --token-budget 500000 \
  --attach "$A/01-conjectures.txt" --attach "$A/02-proposals.txt" --attach "$A/03-objections.txt" "$Q"; echo "rc=$?"
ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "root=$ROOT"
echo "--- results (typed) ---"
deepreason results "$ROOT" --json --verify | tee $D/runs/armR/ARMR_RESULTS.json; echo "rc=$?"
python $D/tools/compose_result.py "$ROOT" --out $D/runs/armR/COMPOSED.txt --json $D/runs/armR/COMPOSED.json; echo "compose-rc=$?"
echo "--- did the organiser render? (the section plans name the plugin) ---"
grep -l 'dr.output-contract.organiser' "$ROOT"/objects/*section-plan*/*.json 2>/dev/null | wc -l
echo "=== ARM R finished $(date -u +%FT%TZ) ==="
