"""Spawn (spec §3): register new problems with provenance — all triggers.

- failed verdict            => successor problem
- >=2 surviving rivals      => discrimination problem
- accepted with low HV      => remove-arbitrariness problem
- reach event               => explanation-debt problem
- critic-gaming signal      => audit-the-critic problem (raised by the
                               response ladder, §11.4)
- iso(a) > 0                => connection problem, hv-floor pinned (§7)
- overlapping accepted, no declared relation => integration problem

Brake 2 (§7): abstraction pays rent — connection/integration problems ARE
open problems, so anything addressing them pays rent by construction; the
scheduler caps the budget share. Problem ids are deterministic, so rescans
are idempotent.
"""

from deepreason.measures.hv import hv_floor_commitment
from deepreason.ontology import Problem, ProblemProvenance, SpawnTrigger, Status
from deepreason.unification.isolation import relation_form_commitment, iso, lineage_ref_commitment, rank_neighbours


def spawn(
    harness,
    trigger: SpawnTrigger,
    from_ids: list[str],
    description: str,
    criteria: list[str] = (),
    problem_id: str | None = None,
) -> Problem | None:
    pid = problem_id or f"{trigger.value}:{'+'.join(i[:12] for i in from_ids[:2])}"
    if pid in harness.state.problems:
        return None
    return harness.register_problem(
        Problem(
            id=pid,
            description=description,
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": trigger, "from": list(from_ids)}
            ),
        )
    )


def scan_spawns(harness, config) -> list[Problem]:
    """Idempotent post-registration sweep over every structural trigger."""
    state = harness.state
    status = state.status
    new: list[Problem] = []
    addressed: dict[str, set[str]] = {}
    by_problem: dict[str, list[str]] = {}
    for aid, pid in state.addr:
        addressed.setdefault(aid, set()).add(pid)
        by_problem.setdefault(pid, []).append(aid)

    def _spawn(*args, **kwargs):
        problem = spawn(harness, *args, **kwargs)
        if problem is not None:
            new.append(problem)

    # Successor: a refuted candidate leaves its problem-shift behind. The
    # parent's description carries forward — criteria alone starve the
    # generator of the problem's format/content contract (observed live:
    # successor packs without the skeleton instruction bred prose that
    # skeleton-wf refuted, cascading successors).
    for aid, pids in addressed.items():
        if status.get(aid) != Status.REFUTED:
            continue
        for pid in sorted(pids):
            parent = state.problems[pid]
            # Carry the ROOT description, not the parent's: a successor of a
            # successor would otherwise nest the whole ancestor chain
            # (observed live: 7 levels deep, 52/70 problems multi-nested,
            # compounding pack size per refutation generation). The text
            # after the last marker is the seed description at any depth.
            root_desc = parent.description.rsplit("Original problem: ", 1)[-1]
            _spawn(
                SpawnTrigger.SUCCESSOR,
                [aid, pid],
                f"supersede refuted candidate {aid[:12]} on {pid}. "
                f"Original problem: {root_desc}",
                criteria=parent.criteria,
                problem_id=f"succ:{aid[:12]}",
            )

    # Discrimination: >=2 surviving rivals for one problem. A discrimination
    # problem's own rivals don't re-trigger it (no disc-of-disc regress).
    for pid, aids in by_problem.items():
        if state.problems[pid].provenance.trigger == SpawnTrigger.DISCRIMINATION:
            continue
        rivals = [a for a in aids if status.get(a) == Status.ACCEPTED]
        if len(rivals) >= 2:
            _spawn(
                SpawnTrigger.DISCRIMINATION,
                [pid, *sorted(rivals)],
                f"discriminate between {len(rivals)} surviving rivals for {pid}",
                problem_id=f"disc:{pid}",
            )

    # Remove-arbitrariness: accepted with logged low HV. Carry the ROOT
    # problem's description + criteria (exactly as Successor does) so the
    # sharper re-attempt stays anchored to the original problem. Without the
    # anchor the ra-pack is just "remove arbitrariness of <id>" with no topical
    # or format contract, and long runs drift off-problem into unrelated
    # formalisms that survive only as criticism-debt (observed live: a 200k
    # resume where the ra-loop wandered into abstract mathematics).
    ra_floor = float(config.HV_MIN if config.HV_MIN is not None else 0.5)
    for aid, hv in state.hv.items():
        if status.get(aid) != Status.ACCEPTED or hv >= ra_floor:
            continue
        for pid in sorted(addressed.get(aid, ())):
            parent = state.problems[pid]
            root_desc = parent.description.rsplit("Original problem: ", 1)[-1]
            _spawn(
                SpawnTrigger.REMOVE_ARBITRARINESS,
                [aid],
                f"sharpen accepted {aid[:12]} (hv={hv:.2f}): it is easy-to-vary; "
                f"produce a harder-to-vary version that still addresses the "
                f"problem. Original problem: {root_desc}",
                criteria=parent.criteria,
                problem_id=f"ra:{aid[:12]}",
            )

    # Explanation-debt: reach hits raise standing AND a debt.
    for aid, reach in state.reach.items():
        if reach > 0 and status.get(aid) == Status.ACCEPTED:
            # Reach = cross-problem survival (Def 3.7 as amended): the sweep
            # has already registered the artifact as ADDRESSING the foreign
            # problems, so its addr set names both sides. The debt problem
            # asks the GENUINE explanatory question — what single deeper
            # account covers all of these domains? — and makes commentary
            # about artifacts structurally off-topic: candidates explain the
            # subject matter, carrying the union of the addressed problems'
            # criteria as their attack surface.
            pids = sorted(addressed.get(aid, ()))
            if len(pids) < 2:
                continue  # reach>0 but addressing not yet on record: wait
            union_criteria = sorted({
                c for pid in pids for c in state.problems[pid].criteria
                if c in harness.commitments
            })
            domains = "; ".join(
                f"({pid}) {state.problems[pid].description[:160]}"
                for pid in pids[:4]
            )
            _spawn(
                SpawnTrigger.EXPLANATION_DEBT,
                [aid, *pids],
                "One explanation has survived the criteria of several "
                f"distinct problems: {domains}. Conjecture the deeper "
                "account: what SINGLE explanation of the underlying subject "
                "matter covers all of these domains, and what does it "
                "predict that the narrower explanations do not? Each "
                "candidate MUST be an explanation of the subject matter "
                "itself - never commentary on, or a review of, any existing "
                "artifact or explanation.",
                criteria=union_criteria,
                problem_id=f"debt:{aid[:12]}",
            )

    # Connection: isolation floor (§7 L2); hv-floor + lineage-ref pinned as
    # criteria. lineage-ref is the structural anti-abstraction-escape catch:
    # a candidate must carry a dependence ref into this problem's declared
    # neighbourhood, program-checked, so a skeleton imported from nowhere is
    # refuted before it ever reaches a rubric judge (which criticism-debt was
    # starving on the long runs).
    floor_commitment = hv_floor_commitment(config)
    for aid in addressed:
        if status.get(aid) != Status.ACCEPTED:
            continue
        if iso(aid, state.conn, config.FLOOR) <= 0:
            continue
        neighbours = rank_neighbours(aid, harness, config.K)
        endpoints = [aid, *neighbours]
        lineage = lineage_ref_commitment(endpoints)
        relation_form = relation_form_commitment()
        harness.register_commitment(floor_commitment)
        harness.register_commitment(lineage)
        harness.register_commitment(relation_form)
        _spawn(
            SpawnTrigger.CONNECTION,
            endpoints,
            f"connect isolated {aid[:12]} to its neighbourhood: propose a "
            "SUBSTANTIVE relation (dependence, reduction, shared mechanism, "
            "compatibility, inheritance, integration, contradiction, or "
            "abstraction), naming its kind and stating what it is REFUTED "
            "IF - a summary of the endpoints is not a relation",
            criteria=[floor_commitment.id, lineage.id, relation_form.id],
            problem_id=f"conn:{aid[:12]}",
        )

    # Research (§12): observation-valued commitment, no covering evidence.
    # Sealed holdout evidence is scheduled-pending — no premature Spawn (§10.5).
    from deepreason.research.backends import pending

    for aid, artifact in state.artifacts.items():
        if status.get(aid) == Status.REFUTED:
            continue
        for cid in artifact.interface.commitments:
            kappa = harness.commitments.get(cid)
            if kappa is None or not kappa.observation_valued:
                continue
            rid = f"research:{cid}:{aid[:12]}"
            if rid in state.problems or pending(harness, rid):
                continue
            _spawn(
                SpawnTrigger.RESEARCH,
                [aid, cid],
                f"obtain evidence for observation-valued {cid} on {aid[:12]}",
                problem_id=rid,
            )

    # Integration: accepted artifacts on overlapping problems, no relation.
    accepted = [a for a in addressed if status.get(a) == Status.ACCEPTED]
    dep = set(state.dep)
    for i, a in enumerate(accepted):
        for b in accepted[i + 1 :]:
            if addressed[a] & addressed[b]:
                continue  # same problem => discrimination's job
            shared = set(state.artifacts[a].interface.commitments) & set(
                state.artifacts[b].interface.commitments
            )
            if not shared or (a, b) in dep or (b, a) in dep:
                continue
            x, y = sorted([a, b])
            relation_form = relation_form_commitment()
            harness.register_commitment(relation_form)
            _spawn(
                SpawnTrigger.INTEGRATION,
                [x, y],
                f"relate {x[:12]} and {y[:12]} (shared commitments, no "
                "relation on record): propose ONE substantive relation - "
                "dependence, reduction, shared mechanism, compatibility, "
                "inheritance, partial integration, contradiction, or a "
                "deeper ABSTRACTION from which both follow. Name the "
                "relation kind and state what it is REFUTED IF. A prose "
                "summary of the two artifacts is not a relation.",
                criteria=[relation_form.id],
                problem_id=f"integ:{x[:12]}+{y[:12]}",
            )
    return new
