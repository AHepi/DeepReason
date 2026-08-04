"""Run `deepreason reason` with a chosen school-population backend active.

Rung 5's A/B driver. The CLI has no backend flag — selection is a Python
scope (`schools.population_backend`), deliberately, because a `Config` field
would enter the qualification subject digest and the manifest sha (SPEC.md
M3). The scheduler resolves the backend through `active_backend()` while the
run executes, so wrapping the in-process CLI entry point selects it for the
whole run and restores it afterwards.

    python reason_with_backend.py <backend-id> [deepreason-reason args...]
"""

import sys

from deepreason.capture import schools
from deepreason.cli.main import main

if __name__ == "__main__":
    backend_id = sys.argv[1]
    with schools.population_backend(backend_id) as backend:
        print(
            f"[driver] population backend = {backend.fingerprint()}",
            file=sys.stderr,
        )
        raise SystemExit(main(["reason", *sys.argv[2:]]))
