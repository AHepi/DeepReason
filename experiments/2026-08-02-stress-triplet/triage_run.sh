#!/usr/bin/env bash
LIVE="$(cd "$(dirname "$0")" && pwd)"
export NAME=triage REASONING=none
export ATTACHES="$LIVE/../2026-08-02-map-falsification/PARKED.md $LIVE/../2026-08-02-map-falsification/RESULTS.md"
exec bash "$LIVE/ladder_common.sh"
