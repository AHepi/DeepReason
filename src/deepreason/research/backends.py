"""Research backends (spec §12): web-search | local-RAG | ask-user.

Evidence enters as an ordinary artifact (provenance.role=import) that
DEPENDS on a source-reliability assertion artifact — the untyped encoding
of "evidence carries a source-reliability validity node": attack the
reliability node and the evidence goes suspended_unsupported (orphaned,
not false), attackable like anything else. The evidence addresses its
research problem, which is what "covering" means (§12): a non-refuted
import-role artifact addressing the problem.
"""

from deepreason.ontology import Artifact, Interface, Provenance, Ref, Status


class StaticBackend:
    """Deterministic corpus backend — tests and local-RAG stand-in.
    corpus maps a query (the research problem description) to
    (evidence_text, source_name)."""

    name = "static"

    def __init__(self, corpus: dict[str, tuple[str, str]]) -> None:
        self.corpus = corpus

    def fetch(self, query: str) -> tuple[str, str] | None:
        return self.corpus.get(query)


class AskUserBackend:
    """Doubles as the appellate channel (§10.6). Headless runs get None;
    the disagreement-ranked docket UI lands with P5."""

    name = "ask-user"

    def fetch(self, query: str) -> tuple[str, str] | None:
        return None


def covered(harness, research_problem_id: str) -> bool:
    """A research problem is covered by an ACCEPTED import artifact
    addressing it — refuted or orphaned evidence (source reliability under
    successful attack) does not cover, so research re-arms. Sealed holdout
    evidence will not count pre-Reveal (P5)."""
    return any(
        pid == research_problem_id
        and harness.state.artifacts[aid].provenance.role.value == "import"
        and harness.state.status.get(aid) == Status.ACCEPTED
        for aid, pid in harness.state.addr
    )


def run_research(harness, problem, backend) -> Artifact | None:
    """Fetch evidence for a research problem and register it."""
    result = backend.fetch(problem.description)
    if result is None:
        return None
    content, source = result
    reliability = harness.create_artifact(
        f"source-reliability: {source} ({backend.name}) is a sound source for "
        f"evidence on {problem.id}",
        provenance=Provenance(role="import"),
    )
    carrier_refs = [
        Ref(target=fid, role="mention")
        for fid in problem.provenance.from_
        if fid in harness.state.artifacts
    ]
    return harness.create_artifact(
        content,
        interface=Interface(
            refs=[Ref(target=reliability.id, role="dependence"), *carrier_refs]
        ),
        provenance=Provenance(role="import"),
        problem_id=problem.id,
    )
