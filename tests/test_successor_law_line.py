"""THE LAW LINE for successor questions (operator law, 2026-08-29).

Stated in the tranche's SPEC.md R1 and repeated here because a test file is
where a law becomes falsifiable:

    The successor-question field is OPTIONAL on criticism output -- never
    required, never penalized. No successor field, destination row, receipt or
    minted problem may feed a label, a warrant, a rank, an admission decision,
    or any adjudication pass. Filling the field earns a critic nothing and
    leaving it empty costs a critic nothing.

This is the operator's standing seats guardrail -- "seats change how content is
GENERATED, never what counts as EVIDENCE" (CLAUDE.md) -- and the
formalism-optional law (`DR-CON-conjecture-kinds`'s R-g) applied to this
channel: nothing may weight an outcome on the KIND of a contribution, and a
proposed question is a kind of contribution.

Pinned four ways, because each closes a different route in. Each pin has a
SPELLING half (cheap, catches the careless case) and, since 2026-08-30, a
BEHAVIOURAL half beside it (dearer, catches the case that spells nothing):

1. an ABSENCE over the packages that decide anything, on the model
   `tests/test_discharge_law_line.py` established -- plus, behaviourally, that
   a routed question does not move problem SELECTION in either ranking mode;
2. the destination declaration record has no numeric field and no shipped row
   carries a numeric VALUE, so there is no weight to set;
3. admission is byte-identical with and without a routed successor question, at
   the CONFIGURED gate and at the frame where admission is actually decided
   (`rules/conj.py`), which is one call above the gate;
4. no status label differs between a field-filled and a field-absent run --
   both on a graph with no contest in it, and on a real defended court where
   the target is REFUTED and something could therefore move.

WHAT THE SPELLING HALVES DO NOT PROVE, stated because three of them were read
as proving it (findings F1/F2/F3, 2026-08-30, each a constructed penalty that
changed real behaviour with all 42 tests green). Pin 1 is a search over source
text: a rank read spelled without one of FORBIDDEN_NAMES passes it. Pin 1 is
mutation-proved for SPELLING only
(`experiments/2026-08-30-change-successor-questions/proof/law_line_pin1_red.txt`):
naming the registry inside the scheduler's rank key turns it red, but that
mutant reads no successor_question and changes no selection. The behavioural
guarantees are carried by the four tests named in the list above, each of which
was watched red under the finding's own mutation and green again on revert.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.contracts import ArgumentativeCriticOutput, BatchCase
from deepreason.llm.embedder import HashingEmbedder
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.rules.conj import conj
from deepreason.rules.crit import crit_argumentative
from deepreason.rules.guards import anti_relapse
from deepreason.scheduler.scheduler import Scheduler
from deepreason.successor import resolve, route
from deepreason.successor.registry import (
    DESTINATIONS,
    GATES,
    SuccessorDeclaration,
    declaration_field_types,
)


class _Config:
    """The shipped defaults, read the way the registry reads any config.

    Deliberately NOT `deepreason.config.Config`: the two per-run fields are
    parked behind a frozen-surface grant, and this channel must be correct
    before they exist. `resolve` reads its selector by `getattr`, so an object
    that carries neither field is exactly the default case.
    """


# The packages that DECIDE something: what a status is, what a problem is worth
# working on, whether a candidate is admitted, whether a prose case survives a
# trial. There is NO permitted exception, and that is the point: this channel's
# dispatch lives outside `rules/` by construction, so a name appearing here is
# either a mistake or an operator decision that has not been written down.
#
# `workflow` and `workflows` are here because the admission gate is called from
# four places, and two of them are outside the rule packages (F4, 2026-08-30:
# four FORBIDDEN_NAMES were planted verbatim in `workflow/conjecture_recovery.py`
# beside its `if not admitted:` branch and this pin stayed green). The census
# below keeps the list honest instead of trusting today's reading of it.
DECIDING_PACKAGES = (
    pathlib.Path("src/deepreason/scheduler"),
    pathlib.Path("src/deepreason/adjudication"),
    pathlib.Path("src/deepreason/informal"),
    pathlib.Path("src/deepreason/rules"),
    pathlib.Path("src/deepreason/workflow"),
    pathlib.Path("src/deepreason/workflows"),
)
PERMITTED: tuple[pathlib.Path, ...] = ()

# The gate whose callers DECIDE admission. Named once so the census below and
# the reason the two workflow packages are listed cannot drift apart.
ADMISSION_GATE_CALL = "anti_relapse.check"

FORBIDDEN_NAMES = (
    "successor_question",
    "deepreason.successor",
    "SuccessorDeclaration",
    "SUCCESSOR_QUESTION_DESTINATION",
    "SUCCESSOR_MINTING_ENABLED",
    "successor-question:",
    "successor-problem-minted",
    "minting_enabled",
    "minting_notices",
    "unknown_destination_notices",
    "SpawnTrigger.SUCCESSOR",
)


# --- pin 1: the absence ---------------------------------------------------- #


def test_nothing_that_labels_ranks_or_admits_reads_a_successor_question():
    """R1. No module that decides anything may name the successor machinery.

    Every negative check is paired with a POSITIVE ANCHOR on the same tree
    (`DR-SCHEMA` check-writing rule 1): a moved or renamed package would
    otherwise make this vacuous rather than failing.

    The bare word "successor" is deliberately NOT forbidden -- `rules/conj.py`
    already uses it to describe `succ:*` problems as attention objects, and
    forbidding an English word would make this test about spelling instead of
    about coupling.
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


def test_every_caller_of_the_admission_gate_is_inside_a_deciding_package():
    """The census that keeps DECIDING_PACKAGES honest.

    Pin 1 above is only as wide as its package list, and that list was wrong
    once already (F4): two of the four production callers of the admission gate
    live in `workflow/` and `workflows/`, so a penalty written beside either
    `if not admitted:` was invisible. Rather than re-reading the tree by hand,
    this DERIVES the requirement -- every file that calls the gate must fall
    inside a package pin 1 scans -- so a fifth caller in a seventh package
    reddens here instead of quietly widening the hole.
    """
    scanned = {package.name for package in DECIDING_PACKAGES}
    callers = {
        path
        for path in pathlib.Path("src/deepreason").rglob("*.py")
        if ADMISSION_GATE_CALL in path.read_text()
    }
    assert len(callers) >= 4, sorted(str(p) for p in callers)   # positive anchor
    outside = sorted(
        str(path) for path in callers
        if not (len(path.parts) > 2 and path.parts[2] in scanned)
    )
    assert not outside, outside


def test_the_channel_has_no_permitted_exception_inside_a_deciding_package():
    """The exception list is EMPTY, and emptiness is the claim.

    The premise channel needed `rules/crit.py` because its dispatch is a
    criticism act. This channel's dispatch site is an open operator question
    (the tranche's Q3: may the criticism side write to the workshop?), so until
    that is answered nothing inside `rules/` may name it. If Q3 is answered
    "yes, crit.py dispatches", the test above goes red and THIS list is where
    the answer gets written down -- which is the alarm working, not failing.

    WHAT THIS ASSERTION IS, stated plainly because it reads like more than it
    is (F26, 2026-08-30): it cannot be reddened by any change to `src/`. It is
    a tripwire on this file's OWN constant, so that adding a path to PERMITTED
    is a deliberate edit here rather than a silent widening of pin 1's scan.
    The failable guard is
    `test_nothing_that_labels_ranks_or_admits_reads_a_successor_question` above,
    and the behavioural guards are the three pins below it.
    """
    assert PERMITTED == ()


# --- pin 1b: the rank, BEHAVIOURALLY --------------------------------------- #


def _seeded(harness, *problem_ids):
    harness.register_commitment(Commitment(id="k-q", eval="predicate:True"))
    for pid in problem_ids:
        harness.register_problem(Problem(
            id=pid, description=f"the operator's question {pid}", criteria=["k-q"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}),
        ))
    return harness


def test_a_routed_question_does_not_move_problem_selection(tmp_path):
    """R1 on the surface the law names FIRST: rank.

    Pin 1 is a source-text search, so a rank read spelled without one of
    FORBIDDEN_NAMES passes it -- measured, not supposed (F1, 2026-08-30: a
    weight multiplier keyed on the routed block's own public `unfinished`
    marker moved selection from p-a to p-b with all 42 tests green). This
    observes the ranking itself: two identical never-worked seed problems, one
    run with nothing routed and one with a question routed under `p-a`, in BOTH
    selection modes. The pick must not move.

    A routed question is an advisory scratch block and a Measure. If either can
    reach `Scheduler._select_problem`'s key, filling the optional field has
    bought or cost the critic a cycle, which is exactly what the law forbids.
    """
    for liveness in (True, False):
        picks = []
        for routed in (None, "p-a"):
            harness = _seeded(
                Harness(tmp_path / f"{liveness}-{routed}"), "p-a", "p-b")
            if routed:
                assert route(harness, _Config(), problem_id=routed,
                             question="what would settle this?") is not None
            scheduler = Scheduler(
                harness, LLMAdapter({}, harness.blobs),
                Config(LIVENESS_QUEUE=liveness, N_SCHOOLS=0),
            )
            selected = scheduler._select_problem()
            assert selected is not None, (liveness, routed)   # positive anchor
            picks.append(selected.id)
        assert picks[0] == picks[1], (liveness, picks)


# --- pin 2: no weight exists to be set ------------------------------------- #


def test_a_successor_declaration_carries_no_number():
    """R1, structurally. The absence is the guarantee.

    A rank, weight, priority or score field here is what would let a proposed
    question reach a decision, and no configuration can set a field that does
    not exist. Checked over the MODEL rather than over today's rows, so a
    destination added tomorrow cannot introduce one.

    The MODEL check alone is not enough, and that is measured (F5, 2026-08-30):
    `declaration_field_types()` reads the BASE class, while `isinstance` is
    satisfied by any subclass, so a `WeightedDeclaration(SuccessorDeclaration)`
    carrying `rank_bonus = 2.5` could be the shipped default row with both
    assertions passing. `register_destination` type-checks nothing, so this is
    exactly the shape a third-party row takes. Hence two further checks: the
    row's type is EXACT, and its actual values are censused for a number.
    """
    numeric = [
        name
        for name, annotation in declaration_field_types().items()
        if annotation in (int, float)
    ]
    assert not numeric, numeric
    assert set(declaration_field_types()) == {
        "id", "routes", "default", "enforcement", "authority", "warning",
    }
    rows = (*DESTINATIONS.values(), *GATES.values())
    assert rows                                            # positive anchor
    for row in rows:
        # EXACT type, not isinstance: a subclass is how a weight gets onto a
        # row without touching the model the assertions above read.
        assert type(row) is SuccessorDeclaration, (row, type(row))
        # And over the VALUES, so a weight smuggled in as an untyped attribute
        # is caught even if the type check is one day relaxed. `bool` is
        # excluded deliberately -- `default` is a bool and bool is an int.
        numeric_values = sorted(
            name for name, value in vars(row).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        )
        assert not numeric_values, (row.id, numeric_values)


def test_the_contract_field_is_optional_on_both_criticism_outputs():
    """R1's other half: absent-legal, and absent means unchanged bytes.

    `None` rather than `""` so a criticism that proposed nothing canonicalises
    to exactly the bytes it always did under `exclude_none` -- an empty string
    would add a key to every critic output ever recorded.
    """
    for model in (ArgumentativeCriticOutput, BatchCase):
        field = model.model_fields["successor_question"]
        assert field.default is None, (model.__name__, field.default)
        assert not field.is_required(), model.__name__
    bare = ArgumentativeCriticOutput(attack=False)
    assert "successor_question" not in bare.model_dump(exclude_none=True)
    filled = BatchCase(target="t", attack=False, successor_question="what next?")
    assert filled.model_dump(exclude_none=True)["successor_question"] == "what next?"


# --- pin 3: admission cannot see a successor question ---------------------- #


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


def test_admission_is_byte_identical_with_and_without_a_successor_question(harness):
    """R1, behaviourally. The gate decides on CONTENT, and a proposed question
    is not content: the same candidate must receive the same verdict and the
    same reason string whether a successor question was routed beside it or not.

    The reason string matters as much as the boolean -- Measure inputs are
    compared against recorded roots, so a verdict that stayed True while its
    reason changed would still move the record.

    The gate is probed CONFIGURED, not degraded. With domain, embedder and
    near_dup_eps all absent, `check` takes its fail-open early return after
    roughly twenty of its ~120 lines and never reaches the semantic-trigger or
    battery-equivalence stages that decide admission in a real run: the
    identical penalty was caught above that early return and missed five lines
    below it (F6, 2026-08-30). Supplying a real scope is what makes this a probe
    of the gate rather than of its degraded path, and the last assertion keeps
    it there if a default ever changes.
    """
    problem = _problem(harness)
    artifact = _candidate(harness, problem, "candidate: the tide is lunar plus solar")
    scope = dict(
        embedder=HashingEmbedder(),
        near_dup_eps=0.2,
        domain=anti_relapse.relapse_domain(
            artifact, harness, workload_profile="text",
            problem_family=problem.id, contract_id="conjecturer.direct.v1",
        ),
    )
    first = anti_relapse.check(artifact, [], harness, **scope)
    assert not first[1].startswith("admitted-degraded"), first   # positive anchor

    routed = route(
        harness, _Config(), problem_id=problem.id,
        question="what would settle whether the solar term is measurable here?",
    )
    assert routed is not None
    second = anti_relapse.check(artifact, [], harness, **scope)
    assert first == second, (first, second)


def test_a_routed_question_does_not_change_what_conj_admits(tmp_path):
    """R1 at the frame where admission is actually DECIDED.

    The gate returns `(admitted, reason)`; the DECISION is the caller's --
    `rules/conj.py` reads that pair and does `observe_candidate(..., "reject")`,
    records a `gate:<reason>` Measure, and drops the candidate. A penalty
    written one call-frame above the gate is a real admission rejection of every
    candidate under a problem whose critic filled the optional field, and the
    guard probe above cannot see it (F2, 2026-08-30: 2 artifacts admitted with
    nothing routed, 0 with a question routed, all 42 tests green).

    So this counts what SURVIVES the whole pass, with and without a routed
    question, which is the quantity the law is about.
    """
    admitted = []
    for routed in (None, "pi-1"):
        harness = Harness(tmp_path / f"run-{routed}")
        harness.register_commitment(Commitment(id="k-true", eval="predicate:True"))
        harness.register_problem(Problem(
            id="pi-1", description="state the tide table for this harbour",
            criteria=["k-true"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}),
        ))
        if routed:
            assert route(harness, _Config(), problem_id=routed,
                         question="what would settle this?") is not None
        adapter = LLMAdapter(
            {"conjecturer": MockEndpoint([json.dumps({"candidates": [
                {"content": text, "typicality": 0.5}
                for text in ("the tide is lunar plus solar",
                             "the tide is lunar only")
            ]})])},
            harness.blobs, retry_max=2,
        )
        conj(harness, "pi-1", adapter, Config(VS_K=2, NEAR_DUP_EPS=None, N_SCHOOLS=0))
        admitted.append(len(harness.state.artifacts))
    assert admitted[0] > 0, admitted                             # positive anchor
    assert admitted[0] == admitted[1], admitted


# --- pin 4: no label differs, field on vs field off ------------------------ #


def _graph(harness, *, successor_question):
    """One identical graph, built twice; the only difference is the field.

    Returns the final labels over the artifacts BOTH runs contain.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem, "candidate: the tide is lunar only")
    critic = harness.create_artifact("critic: omits the solar contribution",
                                     provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    if successor_question:
        route(harness, _Config(), problem_id=problem.id, question=successor_question)
    shared = {target.id, critic.id}
    return {a: s for a, s in harness.state.status.items() if a in shared}, shared


def test_no_label_differs_between_a_filled_and_an_empty_field(tmp_path):
    """R1. "Never penalized" means the graph cannot tell the difference.

    The comparison is over the artifacts BOTH runs contain. The filled run also
    holds one advisory scratch block and one Measure, and those are the DELTA
    -- stated here rather than hidden, because a comparison that quietly
    dropped the new records would be measuring its own filter.

    WHAT IT COVERS, narrowed to the truth (F3, 2026-08-30): routing adds no
    artifact and no attack edge, so no status label on THIS graph can move. The
    graph has zero attack edges, so both runs are trivially ACCEPTED and the
    equality ranges over a single label value -- which is why it stayed green
    while a critic that filled the field was made to lose its refutation. The
    penalty-on-a-contest case is
    `test_filling_the_field_costs_the_critic_no_authority` above.
    """
    off_labels, shared = _graph(Harness(tmp_path / "off"), successor_question=None)
    on_harness = Harness(tmp_path / "on")
    on_labels, _ = _graph(on_harness, successor_question="what would settle it?")

    assert off_labels == on_labels, (off_labels, on_labels)

    # The delta, stated. A routed question adds a scratch block and a Measure;
    # it adds no artifact and no attack edge, which is why the equality above
    # holds by construction rather than by luck.
    assert set(on_harness.state.artifacts) == shared
    assert len(on_harness.scratch_state.blocks) == 1
    assert set(on_harness.state.att) == set(Harness(tmp_path / "off").state.att)


_CASE = "the passage uses parallel fifths in bar 3, violating clause 2"
_DEFENDER = json.dumps({"answer": "the fifths are an intentional echo"})
_FAIL_RULING = json.dumps(
    {"verdict": "fail", "decisive_point": "parallel fifths in bar 3"}
)
_PARAPHRASES = json.dumps({"edits": [
    {"content": "fifths move in parallel at bar 3; clause 2 forbids it"},
    {"content": "bar 3 contains consecutive fifths, contra clause 2"},
]})


def _court(harness, critic_payload):
    """The defended cross-family court of `tests/test_criticism_authority.py`,
    rebuilt here so a status CONTEST exists to be penalised."""
    return LLMAdapter(
        {
            "argumentative_critic": MockEndpoint([json.dumps(critic_payload)]),
            "judge": [
                MockEndpoint([_FAIL_RULING] * 3, name="mock://judge-gemma",
                             model="gemma-test"),
                MockEndpoint([_FAIL_RULING] * 3, name="mock://judge-qwen",
                             model="qwen-test"),
            ],
            "variator": MockEndpoint([_PARAPHRASES]),
            "defender": MockEndpoint([_DEFENDER]),
        },
        harness.blobs, retry_max=2,
    )


def test_filling_the_field_costs_the_critic_no_authority(tmp_path):
    """The SHARPEST form of pin 4, and the one the shipped pin could not see.

    The comparison below (`test_no_label_differs...`) builds a graph with ZERO
    attack edges, so every artifact in both runs is trivially ACCEPTED and the
    equality ranges over one label value: the one thing that could move a label
    -- a criticism that actually attacks -- exists in neither run. Measured, not
    supposed (F3, 2026-08-30): a two-line change that treated a filled field as
    a malformed critic output left the target ACCEPTED instead of REFUTED, and
    all 42 tests stayed green.

    So this runs a real status contest -- the defended cross-family court, the
    same case, the same rulings -- once with the optional field empty and once
    with it filled, and asserts the target's final Status, the attack-edge set
    and the warrant count are identical. This is the operator's law in its own
    words: "filling the field earns a critic nothing and leaving it empty costs
    a critic nothing".
    """
    config = Config(
        ARGUMENTATIVE_AUTHORITY="trial_required",
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        TRIAL_PARAPHRASE_N=2,
    )
    outcomes = []
    for question in (None, "what would settle the echo reading?"):
        harness = Harness(tmp_path / f"run-{bool(question)}")
        target = harness.create_artifact(
            "a chorale passage with parallel fifths in bar 3",
            provenance=Provenance(role="conjecturer"),
        )
        payload = {"attack": True, "case": _CASE}
        if question:
            payload["successor_question"] = question
        critic = crit_argumentative(harness, target.id, _court(harness, payload), config)
        outcomes.append((
            critic is not None,
            harness.state.status[target.id],
            len(set(harness.state.att)),
            len(harness.warrants),
        ))
    # The contest really happened: without these the equality below would be
    # the vacuous comparison over one label value that this test exists to
    # replace.
    assert outcomes[0][0] is True, outcomes                   # positive anchor
    assert outcomes[0][1] == Status.REFUTED, outcomes         # positive anchor
    assert outcomes[0][2] > 0 and outcomes[0][3] > 0, outcomes  # positive anchor
    assert outcomes[0] == outcomes[1], outcomes


def test_a_routed_question_is_not_an_attack_edge(tmp_path):
    """The sharpest form of pin 4, and the one a careless implementation fails.

    Routing appends a Measure. A Measure that somehow minted an attack edge
    would move labels while every other test here still passed, so this asserts
    the edge set directly.
    """
    harness = Harness(tmp_path / "run")
    problem = _problem(harness)
    target = _candidate(harness, problem, "candidate: lunar only")
    critic = harness.create_artifact("critic: omits the solar term",
                                     provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    before = set(harness.state.att)
    route(harness, _Config(), problem_id=problem.id, question="what settles it?")
    assert set(harness.state.att) == before


def test_the_shipped_default_needs_no_config_field_to_be_correct():
    """The channel is correct BEFORE its two per-run switches exist.

    `resolve` reads its selector by `getattr`, so an object carrying neither
    field selects the shipped default. This is what lets the destination
    registry land while the `Config` fields wait behind a frozen-surface grant,
    and it is asserted rather than assumed.
    """
    assert resolve(_Config()).id == "scratchpad.v1"
    assert DESTINATIONS["scratchpad.v1"].default is True
    assert GATES["minting.v1"].default is False


@pytest.fixture
def harness(tmp_path):
    return Harness(tmp_path / "run")
