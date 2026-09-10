"""The solo road: one model in every seat, and a judge that stays optional.

Two operator laws meet here. The 2026-08-09 solo law ("A solo run with
everything on should be an option") requires that a one-model run can reach
status-changing criticism. The 2026-09-09 amendment ("The judge must remain
optional. One seat, two seats, no seats. The default is observe only")
requires that the judge SEAT COUNT is route topology rather than permission,
and that switching the gate says so on the record instead of failing silently.

Every test here asserts the typed record -- a warrant's kind, an attack edge, a
Measure -- never prose, and never a mock's return value.
"""

from __future__ import annotations

import json

from deepreason.config import Config
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import run_argument_trial_from_case
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_endpoints
from deepreason.ontology import (
    Commitment,
    Interface,
    Provenance,
    Status,
    WarrantType,
)
from deepreason.v6_policy import compiled_criticism_authority

_CASE = "clause 2 forbids parallel fifths and bar 3 has them"
_DEFENCE = "the fifths echo the cantus firmus deliberately"
_RULING = json.dumps({"verdict": "fail", "decisive_point": "bar 3 has them"})
_MODEL = "qwen-solo"

_SOLO = dict(
    ARGUMENTATIVE_AUTHORITY="single_family_trial",
    ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
)


def _adapter(harness, *, judge_seats: int):
    """One model in every position; the judge seat COUNT is the only variable."""

    endpoints = {
        "argumentative_critic": MockEndpoint(
            [json.dumps({"attack": True, "case": _CASE})],
            name="mock://critic", model=_MODEL,
        ),
        "defender": MockEndpoint(
            [json.dumps({"answer": _DEFENCE})],
            name="mock://defender", model=_MODEL,
        ),
    }
    if judge_seats:
        endpoints["judge"] = [
            MockEndpoint([_RULING], name=f"mock://j{seat}", model=_MODEL)
            for seat in range(judge_seats)
        ]
    return LLMAdapter(
        endpoints, harness.blobs, retry_max=2, leases=leases_from_endpoints(endpoints)
    )


def _target(harness):
    """A target no oracle can run, so only PROSE can reach a warrant against it."""

    register_standard(harness, "std-fifths", "clause 2: no parallel fifths")
    kappa = Commitment(id="k-solo", eval="rubric:std-fifths")
    harness.register_commitment(kappa)
    return harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )


def _try(harness, adapter, target, config):
    diagnostics: list = []
    critic = run_argument_trial_from_case(
        harness, adapter, config, target.id, _CASE, None,
        authority="status", critic_school_id="school-1", diagnostics=diagnostics,
    )
    return critic, diagnostics


def _measures(harness, head: str):
    return [
        list(event.inputs)
        for event in harness.log.read()
        if event.inputs and event.inputs[0] == head
    ]


# --- the road reaches a run -------------------------------------------------


def test_single_family_trial_compiles_to_the_manifests_own_word():
    """`single_family_trial` names the road the manifest calls `defended_trial`.

    The Config vocabulary and the manifest vocabulary stay two closed sets
    sharing one word -- the value is TRANSLATED at compile, never admitted to
    `CriticismPolicyV1.authority`, whose Literal `DR-INV-frozen-surfaces`
    forbids widening. Under the master gate the run asked for nothing, so it
    gets nothing.
    """

    assert compiled_criticism_authority(Config()) == "observe_only"
    assert compiled_criticism_authority(
        Config(ARGUMENTATIVE_AUTHORITY="single_family_trial")
    ) == "observe_only"
    assert compiled_criticism_authority(Config(**_SOLO)) == "defended_trial"


def test_the_engaged_knob_still_passes_through_untranslated():
    """The translation is `ARGUMENTATIVE_AUTHORITY`'s alone.

    `ENGAGED_CRITICISM_AUTHORITY`'s value-space IS the manifest field's, so a
    configuration that leaves the other knob alone must compile exactly as it
    did before the translation existed. Both directions are asserted, because
    a translation that leaked into this knob would be invisible at the default.
    """

    gate = dict(ADJUDICATION_STATUS_AUTHORITY_ENABLED=True)
    assert compiled_criticism_authority(
        Config(ENGAGED_CRITICISM_AUTHORITY="observe_only", **gate)
    ) == "observe_only"
    assert compiled_criticism_authority(
        Config(ENGAGED_CRITICISM_AUTHORITY="defended_trial", **gate)
    ) == "defended_trial"
    # Two knobs, one manifest field: the resolution is stated, not discovered.
    # A run that asked for a trial on EITHER knob asked for a trial.
    assert compiled_criticism_authority(
        Config(ENGAGED_CRITICISM_AUTHORITY="observe_only", **_SOLO)
    ) == "defended_trial"


def test_a_one_model_run_mints_an_argumentative_warrant_that_becomes_an_edge(harness):
    """The goal, asserted on the record: no warrant, no edge, no REFUTED.

    One model in every seat, two judge seats, a critic school other than the
    target's. The warrant must be ARGUMENTATIVE rather than DEMONSTRATIVE --
    the target carries a `rubric:` commitment no oracle can run, so a
    demonstrative defeat is unavailable and the refutation can only have come
    from prose (`DR-CON-warrants-and-attacks`: the chain is warrant, then
    edge, then status).
    """

    adapter = _adapter(harness, judge_seats=2)
    assert adapter.is_single_model() is True
    target = _target(harness)

    critic, _ = _try(harness, adapter, target, Config(**_SOLO))

    assert critic is not None
    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    assert warrant.type == WarrantType.ARGUMENTATIVE, warrant.type
    assert harness.state.att, "a warrant that carries no attack edge changed nothing"
    assert harness.state.status[target.id] == Status.REFUTED


def test_the_road_is_disclosed_on_the_record(harness):
    """Taking the solo road is a typed fact, not an inference from config.

    The 2026-08-28 law: switching a gate produces a typed WARNING, never
    silence. Read from the record alone, without the configuration that
    produced it.
    """

    target = _target(harness)
    _try(harness, _adapter(harness, judge_seats=2), target, Config(**_SOLO))

    assert ["trial-gate-switched", target.id, "solo-road"] in _measures(
        harness, "trial-gate-switched"
    )


def test_the_same_run_without_the_switches_discloses_nothing(harness):
    """The mutation control for the disclosure above.

    Identical fixture, identical forced trial authority, and only the two
    Config switches removed: the trial still runs and still mints, because
    this call site supplies its own authority -- but no gate was switched, so
    no gate notice may appear. Without this control the previous test could
    pass on a measure that is simply unconditional.
    """

    target = _target(harness)
    critic, _ = _try(harness, _adapter(harness, judge_seats=2), target, Config())

    assert critic is not None, "the control must differ in the DISCLOSURE only"
    assert harness.state.status[target.id] == Status.REFUTED
    assert _measures(harness, "trial-gate-switched") == []


# --- the judge stays optional: one seat, two seats, no seats ---------------


def test_no_judge_seat_declines_and_the_run_continues(harness):
    """"No seats" is a configuration, not a failure.

    The trial cannot rule without a judge, so it declines typed and the run
    carries on. Nothing raises, and no warrant is minted on the way past.
    """

    target = _target(harness)
    critic, _ = _try(harness, _adapter(harness, judge_seats=0), target, Config(**_SOLO))

    assert critic is None
    assert [m[2] for m in _measures(harness, "trial-declined")] == ["no-judge-role"]
    assert not harness.warrants


def test_one_judge_seat_declines_by_default_with_its_historical_spelling(harness):
    """Default False: byte-identical to before the switch existed.

    The decline reason keeps the spelling recorded roots compare against
    (`DR-CON-schools`, Traps: renaming a typed decline reason changes what
    those roots mean).
    """

    target = _target(harness)
    critic, _ = _try(harness, _adapter(harness, judge_seats=1), target, Config(**_SOLO))

    assert critic is None
    assert [m[2] for m in _measures(harness, "trial-declined")] == ["single-judge-seat"]
    assert not harness.warrants
    assert _measures(harness, "trial-gate-switched") == []


def test_one_judge_seat_rules_when_the_run_permits_it_and_says_so(harness):
    """"One seat" is a configuration too -- and never a silent one.

    Same fixture as the test above; the switch is the only difference. The
    seat rules, a warrant is minted, and the record carries the typed
    disclosure, because a single seat is the looser regime the amended judge
    law measures at 47-60% over-conviction.
    """

    target = _target(harness)
    critic, _ = _try(
        harness,
        _adapter(harness, judge_seats=1),
        target,
        Config(SINGLE_JUDGE_SEAT_PERMITTED=True, **_SOLO),
    )

    assert critic is not None
    assert _measures(harness, "trial-declined") == []
    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    assert warrant.type == WarrantType.ARGUMENTATIVE
    assert harness.state.status[target.id] == Status.REFUTED
    assert ["trial-gate-switched", target.id, "single-judge-seat"] in _measures(
        harness, "trial-gate-switched"
    )


def test_the_switch_cannot_conjure_a_seat_that_is_not_there(harness):
    """Zero seats never consults the switch: nothing can rule nothing.

    The shape asserted here is the one that would otherwise CRASH rather than
    decline -- a judge ROLE that is configured with an empty seat list. The
    role check upstream passes (the role exists), the seat count is zero, and
    `_judge_all` would dispatch seat 0 into an empty ensemble. So the count
    guard is load-bearing, not defensive: without it, "the judge is optional"
    would read as "the judge is dispensable" and a run would die where it
    should decline.
    """

    adapter = _adapter(harness, judge_seats=0)
    adapter.endpoints["judge"] = []  # role present, ensemble empty
    assert adapter.has_role("judge") is True
    assert adapter.judge_seats() == ()

    target = _target(harness)
    critic, _ = _try(
        harness, adapter, target, Config(SINGLE_JUDGE_SEAT_PERMITTED=True, **_SOLO)
    )

    assert critic is None
    assert [m[2] for m in _measures(harness, "trial-declined")] == ["single-judge-seat"]
    assert not harness.warrants
    assert _measures(harness, "trial-gate-switched") == []


def test_the_default_is_observe_only_at_every_seat_count(tmp_path):
    """"The default is observe only" -- asserted at all three seat counts.

    Driven through the ordinary criticism rule with a default `Config`, not
    through the trial with a forced authority, because "the default" is a
    claim about what a run that configures NOTHING does. The case is still
    recorded as scrutiny; what must not appear is a warrant, an edge, or a
    status change -- whatever the judge topology. This is the assertion that
    would catch the new switch being wired to the wrong default.
    """

    from deepreason.harness import Harness
    from deepreason.rules.crit import crit_argumentative

    for seats in (0, 1, 2):
        run = Harness(tmp_path / f"observe-{seats}")
        target = _target(run)
        critic = crit_argumentative(
            run, target.id, _adapter(run, judge_seats=seats), Config()
        )
        assert critic is not None, seats  # scrutiny is still recorded
        assert not run.warrants, seats
        assert not run.state.att, seats
        assert run.state.status[target.id] == Status.ACCEPTED, seats


def test_a_permitted_lone_seat_that_never_ruled_discloses_nothing(harness):
    """A gate notice must mean the trial RAN that way, not that it could have.

    One judge seat, the switch on, and a critic from the target's own school:
    the trial declines `same-school-critic` and the lone seat never rules. An
    earlier draft of this fix recorded the disclosure at the seat check, which
    stamped "a lone seat ruled" on trials that went on to decline for an
    unrelated reason -- a record that says something the run did not do is
    worse than one that says nothing.
    """

    target = _target(harness)  # authored by school-0
    diagnostics: list = []
    critic = run_argument_trial_from_case(
        harness, _adapter(harness, judge_seats=1), Config(
            SINGLE_JUDGE_SEAT_PERMITTED=True, **_SOLO
        ),
        target.id, _CASE, None, authority="status",
        critic_school_id="school-0", diagnostics=diagnostics,
    )

    assert critic is None
    assert [m[2] for m in _measures(harness, "trial-declined")] == ["same-school-critic"]
    assert _measures(harness, "trial-gate-switched") == []


# --- the frozen surfaces this tranche was granted contact with -------------


def test_the_granted_contact_moves_no_digest():
    """The grant's own condition: insertions only, and digests PRESERVED.

    `SINGLE_JUDGE_SEAT_PERMITTED` joins the judge-knob block in
    `_versioned_source_config_data`, so a default Config's source hash is
    unchanged at every schema version and the shipped fixture's qualification
    subject digest does not move -- no home requalifies for this tranche. The
    values are the ones measured before the pop line was added.
    """

    from deepreason.qualification import qualification_subject_digest
    from deepreason.run_manifest import source_config_hash
    from tests.test_reusable_qualification import _manifest, _profile

    hashes = [source_config_hash(Config(), schema_version=v) for v in (1, 2, 3, 4, 5, 6)]
    assert hashes[0] == hashes[1] == (
        "6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81"
    )
    assert hashes[2] == hashes[3] == hashes[4] == hashes[5] == (
        "2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5"
    )

    profile = _profile()
    assert qualification_subject_digest(_manifest(profile), profile) == (
        "02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713"
    )


def test_route_fingerprint_did_not_move():
    """The frozen-ADJACENT surface the grant did NOT cover.

    Recorded roots depend on this serialization exactly, and no part of this
    tranche may change it. Asserted over a fixed route rather than by reading
    the diff.
    """

    from deepreason.llm.firewall import Route, route_fingerprint

    route = Route(
        endpoint_id="ep", base_url="https://models.invalid/v1", model_id="m",
        provider="p", family="f",
    )
    assert route_fingerprint(route) == (
        "e00efa5d5990b5dea61dba75b88c1a62cbc60b9639d77844dd8c551128223a78"
    )
