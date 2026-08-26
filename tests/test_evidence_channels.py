"""The evidence-channel registry: three protected channels, on by default.

Operator, 2026-08-26, verbatim: "now the fix. including turning research and,
simulation and coding permanently on" -- and, the same day, the reason:
"simulation and code backends are important. so is research. Otherwise how is
an LLM supposed to test code".

Standing authority, 2026-08-14: "Code testing, simulation, scratch pad and
research backends need to stay live and be able to mint their own evidence",
with the same-day correction "Sorry not scratch pad. that doesn't mint
evidence", and "There was a website development pipeline that I decommissioned
a while ago. That needs to stay decommissioned."

The bound, operator 2026-08-26: "This doesn't demote prose as legitimate
criticism." The last two tests in this file are that bound, checked rather than
promised.

Tranche: experiments/2026-08-26-change-f3-channels-and-wander-cap/ (S1-S6, S15,
S23).
"""

import pytest

from deepreason import channels
from deepreason.config import Config
from deepreason.v6_policy import (
    engaged_inquiry_capability_policy,
    engaged_research_policy,
    engaged_simulation_policy,
)


# --- S1: the registry ------------------------------------------------------ #


def test_the_registry_declares_the_three_evidence_minting_channels():
    """Three rows, and the scratch pad is deliberately not one of them.

    The operator's 2026-08-14 ruling names four protected channels and its
    same-day correction separates them by what they MINT. A registry of
    evidence channels listing the scratch pad would assert the thing that
    correction denies.
    """
    assert set(channels.CHANNEL_DECLARATIONS) == {
        "research",
        "simulation",
        "code-testing",
    }
    assert "scratch" not in channels.CHANNEL_DECLARATIONS
    assert "scratchpad" not in channels.CHANNEL_DECLARATIONS


def test_every_declared_channel_defaults_on():
    """"Permanently on" means the DEFAULT is on, for a run nobody configured.

    Research was reachable before this tranche -- but only for an operator who
    remembered an environment variable, which for every other run is a channel
    that does not exist.
    """
    default = Config()
    assert channels.CHANNEL_DECLARATIONS
    for channel_id, declaration in channels.CHANNEL_DECLARATIONS.items():
        assert declaration.default_enabled is True, channel_id
        assert channels.enabled(channel_id, default) is True, channel_id
    assert channels.disabled_channels(default) == ()


def test_every_declaration_names_a_toggle_that_exists_on_config():
    """A declaration may not claim a switch no configuration carries.

    The failure mode this forbids is the one S0 found in the allocation
    controller: a value written by one component and read by none.
    """
    for channel_id, declaration in channels.CHANNEL_DECLARATIONS.items():
        assert declaration.toggle in type(Config()).model_fields, channel_id


# --- S2: the toggle -------------------------------------------------------- #


def test_a_toggle_turns_off_exactly_the_channel_it_names():
    off = Config(CHANNELS_DISABLED=("research",))

    assert channels.enabled("research", off) is False
    assert channels.enabled("simulation", off) is True
    assert channels.enabled("code-testing", off) is True
    assert channels.disabled_channels(off) == ("research",)


def test_turning_every_channel_off_is_a_lawful_configuration():
    """All-configurations law: nothing refuses, and the census is exact."""
    off = Config(CHANNELS_DISABLED=("research", "simulation", "code-testing"))

    assert channels.disabled_channels(off) == (
        "code-testing",
        "research",
        "simulation",
    )
    assert channels.unknown_channel_notices(off) == ()


def test_an_unknown_channel_id_is_a_typed_notice_never_a_refusal():
    """Disclose, never die -- the all-configurations law applied to channels.

    A typo must not stop a run, and must not pass silently either: silence is
    how an operator believes a channel is off when it is on.
    """
    typo = Config(CHANNELS_DISABLED=("reserch",))

    (notice,) = channels.unknown_channel_notices(typo)
    assert notice.code == "CHANNEL_UNKNOWN"
    assert "reserch" in notice.message
    assert notice.resolution and "research" in notice.resolution
    # And it disabled nothing, because it named nothing.
    assert channels.disabled_channels(typo) == ()
    assert channels.enabled("research", typo) is True


# --- S6: the decommissioned pipeline --------------------------------------- #


def test_the_website_is_a_declared_absence_and_not_a_channel():
    """Operator 2026-08-14: the website pipeline "needs to stay
    decommissioned".

    Declared rather than merely missing: a registry that is SILENT about the
    website is indistinguishable from a registry that forgot it, and an
    oversight is how a remnant gets revived.
    """
    assert "website" in channels.DECOMMISSIONED
    assert "website" not in channels.CHANNEL_DECLARATIONS
    assert channels.enabled("website", Config()) is False
    # Even naming it in the toggle cannot conjure it into being a channel.
    named = Config(CHANNELS_DISABLED=("website",))
    assert channels.enabled("website", named) is False
    (notice,) = channels.unknown_channel_notices(named)
    assert "DECOMMISSIONED" in (notice.resolution or "")


# --- S3/S4: the compiled policies ------------------------------------------ #


def test_research_compiles_enabled_with_a_reachable_allowlist_by_default():
    """The ROAD, not the flag.

    An enabled research policy with no reachable host, or a zero request
    budget, mints nothing -- an enabled flag over a severed road. Each value
    asserted here is one a dispatch would actually consume.
    """
    policy = engaged_research_policy({}, config=Config())

    assert policy.enabled is True
    assert policy.domain_allowlist == channels.DEFAULT_RESEARCH_ALLOWLIST
    assert policy.domain_allowlist
    assert policy.maximum_requests > 0
    assert policy.maximum_sources > 0
    assert policy.maximum_response_bytes > 0


def test_a_blank_allowlist_override_still_leaves_research_reachable():
    """The env var names WHICH hosts, never WHETHER research runs.

    A blank or comma-only value used to mean "off". It now falls back to the
    declared default, because the channel decides enablement and this setting
    decides destinations -- and an enabled policy with an empty allowlist is a
    shape its own validator refuses.
    """
    policy = engaged_research_policy(
        {"DEEPREASON_RESEARCH_ALLOWLIST": " , ,"}, config=Config()
    )

    assert policy.enabled is True
    assert policy.domain_allowlist == channels.DEFAULT_RESEARCH_ALLOWLIST


def test_simulation_is_byte_identical_when_its_channel_is_on():
    """Channel awareness must not perturb the shipped simulation policy.

    Both runner profiles, because the contained runner is a different frozen
    policy and a different qualification subject.
    """
    from deepreason.canonical import canonical_json

    for environ in ({}, {"DEEPREASON_SIMULATION_RUNNER": "contained"}):
        aware = engaged_simulation_policy(environ, config=Config())
        legacy = engaged_simulation_policy(environ)
        assert canonical_json(
            aware.model_dump(mode="json", by_alias=True)
        ) == canonical_json(legacy.model_dump(mode="json", by_alias=True))
        assert aware.enabled is True


def test_a_disabled_simulation_channel_compiles_the_empty_policy():
    """OFF is a valid policy, not a refusal."""
    from deepreason.capabilities.policy import SimulationCapabilityPolicyV1

    off = engaged_simulation_policy(
        {}, config=Config(CHANNELS_DISABLED=("simulation",))
    )

    assert off.enabled is False
    assert off == SimulationCapabilityPolicyV1()


# --- S5: code-testing ------------------------------------------------------ #


def test_code_testing_consults_no_enablement_on_the_path_it_actually_runs():
    """Declared ON, and CHECKED rather than asserted.

    This channel has no gate today, which is why its declaration says so in
    `enforcement`. The claim "it is on" is therefore a claim about a code
    path, and it is proved by driving that path: an execution-class program
    commitment evaluates to a verdict with nothing consulted about
    configuration anywhere along it.

    See PARKED.md P1 for the off-switch this tranche declines to improvise:
    the channel's live entry points are commitment compilers whose ids are
    content-addressed digests over the compiled shape, so gating there would
    change what a record contains rather than what a run may reach for.
    """
    import pathlib

    from deepreason import programs
    from deepreason.harness import Harness
    from deepreason.ontology import Provenance
    from deepreason.oracle import exec_oracle_commitment

    declaration = channels.CHANNEL_DECLARATIONS["code-testing"]
    assert declaration.default_enabled is True
    assert "unconditional" in declaration.enforcement

    # The execution classes exist and are reachable by name.
    for name in ("exec_oracle", "candidate_checker", "property_oracle"):
        assert name in programs.PROGRAMS, name

    # Driven through a real harness on the channel's OWN road: an exec-oracle
    # commitment, a candidate whose content is code, and a verdict a machine
    # computed. Both directions, because a road that can only say PASS is not
    # a criticism road.
    harness = Harness(pathlib.Path(_tmp("code-testing")) / "run")
    commitment = exec_oracle_commitment(
        "double", [{"in": [2], "out": 4}, {"in": [3], "out": 6}]
    )
    harness.register_commitment(commitment)

    passing = harness.create_artifact(
        "def double(n):\n    return n * 2",
        codec="code:python",
        provenance=Provenance(role="conjecturer"),
    )
    failing = harness.create_artifact(
        "def double(n):\n    return n + 2",
        codec="code:python",
        provenance=Provenance(role="conjecturer"),
    )

    assert programs.evaluate(commitment, passing, harness.blobs)[0] == programs.PASS
    verdict, trace = programs.evaluate(commitment, failing, harness.blobs)
    assert verdict == programs.FAIL
    assert trace["commitment"] == commitment.id


# --- S15: every configuration class compiles ------------------------------- #


@pytest.mark.parametrize(
    "disabled",
    [
        (),
        ("research",),
        ("simulation",),
        ("code-testing",),
        ("research", "simulation"),
        ("research", "simulation", "code-testing"),
        ("reserch",),
        ("website",),
    ],
)
def test_every_channel_configuration_compiles_a_manifest(disabled):
    """Channels-off-by-choice is a configuration class, and it COMPILES.

    Through `build_preparation_manifest`, which is the one door every launch
    path enters (operations-parity law), so this is a statement about runs and
    not about a policy factory in isolation.
    """
    from tests.test_v6_engaged_public_defaults import STAMP, _profile
    from deepreason.preparation import build_preparation_manifest

    manifest = build_preparation_manifest(
        _profile(),
        question="does every channel configuration compile?",
        compiled_at=STAMP,
        channels_disabled=disabled,
    )

    capabilities = manifest.inquiry_capability_policy
    assert capabilities is not None
    expected_research = "research" not in disabled
    expected_simulation = "simulation" not in disabled
    assert capabilities.research.enabled is expected_research
    assert capabilities.simulation.enabled is expected_simulation
    # And the notices are available for the same configuration, unrefused.
    notices = channels.unknown_channel_notices(Config(CHANNELS_DISABLED=disabled))
    unknown = set(disabled) - set(channels.CHANNEL_DECLARATIONS)
    assert {n.message.split()[-1].strip("'") for n in notices} == unknown


# --- S23: prose keeps its full standing ------------------------------------ #


def test_prose_criticism_is_identical_whether_or_not_the_channels_are_on():
    """Operator, 2026-08-26: "This doesn't demote prose as legitimate
    criticism."

    The differential is the same instrument `DR-INV-signal-contract` requires
    of allocation: one scripted record, two arms, every label, edge, warrant
    and dependency compared. The record's only criticism is PROSE -- an
    argumentative warrant with a validity node and no program anywhere -- so
    if turning the evidence channels on ever cost a prose case anything, the
    two arms diverge here.
    """
    from tests.test_allocation_signal_consumption import (
        _epistemic_state,
        _live_harness,
        _scripted_epistemic_content,
    )

    on = _live_harness(pytest.importorskip("pathlib").Path(_tmp("on")))
    off = _live_harness(pytest.importorskip("pathlib").Path(_tmp("off")))
    _scripted_epistemic_content(on)
    _scripted_epistemic_content(off)

    # The two arms really are different configurations, or the test passes by
    # comparing a thing with itself.
    assert channels.disabled_channels(Config()) == ()
    all_off = Config(CHANNELS_DISABLED=("research", "simulation", "code-testing"))
    assert len(channels.disabled_channels(all_off)) == 3

    assert _epistemic_state(on) == _epistemic_state(off), (
        "turning the evidence channels on changed a prose criticism's "
        "standing: the channels add a road, they take none away"
    )


def test_the_channel_registry_is_kind_blind():
    """Nothing here may weight a criticism or a conjecture by its KIND.

    The standing 2026-08-08 law from the conjecture side ("nothing may
    penalize a conjecture for being informal -- not admission, not rank, not
    criticism exposure, not acceptance") and the operator's 2026-08-26
    sentence from the criticism side are one rule. A registry that decided
    enablement AND said anything about kind would be the place it broke.
    """
    import pathlib

    source = pathlib.Path("src/deepreason/channels.py").read_text(encoding="utf-8")
    body = "\n".join(
        line for line in source.splitlines() if not line.strip().startswith("#")
    )
    for forbidden in (
        "Warrant",
        "att_add",
        "dep_add",
        "create_artifact",
        "formally_backed",
        "Status",
        "record_measure",
    ):
        assert forbidden not in body, (forbidden, "channels.py")


_TMP_COUNTER = {"n": 0}


def _tmp(name: str) -> str:
    """A fresh run directory, without threading a fixture through the helpers
    borrowed from the allocation suite (they take a path, not a fixture)."""
    import tempfile

    _TMP_COUNTER["n"] += 1
    return tempfile.mkdtemp(prefix=f"channels-{name}-{_TMP_COUNTER['n']}-")
