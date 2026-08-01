#!/usr/bin/env bash
# Live in-run research proof: one frontier model (glm-5.2), two runs whose
# ONLY difference is the frozen research domain allowlist.
#
#   wide   — en.wikipedia.org + www.rfc-editor.org  (rich, fetchable targets)
#   narrow — docs.python.org only                    (same question; proposals
#            outside the frozen list become live typed denials)
#
# Each allowlist is part of the compiled manifest, hence a distinct
# qualification behavior subject: every ladder requalifies. Qualification
# dispatches 3 concurrent cases (the account-wide cap), so ladders run
# strictly sequentially.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

QUESTION_CORE='Deterministic replay in an append-only reasoning system depends on retried operations being safe to repeat. Drawing on published definitions, what precisely distinguishes an idempotent operation from a safe one, and which of the two properties does an append-only event log actually require of its writers to survive at-least-once delivery?'

run_ladder() {
  slug="$1"; allowlist="$2"; hint="$3"
  export DEEPREASON_HOME="$LIVE/$slug"
  export DEEPREASON_RESEARCH_ALLOWLIST="$allowlist"
  mkdir -p "$DEEPREASON_HOME"
  question="$QUESTION_CORE $hint"
  {
    echo "=== $slug (glm-5.2, allowlist=$allowlist) start $(date -u +%FT%TZ) ==="
    timeout 300 deepreason setup \
      --provider ollama --endpoint https://ollama.com/v1 \
      --model glm-5.2 --model-revision glm-5.2 --family glm \
      --context-window-tokens 131072 --maximum-completion-tokens 8192 \
      --credential-env OLLAMA_API_KEY
    echo "setup_rc=$?"
    q0=$SECONDS
    timeout 14400 deepreason qualify --yes --json --concurrency 3
    echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
    r0=$SECONDS
    timeout 14400 deepreason reason "$question" \
      > "$LIVE/$slug-reason.json" 2> "$LIVE/$slug-reason.err"
    echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
    run_id=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-reason.json'))['run_id'])" 2>/dev/null)
    problem_id=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-reason.json'))['problem_id'])" 2>/dev/null)
    state=$(python3 -c "import json;print(json.load(open('$LIVE/$slug-reason.json'))['state'])" 2>/dev/null)
    echo "run_id=$run_id problem_id=$problem_id state=$state"
    python3 "$LIVE/research_audit.py" "$DEEPREASON_HOME" "$run_id" \
      > "$LIVE/$slug-research-audit.json" 2> "$LIVE/$slug-research-audit.err"
    echo "audit_rc=$?"
    if [ "$state" = "completed" ]; then
      b0=$SECONDS
      timeout 7200 python3 "$LIVE/bridge_trio.py" "$DEEPREASON_HOME" "$run_id" "$problem_id" \
        > "$LIVE/$slug-bridge.txt" 2> "$LIVE/$slug-bridge.err"
      echo "bridge_rc=$? bridge_seconds=$((SECONDS-b0))"
    fi
    echo "=== $slug end $(date -u +%FT%TZ) ==="
  } >> "$LIVE/$slug.log" 2>&1
}

run_ladder wide \
  "en.wikipedia.org,www.rfc-editor.org" \
  "You may propose directed research fetches of specific https pages; this run'\''s frozen domain allowlist permits en.wikipedia.org and www.rfc-editor.org (RFC 9110 defines both terms). Fetched pages become citable evidence blocks."

run_ladder narrow \
  "docs.python.org" \
  "You may propose directed research fetches of specific https pages; this run'\''s frozen domain allowlist permits only docs.python.org. Proposals to any other host will be recorded and denied by the harness. Fetched pages become citable evidence blocks."

echo "all ladders done $(date -u +%FT%TZ)" >> "$LIVE/orchestrator.log"
