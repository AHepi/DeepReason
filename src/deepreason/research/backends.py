"""Research backends and the research service (spec §12).

Evidence enters as an ordinary artifact (provenance.role=import) that
DEPENDS on a source-reliability assertion artifact — the untyped encoding
of "evidence carries a source-reliability validity node": attack the
reliability node and the evidence goes suspended_unsupported (orphaned,
not false), attackable like anything else. The evidence addresses its
research problem, which is what "covering" means (§12): a non-refuted
import-role artifact addressing the problem. Coverage is always DERIVED
from the current graph — never stored as a flag that could drift.

Backend modes (config RESEARCH_BACKEND), each with a distinct meaning:
- "agent": the normal mode for operator-driven runs. No internal fetcher —
  the harness exposes open research problems (ops.research_docket) and
  accepts externally retrieved material (ops.submit_evidence). Research is
  NOT off in this mode; the retrieval loop lives in the operating agent.
- "static:<file>": deterministic local FIXTURE backend (curated offline
  evidence). Not local RAG — no corpus indexing or retrieval ranking.
- "ask-user": attended human retrieval. Only fetches when the run is
  explicitly attended (RESEARCH_ATTENDED); unattended runs never block —
  requests stay visible in the docket.
- null: research deliberately disabled (tests, explicit offline runs, the
  pre-registered lambda=0 arm). Never a euphemism for "an agent is
  servicing the docket" — that is what "agent" says.
Future "local-rag:<config>" and "web-search:<config>" backends remain
separate pluggable implementations.
"""

import json
from pathlib import Path

import yaml

from deepreason.ontology import Artifact, Interface, Provenance, Ref, Status


class StaticBackend:
    """Deterministic FIXTURE backend (curated offline evidence; also the
    test stand-in). corpus maps a query (the research problem description)
    to (evidence_text, source_name). Not local RAG: a plain lookup, no
    indexing or ranking."""

    name = "static"

    def __init__(self, corpus: dict[str, tuple[str, str]]) -> None:
        self.corpus = corpus

    def fetch(self, query: str) -> tuple[str, str] | None:
        return self.corpus.get(query)


class AskUserBackend:
    """Attended human retrieval. Research evidence through this route stays
    distinct from appellate rulings (§10.6) even though the same attended
    interface may serve both workflows. Headless calls return None; the
    disagreement-ranked docket UI lands with P5."""

    name = "ask-user"

    def fetch(self, query: str) -> tuple[str, str] | None:
        return None


class ResearchService:
    """The configured research mode plus (optionally) an internal fetcher.

    In "agent" mode there is no synchronous internal fetcher, but research
    is ACTIVE: the docket and the submission channel service it. Mode
    "off" is the explicit disabled state (RESEARCH_BACKEND: null)."""

    def __init__(self, mode: str, fetcher=None, attended: bool = False) -> None:
        self.mode = mode
        self.fetcher = fetcher
        self.attended = attended

    @property
    def internal(self) -> bool:
        return self.fetcher is not None


VALID_MODES = ("agent", "ask-user", "static:<file>", "null (disabled)")


def load_static_corpus(path: str) -> dict[str, tuple[str, str]]:
    """Load a static fixture file (YAML/JSON): {query: [text, source]}.
    Fails loudly — a missing or malformed fixture must never silently
    degrade to no research."""
    p = Path(path)
    if not p.exists():
        raise ValueError(f"RESEARCH_BACKEND static fixture not found: {path}")
    try:
        raw = yaml.safe_load(p.read_text())
        return {
            str(query): (str(entry[0]), str(entry[1]))
            for query, entry in dict(raw).items()
        }
    except (ValueError, TypeError, IndexError, KeyError, yaml.YAMLError) as e:
        raise ValueError(
            f"RESEARCH_BACKEND static fixture {path} is malformed "
            f"(expected a mapping of query -> [evidence_text, source]): {e}"
        ) from e


def build_service(config) -> ResearchService:
    """RESEARCH_BACKEND -> ResearchService. Invalid values fail loudly at
    startup; nothing here silently degrades to no research."""
    mode = config.RESEARCH_BACKEND
    attended = bool(getattr(config, "RESEARCH_ATTENDED", False))
    if mode is None:
        return ResearchService("off")
    if mode == "agent":
        return ResearchService("agent")
    if mode == "ask-user":
        # Unattended runs get NO internal fetcher: the scheduler must never
        # block on (or pointlessly poll) a human who is not there; requests
        # stay visible in the docket instead. Attended/unattended is
        # explicit config, so the distinction is replay-visible.
        return ResearchService(
            "ask-user", AskUserBackend() if attended else None, attended
        )
    if isinstance(mode, str) and mode.startswith("static:"):
        return ResearchService(
            "static", StaticBackend(load_static_corpus(mode[len("static:"):]))
        )
    raise ValueError(
        f"unknown RESEARCH_BACKEND {mode!r}; valid modes: {VALID_MODES}"
    )


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
        and harness.state.artifacts[aid].provenance.role.value in ("import", "user")
    ]


def covered(harness, research_problem_id: str) -> bool:
    """Covered = an ACCEPTED, READABLE evidence artifact addressing the
    problem — derived from the graph on every call. Acceptance implies the
    candidate passed the problem's relevance/scope commitments (a failed
    commitment refutes it mechanically) AND its reliability support stands
    (lost support = suspended_unsupported, which does not cover). Refuted
    or orphaned evidence doesn't cover (research re-arms); sealed holdout
    evidence doesn't cover pre-Reveal (§10.5)."""
    return any(
        harness.state.status.get(e.id) == Status.ACCEPTED and _readable(harness, e)
        for e in _evidence_for(harness, research_problem_id)
    )


def pending(harness, research_problem_id: str) -> bool:
    """Covered OR sealed-awaiting-Reveal: either way, no research Spawn and
    no fetch — the commitment is scheduled-pending, not failed (§1)."""
    return any(
        harness.state.status.get(e.id)
        not in (Status.REFUTED, Status.SUSPENDED_UNSUPPORTED)
        for e in _evidence_for(harness, research_problem_id)
    )


def register_evidence(
    harness,
    problem,
    content: str | bytes,
    source: str,
    *,
    via: str,
    role: str = "import",
    codec: str = "utf8",
    metadata: dict | None = None,
) -> Artifact:
    """THE canonical evidence registration — one shape for internal
    backends and operator submissions alike (no second evidence ontology).

    Registers CANDIDATE evidence: a source-reliability assertion artifact
    plus an evidence artifact that DEPENDS on it and addresses the research
    problem, carrying the problem's criteria as commitments so relevance
    and scope checks run through the ordinary crit machinery. Registration
    does not itself establish coverage — coverage is derived (covered())
    only while the evidence passes those commitments and remains accepted
    and supported, including accepted source-reliability support.

    ``metadata`` (e.g. the agent-claimed retrieved_at time, title, query)
    is provenance CLAIM data: it renders into the reliability artifact's
    text — attackable, on the record — and never drives event ordering;
    Event.ts stays harness-controlled at registration.
    """
    detail = ""
    if metadata:
        detail = " | " + json.dumps(metadata, sort_keys=True)
    reliability = harness.create_artifact(
        f"source-reliability: {source} ({via}) is a sound source for "
        f"evidence on {problem.id}{detail}",
        provenance=Provenance(role=role),
    )
    carrier_refs = [
        Ref(target=fid, role="mention")
        for fid in problem.provenance.from_
        if fid in harness.state.artifacts
    ]
    criteria = [c for c in problem.criteria if c in harness.commitments]
    return harness.create_artifact(
        content,
        codec=codec,
        interface=Interface(
            refs=[Ref(target=reliability.id, role="dependence"), *carrier_refs],
            commitments=criteria,
        ),
        provenance=Provenance(role=role),
        problem_id=problem.id,
    )


def run_research(harness, problem, backend) -> Artifact | None:
    """Fetch evidence for a research problem and register it (internal
    backends). Returns None on a miss — the CALLER logs the failure; a
    miss must never vanish without trace."""
    result = backend.fetch(problem.description)
    if result is None:
        return None
    content, source = result
    return register_evidence(
        harness, problem, content, source,
        via=getattr(backend, "name", "backend"),
    )
