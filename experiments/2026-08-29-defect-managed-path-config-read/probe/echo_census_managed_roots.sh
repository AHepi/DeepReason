#!/bin/sh
# Re-derive the record fact DIAGNOSIS.md rests on: every committed MANAGED-path
# run root (one carrying run-preparation.json, i.e. prepared by
# RunPreparationService) has a BYTE-IDENTICAL engine-config echo, across every
# provider profile and every experiment.
#
#   sh experiments/2026-08-29-defect-managed-path-config-read/probe/echo_census_managed_roots.sh
#
# Expected: one distinct echo digest, N roots, several distinct
# source_config_hash values (the profile-derived roles DO vary; nothing else does).
cd "$(dirname "$0")/../../.." || exit 1
for f in $(find experiments -name run-preparation.json | sort); do
  d=$(dirname "$f")
  m="$d/run-manifest.json"
  [ -f "$m" ] || continue
  PYTHONPATH=src:mini python -c "
import json, hashlib, sys
m = json.load(open(sys.argv[1]))
print(hashlib.sha256(m['engine_config_json'].encode()).hexdigest()[:16], m['source_config_hash'][:16])
" "$m"
done | tee /dev/stderr | awk '{e[$1]++; s[$2]++; n++} END {printf "\nroots=%d distinct_echo_digests=%d distinct_source_config_hashes=%d\n", n, length(e), length(s)}'
