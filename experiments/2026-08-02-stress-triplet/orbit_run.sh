#!/usr/bin/env bash
LIVE="$(cd "$(dirname "$0")" && pwd)"
export NAME=orbit REASONING=none
export ATTACHES="$LIVE/../live_jolt_2026-07-31/dossier/CAPABILITY_CONTRACT.md"
export EXTRA_ENV="DEEPREASON_SIMULATION_RUNNER=contained DEEPREASON_CONFIG_REFEREE=2"
exec bash "$LIVE/ladder_common.sh"
