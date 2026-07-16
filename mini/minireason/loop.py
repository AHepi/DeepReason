"""M2 — the driver: propose -> gate -> check -> log -> rotate (MINI_PLAN §3.7).

Session is a narrow facade over the parent's Harness: every registration,
object, event, fail-warrant package, attack edge, and status is canonical.
The reduced engine retains only the small outer scheduling loop, so graduation
is still just ``Harness(root)`` with no data conversion (G6).

Stop conditions: budget death, queue exhausted, all problems dry. Never
loop a dry problem — that is the measured 4.3x token burn.
"""

import json
from pathlib import Path
from types import MappingProxyType

from deepreason.application.conjecture import ConjectureApplicationBoundary
from deepreason.harness import Harness
from deepreason.log.event_log import (
    ConcurrentWriterError,
    CorruptLogError,
    EventSequenceError,
)
from deepreason.llm.contracts import ConjecturerOutput as ConjOut
from deepreason.ontology import (
    Artifact,
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    SpawnTrigger,
    Warrant,
)
from deepreason.rules.guards import anti_relapse
from deepreason.rules.warrants import register_fail_warrant
from deepreason.run_manifest import (
    MANIFEST_NAME,
    RunManifestError,
    load_run_manifest,
    payload_has_rubric,
    preflight_payload,
)
from minireason import call as llm
from minireason import checks, gate, rotate
from minireason.compat import (
    DEFAULT_MODEL_PROFILE,
    ENGINE_PROFILE,
    MINI_NEAR_DUP_EPS,
    initialize,
)
from minireason.log import Call, Event, SeqError, State, canonical_json


RUBRIC_POLICY_ERROR = "RUBRIC_INPUT_FORBIDDEN"


class _CommitmentOverlayHarness:
    """Read-only candidate commitment view for pre-registration guards.

    The normative guard expects the Harness facade, including its commitment
    mapping. Candidate-derived commitments must be visible while computing
    the active battery, but must not enter canonical state unless that exact
    candidate is admitted.
    """

    def __init__(self, harness: Harness, additions: list[Commitment]) -> None:
        commitments = dict(harness.commitments)
        commitments.update((commitment.id, commitment) for commitment in additions)
        self._harness = harness
        self.commitments = MappingProxyType(commitments)

    def __getattr__(self, name: str):
        return getattr(self._harness, name)


class Session:
    """Small-engine facade over DeepReason's canonical Harness.

    Mini owns the outer loop only. Registration, replay, object identity,
    attack construction, and status are all parent operations.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.harness = Harness(self.root)
        self.blobs = self.harness.blobs
        self.objects = self.harness.objects
        self.log = self.harness.log
        self.state = State(self.harness)
        manifest_path = self.root / MANIFEST_NAME
        self.manifest = load_run_manifest(manifest_path) if manifest_path.exists() else None
        # The repaired guard runs its battery and semantic stages only with a
        # full scope stack (domain, embedder, eps); mini supplies the parent
        # HashingEmbedder so kernel admission keeps the parent semantics.
        from deepreason.llm.embedder import HashingEmbedder

        self._gate_embedder = HashingEmbedder()

    def _rubric_commitments(self, commitments: list[dict]) -> list[str]:
        resolved: list[dict] = []
        for record in commitments:
            item = dict(record)
            cid = str(item.get("id", ""))
            if not item.get("eval") and cid in self.harness.commitments:
                item["eval"] = self.harness.commitments[cid].eval
            resolved.append(item)
        payload = {"commitments": resolved}
        if not payload_has_rubric(payload):
            return []
        if self.manifest is not None:
            try:
                preflight_payload(self.manifest, payload)
            except RunManifestError:
                # Convert the canonical preflight failure into Mini's logged
                # process drop below. No policy error can become an escape.
                pass
        blocked: list[str] = []
        for record in resolved:
            cid = str(record.get("id", ""))
            eval_spec = str(record.get("eval", ""))
            if eval_spec.startswith("rubric:"):
                blocked.append(cid or "<missing-id>")
        return blocked

    def _policy_drop(self, blocked: list[str], candidate_id: str = "") -> Event:
        inputs = ["dropped-candidate", RUBRIC_POLICY_ERROR]
        if candidate_id:
            inputs.append(f"candidate:{candidate_id}")
        inputs.extend(f"commitment:{cid}" for cid in blocked)
        return self.measure(inputs)

    @staticmethod
    def _translate_log_error(error: Exception) -> SeqError:
        return SeqError(str(error))

    def commit(self, rule: str, inputs: list[str], outputs: list[str],
               spend: Call | None = None) -> Event:
        try:
            return self.harness._commit(
                Rule(rule), inputs=list(inputs), outputs=list(outputs), llm=spend
            )
        except (ConcurrentWriterError, CorruptLogError, EventSequenceError) as error:
            raise self._translate_log_error(error) from error

    def measure(self, inputs: list[str], spend: Call | None = None) -> Event:
        try:
            return self.harness.record_measure(inputs=inputs, llm=spend)
        except (ConcurrentWriterError, CorruptLogError, EventSequenceError) as error:
            raise self._translate_log_error(error) from error

    def spawn_problem(self, pid: str, description: str) -> None:
        self.harness.register_problem(
            Problem(
                id=pid,
                description=description,
                provenance=ProblemProvenance(trigger=SpawnTrigger.SEED),
            )
        )

    def register_commitments(self, commitments: list[dict]) -> list[str]:
        """Register through Harness, atomically rejecting rubric input.

        Mini's immutable run policy is ``forbid``. A rubric-bearing batch is
        process-logged and none of its commitments enter canonical state.
        """
        blocked = self._rubric_commitments(commitments)
        if blocked:
            self._policy_drop(blocked)
            return []
        registered: list[str] = []
        for record in commitments:
            commitment = Commitment.model_validate(record)
            self.harness.register_commitment(commitment)
            registered.append(commitment.id)
        return registered

    def build_candidate(
        self,
        content: str,
        commitment_ids: list[str],
        stance: str,
        warrants: list[Warrant] | None = None,
    ) -> Artifact:
        """Construct the one canonical value used for admission and commit."""
        carried = list(warrants or [])
        interface = Interface(commitments=commitment_ids, refs=[])
        content_ref = f"inline:{content}"
        return Artifact(
            id=Artifact.compute_id(content_ref, "utf8", interface),
            content_ref=content_ref,
            codec="utf8",
            interface=interface,
            warrants=[warrant.id for warrant in carried],
            provenance=Provenance(
                role="conjecturer",
                school=stance,
                event_seq=self.harness._next_seq,
            ),
        )

    def guard_scope(
        self,
        artifact: Artifact,
        candidate_commitments: list[Commitment] | None = None,
        near_dup_eps: float | None = MINI_NEAR_DUP_EPS,
    ) -> dict:
        """The full scope stack the repaired guard requires for its battery
        and semantic stages: session embedder, calibrated eps, and a domain
        compiled from the candidate (overlay commitments included). Exposed
        so parity tests can call the full guard with identical inputs."""
        overlay = None
        if candidate_commitments:
            overlay = dict(self.harness.commitments)
            overlay.update({c.id: c for c in candidate_commitments})
        domain = anti_relapse.relapse_domain(
            artifact,
            self.harness,
            workload_profile="text",
            problem_family="mini",
            contract_id="mini.conjecturer.v1",
            commitments=overlay,
        )
        return {
            "embedder": self._gate_embedder,
            "near_dup_eps": near_dup_eps,
            "domain": domain,
            "commitments": overlay,
        }

    def admit_candidate(
        self,
        artifact: Artifact,
        warrants: list[Warrant] | None = None,
        *,
        candidate_commitments: list[Commitment] | None = None,
        embedder=None,
        near_dup_eps: float | None = MINI_NEAR_DUP_EPS,
    ) -> tuple[bool, str]:
        """Delegate admission with a non-persistent commitment overlay."""
        scope = self.guard_scope(
            artifact, candidate_commitments, near_dup_eps=near_dup_eps
        )
        if embedder is not None:
            scope["embedder"] = embedder
        return anti_relapse.check(
            artifact,
            list(warrants or []),
            self.harness,
            **scope,
        )

    def register_candidates(
        self,
        entries: list[tuple[Artifact, list[Warrant]]],
        problem_id: str,
        spend: Call | None,
        *,
        source_call_seq: int | None = None,
    ) -> list[str]:
        """Register the exact canonical Artifacts that passed admission."""
        canonical_entries: list[tuple[Artifact, list[Warrant]]] = []
        ids: list[str] = []
        for artifact, warrants in entries:
            records = [
                self.harness.commitments[cid].model_dump(mode="json", by_alias=True)
                for cid in artifact.interface.commitments
                if cid in self.harness.commitments
            ]
            blocked = self._rubric_commitments(records)
            if blocked:
                self._policy_drop(blocked, artifact.id)
                continue
            canonical_entries.append((artifact, warrants))
            ids.append(artifact.id)
        if not canonical_entries:
            if spend is not None:
                self.measure(["dropped-call", RUBRIC_POLICY_ERROR], spend)
            return []
        self.harness.register_batch(
            canonical_entries,
            problem_id=problem_id,
            rule=Rule.CONJ,
            llm=spend,
            process_inputs=(
                (f"conjecture-call:{source_call_seq}",)
                if source_call_seq is not None
                else ()
            ),
        )
        # Record each artifact's relapse domain so it can serve as a scoped
        # prior in later admission checks (priors without a recorded domain
        # are skipped by the repaired guard, never blocked against).
        for artifact, _warrants in canonical_entries:
            anti_relapse.record_domain(
                self.harness,
                artifact.id,
                self.guard_scope(artifact)["domain"],
            )
        return ids

    def refute(self, target: str, failures: list[dict]) -> None:
        """Delegate the canonical demonstrative fail-warrant package."""
        cid = failures[0]["commitment"]
        nu_content = f"nu: check {cid} is sound and relevant for {target[:12]}"
        register_fail_warrant(
            self.harness,
            commitment_id=cid,
            target_id=target,
            nu_content=nu_content,
            critic_content=f"check-refuter: {cid} fails on {target[:12]}",
            trace_ref=self.blobs.put(canonical_json(failures)),
            skip_if_on_record=True,
        )

    def rotate_stance(self, rotation: rotate.Rotation, reason: str) -> None:
        old = rotation.stance
        stance = rotation.rotate()
        content = json.dumps({"school_policy": {
            "school": stance, "stance": rotate.STANCE_LIBRARY[stance]}}, sort_keys=True)
        interface = Interface()
        pid = Artifact.compute_id(f"inline:{content}", "json", interface)
        if pid not in self.state.artifacts:  # succession, not duplication
            self.harness.create_artifact(
                content,
                codec="json",
                interface=interface,
                provenance=Provenance(
                    role="seed", school=stance, event_seq=self.harness._next_seq
                ),
                rule=Rule.RESEED,
            )
        self.measure(["intervention:reseed", f"school:{old}", reason])

    def survivors(self, problem_id: str) -> list[str]:
        accepted = self.state.accepted
        return [a for a, p in self.state.addr if p == problem_id and a in accepted]


def _neighbourhood(session: Session, problem_id: str, k: int) -> str:
    texts = []
    for aid in session.survivors(problem_id)[-k:]:
        content = session.state.artifacts[aid]["content_ref"][len("inline:"):]
        # Mini's canonical candidate builder does not retain conjecturer refs.
        # Show survivor content for diversity conditioning, but expose neither
        # raw hashes nor alias labels that the output contract cannot preserve.
        texts.append(f"- {content[:300]}")
    return "\n".join(texts)


def _prompt(description: str, stance_directive: str, neighbourhood: str, vs_k: int) -> str:
    return (
        "You are the conjecture operator: propose bold, criticizable explanations "
        "for the PROBLEM below. Verbalized Sampling: return a DISTRIBUTION of "
        f"{vs_k} diverse candidates, each with a typicality estimate in [0,1].\n"
        f"STANCE (condition your generation on it): {stance_directive}.\n"
        "Each candidate's content MUST be a JSON skeleton embedded as a string: "
        '{"claim": ..., "mechanism": ..., "scope": {"covers": [], "excludes": []}, '
        '"forbidden": [{"case": ..., "eval": ...}], "prose_notes": ...}. '
        'Each forbidden case states evidence that would REFUTE the candidate; eval is '
        'a known "program:<name>" for mechanically checkable cases. Inline predicates '
        'from model output are forbidden. Rubric commitments are '
        'outside this reduced engine and are dropped before registration. A candidate '
        'that forbids nothing '
        "is refuted on arrival.\n\n"
        f"PROBLEM: {description}\n"
        + (f"\nRECENT SURVIVORS (do not repeat; differ substantively):\n{neighbourhood}\n"
           if neighbourhood else "")
    )


def _mini_guard_finding(
    candidate_ref: str,
    artifact_ref: str,
    outcome: str,
    reason: str,
):
    """Project Mini's existing code-authored disposition into shared types."""

    from deepreason.workflow.models import (
        GuardFindingCode,
        GuardFindingOutcome,
        GuardFindingV1,
    )

    disposition = GuardFindingOutcome(outcome)
    code = (
        GuardFindingCode.PASSED
        if disposition == GuardFindingOutcome.ADMIT
        else GuardFindingCode.CONTENT_DUPLICATE
        if disposition == GuardFindingOutcome.DEDUPLICATE
        else GuardFindingCode.SCHEMA_INVALID
        if reason == RUBRIC_POLICY_ERROR
        else GuardFindingCode.BATTERY_EQUIVALENT
        if "battery-equivalent" in reason
        else GuardFindingCode.REFUTED_EQUIVALENT
        if reason.startswith("hash:")
        else GuardFindingCode.INTERFACE_INVALID
    )
    return GuardFindingV1(
        candidate_ref=candidate_ref,
        outcome=disposition,
        code=code,
        related_refs=(artifact_ref,),
    )


def _prepare_controlled_candidates(session, output, vs_k: int, stance: str):
    """Compile semantic values without guarding or mutating canonical state."""

    prepared = []
    occurrences: dict[str, int] = {}
    for candidate in output.candidates[:vs_k]:
        content = candidate.content
        commitment_values = checks.compile_checks(content)
        blocked = session._rubric_commitments(commitment_values)
        candidate_commitments = tuple(
            Commitment.model_validate(record) for record in commitment_values
        )
        artifact = session.build_candidate(
            content,
            [commitment.id for commitment in candidate_commitments],
            stance,
        )
        occurrences[artifact.id] = occurrences.get(artifact.id, 0) + 1
        occurrence = occurrences[artifact.id]
        disposition_ref = (
            artifact.id
            if occurrence == 1
            else f"{artifact.id}#occurrence-{occurrence}"
        )
        prepared.append(
            (
                disposition_ref,
                artifact,
                commitment_values,
                candidate_commitments,
                blocked,
            )
        )
    return prepared


def _admit_controlled_candidates(
    session,
    prepared,
    *,
    near_dup_eps: float | None,
):
    """Run Mini's unchanged guards and return their complete shared receipt."""

    admitted = []
    findings = []
    seen: set[str] = set()
    for (
        disposition_ref,
        artifact,
        commitment_values,
        candidate_commitments,
        blocked,
    ) in prepared:
        if blocked:
            session._policy_drop(blocked)
            findings.append(
                _mini_guard_finding(
                    disposition_ref,
                    artifact.id,
                    "reject",
                    RUBRIC_POLICY_ERROR,
                )
            )
            continue
        ok, reason = session.admit_candidate(
            artifact,
            [],
            candidate_commitments=list(candidate_commitments),
            near_dup_eps=near_dup_eps,
        )
        if not ok:
            session.measure([f"gate:{reason}"])
            findings.append(
                _mini_guard_finding(
                    disposition_ref,
                    artifact.id,
                    "reject",
                    reason,
                )
            )
            continue
        if artifact.id in session.state.artifacts or artifact.id in seen:
            findings.append(
                _mini_guard_finding(
                    disposition_ref,
                    artifact.id,
                    "deduplicate",
                    "content-duplicate",
                )
            )
            continue
        seen.add(artifact.id)
        admitted.append(
            (artifact, commitment_values, candidate_commitments)
        )
        findings.append(
            _mini_guard_finding(
                disposition_ref,
                artifact.id,
                "admit",
                "passed",
            )
        )
    return admitted, findings


def run(problems: list[tuple[str, str]], endpoint, budget: int, root: Path | str,
        vs_k: int | None = None, neighbourhood: int = 8,
        stance_decay: int = rotate.STANCE_DECAY, turnover_k: int = rotate.TURNOVER_K,
        window: int = 20, orbit_floor: int = 5, retry_max: int = 2,
        max_cycles: int = 1000,
        model_profile: str = DEFAULT_MODEL_PROFILE.value,
        near_dup_eps: float | None = MINI_NEAR_DUP_EPS) -> dict:
    """Drive (pid, description) problems until budget death, queue
    exhaustion, or global dryness. Returns the run summary; the log at
    ``root`` is the real output."""
    # Resolve presentation, wire schema, and the exact endpoint route before
    # the first call.  The reduced engine stays MiniReason; compact is its
    # explicit default model-facing representation.
    kernel = initialize(root, endpoint, model_profile)
    vs_k = kernel.profile.vs_k if vs_k is None else vs_k
    session = Session(root)
    logged_before = session.state.logged_tokens()
    meter = llm.TokenMeter(budget=budget)
    rotation = rotate.Rotation(decay=stance_decay)
    queue = list(problems)
    stop = "queue-exhausted"
    cycles = 0
    while queue and cycles < max_cycles:
        pid, description = queue[0]
        session.spawn_problem(pid, description)
        turnover = rotate.Turnover(k=turnover_k)
        while not turnover.dry and cycles < max_cycles:
            cycles += 1
            prompt = _prompt(description, rotation.directive,
                             _neighbourhood(session, pid, neighbourhood), vs_k)
            workflow = ConjectureApplicationBoundary.begin(
                session.harness,
                kernel.manifest,
                problem_ref=pid,
                route_lease=kernel.lease,
                contract_id=kernel.wire_contract.contract_id,
                meter_before=meter.snapshot(),
            )
            try:
                out, spend = llm.call(endpoint, prompt, ConjOut, meter,
                                      session.blobs, retry_max, role="conjecturer",
                                      model_profile=kernel.profile,
                                      wire_contract=kernel.wire_contract,
                                      endpoint_lease=kernel.lease,
                                      workflow_dispatch_observer=(
                                          workflow.authorize_dispatch
                                          if workflow is not None
                                          else None
                                      ),
                                      workflow_repair_observer=(
                                          workflow.authorize_repair
                                          if workflow is not None
                                          else None
                                      ))
            except llm.BudgetExceeded as e:
                if e.spend:  # exhaustion mid-retry still carries spend (G1)
                    # No complete provider result exists to settle a proposal
                    # receipt. Keep the spend honest but unbound, then close
                    # the issued shadow work explicitly.
                    partial = e.spend.model_copy(update={"work_order_id": None})
                    session.measure(["budget-exhausted"], partial)
                if workflow is not None:
                    workflow.abandon("mini:budget-exhausted")
                stop = "budget"
                queue = []
                break
            except llm.SchemaError as e:
                if (
                    workflow is not None
                    and e.spend is not None
                    and e.spend.work_order_id == workflow.work_order_id
                ):
                    source = session.measure(
                        ["workflow-conjecture-call", pid], e.spend
                    )
                    workflow.record_provider_result(
                        source_call_seq=source.seq,
                        llm_call=e.spend,
                        candidate_refs=(),
                    )
                    session.measure(["dropped-call"])
                    workflow.complete(
                        admitted_refs=(), meter_after=meter.snapshot()
                    )
                else:
                    session.measure(["dropped-call"], e.spend)
                rotation.tick()
                turnover.draw(0)
                continue
            except llm.EndpointError as e:
                if e.spend:
                    if (
                        workflow is not None
                        and e.spend.work_order_id == workflow.work_order_id
                    ):
                        source = session.measure(
                            ["workflow-conjecture-call", pid], e.spend
                        )
                        workflow.record_provider_result(
                            source_call_seq=source.seq,
                            llm_call=e.spend,
                            candidate_refs=(),
                        )
                        session.measure(["dropped-call"])
                        workflow.complete(
                            admitted_refs=(), meter_after=meter.snapshot()
                        )
                    else:
                        session.measure(["dropped-call"], e.spend)
                elif workflow is not None:
                    workflow.abandon("mini:endpoint-error")
                stop = "endpoint-error"
                queue = []
                break
            admitted: list[tuple[Artifact, list[dict]]] = []
            controlled = bool(
                workflow is not None
                and spend.work_order_id == workflow.work_order_id
            )
            source_call_seq = None
            if controlled:
                prepared = _prepare_controlled_candidates(
                    session, out, vs_k, rotation.stance
                )
                source = session.measure(
                    ["workflow-conjecture-call", pid], spend
                )
                source_call_seq = source.seq
                workflow.record_provider_result(
                    source_call_seq=source.seq,
                    llm_call=spend,
                    candidate_refs=tuple(row[0] for row in prepared),
                )
                admitted_rows, findings = _admit_controlled_candidates(
                    session,
                    prepared,
                    near_dup_eps=near_dup_eps,
                )
                workflow.record_guard(findings)
                for artifact, cks, candidate_commitments in admitted_rows:
                    commitment_ids = [
                        commitment.id for commitment in candidate_commitments
                    ]
                    registered = session.register_commitments(cks)
                    if registered != commitment_ids:
                        continue
                    admitted.append(
                        (
                            artifact.model_copy(
                                update={
                                    "provenance": artifact.provenance.model_copy(
                                        update={"event_seq": session.harness._next_seq}
                                    )
                                }
                            ),
                            cks,
                        )
                    )
            else:
                seen: set[str] = set()
                for candidate in out.candidates[:vs_k]:
                    content = candidate.content
                    cks = checks.compile_checks(content)
                    blocked = session._rubric_commitments(cks)
                    if blocked:
                        session._policy_drop(blocked)
                        continue
                    candidate_commitments = [
                        Commitment.model_validate(record) for record in cks
                    ]
                    commitment_ids = [
                        commitment.id for commitment in candidate_commitments
                    ]
                    artifact = session.build_candidate(
                        content, commitment_ids, rotation.stance
                    )
                    ok, reason = session.admit_candidate(
                        artifact,
                        [],
                        candidate_commitments=candidate_commitments,
                        near_dup_eps=near_dup_eps,
                    )
                    if not ok:
                        session.measure([f"gate:{reason}"])
                        continue
                    if artifact.id in session.state.artifacts or artifact.id in seen:
                        continue  # dedupe of live content: skipped, never gated
                    # Only the exact candidate that survived the mandatory guard
                    # may make its model-derived commitments canonical.
                    registered = session.register_commitments(cks)
                    if registered != commitment_ids:
                        continue
                    seen.add(artifact.id)
                    admitted.append((artifact, cks))
            if admitted:
                session.register_candidates(
                    [(artifact, []) for artifact, _ in admitted],
                    pid,
                    None if controlled else spend,
                    source_call_seq=source_call_seq,
                )
                for artifact, cks in admitted:
                    content = artifact.content_ref[len("inline:"):]
                    failures = checks.run_checks(content, cks)
                    if failures:
                        session.refute(artifact.id, failures)
            else:
                session.measure(
                    ["all-blocked"],
                    None if controlled else spend,
                )  # spend lands exactly once
            if controlled:
                workflow.complete(
                    admitted_refs=tuple(artifact.id for artifact, _ in admitted),
                    meter_after=meter.snapshot(),
                )
            new_survivors = sum(
                1 for artifact, _ in admitted if artifact.id not in session.state.refuted
            )
            rotation.tick()
            turnover.draw(new_survivors)
            orbit_school = gate.orbit(session.state.events, session.state.artifacts,
                                      window, orbit_floor)
            reason = rotation.due(orbit_school)
            if reason:
                session.rotate_stance(rotation, reason)
        if queue:
            if turnover.dry:
                session.measure(["intervention:turnover", f"problem:{pid}"])
            queue.pop(0)
    logged = session.state.logged_tokens()
    logged_this_run = logged - logged_before
    return {
        "engine_profile": ENGINE_PROFILE,
        "model_profile": kernel.profile.name.value,
        "run_manifest_sha256": kernel.manifest.sha256,
        "stop": stop if stop != "queue-exhausted" or not queue else "max-cycles",
        "cycles": cycles,
        "problems": {p: len(session.survivors(p)) for p in session.state.problems},
        "refuted": len(session.state.refuted),
        "gate_blocks": len(gate.gate_blocks(session.state.events, len(session.state.events))),
        "rotations": rotation.rotations,
        "tokens": meter.snapshot(),
        "meter_equals_log": meter.total == logged_this_run,
        "logged_tokens_this_run": logged_this_run,
        "logged_tokens": logged,
    }
