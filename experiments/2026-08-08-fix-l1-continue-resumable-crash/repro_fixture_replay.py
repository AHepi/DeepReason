"""Form 1 (record replay): reproduce the crash against a SCRATCH COPY of
the committed S6 fixture, using today's code, no live provider, no
credentials. `Scheduler.run(0)`'s own first action
(`_recover_workflow_prefixes`) is what crashes in production on
`deepreason continue`; this invokes exactly that mechanism directly,
bypassing only the CLI's credential-requiring provider bootstrap
(recovery-from-blob needs no live provider at all, per SUB-workflow.md's
own "What it is" section).

This WRITES to the given root (same as `deepreason continue` would) --
run it only against a throwaway copy, never against
experiments/2026-08-08-live-two-seat-ab-s6/'s own committed fixture,
which stays byte-frozen.

Usage:
    cp -r experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949 /tmp/scratch-copy
    python3 experiments/2026-08-08-fix-l1-continue-resumable-crash/repro_fixture_replay.py /tmp/scratch-copy
"""

import sys
from pathlib import Path

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.nonconjecture_recovery import NonConjectureRecoveryAuthorityError


def main() -> int:
    root = Path(sys.argv[1])
    manifest = load_run_manifest(root / MANIFEST_NAME)

    def forbidden(prompt: str) -> str:
        raise AssertionError("recovery redispatched a durable result -- should never fire")

    endpoints = {
        role: [MockEndpoint(forbidden, name=route.base_url, model=route.model_id) for route in routes]
        for role, routes in manifest.roles.items()
    }
    config = Config(
        roles={
            role: [
                {
                    "endpoint_id": route.endpoint_id,
                    "endpoint": route.base_url,
                    "model": route.model_id,
                    "provider": route.provider,
                    "family": route.family,
                    "max_tokens": route.max_tokens,
                    "context_window_tokens": route.context_window_tokens,
                }
                for route in routes
            ]
            for role, routes in manifest.roles.items()
        }
    )
    harness = Harness(root)
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(1_000_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )

    try:
        Scheduler(harness, adapter, config, workload_profile="text", run_manifest=manifest).run(0)
        print("NO CRASH -- recovery completed cleanly")
        return 1
    except NonConjectureRecoveryAuthorityError as error:
        print(f"CRASHED as predicted: {type(error).__name__}: {error}")
        assert str(error) == "unknown critic task", error
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
