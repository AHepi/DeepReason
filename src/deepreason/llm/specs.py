"""Level-2 diversity injection (docs/research: Diverse Outline / Keyword
Combo) — specification-level diversity, one stage before generation.

Verbalized Sampling asks for diverse outputs; observed live, that still
mode-collapses at the stem level ("This is...", "That is..."). Level-2
injection instead spends ONE extra call generating orthogonal
SPECIFICATIONS (angle/structure/register outlines), then binds candidate k
to spec k inside the gamma pack. Input-side only: the stateless-gamma
constraint (§0/D2) is untouched, and the whole mechanism is attention —
it shapes what gets proposed, never what survives.

The transmission score checks the specs actually bound: the fraction of
candidates whose embedding sits closest to their OWN spec. Logged as a
Measure event, so it is a replay-derivable diagnostic (§11.3 spirit) and
feeds the eval report's escape-efficacy story.
"""

from pydantic import BaseModel, Field

from deepreason.llm.embedder import distance
from deepreason.ontology import LLMCall
from deepreason.ontology.problem import Problem


class SpecsOutput(BaseModel):
    specs: list[str] = Field(min_length=1)


def generate_specs(harness, adapter, problem: Problem, config) -> tuple[list[str], LLMCall]:
    """One call on the conjecturer endpoint with the spec-generator template."""
    pack = "\n".join([
        f"PROBLEM {problem.id}",
        problem.description,
        "",
        f"DIRECTIVE: produce exactly {config.VS_K} mutually orthogonal "
        "specifications. Each is a compact keyword outline (angle; mechanism "
        "family; structure; register) for one future candidate. Maximize the "
        "pairwise difference between specifications — no two may share an "
        "angle or mechanism family.",
    ])
    output, llm_call = adapter.call(
        "conjecturer", pack, SpecsOutput, template_role="spec_generator"
    )
    return [s.strip() for s in output.specs[: config.VS_K] if s.strip()], llm_call


def transmission_score(specs: list[str], contents: list[str], embedder) -> float | None:
    """Fraction of candidates embedding-closest to their own spec. 1.0 =
    every spec bound; ~1/len(specs) = specs were ignored."""
    if not specs or not contents or len(specs) < 2:
        return None
    spec_vecs = [embedder.embed(s) for s in specs]
    hits = 0
    scored = 0
    for i, content in enumerate(contents[: len(specs)]):
        c = embedder.embed(content)
        nearest = min(range(len(spec_vecs)), key=lambda j: distance(c, spec_vecs[j]))
        hits += 1 if nearest == i else 0
        scored += 1
    return hits / scored if scored else None
