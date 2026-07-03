"""Synthesizer step (spec §9, §11.1): propose a relation artifact for a
connection/integration problem — the crossover operator between schools.
The relation addresses the problem, carries its criteria (hv-floor), and
declares dependence refs to what it connects; it then runs the normal
Conj -> Crit -> Adj loop (D1: spontaneity in the noticing, discipline in
the adjudication).
"""

from deepreason.llm.contracts import SynthesizerOutput
from deepreason.ontology import Artifact, Interface, Problem, Provenance, Ref, Rule
from deepreason.programs import content_text
from deepreason.rules.guards import anti_relapse


def synthesize(
    harness,
    problem: Problem,
    adapter,
    config,
    school_id: str | None = None,
    embedder=None,
) -> Artifact | None:
    endpoints = [i for i in problem.provenance.from_ if i in harness.state.artifacts]
    if not endpoints:
        return None
    lines = [f"PROBLEM {problem.id}", problem.description, "", "ARTIFACTS TO CONNECT:"]
    for aid in endpoints:
        lines.append(f"- {aid}: {content_text(harness.state.artifacts[aid], harness.blobs)[:200]}")
    lines += ["", "DIRECTIVE: propose one relation; list the ids it connects."]
    output, llm_call = adapter.call("synthesizer", "\n".join(lines), SynthesizerOutput)

    connects = [i for i in output.connects if i in harness.state.artifacts]
    if not connects:
        return None
    interface = Interface(
        commitments=[c for c in problem.criteria if c in harness.commitments],
        refs=[Ref(target=i, role="dependence") for i in dict.fromkeys(connects)],
    )
    content_ref = f"inline:{output.relation}"
    artifact = Artifact(
        id=Artifact.compute_id(content_ref, "utf8", interface),
        content_ref=content_ref,
        codec="utf8",
        interface=interface,
        provenance=Provenance(
            role="synthesizer", school=school_id, event_seq=harness._next_seq
        ),
    )
    admitted, _ = anti_relapse.check(
        artifact, [], harness, embedder=embedder, near_dup_eps=config.NEAR_DUP_EPS
    )
    if not admitted or artifact.id in harness.state.artifacts:
        return None
    harness.register_batch(
        [(artifact, [])], problem_id=problem.id, rule=Rule.CONJ, llm=llm_call
    )
    return harness.state.artifacts[artifact.id]
