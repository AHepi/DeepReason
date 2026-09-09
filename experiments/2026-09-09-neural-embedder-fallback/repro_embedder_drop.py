"""Reproduce the silent embedder drop, offline, with no provider and no weights.

Three observations, all against `preparation.build_preparation_manifest` — the
one builder the managed `deepreason reason` path uses:

  1. An operator configuration that EXPLICITLY names the neural embedder still
     compiles `scratch_policy.embedder_model = null`, and the manifest carries
     no notice of any kind about it.
  2. `ops.make_embedder` on that compiled configuration returns the hashing
     default and writes NOTHING to the log — the `embedder-fallback` record
     lives below an early return it never reaches.
  3. The result is independent of the weights: pointing FASTEMBED_CACHE_PATH at
     the warmed cache and then at an unreadable directory produces a
     byte-identical manifest, because no backend is ever built.

Run: python -u experiments/2026-09-09-neural-embedder-fallback/repro_embedder_drop.py
Exit 0 = the defect is PRESENT (pre-fix). Exit 1 = it is gone (post-fix).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from deepreason.config import Config
from deepreason.ops import make_embedder
from deepreason.preparation import build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.run_manifest import config_from_run_manifest

STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


class RecordingHarness:
    """The narrowest stand-in for the harness `make_embedder` is given: it
    records Measure inputs and nothing else, so an absent record is visible as
    an empty list rather than as a missing file."""

    def __init__(self) -> None:
        self.measures: list[list[str]] = []

    def record_measure(self, inputs):
        self.measures.append([str(v) for v in inputs])


def manifest_for(operator: Config | None):
    return build_preparation_manifest(
        profile(),
        question="Why is the sky blue?",
        compiled_at=STAMP,
        **({"config": operator} if operator is not None else {}),
    )


def main() -> int:
    defect_present = True
    print("=" * 72)
    print("1. AN OPERATOR CONFIGURATION THAT NAMES THE NEURAL EMBEDDER")
    print("=" * 72)

    asked = Config().EMBEDDER_MODEL
    print(f"Config() default EMBEDDER_MODEL          : {asked!r}")
    operator = Config(EMBEDDER_MODEL="nomic-ai/nomic-embed-text-v1.5")
    print(f"operator's explicit EMBEDDER_MODEL       : {operator.EMBEDDER_MODEL!r}")

    manifest = manifest_for(operator)
    compiled = config_from_run_manifest(manifest)
    notices = [
        {"code": n.code, "pointer": n.pointer}
        for n in (manifest.compile_notices or ())
    ]
    embedder_notices = [n for n in notices if "EMBEDDER" in json.dumps(n).upper()]

    print(f"manifest scratch_policy.embedder_model   : "
          f"{manifest.scratch_policy.embedder_model!r}")
    print(f"manifest scratch_policy.embedder_backend : "
          f"{manifest.scratch_policy.embedder_backend!r}")
    print(f"runtime Config.EMBEDDER_MODEL            : {compiled.EMBEDDER_MODEL!r}")
    print(f"compile notices, all codes               : {notices}")
    print(f"compile notices mentioning the embedder  : {embedder_notices}")

    dropped = operator.EMBEDDER_MODEL is not None and compiled.EMBEDDER_MODEL is None
    if dropped and not embedder_notices:
        print("\n  >> DEFECT: the value was dropped and NOTHING in the record says so.")
    elif dropped:
        print("\n  >> the value was dropped, and a notice names it. Defect absent.")
        defect_present = False
    else:
        print("\n  >> the value survived into the run. Defect absent.")
        defect_present = False

    print()
    print("=" * 72)
    print("2. WHAT THE RUN-TIME BUILDER DOES WITH THE COMPILED CONFIGURATION")
    print("=" * 72)
    harness = RecordingHarness()
    embedder = make_embedder(harness, compiled)
    print(f"make_embedder returned                   : {embedder!r}")
    print("  (None means: the Scheduler constructs the zero-dependency hashing"
          " default)")
    print(f"Measure records written                  : {harness.measures}")
    if not harness.measures:
        print("\n  >> DEFECT: the geometry instrument changed and the log is silent.")
    else:
        print("\n  >> a typed record names the cause. Defect absent.")
        defect_present = False

    print()
    print("=" * 72)
    print("3. THE WEIGHTS ARE IRRELEVANT — NO BACKEND IS EVER BUILT")
    print("=" * 72)
    warm = os.environ.get("FASTEMBED_CACHE_PATH") or str(
        Path(tempfile.gettempdir()) / "fastembed_cache"
    )
    print(f"warmed cache location                    : {warm}")
    print(f"  exists on disk                         : {Path(warm).exists()}")

    digests = {}
    with tempfile.TemporaryDirectory() as unreadable:
        for label, value in (("warmed", warm), ("unreadable", unreadable)):
            before = os.environ.get("FASTEMBED_CACHE_PATH")
            os.environ["FASTEMBED_CACHE_PATH"] = value
            try:
                digests[label] = manifest_for(operator).model_dump_json()
            finally:
                if before is None:
                    os.environ.pop("FASTEMBED_CACHE_PATH", None)
                else:
                    os.environ["FASTEMBED_CACHE_PATH"] = before

    identical = digests["warmed"] == digests["unreadable"]
    print(f"manifest byte-identical either way       : {identical}")
    if identical:
        print("\n  >> The cache hypothesis is REFUTED: the compiled configuration")
        print("     does not depend on the weights, because it never asks for them.")
    else:
        print("\n  >> UNEXPECTED: the manifest depends on the cache location.")

    print()
    print("=" * 72)
    print(f"VERDICT: defect {'PRESENT' if defect_present else 'ABSENT'}")
    print("=" * 72)
    return 0 if defect_present else 1


if __name__ == "__main__":
    sys.exit(main())
