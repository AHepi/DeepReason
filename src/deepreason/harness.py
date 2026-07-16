"""Harness core (spec §1–§4): registration, materialized view, replay.

Live registration validates well-formedness (§2), persists records to the
content-addressed object store, then builds an event and applies it via the
SAME code path replay uses — so reopening a harness from its log reproduces
state byte-for-byte (P0 acceptance). Adjudication (§4) recomputes after
every registration; its only inputs are att and dep (§0).
"""

from collections.abc import Iterable
from bisect import bisect_left
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from pydantic import BaseModel

from deepreason.adjudication.edges import (
    DependenceCycleError,
    build_att,
    build_dep,
    toposort,
)
from deepreason.adjudication.grounded import label0 as compute_label0
from deepreason.adjudication.support import final_labels
from deepreason.bridge.events import BridgeAction, BridgeEventPayloadV1
from deepreason.bridge.state import BridgeState
from deepreason.canonical import canonical_json
from deepreason.control_events import ControlEventPayloadV1
from deepreason.conjecture_turn import (
    ConjectureAbstentionV1,
    ContextRequestV1,
)
from deepreason.log.event_log import EventLog
from deepreason.ontology import (
    Artifact,
    Commitment,
    ConjectureTurnEventPayloadV1,
    EpistemicState,
    Event,
    Interface,
    LLMCall,
    Problem,
    Provenance,
    Rule,
    StateDiff,
    Warrant,
)
from deepreason.ontology.problem import POPPER_BATTERY
from deepreason.scratch.events import ScratchEventPayloadV1
from deepreason.scratch.models import ScratchActor
from deepreason.scratch.state import ScratchState
from deepreason.storage.blobs import (
    BlobStore,
    FencedBlobStore,
    historical_sealed_refs,
)
from deepreason.storage.objects import SCHEMAS, ObjectStore
from deepreason.unification.isolation import conn_map


class WellFormednessError(ValueError):
    """A registration would violate the formation rules (spec §2)."""


class ReadOnlyHarnessError(RuntimeError):
    """A mutation was attempted through a time-travel materialization."""


class Harness:
    def __init__(
        self,
        root: Path | str,
        *,
        upto_seq: int | None = None,
        read_only: bool | None = None,
    ) -> None:
        """Open (or create) a harness at ``root``; ``upto_seq`` truncates the
        replay for time-travel views (prefer the ``Harness.at`` spelling).

        Replay applies every event but adjudicates ONCE at the end: the
        grounded-extension fixpoint is a pure function of the final graph,
        so per-event adjudication during replay is discarded work (it made
        reopening an N-event log superlinear)."""
        self.root = Path(root)
        self._read_only = (upto_seq is not None) if read_only is None else read_only
        if self._read_only:
            if not self.root.exists():
                raise FileNotFoundError(f"read-only harness root does not exist: {self.root}")
        else:
            self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = BlobStore(self.root / "blobs", read_only=self._read_only)
        self.objects = ObjectStore(self.root / "objects", read_only=self._read_only)
        self.log = EventLog(self.root / "log.jsonl", read_only=self._read_only)
        self._reset()
        revealed_artifact_ids: set[str] = set()
        for event in self.log.read(upto_seq=upto_seq):
            if event.rule == Rule.REVEAL:
                revealed_artifact_ids.update(event.inputs)
            self._apply_event(event, adjudicate=False)
        self._adjudicate()
        if upto_seq is None:
            self._verify_workflow_checkpoint()
        if self._read_only:
            self.blobs = FencedBlobStore(
                self.blobs,
                historical_sealed_refs(
                    self.blobs, self.state.artifacts, revealed_artifact_ids
                ),
            )

    _TAIL_CAP = 512  # bounded in-memory event tail (windows are ~CAPTURE_W)

    def _reset(self) -> None:
        self.state = EpistemicState()
        # Advisory scratch material is replayed beside, never inside, the
        # formal ontology.  No ScratchState field participates in att, dep,
        # warrant carriage, commitments, or adjudication.
        self.scratch_state = ScratchState()
        # Grounded final-view records are likewise process-only.  This index
        # is reconstructed from Bridge events and has no path into formal
        # graph materialization or adjudication.
        self.bridge_state = BridgeState()
        # Authority-only workflow state is reconstructed exclusively from
        # typed Control events and immutable workflow records.  It never
        # participates in formal graph adjudication.
        from deepreason.workflow.replay import WorkflowReplayState

        self.workflow_state = WorkflowReplayState()
        self.commitments: dict[str, Commitment] = {}
        self.warrants: dict[str, Warrant] = {}
        self._next_seq = 0
        # Derived caches — pure functions of the immutable, append-only
        # history, so they never need invalidation, only extension. They
        # exist because capture detection runs EVERY cycle and used to
        # re-read/re-replay/re-embed the whole log each time (measured
        # quadratic: ~7.6s/cycle at 2k events).
        self._tail: list[Event] = []
        self._trans_shadow: "Harness | None" = None
        self._trans_out: list[tuple[int, str, str | None, str]] = []
        self._embed_cache: dict[tuple[str, str], list[float]] = {}
        self._verdict_cache: dict[tuple[str, str], str] = {}
        self._semantic_excluded_event_seqs: set[int] = set()
        self._semantic_excluded_order: tuple[int, ...] | None = ()
        self._semantic_split_call_candidates: set[int] = set()
        # Live-only availability state: a sandbox resource abort is not an
        # epistemic event and is never replayed/cached, but generator/property
        # activation must fail closed until a later deterministic retry.
        self._oracle_pending: set[tuple[str, str]] = set()

    @classmethod
    def at(cls, root: Path | str, seq: int) -> "Harness":
        """Time-travel: the harness as of event ``seq`` (spec §1). Read-only —
        do not register into a truncated view."""
        return cls(root, upto_seq=seq, read_only=True)

    def _ensure_writable(self) -> None:
        if self._read_only:
            raise ReadOnlyHarnessError("time-travel harness is read-only")

    @property
    def _workflow_checkpoint_path(self) -> Path:
        return self.root / "workflow-checkpoint.json"

    def write_workflow_checkpoint(self) -> None:
        """Seal the latest complete authority prefix for tail-loss detection."""

        self._ensure_writable()
        if not self.workflow_state.event_seqs:
            return
        payload = {
            "schema": "workflow.checkpoint.v1",
            "process_digest": self.workflow_state.digest,
            "last_control_seq": max(self.workflow_state.event_seqs),
            "outstanding_work_order_ids": list(
                self.workflow_state.outstanding_work_order_ids
            ),
        }
        target = self._workflow_checkpoint_path
        temporary = target.with_suffix(f".tmp.{os.getpid()}")
        data = canonical_json(payload)
        with open(temporary, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)

    def _verify_workflow_checkpoint(self) -> None:
        path = self._workflow_checkpoint_path
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_bytes())
            if set(payload) != {
                "schema",
                "process_digest",
                "last_control_seq",
                "outstanding_work_order_ids",
            } or payload["schema"] != "workflow.checkpoint.v1":
                raise ValueError("workflow checkpoint has an invalid schema")
            checkpoint_seq = payload["last_control_seq"]
            if type(checkpoint_seq) is not int or checkpoint_seq < 0:
                raise ValueError("workflow checkpoint sequence is invalid")
            process_digest = payload["process_digest"]
            outstanding = payload["outstanding_work_order_ids"]
            if (
                not isinstance(process_digest, str)
                or not process_digest.startswith("sha256:")
                or len(process_digest) != 71
                or not isinstance(outstanding, list)
                or any(not isinstance(item, str) for item in outstanding)
                or outstanding != sorted(set(outstanding))
            ):
                raise ValueError("workflow checkpoint authority fields are invalid")
            current_seq = (
                max(self.workflow_state.event_seqs)
                if self.workflow_state.event_seqs
                else -1
            )
            if current_seq < checkpoint_seq:
                raise ValueError("workflow authority log lost its checkpointed tail")
            # Verify the sealed authority prefix even when newer Control
            # events exist.  Comparing only the latest state would let an
            # attacker replace a checkpointed transition and append an
            # unrelated later transition to bypass the equality check.
            from deepreason.workflow.replay import replay_workflow

            checkpoint_state = replay_workflow(
                self.log.read(upto_seq=checkpoint_seq),
                self.objects,
            )
            if (
                checkpoint_seq not in checkpoint_state.event_seqs
                or process_digest != checkpoint_state.digest
                or tuple(outstanding)
                != checkpoint_state.outstanding_work_order_ids
            ):
                raise ValueError("workflow checkpoint differs from replayed authority")
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError("workflow checkpoint is corrupt") from error

    # ------------------------------------------------------------------ #
    # Registration (live path: validate -> persist -> commit event)      #
    # ------------------------------------------------------------------ #

    def register_commitment(self, commitment: Commitment) -> Commitment:
        self._ensure_writable()
        if commitment.id in self.commitments:
            existing = self.commitments[commitment.id]
            if existing != commitment:
                raise WellFormednessError(
                    f"commitment id {commitment.id!r} conflicts with its registered record"
                )
            return existing
        self.objects.put("commitment", commitment)
        self._commit(Rule.REGISTER, inputs=[], outputs=[commitment.id])
        return self.commitments[commitment.id]

    def register_problem(self, problem: Problem) -> Problem:
        self._ensure_writable()
        # Popper battery auto-pinned (spec §1).
        criteria = list(problem.criteria) + [
            b for b in POPPER_BATTERY if b not in problem.criteria
        ]
        payload = problem.model_dump(mode="json", by_alias=True)
        payload["criteria"] = criteria
        problem = Problem.model_validate(payload)
        if problem.id in self.state.problems:
            existing = self.state.problems[problem.id]
            if existing != problem:
                raise WellFormednessError(
                    f"problem id {problem.id!r} conflicts with its registered record"
                )
            return existing
        self.objects.put("problem", problem)
        self._commit(Rule.SPAWN, inputs=list(problem.provenance.from_), outputs=[problem.id])
        return self.state.problems[problem.id]

    def create_artifact(
        self,
        content: bytes | str,
        *,
        codec: str = "utf8",
        interface: Interface | None = None,
        provenance: Provenance | None = None,
        warrants: Iterable[Warrant] = (),
        problem_id: str | None = None,
        rule: Rule = Rule.REGISTER,
        llm: LLMCall | None = None,
    ) -> Artifact:
        """Store content, compute the canonical id, and register."""
        self._ensure_writable()
        interface = interface or Interface()
        if isinstance(content, bytes):
            content_ref = self.blobs.put(content)
        else:
            content_ref = f"inline:{content}"
        warrants = list(warrants)
        artifact = Artifact(
            id=Artifact.compute_id(content_ref, codec, interface),
            content_ref=content_ref,
            codec=codec,
            interface=interface,
            warrants=[w.id for w in warrants],
            provenance=provenance or Provenance(role="user"),
        )
        return self.register_artifact(
            artifact, warrants=warrants, problem_id=problem_id, rule=rule, llm=llm
        )

    def register_artifact(
        self,
        artifact: Artifact,
        *,
        warrants: Iterable[Warrant] = (),
        problem_id: str | None = None,
        rule: Rule = Rule.REGISTER,
        llm: LLMCall | None = None,
    ) -> Artifact:
        self._ensure_writable()
        # register_batch handles both content dedupe and any NEW carriage
        # declared for an existing content artifact.
        self.register_batch(
            [(artifact, list(warrants))], problem_id=problem_id, rule=rule, llm=llm
        )
        return self.state.artifacts[artifact.id]

    def register_batch(
        self,
        entries: list[tuple[Artifact, list[Warrant]]],
        *,
        problem_id: str | None = None,
        rule: Rule = Rule.REGISTER,
        llm: LLMCall | None = None,
        process_inputs: Iterable[str] = (),
    ) -> list[Artifact]:
        """Register artifacts and explicit warrant-carriage relations.

        Content-addressed artifacts dedupe, but a new ``(artifact, warrant)``
        pair still commits. This is what lets identical criticism prose attack
        more than one target without changing the prose artifact's id.
        """
        self._ensure_writable()
        candidate = dict(self.state.artifacts)
        accepted_entries: list[tuple[Artifact, list[Warrant]]] = []
        carry_add: list[tuple[str, str]] = []
        known_carries = set(self.state.carries)
        new_warrants: dict[str, Warrant] = {}
        for artifact, warrants in entries:
            is_new = artifact.id not in candidate
            if not is_new:
                existing_artifact = candidate[artifact.id]
                if (
                    existing_artifact.content_ref != artifact.content_ref
                    or existing_artifact.codec != artifact.codec
                    or existing_artifact.interface != artifact.interface
                ):
                    raise WellFormednessError(
                        f"artifact id {artifact.id} conflicts with its content identity"
                    )
            provided = {w.id: w for w in warrants}
            # Every attack edge carries a registered warrant (§2).
            for wid in artifact.warrants:
                w = provided.get(wid) or new_warrants.get(wid) or self.warrants.get(wid)
                if w is None:
                    raise WellFormednessError(f"carried warrant not provided/registered: {wid}")
                if (
                    wid in provided
                    and wid in self.warrants
                    and provided[wid] != self.warrants[wid]
                ):
                    raise WellFormednessError(
                        f"warrant id {wid} conflicts with the registered record"
                    )
                # A warrant's validity node may be an earlier artifact in this
                # same batch, not only one already in state (one Conj event can
                # carry both the nu and the critic that cites it).
                self._validate_warrant(w, known_artifacts=candidate)
                pair = (artifact.id, wid)
                if pair not in known_carries:
                    carry_add.append(pair)
                    known_carries.add(pair)
                if wid in provided and wid not in self.warrants:
                    existing = new_warrants.get(wid)
                    if existing is not None and existing != provided[wid]:
                        raise WellFormednessError(
                            f"warrant id {wid} has conflicting records in one batch"
                        )
                    new_warrants[wid] = provided[wid]
            if not is_new:
                # The content object already exists, but newly declared
                # carriage above is still a real append-only graph relation.
                continue
            # Interface commitments must be registered (§2).
            for cid in artifact.interface.commitments:
                if cid not in self.commitments:
                    raise WellFormednessError(f"interface commitment not registered: {cid}")
            candidate[artifact.id] = artifact
            accepted_entries.append((artifact, warrants))
        if not accepted_entries and not carry_add:
            return []
        # dep must remain a DAG (§1): check the materialized edge set.
        try:
            toposort(set(candidate), build_dep(candidate))
        except DependenceCycleError as e:
            raise WellFormednessError(str(e)) from e

        outputs: list[str] = []
        for wid, warrant in new_warrants.items():
            self.objects.put("warrant", warrant)
            outputs.append(wid)
        for artifact, _ in accepted_entries:
            self.objects.put("artifact", artifact)
            outputs.append(artifact.id)
        # Existing callers detect content dedupe and record a shared LLM call
        # as a Measure. A carriage-only event therefore leaves llm unset so the
        # same call is not counted twice; a newly registered artifact keeps the
        # original attachment behavior.
        event_llm = llm if accepted_entries else None
        extra_inputs = tuple(process_inputs)
        if any(not isinstance(value, str) or not value for value in extra_inputs):
            raise ValueError("register_batch process inputs must be nonempty strings")
        self._commit(
            rule,
            inputs=[*([problem_id] if problem_id else []), *extra_inputs],
            outputs=outputs,
            llm=event_llm,
            carry_add=carry_add,
        )
        return [self.state.artifacts[a.id] for a, _ in accepted_entries]

    def carried_warrant_ids(self, artifact_id: str) -> list[str]:
        """Warrants explicitly carried by an artifact, in registration order.

        The materialized relation includes legacy Artifact.warrants entries,
        so callers do not need to distinguish old and new logs.
        """
        return [wid for carrier, wid in self.state.carries if carrier == artifact_id]

    def carrier_ids(self, warrant_id: str) -> list[str]:
        """Every artifact carrying ``warrant_id``, in registration order."""
        return [carrier for carrier, wid in self.state.carries if wid == warrant_id]

    def record_measure(
        self,
        *,
        hv: dict[str, float] | None = None,
        reach: dict[str, float] | None = None,
        addr: list[tuple[str, str]] | None = None,
        inputs: Iterable[str] = (),
        llm: LLMCall | None = None,
    ) -> Event:
        """Measure event (spec §3/§6): estimates steer attention, never
        status — they land in state.hv/state.reach only. ``addr`` carries the
        reach amendment (Def 3.7): full cross-problem survival registers the
        artifact as addressing the foreign problem (structure, not status)."""
        return self._commit(
            Rule.MEASURE,
            inputs=list(inputs),
            outputs=[],
            llm=llm,
            hv_set=hv or {},
            reach_set=reach or {},
            addr_add=addr or [],
        )

    def record_scratch_event(
        self,
        payload: ScratchEventPayloadV1,
        *,
        llm: LLMCall | None = None,
    ) -> Event:
        """Append one already-validated advisory scratch mutation.

        This is the narrow harness-owned persistence seam used by the scratch
        service and replay tests.  Callers must persist every named immutable
        output first; the shared apply path resolves and type-checks those
        records before the event becomes durable.  LLM accounting remains on
        the enclosing Event and is therefore counted exactly once.
        """
        return self._commit(
            Rule.SCRATCH,
            inputs=list(payload.inputs),
            outputs=list(payload.outputs),
            llm=llm,
            scratch=payload,
        )

    def record_conjecture_turn_event(
        self,
        payload: ConjectureTurnEventPayloadV1,
        *,
        request: ContextRequestV1 | None = None,
        abstention: ConjectureAbstentionV1 | None = None,
    ) -> Event:
        """Validate and append one harness-authored conjecture-turn result."""

        self._ensure_writable()
        payload = ConjectureTurnEventPayloadV1.model_validate(payload)
        source = next(
            (
                event
                for event in self._events_since(payload.source_call_seq)
                if event.seq == payload.source_call_seq
            ),
            None,
        )
        call = source.llm if source is not None else None
        expected_inputs = [
            "conjecture-turn-call",
            payload.problem_id,
            f"manifest:{payload.manifest_digest}",
        ]
        if payload.school_id is not None:
            expected_inputs.append(f"school:{payload.school_id}")
        if (
            source is None
            or source.seq >= self._next_seq
            or list(source.inputs) != expected_inputs
            or call is None
            or call.role != "conjecturer"
            or not call.attempt_trace
            or any(
                attempt.contract_id != "conjecturer.turn.v4"
                for attempt in call.attempt_trace
            )
        ):
            raise ValueError(
                "conjecture turn source must be one preceding manifest-bound v4 call"
            )
        route_school = (
            call.school_route.school_id if call.school_route is not None else None
        )
        if route_school != payload.school_id:
            raise ValueError("conjecture turn school differs from its source call")
        context = call.conjecture_context
        source_selection = (
            context.selection_receipt_ref if context is not None else None
        )
        if source_selection != payload.prior_selection_receipt_ref:
            raise ValueError(
                "conjecture turn prior selection differs from its source context"
            )
        if context is not None and (
            context.manifest_digest != payload.manifest_digest
            or context.problem_id != payload.problem_id
            or context.school_id != payload.school_id
        ):
            raise ValueError(
                "conjecture turn source context belongs to another work item"
            )

        evidence = None
        evidence_hash = None
        evidence_ref = None
        if payload.request_ref is not None:
            if request is None or abstention is not None:
                raise ValueError("context decisions require their canonical request")
            evidence = ContextRequestV1.model_validate(request)
            evidence_hash = evidence.request_hash
            evidence_ref = payload.request_ref
        elif payload.abstention_ref is not None:
            if abstention is None or request is not None:
                raise ValueError("abstention decisions require their canonical evidence")
            evidence = ConjectureAbstentionV1.model_validate(abstention)
            evidence_hash = evidence.abstention_hash
            evidence_ref = payload.abstention_ref
        if evidence is None or evidence_hash != (
            payload.request_hash or payload.abstention_hash
        ):
            raise ValueError("conjecture turn evidence hash differs from its payload")
        try:
            stored = self.blobs.get(evidence_ref)
        except KeyError as error:
            raise ValueError("conjecture turn evidence blob is missing") from error
        expected = canonical_json(
            evidence.model_dump(mode="json", exclude_none=True)
        )
        if stored != expected:
            raise ValueError("conjecture turn evidence blob is not canonical")

        reference = payload.request_hash or payload.abstention_hash
        assert reference is not None  # enforced by the typed payload
        return self._commit(
            Rule.CONJECTURE_TURN,
            inputs=[payload.problem_id, reference],
            outputs=[],
            conjecture_turn=payload,
        )

    def record_bridge_event(
        self,
        action: BridgeAction | str,
        *,
        actor: ScratchActor | str = ScratchActor.HARNESS,
        inputs: Iterable[str] = (),
        outputs: Iterable[str] | None = None,
        records: Iterable[tuple[str, BaseModel]] = (),
        llm: LLMCall | None = None,
        finding_ref: str | None = None,
        error_code: str | None = None,
    ) -> Event:
        """Persist canonical bridge records and append one typed process event.

        This is the sole public bridge persistence seam.  Every supplied
        record is revalidated against the shared object-store schema and its
        computed canonical identity before any write.  Explicit output IDs,
        when supplied, must exactly match those records in order; callers
        cannot author a different ID into the append-only log.
        """

        self._ensure_writable()

        def bounded(values, label: str, maximum: int = 2_048):
            if isinstance(values, (str, bytes)):
                raise TypeError(f"{label} must be an iterable of values, not a string")
            result = []
            for value in values:
                if len(result) >= maximum:
                    raise ValueError(f"{label} exceeds the bounded limit of {maximum}")
                result.append(value)
            return result

        normalized_records: list[tuple[str, str, BaseModel]] = []
        for item in bounded(records, "records"):
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise TypeError("each bridge record must be a (schema, object) pair")
            schema, obj = item
            if not isinstance(schema, str) or not schema.startswith("bridge-"):
                raise ValueError("record_bridge_event accepts only bridge object schemas")
            if not isinstance(obj, BaseModel):
                raise TypeError("bridge records must be validated Pydantic models")
            canonical = ObjectStore._record(schema, obj)
            normalized = SCHEMAS[schema].model_validate(canonical["data"])
            normalized_records.append((schema, canonical["id"], normalized))

        record_ids = [oid for _schema, oid, _obj in normalized_records]
        input_ids = bounded(inputs, "inputs")
        output_ids = record_ids if outputs is None else bounded(outputs, "outputs")
        if normalized_records and output_ids != record_ids:
            raise ValueError("explicit bridge outputs must exactly match canonical record IDs")
        if len(output_ids) != len(set(output_ids)):
            raise ValueError("bridge outputs must not contain duplicate object IDs")

        if normalized_records:
            resolved_records = normalized_records
        else:
            resolved_records = []
            for oid in output_ids:
                schema, obj = self.objects.get(oid)
                resolved_records.append((schema, oid, obj))

        payload_values = {
            "action": action,
            "actor": actor,
            "inputs": input_ids,
            "outputs": output_ids,
            "finding_ref": finding_ref,
            "error_code": error_code,
        }
        payload = BridgeEventPayloadV1.model_validate(payload_values)
        if payload.action == BridgeAction.WORKFLOW_RETRY_STARTED and llm is not None:
            raise ValueError("workflow retry authorization cannot contain an LLM call")
        self.bridge_state.validate(payload, resolved_records)

        if llm is not None:
            if not llm.prompt_ref:
                raise ValueError("bridge LLM call requires a prompt blob reference")
            self.blobs.get(llm.prompt_ref)
            empty_raw_allowed = bool(
                llm.attempt_trace and llm.attempt_trace[-1].usage_unknown
            )
            if llm.raw_ref:
                self.blobs.get(llm.raw_ref)
            elif not empty_raw_allowed:
                raise ValueError("bridge LLM call requires a raw-output blob reference")

        for schema, _oid, obj in normalized_records:
            self.objects.put(schema, obj)
        return self._commit(
            Rule.BRIDGE,
            inputs=input_ids,
            outputs=output_ids,
            llm=llm,
            bridge=payload,
        )

    def record_control_transition(
        self,
        decision,
        *,
        work_order=None,
        proposal_receipt=None,
        guard_result=None,
    ) -> Event:
        """Persist one canonical authority transition and its required record.

        Callers supply validated records, never event references.  This seam
        derives the exact input/output shape and the replay materializer
        checks pairing, route, capability, budget, and state-digest authority
        before the append becomes durable.
        """

        from deepreason.workflow.models import (
            GuardResultV1,
            ProposalReceiptV1,
            TransitionDecisionV1,
            TransitionKind,
            WorkOrderEnvelopeV1,
        )

        self._ensure_writable()

        def canonical(model_type, value):
            if value is None:
                return None
            payload = value.model_dump(mode="python", by_alias=True)
            return model_type.model_validate(payload)

        decision = canonical(TransitionDecisionV1, decision)
        work_order = canonical(WorkOrderEnvelopeV1, work_order)
        proposal_receipt = canonical(ProposalReceiptV1, proposal_receipt)
        guard_result = canonical(GuardResultV1, guard_result)
        provider = decision.transition_kind in {
            TransitionKind.PROPOSAL_RECEIVED,
            TransitionKind.REPAIR_EXHAUSTED,
        }
        guarded = decision.transition_kind in {
            TransitionKind.PROPOSAL_ADMITTED,
            TransitionKind.PROPOSAL_REJECTED,
            TransitionKind.PROPOSAL_DEDUPLICATED,
        }
        if (decision.transition_kind == TransitionKind.WORK_ENABLED) != (
            work_order is not None
        ):
            raise ValueError("work_enabled requires exactly one work-order record")
        if provider != (proposal_receipt is not None):
            raise ValueError(
                "provider-result transition requires exactly one proposal receipt"
            )
        if guarded != (guard_result is not None):
            raise ValueError("guarded transition requires exactly one guard result")

        records: list[tuple[str, BaseModel]] = []
        if work_order is not None:
            records.append(("workflow-work-order", work_order))
        if proposal_receipt is not None:
            records.append(("workflow-proposal-receipt", proposal_receipt))
        if guard_result is not None:
            records.append(("workflow-guard-result", guard_result))
        records.append(("workflow-transition-decision", decision))
        for schema, record in records:
            self.objects.put(schema, record)
        outputs = [record.id for _schema, record in records]
        inputs = [decision.work_order_id, decision.trigger_ref]
        payload = ControlEventPayloadV1(
            decision_ref=decision.id,
            inputs=inputs,
            outputs=outputs,
        )
        return self._commit(
            Rule.CONTROL,
            inputs=inputs,
            outputs=outputs,
            control=payload,
        )

    def build_bridge(self, problem_id: str, target: str, policy, **kwargs):
        """Build one fixed-fence grounded final view through canonical services.

        Adapters and the manifest digest are explicit keyword inputs until the
        RunManifest-v3 compiler binds them.  The implementation lives outside
        this already-large materializer so formal replay remains focused.
        """

        from deepreason.bridge.harness import build_grounded_bridge

        return build_grounded_bridge(self, problem_id, target, policy, **kwargs)

    def recent_events(self, window: int) -> list[Event]:
        """The last ``window`` events. Served from the bounded in-memory tail
        (populated by every _apply_event, live and replay) — capture detection
        calls this every cycle, and re-reading the JSONL log three times per
        cycle was measured quadratic. Falls back to a log read only when the
        window exceeds the tail."""
        if window <= len(self._tail) or self._next_seq <= len(self._tail):
            return self._tail[-window:]
        return list(self.log.read())[-window:]

    @staticmethod
    def _is_split_conjecture_call_carrier(event: Event) -> bool:
        return bool(
            event.llm is not None
            and event.inputs
            and event.inputs[0]
            in {"workflow-conjecture-call", "conjecture-turn-call"}
        )

    @classmethod
    def _split_conjecture_call_carriers(
        cls,
        values: Iterable[Event],
    ) -> set[int]:
        """Return provider carriers replaced by their referencing Conj action."""

        events = tuple(values)
        referenced_calls = {
            int(value.removeprefix("conjecture-call:"))
            for event in events
            for value in event.inputs
            if value.startswith("conjecture-call:")
            and value.removeprefix("conjecture-call:").isdigit()
        }
        return {
            event.seq
            for event in events
            if event.seq in referenced_calls
            and cls._is_split_conjecture_call_carrier(event)
        }

    def _advance_semantic_event_clock(self, event: Event) -> None:
        """Extend the derived clock with one replayed physical event."""

        changed = False
        if event.rule == Rule.CONTROL:
            self._semantic_excluded_event_seqs.add(event.seq)
            changed = True
        if self._is_split_conjecture_call_carrier(event):
            self._semantic_split_call_candidates.add(event.seq)
        for value in event.inputs:
            if not value.startswith("conjecture-call:"):
                continue
            suffix = value.removeprefix("conjecture-call:")
            if not suffix.isdigit():
                continue
            carrier_seq = int(suffix)
            if (
                carrier_seq in self._semantic_split_call_candidates
                and carrier_seq not in self._semantic_excluded_event_seqs
            ):
                self._semantic_excluded_event_seqs.add(carrier_seq)
                changed = True
        if changed:
            self._semantic_excluded_order = None

    def semantic_event_clock(self, event_seq: int | None = None) -> int:
        """Count behavior-visible actions before one physical event boundary.

        Control receipts do not advance semantic age. A split conjecturer-call
        Measure that is referenced by a later Conj event is the process carrier
        for that one semantic action, so it is replaced by (not counted beside)
        the Conj event. Unreferenced calls remain actions in their own right.

        ``event_seq`` is an exclusive physical boundary and defaults to the
        current append position. This keeps historical artifact provenance
        usable without letting C1 instrumentation accelerate semantic policy.
        """

        boundary = self._next_seq if event_seq is None else event_seq
        if type(boundary) is not int or not 0 <= boundary <= self._next_seq:
            raise ValueError("semantic event boundary is outside the replayed log")
        if self._semantic_excluded_order is None:
            self._semantic_excluded_order = tuple(
                sorted(self._semantic_excluded_event_seqs)
            )
        return boundary - bisect_left(self._semantic_excluded_order, boundary)

    def recent_semantic_events(self, window: int) -> list[Event]:
        """Return the last ``window`` semantic actions and their call carriers.

        C1 authority receipts are deliberately process-only.  Legacy capture
        metrics must therefore take their window *after* excluding them;
        filtering a normal recent-event window would let Control receipts or
        a split provider-call carrier displace the semantic observations that
        previously drove scheduling.  A carrier referenced by a chosen Conj
        event is included without consuming its own window slot.
        """

        if window <= 0:
            return []

        def select(values: list[Event]) -> tuple[list[Event], int, bool]:
            carriers = self._split_conjecture_call_carriers(values)
            core = [
                event
                for event in values
                if event.rule != Rule.CONTROL and event.seq not in carriers
            ]
            chosen = core[-window:]
            needed = {
                int(value.removeprefix("conjecture-call:"))
                for event in chosen
                for value in event.inputs
                if value.startswith("conjecture-call:")
                and value.removeprefix("conjecture-call:").isdigit()
            }
            chosen_seqs = {event.seq for event in chosen} | needed
            present = {event.seq for event in values}
            return (
                [event for event in values if event.seq in chosen_seqs],
                len(core),
                not needed.issubset(present),
            )

        tail = list(self._tail)
        selected, core_count, missing_carrier = select(tail)
        if (
            not missing_carrier
            and (core_count >= window or self._next_seq <= len(tail))
        ):
            return selected
        return select(list(self.log.read()))[0]

    def embed_artifact(self, embedder, aid: str) -> list[float]:
        """Embed an artifact's content, cached: artifacts are immutable and
        content-addressed, so re-embedding the same id every cycle (capture
        metrics, the refuted index) is pure waste — and real money with an
        API embedder. Keyed by embedder MODEL (falling back to type):
        embedders are deterministic functions within a process, and distinct
        models give distinct vectors — two NeuralEmbedders with different
        model ids must not share entries."""
        from deepreason.programs import content_text

        key = (getattr(embedder, "model", type(embedder).__name__), aid)
        vec = self._embed_cache.get(key)
        if vec is None:
            vec = embedder.embed(content_text(self.state.artifacts[aid], self.blobs))
            self._embed_cache[key] = vec
        return vec

    def _events_since(self, seq: int):
        """Events with .seq >= seq, from the tail when it covers them."""
        if self._tail and self._tail[0].seq <= seq:
            return [e for e in self._tail if e.seq >= seq]
        return (e for e in self.log.read() if e.seq >= seq)

    def record_llm_calls(self, calls: Iterable[LLMCall | None], tag: str, *extra: str) -> None:
        """Persist LLM calls that landed on no registration event — blocked
        trials, extra ensemble seats, defender/variator exchanges, all-deduped
        batches — as Measure events. Every call reaches the log exactly once
        (§0: replay consumes logged raws; token accounting reads event.llm),
        or replay and eval_report silently under-count real spend. ``extra``
        strings are appended to inputs — e.g. the drop REASON on a
        dropped-call, so the log answers 'why' without the in-memory
        diagnostics."""
        for call in calls:
            if call is not None:
                self.record_measure(inputs=[tag, *extra], llm=call)

    def transitions(self) -> list[tuple[int, str, str | None, str]]:
        """(seq, artifact, old_status, new_status) per logged event — a
        replay program over the log (§11.3 instrument). The shadow shares
        this instance's stores (read-only) and rewalks the log with a fresh
        state; copying __dict__ then _reset() keeps it in sync with any
        future field added to __init__ (no hand-mirrored constructor).

        INCREMENTAL: the shadow and its output persist on this instance and
        only the events committed since the previous call are applied.
        Capture detection calls this every cycle; the from-scratch rewalk
        (full per-event adjudication) was measured quadratic. The history is
        append-only, so extension is always sound."""
        if self._trans_shadow is None:
            shadow = Harness.__new__(Harness)
            shadow.__dict__.update(self.__dict__)
            shadow._reset()
            self._trans_shadow, self._trans_out = shadow, []
        shadow, out = self._trans_shadow, self._trans_out
        if shadow._next_seq < self._next_seq:
            for event in self._events_since(shadow._next_seq):
                pre = {aid: status for aid, status in shadow.state.status.items()}
                shadow._apply_event(event)
                for aid in event.state_diff.status_changed:
                    old = pre.get(aid)
                    new = shadow.state.status.get(aid)
                    if new is not None:
                        out.append((event.seq, aid, old.value if old else None, new.value))
        return list(out)

    def _validate_warrant(self, warrant: Warrant, known_artifacts=None) -> None:
        known = self.state.artifacts if known_artifacts is None else known_artifacts
        if warrant.validity_node not in known:
            raise WellFormednessError(
                f"warrant {warrant.id}: validity_node {warrant.validity_node} not registered"
            )
        if warrant.commitment and warrant.commitment not in self.commitments:
            raise WellFormednessError(
                f"warrant {warrant.id}: commitment {warrant.commitment} not registered"
            )
        # §2: every rubric-derived demonstrative warrant's trace_ref must
        # contain a conforming trial transcript (§3 guard, unbypassable).
        if warrant.commitment and self.commitments[warrant.commitment].eval.startswith(
            "rubric:"
        ):
            from deepreason.informal.trial import conforming_transcript

            if warrant.trace_ref is None or not conforming_transcript(
                self.blobs, warrant.trace_ref
            ):
                raise WellFormednessError(
                    f"warrant {warrant.id}: rubric-derived but trace_ref lacks a "
                    "conforming trial transcript (§2/§3)"
                )

    # ------------------------------------------------------------------ #
    # Event application (shared by live path and replay)                 #
    # ------------------------------------------------------------------ #

    def _commit(
        self,
        rule: Rule,
        inputs: list[str],
        outputs: list[str],
        llm: LLMCall | None = None,
        hv_set: dict[str, float] | None = None,
        reach_set: dict[str, float] | None = None,
        addr_add: list[tuple[str, str]] | None = None,
        carry_add: list[tuple[str, str]] | None = None,
        scratch: ScratchEventPayloadV1 | None = None,
        bridge: BridgeEventPayloadV1 | None = None,
        conjecture_turn: ConjectureTurnEventPayloadV1 | None = None,
        control: ControlEventPayloadV1 | None = None,
    ) -> Event:
        self._ensure_writable()
        event = Event(
            seq=self._next_seq,
            ts=datetime.now(timezone.utc).isoformat(),
            rule=rule,
            inputs=inputs,
            outputs=outputs,
            llm=llm,
            state_diff=StateDiff(hv_set=hv_set or {}, reach_set=reach_set or {},
                                 addr_add=addr_add or [], carry_add=carry_add or []),
            scratch=scratch,
            bridge=bridge,
            conjecture_turn=conjecture_turn,
            control=control,
        )
        try:
            state_diff = self._apply_event(event)
            event = event.model_copy(update={"state_diff": state_diff})
            self._tail[-1] = event  # _apply_event saw the provisional immutable event
            self.log.append(event)
        except Exception:
            # Object/blob writes are content-addressed and may remain orphaned,
            # but the live materialization must never outrun the durable log.
            self._reset()
            for durable in self.log.read():
                self._apply_event(durable, adjudicate=False)
            self._adjudicate()
            raise
        return event

    def _apply_event(self, event: Event, adjudicate: bool = True) -> StateDiff | None:
        """Apply one event to the materialized view. ``adjudicate=False`` skips
        the grounded-extension recompute and the per-event diff — used by
        replay, which adjudicates once at the end and discards the diffs."""
        pre_att = set(self.state.att)
        pre_dep = set(self.state.dep)
        pre_status = dict(self.state.status)
        a_add: list[str] = []
        pi_add: list[str] = []
        # Validate and materialize process-only outputs before the formal
        # object loop. A corrupt/malicious process event therefore cannot
        # transiently register a formal artifact and rely on model_copy to
        # bypass Event's StateDiff validator.
        try:
            self.workflow_state.observe_event(event)
            if event.control is not None:
                resolved_workflow = []
                for object_id in event.outputs:
                    schema, value = self.objects.get(object_id)
                    resolved_workflow.append((schema, object_id, value))
                self.workflow_state.apply(event, resolved_workflow)
        except ValueError as error:
            raise WellFormednessError(str(error)) from error
        if event.scratch is not None:
            self.scratch_state.apply(event, self.objects)
        if event.bridge is not None:
            try:
                self.bridge_state.apply(event, self.objects)
            except ValueError as error:
                raise WellFormednessError(str(error)) from error
        if event.rule == Rule.REVEAL:
            # Reveal (§10.5): move sealed bytes from the holdout namespace
            # into the blob store — idempotent, so replay reproduces it.
            for aid in event.inputs:
                artifact = self.state.artifacts.get(aid)
                if artifact is None:
                    continue
                sealed = self.root / "holdout" / artifact.content_ref
                if sealed.exists() and not self._read_only:
                    self.blobs.put(sealed.read_bytes())
        for oid in event.outputs:
            schema, obj = self.objects.get(oid)
            if schema == "commitment":
                self.commitments[obj.id] = obj
            elif schema == "warrant":
                self.warrants[obj.id] = obj
            elif schema == "problem":
                self.state.problems[obj.id] = obj
                pi_add.append(obj.id)
            elif schema == "artifact":
                self.state.artifacts[obj.id] = obj
                a_add.append(obj.id)
                # Backward compatibility: historical records embedded carriage
                # on the artifact. Materialize those entries into the explicit
                # relation during replay.
                for wid in obj.warrants:
                    pair = (obj.id, wid)
                    if pair not in self.state.carries:
                        self.state.carries.append(pair)
                for pid in event.inputs:
                    if pid in self.state.problems and (obj.id, pid) not in self.state.addr:
                        self.state.addr.append((obj.id, pid))
        for aid, value in event.state_diff.hv_set.items():
            self.state.hv[aid] = value
        for aid, value in event.state_diff.reach_set.items():
            self.state.reach[aid] = value
        for aid, pid in event.state_diff.addr_add:
            if pid in self.state.problems and (aid, pid) not in self.state.addr:
                self.state.addr.append((aid, pid))
        for carrier, wid in event.state_diff.carry_add:
            if (
                carrier in self.state.artifacts
                and wid in self.warrants
                and (carrier, wid) not in self.state.carries
            ):
                self.state.carries.append((carrier, wid))
        self._next_seq = event.seq + 1
        self._advance_semantic_event_clock(event)
        self._tail.append(event)
        if len(self._tail) > self._TAIL_CAP:
            del self._tail[: -self._TAIL_CAP]
        if not adjudicate:
            return None  # replay recomputes status once after the full walk
        self._adjudicate()
        return StateDiff(
            att_add=sorted(set(self.state.att) - pre_att),
            dep_add=sorted(set(self.state.dep) - pre_dep),
            a_add=a_add,
            pi_add=pi_add,
            status_changed=sorted(
                i for i in self.state.artifacts if pre_status.get(i) != self.state.status.get(i)
            ),
            hv_set=event.state_diff.hv_set,
            reach_set=event.state_diff.reach_set,
            addr_add=event.state_diff.addr_add,
            carry_add=event.state_diff.carry_add,
        )

    # ------------------------------------------------------------------ #
    # Adjudication (Adj: after any registration, spec §3/§4)             #
    # ------------------------------------------------------------------ #

    def _adjudicate(self) -> None:
        nodes = set(self.state.artifacts)
        att = build_att(
            self.state.artifacts,
            self.warrants,
            self.commitments,
            self.state.carries,
        )
        dep = build_dep(self.state.artifacts)
        final = final_labels(compute_label0(nodes, att), dep)
        self.state.att = sorted(att)
        self.state.dep = sorted(dep)
        # Insertion (= registration) order keeps serialization deterministic.
        self.state.status = {i: final[i] for i in self.state.artifacts}
        self.state.conn = conn_map(dep, self.state.status)
