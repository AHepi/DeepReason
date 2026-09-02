"""Unit reproduction: the gate defers `hv` even when the seat holds the grant.

Fidelity is not simulated. The manifest here is the REAL committed manifest of
`experiments/2026-08-12-live-grounded-extension-expansion/run` — the one root on
`main` whose `variator[0]` seat holds `variator.direct.v1` and whose log records
336 deferred `hv` phases and zero `hv_set` measurements. Nothing about the
route, the seat, or the grant is invented; the file is read read-only and parsed
by the shipped `RunManifest` model.

This lives in the tranche directory rather than in `tests/` on purpose: today it
asserts the DEFECT, and a defect assertion in the gate would make
`pytest tests/ -q -n 4` red for the whole tranche. `dr-implement-fix` lands the
INVERTED assertion in `tests/` as the regression.

Usage:  python experiments/2026-09-02-defect-hv-v6-reachability/repro_gate.py
Exit 0  the defect is REPRODUCED (the gate deferred despite the grant).
Exit 1  the gate consulted the grant (post-fix behaviour).
"""

from __future__ import annotations

import json
import pathlib
import sys
from types import SimpleNamespace

REPO = pathlib.Path(__file__).resolve().parents[2]
GRANT_ROOT = REPO / "experiments/2026-08-12-live-grounded-extension-expansion/run"
NO_GRANT_ROOT = REPO / "experiments/2026-08-25-poietics-program/run"

# The two phases whose deferral is this tranche's goal, with the role each
# names at its call site (scheduler.py:1358 and scheduler.py:2947).
HV_PHASES = (("hv-floor", "variator"), ("hv-spot-check", "variator"))


class _Log:
    def __init__(self):
        self.events: list[SimpleNamespace] = []

    def read(self):
        return tuple(self.events)


class _Harness:
    """The minimum surface `_defer_untransactional_v6_phase` touches."""

    def __init__(self):
        self.log = _Log()

    def record_measure(self, *, inputs, **_kwargs):
        self.log.events.append(SimpleNamespace(inputs=tuple(inputs)))


def scheduler_for(manifest):
    from deepreason.scheduler.scheduler import Scheduler

    scheduler = object.__new__(Scheduler)
    scheduler.run_manifest = manifest
    scheduler.harness = _Harness()
    scheduler.adapter = SimpleNamespace(has_role=lambda role: True)
    scheduler.diagnostics = []
    scheduler._cycles = 0
    return scheduler


def load_manifest(root: pathlib.Path):
    from deepreason.run_manifest import RunManifest

    return RunManifest.model_validate(json.loads((root / "run-manifest.json").read_text()))


def variator_contracts(manifest) -> list[str]:
    plan = manifest.route_seat_behavioral_capability_plan
    if plan is None:
        return []
    return sorted(
        contract.contract_id
        for entry in plan.entries
        if entry.role == "variator"
        for contract in entry.contracts
    )


def probe(label: str, root: pathlib.Path) -> dict:
    manifest = load_manifest(root)
    grants = variator_contracts(manifest)
    scheduler = scheduler_for(manifest)
    deferred = {
        phase: scheduler._defer_untransactional_v6_phase(phase, role, "artifact-1", "k-1")
        for phase, role in HV_PHASES
    }
    markers = [
        event.inputs[1]
        for event in scheduler.harness.log.read()
        if event.inputs and event.inputs[0] == "v6-model-phase-deferred.v1"
    ]
    print(f"--- {label}: {root.relative_to(REPO)}")
    print(f"    schema_version                 {manifest.schema_version}")
    print(f"    variator seat behavioural grant {grants or 'NONE'}")
    for phase, was_deferred in deferred.items():
        print(f"    _defer(...'{phase}', 'variator')  -> {was_deferred}")
    print(f"    typed deferral markers written  {markers}")
    return {"grants": grants, "deferred": deferred}


def main() -> int:
    granted = probe("GRANT PRESENT", GRANT_ROOT)
    print()
    control = probe("CONTROL, no grant", NO_GRANT_ROOT)
    print()

    assert control["grants"] == [], "the control root must carry no variator grant"
    assert all(control["deferred"].values()), (
        "the control root must still defer — that behaviour is correct and the fix "
        "must not change it"
    )
    print(
        "CONTROL holds: a seat with no grant defers both hv phases and writes the "
        "typed notice. This is the behaviour the fix must PRESERVE."
    )

    assert granted["grants"] == ["variator.direct.v1"], granted["grants"]
    if all(granted["deferred"].values()):
        print()
        print(
            "REPRODUCED: variator[0] holds variator.direct.v1 and the gate deferred\n"
            "            BOTH hv phases anyway. The gate never reads the grant, so no\n"
            "            configuration can open it. Post-fix, both calls return False."
        )
        return 0
    print()
    print("NOT REPRODUCED: the gate consulted the grant (post-fix behaviour).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
