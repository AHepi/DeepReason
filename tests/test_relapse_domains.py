"""Archived Gemma-shaped anti-relapse and mandatory-interface regressions."""

from deepreason.ontology import (
    Artifact,
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.llm.embedder import HashingEmbedder
from deepreason.rules.crit import crit_program
from deepreason.rules.guards import anti_relapse
from deepreason.workloads.models import MandatoryInterface, compile_interface
from tests.conftest import art


def _problem(harness, problem_id: str) -> Problem:
    return harness.register_problem(
        Problem(
            id=problem_id,
            description=problem_id,
            criteria=["k-required"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


# The archived regression predates the calibrated semantic stage; a wide
# radius routes every prior through the domain checks it exercises.
EMBEDDER = HashingEmbedder()
EPS = 1.5


def _candidate(text: str) -> Artifact:
    interface = Interface(commitments=["k-required"])
    content_ref = f"inline:{text}"
    return Artifact(
        id=Artifact.compute_id(content_ref, "utf8", interface),
        content_ref=content_ref,
        codec="utf8",
        interface=interface,
        provenance=Provenance(role="conjecturer"),
    )


def test_archived_gemma_shape_scopes_battery_equivalence(harness):
    harness.register_commitment(
        Commitment(id="k-required", eval="predicate:'present-marker' in content")
    )
    for problem_id in ("pi-plan", "pi-comp-hero", "pi-comp-copy", "pi-later"):
        _problem(harness, problem_id)

    prior = art(
        harness,
        "hero omits the element",
        interface=Interface(commitments=["k-required"]),
    )
    prior_domain = anti_relapse.relapse_domain(
        prior,
        harness,
        workload_profile="website",
        problem_family="pi-comp-hero",
        contract_id="website.component.compact.v1",
        component_spec="hero-v1",
    )
    anti_relapse.record_domain(harness, prior.id, prior_domain)
    crit_program(harness, prior.id)
    assert harness.state.status[prior.id] == Status.REFUTED

    copy_candidate = _candidate("copy section also omits the element")
    copy_domain = anti_relapse.relapse_domain(
        copy_candidate,
        harness,
        workload_profile="website",
        problem_family="pi-comp-copy",
        contract_id="website.component.compact.v1",
        component_spec="copy-v1",
    )
    admitted, _ = anti_relapse.check(
        copy_candidate, [], harness, embedder=EMBEDDER, near_dup_eps=EPS,
        domain=copy_domain,
    )
    assert admitted

    planning_candidate = _candidate("plan omits the element")
    planning_domain = anti_relapse.relapse_domain(
        planning_candidate,
        harness,
        workload_profile="website",
        problem_family="pi-plan",
        contract_id="website.plan.compact.v1",
        component_spec="plan-v1",
    )
    admitted, _ = anti_relapse.check(
        planning_candidate, [], harness, embedder=EMBEDDER, near_dup_eps=EPS,
        domain=planning_domain,
    )
    assert admitted

    later_candidate = _candidate("later hero still omits content")
    later_domain = anti_relapse.relapse_domain(
        later_candidate,
        harness,
        workload_profile="website",
        problem_family="pi-comp-hero",
        contract_id="website.component.compact.v1",
        component_spec="hero-v2",
    )
    admitted, _ = anti_relapse.check(
        later_candidate, [], harness, embedder=EMBEDDER, near_dup_eps=EPS,
        domain=later_domain,
    )
    assert admitted

    same_domain_candidate = _candidate("same hero again omits the element")
    same_domain = anti_relapse.relapse_domain(
        same_domain_candidate,
        harness,
        workload_profile="website",
        problem_family="pi-comp-hero",
        contract_id="website.component.compact.v1",
        component_spec="hero-v1",
    )
    admitted, reason = anti_relapse.check(
        same_domain_candidate, [], harness, embedder=EMBEDDER, near_dup_eps=EPS,
        domain=same_domain,
    )
    assert not admitted
    assert "battery-equivalent" in reason
    operational = (harness.root / "relapse.log.jsonl").read_text()
    assert "relapse-domain-rejected" in operational


def test_exact_hash_block_remains_global_across_domains(harness):
    harness.register_commitment(
        Commitment(id="k-required", eval="predicate:'present-marker' in content")
    )
    prior = art(
        harness,
        "missing",
        interface=Interface(commitments=["k-required"]),
    )
    crit_program(harness, prior.id)
    assert harness.state.status[prior.id] == Status.REFUTED
    other = anti_relapse.relapse_domain(
        prior,
        harness,
        workload_profile="text",
        problem_family="unrelated",
        contract_id="different",
    )
    admitted, reason = anti_relapse.check(prior, [], harness, domain=other)
    assert not admitted
    assert reason.startswith("hash")


def test_harness_compiles_mandatory_refs_and_criteria_before_identity(harness):
    harness.register_commitment(Commitment(id="k-required", eval="predicate:True"))
    problem = _problem(harness, "pi-text")
    source = art(harness, "pinned source")

    interface = compile_interface(
        harness,
        problem,
        "semantic proposal only",
        mandatory=MandatoryInterface(refs=(source.id,)),
        optional_refs=(("unknown-model-alias", "mention"),),
    )
    artifact_id = Artifact.compute_id("inline:semantic proposal only", "utf8", interface)

    assert interface.commitments == ["k-required"]
    assert [(ref.target, ref.role.value) for ref in interface.refs] == [
        (source.id, "dependence")
    ]
    assert artifact_id != Artifact.compute_id(
        "inline:semantic proposal only", "utf8", Interface()
    )
