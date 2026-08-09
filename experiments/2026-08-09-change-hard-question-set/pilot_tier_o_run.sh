#!/usr/bin/env bash
# Tier O pilot: sole-model gemma4:31b (no --seat flags), representative
# question to-01 (Collatz conjecture), per CHECKLIST.md step 21 /
# SPEC.md R13/R14/A5/A1. Same shape as pilot_tier_v_run.sh; no --checker
# is passed to pilot_audit.py since Tier O is never scored for
# correctness (R10) -- the hygiene classification is applied by hand
# against the run's final accepted claims per PREREG.md, in step 22.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

QUESTION_ID="to-01"
QUESTION='Collatz conjecture: start from any positive integer n. If n is even, divide it by 2; if n is odd, replace it with 3n+1. Repeating this, does every starting value eventually reach 1? State clearly whether you consider this settled, and if not, what would be needed to settle it.'

export DEEPREASON_HOME="$LIVE/pilot-tier-o"
mkdir -p "$DEEPREASON_HOME"

{
  echo "=== pilot-tier-o start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) question_id=$QUESTION_ID ==="

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
    > "$LIVE/tier-o-reason.json" 2> "$LIVE/tier-o-reason.err"
  rrc=$?
  echo "reason_rc=$rrc reason_seconds=$((SECONDS-r0)) tier=full"

  if [ "$rrc" -ne 0 ] && grep -q "QUALIFICATION_TIER_SHALLOW" "$LIVE/tier-o-reason.err"; then
    echo "full-tier reason refused (QUALIFICATION_TIER_SHALLOW) -- retrying --shallow per R15"
    r0=$SECONDS
    timeout 14400 deepreason reason "$QUESTION" --cycles 10 --token-budget 195000 --allow-partial --shallow \
      > "$LIVE/tier-o-reason.json" 2> "$LIVE/tier-o-reason.err"
    rrc=$?
    echo "reason_shallow_rc=$rrc reason_shallow_seconds=$((SECONDS-r0)) tier=shallow"
  fi

  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/tier-o-reason.json'))['run_id'])" 2>/dev/null)
  echo "run_id=$run_id"
  root="$DEEPREASON_HOME/runs/$run_id"

  if [ -n "$run_id" ] && [ -d "$root" ]; then
    python3 "$LIVE/pilot_audit.py" "$root" > "$LIVE/tier-o-audit1.json" 2> "$LIVE/tier-o-audit1.err"
    echo "audit1_rc=$?"

    stop_reason=$(python3 -c "import json;print(json.load(open('$LIVE/tier-o-audit1.json')).get('stop_reason'))" 2>/dev/null)
    echo "stop_reason=$stop_reason"
    resumable=$(python3 -c "
import json
resumable = {'budget_exhausted', 'converged'}
d = json.load(open('$LIVE/tier-o-audit1.json'))
print('yes' if d.get('stop_reason') in resumable else 'no')
" 2>/dev/null)
    echo "resumable=$resumable"

    attempt=0
    while [ "$resumable" = "yes" ] && [ "$attempt" -lt 2 ]; do
      attempt=$((attempt+1))
      c0=$SECONDS
      timeout 14400 deepreason --root "$root" continue --budget cycles=2 \
        > "$LIVE/tier-o-continue${attempt}.json" 2> "$LIVE/tier-o-continue${attempt}.err"
      echo "continue${attempt}_rc=$? continue${attempt}_seconds=$((SECONDS-c0))"

      python3 "$LIVE/pilot_audit.py" "$root" > "$LIVE/tier-o-audit$((attempt+1)).json" 2> "$LIVE/tier-o-audit$((attempt+1)).err"
      echo "audit$((attempt+1))_rc=$?"
      stop_reason=$(python3 -c "import json;print(json.load(open('$LIVE/tier-o-audit$((attempt+1)).json')).get('stop_reason'))" 2>/dev/null)
      echo "stop_reason=$stop_reason"
      resumable=$(python3 -c "
import json
resumable = {'budget_exhausted', 'converged'}
d = json.load(open('$LIVE/tier-o-audit$((attempt+1)).json'))
print('yes' if d.get('stop_reason') in resumable else 'no')
" 2>/dev/null)
      echo "resumable=$resumable"
    done
  else
    echo "audit_skipped=no_run_root"
  fi

  echo "=== pilot-tier-o end $(date -u +%FT%TZ) ==="
} >> "$LIVE/tier-o-driver.log" 2>&1
