"""Rule-registry scheduler (spec §14).

Control flow is "apply enabled rules under budget" — not a fixed node
graph. Per cycle: scan Spawn triggers; select a focus problem (integration
work capped by INTEGRATION_BUDGET_SHARE); allocate schools (§11.2); run
gamma (conjecturer, or synthesizer for connection/integration problems);
criticize (program + hv-floor + argumentative); sweep reach; lazy HV
spot-checks; capture detection with hysteresis feeding the response ladder
(§11.4). The frontier persists across sessions because the log does.
"""

from deepreason.capture import detection, ladder, schools
from deepreason.capture.pareto import frontier
from deepreason.llm.adapter import SchemaRepairError
from deepreason.llm.embedder import HashingEmbedder
from deepreason.measures.hv import hv_spot_check, is_hv_floor, run_hv_floor
from deepreason.measures.reach import reach_sweep
from deepreason.ontology import SpawnTrigger, Status
from deepreason.rules.conj import conj
from deepreason.rules.crit import crit_argumentative, crit_program
from deepreason.rules.spawn import scan_spawns
from deepreason.rules.synth import synthesize

_INTEGRATION_TRIGGERS = (SpawnTrigger.CONNECTION, SpawnTrigger.INTEGRATION)


class Scheduler:
    def __init__(self, harness, adapter, config, embedder=None, research_backend=None) -> None:
        self.harness = harness
        self.adapter = adapter
        self.config = config
        self.embedder = embedder or HashingEmbedder()
        self.research_backend = research_backend
        self.schools = (
            schools.init_schools(harness, config) if config.N_SCHOOLS > 0 else {}
        )
        self.diagnostics: list[dict] = []
        # Ladder state (§11.4) — attention only.
        self.recruit_all = False
        self.tail_weighted = False
        self.complement = False
        self.research_priority = False
        self._cycles = 0
        self._integration_cycles = 0
        self._flag_streak: dict[str, int] = {}
        self._cooldown: dict[str, int] = {}

    # -------------------------------------------------------------- #

    def _select_problem(self):
        state = self.harness.state
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
        }

    def _criticize(self, artifact) -> None:
        harness = self.harness
        crit_program(harness, artifact.id)
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
                try:
                    run_trial(
                        harness, artifact.id, kappa, self.adapter, self.config,
                        self.diagnostics, embedder=self.embedder,
                    )
                except SchemaRepairError as e:
                    self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})
        if (
            harness.state.status.get(artifact.id) == Status.ACCEPTED
            and self.adapter.has_role("argumentative_critic")
        ):
            try:
                crit_argumentative(harness, artifact.id, self.adapter, self.config)
            except SchemaRepairError as e:
                self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})

    def step(self) -> None:
        harness, config = self.harness, self.config
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
                except SchemaRepairError as e:
                    self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})
            reach_sweep(harness)
            self._capture_step()
            self._cycles += 1
            return

        assigned = schools.allocate(harness, problem, self.schools, config)
        if self.recruit_all and self.schools:
            assigned = sorted(self.schools)
        if not assigned:
            assigned = [None]

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
                        complement=self.complement, embedder=self.embedder,
                    )
            except SchemaRepairError as e:
                self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})
                continue
            for artifact in admitted:
                self._criticize(artifact)

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
        except SchemaRepairError as e:
            self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})

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
                except SchemaRepairError as e:
                    self.diagnostics.append({"cycle": self._cycles, "dropped": str(e)})
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
        for _ in range(cycles):
            self.step()
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
