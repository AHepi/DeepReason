"""D2 offline semantic acceptance for the opt-in conjecture controller.

The fixtures are deterministic model replies.  Their executable checks are
comparison diagnostics only: they do not participate in routing, admission,
status, or controller decisions.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from pydantic import BaseModel

from deepreason import programs
from deepreason.invariants import verify_root
from deepreason.ontology import Commitment
from deepreason.workflows.manifest_compiler import CompactDesignOutline
from deepreason.workloads.code import CodePatchCandidate
from deepreason.workloads.formal import FormalClaim
from deepreason.workloads.simulation import SimulationClaim
from deepreason.workloads.text import ReasoningEnvelopeV1
from tests.test_workflow_shadow_c0 import (
    _assert_authoritative_surfaces_equal,
    _run,
)


Validator = Callable[[str], BaseModel]


def _generic_response(*bodies: str) -> str:
    return json.dumps(
        {
            "candidates": [
                {
                    "content": body,
                    "typicality": 0.21 + index / 10,
                }
                for index, body in enumerate(bodies)
            ]
        }
    )


def _semantic_fixture(
    workload: str,
) -> tuple[str, bool, str, Validator, tuple[str, str]]:
    families = (f"{workload}-family-alpha", f"{workload}-family-beta")
    if workload == "text":
        response = json.dumps(
            {
                "candidates": [
                    {
                        "claim": f"A delayed exchange explains {family}.",
                        "mechanism": (
                            f"The {family} mechanism retains a discrepancy "
                            "until a counterfactual boundary opens."
                        ),
                        "counterconditions": [
                            f"No delayed exchange occurs for {family}."
                        ],
                        "typicality": 0.21 + index / 10,
                    }
                    for index, family in enumerate(families)
                ]
            }
        )
        return (
            "text",
            True,
            response,
            ReasoningEnvelopeV1.model_validate_json,
            families,
        )

    if workload == "code":
        bodies = tuple(
            CodePatchCandidate(
                patches=(
                    {
                        "file": "F1",
                        "anchor": "S1",
                        "replacement": f"return preserve('{family}')",
                    },
                ),
                rationale=f"Preserve identity through {family}.",
                typicality=0.21 + index / 10,
            ).model_dump_json()
            for index, family in enumerate(families)
        )
        return (
            "code",
            False,
            _generic_response(*bodies),
            CodePatchCandidate.model_validate_json,
            families,
        )

    if workload == "simulation":
        # Simulation specifications are a bounded sub-contract of the code
        # workload, so v4 intentionally freezes this run under the code profile.
        bodies = tuple(
            SimulationClaim(
                statement=f"A seeded trajectory distinguishes {family}."
            ).model_dump_json()
            for family in families
        )
        return (
            "code",
            False,
            _generic_response(*bodies),
            SimulationClaim.model_validate_json,
            families,
        )

    if workload == "proof":
        bodies = tuple(
            FormalClaim(
                statement=f"Every finite trace has a {family} normal form."
            ).model_dump_json()
            for family in families
        )
        return (
            "formal",
            False,
            _generic_response(*bodies),
            FormalClaim.model_validate_json,
            families,
        )

    if workload == "website":
        bodies = tuple(
            CompactDesignOutline(
                components=[
                    {
                        "alias": "C1",
                        "purpose": f"Reveal the archive through {family} motion.",
                    }
                ]
            ).model_dump_json()
            for family in families
        )
        return (
            "website",
            False,
            _generic_response(*bodies),
            CompactDesignOutline.model_validate_json,
            families,
        )

    raise AssertionError(f"unhandled semantic fixture: {workload}")


def _candidate_contents(run) -> tuple[str, ...]:
    return tuple(
        sorted(
            programs.content_text(artifact, run.harness.blobs)
            for artifact in run.harness.state.artifacts.values()
            if artifact.provenance.role == "conjecturer"
        )
    )


def _semantic_diagnostics(run, validator: Validator, families: tuple[str, str]):
    contents = _candidate_contents(run)
    for content in contents:
        validator(content)

    utility_check = Commitment(
        id="d2-offline-semantic-utility",
        eval=(
            f"predicate:{families[0]!r} in content or "
            f"{families[1]!r} in content"
        ),
    )
    statuses_before = dict(run.harness.state.status)
    verdicts = tuple(
        programs.evaluate(utility_check, artifact, run.harness.blobs)[0]
        for artifact in run.harness.state.artifacts.values()
        if artifact.provenance.role == "conjecturer"
    )
    assert run.harness.state.status == statuses_before
    return {
        "candidate_family_count": sum(
            any(family in content for content in contents) for family in families
        ),
        "unique_candidate_bodies": len(set(contents)),
        "verifier_backed_success": sum(
            verdict == programs.PASS for verdict in verdicts
        ),
        "candidate_count": len(verdicts),
    }


@pytest.mark.parametrize(
    "workload",
    ("text", "code", "simulation", "proof", "website"),
)
def test_active_controller_preserves_diverse_verifier_backed_semantics(
    tmp_path,
    workload,
):
    profile, reasoning, response, validator, families = _semantic_fixture(workload)
    runs = {
        mode: _run(
            tmp_path / mode,
            mode,
            response=response,
            vs_k=2,
            problem_id=f"pi-d2-{workload}",
            workload_profile=profile,
            reasoning=reasoning,
        )
        for mode in ("legacy", "shadow", "active_conjecture")
    }

    _assert_authoritative_surfaces_equal(runs["legacy"], runs["shadow"])
    assert _candidate_contents(runs["active_conjecture"]) == _candidate_contents(
        runs["legacy"]
    )
    assert runs["active_conjecture"].report == runs["legacy"].report

    diagnostics = {
        mode: _semantic_diagnostics(run, validator, families)
        for mode, run in runs.items()
    }
    assert diagnostics == {
        mode: {
            "candidate_family_count": 2,
            "unique_candidate_bodies": 2,
            "verifier_backed_success": 2,
            "candidate_count": 2,
        }
        for mode in runs
    }

    for mode in ("shadow", "active_conjecture"):
        run = runs[mode]
        assert all(
            comparison.matched
            for comparison in run.scheduler.workflow_shadow_observations
        )
        assert verify_root(
            run.harness.root,
            meter_total=run.meter.total,
        )["violations"] == []
