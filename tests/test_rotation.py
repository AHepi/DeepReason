"""Discrimination futility backoff (§14): a pairwise trial the judges cannot
resolve (order-swap deadlock) leaves its problem 'unsolved', and unsolved-first
selection would re-feed it judge calls forever — live run 3 burned 18 blocked
trials while the root problem got ONE conjecturer call. Attempts now start a
cooldown and cap out; a paused rivalry is recorded as unresolved, never
retried into starvation. Attention only — no status is ever touched."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
)
from deepreason.scheduler.scheduler import Scheduler

ALWAYS_A = json.dumps({"winner": "A", "decisive_point": "x"})  # never swaps => block
MOON = json.dumps({"candidates": [{"content": "moon idea", "typicality": 0.9}]})


def _starvation_setup(tmp_path, **config_kwargs):
    """Root problem SOLVED (has a survivor) + an unresolvable discrimination
    problem: the exact run-3 shape."""
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-root", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    # A survivor addressed to the root: the root counts as 'solved', so
    # legacy unsolved-first selection deprioritizes it forever.
    harness.create_artifact(
        "moon survivor", provenance=Provenance(role="conjecturer"), problem_id="pi-root"
    )
    a = harness.create_artifact("rival moon A", provenance=Provenance(role="conjecturer"))
    b = harness.create_artifact("rival moon B", provenance=Provenance(role="conjecturer"))
    harness.register_problem(
        Problem(
            id="disc:rivals", description="discriminate the rivals", criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": [a.id, b.id]}
            ),
        )
    )
    # The repaired anti-relapse gate (RC2/RC3) fails open without a domain
    # and threshold, so the root's re-proposed candidate is now correctly
    # admitted and a second discrimination problem can spawn later. These
    # regressions are about the FUTILITY BACKOFF, so blocked-attempt counts
    # are scoped to the seeded rivalry.
    harness._rotation_pair = f"{a.id[:12]}v{b.id[:12]}"
    conj_calls = [0]  # conjecturer calls for the ROOT problem specifically

    def _conj(prompt):
        if "PROBLEM pi-root" in prompt:
            conj_calls[0] += 1
        return MOON

    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(_conj),
            "judge": MockEndpoint(lambda prompt: ALWAYS_A),
        },
        harness.blobs,
        retry_max=2,
    )
    config = Config(
        VS_K=1, N_SCHOOLS=0, FUZZ_N=0, JUDGE_SEATS_ENABLED=True, **config_kwargs
    )
    return harness, Scheduler(harness, adapter, config), conj_calls


def _blocked_attempts(harness) -> int:
    pair = getattr(harness, "_rotation_pair", None)
    return sum(
        1 for e in harness.log.read()
        if e.rule == Rule.MEASURE and e.inputs
        and str(e.inputs[0]).startswith("trial-blocked")
        and (pair is None or (len(e.inputs) > 1 and e.inputs[1] == pair))
    )


def test_legacy_starvation_reproduced(tmp_path):
    """The recorded defect, reproduced -- with the wander cap turned OFF.

    Reproducing a PRE-CAP defect requires the pre-cap policy, and since
    F3 (2026-08-26) that is a lawful configuration rather than a code state:
    `ATTENTION_ALLOCATION_POLICY="open-lineage.v1"` is the null throttle in
    `wander.LINEAGE_POLICIES`. Leaving it at the shipped default would not
    reproduce anything, because the cap rescues exactly this shape -- which is
    the point of the test below.
    """
    harness, scheduler, conj_calls = _starvation_setup(
        tmp_path,
        DISC_ATTEMPTS_MAX=None,
        DISC_COOLDOWN=0,
        LIVENESS_QUEUE=False,
        ATTENTION_ALLOCATION_POLICY="open-lineage.v1",
    )
    for _ in range(6):
        scheduler.step()
    # The deadlocked trial keeps being retried (exact count depends on what
    # else spawns into the unsolved pool)...
    assert _blocked_attempts(harness) >= 2
    # ...and the SOLVED root problem is never selected at all: starvation.
    assert conj_calls[0] == 0


def test_the_wander_cap_rescues_the_legacy_starvation_shape(tmp_path):
    """The same fixture, the shipped default, and the root gets worked.

    Free evidence, and worth pinning: the starvation this module was written
    for is a SELF-SPAWNED lineage crowding out the operator's seeded problem,
    which is the same failure W6 measured at scale (41.2 % of one run's budget
    on a problem it invented about its own critic). The cap was designed from
    the token post-mortem, not from this fixture, and it happens to close the
    fixture's own defect with no rotation machinery involved at all --
    `DISC_ATTEMPTS_MAX=None`, `DISC_COOLDOWN=0`, legacy round-robin selection.

    This is a floor, not a cure: the discrimination problem still runs, and
    the assertion below says the root is worked, never that the rival work
    stopped.
    """
    harness, scheduler, conj_calls = _starvation_setup(
        tmp_path, DISC_ATTEMPTS_MAX=None, DISC_COOLDOWN=0, LIVENESS_QUEUE=False
    )
    for _ in range(6):
        scheduler.step()

    assert conj_calls[0] > 0, "the seeded root starved under the shipped default"
    assert _blocked_attempts(harness) >= 1, "the rival work was not stopped"


def test_attempt_cap_frees_the_rotation(tmp_path):
    """The futility cap holds at 2 and the root gets worked.

    Twelve cycles rather than the original eight, and the extra four are the
    wander cap working (F3, 2026-08-26). `disc:rivals` is a SELF-SPAWNED
    lineage and `pi-root` is the operator's seed, so once the seed's share of
    worked cycles falls below `SEED_PROBLEM_BUDGET_FLOOR` the discrimination
    problem yields candidacy and reaches its second attempt later in wall-cycle
    terms. The GUARANTEE is unchanged and is now pinned harder: still exactly
    2 at twelve cycles, and still exactly 2 at twenty-four.
    """
    harness, scheduler, conj_calls = _starvation_setup(
        tmp_path, DISC_ATTEMPTS_MAX=2, DISC_COOLDOWN=1
    )
    for _ in range(12):
        scheduler.step()
    assert _blocked_attempts(harness) == 2  # capped — never retried after that
    assert conj_calls[0] > 0                # the root problem got worked
    for _ in range(12):
        scheduler.step()
    assert _blocked_attempts(harness) == 2  # and still capped, twelve later
    exhausted = [
        e for e in harness.log.read()
        if e.rule == Rule.MEASURE and e.inputs
        and e.inputs[0] == "disc-attempts-exhausted"
        and e.inputs[1] == "disc:rivals"
    ]
    assert len(exhausted) == 1


def test_cooldown_spaces_attempts_and_interleaves_root_work(tmp_path):
    harness, scheduler, conj_calls = _starvation_setup(
        tmp_path, DISC_ATTEMPTS_MAX=None, DISC_COOLDOWN=3
    )
    for _ in range(9):
        scheduler.step()
    # Retries continue (no cap) but are SPACED by the cooldown, and the
    # freed cycles reach the root problem.
    blocked = _blocked_attempts(harness)
    assert 2 <= blocked <= 3
    assert conj_calls[0] > 0


def test_default_config_no_longer_starves(tmp_path):
    harness, scheduler, conj_calls = _starvation_setup(tmp_path)  # shipped defaults
    for _ in range(20):
        scheduler.step()
    assert _blocked_attempts(harness) <= 3  # DISC_ATTEMPTS_MAX default
    assert conj_calls[0] > 0


def test_transport_drop_defers_instead_of_burning_the_futility_cap(tmp_path):
    """A transport failure is not an epistemic verdict: a dropped ruling
    must not count toward DISC_ATTEMPTS_MAX (which pauses the problem
    PERMANENTLY) — the rivalry stays schedulable for when transport heals."""
    from deepreason.llm.endpoints import EndpointError

    harness = Harness(tmp_path / "run")
    a = harness.create_artifact("rival moon A", provenance=Provenance(role="conjecturer"))
    b = harness.create_artifact("rival moon B", provenance=Provenance(role="conjecturer"))
    harness.register_problem(
        Problem(
            id="disc:rivals", description="discriminate the rivals", criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": [a.id, b.id]}
            ),
        )
    )

    def _judge_down(prompt):
        raise EndpointError(
            "no complete response within escalated read timeouts (1s, 2s)"
        )

    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(lambda prompt: MOON),
            "judge": MockEndpoint(_judge_down),
        },
        harness.blobs,
        retry_max=2,
    )
    scheduler = Scheduler(
        harness, adapter,
        Config(
            VS_K=1, N_SCHOOLS=0, FUZZ_N=0, DISC_ATTEMPTS_MAX=2, DISC_COOLDOWN=0,
            JUDGE_SEATS_ENABLED=True,
        ),
    )
    for _ in range(4):
        scheduler.step()

    deferred = [
        e for e in harness.log.read()
        if e.rule == Rule.MEASURE and e.inputs
        and e.inputs[0] == "disc-transport-deferred"
    ]
    exhausted = [
        e for e in harness.log.read()
        if e.rule == Rule.MEASURE and e.inputs
        and e.inputs[0] == "disc-attempts-exhausted"
    ]
    # The drops are logged and deferred; the permanent cap never fires and
    # the problem is still eligible for future selection.
    assert len(deferred) >= 2 and deferred[0].inputs[1] == "disc:rivals"
    assert not exhausted
    assert scheduler._disc_attempts.get("disc:rivals", 0) == 0
    assert not scheduler._disc_paused(harness.state.problems["disc:rivals"])
