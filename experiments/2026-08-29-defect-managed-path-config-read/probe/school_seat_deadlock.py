"""Is any school-seat opt-in reachable on the managed path today?

    PYTHONPATH=src:mini python \
      experiments/2026-08-29-defect-managed-path-config-read/probe/school_seat_deadlock.py

`prepare` resolves school/criticism seats and hands them to
`build_preparation_manifest`, which refuses unless `config.SCHOOL_SEATS_ENABLED`
-- and the managed path's Config is synthesised from the provider profile, where
that flag is always its default. Exit code 0 always: a measurement, not a test.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from deepreason.preparation import (  # noqa: E402
    _config_for_profile,
    build_preparation_manifest,
)
from deepreason.provider_profile import ProviderProfileV1  # noqa: E402
from deepreason.run_manifest import RunManifestError  # noqa: E402


def profile(model="model-a", revision="rev-a", family="family-a"):
    return ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id=model,
        model_revision=revision,
        family=family,
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )


def main() -> int:
    prof = profile()
    synthesised = _config_for_profile(prof)
    print("managed-path Config.SCHOOL_SEATS_ENABLED   =", synthesised.SCHOOL_SEATS_ENABLED)
    print("managed-path Config.LEGACY_CRITICISM_ENABLED =", synthesised.LEGACY_CRITICISM_ENABLED)
    print()
    other = profile("model-b", "rev-b", "family-b")
    for label, kwargs in (
        ("reason --school-seat popper=<profile>", {"school_seats": {"popper": other}}),
        ("reason --criticism-seat popper=<profile>", {"criticism_seats": {"popper": other}}),
    ):
        try:
            build_preparation_manifest(
                prof, question="Q", compiled_at="2026-07-23T00:00:00Z", **kwargs
            )
            print(f"{label:44s} -> COMPILES")
        except RunManifestError as error:
            print(f"{label:44s} -> REFUSED {error.args[0]}")
    print()
    print("VERDICT: on the managed path these opt-ins are unreachable for every")
    print("provider profile, because no route exists by which the operator's")
    print("SCHOOL_SEATS_ENABLED could reach _config_for_profile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
