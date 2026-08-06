#!/usr/bin/env bash
# Test-phase ladder: one live run at the post-program head, then a typed
# continuation of its stop. Success criteria live in PLAN.md; this script
# only produces the typed record that will be judged against them.
set -u
LIVE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$LIVE/env"; set +a

QUESTION='A regression test that pins an exact count of committed artifacts fails the first time legitimate new evidence arrives. What general property should such a test assert instead, and which published testing principles support that choice?'

export DEEPREASON_HOME="$LIVE/home-testphase"
mkdir -p "$DEEPREASON_HOME"

{
  echo "=== testphase start $(date -u +%FT%TZ) head=$(git -C "$LIVE/../.." log --oneline -1 | cut -d' ' -f1) ==="

  timeout 300 deepreason setup \
    --provider ollama --endpoint https://ollama.com/v1 \
    --model glm-5.2 --model-revision glm-5.2 --family glm \
    --context-window-tokens 131072 --maximum-completion-tokens 8192 \
    --reasoning none \
    --credential-env OLLAMA_API_KEY
  echo "setup_rc=$?"

  q0=$SECONDS
  timeout 14400 deepreason qualify --yes --json --concurrency 3
  echo "qualify_rc=$? qualify_seconds=$((SECONDS-q0))"

  r0=$SECONDS
  timeout 14400 deepreason reason "$QUESTION" --cycles 4 \
    > "$LIVE/testphase-reason.json" 2> "$LIVE/testphase-reason.err"
  echo "reason_rc=$? reason_seconds=$((SECONDS-r0))"

  run_id=$(python3 -c "import json;print(json.load(open('$LIVE/testphase-reason.json'))['run_id'])" 2>/dev/null)
  echo "run_id=$run_id"
  root="$DEEPREASON_HOME/runs/run-$run_id"

  if [ -n "$run_id" ] && [ -d "$root" ]; then
    python3 - "$root" > "$LIVE/testphase-audit1.json" 2> "$LIVE/testphase-audit1.err" <<'EOF'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
status = json.loads((root / "run-status.json").read_text())
out = {"state": status.get("state"), "stop_reason": status.get("stop_reason")}
try:
    from deepreason.invariants import verify_root
    out["violations"] = verify_root(root)["violations"]
except Exception as e:
    out["verify_error"] = repr(e)
try:
    from deepreason.harness import Harness
    from deepreason.module_events import recorded_module_fingerprints
    h = Harness(root, read_only=True)
    stamps = recorded_module_fingerprints(h)
    out["fingerprint_stamps"] = [
        {"registry": s.registry, "module_id": s.module_id} for s in stamps
    ]
except Exception as e:
    out["fingerprint_error"] = repr(e)
print(json.dumps(out, indent=2))
EOF
    echo "audit1_rc=$?"

    c0=$SECONDS
    timeout 14400 deepreason --root "$root" continue --budget cycles=2 \
      > "$LIVE/testphase-continue.json" 2> "$LIVE/testphase-continue.err"
    echo "continue_rc=$? continue_seconds=$((SECONDS-c0))"

    python3 - "$root" > "$LIVE/testphase-audit2.json" 2> "$LIVE/testphase-audit2.err" <<'EOF'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
status = json.loads((root / "run-status.json").read_text())
out = {"state": status.get("state"), "stop_reason": status.get("stop_reason"),
       "continuations_present": (root / "continuations.jsonl").exists()}
try:
    from deepreason.invariants import verify_root
    out["violations"] = verify_root(root)["violations"]
except Exception as e:
    out["verify_error"] = repr(e)
print(json.dumps(out, indent=2))
EOF
    echo "audit2_rc=$?"
  else
    echo "audit_skipped=no_run_root"
  fi

  echo "=== testphase end $(date -u +%FT%TZ) ==="
} >> "$LIVE/testphase-driver.log" 2>&1
