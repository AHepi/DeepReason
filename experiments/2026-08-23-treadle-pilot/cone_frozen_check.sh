#!/usr/bin/env bash
# R10: no pilot task cone may include a frozen surface.
# The seven paths are enumerated from docs/map/INV-frozen-surfaces.md
# (five surfaces + the frozen-adjacent route_fingerprint carrier).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
FROZEN='src/deepreason/capabilities/state.py
src/deepreason/harness.py
src/deepreason/invariants.py
src/deepreason/verification/
src/deepreason/run_manifest.py
src/deepreason/qualification.py
src/deepreason/llm/firewall.py'

fail=0
check() {  # check <task-id> <file-list-producing-command...>
    local tid="$1"; shift
    local hits
    hits=$("$@" | grep -Ff <(echo "$FROZEN") || true)
    if [ -n "$hits" ]; then
        echo "FROZEN CONTACT  $tid:"; echo "$hits" | sed 's/^/    /'; fail=1
    else
        echo "clean           $tid"
    fi
}
cone_files() { git ls-files -- "$@"; }

check PIL-DocsVerifyDelta      cone_files 'experiments/2026-08-23-treadle-pilot/T1/*'
check PIL-RegressionFixture    cone_files 'experiments/2026-08-23-treadle-pilot/T3/*'
check PIL-SpecDriftJudgment    cone_files 'experiments/2026-08-23-treadle-pilot/T4/*'
check REV-RungD                git diff --name-only b10fc5fd2..c1a2f09a1

echo
[ $fail -eq 0 ] && echo "R10: every pilot cone is clear of every frozen surface." \
                || echo "R10: VIOLATED — a cone touches a frozen surface; the task may not be added."
exit $fail
