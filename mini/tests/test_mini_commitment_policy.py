"""Cycles that run with commitments disabled, and say so.

Implements S3 (R3, C10) of the mini isolation programme. R3 is the operator's
own "it needs to run its full conjecture/criticism cycles with commitments
disabled".

WHY R2 AND R3 ARE ONE CHANGE. Relaxing the FORM buys nothing on its own: free
prose already passes the shipped wire schema, because `content` is just a
string. What refutes it is the mandatory `skeleton-wf` commitment, compiled
onto every candidate and executed on arrival. So a run with relaxed forms and
the default commitment policy admits every candidate and refutes every one of
them, and the problem is dry in a few cycles with nothing to show. The first
test below is that measurement, committed.

C10 is the other half: "Gates are always optional: with warnings" (operator,
2026-08-28). Switching a channel off must produce a typed WARNING in the
record -- never a refusal, and never silence.
"""

import json

import pytest

from minireason.call import MockEndpoint
from minireason.log import replay
from minireason.loop import Session, run


_PROSE = (
    "Sunlight scatters off molecules much smaller than its wavelength, and the "
    "short-wavelength end scatters far more strongly. I am not at all sure how "
    "to state that as a mechanism with forbidden cases, and I would rather say "
    "the interesting part than force it into a shape."
)


def _prose_endpoint(n_per_cycle: int = 2):
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": f"{_PROSE} (variation {calls['n']}.{i})",
                        "typicality": 0.5,
                    }
                    for i in range(n_per_cycle)
                ]
            }
        )

    return MockEndpoint(endpoint_fn)


def test_free_prose_is_refuted_on_arrival_under_the_default_policy(tmp_path):
    """The BEFORE, committed as a test rather than left in a proof file.

    Reproduces `experiments/2026-09-05-change-mini-isolation-programme/proof/
    m2_free_prose_today.txt`: every candidate admitted, every candidate
    refuted, zero survivors. This is what R2 alone produces, and it is why R3
    is not a separate wish.
    """
    from minireason.checks import compile_checks, run_checks

    compiled = compile_checks(_PROSE)
    assert [c["id"] for c in compiled] == ["skeleton-wf"]
    failures = run_checks(_PROSE, compiled)
    assert [f["verdict"] for f in failures] == ["fail"]
    assert "does not parse as a skeleton" in failures[0]["error"]

    root = tmp_path / "before"
    summary = run(
        [("pi-0", "why does the sky look blue?")],
        _prose_endpoint(),
        budget=200_000,
        root=root,
        max_cycles=3,
    )
    assert summary["refuted"] > 0
    assert Session(root).survivors("pi-0") == []


def test_with_both_channels_off_free_prose_survives(tmp_path):
    """R3: the cycles run, and what they produce is not destroyed on arrival."""
    from minireason.policy import MiniCommitmentPolicyV1

    off = MiniCommitmentPolicyV1(
        mandatory_skeleton_wf=False, model_authored_forbidden=False
    )
    root = tmp_path / "off"
    summary = run(
        [("pi-0", "why does the sky look blue?")],
        _prose_endpoint(),
        budget=200_000,
        root=root,
        max_cycles=3,
        commitment_policy=off,
    )
    assert summary["refuted"] == 0, summary
    assert len(Session(root).survivors("pi-0")) >= 1, summary
    # The record still replays: relaxing a policy is not relaxing the record.
    assert replay(root).digest() == Session(root).state.digest()


def test_the_default_policy_is_unchanged(tmp_path):
    """C1/C4: nothing changes for a caller that selects nothing."""
    from minireason.checks import compile_checks
    from minireason.policy import MiniCommitmentPolicyV1

    default = MiniCommitmentPolicyV1()
    assert default.mandatory_skeleton_wf is True
    assert default.model_authored_forbidden is True
    assert compile_checks(_PROSE) == compile_checks(_PROSE, policy=default)
    assert [c["id"] for c in compile_checks(_PROSE)] == ["skeleton-wf"]


def test_each_channel_switches_independently():
    """Two switches, not one: the operator can restore either.

    The model-authored channel is the candidate's own `forbidden[]`; the
    mandatory one is the well-formedness commitment compiled onto everything.
    A reading of R3 that collapses them would leave no way back from either.
    """
    from minireason.checks import compile_checks
    from minireason.policy import MiniCommitmentPolicyV1

    skeleton = json.dumps(
        {
            "claim": "short wavelengths scatter more",
            "mechanism": "Rayleigh scattering",
            "forbidden": [
                {"case": "must state a mechanism", "eval": "program:json-wf"}
            ],
        }
    )
    both_on = [c["id"] for c in compile_checks(skeleton)]
    assert both_on[0] == "skeleton-wf" and len(both_on) == 2

    no_mandatory = compile_checks(
        skeleton, policy=MiniCommitmentPolicyV1(mandatory_skeleton_wf=False)
    )
    assert [c["id"] for c in no_mandatory] == both_on[1:]

    no_authored = compile_checks(
        skeleton, policy=MiniCommitmentPolicyV1(model_authored_forbidden=False)
    )
    assert [c["id"] for c in no_authored] == ["skeleton-wf"]

    assert (
        compile_checks(
            skeleton,
            policy=MiniCommitmentPolicyV1(
                mandatory_skeleton_wf=False, model_authored_forbidden=False
            ),
        )
        == []
    )


def test_switching_a_channel_off_writes_a_typed_warning_into_the_record(tmp_path):
    """C10: a gate switched off produces a typed WARNING, never a refusal and
    NEVER SILENCE.

    The warning is in the run's own record, not only in a return value: a
    reader opening the root months later must be able to see that these cycles
    ran without the checks, and which ones.
    """
    from minireason.policy import MiniCommitmentPolicyV1

    root = tmp_path / "warned"
    run(
        [("pi-0", "why does the sky look blue?")],
        _prose_endpoint(),
        budget=200_000,
        root=root,
        max_cycles=2,
        commitment_policy=MiniCommitmentPolicyV1(
            mandatory_skeleton_wf=False, model_authored_forbidden=False
        ),
    )

    warnings = [
        event
        for event in replay(root).events
        if any(
            marker.startswith("mini:commitments-disabled") for marker in event.inputs
        )
    ]
    assert warnings, "a gate switched off in silence is the failure C10 names"
    named = " ".join(marker for event in warnings for marker in event.inputs)
    assert "skeleton" in named and "forbidden" in named, named


def test_a_run_with_the_default_policy_writes_no_warning(tmp_path):
    """The warning means something only if its absence does too."""
    root = tmp_path / "quiet"
    run(
        [("pi-0", "why does the sky look blue?")],
        _prose_endpoint(),
        budget=200_000,
        root=root,
        max_cycles=2,
    )
    assert not [
        event
        for event in replay(root).events
        if any(
            marker.startswith("mini:commitments-disabled") for marker in event.inputs
        )
    ]
