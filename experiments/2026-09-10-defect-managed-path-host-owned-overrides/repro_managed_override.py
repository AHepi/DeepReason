"""Reproduce the managed path's silent host-owned overrides, offline.

No provider, no network, no weights required. Two observations, both against
the SAME door `deepreason reason` uses -- `preparation.build_preparation_manifest`
-- and then the same run-time rebuild (`config_from_run_manifest`), the same
builder (`ops.make_embedder`), the same geometry stamp (`Scheduler`'s own
`_embedder_fingerprint`, recorded exactly as `Scheduler.step` records it) and
the same reader `deepreason results` calls (`embedder_summary_for_root`).

  1. THE SEVEN. An operator configuration stating all seven host-owned values
     away from the host's own compiles with ZERO notices, and not one of the
     seven is carried. Neither carried nor disclosed is the defect.

  2. THE GEOMETRY. That configuration names the neural embedder, and the run
     it produces measures on the hashing scale and says so with
     `embedder-unconfigured` -- a true record of the compiled configuration
     and a silent one about the operator's.

  3. THE CONTROL. The SAME rebuilt configuration with the one overridden field
     restored measures on the neural scale in this same container, through the
     same builder and the same stamp. This is what makes observation 2 a
     reproduction of the CAUSE and not of the weather: nothing about the cache,
     the container or the process decides it -- one value does.

Run from the repo root:

    python -u experiments/2026-09-10-defect-managed-path-host-owned-overrides/repro_managed_override.py

Exit 1 = the defect is PRESENT (pre-fix). Exit 0 = it is gone (post-fix).
The verdict rests on both observations: after the fix, observation 2 must
stamp the neural fingerprint with no `embedder-unconfigured`, and every row of
observation 1 must be carried or disclosed.

The neural half of observation 2 needs the fastembed weights in the cache
(`deepreason embedder-warmup`). Without them the run legitimately falls back
and records `embedder-fallback` -- which is the OTHER correct post-fix answer,
and the script accepts it as such, because a fix that made the geometry depend
on the cache being warm would have made run identity depend on the container.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from deepreason.application.results import embedder_line, embedder_summary_for_root
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ops import make_embedder
from deepreason.preparation import (
    build_preparation_manifest,
    engaged_bridge_source,
    engaged_scratchpad_source,
)
from deepreason.provider_profile import ProviderProfileV1
from deepreason.run_manifest import config_from_run_manifest
from deepreason.scheduler.scheduler import Scheduler

STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
NEURAL = "nomic-ai/nomic-embed-text-v1.5"
SEVEN = (
    "engine_profile",
    "model_profile",
    "scratchpad",
    "bridge",
    "EMBEDDER_MODEL",
    "CHANNELS_DISABLED",
    "roles",
)


def profile() -> ProviderProfileV1:
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


def operator_config() -> Config:
    """Every one of the seven stated AWAY from the host's own value.

    `scratchpad` and `bridge` start from the host's own preset and move one
    field each, so neither row can pass by matching a code default the host
    never uses.
    """

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
            "EMBEDDER_MODEL": NEURAL,
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


def observation_one(manifest, operator) -> list[str]:
    """Return the values that are neither carried nor disclosed."""

    runtime = config_from_run_manifest(manifest)
    pointers = {n.pointer for n in (manifest.compile_notices or ())}
    print("## 1. THE SEVEN")
    print(f"compile notices on the manifest: {len(manifest.compile_notices or ())}")
    for notice in manifest.compile_notices or ():
        print(f"    {notice.code} {notice.pointer}")
    print(f"{'value':<20} {'carried':<9} {'disclosed':<10} the operator stated")
    silent = []
    for name in SEVEN:
        asked = getattr(operator, name)
        carried = getattr(runtime, name, object()) == asked
        disclosed = f"/engine_config/{name}" in pointers
        if not carried and not disclosed:
            silent.append(name)
        print(f"{name:<20} {carried!s:<9} {disclosed!s:<10} {str(asked)[:44]!r}")
    print(f"neither carried nor disclosed: {len(silent)} of {len(SEVEN)} -> {silent}")
    return silent


def observation_two(manifest, root: Path) -> dict:
    """Drive the geometry stamp onto a real log and read it back."""

    runtime = config_from_run_manifest(manifest)
    harness = Harness(root)
    embedder = make_embedder(harness, runtime)
    # Exactly what `Scheduler.step` records once per run, through the
    # scheduler's own fingerprint reader -- not a restatement of it.
    scheduler = Scheduler(harness, None, runtime, embedder=embedder)
    fingerprint = scheduler._embedder_fingerprint()
    harness.record_measure(
        inputs=[
            "embedder",
            fingerprint["model"],
            fingerprint["version"],
            fingerprint["sentinel"],
        ]
    )
    kinds = [
        str(event.inputs[0])
        for event in harness.log.read()
        if event.inputs and str(event.inputs[0]).startswith("embedder")
    ]
    summary = embedder_summary_for_root(root)
    print("\n## 2. THE GEOMETRY")
    print(f"compiled scratch policy: backend={manifest.scratch_policy.embedder_backend!r} "
          f"model={manifest.scratch_policy.embedder_model!r}")
    print(f"engine_config EMBEDDER_MODEL (what the run rebuilds): {runtime.EMBEDDER_MODEL!r}")
    print(f"Measure kinds on the log: {kinds}")
    print(f"deepreason results would print: embedder: {embedder_line(summary)}")
    return {"summary": summary, "kinds": kinds}


def observation_three(manifest, root: Path) -> dict:
    """The control: the same rebuild with the one field put back."""

    runtime = config_from_run_manifest(manifest).model_copy(
        update={"EMBEDDER_MODEL": NEURAL}
    )
    harness = Harness(root)
    embedder = make_embedder(harness, runtime)
    scheduler = Scheduler(harness, None, runtime, embedder=embedder)
    fingerprint = scheduler._embedder_fingerprint()
    harness.record_measure(
        inputs=[
            "embedder",
            fingerprint["model"],
            fingerprint["version"],
            fingerprint["sentinel"],
        ]
    )
    summary = embedder_summary_for_root(root)
    print("\n## 3. THE CONTROL (the same rebuild, EMBEDDER_MODEL put back)")
    print(f"deepreason results would print: embedder: {embedder_line(summary)}")
    return summary


def main() -> int:
    operator = operator_config()
    manifest = build_preparation_manifest(
        profile(), question="Why is the sky blue?", compiled_at=STAMP, config=operator
    )
    silent = observation_one(manifest, operator)
    with tempfile.TemporaryDirectory() as tmp:
        seen = observation_two(manifest, Path(tmp) / "root")
        control = observation_three(manifest, Path(tmp) / "control")

    summary, kinds = seen["summary"], seen["kinds"]
    measured_neural = summary.get("model") == NEURAL
    asked_and_answered = measured_neural or "embedder-fallback" in kinds
    print("\n## VERDICT")
    print(f"the operator asked for {NEURAL!r}")
    print(f"the run measured with {summary.get('model')!r} "
          f"(backend {summary.get('backend')!r})")
    print(f"the run asked the neural backend for it at all: {asked_and_answered}")
    print(f"the same rebuild with the field restored measured with "
          f"{control.get('model')!r} (backend {control.get('backend')!r})")
    if silent or not asked_and_answered:
        print("DEFECT PRESENT: "
              + (f"{len(silent)} of {len(SEVEN)} values silently replaced; " if silent else "")
              + ("the configured embedder was never requested"
                 if not asked_and_answered else "").strip("; "))
        return 1
    print("DEFECT ABSENT: every host-owned value is carried or disclosed, and the "
          "configured embedder reached the run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
