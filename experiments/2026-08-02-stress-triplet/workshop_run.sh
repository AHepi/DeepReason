#!/usr/bin/env bash
LIVE="$(cd "$(dirname "$0")" && pwd)"
export NAME=workshop REASONING=none
export ATTACHES=""
exec bash "$LIVE/ladder_common.sh"
