"""Shared operations behind the CLI and the MCP server (spec §13).

Both surfaces expose the same verbs; the behavior lives here exactly once
so a fix to seeding or run setup cannot land on one surface and drift on
the other (the two copies had already diverged in error type and wording).
Surface-specific concerns — argv/JSON parsing, exit codes vs isError
payloads — stay in cli/main.py and mcp_server.py.
"""

import importlib.util

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


def make_embedder(harness, config):
    """The embedder a run actually gets. EMBEDDER_MODEL unset => the
    zero-dependency hashing default (None: the Scheduler constructs it).
    Set but unavailable => hashing fallback with `embedder-fallback` on the
    log — degraded geometry must be visible to the post-hoc reader, never
    silent (the browser-oracle precedent records nothing because absence
    disables a feature; here the run still embeds, just worse)."""
    if not config.EMBEDDER_MODEL:
        return None
    from deepreason.llm.embedder import EmbedderUnavailable, build_embedder

    try:
        return build_embedder(config.EMBEDDER_MODEL)
    except EmbedderUnavailable as e:
        harness.record_measure(
            inputs=["embedder-fallback", config.EMBEDDER_MODEL, str(e)[:160]]
        )
        return None


def run_scheduler(harness, config, cycles: int, token_budget: int | None = None,
                  on_cycle=None):
    """Meter + adapter + conjecturer check + Scheduler.run. Returns
    (result, meter, accounting). An explicit token_budget of 0 is a real
    ceiling. Raises ValueError when no conjecturer role is configured.

    ``accounting`` reconciles the meter against the event log for THIS
    invocation (the log may carry prior runs on a resumed root): silent
    spend was the pipeline's most-recurrent bug class, so the check ships
    in-band with every run rather than living in an operator's habits."""
    from deepreason.llm.adapter import build_adapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.scheduler.scheduler import Scheduler

    logged_before = sum(e.llm.tokens for e in harness.log.read() if e.llm)
    meter = TokenMeter(budget=token_budget) if token_budget is not None else None
    adapter = build_adapter(config, harness.blobs, meter=meter)
    if not adapter.has_role("conjecturer"):
        raise ValueError(
            "no conjecturer endpoint configured — set roles.conjecturer "
            "(endpoint, model, api_key_env) in the config knob file (§15)"
        )
    # Browser oracle (rules/act.py): available iff playwright is importable
    # (optional dependency) — otherwise the feature is silently off, exactly
    # like an absent research backend.
    browser_backend = None
    if importlib.util.find_spec("playwright") is not None:
        from deepreason.browser import PlaywrightBrowser

        browser_backend = PlaywrightBrowser()
    # Self-calibration controller (docs/CONTROLLER_SPEC.md): ON by default.
    # It used to be reachable only through a research-script flag, so every
    # CLI/MCP run silently shipped without live tuning — the loop could not
    # heal its own process failures. config.CONTROLLER=False opts out
    # (controlled experiments, replays of pre-controller roots).
    controller = None
    if config.CONTROLLER:
        from deepreason.controller import Controller

        controller = Controller(harness, adapter)
    result = Scheduler(
        harness, adapter, config, embedder=make_embedder(harness, config),
        browser_backend=browser_backend, controller=controller,
    ).run(int(cycles), on_cycle=on_cycle)
    logged_now = sum(e.llm.tokens for e in harness.log.read() if e.llm)
    accounting = {
        "metered_tokens": meter.total if meter is not None else None,
        "logged_tokens_this_run": logged_now - logged_before,
        "delta": (meter.total - (logged_now - logged_before))
                 if meter is not None else None,
        "note": "nonzero delta = spend invisible to the log; investigate "
                "before trusting metrics",
    }
    return result, meter, accounting
