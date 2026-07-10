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

import json

from deepreason.ontology.commitment import Commitment
from deepreason.ontology.problem import Problem
from deepreason.ontology.state import EpistemicState, Status
from deepreason.oracle import EXEC_PROGRAMS
from deepreason.programs import content_text

_CHARS_PER_TOKEN = 4
NEIGHBOURHOOD_N = 8
ATTACKERS_N = 5
FOUNDATION_CHARS = 8000  # total across all lineage endpoints in one pack

_EXECUTION_EVALS = {f"program:{p}" for p in EXEC_PROGRAMS}

_COUNTEREXAMPLE_NOTE = (
    "EXECUTION-BACKED TARGETS: a target whose commitments include an "
    "execution oracle is judged by RUNNING it — if it currently passes, a "
    "purely argumentative case CANNOT refute it. To refute such a target, "
    "also return \"counterexample\": a JSON list of positional args for its "
    "entry point; the harness will run the target on it and check the "
    "declared property. An input the problem's gate rejects, or one the "
    "target handles correctly, grounds nothing."
)


def _active_property_claims(state: EpistemicState, blobs, criteria: list[str]) -> list[str]:
    """Docstring claims of ACCEPTED proposed properties (code:python-prop
    artifacts with a MENTION ref into the problem's criteria). Shown to the
    conjecturer so candidates comply with the run's validated standards up
    front — presentation only (§9); the checkers still decide everything.
    (Reimplemented from rules/experiment.py against raw state: packs must not
    import rules.)"""
    from deepreason.ontology.artifact import RefRole

    criteria_set = set(criteria)
    claims: list[str] = []
    for aid, artifact in state.artifacts.items():
        if artifact.codec != "code:python-prop":
            continue
        if state.status.get(aid) != Status.ACCEPTED:
            continue
        if not any(
            r.role == RefRole.MENTION and r.target in criteria_set
            for r in artifact.interface.refs
        ):
            continue
        text = content_text(artifact, blobs)
        if text.startswith('"""'):
            end = text.find('"""', 3)
            if end > 0:
                claims.append(text[3:end].strip())
    return claims


def _lineage_foundation(
    problem: Problem,
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
) -> list[str]:
    """FOUNDATION section: full content of the lineage-ref endpoints the
    problem's criteria freeze (staged pipelines: the surviving plan/design
    the next stage must build on). Presentation only (§9) — the AUTHORITY
    is the program:lineage_ref commitment itself, which mechanically
    refutes any candidate that fails to declare the dependence. The
    endpoint set is frozen into the commitment id, so this section is
    static for the life of the problem and all its successors — it belongs
    in the cacheable prefix."""
    endpoints: list[str] = []
    for cid in problem.criteria:
        kappa = commitments.get(cid)
        if kappa is None or kappa.eval != "program:lineage_ref":
            continue
        for eid in (kappa.budget.extra.get("endpoints") or "").split(","):
            if eid and eid in state.artifacts and eid not in endpoints:
                endpoints.append(eid)
    if not endpoints:
        return []
    per_endpoint = FOUNDATION_CHARS // len(endpoints)
    lines = ["", "FOUNDATION (adjudicated groundwork this problem builds on — "
                 "your candidate MUST implement it faithfully):"]
    for eid in endpoints:
        lines += [f"--- foundation artifact {eid} ---",
                  content_text(state.artifacts[eid], blobs)[:per_endpoint]]
    lines.append(
        "REQUIRED: every candidate's \"refs\" MUST include "
        + " or ".join(f'{{"target": "{eid}", "role": "dependence"}}' for eid in endpoints)
        + " for the foundation it builds on — candidates without this ref "
          "are refuted mechanically."
    )
    return lines


def _carries_execution_oracle(artifact, commitments: dict[str, Commitment]) -> bool:
    return any(
        (kappa := commitments.get(cid)) is not None and kappa.eval in _EXECUTION_EVALS
        for cid in artifact.interface.commitments
    )


def _execution_spec_lines(kappa: Commitment) -> list[str]:
    """Render an execution commitment's frozen spec so critics can aim: the
    entry point, one example input, and the counterexample admission gate. A
    critic that cannot see the gate proposes out-of-spec inputs (integer node
    ids, cyclic graphs) that ground nothing — the commitment is the declared
    attack surface, so its spec belongs in the pack. Presentation only."""
    if kappa.eval not in _EXECUTION_EVALS:
        return []
    try:
        spec = json.loads(kappa.budget.extra.get("spec", "{}"))
    except (ValueError, AttributeError):
        return []
    if not spec:
        return []
    example = None
    if spec.get("inputs"):
        example = spec["inputs"][0]
    elif spec.get("tests"):
        example = spec["tests"][0].get("in")
    lines = [f"    entry point: {spec.get('entry')}"]
    if example is not None:
        lines.append(f"    example input (positional args): {json.dumps(example)}")
    contract = spec.get("input_contract")
    if contract:
        lines.append(f"    INPUT CONTRACT (binding): {contract}")
    gate = spec.get("input_check")
    if gate:
        lines.append("    counterexample admission gate — def valid(inp) must return True:")
        lines += [f"      {line}" for line in gate.splitlines()]
    return lines


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
    neighbourhood_n: int = NEIGHBOURHOOD_N,
) -> str:
    """school = {"id", "stance_text", "weight"} — lineage inheritance (§11.1):
    the neighbourhood prefers the school's own accepted descendants; the
    stance directive fades as lineage grows. complement is the §11.4
    stagnation directive. specs are Level-2 diversity specifications:
    candidate k must realize spec k (llm/specs.py). neighbourhood_n caps
    the exemplar section (0 = blind generation — the basin study's
    conditioning-vs-repertoire manipulation); presentation only."""
    lines = [
        f"PROBLEM {problem.id}",
        problem.description,
        "",
        "CRITERIA (commitments every candidate will carry and face):",
    ]
    for cid in problem.criteria:
        kappa = commitments.get(cid)
        lines.append(f"- {cid}: {kappa.eval if kappa else '(schema pending)'}")
    # FOUNDATION before the volatile sections: frozen into the lineage
    # commitment's id, hence static per problem (cache-prefix, angle 4).
    lines += _lineage_foundation(problem, state, commitments, blobs)
    claims = _active_property_claims(state, blobs, problem.criteria)
    if claims:
        lines += ["", "ACTIVE PROPERTIES (conjectured standards the run has "
                      "validated — candidates violating them are refuted by "
                      "execution):"]
        lines += [f"- {c[:200]}" for c in claims]
    accepted = [aid for aid, status in state.status.items() if status == Status.ACCEPTED]
    if school is not None:
        lineage = [
            aid for aid in accepted
            if state.artifacts[aid].provenance.school == school["id"]
        ]
        others = [aid for aid in accepted if aid not in set(lineage)]
        accepted = (lineage + others)[:neighbourhood_n]
    else:
        accepted = accepted[-neighbourhood_n:] if neighbourhood_n else []
    # Stance before neighbourhood: the stance text is stable per school while
    # the neighbourhood changes every cycle — cache-prefix ordering (angle 4).
    if school is not None and school.get("weight", 0) > 0:
        lines += ["", f"SCHOOL STANCE (weight {school['weight']:.2f}): {school['stance_text']}"]
    if accepted:
        lines += ["", "NEIGHBOURHOOD (accepted artifacts; carry dependence refs where natural):"]
        for aid in accepted:
            lines.append(f"- {aid}: {_head(state, aid, blobs)}")
    crossover = (school or {}).get("crossover") if school else None
    if crossover:
        lines += [
            "",
            "CROSSOVER (a divergent lineage from the most distant school — "
            "your school just reseeded on convergence; reconcile or bridge "
            "these, do NOT echo your own lineage):",
        ]
        for aid in crossover:
            if aid in state.artifacts:
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
    lines = _problem_context(state, target_ids)
    lines += [
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
            if kappa is not None:
                lines += _execution_spec_lines(kappa)
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
    if any(_carries_execution_oracle(state.artifacts[tid], commitments) for tid in target_ids):
        lines += ["", _COUNTEREXAMPLE_NOTE]
    lines += [
        "",
        "DIRECTIVE: return exactly one entry per target id above — the "
        "strongest NEW specific case (attack=true) or attack=false. Never "
        "attack an id that is not listed.",
    ]
    return _clip("\n".join(lines), token_budget)


def render_experiment_pack(
    base: Commitment,
    existing: list[str],
    token_budget: int,
    n_generators: int = 2,
    targets: list[str] | None = None,
) -> str:
    """Experiment-design pack (rules/experiment.py): the property oracle's
    full frozen spec — entry, example inputs, CHECKER source (what a violation
    means), input contract, and admission gate — plus the heads of already-
    accepted generators so new designs cover DIFFERENT ground, plus the CODE
    of standing execution-backed survivors. The survivors are what the
    experiment is FOR: a blind generator explores coverage; a generator
    designed against real code hunts the specific dimension its shortcuts
    ignore. Showing the code cannot bias adjudication — the frozen gate and
    checker decide every verdict (presentation only, §9)."""
    try:
        spec = json.loads(base.budget.extra.get("spec", "{}"))
    except (ValueError, AttributeError):
        spec = {}
    lines = [
        f"PROPERTY ORACLE {base.id}",
        f"entry point: {spec.get('entry')}",
        f"frozen example inputs (positional-args lists): "
        f"{json.dumps(spec.get('inputs', [])[:4])}",
    ]
    contract = spec.get("input_contract")
    if contract:
        lines.append(f"INPUT CONTRACT (binding): {contract}")
    checker = spec.get("checker")
    if checker:
        lines += ["", "correctness checker — a candidate output violating this "
                      "refutes the candidate:", checker]
    gate = spec.get("input_check")
    if gate:
        lines += ["", "admission gate — def valid(inp) must return True for every "
                      "generated input:", gate]
    if targets:
        lines += [
            "",
            "STANDING SURVIVORS (they pass every existing input; your "
            "experiments exist to probe THEM — read each implementation and "
            "design inputs that reach whatever the frozen examples and "
            "existing generators never vary: sizes, orderings, ties, "
            "degenerate shapes):",
        ]
        lines += targets
    if existing:
        lines += ["", "ALREADY-ACCEPTED GENERATORS (cover DIFFERENT ground — do "
                      "not duplicate these):"]
        for src in existing:
            head = " / ".join(src.splitlines()[:3])
            lines.append(f"- {head[:160]}")
    lines += [
        "",
        f"DIRECTIVE: return exactly {n_generators} substantively different "
        "generators (different structural families of inputs, not parameter "
        "tweaks of one idea).",
    ]
    return _clip("\n".join(lines), token_budget)


def render_property_pack(
    base: Commitment,
    problem_description: str,
    existing_claims: list[str],
    token_budget: int,
    n_properties: int = 2,
) -> str:
    """Property-design pack (rules/experiment.py): the PROBLEM STATEMENT (the
    sole source of legitimacy) plus the oracle's current spec. Deliberately
    shows NO candidate code — a property derived from code enshrines the
    code's bugs; a property derived from the problem statement tests them."""
    try:
        spec = json.loads(base.budget.extra.get("spec", "{}"))
    except (ValueError, AttributeError):
        spec = {}
    lines = [
        "PROBLEM STATEMENT (the sole source of legitimacy for any property):",
        problem_description,
        "",
        f"PROPERTY ORACLE {base.id}",
        f"entry point: {spec.get('entry')}",
        f"frozen example inputs (positional-args lists): "
        f"{json.dumps(spec.get('inputs', [])[:4])}",
    ]
    contract = spec.get("input_contract")
    if contract:
        lines.append(f"INPUT CONTRACT: {contract}")
    checker = spec.get("checker")
    if checker:
        lines += ["", "CURRENT checker — find requirements the problem states "
                      "that this does NOT enforce:", checker]
    if existing_claims:
        lines += ["", "ALREADY-ACTIVE PROPERTY CLAIMS (do not duplicate):"]
        lines += [f"- {c[:160]}" for c in existing_claims]
    lines += [
        "",
        f"DIRECTIVE: return at most {n_properties} properties, each targeting "
        "a DIFFERENT unenforced requirement. If the current checker already "
        "enforces everything the problem states, return one property that "
        "restates the weakest-enforced requirement more strictly ONLY if the "
        "problem statement actually demands it.",
    ]
    return _clip("\n".join(lines), token_budget)


def render_cx_retry_pack(
    rejected: list[dict],
    state: EpistemicState,
    commitments: dict[str, Commitment],
    blobs,
    token_budget: int,
) -> str:
    """Counterexample-retry pack (§3): each entry is {target, counterexample,
    reason} for an attack on an execution-backed target whose counterexample
    failed to ground. The rejection reason is the gate/oracle's own
    deterministic verdict — echoing it back is what turns a one-shot guesser
    into an experimenter. Renders the target's code and its frozen spec
    (entry, example input, gate) so the critic can aim."""
    lines = [
        f"COUNTEREXAMPLE RETRY ({len(rejected)} target(s)) — your previous "
        "attack(s) on execution-backed targets did not ground. For each "
        "target below: the harness's verdict on your proposed input, the "
        "target's code, and its oracle spec. Return one entry per target id "
        "with a NEW \"counterexample\" (a JSON list of positional args) that "
        "satisfies the admission gate AND makes the target's output violate "
        "the checker; attack=false if you cannot construct one.",
    ]
    for item in rejected:
        tid = item["target"]
        target = state.artifacts[tid]
        lines += [
            "",
            f"TARGET {tid}",
            content_text(target, blobs)[: max(320, token_budget // max(1, len(rejected)))],
            f"your previous counterexample: {json.dumps(item.get('counterexample'))}",
            f"harness verdict: {item.get('reason') or 'did not ground'}",
        ]
        for cid in target.interface.commitments:
            kappa = commitments.get(cid)
            if kappa is not None and kappa.eval in _EXECUTION_EVALS:
                lines.append(f"- {cid}: {kappa.eval}")
                lines += _execution_spec_lines(kappa)
    return _clip("\n".join(lines), token_budget)


def _problem_context(state: EpistemicState, target_ids: list[str]) -> list[str]:
    """The problem statements the targets address — the STANDARD criticism is
    measured against. A critic shown a plan but not its problem reliably
    manufactures out-of-scope faults (observed live: 'lacks accessibility
    provisions' and 'raises privacy concerns' against a problem that scoped a
    small local timer page — unbounded scope-expansion always wins against a
    finite document). Problem descriptions are the run's most stable text, so
    the section leads the pack (cache-prefix, angle 4)."""
    targets = set(target_ids)
    pids: list[str] = []
    for aid, pid in state.addr:
        if aid in targets and pid in state.problems and pid not in pids:
            pids.append(pid)
    lines: list[str] = []
    for pid in pids[:3]:
        lines += [
            f"PROBLEM CONTEXT ({pid}) — the standard the target answers to. "
            "A FAULT must show the target fails THIS problem as stated; "
            "omitting scope the problem never asked for is not a fault:",
            state.problems[pid].description[:1500],
            "",
        ]
    return lines


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
    lines = _problem_context(state, [target_id])
    lines += ["TARGET COMMITMENTS (the target's declared attack surface):"]
    for cid in target.interface.commitments:
        kappa = commitments.get(cid)
        lines.append(f"- {cid}: {kappa.eval if kappa else '(unregistered)'}")
        if kappa is not None:
            lines += _execution_spec_lines(kappa)
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
    if _carries_execution_oracle(target, commitments):
        lines += ["", _COUNTEREXAMPLE_NOTE]
    lines += [
        "",
        "DIRECTIVE: mount the strongest NEW specific case against the target, "
        "or attack=false if you find no genuine fault.",
    ]
    return _clip("\n".join(lines), token_budget)
