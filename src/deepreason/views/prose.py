"""prose(id) view (spec §8, §10.1).

For skeleton-codec artifacts, render the readable narrative from the
skeleton — the skeleton is what gets criticized; prose is a view, never
adjudicated. Uses the summarizer role when configured (re-voicing, §9);
otherwise a deterministic template render.
"""

from deepreason.informal.skeleton import parse_skeleton
from deepreason.ontology.state import EpistemicState
from deepreason.programs import content_text


def prose(artifact_id: str, state: EpistemicState, blobs, adapter=None) -> str:
    if artifact_id not in state.artifacts:
        return f"{artifact_id}: not registered"
    text = content_text(state.artifacts[artifact_id], blobs)
    skeleton = parse_skeleton(text)
    if skeleton is None:
        return text
    if adapter is not None and adapter.has_role("summarizer"):
        from deepreason.llm.contracts import ProseOutput

        output, _ = adapter.call("summarizer", text, ProseOutput)
        return output.prose
    lines = [skeleton.claim, "", f"Mechanism: {skeleton.mechanism}"]
    if skeleton.scope.covers:
        lines.append("Covers: " + "; ".join(skeleton.scope.covers))
    if skeleton.scope.excludes:
        lines.append("Excludes: " + "; ".join(skeleton.scope.excludes))
    if skeleton.forbidden:
        lines.append("This account fails if: " + "; ".join(f.case for f in skeleton.forbidden))
    if skeleton.prose_notes:
        lines += ["", skeleton.prose_notes]
    return "\n".join(lines)
