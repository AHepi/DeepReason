"""What makes a criticism OPEN, and where it renders (REBUILD F1, R1/R2).

The motivating measurement, and the reason this file reads BOTH criticism
channels rather than the obvious one: W2 found that across the two newest and
largest committed roots, **0 of 196 LLM attacks were ever exposed to a later
conjecture dispatch**, and that every status a criticism moved was moved by the
problem's own admission criteria rather than by anything a critic seat wrote
(`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`, segment 1).

Those 196 were `observe_only` dispatches. `observe_only` is the authority mode
that CANNOT mint a warrant, so none of them produced an attack edge -- they
produced a critic-role artifact and a `["scrutiny", target, critic]` Measure and
nothing else. A channel that read `state.att` alone would therefore ship
carrying only the criticism that was already acting, and would reproduce the
defect it exists to close. Every fixture here uses the `observe_only` shape for
that reason.
"""

import pytest

from deepreason.config import Config
from deepreason.discharge import open_criticisms, render_open_criticism_context, resolve_policy
from deepreason.harness import Harness
from deepreason.llm.packs import render_conj_pack
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance, Status
from tests.conftest import attack

ON = "discharge-required.v1"


@pytest.fixture
def policy():
    return resolve_policy(Config(DISCHARGE_POLICY=ON))


def _problem(harness, pid="p-tides", description="state the tide table for this harbour"):
    return harness.register_problem(
        Problem(
            id=pid, description=description, criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _candidate(harness, problem, text="candidate: the tide is lunar only"):
    return harness.create_artifact(
        text, problem_id=problem.id, provenance=Provenance(role="conjecturer"),
        interface=Interface(refs=[]),
    )


def _scrutiny(harness, target, text):
    """An `observe_only` criticism: a critic artifact, a scrutiny Measure, NO warrant.

    Built by hand rather than through `rules/crit.py` deliberately -- the
    fixture must pin the RECORD SHAPE the channel reads, so that a future
    change to how `_observe_case` writes it fails here rather than silently
    emptying the channel.
    """
    critic = harness.create_artifact(text, provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    return critic


# --- what is OPEN ---------------------------------------------------------- #


def test_an_observe_only_criticism_is_open(harness, policy):
    """R1. The population W2 measured as never routed anywhere is IN.

    This is the whole tranche in one assertion. The criticism carries no
    warrant and produces no attack edge; if the channel could not see it, the
    channel would be shipping around the defect.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem)
    critic = _scrutiny(harness, target, "critic: the solar contribution is omitted")

    assert not harness.state.att                       # positive anchor: no edge exists
    handles = [c.handle for c in open_criticisms(harness, problem.id, policy)]
    assert handles == [critic.id]


def test_a_warrant_bearing_attack_is_also_open(harness, policy):
    """R1. Both channels, not one. An attack edge counts too."""
    problem = _problem(harness)
    target = _candidate(harness, problem)
    critic, _ = attack(harness, target.id, "the-neap-range-is-wrong")

    assert (critic.id, target.id) in harness.state.att   # positive anchor
    assert [c.handle for c in open_criticisms(harness, problem.id, policy)] == [critic.id]


def test_a_refuted_critic_is_not_open(harness, policy):
    """R1. A defeated attack was MADE AND LOST; it is not an open indictment.

    The same rule the frame crisis already applies
    (`test_a_defeated_attacker_stops_occupying_a_crisis_slot`): under a cap,
    rendering a dead criticism would displace a live one, so the list would
    understate itself in exactly the case where it matters most.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem)
    critic = _scrutiny(harness, target, "critic: the solar contribution is omitted")
    assert open_criticisms(harness, problem.id, policy)   # positive anchor

    attack(harness, critic.id, "the-objection-misreads-the-tide-table")
    assert harness.state.status[critic.id] == Status.REFUTED
    assert open_criticisms(harness, problem.id, policy) == ()


def test_a_criticism_of_another_problem_is_not_open_here(harness, policy):
    """R1. `state.addr` is the boundary: a problem sees its own criticism."""
    mine = _problem(harness, "p-tides")
    theirs = _problem(harness, "p-winds", "state the wind rose for this harbour")
    _scrutiny(harness, _candidate(harness, theirs), "critic: the gust model is absent")

    assert open_criticisms(harness, mine.id, policy) == ()
    assert len(open_criticisms(harness, theirs.id, policy)) == 1


def test_the_channel_is_empty_when_the_policy_is_off(harness):
    """R13/A7. Off is off, at the reader as well as the renderer."""
    problem = _problem(harness)
    _scrutiny(harness, _candidate(harness, problem), "critic: the solar term is omitted")
    assert open_criticisms(harness, problem.id, resolve_policy(Config())) == ()


def test_a_handle_is_the_critic_artifact_id_and_does_not_renumber(harness, policy):
    """R1's word "stable", made falsifiable.

    A short ordinal would renumber the moment a lower-sorting criticism
    arrived, which is the one thing a handle may not do -- and the failure
    would be silent, because both renders look equally well-formed. Content
    addressing makes the property structural instead of tested-by-luck.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem)
    first = _scrutiny(harness, target, "critic A: the solar contribution is omitted")
    before = {c.handle for c in open_criticisms(harness, problem.id, policy)}
    assert before == {first.id}

    second = _scrutiny(harness, target, "critic B: the harbour datum is unstated")
    after = {c.handle for c in open_criticisms(harness, problem.id, policy)}
    assert after == {first.id, second.id}
    # The first handle is UNCHANGED by the arrival of the second, whatever
    # order the two ids sort in.
    assert first.id in after


def test_the_cap_states_itself_in_band(harness, policy):
    """R1. An undisclosed cap is a silent truncation.

    The count is in the rendered text, not only in the returned tuple: a reader
    of the pack must be able to tell "these are all of them" from "these are
    the first N", and a model cannot inspect a Python object.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem)
    for index in range(3):
        _scrutiny(harness, target, f"critic {index}: an omission, number {index}")

    narrow = policy.model_copy(update={"handles_n": 2})
    assert len(open_criticisms(harness, problem.id, narrow)) == 2
    assert "2 of 3" in render_open_criticism_context(harness, problem.id, narrow)
    # And with nothing cut, no count is stated at all -- an always-present
    # "3 of 3" would be the empty provenance-shaped slot N1 rules out.
    whole = render_open_criticism_context(harness, problem.id, policy)
    assert "3 of 3" not in whole


# --- the render ------------------------------------------------------------ #


def test_an_absent_channel_renders_nothing(harness, policy):
    """N1. `None`, not an empty string and not a "no open criticisms" notice.

    A section announcing the absence of criticism is exactly the empty
    provenance-shaped slot `RESEARCH_JUDGE_BLINDING` measured as WORSE than a
    populated one, and Rung 6 already obeys the rule for the frame slice.
    """
    problem = _problem(harness)
    _candidate(harness, problem)
    assert render_open_criticism_context(harness, problem.id, policy) is None


def test_the_render_carries_the_claim_the_span_and_the_handle(harness, policy):
    """R1. All three, because two of them are useless alone.

    A handle with no claim is an instruction to answer something the writer
    cannot see; a claim with no handle cannot be discharged.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem, "candidate: the tide is the moon alone")
    critic = _scrutiny(
        harness, target,
        'critic: it says "the tide is the moon alone", which omits the solar '
        "contribution and so cannot give the spring-neap range",
    )
    rendered = render_open_criticism_context(harness, problem.id, policy)

    assert critic.id in rendered
    assert "omits the solar" in rendered
    assert "OPEN CRITICISMS" in rendered
    for kind in ("revised", "rebutted", "departure_declared"):
        assert kind in rendered


def test_the_render_lands_in_the_binding_block_not_a_sidebar(harness, policy):
    """R1's "INSIDE the conjecturer's working section (not a sidebar section)".

    Structural, not a wording choice: `allocate_pack` admits sections in
    `(priority, id)` order, so this asserts the criticisms sit among what the
    candidate is BOUND BY -- after `criteria`, before `mandatory-interface` --
    and above every advisory section. A pack that merely MENTIONED criticism
    somewhere would pass a text search and fail this.
    """
    import ast
    import pathlib

    problem = _problem(harness)
    target = _candidate(harness, problem)
    critic = _scrutiny(harness, target, "critic: the solar contribution is omitted")

    source = pathlib.Path("src/deepreason/llm/packs.py").read_text()
    tree = ast.parse(source)
    conj = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "render_conj_pack"
    )
    priorities = {
        ast.literal_eval(c.args[0]): c.args[2].value
        for c in ast.walk(conj)
        if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_pack_section"
    }
    keywords = {
        ast.literal_eval(c.args[0]): {k.arg: getattr(k.value, "value", None) for k in c.keywords}
        for c in ast.walk(conj)
        if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_pack_section"
    }

    assert priorities["criteria"] == 2                    # positive anchor
    assert priorities["open-criticisms"] == 2
    assert priorities["mandatory-interface"] == 3
    # The ordering claim itself, in the exact terms `allocate_pack` sorts by
    # (`sorted(ir.sections, key=lambda s: (s.priority, s.id))`), so this fails
    # if either the priority or the section id changes the resulting order.
    assert (2, "criteria") < (2, "open-criticisms") < (3, "mandatory-interface")
    for advisory in ("neighbourhood", "scratch-advisory-context"):
        assert priorities["open-criticisms"] < priorities[advisory]

    # Neither droppable nor compressible: a dropped section leaves no header,
    # and Rung 6 measured a compressible one losing its middle at a tight
    # budget while still looking present.
    assert keywords["open-criticisms"]["droppable"] is False
    assert keywords["open-criticisms"]["compressible"] is False

    pack = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=4000,
        open_criticism_context=render_open_criticism_context(harness, problem.id, policy),
    )
    assert critic.id in pack


def test_the_output_contract_states_the_precondition(harness, policy):
    """R3/R4. The obligation is on the SUBMISSION, so it is in the contract.

    Rendering the criticisms without saying they must be discharged would be
    the separable-advice interface Q5 measured as neglected -- the same content
    in a place the writer may treat as optional.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem)
    _scrutiny(harness, target, "critic: the solar contribution is omitted")

    with_channel = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=4000,
        open_criticism_context=render_open_criticism_context(harness, problem.id, policy),
    )
    without = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=4000,
    )
    assert "discharge" in with_channel.lower()
    assert "discharge" not in without.lower()


def test_a_criticism_at_cycle_k_still_renders_at_the_terminal_cycle(tmp_path, policy):
    """R2. Persistence asserted AT THE TERMINAL step, never at injection.

    Modelled on `test_a_standing_attacker_at_cycle_k_still_renders_at_the_
    terminal_cycle`, including its reason: the record forgetting nothing does
    not make the PACK remember. Every later cycle adds ACCEPTED state so the
    pack competes for budget as a real run's does, and the question is asked
    only at cycle 8 -- the cycle where a renderer that had quietly stopped
    carrying the criticism would look identical to one that never carried it.
    """
    harness = Harness(tmp_path / "run")
    problem = _problem(harness)
    target = _candidate(harness, problem)

    critic = None
    packs = {}
    for cycle in range(1, 9):
        if cycle == 2:
            critic = _scrutiny(harness, target, "critic: the solar contribution is omitted")
        harness.create_artifact(
            f"candidate produced at cycle {cycle} " + "detail " * 40,
            problem_id=problem.id, provenance=Provenance(role="conjecturer"),
        )
        packs[cycle] = render_conj_pack(
            problem, harness.state, harness.commitments, harness.blobs,
            # 200, not a comfortable number: the budget at which a DROPPABLE
            # section is cut outright. A test at 400 would pass with the
            # section made droppable and would therefore prove nothing.
            vs_k=2, token_budget=200,
            open_criticism_context=render_open_criticism_context(harness, problem.id, policy),
        )

    assert critic is not None
    assert critic.id not in packs[1]
    for cycle in range(2, 9):
        assert critic.id in packs[cycle], cycle
    assert "OPEN CRITICISMS" in packs[8]
    assert "## neighbourhood" not in packs[8]


def test_the_open_criticism_section_is_bounded_by_construction(harness, policy):
    """R1. EXACT is affordable only because the section cannot grow without limit.

    Three caps, all from the policy: how many handles, and how much of the
    claim and the span each shows. Without them a non-compressible section
    would push the pack into `mandatory_overflow` on a long criticism, which is
    a refusal rather than a quiet cut -- correct, but not a channel anyone
    could run.
    """
    problem = _problem(harness)
    target = _candidate(harness, problem)
    for index in range(20):
        _scrutiny(harness, target, f"critic {index}: " + "a very long complaint " * 200)

    rendered = render_open_criticism_context(harness, problem.id, policy)
    assert len(open_criticisms(harness, problem.id, policy)) == policy.handles_n
    ceiling = policy.handles_n * (policy.claim_head_chars + policy.span_head_chars + 512)
    assert len(rendered) < ceiling


def test_the_render_is_byte_identical_across_calls(harness, policy):
    """G4/C1. Determinism, which a sorted read gives and a set read does not."""
    problem = _problem(harness)
    target = _candidate(harness, problem)
    for index in range(4):
        _scrutiny(harness, target, f"critic {index}: an omission, number {index}")
    first = render_open_criticism_context(harness, problem.id, policy)
    assert first == render_open_criticism_context(harness, problem.id, policy)


def test_rendering_writes_nothing_to_the_log(harness, policy):
    """G2. A render is a READ. It moves no label and appends no event."""
    problem = _problem(harness)
    target = _candidate(harness, problem)
    _scrutiny(harness, target, "critic: the solar contribution is omitted")

    before_len = len(list(harness.log.read()))
    before_status = dict(harness.state.status)
    render_open_criticism_context(harness, problem.id, policy)
    assert len(list(harness.log.read())) == before_len
    assert dict(harness.state.status) == before_status
