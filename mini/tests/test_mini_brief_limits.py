"""The limits (writer's-room tranche S1): no mandatory section is ever cut.

Regression (D8 live root shallow-b4dcb1c81ea7af2e5ecd5faa, 2026-09-06): 7 of
8 commitment briefs and 2 of 3 conjecture briefs reached the model with the
directive cut off, because the everything-so-far section's withheld notice
was not counted against its budget, the mandatory sections were not
reserved, and the call layer clips from the tail where the directive sits.
This test drives the same flow against a stub that writes long content and
asserts what the live run lacked: every brief inside the limit, every seat's
directive byte-intact.
"""

import json

import pytest

from minireason.call import MockEndpoint
from minireason.loop import Session, run
from minireason.seats import (
    COMMITMENT_DIRECTIVE,
    CONJECTURER_DIRECTIVE,
    CRITIC_DIRECTIVE,
)


def _long_endpoint(calls, *, chars=1500):
    def endpoint_fn(prompt):
        calls.append(prompt)
        n = len(calls)
        filler = ("the mechanism is asserted at length and in detail " * 40)[:chars]
        if "## target-conjecture" in prompt and "objections" in prompt.split("SYNTAX EXAMPLE", 1)[0]:
            target = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"objections": [{"about": target, "body": f"objection {n}: {filler}"}]})
        if "## target-conjecture" in prompt:
            target = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"proposals": [{"about": target, "body": f"proposal {n}: {filler}"}]})
        return json.dumps({"candidates": [
            {"content": f"conjecture {n}a: {filler}", "typicality": 0.5},
            {"content": f"conjecture {n}b: {filler[::-1]}", "typicality": 0.4},
        ]})
    return MockEndpoint(endpoint_fn)


def _directive_for(prompt):
    if "## target-conjecture" in prompt and '"objections"' in prompt.split("## problem", 1)[0]:
        return CRITIC_DIRECTIVE
    if "## target-conjecture" in prompt:
        return COMMITMENT_DIRECTIVE
    return CONJECTURER_DIRECTIVE.format(vs_k=2)


def test_every_brief_fits_and_every_directive_is_intact(tmp_path):
    """Three cycles, two long candidates a cycle, one long objection and one
    long proposal per candidate: by cycle 2 the pool is far over the compact
    limit. The record must show NO `mini:brief-clipped`, and every prompt the
    stub received must end with its seat's whole directive."""
    from minireason.compat import get_profile
    from deepreason.llm.profiles import ModelProfile

    limit = get_profile(ModelProfile.COMPACT).pack_budget() * 4
    calls: list[str] = []
    root = tmp_path / "limits"
    summary = run([("pi-0", "why does the sky look blue?")], _long_endpoint(calls),
                  budget=900_000, root=root, vs_k=2, max_cycles=3,
                  flow="mini.flow.isolation.v1")
    assert summary["cycles"] == 3 and summary["stop"] != "endpoint-error"
    session = Session(root)
    markers = [i for e in session.state.events for i in e.inputs if i.startswith("mini:brief")]
    assert markers == [], markers

    schema_free = [p.split("SYNTAX EXAMPLE", 1)[1].split("\n\n", 1)[1] for p in calls]
    over = [(i, len(b)) for i, b in enumerate(schema_free) if len(b) > limit]
    assert over == [], f"briefs over the {limit}-char limit: {over}"
    cut = [i for i, (p, b) in enumerate(zip(calls, schema_free)) if not b.rstrip().endswith(_directive_for(p))]
    assert cut == [], f"briefs whose directive is not intact: {cut} of {len(calls)}"


def test_a_flow_declared_brief_budget_wins_over_the_profile_preset(tmp_path):
    """S1b: a flow may declare the room it needs. Under a 9 000-character
    budget on the compact profile, a brief the preset would have clipped at
    4 800 reaches the stub whole, and the record carries no clip marker."""
    from minireason.flow import (
        MiniFlowV1,
        MiniStageV1,
        register_mini_flow,
        resolve_mini_flow,
    )
    from minireason.policy import MiniCommitmentPolicyV1

    base = resolve_mini_flow("mini.flow.isolation.v1")
    roomy = MiniFlowV1(
        flow_id="mini.flow.test-roomy.v1", flow_version="1.0.0",
        stages=base.stages, artifact_kinds=base.artifact_kinds,
        commitment_policy=MiniCommitmentPolicyV1(
            mandatory_skeleton_wf=False, model_authored_forbidden=False
        ),
        brief_budget_chars=9000,
    )
    try:
        register_mini_flow(roomy)
    except Exception:  # noqa: BLE001 - re-registration of the same value is refused
        pass
    calls: list[str] = []
    run([("pi-0", "why does the sky look blue?")], _long_endpoint(calls),
        budget=900_000, root=tmp_path / "roomy", vs_k=2, max_cycles=3,
        flow="mini.flow.test-roomy.v1")
    session = Session(tmp_path / "roomy")
    assert not [i for e in session.state.events for i in e.inputs if i == "mini:brief-clipped"]
    briefs = [p.split("SYNTAX EXAMPLE", 1)[1].split("\n\n", 1)[1] for p in calls]
    assert max(len(b) for b in briefs) > 4800, "the roomy flow never needed its room"
    assert all(len(b) <= 9000 for b in briefs)
    assert all(b.rstrip().endswith(_directive_for(p)) for p, b in zip(calls, briefs))


def test_a_non_positive_brief_budget_is_refused_typed():
    from minireason.flow import MiniFlowError, MiniFlowV1, resolve_mini_flow

    base = resolve_mini_flow("mini.flow.isolation.v1")
    with pytest.raises(MiniFlowError, match="MINI_FLOW_BRIEF_BUDGET_INVALID"):
        MiniFlowV1(flow_id="x", flow_version="1", stages=base.stages,
                   artifact_kinds=base.artifact_kinds, brief_budget_chars=0)
