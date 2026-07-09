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

from deepreason.capture import detection, ladder, schools
from deepreason.capture.pareto import frontier
from deepreason.llm.adapter import SchemaRepairError
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.embedder import HashingEmbedder
from deepreason.measures.hv import hv_spot_check, is_hv_floor, run_hv_floor
from deepreason.measures.reach import reach_sweep
from deepreason.ontology import SpawnTrigger, Status
from deepreason.rules.conj import conj
from deepreason.rules.crit import crit_argumentative_batch, crit_fuzz, crit_program
from deepreason.rules.spawn import scan_spawns
from deepreason.rules.synth import synthesize

_INTEGRATION_TRIGGERS = (SpawnTrigger.CONNECTION, SpawnTrigger.INTEGRATION)


class Scheduler:
    def __init__(self, harness, adapter, config, embedder=None, research_backend=None,
                 controller=None) -> None:
        self.harness = harness
        self.adapter = adapter
        self.config = config
        self.embedder = embedder or HashingEmbedder()
        self.research_backend = research_backend
        # Self-calibration controller (controller.py) — optional; None means
        # fixed knobs (legacy). It reads process signals and tunes generator
        # caps; it cannot touch a status (§0 preserved structurally).
        self.controller = controller
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
        self._flag_streak: dict[str, int] = {}
        self._cooldown: dict[str, int] = {}

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
        adapter attaches one to SchemaRepairError/EndpointError), then log
        the drop reason in diagnostics."""
        self.harness.record_llm_calls([getattr(e, "spend", None)], "dropped-call")
        self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})

    def _select_problem(self):
        state = self.harness.state
        if self.config.FOCUS_PROBLEM is not None:
            return state.problems.get(self.config.FOCUS_PROBLEM)
        survivors_by_problem: dict[str, int] = {}
        for aid, pid in state.addr:
            if state.status.get(aid) == Status.ACCEPTED:
                survivors_by_problem[pid] = survivors_by_problem.get(pid, 0) + 1
        integration_allowed = (
            self._cycles == 0
            or self._integration_cycles / self._cycles < self.config.INTEGRATION_BUDGET_SHARE
        )
        candidates = [
            p
            for p in state.problems.values()
            # Research problems are worked by backends, not gamma (§12).
            if p.provenance.trigger != SpawnTrigger.RESEARCH
            and (integration_allowed or p.provenance.trigger not in _INTEGRATION_TRIGGERS)
        ]
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
            if (artifact.provenance.role if artifact.provenance else "") not in (
                "conjecturer", "synthesizer", "seed"
            ):
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
        early — or seeded — was never attacked again (accepted-by-neglect)."""
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
        if self.controller is not None:
            self.controller.step()  # calibrate generator knobs from process signals
        scan_spawns(harness, config)
        problem = self._select_problem()
        if problem is None:
            self._cycles += 1
            return
        if problem.provenance.trigger in _INTEGRATION_TRIGGERS:
            self._integration_cycles += 1

        # Discrimination in informal mode resolves comparatively (§10.2):
        # a pairwise ruling, not more conjectures.
        if (
            problem.provenance.trigger == SpawnTrigger.DISCRIMINATION
            and self.adapter.has_role("judge")
        ):
            from deepreason.informal.trial import pairwise_discriminate

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
            reach_sweep(harness)
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
                    admitted = conj(
                        harness, problem.id, self.adapter, config, self.diagnostics,
                        school=school, tail_weighted=self.tail_weighted,
                        complement=self.complement, specs=specs,
                        embedder=self.embedder,
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

        reach_sweep(harness)  # hits recorded; debt problems spawn on the next scan
        self._lazy_hv()
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

    def _research_step(self) -> None:
        """Standing exogenous schedule (§12): work one uncovered research
        problem every RESEARCH_PERIOD cycles — every cycle under the
        grounding brake (§11.4)."""
        if self.research_backend is None:
            return
        due = self.research_priority or self._cycles % self.config.RESEARCH_PERIOD == 0
        if not due:
            return
        from deepreason.research.backends import pending, run_research

        for problem in self.harness.state.problems.values():
            if problem.provenance.trigger != SpawnTrigger.RESEARCH:
                continue
            if pending(self.harness, problem.id):
                continue
            if run_research(self.harness, problem, self.research_backend) is not None:
                return  # one fetch per due cycle (budgeted)

    def _lazy_hv(self) -> None:
        """One spot-check per cycle on an accepted, unmeasured artifact."""
        if not self.adapter.has_role("variator"):
            return
        addressed = {aid for aid, _ in self.harness.state.addr}
        for aid, status in self.harness.state.status.items():
            if (
                status == Status.ACCEPTED
                and aid in addressed
                and aid not in self.harness.state.hv
            ):
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

    def run(self, cycles: int) -> dict:
        from deepreason.llm.budget import TokenBudgetExceeded

        for _ in range(cycles):
            try:
                self.step()
            except TokenBudgetExceeded as e:
                # Budget exhaustion is a logged stop, never a crash: state is
                # consistent (Adj runs inside every registration). Mid-retry
                # exhaustion carries the spent-but-uncarried attempts.
                self.harness.record_llm_calls([getattr(e, "spend", None)], "dropped-call")
                self.diagnostics.append({"cycle": self._cycles, "stopped": str(e)})
                break
        return self.report()

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
