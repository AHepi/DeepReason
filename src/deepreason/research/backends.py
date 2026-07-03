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


def _readable(harness, artifact) -> bool:
    if artifact.content_ref.startswith("inline:"):
        return True
    try:
        harness.blobs.get(artifact.content_ref)
        return True
    except KeyError:
        return False


def _evidence_for(harness, research_problem_id: str):
    return [
        harness.state.artifacts[aid]
        for aid, pid in harness.state.addr
        if pid == research_problem_id
        and harness.state.artifacts[aid].provenance.role.value == "import"
    ]


def covered(harness, research_problem_id: str) -> bool:
    """Covered = an ACCEPTED, READABLE import artifact addressing the
    problem. Refuted/orphaned evidence doesn't cover (research re-arms);
    sealed holdout evidence doesn't cover pre-Reveal (§10.5)."""
    return any(
        harness.state.status.get(e.id) == Status.ACCEPTED and _readable(harness, e)
        for e in _evidence_for(harness, research_problem_id)
    )


def pending(harness, research_problem_id: str) -> bool:
    """Covered OR sealed-awaiting-Reveal: either way, no research Spawn and
    no fetch — the commitment is scheduled-pending, not failed (§1)."""
    return any(
        harness.state.status.get(e.id) != Status.REFUTED
        for e in _evidence_for(harness, research_problem_id)
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
