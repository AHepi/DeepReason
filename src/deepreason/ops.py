"""Shared operations behind the CLI and the MCP server (spec §13).

Both surfaces expose the same verbs; the behavior lives here exactly once
so a fix to seeding or run setup cannot land on one surface and drift on
the other (the two copies had already diverged in error type and wording).
Surface-specific concerns — argv/JSON parsing, exit codes vs isError
payloads — stay in cli/main.py and mcp_server.py.
"""

from deepreason.ontology import Problem, ProblemProvenance


def resolve_prefix(harness, prefix: str) -> str:
    """Resolve an artifact-id prefix; unique match wins, ambiguity raises."""
    matches = [i for i in harness.state.artifacts if i.startswith(prefix)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        return prefix
    raise ValueError(f"ambiguous id prefix {prefix!r}: {[m[:12] for m in matches]}")


def seed_problem_payload(harness, data: dict) -> Problem:
    """Register standard + commitments + problem from one payload dict:
    {"standard"?: {...}, "commitments"?: [...], "problem": {...}}.
    Auto-registers the skeleton-wf commitment when the criteria name it;
    a problem spec without provenance defaults to a seed trigger."""
    from deepreason.ontology import Commitment

    if data.get("standard"):
        from deepreason.informal.standards import register_standard

        std = data["standard"]
        register_standard(harness, std["id"], rubric=std["rubric"], mode=std.get("mode", "absolute"))
    for c in data.get("commitments") or []:
        harness.register_commitment(Commitment.model_validate(c))
    spec = dict(data["problem"])
    criteria = list(spec.get("criteria") or [])
    if "skeleton-wf" in criteria and "skeleton-wf" not in harness.commitments:
        from deepreason.informal.skeleton import skeleton_wf_commitment

        harness.register_commitment(skeleton_wf_commitment())
    spec.setdefault(
        "provenance", ProblemProvenance.model_validate({"trigger": "seed", "from": []})
    )
    return harness.register_problem(Problem.model_validate(spec))


def run_scheduler(harness, config, cycles: int, token_budget: int | None = None):
    """Meter + adapter + conjecturer check + Scheduler.run. Returns
    (result, meter). An explicit token_budget of 0 is a real ceiling.
    Raises ValueError when no conjecturer role is configured."""
    from deepreason.llm.adapter import build_adapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.scheduler.scheduler import Scheduler

    meter = TokenMeter(budget=token_budget) if token_budget is not None else None
    adapter = build_adapter(config, harness.blobs, meter=meter)
    if not adapter.has_role("conjecturer"):
        raise ValueError(
            "no conjecturer endpoint configured — set roles.conjecturer "
            "(endpoint, model, api_key_env) in the config knob file (§15)"
        )
    result = Scheduler(harness, adapter, config).run(int(cycles))
    return result, meter
