"""Anti-relapse gate (spec §3, §11.5; bronze postrun repair RC2-RC4):
hash stage, degraded fail-open scope, discriminating battery, and complete
block receipts."""

import json

from deepreason.informal.skeleton import skeleton_wf_commitment
from deepreason.llm.embedder import HashingEmbedder, distance
from deepreason.ontology import (
    Artifact,
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.rules.conj import root_problem_family
from deepreason.rules.crit import crit_program
from deepreason.rules.guards import anti_relapse
from deepreason.rules.guards.anti_relapse import check
from tests.conftest import art, attack

EMBEDDER = HashingEmbedder()
EPS = 0.35  # calibrated below: paraphrase ~0.10, far candidates >= 0.6


def _skeleton(claim: str, mechanism: str, case: str) -> str:
    return json.dumps(
        {
            "claim": claim,
            "mechanism": mechanism,
            "forbidden": [{"case": case, "eval": "rubric:std-collapse"}],
        },
        sort_keys=True,
    )


SYSTEMS = _skeleton(
    "the bronze age collapse was a systems-network failure",
    "interdependent palace economies transmitted local shocks through trade "
    "and tribute links until the whole exchange network unravelled",
    "a polity collapses with no upstream trade disruption",
)
PARAPHRASE = _skeleton(
    "the bronze age collapse was a failure of the systems network",
    "interdependent palace economies transmitted local shocks through tribute "
    "and trade links until the exchange network unravelled entirely",
    "a polity collapses with no upstream trade disruption",
)
# Shortened stand-ins for the retained bronze-run candidates: the admitted
# systems-network conjecture vs the blocked peasant/merchant-revolt and
# elite-gift-exchange proposals.
PEASANT = _skeleton(
    "the bronze age collapse was driven by peasant and merchant revolt",
    "rural producers and traders withdrew labour and goods from palace "
    "redistribution, starving elite centres until administration failed",
    "records show stable rural tribute flows during the terminal decades",
)
GIFT = _skeleton(
    "the collapse followed elite gift-exchange breakdown",
    "prestige-good circulation between courts stopped legitimating rulers, "
    "so vassal hierarchies dissolved from the top",
    "prestige goods keep circulating while polities still fall",
)


def _unregistered(text: str, commitments: list[str]) -> Artifact:
    interface = Interface(commitments=commitments)
    content_ref = f"inline:{text}"
    return Artifact(
        id=Artifact.compute_id(content_ref, "utf8", interface),
        content_ref=content_ref,
        codec="utf8",
        interface=interface,
        provenance=Provenance(role="conjecturer"),
    )


def _domain(harness, artifact, family: str = "pi-collapse"):
    return anti_relapse.relapse_domain(
        artifact,
        harness,
        workload_profile="text",
        problem_family=family,
        contract_id="test.conjecturer.v1",
    )


def _register_battery(harness) -> list[str]:
    """skeleton-wf (structural) + one substantive content predicate."""
    if "skeleton-wf" not in harness.commitments:
        harness.register_commitment(skeleton_wf_commitment())
    if "k-bronze" not in harness.commitments:
        harness.register_commitment(
            Commitment(
                id="k-bronze",
                eval="predicate:'bronze-evidence-marker' in content",
            )
        )
    return ["skeleton-wf", "k-bronze"]


def _refuted_prior(harness, content: str = SYSTEMS, family: str = "pi-collapse"):
    """Register a valid skeleton, record its domain, refute it by program."""
    commitments = _register_battery(harness)
    prior = art(
        harness,
        content,
        interface=Interface(commitments=commitments),
        provenance=Provenance(role="conjecturer"),
    )
    anti_relapse.record_domain(harness, prior.id, _domain(harness, prior, family))
    crit_program(harness, prior.id)  # k-bronze fails: the marker is absent
    assert harness.state.status[prior.id] == Status.REFUTED
    return prior


def _receipts(harness, kind: str) -> list[dict]:
    path = harness.root / "relapse.log.jsonl"
    if not path.exists():
        return []
    entries = [json.loads(line) for line in path.read_text().splitlines()]
    return [entry for entry in entries if entry.get("type") == kind]


def test_hash_stage_blocks_refuted_resubmission(harness):
    prior = _refuted_prior(harness)
    resubmission = _unregistered(SYSTEMS, ["skeleton-wf", "k-bronze"])
    assert resubmission.id == prior.id  # same content + interface => same id
    # Hash blocking is global and unconditional: no embedder, eps, or domain.
    admitted, reason = check(resubmission, [], harness)
    assert not admitted
    assert reason.startswith("hash")


def test_structural_only_does_not_block(harness):
    """RC2: a battery reduced to structural well-formedness (skeleton-wf)
    cannot make a semantically different valid skeleton 'equivalent' to a
    refuted one. Only skeleton-wf + rubric commitments are shared here, so
    even a worst-case semantic trigger must admit."""
    if "skeleton-wf" not in harness.commitments:
        harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="k-taste", eval="rubric:std-collapse"))
    prior = art(
        harness,
        SYSTEMS,
        interface=Interface(commitments=["skeleton-wf", "k-taste"]),
        provenance=Provenance(role="conjecturer"),
    )
    anti_relapse.record_domain(harness, prior.id, _domain(harness, prior))
    attack(harness, prior.id, "the network story ignores documented droughts")
    assert harness.state.status[prior.id] == Status.REFUTED

    candidate = _unregistered(GIFT, ["skeleton-wf", "k-taste"])
    # eps=2.0 forces every refuted prior through the battery stage: the
    # admission must come from the discriminating-battery rule, not distance.
    admitted, reason = check(
        candidate,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=2.0,
        domain=_domain(harness, candidate),
    )
    assert admitted, reason
    receipts = _receipts(harness, "relapse-structural-only")
    assert receipts
    assert receipts[-1]["candidate_id"] == candidate.id
    assert receipts[-1]["prior_id"] == prior.id
    assert receipts[-1]["battery"] == ["skeleton-wf"]


def test_semantic_near_duplicate_blocks(harness):
    """Calibrated embedder + threshold + matching domain: a close paraphrase
    of a refuted skeleton blocks, and the block receipt is complete."""
    prior = _refuted_prior(harness)
    candidate = _unregistered(PARAPHRASE, ["skeleton-wf", "k-bronze"])
    d = distance(EMBEDDER.embed(PARAPHRASE), EMBEDDER.embed(SYSTEMS))
    assert d <= EPS  # the pair really is a near-duplicate at this threshold
    admitted, reason = check(
        candidate,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=EPS,
        domain=_domain(harness, candidate),
    )
    assert not admitted
    assert "battery-equivalent" in reason
    receipt = _receipts(harness, "relapse-block")[-1]
    assert receipt["candidate_id"] == candidate.id
    assert receipt["prior_id"] == prior.id
    assert receipt["domain_digest"] == _domain(harness, candidate).digest
    assert receipt["embedder_fingerprint"]["model"] == EMBEDDER.fingerprint()["model"]
    assert receipt["distance"] <= receipt["threshold"] == EPS
    assert receipt["battery"] == ["k-bronze", "skeleton-wf"]
    assert receipt["candidate_verdicts"] == receipt["prior_verdicts"]
    assert len(receipt["candidate_verdicts"]) == len(receipt["battery"])
    assert receipt["refuter_ids"]
    assert all(
        harness.state.status[refuter] == Status.ACCEPTED
        for refuter in receipt["refuter_ids"]
    )
    assert all(
        (refuter, prior.id) in set(harness.state.att)
        for refuter in receipt["refuter_ids"]
    )


def test_semantic_far_candidate_admits(harness):
    """The peasant-revolt stand-in must not be blocked as equivalent to the
    refuted systems-network stand-in: it sits outside the calibrated radius,
    so the battery stage never runs against it."""
    _refuted_prior(harness)
    candidate = _unregistered(PEASANT, ["skeleton-wf", "k-bronze"])
    d = distance(EMBEDDER.embed(PEASANT), EMBEDDER.embed(SYSTEMS))
    assert d > EPS  # genuinely different mechanism at this threshold
    admitted, reason = check(
        candidate,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=EPS,
        domain=_domain(harness, candidate),
    )
    assert admitted, reason
    assert not _receipts(harness, "relapse-block")


def test_successor_family_scope(harness):
    """A successor problem scopes its domain by the stable provenance-root
    family key: the root's negative case law still applies (a paraphrase
    blocks), and nothing falls back to a global comparison."""
    root = harness.register_problem(
        Problem(
            id="pi-collapse",
            description="explain the bronze age collapse",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    prior = _refuted_prior(harness, family=root_problem_family(harness.state, root.id))
    successor = harness.register_problem(
        Problem(
            id=f"succ:{root.id}:1",
            description="successor after the first refutation",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "successor", "from": [root.id]}
            ),
        )
    )
    family = root_problem_family(harness.state, successor.id)
    assert family == root.id  # the stable key, not the successor's own id
    candidate = _unregistered(PARAPHRASE, ["skeleton-wf", "k-bronze"])
    admitted, reason = check(
        candidate,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=EPS,
        domain=_domain(harness, candidate, family=family),
    )
    assert not admitted
    assert prior.id[:12] in reason
    # A domain keyed on the successor's own id would have missed the prior.
    fresh = _unregistered(PARAPHRASE + " ", ["skeleton-wf", "k-bronze"])
    admitted, _ = check(
        fresh,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=EPS,
        domain=_domain(harness, fresh, family=successor.id),
    )
    assert admitted  # scope mismatch admits; it never widens to global


def test_missing_threshold_fails_open(harness):
    """With NEAR_DUP_EPS missing only the exact-hash stage blocks; the
    degraded mode lands as an operational receipt, never a silent global
    battery comparison (the bronze-run failure)."""
    prior = _refuted_prior(harness)
    candidate = _unregistered(PARAPHRASE, ["skeleton-wf", "k-bronze"])
    admitted, reason = check(
        candidate,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=None,
        domain=_domain(harness, candidate),
    )
    assert admitted
    assert reason.startswith("admitted-degraded")
    receipt = _receipts(harness, "relapse-gate-degraded")[-1]
    assert receipt["missing"] == ["near_dup_eps"]
    assert receipt["candidate_id"] == candidate.id
    # The hash stage is unaffected by the degradation.
    resubmission = _unregistered(SYSTEMS, ["skeleton-wf", "k-bronze"])
    assert resubmission.id == prior.id
    admitted, reason = check(
        resubmission,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=None,
        domain=_domain(harness, resubmission),
    )
    assert not admitted and reason.startswith("hash")


def test_differing_verdicts_admit(harness):
    """A near-duplicate whose verdict vector differs is a near-miss
    diagnostic, never a block."""
    _refuted_prior(harness)
    passing = json.loads(PARAPHRASE)
    passing["mechanism"] += " (bronze-evidence-marker attested)"
    content = json.dumps(passing, sort_keys=True)
    candidate = _unregistered(content, ["skeleton-wf", "k-bronze"])
    assert distance(EMBEDDER.embed(content), EMBEDDER.embed(SYSTEMS)) <= EPS
    admitted, _ = check(
        candidate,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=EPS,
        domain=_domain(harness, candidate),
    )
    assert admitted


def test_counter_warrant_exempts(harness):
    """~=_B to a refuted prior is admitted iff the candidate carries a
    warrant against the prior's accepted refuter (spec §3 stage 3). The
    exemption applies to callers that supply warrants; production Conj
    relies on the block receipt's refuter_ids instead."""
    prior = _refuted_prior(harness)
    refuter = next(
        x
        for x, t in harness.state.att
        if t == prior.id and harness.state.status[x] == Status.ACCEPTED
    )
    nu = art(harness, "nu: the k-bronze test is unfair here")
    counter = Warrant(
        id="w-counter",
        target=refuter,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu.id,
    )
    candidate = _unregistered(PARAPHRASE, ["skeleton-wf", "k-bronze"])
    admitted, _ = check(
        candidate,
        [counter],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=EPS,
        domain=_domain(harness, candidate),
    )
    assert admitted


def test_near_duplicates_of_accepted_never_blocked(harness):
    _register_battery(harness)
    accepted = art(
        harness,
        SYSTEMS + " with the bronze-evidence-marker attested",
        interface=Interface(commitments=["k-bronze"]),
    )
    assert harness.state.status[accepted.id] == Status.ACCEPTED
    twin = _unregistered(
        SYSTEMS + " with the bronze-evidence-marker attested twice", ["k-bronze"]
    )
    admitted, _ = check(
        twin,
        [],
        harness,
        embedder=EMBEDDER,
        near_dup_eps=EPS,
        domain=_domain(harness, twin),
    )
    assert admitted  # blocking would be a diversity gate adjudicating (§0)
