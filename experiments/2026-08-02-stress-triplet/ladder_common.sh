#!/usr/bin/env bash
# Shared ladder body for the 2026-08-02 stress triplet. Caller sets:
#   NAME       triage|orbit|workshop
#   REASONING  none | default   (default keeps glm-5.2's reasoning channel on)
#   ATTACHES   space-separated file list (may be empty)
#   EXTRA_ENV  optional "KEY=VAL KEY=VAL" simulation/research opt-ins
# The three runs share one FRESH home apiece: qualification runs in full,
# concurrently across the triplet - that concurrency is a deliberate stress.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a
QUESTION="$(cat "$LIVE/QUESTION-$NAME.txt")"
export DEEPREASON_HOME="$LIVE/home-$NAME"
for kv in ${EXTRA_ENV:-}; do export "$kv"; done
mkdir -p "$DEEPREASON_HOME"
REASONING_FLAG=""
[ "$REASONING" = "none" ] && REASONING_FLAG="--reasoning none"
ATTACH_FLAGS=""
for f in ${ATTACHES:-}; do ATTACH_FLAGS="$ATTACH_FLAGS --attach $f"; done
{
  echo "=== $NAME ladder start $(date -u +%FT%TZ) ==="
  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 24576 \
    --credential-env OLLAMA_API_KEY $REASONING_FLAG
  echo "setup_rc=$?"
  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 4 --attached-evidence \
    > "$LIVE/$NAME-qual.json" 2> "$LIVE/$NAME-qual.err"
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"
  # Preflight gate: the compiled policy surface, printed BEFORE any reasoning
  # spend, so the record shows what authority this run actually carried.
  python3 - "$DEEPREASON_HOME" <<'PYEOF'
import json, pathlib, sys
home = pathlib.Path(sys.argv[1])
prof = sorted(home.glob("**/run-manifest.json"))
print(f"preflight: {len(prof)} manifest(s) present pre-reason (expect 0; policy prints post-run)")
PYEOF
  r0=$SECONDS
  timeout 7200 deepreason reason --token-budget 200000 \
    $ATTACH_FLAGS \
    --allow-partial \
    "$QUESTION" \
    > "$LIVE/$NAME-reason.json" 2> "$LIVE/$NAME-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"
  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/$NAME-reason.json'))['run_id'])" 2>/dev/null)
  state=$(python3 -c "import json;print(json.load(open('$LIVE/$NAME-reason.json'))['state'])" 2>/dev/null)
  echo "run_id=$run_id state=$state"
  if [ -n "${run_id:-}" ]; then
    python3 - "$DEEPREASON_HOME" "$run_id" > "$LIVE/$NAME-audit.json" 2> "$LIVE/$NAME-audit.err" <<'PYEOF'
import collections, json, sys
from pathlib import Path
from deepreason.harness import Harness
from deepreason.invariants import verify_root

home, run_id = sys.argv[1], sys.argv[2]
root = Path(home) / "runs" / run_id
harness = Harness(root, read_only=True)
out = {"cycles": [], "declines": collections.Counter(), "crit": 0,
       "scratch_events": 0, "research": [], "simulation": []}
for event in harness.log.read():
    ins = [str(v) for v in (event.inputs or [])]
    if not ins:
        continue
    if ins[0] == "cycle":
        out["cycles"].append({"seq": event.seq, "cycle": ins[1:3]})
    elif ins[0] == "trial-declined" and len(ins) > 2:
        out["declines"][ins[2]] += 1
    elif ins[0].startswith("scratch"):
        out["scratch_events"] += 1
    elif ins[0].startswith("research-"):
        out["research"].append(ins[0][:60])
    if event.rule.value == "Crit":
        out["crit"] += 1
out["declines"] = dict(out["declines"])
state = harness.capability_state
for proposal in state.proposals.values():
    ref = state.current_transition_by_request.get(proposal.id)
    transition = state.transitions[ref] if ref else None
    out["simulation"].append({
        "kind": type(proposal).__name__,
        "mode": getattr(proposal, "simulation_mode", None),
        "lifecycle": transition.lifecycle.value if transition else None,
        "reason": transition.reason_code if transition else None,
    })
out["att"] = len(harness.state.att)
out["statuses"] = dict(collections.Counter(s.value for s in harness.state.status.values()))
manifest = json.loads((root / "run-manifest.json").read_text())
cp = manifest.get("criticism_policy") or {}
out["criticism_authority"] = cp.get("authority")
out["criticism_bindings"] = len(cp.get("bindings", []))
validation = verify_root(root)
out["replay_valid"] = validation.get("valid")
out["replay_violations"] = validation.get("violations", [])[:8]
print(json.dumps(out, indent=2))
PYEOF
    echo "audit_rc=$?"
  fi
  echo "=== $NAME ladder end $(date -u +%FT%TZ) ==="
} >> "$LIVE/$NAME.log" 2>&1
