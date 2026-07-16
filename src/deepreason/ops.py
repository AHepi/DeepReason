"""Shared operations behind the CLI and the MCP server (spec §13).

Both surfaces expose the same verbs; the behavior lives here exactly once
so a fix to seeding or run setup cannot land on one surface and drift on
the other (the two copies had already diverged in error type and wording).
Surface-specific concerns — argv/JSON parsing, exit codes vs isError
payloads — stay in cli/main.py and mcp_server.py.
"""

import importlib.util

from deepreason.ontology import Problem, ProblemProvenance


class EngineProfileError(ValueError):
    """A workload was sent to an engine surface that cannot execute it."""

    def __init__(self, code: str, profile: str, workload: str) -> None:
        self.code = code
        self.profile = profile
        self.workload = workload
        super().__init__(
            f"{code}: engine_profile={profile!r} cannot execute {workload}; "
            "run it through the matching engine surface"
        )


def require_full_engine(subject, *, workload: str) -> None:
    """Fail before model calls when MiniReason is sent to a full-only path.

    ``subject`` may be a Config, RunManifest, or explicit profile string.
    The check lives in shared operations so CLI, MCP, and direct callers use
    the same stable error codes instead of treating ``engine_profile`` as
    reporting-only metadata.
    """
    profile = str(getattr(subject, "engine_profile", subject))
    if profile == "full":
        return
    if workload == "website":
        code = "ENGINE_PROFILE_UNSUPPORTED_FOR_WEBSITE"
    else:
        code = "ENGINE_PROFILE_UNSUPPORTED_FOR_FULL_RUN"
    raise EngineProfileError(code, profile, workload)


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


def review_infrastructure(harness, adapter, config, artifact_id: str):
    """Explicit infrastructure review (RC6): the ONLY route by which
    infrastructure artifacts (standards, stance policies, seeds) can be
    attacked. They are excluded from the scheduler's ordinary standing
    criticism pool, so criticism of them must be a deliberate operation.

    Flow: the argumentative_critic drafts a case against the named artifact.
    The default observe-only policy records that case as scrutiny; an explicit
    status policy sends it through the defended trial. This operation is
    deliberately separate from ordinary scheduler criticism."""
    from deepreason.authority import (
        AuthoritySurface,
        TrialAuthority,
        trial_authority_for,
    )
    from deepreason.informal.trial import run_argument_trial_from_case
    from deepreason.llm.contracts import ArgumentativeCriticOutput
    from deepreason.programs import content_text
    from deepreason.rules.crit import _observe_case

    artifact_id = resolve_prefix(harness, artifact_id)
    target = harness.state.artifacts.get(artifact_id)
    if target is None:
        raise ValueError(f"unknown artifact: {artifact_id}")
    if not adapter.has_role("argumentative_critic"):
        raise ValueError("infrastructure review requires the argumentative_critic role")
    pack = "\n".join([
        "INFRASTRUCTURE UNDER REVIEW (standard / stance / policy artifact):",
        content_text(target, harness.blobs),
        "",
        "Draft the strongest case that this infrastructure is unsound or "
        "unfit for its role, citing specific clauses, or attack=false if "
        "none exists.",
    ])
    case_out, llm_call = adapter.call(
        "argumentative_critic", pack, ArgumentativeCriticOutput
    )
    if not case_out.attack or not case_out.case.strip():
        harness.record_measure(inputs=["infra-review-no-case", artifact_id], llm=llm_call)
        return None
    authority = trial_authority_for(
        config, "text", AuthoritySurface.INFRASTRUCTURE
    )
    if authority == TrialAuthority.OBSERVE_ONLY:
        return _observe_case(harness, artifact_id, case_out.case, llm_call)
    return run_argument_trial_from_case(
        harness, adapter, config, artifact_id, case_out.case, llm_call,
        authority=authority,
    )


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
        if getattr(config, "EMBEDDER_FAILURE_POLICY", "fallback") == "error":
            # Evidence/scientific mode: a missing neural backend must stop
            # the run BEFORE the first model call, never silently swap the
            # geometry instrument (the bronze flat v1 novelty figures were
            # misattributed for exactly this reason).
            raise
        harness.record_measure(
            inputs=["embedder-fallback", config.EMBEDDER_MODEL, str(e)[:160]]
        )
        return None


def make_research_service(harness, config):
    """The research service a run actually gets (§12): built from
    RESEARCH_BACKEND, failing loudly on invalid modes or missing fixture
    files — enabling research must never require a source edit, and a
    misconfiguration must never silently degrade to no research."""
    from deepreason.research.backends import build_service

    return build_service(config)


def _research_events(harness):
    """Per-problem internal attempt state, reconstructed from the LOG (no
    hidden counters — replay reproduces the same eligibility decisions).
    Returns {problem_id: {"attempts": int, "last_cycle": int}} counting
    only INTERNAL strategy attempts (via != 'agent')."""
    from deepreason.ontology import Rule

    out: dict[str, dict] = {}
    for event in harness.log.read():
        if event.rule != Rule.MEASURE or not event.inputs:
            continue
        if event.inputs[0] != "research-fetch-failed" or len(event.inputs) < 4:
            continue
        _, pid, cycle, via = event.inputs[:4]
        if via == "agent":
            continue  # operator-reported failures never burn the internal cap
        entry = out.setdefault(pid, {"attempts": 0, "last_cycle": -1})
        entry["attempts"] += 1
        try:
            entry["last_cycle"] = max(entry["last_cycle"], int(cycle))
        except ValueError:
            pass
    return out


def open_research_problems(harness) -> list:
    """Uncovered research problems in deterministic order (§12): openness
    is DERIVED from the graph — no mutable covered flag."""
    from deepreason.ontology import SpawnTrigger
    from deepreason.research.backends import covered

    return sorted(
        (
            p for p in harness.state.problems.values()
            if p.provenance.trigger == SpawnTrigger.RESEARCH
            and not covered(harness, p.id)
        ),
        key=lambda p: p.id,
    )


def _escalated_research(harness) -> set[str]:
    """Problem ids named by the most recent grounding-decay escalation
    (research-agent-requested) — log-derived, so docket priority is a pure
    function of the record."""
    from deepreason.ontology import Rule

    latest: set[str] = set()
    for event in harness.log.read():
        if (event.rule == Rule.MEASURE and event.inputs
                and event.inputs[0] == "research-agent-requested"):
            latest = set(event.inputs[2:])
    return latest


def research_docket(harness, config, cycle: int | None = None) -> list[dict]:
    """Deterministic, read-only view of open evidence requests — what the
    operating agent reads to know what to retrieve. Escalated entries (the
    grounding-decay brake) order first; ties break on problem id. Never
    mutates state."""
    attempts = _research_events(harness)
    escalated = _escalated_research(harness)
    entries = []
    for problem in open_research_problems(harness):
        state = attempts.get(problem.id, {"attempts": 0, "last_cycle": -1})
        cooldown_left = 0
        if cycle is not None and state["last_cycle"] >= 0:
            cooldown_left = max(
                0, config.RESEARCH_COOLDOWN - (cycle - state["last_cycle"])
            )
        entries.append({
            "problem": problem.id,
            "artifact": problem.provenance.from_[0] if problem.provenance.from_ else None,
            "commitment": problem.provenance.from_[1] if len(problem.provenance.from_) > 1 else None,
            "claim": problem.description,
            "backend_mode": config.RESEARCH_BACKEND or "off",
            "failed_internal_attempts": state["attempts"],
            "last_attempt_cycle": state["last_cycle"] if state["last_cycle"] >= 0 else None,
            "cooldown_remaining": cooldown_left,
            "internal_exhausted": state["attempts"] >= config.RESEARCH_ATTEMPTS_MAX,
            "external_submission_open": config.RESEARCH_BACKEND is not None,
            "priority": "escalated" if problem.id in escalated else "normal",
        })
    entries.sort(key=lambda e: (e["priority"] != "escalated", e["problem"]))
    return entries


def submit_evidence(harness, problem_id: str, source: str, content: str | bytes,
                    *, codec: str = "utf8", role: str = "import",
                    metadata: dict | None = None):
    """Register CANDIDATE evidence retrieved by the operating agent (or a
    human — role='user' only when a human genuinely supplied it; agent
    material is always 'import'). Registration does not itself establish
    coverage: the candidate carries the research problem's relevance/scope
    commitments and a dependence on its source-reliability assertion, and
    coverage is derived only while it passes those commitments and remains
    accepted and supported. The agent-claimed retrieval time (metadata,
    e.g. {'retrieved_at': ...}) is provenance claim data on the record —
    Event.ts stays harness-controlled; ordering never trusts it. The
    retrieved bytes are content-addressed; replay reads them, never the
    live URL."""
    from deepreason.ontology import SpawnTrigger
    from deepreason.research.backends import register_evidence
    from deepreason.rules.crit import crit_program

    problem = harness.state.problems.get(problem_id)
    if problem is None or problem.provenance.trigger != SpawnTrigger.RESEARCH:
        known = [p.id for p in open_research_problems(harness)][:8]
        raise ValueError(
            f"{problem_id!r} is not a research problem; open requests: {known}"
        )
    if role not in ("import", "user"):
        raise ValueError("evidence role must be 'import' (agent) or 'user' (human)")
    evidence = register_evidence(
        harness, problem, content, source, via="agent", role=role,
        codec=codec, metadata=metadata,
    )
    # Relevance/scope commitments are evaluated NOW through the ordinary
    # crit path (a failure is a warranted refutation of the candidate, not
    # a bespoke rejection); coverage is then read off the recomputed graph.
    crit_program(harness, evidence.id)
    harness.record_measure(
        inputs=["research-evidence-registered", problem_id, evidence.id, source[:120]]
    )
    return evidence


def report_research_failure(harness, problem_id: str, source: str, reason: str,
                            *, category: str = "fetch-error",
                            detail: str | None = None) -> None:
    """A failed retrieval is an OPERATIONAL event, not evidence: it lands
    as a Measure with the reason, and touches no artifact, commitment, or
    status — absence of evidence is never a failed verdict (§12)."""
    inputs = ["research-fetch-failed", problem_id, "-", "agent",
              category, f"{source[:120]}: {reason[:200]}"]
    if detail:
        inputs.append(str(detail)[:200])
    harness.record_measure(inputs=inputs)


def run_scheduler(harness, config, cycles: int, token_budget: int | None = None,
                  on_cycle=None, run_manifest=None, *, stop_controller=None,
                  progress_sink=None):
    """Meter + adapter + conjecturer check + Scheduler.run. Returns
    (result, meter, accounting). An explicit token_budget of 0 is a real
    ceiling. Raises ValueError when no conjecturer role is configured.

    ``accounting`` reconciles the meter against the event log for THIS
    invocation (the log may carry prior runs on a resumed root): silent
    spend was the pipeline's most-recurrent bug class, so the check ships
    in-band with every run rather than living in an operator's habits."""
    require_full_engine(run_manifest or config, workload="full scheduler")

    if run_manifest is not None:
        from deepreason.run_manifest import preflight_harness

        preflight_harness(run_manifest, harness, config)

    from deepreason.llm.adapter import build_adapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.scheduler.scheduler import Scheduler

    logged_before = sum(e.llm.tokens for e in harness.log.read() if e.llm)
    meter = TokenMeter(budget=token_budget) if token_budget is not None else None
    adapter = build_adapter(
        config,
        harness.blobs,
        meter=meter,
        run_manifest=run_manifest,
        # Later-call direct -> compact recovery is append-only process state.
        # Rehydrate it on every scheduler resume without reading model raws.
        process_events=harness.log.read(),
    )
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
    if (
        stop_controller is None
        and getattr(run_manifest, "schema_version", 1) in {2, 3, 4, 5}
    ):
        from deepreason.runtime.stop import StopController, StopPolicy

        stop_controller = StopController(
            StopPolicy.model_validate(
                getattr(run_manifest, "stop_policy", None) or {}
            )
        )
    scheduler = Scheduler(
        harness, adapter, config, embedder=make_embedder(harness, config),
        browser_backend=browser_backend, controller=controller,
        research_backend=make_research_service(harness, config),
        workload_profile=getattr(run_manifest, "workload_profile", None),
        run_manifest=run_manifest,
        stop_controller=stop_controller,
        progress_sink=progress_sink,
    )
    result = scheduler.run(int(cycles), on_cycle=on_cycle)
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
