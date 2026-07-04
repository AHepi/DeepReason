"""Pack renderer (spec §9) — deterministic, budgeted.

P1 renders: problem + compressed criteria + neighbourhood (born-connected,
§7 L1) + VS directive for Conj packs; commitments + target + standing
attackers for Crit packs. School render weights, precedent slices, and
summarizer re-voicing land with P2/P5. Negative case law is NEVER rendered
(§11.5); sealed holdout bytes are excluded until Reveal (§10.5).

Section ORDER is stable-prefix-first (docs/TOKEN_ECONOMY.md angle 4):
slow-changing sections (problem, criteria, school stance, shared
commitment schemas) render before volatile ones (neighbourhood, target
content, directives), so provider prefix caches bill the repeated head at
the cached rate. Ordering is presentation only — zero epistemic content.
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
    school: dict | None = None,
    complement: bool = False,
    specs: list[str] | None = None,
) -> str:
    """school = {"id", "stance_text", "weight"} — lineage inheritance (§11.1):
    the neighbourhood prefers the school's own accepted descendants; the
    stance directive fades as lineage grows. complement is the §11.4
    stagnation directive. specs are Level-2 diversity specifications:
    candidate k must realize spec k (llm/specs.py)."""
    lines = [
        f"PROBLEM {problem.id}",
        problem.description,
        "",
        "CRITERIA (commitments every candidate will carry and face):",
    ]
    for cid in problem.criteria:
        kappa = commitments.get(cid)
        lines.append(f"- {cid}: {kappa.eval if kappa else '(schema pending)'}")
    accepted = [aid for aid, status in state.status.items() if status == Status.ACCEPTED]
    if school is not None:
        lineage = [
            aid for aid in accepted
            if state.artifacts[aid].provenance.school == school["id"]
        ]
        others = [aid for aid in accepted if aid not in set(lineage)]
        accepted = (lineage + others)[:NEIGHBOURHOOD_N]
    else:
        accepted = accepted[-NEIGHBOURHOOD_N:]
    # Stance before neighbourhood: the stance text is stable per school while
    # the neighbourhood changes every cycle — cache-prefix ordering (angle 4).
    if school is not None and school.get("weight", 0) > 0:
        lines += ["", f"SCHOOL STANCE (weight {school['weight']:.2f}): {school['stance_text']}"]
    if accepted:
        lines += ["", "NEIGHBOURHOOD (accepted artifacts; carry dependence refs where natural):"]
        for aid in accepted:
            lines.append(f"- {aid}: {_head(state, aid, blobs)}")
    if complement:
        lines += [
            "",
            "COMPLEMENT DIRECTIVE: produce the attempt these summaries make "
            "least likely — avoid the modal continuation of the neighbourhood.",
        ]
    if specs:
        lines += ["", "DIVERSITY SPECIFICATIONS (binding — candidate k MUST realize spec k):"]
        lines += [f"  spec {i + 1}: {s}" for i, s in enumerate(specs)]
    lines += [
        "",
        f"DIRECTIVE: return exactly {vs_k} diverse candidates with typicality "
        "estimates. Include atypical candidates, not just the modal answer.",
    ]
    return _clip("\n".join(lines), token_budget)


def render_batch_crit_pack(
    target_ids: list[str],
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    token_budget: int,
) -> str:
    """One critic pass over several targets (§14 batching): the commitment
    schemas — usually shared, since batch-mates come from one problem —
    render once; each target carries its content and standing attacks.
    Only the call is shared; every warrant stays per-target."""
    lines = [
        f"TARGETS ({len(target_ids)}) — judge each independently.",
        "",
        "COMMITMENT SCHEMAS (attack surfaces; each target lists its own ids):",
    ]
    seen: set[str] = set()
    for tid in target_ids:
        for cid in state.artifacts[tid].interface.commitments:
            if cid in seen:
                continue
            seen.add(cid)
            kappa = commitments.get(cid)
            lines.append(f"- {cid}: {kappa.eval if kappa else '(unregistered)'}")
    content_chars = max(320, (token_budget * 2) // max(1, len(target_ids)))
    for tid in target_ids:
        target = state.artifacts[tid]
        lines += [
            "",
            f"TARGET {tid}",
            content_text(target, blobs)[:content_chars],
            f"commitments: {', '.join(target.interface.commitments) or '(none)'}",
        ]
        attackers = [x for x, t in sorted(state.att) if t == tid][:ATTACKERS_N]
        if attackers:
            lines.append("standing attacks (do not repeat these):")
            for x in attackers:
                status = state.status.get(x)
                lines.append(f"- {x} [{status.value if status else '?'}]: {_head(state, x, blobs)}")
    lines += [
        "",
        "DIRECTIVE: return exactly one entry per target id above — the "
        "strongest NEW specific case (attack=true) or attack=false. Never "
        "attack an id that is not listed.",
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
    # Commitments render BEFORE the target (angle 4): problem criteria lead
    # each interface list, so sibling targets share this section verbatim
    # and the cacheable prefix runs through it.
    lines = ["TARGET COMMITMENTS (the target's declared attack surface):"]
    for cid in target.interface.commitments:
        kappa = commitments.get(cid)
        lines.append(f"- {cid}: {kappa.eval if kappa else '(unregistered)'}")
    lines += [
        "",
        f"TARGET {target_id}",
        content_text(target, blobs)[: token_budget * 2],
    ]
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
