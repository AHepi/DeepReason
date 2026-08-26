"""The architecture tests for F3's two halves.

Operator design law, 2026-08-26 (CLAUDE.md), verbatim: "There needs to be a
priority that enforces modularity. Customisation needs to be easy." Bound to
this tranche in the operator's own words:

    F3: you are closest to compliant already -- the wander cap is a policy
    artifact and the channels are config defaults; add the architecture test
    that a channel toggle and a floor change are pure configuration, and
    strike-or-emit the phantom signals so the registry never lies about what
    is customizable.

and, for the road:

    the H1 architecture test should cover that the road exists in every launch
    path, not merely that the flags default true.

"A modularity claim without a failable check is decoration." Every test below
is written to go RED on the BYPASS it names, not on a rename.

Tranche: experiments/2026-08-26-change-f3-channels-and-wander-cap/ (S17, S22).
"""

import inspect
import pathlib

import pytest

from deepreason import allocation, channels, wander
from deepreason.config import Config


# --- 1: a channel toggle is pure configuration ----------------------------- #


def test_a_channel_toggle_is_pure_configuration():
    """Two Config values, two compiled topologies, no source edit anywhere.

    The bypass this forbids: a channel whose OFF state needs a code change, an
    environment variable a Config cannot express, or a second knob per channel.
    """
    from deepreason.v6_policy import engaged_inquiry_capability_policy

    on = engaged_inquiry_capability_policy({}, config=Config())
    off = engaged_inquiry_capability_policy(
        {}, config=Config(CHANNELS_DISABLED=("research", "simulation"))
    )

    assert on.research.enabled is True and on.simulation.enabled is True
    assert off.research.enabled is False and off.simulation.enabled is False
    assert on.digest != off.digest

    # ONE field serves every channel, present and future. A second would mean a
    # new channel costs a knob, and every knob moves a qualification subject.
    assert len({d.toggle for d in channels.CHANNEL_DECLARATIONS.values()}) == 1
    assert channels.CHANNEL_TOGGLE_FIELD in type(Config()).model_fields


def test_a_new_channel_would_need_no_new_config_field():
    """The registry, not the schema, is where a channel is added.

    Proved by asking the registry a question about an id it has never seen:
    the toggle path is keyed by STRING, so a row added tomorrow is toggleable
    the moment it exists.
    """
    hypothetical = "a-channel-nobody-has-written-yet"
    assert hypothetical not in channels.CHANNEL_DECLARATIONS

    named = Config(CHANNELS_DISABLED=(hypothetical,))
    # It is not enabled (it does not exist) and naming it refuses nothing.
    assert channels.enabled(hypothetical, named) is False
    assert len(channels.unknown_channel_notices(named)) == 1
    # And every real channel is unaffected by the presence of a stranger.
    assert channels.disabled_channels(named) == ()


# --- 2: a floor change is pure configuration ------------------------------- #


def test_a_floor_change_is_pure_configuration():
    """Two Config values, two decisions, no source edit."""
    strict = Config(SEED_PROBLEM_BUDGET_FLOOR=0.9)
    loose = Config(SEED_PROBLEM_BUDGET_FLOOR=0.1)

    def decide(config):
        return wander.decide(
            config, wander.reading_from(config, cycles=10, seed_worked=4)
        )

    assert decide(strict).engaged is True
    assert decide(loose).engaged is False
    assert decide(strict).floor == 0.9


def test_a_different_throttle_is_a_configuration_not_a_code_edit():
    """The VERSIONED registry: selection by id, from Config.

    The bypass this forbids: a second throttle that a consumer has to be
    taught about, or a policy reachable only by editing the module that runs
    it.
    """
    reading = wander.LineageReading(
        cycles=10, seed_worked=1, other_worked=9, floor=0.5
    )

    assert len(wander.LINEAGE_POLICIES) >= 2
    for policy_id in wander.LINEAGE_POLICIES:
        decision = wander.decide(
            Config(ATTENTION_ALLOCATION_POLICY=policy_id), reading
        )
        assert decision.policy_id == policy_id, policy_id
        assert decision.fallback_from is None, policy_id

    assert Config().ATTENTION_ALLOCATION_POLICY in wander.LINEAGE_POLICIES


# --- 3: the consumer reads the interface and nothing else ------------------ #


def test_the_scheduler_consumes_only_the_wander_interface():
    """RED on the bypass: a scheduler that names a policy implementation.

    A consumer taught which throttle it is running would have to be EDITED to
    run a different one, which is precisely the coupling the registry exists
    to prevent. The operator priced this fork and chose the interface.
    """
    from deepreason.scheduler.scheduler import Scheduler

    source = inspect.getsource(Scheduler)
    # Comments may NAME the registry -- the point of a comment is to say where
    # the thing lives. What must not appear is a reference the interpreter
    # follows, so the census is over code.
    code = "\n".join(
        line for line in source.splitlines() if not line.strip().startswith("#")
    )

    assert "wander.decide(" in code
    assert "wander.reading_from(" in code
    for implementation in ("wander_cap_v1", "open_lineage_v1", "LINEAGE_POLICIES"):
        assert implementation not in code, implementation


def test_the_wander_policy_module_imports_no_subsystem():
    """The other side of the same boundary.

    `INV-signal-contract` requires the allocation controller to consume only
    the signal interface. A policy module is stricter still: it takes numbers
    and returns a decision, so it needs nothing from `deepreason` at all --
    and a policy that imported one could read a subsystem instead of a signal.
    """
    source = pathlib.Path("src/deepreason/wander.py").read_text(encoding="utf-8")
    body = "\n".join(
        line for line in source.splitlines() if not line.strip().startswith("#")
    )

    assert "from deepreason" not in body
    assert "import deepreason" not in body


# --- 4: every declaration names something that exists ---------------------- #


def test_every_declaration_and_policy_id_is_reachable_from_config():
    """A registry may not promise a customization point that does not exist.

    Both halves: every channel's toggle must be a real Config field, and every
    registered policy id must be selectable through the real Config field that
    selects one.
    """
    fields = type(Config()).model_fields

    for channel_id, declaration in channels.CHANNEL_DECLARATIONS.items():
        assert declaration.toggle in fields, (channel_id, declaration.toggle)

    assert "ATTENTION_ALLOCATION_POLICY" in fields
    assert "SEED_PROBLEM_BUDGET_FLOOR" in fields
    for policy_id in wander.LINEAGE_POLICIES:
        assert Config(ATTENTION_ALLOCATION_POLICY=policy_id)


# --- 5: the signal pair, never half of it ---------------------------------- #


def test_every_wander_signal_is_declared_and_has_a_producer():
    """The declaration is a PAIR: a registry row and a producer predicate.

    Adding a name to `POLICY_SIGNALS` without its `_PRODUCERS` entry raises
    KeyError inside `open_loop_signals` -- loudly, on purpose -- and this test
    is what makes that loudness arrive in the gate rather than in a run.
    """
    from deepreason.signals import declaration

    for name in wander.SIGNALS:
        assert name in allocation.POLICY_SIGNALS, name
        declared = declaration(name)
        assert declared is not None, name
        assert declared.unit != "unspecified", name
        assert declared.staleness != "unspecified", name

    # The census ANSWERS for both -- and answers "closed" for any topology that
    # binds a seat at all, because the reading is over problem selection rather
    # than over a seat's output. A run that reaches cycle 1 can always produce
    # them, so neither may ever be reported as an open loop.
    for topology in (
        {"conjecturer": object()},
        {"conjecturer": object(), "argumentative_critic": object()},
    ):
        open_loops = allocation.open_loop_signals(topology)
        assert not set(wander.SIGNALS) & set(open_loops), open_loops
    # The one signal a seatless topology genuinely cannot produce still says so,
    # which is what shows the census above is discriminating rather than empty.
    assert set(wander.SIGNALS) <= set(allocation.open_loop_signals({}))
    assert set(wander.SIGNALS) <= set(allocation.POLICY_SIGNALS)


# --- 6 (S22): the ROAD exists in every launch path ------------------------- #


def _profile():
    from tests.test_v6_engaged_public_defaults import _profile as profile

    return profile()


def _manifests():
    """One compiled manifest per launch path.

    The operations-parity law (2026-08-13) says there is ONE run path -- every
    configuration enters through `start_manifest_run` -- so "every launch path"
    is every entry that COMPILES a manifest into it. Two shapes exist: an
    in-memory preparation (the managed `deepreason reason` and every ladder),
    and a precompiled manifest serialized to disk and loaded back
    (`deepreason run --run-manifest`).
    """
    import json
    import tempfile

    from deepreason.preparation import build_preparation_manifest
    from deepreason.run_manifest import load_run_manifest
    from tests.test_v6_engaged_public_defaults import STAMP

    prepared = build_preparation_manifest(
        _profile(),
        question="does the road exist in every launch path?",
        compiled_at=STAMP,
    )
    root = pathlib.Path(tempfile.mkdtemp(prefix="road-"))
    path = root / "run-manifest.json"
    path.write_text(
        json.dumps(prepared.model_dump(mode="json", by_alias=True)),
        encoding="utf-8",
    )
    return {"prepared": prepared, "precompiled": load_run_manifest(path)}


@pytest.mark.parametrize("launch_path", ["prepared", "precompiled"])
def test_the_research_road_exists_in_every_launch_path(launch_path):
    """Not the flag: the values a dispatch would actually consume.

    A default of True over a severed road is exactly the failure S0 found in
    the allocation controller -- 47 decisions written to a field nothing read.
    An enabled research policy with no reachable host, or a zero request
    budget, is the same failure wearing an enabled flag.
    """
    policy = _manifests()[launch_path].inquiry_capability_policy.research

    assert policy.enabled is True
    assert policy.domain_allowlist, "enabled research with no reachable host"
    assert policy.maximum_requests > 0
    assert policy.maximum_sources > 0
    assert policy.maximum_response_bytes > 0
    assert policy.backend_identity != "disabled"


@pytest.mark.parametrize("launch_path", ["prepared", "precompiled"])
def test_the_simulation_road_exists_in_every_launch_path(launch_path, tmp_path):
    """The controller CONSTRUCTS against the compiled manifest.

    `SimulationCapabilityController` "refuses to exist without one", so
    construction is the road's first real gate -- a stronger statement than
    reading `enabled` off the policy, because it exercises the agreement
    between the policy, the toolchain pin and the controller.
    """
    from deepreason.capabilities.simulation import SimulationCapabilityController
    from deepreason.harness import Harness

    manifest = _manifests()[launch_path]
    policy = manifest.inquiry_capability_policy.simulation

    assert policy.enabled is True
    assert policy.maximum_simulation_requests > 0
    assert policy.maximum_simulation_executions > 0
    assert policy.maximum_proposals_per_turn > 0
    assert manifest.toolchains
    assert policy.python_toolchain_identity in {t.id for t in manifest.toolchains}

    harness = Harness(tmp_path / f"sim-{launch_path}")
    controller = SimulationCapabilityController(harness, manifest)
    assert controller is not None


def test_the_code_testing_road_reaches_a_machine_verdict(tmp_path):
    """The channel with no flag at all, proved by driving it end to end.

    Both directions, because a road that can only say PASS is not a criticism
    road. This is the road the operator's own question names: "Otherwise how
    is an LLM supposed to test code".
    """
    from deepreason import programs
    from deepreason.harness import Harness
    from deepreason.ontology import Provenance
    from deepreason.oracle import exec_oracle_commitment

    harness = Harness(tmp_path / "code-testing")
    commitment = exec_oracle_commitment(
        "solve", [{"in": [2], "out": 4}, {"in": [5], "out": 10}]
    )
    harness.register_commitment(commitment)

    right = harness.create_artifact(
        "def solve(x):\n    return x * 2",
        codec="code:python",
        provenance=Provenance(role="conjecturer"),
    )
    wrong = harness.create_artifact(
        "def solve(x):\n    return x + 2",
        codec="code:python",
        provenance=Provenance(role="conjecturer"),
    )

    assert programs.evaluate(commitment, right, harness.blobs)[0] == programs.PASS
    assert programs.evaluate(commitment, wrong, harness.blobs)[0] == programs.FAIL


def test_the_road_tests_would_fail_on_a_severed_road():
    """The failability statement, as a check rather than a claim in a
    docstring.

    Each road assertion above names a value a consumer reads. This test proves
    the OFF configuration really does sever them -- so the assertions are
    discriminating between two reachable states, not restating a constant.
    """
    from deepreason.v6_policy import engaged_inquiry_capability_policy

    severed = engaged_inquiry_capability_policy(
        {}, config=Config(CHANNELS_DISABLED=("research", "simulation"))
    )

    assert severed.research.enabled is False
    assert severed.research.domain_allowlist == ()
    assert severed.research.maximum_requests == 0
    assert severed.simulation.enabled is False
    assert severed.simulation.maximum_simulation_requests == 0
