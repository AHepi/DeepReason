#!/bin/bash
#   m1_attach.sh <arm-label> <attachment-file> <logname>
#
# M1 THROUGH THE EVIDENCE CHANNEL, because the scratch channel cannot reach a
# multi-cycle run without code (PARKED P6: MANIFEST_FILE_UNAVAILABLE before the
# run, SCRATCH_ROOT_BUSY during it, CONTINUE_TYPED_STOP_REQUIRED between
# cycles). `reason --attach` works pre-run, so it is the only route left that
# delivers a document to the seats without touching src/.
#
# ITS COST IS EPISTEMIC AND IS NOT HIDDEN. The scratchpad is declared
# advisory_non_grounding; an attached dossier is EVIDENCE and can ground a
# claim. So this measures whether HISTORY CONTENT changes what conjecturers
# produce -- which is R6 -- and NOT whether the advisory channel the spec
# designs would do the same. RESULTS.md must say so.
#
# BOTH ARMS ATTACH. The control's attachment is a real, structurally identical
# history document from an UNRELATED committed run (the poietics program),
# length-matched to the treatment's. That isolates "history OF THIS PROBLEM"
# from "a history-shaped document exists", which a no-attachment control could
# not: it would differ from the treatment in two ways at once.
#
# --concurrency 2 on qualification, deliberately. The default is 4, and five
# arms at 4 apiece is what produced the ENDPOINT_HTTP_429 storm that cost two
# arms (P3, P4). The flag's own help text names this use.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-03-change-provenance-history-channel
LABEL="$1"; ATTACH="$2"
export DEEPREASON_HOME="$PWD/$D/runs/home-m3"
set -a; . $D/env; set +a
mkdir -p "$DEEPREASON_HOME"
Q="$(cat $D/QUESTION.txt)"

echo "=== $LABEL started $(date -u +%FT%TZ) ==="
[ -s "$ATTACH" ] || { echo "ARM INVALID: attachment '$ATTACH' missing or empty"; exit 6; }
echo "--- attachment ($(wc -c < "$ATTACH") bytes), verbatim, so the arm is auditable ---"
cat "$ATTACH"
echo "--- end attachment ---"

echo "--- setup ---"
deepreason setup --provider ollama --endpoint https://ollama.com/v1 \
  --model qwen3.5:397b --family qwen --credential-env OLLAMA_API_KEY \
  --reasoning none --context-window-tokens 131072 --maximum-completion-tokens 8192
echo "rc=$?"
echo "--- qualify (attached-evidence subject, concurrency 2) ---"
deepreason qualify --yes --attached-evidence --concurrency 2; echo "rc=$?"
echo "--- reason, 4 cycles, attached $(date -u +%FT%TZ) ---"
deepreason reason --cycles 4 --token-budget 600000 --attach "$ATTACH" "$Q"; echo "rc=$?"
ROOT="$(ls -dt $DEEPREASON_HOME/runs/run-* 2>/dev/null | head -1)"
echo "=== results $(date -u +%FT%TZ) ==="
deepreason results "$ROOT" --json --verify
echo "=== $LABEL finished $(date -u +%FT%TZ) ==="
