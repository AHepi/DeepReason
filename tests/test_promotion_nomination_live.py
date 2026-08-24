"""M-4's NEGATIVE half, measured on real live data (L-6, R11, R15).

The committed root is
`experiments/2026-08-22-change-epoch3-second-lineage/run`, run id
`bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4`: the first
live run of its configuration ever to reach a healthy typed terminal
(`completed`, `budget_exhausted`, 8 of 8 cycles, `verify_root` 0 violations),
and the first text run in this repository's history to record a `reach_set`
event at all. It has exactly ONE.

That one event is what makes this root the right negative control rather than a
convenient empty one. Nomination is a measure over reach; a root with no reach
would prove nothing about it, because a measure that never runs cannot
misfire. Here reach really did fire, and nomination must still decline --
because the two problems the reaching artifact addresses, a spawned connection
problem and the seed question, descend from the SAME seed. One lineage is the
run's own descent, which every artifact in a single-question run shares; the
threshold exists to detect a subject that has escaped it.

A no-fire on real live data is as load-bearing as a fire. A threshold that
fires on the first genuine reach event any live run ever produced would be a
threshold measuring nothing.

The root is opened READ-ONLY. A writable open REPAIRS a root, which is to say
it destroys the evidence a reader opened it to look at (`dr-drive-harness` §5).
"""

import pathlib

import pytest

from deepreason.calculus import nomination
from deepreason.config import Config
from deepreason.harness import Harness

ROOT = (
    pathlib.Path(__file__).resolve().parents[1]
    / "experiments"
    / "2026-08-22-change-epoch3-second-lineage"
    / "run"
)
RUN_ID = "bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4"
REACHING_ARTIFACT = (
    "dd15f0da59cbec86c1bf837221740c10f30b07808345087941bc627a7866a7ed"
)
SEED_PROBLEM = "question-4dd62735b90864a75220e09b302500bc"
CONNECTION_PROBLEM = "conn:0793267d0d4d"


@pytest.fixture(scope="module")
def live():
    if not (ROOT / "log.jsonl").exists():
        pytest.skip(f"committed root absent: {ROOT}")
    return Harness(ROOT, read_only=True)


def test_the_fixture_is_the_root_this_test_claims_it_is(live):
    """Pin the evidence before reasoning about it. A test that silently ran
    against a different root would report a no-fire that means nothing."""
    assert ROOT.name == "run"
    assert (ROOT / "run-status.json").exists()
    reach = {aid: value for aid, value in live.state.reach.items() if value}
    assert reach == {REACHING_ARTIFACT: 1.0}, reach
    addressed = sorted(pid for aid, pid in live.state.addr if aid == REACHING_ARTIFACT)
    assert addressed == [CONNECTION_PROBLEM, SEED_PROBLEM], addressed


def test_the_one_reach_event_spans_exactly_one_lineage(live):
    """The REASON for the no-fire, asserted rather than assumed.

    Asserting only the empty result would pass for the wrong reason if
    nomination were broken and returned nothing on every input.
    """
    assert nomination.origin_problem(live, REACHING_ARTIFACT) == CONNECTION_PROBLEM
    assert nomination.lineage_root(live, CONNECTION_PROBLEM) == SEED_PROBLEM
    assert nomination.lineage_root(live, SEED_PROBLEM) == SEED_PROBLEM
    assert nomination.lineage_span(live, REACHING_ARTIFACT) == (SEED_PROBLEM,)


def test_every_problem_in_the_run_descends_from_the_one_seed(live):
    """210 problems, one lineage. The run asked one question, and everything it
    spawned -- 136 research, 46 connection, 24 integration, 3 discrimination --
    descends from it. This is what a single-question run looks like, and it is
    why the threshold cannot be one."""
    roots = {nomination.lineage_root(live, pid) for pid in live.state.problems}
    assert roots == {SEED_PROBLEM}, sorted(roots)
    assert len(live.state.problems) == 210


def test_nomination_does_not_fire_on_the_committed_live_root(live):
    """M-4's negative half. At the shipped default and at every threshold the
    knob admits above one, the answer is the same: nothing is nominated."""
    for k_frame in (2, 3, 4):
        assert nomination.nominate(live, Config(K_FRAME=k_frame)) == []
    assert Config().K_FRAME == 2


def test_the_read_only_open_wrote_nothing(live):
    """The evidence is unchanged by having been read. `nominate` is a fold over
    the log and could only write through the harness, which refuses here."""
    from deepreason.harness import ReadOnlyHarnessError

    with pytest.raises(ReadOnlyHarnessError):
        live.record_measure(inputs=["this must never reach the log"])
