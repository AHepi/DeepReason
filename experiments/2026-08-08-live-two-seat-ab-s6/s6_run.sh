#!/usr/bin/env bash
# Rung S6 live two-seat A/B: conjecturer on glm-5.2 (default profile),
# coder seat (property_designer) bound to gemma4:31b, same Ollama Cloud
# host -- see PLAN.md for the recorded model-choice rationale and the
# two priced deviations (single provider credential; property_designer's
# own stochasticity).
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

QUESTION='When a research team splits work across two different reasoning engines with different training histories, the SAME engine that authors a claim is often trusted to also check it. Argue for or against the claim that separating the authoring engine from the checking engine is necessary for a result to count as independently verified, and identify what evidence within a single run'"'"'s own record would distinguish genuine independent verification from mere restatement. Where a claim can be tested by counting or by execution, say exactly what to count or execute.'

export DEEPREASON_HOME="$LIVE/home-s6"
mkdir -p "$DEEPREASON_HOME"

{
  echo "=== s6 start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) ==="

  python3 "$LIVE/write_coder_profile.py" "$LIVE/coder-profile.yaml"
  echo "write_coder_profile_rc=$?"

  # maximum-completion-tokens raised 8192 -> 16384 after Failure #1
  # (a REPAIR_SCOPE_VIOLATION on the summarizer/compact contract at
  # 8192); see RESULTS.md.
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 16384 \
    --reasoning none \
    --credential-env OLLAMA_API_KEY \
    --seat "coder=$LIVE/coder-profile.yaml"
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  r0=$SECONDS
  timeout 14400 deepreason reason "$QUESTION" --cycles 6 --token-budget 150000 --allow-partial \
    > "$LIVE/s6-reason.json" 2> "$LIVE/s6-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"

  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/s6-reason.json'))['run_id'])" 2>/dev/null)
  echo "run_id=$run_id"
  root="$DEEPREASON_HOME/runs/$run_id"

  if [ -n "$run_id" ] && [ -d "$root" ]; then
    python3 "$LIVE/s6_audit.py" "$root" > "$LIVE/s6-audit1.json" 2> "$LIVE/s6-audit1.err"
    echo "audit1_rc=$?"

    stop_reason=$(python3 -c "import json;print(json.load(open('$LIVE/s6-audit1.json')).get('stop_reason'))" 2>/dev/null)
    echo "stop_reason=$stop_reason"
    resumable=$(python3 -c "
import json
resumable = {'budget_exhausted', 'converged'}
d = json.load(open('$LIVE/s6-audit1.json'))
print('yes' if d.get('stop_reason') in resumable else 'no')
" 2>/dev/null)
    echo "resumable=$resumable"

    if [ "$resumable" = "yes" ]; then
      c0=$SECONDS
      timeout 14400 deepreason --root "$root" continue --budget cycles=2 \
        > "$LIVE/s6-continue.json" 2> "$LIVE/s6-continue.err"
      echo "continue_rc=$? continue_seconds=$((SECONDS-c0))"

      python3 "$LIVE/s6_audit.py" "$root" > "$LIVE/s6-audit2.json" 2> "$LIVE/s6-audit2.err"
      echo "audit2_rc=$?"
    else
      echo "continue_skipped=non_resumable_stop"
    fi
  else
    echo "audit_skipped=no_run_root"
  fi

  echo "=== s6 end $(date -u +%FT%TZ) ==="
} >> "$LIVE/s6-driver.log" 2>&1
