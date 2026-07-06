"""User as appellate court (spec §10.6).

A disagreement-ranked docket (ensemble splits, guard-block streaks, audit
hits, maximum-entropy rivalries) — never round-robin, capped at
USER_RULINGS_BUDGET: the user is the scarce calibration resource and is
spent where the machine is most confused. Each ruling registers as a
precedent artifact (provenance.role: user) with a mention ref to the
standard it calibrates: ranked first in precedent slices, yet an ordinary
artifact — attackable, reinstateable (N1). Appellate, not oracle. A
starved docket degrades calibration silently; the docket makes starvation
visible, which is the most the design can do (§17).
"""

import json

from deepreason.informal.standards import resolve_standard
from deepreason.ontology import Interface, Provenance, Ref, SpawnTrigger, Status


def docket(harness, config) -> list[dict]:
    """Disagreement-ranked queue, capped at USER_RULINGS_BUDGET."""
    scores: dict[str, dict] = {}

    def bump(case: str, kind: str, weight: int = 1) -> None:
        entry = scores.setdefault(case, {"case": case, "kinds": set(), "score": 0})
        entry["score"] += weight
        entry["kinds"].add(kind)

    for event in harness.log.read():
        for tag in event.inputs:
            if tag.startswith("trial-blocked:ensemble-split"):
                bump(event.inputs[-1], "ensemble-split", 3)
            elif tag.startswith("trial-blocked:"):
                bump(event.inputs[-1], "guard-block", 1)
            elif tag.startswith("audit-hit:"):
                bump(tag.split(":", 1)[1], "audit-hit", 2)
    # Maximum-entropy rivalries: open discrimination problems.
    for problem in harness.state.problems.values():
        if problem.provenance.trigger != SpawnTrigger.DISCRIMINATION:
            continue
        rivals = [
            i for i in problem.provenance.from_
            if harness.state.status.get(i) == Status.ACCEPTED
        ]
        if len(rivals) >= 2:
            bump(problem.id, "unresolved-rivalry", 2)

    ranked = sorted(scores.values(), key=lambda e: (-e["score"], e["case"]))
    for entry in ranked:
        entry["kinds"] = sorted(entry["kinds"])
        # Which standard(s) a ruling on this case would calibrate — without
        # this, an operator must GUESS the spec id for appellate_rule
        # (observed live: an operator invented 'std-explain' and was
        # rejected). Empty list = no rubric standard applies: appellate_rule
        # is not the instrument for this case.
        entry["standards"] = _standards_for(harness, entry["case"])
    return ranked[: config.USER_RULINGS_BUDGET]


def _standards_for(harness, case: str) -> list[str]:
    """Rubric spec ids reachable from a docket case: the trial target's
    rubric commitments, a nu's mentioned standard artifact, or a problem's
    rubric criteria."""
    specs: set[str] = set()

    def from_commitments(cids) -> None:
        for cid in cids:
            kappa = harness.commitments.get(cid)
            if kappa is not None and kappa.eval.startswith("rubric:"):
                specs.add(kappa.eval.split(":", 1)[1])

    artifact = harness.state.artifacts.get(case)
    if artifact is not None:
        from_commitments(artifact.interface.commitments)
        for ref in artifact.interface.refs:  # a nu MENTIONS its standard
            target = harness.state.artifacts.get(ref.target)
            if target is None or not target.content_ref.startswith("inline:"):
                continue
            try:
                body = json.loads(target.content_ref[len("inline:"):])
            except ValueError:
                continue
            spec = (body.get("standard") or {}).get("spec")
            if spec:
                specs.add(spec)
    problem = harness.state.problems.get(case)
    if problem is not None:
        from_commitments(problem.criteria)
        for aid in problem.provenance.from_:
            rival = harness.state.artifacts.get(aid)
            if rival is not None:
                from_commitments(rival.interface.commitments)
    return sorted(specs)


def rule(harness, case_id: str, holding: str, spec_id: str):
    """Enter an appellate ruling: a precedent artifact calibrating spec_id."""
    standard = resolve_standard(harness, spec_id)
    if standard is None:
        raise KeyError(f"no standard registered for spec {spec_id!r}")
    return harness.create_artifact(
        json.dumps(
            {"precedent": {"case": case_id, "holding": holding}}, sort_keys=True
        ),
        codec="json",
        interface=Interface(refs=[Ref(target=standard.id, role="mention")]),
        provenance=Provenance(role="user"),
    )


def spawn_audit_problem(harness, reason: str) -> None:
    from deepreason.rules.spawn import spawn

    spawn(
        harness,
        SpawnTrigger.AUDIT_CRITIC,
        [],
        f"audit the critic: {reason}",
        problem_id=f"audit:{reason}",
    )
