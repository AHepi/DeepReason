"""Baseline the managed request digest, so the P14 fix can pin it unchanged.

    PYTHONPATH=src:mini python \
      experiments/2026-08-29-defect-managed-path-config-read/probe/request_identity_baseline.py

FIX.md change site 5 admits a configuration digest into run identity, and the
guarantee it owes is that a QUESTION-ONLY request's digest does not move --
the same guarantee `dossier_digest` gave when it was admitted. Exit code 0
always: a measurement, not a test.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from deepreason.preparation import (  # noqa: E402
    RunPreparationRequestV1,
    _request_digest,
)
from deepreason.provider_profile import ProviderProfileV1  # noqa: E402


def main() -> int:
    prof = ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id="model-a",
        model_revision="rev-a",
        family="family-a",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )
    request = RunPreparationRequestV1(question="Why is the sky blue?")
    digest = _request_digest(request, prof)
    print("question-only request digest :", digest)
    print("managed run id               : run-" + digest[:32])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
