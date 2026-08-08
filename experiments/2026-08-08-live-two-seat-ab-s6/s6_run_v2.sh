#!/usr/bin/env bash
# Rung S6 live two-seat A/B, v2 (correction re-run): conjecture group
# (conjecturer + variator) bound to gemma4:31b, everything else on the
# default glm-5.2 profile, same Ollama Cloud host. Supersedes the first
# run's demonstration of the `coder` seat, whose only role
# (property_designer) was found to have NO public dispatch path at all
# -- see RESULTS.md's dated correction segment and PARKED.md P1. The
# conjecture group made most of the first run's 38 calls, so it is
# guaranteed to fire and gives a real two-model attribution proof.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

# Distinguished from the first run's identical question by one leading
# sentence: run identity (_request_digest) hashes the question verbatim
# and does NOT include seat bindings (PARKED.md P2, Failure #3), so an
# unchanged question here would collide with the already-committed
# coder-seat run root instead of minting a fresh one.
QUESTION='This is the second-seat variant of the same question: this run binds the conjecture role group (conjecturer, variator) to the second model instead of the coder role group. When a research team splits work across two different reasoning engines with different training histories, the SAME engine that authors a claim is often trusted to also check it. Argue for or against the claim that separating the authoring engine from the checking engine is necessary for a result to count as independently verified, and identify what evidence within a single run'"'"'s own record would distinguish genuine independent verification from mere restatement. Where a claim can be tested by counting or by execution, say exactly what to count or execute.'

export DEEPREASON_HOME="$LIVE/home-s6"
mkdir -p "$DEEPREASON_HOME"

{
  echo "=== s6-v2 start $(date -u +%FT%TZ) head=$(git -C "$REPO" log --oneline -1 | cut -d' ' -f1) ==="

  # Reuses the coder-profile.yaml written for the first run -- it is
  # just a provider profile file (gemma4:31b on Ollama Cloud); nothing
  # about its content is coder-specific, only which seat group it gets
  # bound to at setup time.
  if [ ! -f "$LIVE/coder-profile.yaml" ]; then
    python3 "$LIVE/write_coder_profile.py" "$LIVE/coder-profile.yaml"
    echo "write_coder_profile_rc=$?"
  else
    echo "coder_profile_reused=$LIVE/coder-profile.yaml"
  fi

  # Same 8192 -> 16384 maximum-completion-tokens fix proven in the
  # first run (Failure #1); rebinding the seat group changes the
  # compiled manifest's roles table and therefore the request digest,
  # so this is a fresh combination subject regardless.
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 16384 \
    --reasoning none \
    --credential-env OLLAMA_API_KEY \
    --seat "conjecture=$LIVE/coder-profile.yaml"
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  # Cycles/budget raised 6/150000 -> 10/220000 after Failure #4: the
  # first attempt stopped budget_exhausted mid a schema-exhausted
  # critic-batch recovery decomposition, and `continue` crashed trying
  # to resume it (PARKED.md P3). More headroom does not prevent
  # schema_exhausted (a model-reliability trigger, not a budget one)
  # but does make it far less likely the run stops mid-decomposition.
  r0=$SECONDS
  timeout 14400 deepreason reason "$QUESTION" --cycles 10 --token-budget 220000 --allow-partial \
    > "$LIVE/s6-reason-v2.json" 2> "$LIVE/s6-reason-v2.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"

  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/s6-reason-v2.json'))['run_id'])" 2>/dev/null)
  echo "run_id=$run_id"
  root="$DEEPREASON_HOME/runs/$run_id"

  if [ -n "$run_id" ] && [ -d "$root" ]; then
    python3 "$LIVE/s6_audit_v2.py" "$root" > "$LIVE/s6-audit1-v2.json" 2> "$LIVE/s6-audit1-v2.err"
    echo "audit1_rc=$?"

    stop_reason=$(python3 -c "import json;print(json.load(open('$LIVE/s6-audit1-v2.json')).get('stop_reason'))" 2>/dev/null)
    echo "stop_reason=$stop_reason"
    resumable=$(python3 -c "
import json
resumable = {'budget_exhausted', 'converged'}
d = json.load(open('$LIVE/s6-audit1-v2.json'))
print('yes' if d.get('stop_reason') in resumable else 'no')
" 2>/dev/null)
    echo "resumable=$resumable"

    if [ "$resumable" = "yes" ]; then
      c0=$SECONDS
      timeout 14400 deepreason --root "$root" continue --budget cycles=2 \
        > "$LIVE/s6-continue-v2.json" 2> "$LIVE/s6-continue-v2.err"
      echo "continue_rc=$? continue_seconds=$((SECONDS-c0))"

      python3 "$LIVE/s6_audit_v2.py" "$root" > "$LIVE/s6-audit2-v2.json" 2> "$LIVE/s6-audit2-v2.err"
      echo "audit2_rc=$?"
    else
      echo "continue_skipped=non_resumable_stop"
    fi
  else
    echo "audit_skipped=no_run_root"
  fi

  echo "=== s6-v2 end $(date -u +%FT%TZ) ==="
} >> "$LIVE/s6-driver-v2.log" 2>&1
