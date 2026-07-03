"""why(id) — print the attack/defence chain justifying a status (spec §13).

Computable from grounded semantics: an accepted node's attackers are all
refuted; a refuted node has an accepted attacker; a suspended node has an
unresolved attacker. Deterministic function of the graph.
"""

from deepreason.ontology.state import EpistemicState


def _head(state: EpistemicState, artifact_id: str) -> str:
    a = state.artifacts.get(artifact_id)
    if a is not None and a.content_ref.startswith("inline:"):
        text = a.content_ref[len("inline:"):]
        return f' "{text[:48]}"'
    return ""


def why(artifact_id: str, state: EpistemicState) -> str:
    if artifact_id not in state.artifacts:
        return f"{artifact_id}: not registered"
    lines: list[str] = []

    def visit(aid: str, depth: int, seen: frozenset[str]) -> None:
        status = state.status.get(aid)
        label = status.value if status is not None else "unregistered"
        prefix = "  " * depth + ("<- attacked by " if depth else "")
        lines.append(f"{prefix}{aid[:12]} [{label}]{_head(state, aid)}")
        if aid in seen:
            lines[-1] += " (cycle)"
            return
        for x, target in sorted(state.att):
            if target == aid:
                visit(x, depth + 1, seen | {aid})

    visit(artifact_id, 0, frozenset())
    return "\n".join(lines)
