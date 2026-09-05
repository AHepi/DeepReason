#!/bin/bash
#   m1_replicate.sh <home-dir-name> <arm-label> <attachment-file> 
#
# A REPLICATE of one M1 arm, under PREREG.md Amendment 5. Every value below is
# the one `m1_attach.sh` already used; the ONLY difference is which home the
# run lands in, and that difference is forced rather than chosen.
#
# WHY A SEPARATE HOME. Run identity is deterministic: same question + same
# config + same dossier digest yields the same run id. The first pair's roots
# are committed in home-m1, so a replicate there would carry a committed root's
# id and be refused with RUN_ALREADY_STARTED. A fresh home has no leftover
# root. The replicate roots therefore carry the SAME ids as the originals, in
# different homes -- determinism working, not a collision. Every downstream
# script keys on root PATH for exactly this reason.
#
# WHY THE QUALIFICATION CACHE IS COPIED IN. PREREG.md section 0 fixes one
# shared qualification across arms so no arm pays a battery the others did not.
# The copy preserves that across homes. If the subject digest does not match,
# qualify reruns the ~14-minute battery and the log says so; that costs time,
# not comparability.
set -u
cd /home/user/DeepReason
D=experiments/2026-09-03-change-provenance-history-channel
HOMEDIR="$1"; LABEL="$2"; ATTACH="$3"
export DEEPREASON_HOME="$PWD/$D/runs/$HOMEDIR"
set -a; . $D/env; set +a
mkdir -p "$DEEPREASON_HOME"

# Seed the new home from the first pair's, cache only -- never the admission
# store, which each run rebuilds from its own attachment.
if [ ! -d "$DEEPREASON_HOME/qualification-cache" ]; then
  cp -r "$PWD/$D/runs/home-m1/qualification-cache" "$DEEPREASON_HOME/" 2>/dev/null \
    && echo "--- qualification cache seeded from home-m1 ---" \
    || echo "--- qualification cache NOT seeded; a full battery will run ---"
fi

Q="$(cat $D/QUESTION.txt)"
echo "=== $LABEL started $(date -u +%FT%TZ)  home=$HOMEDIR ==="
[ -s "$ATTACH" ] || { echo "ARM INVALID: attachment '$ATTACH' missing or empty"; exit 6; }
echo "--- attachment $(wc -c < "$ATTACH") bytes, sha256 $(sha256sum "$ATTACH" | cut -d' ' -f1) ---"

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
