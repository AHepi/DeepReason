#!/usr/bin/env bash
# Corpus-enrichment pilot, Phase 1: one shared DEEPREASON_HOME, 10 runs
# across base/hard/hard2 tiers (prereg.yaml run_matrix), coder-group seat
# bound to gemma4:31b (covers property_designer + encoder roles).
# Mirrors experiments/2026-08-08-live-two-seat-ab-s6/s6_run.sh's ladder
# shape (setup -> qualify -> per-question reason/continue/audit), looped.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

export DEEPREASON_HOME="$LIVE/home"
mkdir -p "$DEEPREASON_HOME"

CYCLES=10
TOKEN_BUDGET=180000

RUN_IDS=(base-q01 base-q13 hard-h01 hard-h05 hard-h10 hard-h15 hard2-h2-01 hard2-h2-08 hard2-h2-15 hard2-h2-22)
RUN_SOURCES=(
  "experiments/validation_questions.json:q01"
  "experiments/validation_questions.json:q13"
  "experiments/validation_questions_hard.json:h01"
  "experiments/validation_questions_hard.json:h05"
  "experiments/validation_questions_hard.json:h10"
  "experiments/validation_questions_hard.json:h15"
  "experiments/validation_questions_hard2.json:h2-01"
  "experiments/validation_questions_hard2.json:h2-08"
  "experiments/validation_questions_hard2.json:h2-15"
  "experiments/validation_questions_hard2.json:h2-22"
)

question_text() {
  # $1 = "path:qid"
  local path="${1%%:*}"
  local qid="${1##*:}"
  python3 -c "
import json
d = json.load(open('$REPO/$path'))
row = next(r for r in d if r['id'] == '$qid')
print(row['q'])
"
}

{
  echo "=== phase1 start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) ==="

  python3 "$LIVE/write_coder_profile.py" "$LIVE/coder-profile.yaml"
  echo "write_coder_profile_rc=$?"

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

  for i in "${!RUN_IDS[@]}"; do
    rid="${RUN_IDS[$i]}"
    src="${RUN_SOURCES[$i]}"
    echo "--- run $rid ($src) start $(date -u +%FT%TZ) ---"

    question="$(question_text "$src")"
    if [ -z "$question" ]; then
      echo "question_lookup_failed rid=$rid src=$src"
      continue
    fi

    r0=$SECONDS
    timeout 14400 deepreason reason "$question" --cycles "$CYCLES" --token-budget "$TOKEN_BUDGET" --allow-partial \
      > "$LIVE/phase1-$rid-reason.json" 2> "$LIVE/phase1-$rid-reason.err"
    echo "reason_rc=$? reason_seconds=$((SECONDS-r0)) rid=$rid"

    run_id=$(python3 -c "import json;print(json.load(open('$LIVE/phase1-$rid-reason.json'))['run_id'])" 2>/dev/null)
    echo "run_id=$run_id rid=$rid"
    root="$DEEPREASON_HOME/runs/$run_id"

    if [ -n "$run_id" ] && [ -d "$root" ]; then
      python3 "$LIVE/phase1_audit.py" "$root" > "$LIVE/phase1-$rid-audit1.json" 2> "$LIVE/phase1-$rid-audit1.err"
      echo "audit1_rc=$? rid=$rid"

      stop_reason=$(python3 -c "import json;print(json.load(open('$LIVE/phase1-$rid-audit1.json')).get('stop_reason'))" 2>/dev/null)
      echo "stop_reason=$stop_reason rid=$rid"
      resumable=$(python3 -c "
import json
resumable = {'budget_exhausted', 'converged'}
d = json.load(open('$LIVE/phase1-$rid-audit1.json'))
print('yes' if d.get('stop_reason') in resumable else 'no')
" 2>/dev/null)
      echo "resumable=$resumable rid=$rid"

      if [ "$resumable" = "yes" ]; then
        c0=$SECONDS
        timeout 14400 deepreason --root "$root" continue --budget cycles=2 \
          > "$LIVE/phase1-$rid-continue.json" 2> "$LIVE/phase1-$rid-continue.err"
        echo "continue_rc=$? continue_seconds=$((SECONDS-c0)) rid=$rid"

        python3 "$LIVE/phase1_audit.py" "$root" > "$LIVE/phase1-$rid-audit2.json" 2> "$LIVE/phase1-$rid-audit2.err"
        echo "audit2_rc=$? rid=$rid"
      else
        echo "continue_skipped=non_resumable_stop rid=$rid"
      fi

      echo "record_root=$root rid=$rid"
    else
      echo "audit_skipped=no_run_root rid=$rid"
    fi

    echo "--- run $rid end $(date -u +%FT%TZ) ---"
  done

  echo "=== phase1 end $(date -u +%FT%TZ) ==="
} >> "$LIVE/phase1-driver.log" 2>&1
