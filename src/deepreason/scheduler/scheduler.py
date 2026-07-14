"""Rule-registry scheduler (spec §14).

Control flow is "apply enabled rules under budget" — not a fixed node
graph. Per cycle: scan Spawn triggers; select a focus problem (integration
work capped by INTEGRATION_BUDGET_SHARE); allocate schools (§11.2); run
gamma (conjecturer, or synthesizer for connection/integration problems);
criticize (program + hv-floor + argumentative); sweep reach; lazy HV
spot-checks; capture detection with hysteresis feeding the response ladder
(§11.4). The frontier persists across sessions because the log does.
"""

from collections.abc import Iterable
import json

from deepreason.capture import detection, ladder, schools
from deepreason.capture.pareto import frontier
from deepreason.llm.adapter import SchemaRepairError
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import RouteFirewallError
from deepreason.llm.embedder import HashingEmbedder
from deepreason.measures.hv import hv_spot_check, is_hv_floor, run_hv_floor
from deepreason.measures.reach import reach_sweep
from deepreason.ontology import SpawnTrigger, Status
from deepreason.rules.conj import conj
from deepreason.rules.crit import crit_argumentative_batch, crit_fuzz, crit_program
from deepreason.rules.spawn import scan_spawns
from deepreason.rules.synth import synthesize
from deepreason.workloads.models import MandatoryInterface, MandatoryRef

_INTEGRATION_TRIGGERS = (SpawnTrigger.CONNECTION, SpawnTrigger.INTEGRATION)
# Reflexive theory-building work: problems ABOUT the run's own artifacts
# (unification layer). All of it draws from ONE shared budget so it can
# steer attention but never consume the inquiry (Bronze Age postmortem: the
# meta-economy ate ~40/48 artifacts because debt problems were budgeted as
# ordinary work and their successors escaped entirely).
_REFLEXIVE_TRIGGERS = (
    SpawnTrigger.CONNECTION, SpawnTrigger.INTEGRATION,
    SpawnTrigger.EXPLANATION_DEBT, SpawnTrigger.REMOVE_ARBITRARINESS,
)


def reflexive_problems(state) -> set[str]:
    """The reflexive set FOLLOWS LINEAGE: a problem is reflexive if its
    trigger is, or if every provenance root it descends from is reflexive —
    so a successor of a debt problem keeps drawing from the reflexive
    budget instead of laundering itself into ordinary work. Lineage returns
    to independence only through an independently originating problem."""
    out = {p.id for p in state.problems.values()
           if p.provenance.trigger in _REFLEXIVE_TRIGGERS}
    addressed: dict[str, set[str]] = {}
    for aid, pid in state.addr:
        addressed.setdefault(aid, set()).add(pid)
    changed = True
    while changed:
        changed = False
        for pid, problem in state.problems.items():
            if pid in out or not problem.provenance.from_:
                continue
            reflexive_parent = False
            independent_parent = False
            for fid in problem.provenance.from_:
                if fid in state.problems:
                    if fid in out:
                        reflexive_parent = True
                    else:
                        independent_parent = True
                elif fid in addressed:
                    if addressed[fid] & out:
                        reflexive_parent = True
                    if addressed[fid] - out:
                        independent_parent = True
            if reflexive_parent and not independent_parent:
                out.add(pid)
                changed = True
    return out


def problem_family(state, root_pid: str) -> set[str]:
    """The problem plus everything spawned (transitively) from it or from
    artifacts addressing a family problem — successors, discriminations,
    lineage/debt problems, research. Deterministic fixpoint over provenance
    (`from_` entries are problem ids OR artifact ids; artifacts join via
    their addr edges). Used by FOCUS_FAMILY (attention only) and by
    easy.py's staged pipeline for tickers and survivor picks."""
    if root_pid not in state.problems:
        return set()
    addressed: dict[str, set[str]] = {}
    for aid, pid in state.addr:
        addressed.setdefault(aid, set()).add(pid)
    family = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, problem in state.problems.items():
            if pid in family:
                continue
            for fid in problem.provenance.from_:
                if fid in family or addressed.get(fid, set()) & family:
                    family.add(pid)
                    changed = True
                    break
    return family


def problem_family_key(state, problem_id: str) -> str:
    """Return the stable provenance-root identity of a problem family.

    Successor problem ids are fresh attention objects.  Using them directly
    as anti-relapse domains lets a refuted approach re-enter unchanged on its
    next successor.  This walk follows problem and addressed-artifact
    provenance back to independently seeded roots without changing ontology.
    """
    addressed: dict[str, set[str]] = {}
    for artifact_id, pid in state.addr:
        addressed.setdefault(artifact_id, set()).add(pid)

    def roots(pid: str, visiting: frozenset[str]) -> set[str]:
        if pid in visiting or pid not in state.problems:
            return {pid}
        problem = state.problems[pid]
        parents: set[str] = set()
        for source in problem.provenance.from_:
            if source in state.problems:
                parents.add(source)
            else:
                parents.update(addressed.get(source, ()))
        if not parents:
            return {pid}
        found: set[str] = set()
        for parent in sorted(parents):
            found.update(roots(parent, visiting | {pid}))
        return found or {pid}

    return "|".join(sorted(roots(problem_id, frozenset())))


def lineage_endpoints(problem, commitments, state) -> tuple[str, ...]:
    """Registered endpoints frozen by structural lineage commitments."""
    endpoints: list[str] = []
    for commitment_id in problem.criteria:
        commitment = commitments.get(commitment_id)
        if commitment is None or commitment.eval != "program:lineage_ref":
            continue
        for endpoint in str(
            commitment.budget.extra.get("endpoints", "")
        ).split(","):
            if endpoint in state.artifacts and endpoint not in endpoints:
                endpoints.append(endpoint)
    return tuple(endpoints)


def stable_component_spec(problem, endpoints: tuple[str, ...]) -> str:
    """Frozen input-side component identity; never candidate output bytes."""
    return json.dumps(
        {
            "problem": problem.id,
            "description": problem.description,
            "criteria": list(problem.criteria),
            "lineage_endpoints": list(endpoints),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


class Scheduler:
    def __init__(self, harness, adapter, config, embedder=None, research_backend=None,
                 controller=None, browser_backend=None,
                 workload_profile: str | None = None, stop_controller=None,
                 progress_sink=None) -> None:
        self.harness = harness
        self.adapter = adapter
        self.config = config
        self.embedder = embedder or HashingEmbedder()
        # Research service (§12; research/backends.py). Accepts a
        # ResearchService, a bare duck-typed backend (legacy tests: wrapped
        # as an internal-fetcher service), or None (mode "off").
        from deepreason.research.backends import ResearchService

        if research_backend is None:
            self.research = ResearchService("off")
        elif isinstance(research_backend, ResearchService):
            self.research = research_backend
        else:
            self.research = ResearchService(
                getattr(research_backend, "name", "custom"), research_backend
            )
        self._research_episode: str | None = None  # awaiting/off dedup state
        # Browser oracle backend (rules/act.py, duck-typed like research
        # backends). None = feature off; set to None on BrowserUnavailable.
        self.browser_backend = browser_backend
        self._vision_done: set[str] = set()  # attention-only: one look per target
        # Self-calibration controller (controller.py) — optional; None means
        # fixed knobs (legacy). It reads process signals and tunes generator
        # caps; it cannot touch a status (§0 preserved structurally).
        self.controller = controller
        # None preserves the pre-workload behavior for direct legacy callers.
        # Shared production operations always set an explicit profile before
        # run(), while reasoning-envelope problems self-identify inside Conj.
        self.workload_profile = workload_profile
        # Operational completion is optional and evaluated only after a full
        # cycle.  Neither collaborator participates in adjudication.
        self.stop_controller = stop_controller
        self.progress_sink = progress_sink
        self.last_stop_decision = None
        self._problem_worked: dict[str, int] = {}  # pid -> last cycle selected (liveness)
        self.schools = (
            schools.init_schools(harness, config) if config.N_SCHOOLS > 0 else {}
        )
        self.diagnostics: list[dict] = []
        # Ladder state (§11.4) — attention only. An intervention is active for a
        # bounded window (CAPTURE_W cycles) after the ladder fires, then clears;
        # it must NOT latch on for the rest of the run. Held as name -> expiry
        # cycle so the flags are derived, never stuck (spec §11.4 hysteresis).
        self._intervention_until: dict[str, int] = {}
        self._cycles = 0
        self._integration_cycles = 0
        self._arg_crit_this_cycle = 0
        self._recrit_cursor = 0  # round-robin over standing survivors (§14)
        self._fuzz_clean: set[str] = set()  # fuzz-passed ids (deterministic => cacheable)
        self._hv_skipped: set[str] = set()  # oversize hv skips, logged once each
        # Discrimination futility tracking (§14 attention only): pid -> attempt
        # count / last-attempt cycle. A pairwise trial that blocks (order-swap
        # deadlock) or rules 'neither' leaves the problem unsolved, and
        # unsolved-first selection would re-feed it judge calls forever — the
        # run-3 starvation (18 blocked trials, one conjecturer call).
        self._disc_attempts: dict[str, int] = {}
        self._disc_last: dict[str, int] = {}
        self._flag_streak: dict[str, int] = {}
        self._cooldown: dict[str, int] = {}
        self._embedder_stamped = False  # geometry identity, logged once per run

    def _embedder_fingerprint(self) -> dict:
        """fingerprint() when the embedder provides it; a minimal identity
        otherwise (duck-typed test embedders keep working)."""
        fp = getattr(self.embedder, "fingerprint", None)
        if callable(fp):
            return fp()
        return {"model": getattr(self.embedder, "model", type(self.embedder).__name__),
                "version": getattr(self.embedder, "version", "?"), "sentinel": "-"}

    # -------------------------------------------------------------- #
    # Response-ladder interventions (§11.4): derived, time-bounded flags.     #

    def activate_interventions(self, names: Iterable[str]) -> None:
        """Turn on the named interventions for the next CAPTURE_W cycles."""
        until = self._cycles + self.config.CAPTURE_W
        for name in names:
            self._intervention_until[name] = until

    def _intervention_active(self, name: str) -> bool:
        return self._cycles < self._intervention_until.get(name, 0)

    @property
    def recruit_all(self) -> bool:
        return self._intervention_active("recruit_all")

    @property
    def tail_weighted(self) -> bool:
        return self._intervention_active("tail_weighted")

    @property
    def complement(self) -> bool:
        return self._intervention_active("complement")

    @property
    def research_priority(self) -> bool:
        return self._intervention_active("research_priority")

    @property
    def spec_injection(self) -> bool:
        # Config default is always on; the ladder can also inject transiently.
        return self.config.SPEC_INJECTION or self._intervention_active("spec_injection")

    # -------------------------------------------------------------- #

    def _drop(self, e: Exception) -> None:
        """A dropped call still spent tokens: persist its spend record (the
        adapter attaches one to SchemaRepairError/EndpointError) WITH the
        drop reason — the log must answer 'why was this dropped' without the
        in-memory diagnostics (which die with the process)."""
        spend = getattr(e, "spend", None)
        if spend is not None:
            self.harness.record_llm_calls([spend], "dropped-call", str(e)[:120])
        else:
            # No tokens were spent, but the drop itself must still be on the
            # record for a log-follower.
            self.harness.record_measure(inputs=["dropped-call", str(e)[:120]])
        self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})

    def _disc_paused(self, problem) -> bool:
        """Futility backoff for discrimination problems (§14 attention only):
        each attempt — resolved, 'neither', or blocked — starts a cooldown of
        DISC_COOLDOWN cycles, and after DISC_ATTEMPTS_MAX attempts the problem
        is paused permanently (a rivalry the judges cannot presently resolve
        is recorded as unresolved, not retried into starvation; new evidence
        arrives through new artifacts, not identical re-rulings). Pausing
        never touches a status — selection only."""
        if problem.provenance.trigger != SpawnTrigger.DISCRIMINATION:
            return False
        attempts = self._disc_attempts.get(problem.id, 0)
        if (
            self.config.DISC_ATTEMPTS_MAX is not None
            and attempts >= self.config.DISC_ATTEMPTS_MAX
        ):
            return True
        last = self._disc_last.get(problem.id)
        return last is not None and self._cycles - last < self.config.DISC_COOLDOWN

    def _select_problem(self):
        state = self.harness.state
        if self.config.FOCUS_PROBLEM is not None:
            return state.problems.get(self.config.FOCUS_PROBLEM)
        survivors_by_problem: dict[str, int] = {}
        for aid, pid in state.addr:
            if state.status.get(aid) == Status.ACCEPTED:
                survivors_by_problem[pid] = survivors_by_problem.get(pid, 0) + 1
        integration_allowed = self.config.INTEGRATION_BUDGET_SHARE > 0 and (
            self._cycles == 0
            or self._integration_cycles / self._cycles < self.config.INTEGRATION_BUDGET_SHARE
        )
        reflexive = reflexive_problems(state)
        candidates = [
            p
            for p in state.problems.values()
            # Research problems are worked by backends, not gamma (§12).
            if p.provenance.trigger != SpawnTrigger.RESEARCH
            and (integration_allowed or p.id not in reflexive)
            and not self._disc_paused(p)
        ]
        if self.config.FOCUS_FAMILY is not None:
            # Stage isolation (attention only): without it, an earlier
            # stage's unsolved successor leftovers out-age this stage's
            # seed under the liveness queue and the stage bleeds backward.
            family = problem_family(state, self.config.FOCUS_FAMILY)
            candidates = [p for p in candidates if p.id in family]
        if not candidates:
            return None
        if self.config.LIVENESS_QUEUE:
            # Aging priority (docs/CONTROLLER_SPEC.md liveness): age = cycles
            # since a problem was last WORKED (never-worked => -1, so it has
            # waited longest). age grows without bound until the problem wins,
            # so nothing starves; unsolved outweighs solved; lower id breaks
            # ties. Selecting a problem resets its age — that is what makes
            # this a fair rotation rather than a fixed winner.
            def rank(p):
                age = self._cycles - self._problem_worked.get(p.id, -1)
                weight = 1.0 if not survivors_by_problem.get(p.id) else 0.3
                return (-(age * weight), p.id)

            best = min(candidates, key=rank)
            self._problem_worked[best.id] = self._cycles
            return best
        # Unsolved problems first, then round-robin rotation by cycle count.
        unsolved = [p for p in candidates if not survivors_by_problem.get(p.id)]
        pool = unsolved or candidates
        return pool[self._cycles % len(pool)]

    def _school_dict(self, school_id: str) -> dict:
        policy = self.schools[school_id]
        return {
            "id": school_id,
            "stance_text": schools.STANCE_LIBRARY.get(policy["stance"], policy["stance"]),
            "weight": schools.stance_weight(self.harness, school_id, self.config),
            # Forced cross-school crossover after a convergence reseed (§11.4);
            # empty unless the school's policy names a crossover_from.
            "crossover": schools.crossover_exemplars(self.harness, school_id),
        }

    def _criticize(self, artifact) -> None:
        harness, config = self.harness, self.config
        crit_program(harness, artifact.id)
        if harness.state.status.get(artifact.id) == Status.ACCEPTED:
            # Passed its declared oracles on the frozen inputs: the fuzz pass
            # (deterministic enumeration, no LLM) probes BEYOND them before
            # anything more expensive runs.
            crit_fuzz(harness, artifact.id, config)
        trials = 0
        for cid in artifact.interface.commitments:
            kappa = harness.commitments.get(cid)
            if kappa is None:
                continue
            if is_hv_floor(kappa):
                run_hv_floor(harness, self.adapter, artifact.id, kappa, self.embedder)
            elif kappa.eval.startswith("rubric:") and self.adapter.has_role("judge"):
                from deepreason.informal.trial import run_trial

                if harness.state.status.get(artifact.id) != Status.ACCEPTED:
                    continue  # budget triage: already felled
                if (
                    config.RUBRIC_TRIALS_PER_ARTIFACT is not None
                    and trials >= config.RUBRIC_TRIALS_PER_ARTIFACT
                ):
                    continue  # budget triage (§14): remaining trials next cycle
                trials += 1
                try:
                    run_trial(
                        harness, artifact.id, kappa, self.adapter, self.config,
                        self.diagnostics, embedder=self.embedder,
                    )
                except (SchemaRepairError, EndpointError) as e:
                    self._drop(e)
    def _standing_recrit_pool(self) -> list[str]:
        """Standing survivors eligible for re-criticism (§14 attention only):
        ACCEPTED candidate-role artifacts with NO warrant on record against
        them — accepted-by-neglect is untested acceptance, not corroboration.
        Seed infrastructure (standards, stance policies) is excluded (RC6):
        infrastructure is attackable only through the explicit
        ops.review_infrastructure trial path, never the ordinary sweep.
        Execution-oracle carriers order first: a passing oracle is the
        strongest standing claim on the graph, and a Goodhart survivor (right
        on the frozen inputs, wrong in general) can hide nowhere else.
        Deterministic: state insertion order within each group."""
        from deepreason.oracle import EXEC_PROGRAMS

        harness = self.harness
        execution_evals = {f"program:{p}" for p in EXEC_PROGRAMS}
        attacked = {w.target for w in harness.warrants.values()}
        backed: list[str] = []
        rest: list[str] = []
        for aid, artifact in harness.state.artifacts.items():
            if harness.state.status.get(aid) != Status.ACCEPTED or aid in attacked:
                continue
            # ACTIVE conjectured properties are CRITERIA with kill authority
            # and must face the same rotation (intervals/boot postmortem: a
            # buggy checker "survived criticism" for 80+ events because no
            # criticism ever visited it — accepted-by-neglect on the criteria
            # side). Candidates by role; properties by codec.
            role = artifact.provenance.role if artifact.provenance else ""
            if role not in ("conjecturer", "synthesizer") \
                    and artifact.codec != "code:python-prop":
                continue
            carries = any(
                (kappa := harness.commitments.get(cid)) is not None
                and kappa.eval in execution_evals
                for cid in artifact.interface.commitments
            )
            (backed if carries else rest).append(aid)
        return backed + rest

    def _arg_crit(self, admitted_ids: list[str]) -> None:
        """Argumentative pass over the admitted-and-still-accepted targets.
        With CRIT_BATCH_K set, up to K targets share one call (angle 3 of
        docs/TOKEN_ECONOMY.md); warrants stay per-target inside the rule.
        ARG_CRIT_PER_CYCLE caps targets, batched or not. Unused slots go to
        STANDING survivors (round-robin): without this, an artifact was only
        ever criticized in the cycle it was admitted, so anything accepted
        early was never attacked again (accepted-by-neglect). Seed
        infrastructure never enters the pool (RC6: ops.review_infrastructure
        is the only route by which it can be attacked)."""
        harness, config = self.harness, self.config
        if not self.adapter.has_role("argumentative_critic"):
            return
        eligible: list[str] = []
        for aid in admitted_ids:
            if harness.state.status.get(aid) != Status.ACCEPTED:
                continue  # budget triage: already felled by cheaper criticism
            if (
                config.ARG_CRIT_PER_CYCLE is not None
                and self._arg_crit_this_cycle >= config.ARG_CRIT_PER_CYCLE
            ):
                break
            self._arg_crit_this_cycle += 1
            eligible.append(aid)
        if config.RECRIT_STANDING:
            # Leftover capacity sweeps the standing pool; a bounded default
            # (2) when ARG_CRIT_PER_CYCLE is None keeps the sweep from
            # scaling with population size.
            remaining = (
                config.ARG_CRIT_PER_CYCLE - self._arg_crit_this_cycle
                if config.ARG_CRIT_PER_CYCLE is not None
                else 2
            )
            pool = [x for x in self._standing_recrit_pool() if x not in set(eligible)]
            if pool and remaining > 0:
                start = self._recrit_cursor % len(pool)
                for aid in (pool[start:] + pool[:start])[:remaining]:
                    self._recrit_cursor += 1
                    # Machine experimentation first: if the deterministic fuzz
                    # pass fells the standing survivor, the LLM call is saved.
                    if aid not in self._fuzz_clean:
                        crit_fuzz(harness, aid, config)
                        if harness.state.status.get(aid) != Status.ACCEPTED:
                            continue
                        self._fuzz_clean.add(aid)  # cache: fuzz is deterministic
                    eligible.append(aid)
                    self._arg_crit_this_cycle += 1
        size = config.CRIT_BATCH_K or 1
        for i in range(0, len(eligible), size):
            try:
                crit_argumentative_batch(
                    harness, eligible[i : i + size], self.adapter, config
                )
            except (SchemaRepairError, EndpointError) as e:
                self._drop(e)

    def step(self) -> None:
        harness, config = self.harness, self.config
        self._arg_crit_this_cycle = 0
        if not self._embedder_stamped:
            # Geometry identity on the record (§11.5/§17, adjudicated in
            # runs/embedder_design): model + library versions + sentinel-
            # embedding hash. Two runs' school geometry / atlas distances are
            # comparable iff their stamps match — cross-environment drift is
            # DETECTED here, never assumed away. Once per scheduler, before
            # the first heartbeat: a pre-run provenance record, like Register.
            self._embedder_stamped = True
            fp = self._embedder_fingerprint()
            harness.record_measure(
                inputs=["embedder", fp["model"], fp["version"], fp["sentinel"]]
            )
        if self.controller is not None:
            self.controller.step()  # calibrate generator knobs from process signals
        scan_spawns(harness, config)
        problem = self._select_problem()
        # Heartbeat: every event that follows (by seq) until the next
        # heartbeat belongs to this cycle — the log segments itself, live
        # progress is tail-able, and stalls become diagnosable post hoc.
        harness.record_measure(
            inputs=["cycle", str(self._cycles), problem.id if problem else "-"]
        )
        if problem is None:
            self._cycles += 1
            return
        if problem.id in reflexive_problems(harness.state):
            self._integration_cycles += 1

        # Discrimination in informal mode resolves comparatively (§10.2):
        # a pairwise ruling, not more conjectures.
        if (
            problem.provenance.trigger == SpawnTrigger.DISCRIMINATION
            and self.adapter.has_role("judge")
        ):
            from deepreason.informal.trial import pairwise_discriminate

            # Futility tracking: every selection is an attempt — resolved,
            # 'neither', blocked, or rivals-missing alike (each burned the
            # cycle). Cooldown + attempt cap keep an unresolvable rivalry
            # from starving the rest of the run (_disc_paused). EXCEPTION:
            # a transport-dropped ruling is no verdict at all — it must not
            # count toward the PERMANENT cap (the cooldown still applies via
            # _disc_last; only the epistemic attempt is preserved).
            self._disc_last[problem.id] = self._cycles
            transport_deferred = False
            rivals = [
                i for i in problem.provenance.from_
                if harness.state.status.get(i) == Status.ACCEPTED
            ][:2]
            if len(rivals) == 2:
                try:
                    pairwise_discriminate(
                        harness, problem, rivals[0], rivals[1],
                        self.adapter, config, self.diagnostics,
                    )
                except (SchemaRepairError, EndpointError) as e:
                    self._drop(e)
                    if isinstance(e, EndpointError):
                        transport_deferred = True
                        harness.record_measure(
                            inputs=["disc-transport-deferred", problem.id]
                        )
            if not transport_deferred:
                self._disc_attempts[problem.id] = (
                    self._disc_attempts.get(problem.id, 0) + 1
                )
                if self._disc_attempts[problem.id] == self.config.DISC_ATTEMPTS_MAX:
                    # Observability: from here on, selection skips this problem.
                    harness.record_measure(
                        inputs=["disc-attempts-exhausted", problem.id]
                    )
            reach_sweep(harness, coverage_min=config.REACH_COVERAGE_MIN)
            self._capture_step()
            self._cycles += 1
            return

        assigned = schools.allocate(harness, problem, self.schools, config)
        if self.recruit_all and self.schools:
            assigned = sorted(self.schools)
        if not assigned:
            assigned = [None]

        # Level-2 diversity injection: one spec call per step, shared across
        # schools (inter-school diversity comes from stances; specs fight
        # intra-call stem collapse). Logged so tokens and replay both see it.
        specs = None
        if self.spec_injection and problem.provenance.trigger not in _INTEGRATION_TRIGGERS:
            from deepreason.llm.specs import generate_specs

            try:
                specs, spec_call = generate_specs(harness, self.adapter, problem, config)
                harness.record_measure(inputs=["spec-generation", problem.id], llm=spec_call)
            except (SchemaRepairError, EndpointError) as e:
                self._drop(e)

        for school_id in assigned:
            school = self._school_dict(school_id) if school_id else None
            try:
                if (
                    problem.provenance.trigger in _INTEGRATION_TRIGGERS
                    and self.adapter.has_role("synthesizer")
                ):
                    relation = synthesize(
                        harness, problem, self.adapter, config,
                        school_id=school_id, embedder=self.embedder,
                    )
                    admitted = [relation] if relation else []
                else:
                    endpoints = lineage_endpoints(
                        problem, harness.commitments, harness.state
                    )
                    mandatory = MandatoryInterface(
                        refs=tuple(
                            MandatoryRef(target=endpoint, role="dependence")
                            for endpoint in endpoints
                        ) if self.workload_profile is not None else ()
                    )
                    component_spec = (
                        stable_component_spec(problem, endpoints)
                        if self.workload_profile in {"code", "website"}
                        else None
                    )
                    theorem_interface = (
                        stable_component_spec(problem, endpoints)
                        if self.workload_profile == "formal"
                        else None
                    )
                    admitted = conj(
                        harness, problem.id, self.adapter, config, self.diagnostics,
                        school=school, tail_weighted=self.tail_weighted,
                        complement=self.complement, specs=specs,
                        embedder=self.embedder,
                        mandatory_interface=mandatory,
                        workload_profile=self.workload_profile,
                        contract_id=(
                            f"scheduler.conjecturer.{self.workload_profile}.v1"
                            if self.workload_profile is not None
                            else "conjecturer.direct.v1"
                        ),
                        component_spec=component_spec,
                        theorem_interface=theorem_interface,
                    )
            except (SchemaRepairError, EndpointError) as e:
                self._drop(e)
                continue
            for artifact in admitted:
                self._criticize(artifact)
            # Argumentative criticism runs after the cheap per-target passes
            # so program-felled targets never spend a call — and survivors
            # can share one (CRIT_BATCH_K).
            self._arg_crit([a.id for a in admitted])

        reach_sweep(harness, coverage_min=config.REACH_COVERAGE_MIN)  # hits recorded; debt spawns next scan
        self._lazy_hv()
        self._experiment_step()
        self._property_step()
        self._fuzz_sweep()  # after design steps: new probes/oracles apply NOW
        self._browser_step()
        self._vision_step()  # after browser: judges freshly recorded renders
        self._research_step()
        self._audit_step()
        self._capture_step()
        self._cycles += 1

    def _audit_step(self) -> None:
        """Judge-audit sweep every AUDIT_PERIOD cycles (§10.4), budgeted."""
        if (
            self._cycles == 0
            or self._cycles % self.config.AUDIT_PERIOD != 0
            or not self.adapter.has_role("judge")
            or not self.adapter.has_role("variator")
        ):
            return
        from deepreason.informal.audits import paraphrase_invariance_audit

        try:
            paraphrase_invariance_audit(self.harness, self.adapter, self.config)
        except (SchemaRepairError, EndpointError) as e:
            self._drop(e)

    def _fuzz_sweep(self) -> None:
        """Deterministic criticism is never rationed (§14): LLM criticism
        queues behind ARG_CRIT_PER_CYCLE because calls cost tokens, but fuzz
        costs sandbox steps only — so every cycle, re-probe EVERY standing
        accepted candidate whose fuzz-clean bit is unset. The bit clears when
        the generator pool grows (surviving yesterday's experiments is not
        surviving today's). Without this, a target was only re-fuzzed when
        the arg-crit sweep had leftover slots — a token-economy constraint
        wrongly imposed on free criticism."""
        config = self.config
        if config.FUZZ_N <= 0:
            return
        from deepreason.oracle import PROPERTY_PROGRAM

        harness = self.harness
        property_eval = f"program:{PROPERTY_PROGRAM}"
        for aid, artifact in list(harness.state.artifacts.items()):
            if aid in self._fuzz_clean:
                continue
            if harness.state.status.get(aid) != Status.ACCEPTED:
                continue
            if (artifact.provenance.role if artifact.provenance else "") not in (
                "conjecturer", "synthesizer", "seed"
            ):
                continue
            if not any(
                (kappa := harness.commitments.get(cid)) is not None
                and kappa.eval == property_eval
                for cid in artifact.interface.commitments
            ):
                continue
            from deepreason.rules.crit import QUARANTINE_TICK

            tick = QUARANTINE_TICK[0]
            crit_fuzz(harness, aid, config)
            if (
                harness.state.status.get(aid) == Status.ACCEPTED
                and QUARANTINE_TICK[0] == tick  # no verdict pending population
            ):
                self._fuzz_clean.add(aid)

    def _experiment_step(self) -> None:
        """Experiment design (rules/experiment.py): every GEN_PROPOSE_PERIOD
        cycles, ONE experimenter call for the first property oracle among the
        registered problems' criteria that still has fewer than GEN_MAX
        accepted generators. New accepted generators invalidate the fuzz-clean
        cache — a target that survived yesterday's experiments has not
        survived today's."""
        config = self.config
        if (
            config.GEN_PROPOSE_PERIOD <= 0
            or config.FUZZ_N <= 0
            or self._cycles % config.GEN_PROPOSE_PERIOD != 0
            or not self.adapter.has_role("conjecturer")
        ):
            return
        from deepreason.oracle import PROPERTY_PROGRAM
        from deepreason.rules.experiment import accepted_generators, propose_generators

        for problem in self.harness.state.problems.values():
            for cid in problem.criteria:
                base = self.harness.commitments.get(cid)
                if base is None or base.eval != f"program:{PROPERTY_PROGRAM}":
                    continue
                if len(accepted_generators(self.harness, cid)) >= config.GEN_MAX:
                    continue
                try:
                    survivors = propose_generators(
                        self.harness, base, self.adapter, config
                    )
                except (SchemaRepairError, EndpointError) as e:
                    self._drop(e)
                    return
                if survivors:
                    self._fuzz_clean.clear()  # new experiments: re-probe everyone
                return  # one design call per due cycle (budgeted)

    def _property_step(self) -> None:
        """Property conjecture (rules/experiment.py): every PROP_PROPOSE_PERIOD
        cycles, ONE property-designer call for the first property oracle whose
        active-property count is below PROP_MAX. Requires the judge ensemble
        (the relevance trial is part of admission — no judges, no proposals:
        fail closed). Activation clears the fuzz-clean cache: a stronger
        oracle re-probes everything."""
        config = self.config
        if (
            config.PROP_PROPOSE_PERIOD <= 0
            or config.FUZZ_N <= 0
            or self._cycles % config.PROP_PROPOSE_PERIOD != 0
            or not self.adapter.has_role("property_designer")
            or not self.adapter.has_role("judge")
        ):
            return
        from deepreason.oracle import PROPERTY_PROGRAM
        from deepreason.rules.experiment import active_properties, propose_properties

        for problem in self.harness.state.problems.values():
            for cid in problem.criteria:
                base = self.harness.commitments.get(cid)
                if base is None or base.eval != f"program:{PROPERTY_PROGRAM}":
                    continue
                if len(active_properties(self.harness, cid)) >= config.PROP_MAX:
                    continue
                try:
                    activated = propose_properties(
                        self.harness, base, problem, self.adapter, config
                    )
                except (SchemaRepairError, EndpointError) as e:
                    self._drop(e)
                    return
                if activated:
                    self._fuzz_clean.clear()  # stronger oracle: re-probe everyone
                return  # one design call per due cycle (budgeted)

    def _browser_step(self) -> None:
        """Browser evidence (rules/act.py): render + drive app candidates
        that carry browser commitments and lack recorded evidence — at most
        BROWSER_PER_CYCLE new runs per cycle. Exogenous like research: each
        run happens once and its outcome is materialized; a missing
        playwright disables the feature for the run (fail closed)."""
        config = self.config
        if self.browser_backend is None or config.BROWSER_PER_CYCLE <= 0:
            return
        from deepreason.browser import BrowserUnavailable
        from deepreason.rules.act import needs_browser_run, run_browser_evidence

        harness = self.harness
        runs = 0
        for aid, artifact in list(harness.state.artifacts.items()):
            if runs >= config.BROWSER_PER_CYCLE:
                break
            if harness.state.status.get(aid) != Status.ACCEPTED:
                continue
            if (artifact.provenance.role if artifact.provenance else "") not in (
                "conjecturer", "synthesizer", "seed"
            ):
                continue
            if not needs_browser_run(harness, aid):
                continue
            try:
                run_browser_evidence(harness, aid, self.browser_backend, config)
            except BrowserUnavailable as e:
                self.browser_backend = None  # optional dep missing: feature off
                self.diagnostics.append({"cycle": self._cycles, "browser": str(e)})
                return
            runs += 1

    def _vision_step(self) -> None:
        """Vision criticism (rules/vision.py): one look per target with
        recorded screenshots, at most VISION_CRIT_PER_CYCLE calls per cycle.
        Attention-only cache — screenshots are recorded once per candidate,
        so one look is complete coverage."""
        config = self.config
        if (
            config.VISION_CRIT_PER_CYCLE <= 0
            or not self.adapter.has_role("vision_critic")
        ):
            return
        from deepreason.rules.act import browser_evidence
        from deepreason.rules.vision import crit_vision

        harness = self.harness
        calls = 0
        for aid in list(harness.state.artifacts):
            if calls >= config.VISION_CRIT_PER_CYCLE:
                break
            if aid in self._vision_done:
                continue
            if harness.state.status.get(aid) != Status.ACCEPTED:
                continue
            if not browser_evidence(harness, aid):
                continue
            try:
                crit_vision(harness, aid, self.adapter, config)
            except (SchemaRepairError, EndpointError) as e:
                self._drop(e)
            self._vision_done.add(aid)
            calls += 1

    def _research_signal(self, signal: str | None, *extra: str) -> None:
        """Episode-deduplicated research state signal: emit only on a state
        TRANSITION (None <-> off/awaiting), never per cycle — the log shows
        each continuous unavailable/waiting episode exactly once. A new
        episode after recovery logs a new event."""
        if signal == self._research_episode:
            return
        self._research_episode = signal
        if signal is not None:
            self.harness.record_measure(inputs=[signal, *extra])

    def _research_step(self) -> None:
        """Standing exogenous schedule (§12): at most ONE eligible internal
        retrieval attempt per due cycle, problems in deterministic order,
        failures logged and bounded (cooldown + per-strategy attempt cap,
        both reconstructed from the log), backend exceptions caught at this
        boundary. In "agent" mode there is no internal fetcher: uncovered
        requests wait in ops.research_docket for the operating agent —
        that is the ordinary waiting state, not research being off."""
        from deepreason.ops import _research_events, open_research_problems
        from deepreason.research.backends import pending, run_research

        open_problems = open_research_problems(self.harness)
        if not open_problems:
            self._research_signal(None)
            return
        if self.research.mode == "off":
            # Research deliberately disabled while requests go unmet: the
            # record must say so honestly (once per episode) — the §11.4
            # exogenous brake has no actuator here and must not spin.
            self._research_signal("research-off")
            return
        if not self.research.internal:
            # "agent" mode (or unattended ask-user): the docket is live and
            # the agent may submit at any time. Silence is NOT evidence of
            # absence — without a heartbeat protocol the harness cannot
            # distinguish absent, delayed, or mid-search. Never research-off.
            self._research_signal(
                "research-awaiting-agent", *[p.id for p in open_problems[:8]]
            )
            return
        self._research_signal(None)

        due = self.research_priority or self._cycles % self.config.RESEARCH_PERIOD == 0
        if not due:
            return
        attempts = _research_events(self.harness)
        for problem in open_problems:  # deterministic order (sorted ids)
            if pending(self.harness, problem.id):
                continue  # sealed holdout: scheduled-pending, not failed
            state = attempts.get(problem.id, {"attempts": 0, "last_cycle": -1})
            if state["attempts"] >= self.config.RESEARCH_ATTEMPTS_MAX:
                continue  # internal strategy exhausted (already logged)
            if (
                state["last_cycle"] >= 0
                and self._cycles - state["last_cycle"] < self.config.RESEARCH_COOLDOWN
            ):
                continue  # cooling down after a failed attempt
            try:
                result = run_research(self.harness, problem, self.research.fetcher)
            except Exception as e:  # noqa: BLE001 - retrieval must never kill the cycle
                result = None
                self._log_research_failure(problem.id, type(e).__name__, str(e))
            else:
                if result is None:
                    self._log_research_failure(problem.id, "no-result", "backend returned nothing")
            return  # exactly one internal attempt per due cycle, hit or miss

    def _log_research_failure(self, pid: str, category: str, reason: str) -> None:
        """research-fetch-failed carries [pid, cycle, strategy, ...] so the
        cooldown/attempt state is a pure function of the log (replay-safe),
        and the exhaustion transition is logged exactly once."""
        from deepreason.ops import _research_events

        self.harness.record_measure(inputs=[
            "research-fetch-failed", pid, str(self._cycles),
            self.research.mode, category, reason[:200],
        ])
        state = _research_events(self.harness).get(pid, {"attempts": 0})
        if state["attempts"] == self.config.RESEARCH_ATTEMPTS_MAX:
            # Attention only: internal fetching pauses; the problem stays
            # open and the agent channel can still cover it at any time.
            self.harness.record_measure(
                inputs=["research-fetch-exhausted", pid, self.research.mode]
            )

    def _lazy_hv(self) -> None:
        """One spot-check per cycle on an accepted, unmeasured artifact.
        Oversized content is skipped (HV_CONTENT_MAX_CHARS): the variator
        cannot emit K whole-document edits of a multi-KB app inside its
        completion window — every attempt was a guaranteed length-limit drop
        (observed live). Attention-only machinery, so skipping is legal."""
        if not self.adapter.has_role("variator"):
            return
        from deepreason.programs import content_text

        addressed = {aid for aid, _ in self.harness.state.addr}
        limit = self.config.HV_CONTENT_MAX_CHARS
        for aid, status in self.harness.state.status.items():
            if (
                status != Status.ACCEPTED
                or aid not in addressed
                or aid in self.harness.state.hv
                or aid in self._hv_skipped
            ):
                continue
            if limit is not None:
                text = content_text(self.harness.state.artifacts[aid], self.harness.blobs)
                if len(text) > limit:
                    self._hv_skipped.add(aid)
                    self.harness.record_measure(
                        inputs=["hv-skip-oversize", aid, str(len(text))]
                    )
                    continue  # keep scanning: the cycle's slot is not spent
            try:
                hv_spot_check(
                    self.harness, self.adapter, aid, self.config.HV_K, self.embedder
                )
            except (SchemaRepairError, EndpointError) as e:
                self._drop(e)
            return

    def _capture_step(self) -> None:
        """Detection + hysteresis (raw flag sustained 2 checks) + ladder,
        with a CAPTURE_W-cycle cooldown per intervention (§11.4)."""
        raw = detection.raw_flags(self.harness, self.embedder, self.config)
        active: dict[str, bool] = {}
        for flag, is_raised in raw.items():
            self._flag_streak[flag] = self._flag_streak.get(flag, 0) + 1 if is_raised else 0
            if (
                self._flag_streak[flag] >= 2
                and self._cycles >= self._cooldown.get(flag, 0)
            ):
                active[flag] = True
        if active:
            applied = ladder.respond(self, active)
            for flag in active:
                self._cooldown[flag] = self._cycles + self.config.CAPTURE_W
                self._flag_streak[flag] = 0
            self.diagnostics.append(
                {"cycle": self._cycles, "flags": sorted(active), "responses": applied}
            )

    # -------------------------------------------------------------- #

    def _stop_snapshot(self) -> dict:
        report = self.report()
        state = self.harness.state
        accepted = {
            artifact_id
            for artifact_id, _ in state.addr
            if state.status.get(artifact_id) == Status.ACCEPTED
        }
        return {
            "frontier": frozenset(report["frontier"]),
            "statuses": dict(state.status),
            "problems": frozenset(state.problems),
            "admissions": frozenset(accepted),
        }

    def _stop_metrics(self, before: dict, diagnostic_start: int):
        """Compile process-only convergence inputs at a safe cycle boundary."""
        from deepreason.ops import open_research_problems
        from deepreason.runtime.stop import StopMetrics

        after = self._stop_snapshot()
        status_ids = set(before["statuses"]) | set(after["statuses"])
        status_churn = sum(
            before["statuses"].get(artifact_id)
            != after["statuses"].get(artifact_id)
            for artifact_id in status_ids
        )
        recent_diagnostics = self.diagnostics[diagnostic_start:]
        stuck_signal = any(
            item.get("search_signal") == "stuck"
            for item in recent_diagnostics
        )
        gate_orbit = any(
            str(item.get("gate", "")).startswith(("battery-equivalent", "hash:"))
            for item in recent_diagnostics
        )
        repair_exhausted = any(
            "schema" in str(item.get("dropped", "")).casefold()
            or "repair" in str(item.get("dropped", "")).casefold()
            for item in recent_diagnostics
        )
        debt = detection.adjudicator_metrics(
            self.harness, self.config.CAPTURE_W
        )["criticism_debt"]
        metrics = StopMetrics(
            cycle=self._cycles,
            frontier_delta=len(before["frontier"] ^ after["frontier"]),
            status_churn=status_churn,
            new_problems=len(after["problems"] - before["problems"]),
            new_admissions=len(after["admissions"] - before["admissions"]),
            # Deterministic checks run synchronously in _criticize before this
            # boundary; no hidden worker queue exists in this scheduler.
            pending_deterministic_checks=0,
            criticism_debt=debt,
            open_research=len(open_research_problems(self.harness)),
            stuck_signal=stuck_signal,
            gate_orbit=gate_orbit,
            repair_exhausted=repair_exhausted,
        )
        return metrics, after

    def _emit_progress(self, metrics, decision) -> None:
        if self.progress_sink is None:
            return
        state = self.harness.state
        counts = {"accepted": 0, "refuted": 0, "suspended": 0}
        for status in state.status.values():
            if status == Status.ACCEPTED:
                counts["accepted"] += 1
            elif status == Status.REFUTED:
                counts["refuted"] += 1
            else:
                counts["suspended"] += 1
        stopped = decision is not None and decision.stop
        self.progress_sink.emit(
            state="completed" if stopped else "running",
            phase="convergence",
            activity=(
                f"stop: {decision.reason}"
                if stopped
                else (
                    f"escape: {decision.escape_action}"
                    if decision is not None and decision.escape_action
                    else "cycle evaluated"
                )
            ),
            cycle=metrics.cycle,
            frontier_size=len(self.report()["frontier"]),
            accepted=counts["accepted"],
            refuted=counts["refuted"],
            suspended=counts["suspended"],
            queued_checks=metrics.pending_deterministic_checks,
            determinate=False,
            stop_reason=decision.reason if stopped else None,
        )

    def _record_stop(self, decision, metrics) -> None:
        from deepreason.runtime.stop import write_stop_record

        self.harness.record_measure(
            inputs=[
                "scheduler-stop",
                str(decision.reason),
                self.stop_controller.policy.digest,
            ]
        )
        write_stop_record(
            self.harness.root,
            reason=decision.reason,
            policy=self.stop_controller.policy,
            metrics=metrics,
            event_seq=max(0, self.harness._next_seq - 1),
        )

    def run(self, cycles: int, on_cycle=None) -> dict:
        """on_cycle(self) fires after every completed cycle — a read-only
        progress hook (easy.make's friendly ticker); it must not register.
        A truthy return stops the run early (staged pipelines stop a stage
        on its first survivor without rebuilding the Scheduler, which would
        wipe the attention caches)."""
        from deepreason.llm.budget import TokenBudgetExceeded

        stop_snapshot = (
            self._stop_snapshot() if self.stop_controller is not None else None
        )
        for _ in range(cycles):
            try:
                diagnostic_start = len(self.diagnostics)
                self.step()
                if on_cycle is not None and on_cycle(self):
                    break
                if self.stop_controller is not None and stop_snapshot is not None:
                    metrics, stop_snapshot = self._stop_metrics(
                        stop_snapshot, diagnostic_start
                    )
                    decision = self.stop_controller.evaluate(metrics)
                    self.last_stop_decision = decision
                    if decision.escape_action:
                        self.harness.record_measure(
                            inputs=[
                                "stop-escape",
                                decision.escape_action,
                                str(metrics.cycle),
                            ]
                        )
                    self._emit_progress(metrics, decision)
                    if decision.stop:
                        self._record_stop(decision, metrics)
                        break
            except RouteFirewallError as e:
                # A leased route changing during a run is a fail-closed
                # security/configuration error, not an ordinary model or
                # transport failure. Preserve any already-spent attempts on
                # the append-only process record, then stop the run loudly so
                # the scheduler cannot continue against the mutated endpoint.
                self._drop(e)
                raise
            except TokenBudgetExceeded as e:
                # Budget exhaustion is a logged stop, never a crash: state is
                # consistent (Adj runs inside every registration). Mid-retry
                # exhaustion carries the spent-but-uncarried attempts — and the
                # stop REASON goes into the log for the post-hoc reader.
                spend = getattr(e, "spend", None)
                if spend is not None:
                    self.harness.record_llm_calls([spend], "dropped-call", str(e)[:120])
                else:
                    self.harness.record_measure(inputs=["dropped-call", str(e)[:120]])
                self.diagnostics.append({"cycle": self._cycles, "stopped": str(e)})
                break
        report = self.report()
        if self.last_stop_decision is not None and self.last_stop_decision.stop:
            report["stop_reason"] = self.last_stop_decision.reason
        return report

    def report(self) -> dict:
        """Pareto retention (§11.7): focus/reporting keeps the frontier over
        (HV, reach, coverage) — attention only, never a status."""
        from deepreason import programs

        state = self.harness.state
        survivors = sorted(
            {aid for aid, _ in state.addr if state.status.get(aid) == Status.ACCEPTED}
        )
        scored = []
        for aid in survivors:
            commitments = [
                c for c in state.artifacts[aid].interface.commitments
                if c in self.harness.commitments
                and programs.evaluable(self.harness.commitments[c])
            ]
            coverage = (
                sum(
                    1
                    for c in commitments
                    if programs.evaluate(
                        self.harness.commitments[c], state.artifacts[aid], self.harness.blobs
                    )[0] == programs.PASS
                )
                / len(commitments)
                if commitments
                else 0.0
            )
            scored.append(
                (
                    aid,
                    {
                        "hv": state.hv.get(aid, 0.0),
                        "reach": state.reach.get(aid, 0.0),
                        "coverage": coverage,
                    },
                )
            )
        return {
            "survivors": survivors,
            "frontier": frontier(scored, self.config.PARETO_AXES),
            "problems": sorted(state.problems),
            "diagnostics": self.diagnostics,
        }
