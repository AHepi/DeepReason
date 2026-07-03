"""Pack renderer (spec §9) — deterministic, budgeted.

P1 renders: problem + compressed criteria + neighbourhood (born-connected,
§7 L1) + VS directive for Conj packs; target + commitments + standing
attackers for Crit packs. School render weights, precedent slices, and
summarizer re-voicing land with P2/P5. Negative case law is NEVER rendered
(§11.5); sealed holdout bytes are excluded until Reveal (§10.5).
"""

from deepreason.ontology.commitment import Commitment
from deepreason.ontology.problem import Problem
from deepreason.ontology.state import EpistemicState, Status
from deepreason.programs import content_text

_CHARS_PER_TOKEN = 4
NEIGHBOURHOOD_N = 8
ATTACKERS_N = 5


def _head(state: EpistemicState, artifact_id: str, blobs, limit: int = 160) -> str:
    text = content_text(state.artifacts[artifact_id], blobs)
    return text[:limit].replace("\n", " ")


def _clip(text: str, token_budget: int) -> str:
    return text[: token_budget * _CHARS_PER_TOKEN]


def render_conj_pack(
    problem: Problem,
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    vs_k: int,
    token_budget: int,
) -> str:
    lines = [
        f"PROBLEM {problem.id}",
        problem.description,
        "",
        "CRITERIA (commitments every candidate will carry and face):",
    ]
    for cid in problem.criteria:
        kappa = commitments.get(cid)
        lines.append(f"- {cid}: {kappa.eval if kappa else '(schema pending)'}")
    accepted = [
        aid for aid, status in state.status.items() if status == Status.ACCEPTED
    ][-NEIGHBOURHOOD_N:]
    if accepted:
        lines += ["", "NEIGHBOURHOOD (accepted artifacts; carry dependence refs where natural):"]
        for aid in accepted:
            lines.append(f"- {aid}: {_head(state, aid, blobs)}")
    lines += [
        "",
        f"DIRECTIVE: return exactly {vs_k} diverse candidates with typicality "
        "estimates. Include atypical candidates, not just the modal answer.",
    ]
    return _clip("\n".join(lines), token_budget)


def render_crit_pack(
    target_id: str,
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    token_budget: int,
) -> str:
    target = state.artifacts[target_id]
    lines = [
        f"TARGET {target_id}",
        content_text(target, blobs)[: token_budget * 2],
        "",
        "TARGET COMMITMENTS (its declared attack surface):",
    ]
    for cid in target.interface.commitments:
        kappa = commitments.get(cid)
        lines.append(f"- {cid}: {kappa.eval if kappa else '(unregistered)'}")
    attackers = [x for x, t in sorted(state.att) if t == target_id][:ATTACKERS_N]
    if attackers:
        lines += ["", "STANDING ATTACKS (do not repeat these):"]
        for x in attackers:
            status = state.status.get(x)
            lines.append(f"- {x} [{status.value if status else '?'}]: {_head(state, x, blobs)}")
    lines += [
        "",
        "DIRECTIVE: mount the strongest NEW specific case against the target, "
        "or attack=false if you find no genuine fault.",
    ]
    return _clip("\n".join(lines), token_budget)
