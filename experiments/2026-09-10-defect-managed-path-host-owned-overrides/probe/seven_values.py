"""The seven host-owned values, one operator configuration, one table.

Read-only, offline, no provider. Run from the repo root:
    python -u <this file>

For each of the seven values `preparation._config_for_profile` owns, the table
says whether the operator's stated value reached the run (`carried`) and
whether the compiled manifest says it did not (`disclosed`). A row that is
False/False is a value the managed path replaced in silence.
"""
from __future__ import annotations

from datetime import datetime, timezone

from deepreason.config import Config
from deepreason.preparation import (
    build_preparation_manifest,
    engaged_bridge_source,
    engaged_scratchpad_source,
)
from deepreason.provider_profile import ProviderProfileV1
from deepreason.run_manifest import config_from_run_manifest

STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SEVEN = (
    "engine_profile",
    "model_profile",
    "scratchpad",
    "bridge",
    "EMBEDDER_MODEL",
    "CHANNELS_DISABLED",
    "roles",
)


def _profile() -> ProviderProfileV1:
    return ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id="model-a",
        model_revision="rev-a",
        family="family-a",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )


def _operator_config() -> Config:
    # Every value below is stated AWAY from the host's own, so no row can pass
    # by accident: the host takes `engaged_scratchpad_source()` and
    # `engaged_bridge_source()`, and these differ from both in one field.
    scratchpad = dict(engaged_scratchpad_source())
    scratchpad["similarity_top_k"] = 13
    bridge = dict(engaged_bridge_source())
    bridge["output_section_limit"] = 6
    return Config.model_validate(
        {
            "engine_profile": "mini",
            "model_profile": "frontier",
            "scratchpad": scratchpad,
            "bridge": bridge,
            "EMBEDDER_MODEL": "nomic-ai/nomic-embed-text-v1.5",
            "CHANNELS_DISABLED": ["simulation"],
            "roles": {
                "conjecturer": {
                    "provider": "openai",
                    "model": "model-z",
                    "endpoint": "https://elsewhere.example/v1",
                }
            },
        }
    )


def main() -> int:
    operator = _operator_config()
    manifest = build_preparation_manifest(
        _profile(), question="Why is the sky blue?", compiled_at=STAMP, config=operator
    )
    runtime = config_from_run_manifest(manifest)
    pointers = {n.pointer for n in (manifest.compile_notices or ())}
    print(f"compile_notices: {len(manifest.compile_notices or ())}")
    print(
        "scratch_policy: "
        f"backend={manifest.scratch_policy.embedder_backend!r} "
        f"model={manifest.scratch_policy.embedder_model!r}"
    )
    print(f"{'value':<20} {'carried':<9} {'disclosed':<10} operator asked for")
    silent = []
    for name in SEVEN:
        asked = getattr(operator, name)
        got = getattr(runtime, name, object())
        carried = got == asked
        disclosed = f"/engine_config/{name}" in pointers
        if not carried and not disclosed:
            silent.append(name)
        print(f"{name:<20} {carried!s:<9} {disclosed!s:<10} {str(asked)[:46]!r}")
    print(f"\nsilently replaced: {len(silent)} of {len(SEVEN)} -> {silent}")
    return 1 if silent else 0


if __name__ == "__main__":
    raise SystemExit(main())
