"""theory(id) view (spec §8).

Walk the refs-union-dep closure from id; render content, per-component
status, attack surface, standing attacks, and status history from the log.
Deterministic function of the graph — cannot drift. Time-travel by passing
a Harness.at() state/log.
"""

from deepreason.ontology.state import EpistemicState
from deepreason.programs import content_text


def theory(artifact_id: str, state: EpistemicState, blobs, log=None) -> str:
    if artifact_id not in state.artifacts:
        return f"{artifact_id}: not registered"
    # BFS closure over refs (dep edges derive from dependence refs).
    order: list[str] = []
    seen = {artifact_id}
    queue = [artifact_id]
    while queue:
        node = queue.pop(0)
        order.append(node)
        artifact = state.artifacts[node]
        for ref in artifact.interface.refs:
            if ref.target in state.artifacts and ref.target not in seen:
                seen.add(ref.target)
                queue.append(ref.target)

    lines = [f"# Theory: {artifact_id[:12]}", ""]
    for node in order:
        artifact = state.artifacts[node]
        status = state.status.get(node)
        lines += [
            f"## {node[:12]} [{status.value if status else '?'}]",
            "",
            content_text(artifact, blobs)[:400],
            "",
        ]
        if artifact.interface.commitments:
            lines.append(
                "- attack surface: " + ", ".join(artifact.interface.commitments)
            )
        refs = [f"{r.target[:12]} ({r.role.value})" for r in artifact.interface.refs]
        if refs:
            lines.append("- refs: " + ", ".join(refs))
        attackers = [
            f"{x[:12]} [{state.status[x].value}]"
            for x, t in sorted(state.att)
            if t == node
        ]
        if attackers:
            lines.append("- attacked by: " + ", ".join(attackers))
        if log is not None:
            history = [
                str(e.seq) for e in log.read() if node in e.state_diff.status_changed
            ]
            if history:
                lines.append("- status changed at seq: " + ", ".join(history))
        lines.append("")
    return "\n".join(lines)
