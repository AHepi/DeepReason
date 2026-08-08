#!/usr/bin/env bash
# Continuation driver after the container/process death that killed the
# original phase1_run.sh mid-ladder (base-q01 completed and recovered
# separately -- see RESULTS.md failure ledger). Runs the REMAINING 9
# questions only; reuses the same DEEPREASON_HOME (setup/qualify already
# cached there, so this skips straight to the per-question loop).
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

export DEEPREASON_HOME="$LIVE/home"

CYCLES=10
TOKEN_BUDGET=180000

RUN_IDS=(base-q13 hard-h01 hard-h05 hard-h10 hard-h15 hard2-h2-01 hard2-h2-08 hard2-h2-15 hard2-h2-22)
RUN_SOURCES=(
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
  echo "=== phase1-resume start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) ==="

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

      # Commit this completed root individually right away (prereg's
      # commit_policy) -- do not let a second interruption strand
      # multiple finished roots uncommitted at once.
      git -C "$REPO" add -- "$root" "$LIVE/phase1-$rid-reason.json" "$LIVE/phase1-$rid-reason.err" \
        "$LIVE/phase1-$rid-audit1.json" "$LIVE/phase1-$rid-audit1.err" \
        "$LIVE/phase1-$rid-continue.json" "$LIVE/phase1-$rid-continue.err" \
        "$LIVE/phase1-$rid-audit2.json" "$LIVE/phase1-$rid-audit2.err" 2>/dev/null
      git -C "$REPO" commit -q -m "Phase 1 root $rid: completed ($stop_reason)" -- "$root" \
        "$LIVE/phase1-$rid-reason.json" "$LIVE/phase1-$rid-reason.err" \
        "$LIVE/phase1-$rid-audit1.json" "$LIVE/phase1-$rid-audit1.err" \
        "$LIVE/phase1-$rid-continue.json" "$LIVE/phase1-$rid-continue.err" \
        "$LIVE/phase1-$rid-audit2.json" "$LIVE/phase1-$rid-audit2.err" 2>/dev/null
      for attempt in 1 2 3 4; do
        git -C "$REPO" push origin claude/corpus-enrichment-patrol-pilot-f4khnk >/dev/null 2>&1 && break
        sleep $((2 ** attempt))
      done
      echo "committed_and_pushed rid=$rid"
    else
      echo "audit_skipped=no_run_root rid=$rid"
    fi

    echo "--- run $rid end $(date -u +%FT%TZ) ---"
  done

  echo "=== phase1-resume end $(date -u +%FT%TZ) ==="
} >> "$LIVE/phase1-resume-driver.log" 2>&1
