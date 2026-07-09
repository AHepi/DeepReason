"""why(id) — print the attack/defence chain justifying a status (spec §13).

Computable from grounded semantics: an accepted node's attackers are all
refuted; a refuted node has an accepted attacker; a suspended node has an
unresolved attacker. Deterministic function of the graph.
"""

from deepreason.ontology import Status
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

    # The load-bearing operator mechanic is unwritten (docs/OPERATOR_DIAGNOSIS.md):
    # a status is computed, never set, so a wrong verdict is contested by
    # criticism, not by a tool. Surface the sanctioned move right where the
    # operator sees the bad status — refuted is where every probed model reached
    # for a (nonexistent) verdict-flip instead.
    status = state.status.get(artifact_id)
    if status == Status.REFUTED:
        lines.append("")
        lines.append(
            "To contest: you cannot set a status. Criticize the CRITIC — attack "
            "the validity node (nu) of its warrant above, or seed a problem "
            "targeting the critic's weakness, then fund cycles. If that attack "
            "survives adjudication the target is REINSTATED, computed — never granted."
        )
    elif status in (Status.SUSPENDED, Status.SUSPENDED_UNSUPPORTED):
        lines.append("")
        lines.append(
            "Suspended is not a verdict: an attacker (or a dependence) is "
            "unresolved. Fund cycles to resolve the open attack, or criticize "
            "it — status is computed, never set."
        )
    return "\n".join(lines)
