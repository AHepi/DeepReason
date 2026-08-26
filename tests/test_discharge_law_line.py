"""THE LAW LINE (REBUILD F1, R5/R7/R8).

Stated in SPEC.md S7 and repeated here because a test file is where a law
becomes falsifiable:

    Discharge constrains how content is GENERATED -- a precondition on
    SUBMISSION, nothing more. It never constrains what counts as EVIDENCE. No
    discharge field, kind, count or record may feed a label, a warrant, a rank,
    an admission decision, or any adjudication pass. A REBUTTED discharge
    enters the ordinary graph as an ordinary artifact and is judged there, by
    criticism, like anything else. Discharge kinds carry no rank and no
    admission weight.

This is the operator's standing seats guardrail -- "seats change how content is
GENERATED, never what counts as EVIDENCE" (CLAUDE.md) -- and the
formalism-optional law (`DR-CON-conjecture-kinds`'s R-g) applied to this
channel. Both say the same thing from different directions: nothing may weight
an outcome on the KIND of a contribution.

Pinned four ways, because each closes a different route in:

1. an ABSENCE over the four packages that decide anything, in the shape
   `test_nothing_that_ranks_admits_or_accepts_reads_a_departure` uses;
2. the declaration record has no numeric field, so there is no weight to set;
3. admission is byte-identical with and without discharges;
4. no label differs between a channel-on and a channel-off run on one graph.

Pin 1 is mutation-proved (`proof/c3_red.txt`): a discharge wired into label
computation turns it red.
"""

import ast
import pathlib

import pytest

from deepreason.config import Config
from deepreason.discharge import (
    DischargeKindDeclaration,
    record_discharges,
    resolve_policy,
)
from deepreason.harness import Harness
from deepreason.llm.wire import DischargeWireV1
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance
from deepreason.rules.guards import anti_relapse

ON = "discharge-required.v1"

# The packages that DECIDE something: what a status is, what a problem is worth
# working on, whether a candidate is admitted, whether a prose case survives a
# trial. `rules/conj.py` is the one permitted exception -- it is the submission
# path, where the precondition lives by design.
DECIDING_PACKAGES = (
    pathlib.Path("src/deepreason/scheduler"),
    pathlib.Path("src/deepreason/adjudication"),
    pathlib.Path("src/deepreason/informal"),
    pathlib.Path("src/deepreason/rules"),
)
PERMITTED = (pathlib.Path("src/deepreason/rules/conj.py"),)

FORBIDDEN_NAMES = (
    "DischargeWireV1",
    "discharges",
    "discharge_kind",
    "DISCHARGE_KIND_DECLARATIONS",
    "discharge-policy.v1",
    "screen_submission",
    "record_discharges",
    "open_criticisms",
)


@pytest.fixture
def policy():
    return resolve_policy(Config(DISCHARGE_POLICY=ON))


# --- pin 1: the absence ---------------------------------------------------- #


def test_nothing_that_labels_ranks_or_admits_reads_a_discharge():
    """R5. No module that decides anything may name the discharge machinery.

    Every negative check is paired with a POSITIVE ANCHOR on the same tree
    (`DR-SCHEMA` check-writing rule 1): a moved or renamed package would
    otherwise make this vacuous rather than failing, and four documents in this
    repo have already carried checks that passed with their subject deleted.
    """
    anchored = 0
    offenders = []
    for package in DECIDING_PACKAGES:
        files = [p for p in package.rglob("*.py") if p not in PERMITTED]
        assert files, package                              # positive anchor
        anchored += len(files)
        for path in files:
            text = path.read_text()
            for name in FORBIDDEN_NAMES:
                if name in text:
                    offenders.append((str(path), name))
    assert anchored > 20, anchored                         # positive anchor
    assert not offenders, offenders


def test_the_permitted_exception_is_exactly_the_submission_path():
    """The exception has to be narrow to mean anything.

    `rules/conj.py` is permitted because it IS the submission boundary. If a
    second file in `rules/` ever needed the exception, the channel would have
    stopped being a precondition and started being a consideration, and this
    test is where that shows up.
    """
    for path in PERMITTED:
        assert path.exists(), path                         # positive anchor
        assert "screen_submission" in path.read_text()


# --- pin 2: no weight exists to be set ------------------------------------- #


def test_a_discharge_kind_declaration_carries_no_number():
    """R8, and the formalism-optional law it inherits from.

    The absence is the guarantee. A rank, weight or score field here is what
    would let a discharge reach adjudication, and no configuration can set a
    field that does not exist. Checked over the MODEL rather than over today's
    three declarations, so a fourth kind cannot introduce one.
    """
    numeric = [
        name for name, field in DischargeKindDeclaration.model_fields.items()
        if field.annotation in (int, float)
    ]
    assert not numeric, numeric
    assert set(DischargeKindDeclaration.model_fields) == {
        "name", "asserts", "requires", "directive_line", "attackable",
    }


# --- pin 3: admission cannot see a discharge ------------------------------- #


def _problem(harness, pid="p-tides"):
    return harness.register_problem(
        Problem(
            id=pid, description="state the tide table for this harbour", criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _candidate(harness, problem, text):
    return harness.create_artifact(
        text, problem_id=problem.id, provenance=Provenance(role="conjecturer"),
        interface=Interface(refs=[]),
    )


def test_admission_is_byte_identical_with_and_without_discharges(harness, policy):
    """R8, behaviourally. The gate decides on CONTENT, and a discharge is not
    content: the same candidate must receive the same verdict and the same
    reason string whether it arrived carrying three discharges or none.

    The reason string matters as much as the boolean -- Measure inputs are
    compared against recorded roots, so a verdict that stayed True while its
    reason changed would still move the record.
    """
    problem = _problem(harness)
    artifact = _candidate(harness, problem, "candidate: the tide is lunar plus solar")
    first = anti_relapse.check(artifact, [], harness)

    critic = harness.create_artifact("critic: omits the solar term",
                                     provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", artifact.id, critic.id])
    record_discharges(
        harness, problem.id, artifact.id,
        [DischargeWireV1(handle=critic.id, kind="revised", note="added it", where="p2")],
        policy,
    )
    second = anti_relapse.check(artifact, [], harness)
    assert first == second, (first, second)


# --- pin 4: no label differs, channel on vs channel off -------------------- #


def _graph(harness, *, policy, discharge):
    """One identical graph, built twice; the only difference is the channel.

    Returns the final labels over the artifacts BOTH runs contain.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem, "candidate: the tide is lunar only")
    critic = harness.create_artifact("critic: omits the solar contribution",
                                     provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    successor = _candidate(harness, problem, "candidate: the tide is lunar plus solar")
    shared = {target.id, critic.id, successor.id}
    if discharge:
        record_discharges(
            harness, problem.id, successor.id,
            [DischargeWireV1(handle=critic.id, kind="rebutted",
                             note="the solar term is below the harbour's resolution")],
            policy,
        )
    return {a: s for a, s in harness.state.status.items() if a in shared}, shared


def test_no_label_differs_between_channel_on_and_channel_off(tmp_path, policy):
    """R10. The comparison the operator named: "no label differs between
    channel-on and channel-off runs on the same graph".

    "On the same graph" is the operative phrase and is honoured literally: the
    comparison is over the artifacts BOTH runs contain. The channel-on run also
    holds a rebuttal artifact and discharge Measures, and those are the DELTA
    -- listed here rather than hidden, because a comparison that quietly
    dropped the new nodes would be measuring its own filter.
    """
    off_labels, shared = _graph(Harness(tmp_path / "off"), policy=policy, discharge=False)
    on_harness = Harness(tmp_path / "on")
    on_labels, _ = _graph(on_harness, policy=policy, discharge=True)

    assert off_labels == on_labels, (off_labels, on_labels)

    # The delta, stated. A rebuttal is a NEW node with mention-only refs, so it
    # adds nothing to any existing node's attacker set -- which is why the
    # equality above holds by construction rather than by luck.
    delta = set(on_harness.state.artifacts) - shared
    assert len(delta) == 1, delta
    rebuttal = next(iter(delta))
    assert all(ref.role.value == "mention"
               for ref in on_harness.state.artifacts[rebuttal].interface.refs)
    assert not any(x == rebuttal or t == rebuttal for x, t in on_harness.state.att)


def test_a_discharge_measure_is_not_an_attack_edge(tmp_path, policy):
    """The sharpest form of pin 4, and the one a careless implementation fails.

    Recording a discharge appends Measures. A Measure that somehow minted an
    attack edge would move labels while every other test here still passed, so
    this asserts the edge set directly.
    """
    harness = Harness(tmp_path / "run")
    problem = _problem(harness)
    target = _candidate(harness, problem, "candidate: lunar only")
    critic = harness.create_artifact("critic: omits the solar term",
                                     provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    before = set(harness.state.att)
    record_discharges(
        harness, problem.id, target.id,
        [DischargeWireV1(handle=critic.id, kind="revised", note="added it", where="p2")],
        policy,
    )
    assert set(harness.state.att) == before


@pytest.fixture
def harness(tmp_path):
    return Harness(tmp_path / "run")
