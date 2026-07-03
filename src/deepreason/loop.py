"""Single-problem loop (spec §16 P1): Conj -> Crit(program + argumentative)
-> Adj, for N cycles; returns the Pareto frontier of surviving G-members.

Adj runs inside every registration (harness), so criticism lands
immediately. The full scheduler (all Spawn triggers, budgets, schools) is
P2 — this is the minimal usable loop.
"""

from deepreason.capture.pareto import frontier
from deepreason.llm.adapter import SchemaRepairError
from deepreason.ontology.state import Status
from deepreason.rules.conj import conj
from deepreason.rules.crit import crit_argumentative, crit_program


def run_problem(harness, problem_id: str, adapter, config, cycles: int = 1) -> dict:
    if problem_id not in harness.state.problems:
        raise KeyError(f"no such problem: {problem_id} (Conj is gated on the frontier)")
    diagnostics: list[dict] = []
    for cycle in range(cycles):
        try:
            admitted = conj(harness, problem_id, adapter, config, diagnostics)
        except SchemaRepairError as e:
            diagnostics.append({"cycle": cycle, "dropped": str(e)})
            continue  # drop the cycle, logged (spec §9)
        for artifact in admitted:
            crit_program(harness, artifact.id)
            # Budget triage (attention, never status §0): don't spend an
            # argumentative call on a target program criticism already felled.
            if harness.state.status.get(artifact.id) != Status.ACCEPTED:
                continue
            if adapter.has_role("argumentative_critic"):
                try:
                    crit_argumentative(harness, artifact.id, adapter, config)
                except SchemaRepairError as e:
                    diagnostics.append({"cycle": cycle, "dropped": str(e)})
    survivors = [
        aid
        for aid, pid in harness.state.addr
        if pid == problem_id and harness.state.status.get(aid) == Status.ACCEPTED
    ]
    # P1: HV/reach/coverage all land with P2, so the frontier degenerates to
    # the survivor set — attention and reporting only, never a status (§11.7).
    scored = [(aid, {}) for aid in survivors]
    return {
        "survivors": survivors,
        "frontier": frontier(scored, config.PARETO_AXES),
        "diagnostics": diagnostics,
    }
