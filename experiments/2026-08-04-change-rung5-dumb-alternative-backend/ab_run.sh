#!/usr/bin/env bash
# Rung 5 live A/B: the same question, default allocation vs the deliberately
# dumb round-robin, compared on TYPED outcomes only.
#
# Both arms run against IDENTICAL qualification evidence: the round-robin
# home is a copy of the qualified default home, so the only difference
# between the arms is which registered population backend is active. That is
# the whole point of the comparison, and copying beats re-qualifying because
# re-qualifying would introduce a second, independently-sampled battery as a
# confound.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
REPO="$(cd "$LIVE/../.." && pwd)"

QUESTION='Rival research programmes inside one reasoning system are usually allocated to problems by ownership: whichever lineage produced the parent artifact works its successors. Argue for or against the claim that ownership-based allocation systematically suppresses the discovery of cross-cutting explanations, and identify what evidence within a single run would distinguish suppression from mere efficiency. Where a claim can be tested by counting, say exactly what to count.'

TOKEN_BUDGET=120000

run_arm () {
  local arm="$1" home="$2"
  echo "=== arm=$arm start $(date -u +%FT%TZ) ==="
  export DEEPREASON_HOME="$home"
  local t0=$SECONDS
  if [ "$arm" = "default" ]; then
    timeout 14400 deepreason reason --token-budget "$TOKEN_BUDGET" --allow-partial \
      "$QUESTION" > "$LIVE/$arm-reason.json" 2> "$LIVE/$arm-reason.err"
  else
    timeout 14400 python "$LIVE/reason_with_backend.py" round-robin \
      --token-budget "$TOKEN_BUDGET" --allow-partial \
      "$QUESTION" > "$LIVE/$arm-reason.json" 2> "$LIVE/$arm-reason.err"
  fi
  echo "arm=$arm reason_rc=$? seconds=$((SECONDS-t0))"
  local rid state
  rid=$(python3 -c "import json;print(json.load(open('$LIVE/$arm-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/$arm-reason.json'))['state'])" 2>/dev/null)
  echo "arm=$arm run_id=$rid state=$state"
}

{
  echo "=== rung5 A/B start $(date -u +%FT%TZ) ==="
  # Both arms share ONE qualification: rr-home is a byte copy of the
  # qualified default home, so the active backend is the only difference
  # between the arms. Re-qualifying would introduce a second,
  # independently-sampled battery as a confound.
  rm -rf "$LIVE/rr-home"
  cp -a "$LIVE/ab-home" "$LIVE/rr-home"
  echo "rr-home seeded from qualified ab-home rc=$?"
  run_arm default    "$LIVE/ab-home"
  run_arm roundrobin "$LIVE/rr-home"
  echo "=== audit ==="
  python3 "$LIVE/ab_audit.py" "$LIVE" > "$LIVE/ab-audit.json" 2> "$LIVE/ab-audit.err"
  echo "audit_rc=$?"
  echo "=== rung5 A/B end $(date -u +%FT%TZ) ==="
} 2>&1 | tee -a "$LIVE/ab_run.log"
