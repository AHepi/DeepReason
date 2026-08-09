#!/usr/bin/env bash
# Tier V pilot: sole-model gemma4:31b (no --seat flags -- every role on
# this one profile), representative question tv-m04, per CHECKLIST.md
# step 18 / SPEC.md R13/R14/A5/A1. Modeled on
# experiments/2026-08-08-live-two-seat-ab-s6/s6_run.sh minus its seat
# binding. Context-window/completion-token/reasoning values are
# easy.py's own proven "gemma4_31b" preset (context=131072,
# completion=8192, reasoning=none), not guessed.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

QUESTION_ID="tv-m04"
QUESTION='For positive integer n such that n < 10,000, the number n+2005 has exactly 21 positive factors. What is the sum of all the possible values of n? State your final answer as a single number in your concluding claim.'
CHECKER="$REPO/experiments/tier_v_checkers/tv-m04_checker.py"

export DEEPREASON_HOME="$LIVE/pilot-tier-v"
mkdir -p "$DEEPREASON_HOME"

{
  echo "=== pilot-tier-v start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) question_id=$QUESTION_ID ==="

  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model gemma4:31b --model-revision gemma4:31b --family gemma \
    --context-window-tokens 131072 --maximum-completion-tokens 8192 \
    --reasoning none \
    --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  qrc=$?
  echo "qualify_rc=$qrc qualify_seconds=$((SECONDS-q0))"

  r0=$SECONDS
  timeout 14400 deepreason reason "$QUESTION" --cycles 10 --token-budget 195000 --allow-partial \
    > "$LIVE/tier-v-reason.json" 2> "$LIVE/tier-v-reason.err"
  rrc=$?
  echo "reason_rc=$rrc reason_seconds=$((SECONDS-r0)) tier=full"

  if [ "$rrc" -ne 0 ] && grep -q "QUALIFICATION_TIER_SHALLOW" "$LIVE/tier-v-reason.err"; then
    echo "full-tier reason refused (QUALIFICATION_TIER_SHALLOW) -- retrying --shallow per R15"
    r0=$SECONDS
    timeout 14400 deepreason reason "$QUESTION" --cycles 10 --token-budget 195000 --allow-partial --shallow \
      > "$LIVE/tier-v-reason.json" 2> "$LIVE/tier-v-reason.err"
    rrc=$?
    echo "reason_shallow_rc=$rrc reason_shallow_seconds=$((SECONDS-r0)) tier=shallow"
  fi

  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/tier-v-reason.json'))['run_id'])" 2>/dev/null)
  echo "run_id=$run_id"
  root="$DEEPREASON_HOME/runs/$run_id"

  if [ -n "$run_id" ] && [ -d "$root" ]; then
    python3 "$LIVE/pilot_audit.py" "$root" --checker "$CHECKER" > "$LIVE/tier-v-audit1.json" 2> "$LIVE/tier-v-audit1.err"
    echo "audit1_rc=$?"

    stop_reason=$(python3 -c "import json;print(json.load(open('$LIVE/tier-v-audit1.json')).get('stop_reason'))" 2>/dev/null)
    echo "stop_reason=$stop_reason"
    resumable=$(python3 -c "
import json
resumable = {'budget_exhausted', 'converged'}
d = json.load(open('$LIVE/tier-v-audit1.json'))
print('yes' if d.get('stop_reason') in resumable else 'no')
" 2>/dev/null)
    echo "resumable=$resumable"

    attempt=0
    while [ "$resumable" = "yes" ] && [ "$attempt" -lt 2 ]; do
      attempt=$((attempt+1))
      c0=$SECONDS
      timeout 14400 deepreason --root "$root" continue --budget cycles=2 \
        > "$LIVE/tier-v-continue${attempt}.json" 2> "$LIVE/tier-v-continue${attempt}.err"
      echo "continue${attempt}_rc=$? continue${attempt}_seconds=$((SECONDS-c0))"

      python3 "$LIVE/pilot_audit.py" "$root" --checker "$CHECKER" > "$LIVE/tier-v-audit$((attempt+1)).json" 2> "$LIVE/tier-v-audit$((attempt+1)).err"
      echo "audit$((attempt+1))_rc=$?"
      stop_reason=$(python3 -c "import json;print(json.load(open('$LIVE/tier-v-audit$((attempt+1)).json')).get('stop_reason'))" 2>/dev/null)
      echo "stop_reason=$stop_reason"
      resumable=$(python3 -c "
import json
resumable = {'budget_exhausted', 'converged'}
d = json.load(open('$LIVE/tier-v-audit$((attempt+1)).json'))
print('yes' if d.get('stop_reason') in resumable else 'no')
" 2>/dev/null)
      echo "resumable=$resumable"
    done
  else
    echo "audit_skipped=no_run_root"
  fi

  echo "=== pilot-tier-v end $(date -u +%FT%TZ) ==="
} >> "$LIVE/tier-v-driver.log" 2>&1
