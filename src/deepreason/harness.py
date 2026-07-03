"""Harness core (spec §1–§4): registration, materialized view, replay.

Live registration validates well-formedness (§2), persists records to the
content-addressed object store, then builds an event and applies it via the
SAME code path replay uses — so reopening a harness from its log reproduces
state byte-for-byte (P0 acceptance). Adjudication (§4) recomputes after
every registration; its only inputs are att and dep (§0).
"""

from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from deepreason.adjudication.edges import (
    DependenceCycleError,
    build_att,
    build_dep,
    toposort,
)
from deepreason.adjudication.grounded import label0 as compute_label0
from deepreason.adjudication.support import final_labels
from deepreason.log.event_log import EventLog
from deepreason.ontology import (
    Artifact,
    Commitment,
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
from deepreason.storage.blobs import BlobStore
from deepreason.storage.objects import ObjectStore
from deepreason.unification.isolation import conn_map


class WellFormednessError(ValueError):
    """A registration would violate the formation rules (spec §2)."""


class Harness:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = BlobStore(self.root / "blobs")
        self.objects = ObjectStore(self.root / "objects")
        self.log = EventLog(self.root / "log.jsonl")
        self._reset()
        for event in self.log.read():
            self._apply_event(event)

    def _reset(self) -> None:
        self.state = EpistemicState()
        self.commitments: dict[str, Commitment] = {}
        self.warrants: dict[str, Warrant] = {}
        self._next_seq = 0

    @classmethod
    def at(cls, root: Path | str, seq: int) -> "Harness":
        """Time-travel: the harness as of event ``seq`` (spec §1). Read-only —
        do not register into a truncated view."""
        h = cls.__new__(cls)
        h.root = Path(root)
        h.blobs = BlobStore(h.root / "blobs")
        h.objects = ObjectStore(h.root / "objects")
        h.log = EventLog(h.root / "log.jsonl")
        h._reset()
        for event in h.log.read(upto_seq=seq):
            h._apply_event(event)
        return h

    # ------------------------------------------------------------------ #
    # Registration (live path: validate -> persist -> commit event)      #
    # ------------------------------------------------------------------ #

    def register_commitment(self, commitment: Commitment) -> Commitment:
        if commitment.id in self.commitments:
            return self.commitments[commitment.id]
        self.objects.put("commitment", commitment)
        self._commit(Rule.REGISTER, inputs=[], outputs=[commitment.id])
        return commitment

    def register_problem(self, problem: Problem) -> Problem:
        if problem.id in self.state.problems:
            return self.state.problems[problem.id]
        # Popper battery auto-pinned (spec §1).
        criteria = list(problem.criteria) + [
            b for b in POPPER_BATTERY if b not in problem.criteria
        ]
        problem = problem.model_copy(update={"criteria": criteria})
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
        if artifact.id in self.state.artifacts:
            return self.state.artifacts[artifact.id]  # content-addressed dedupe
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
    ) -> list[Artifact]:
        """Register several artifacts (+ their warrants) in one event — e.g.
        one Conj event per gamma-call carrying all admitted VS candidates."""
        candidate = dict(self.state.artifacts)
        accepted_entries: list[tuple[Artifact, list[Warrant]]] = []
        for artifact, warrants in entries:
            if artifact.id in candidate:
                continue  # content-addressed dedupe (incl. within the batch)
            provided = {w.id: w for w in warrants}
            # Every attack edge carries a registered warrant (§2).
            for wid in artifact.warrants:
                w = provided.get(wid) or self.warrants.get(wid)
                if w is None:
                    raise WellFormednessError(f"carried warrant not provided/registered: {wid}")
                self._validate_warrant(w)
            # Interface commitments must be registered (§2).
            for cid in artifact.interface.commitments:
                if cid not in self.commitments:
                    raise WellFormednessError(f"interface commitment not registered: {cid}")
            candidate[artifact.id] = artifact
            accepted_entries.append((artifact, warrants))
        if not accepted_entries:
            return []
        # dep must remain a DAG (§1): check the materialized edge set.
        try:
            toposort(set(candidate), build_dep(candidate))
        except DependenceCycleError as e:
            raise WellFormednessError(str(e)) from e

        outputs: list[str] = []
        for artifact, warrants in accepted_entries:
            provided = {w.id: w for w in warrants}
            for wid in artifact.warrants:
                if wid in provided and wid not in self.warrants and wid not in outputs:
                    self.objects.put("warrant", provided[wid])
                    outputs.append(wid)
            self.objects.put("artifact", artifact)
            outputs.append(artifact.id)
        self._commit(rule, inputs=[problem_id] if problem_id else [], outputs=outputs, llm=llm)
        return [self.state.artifacts[a.id] for a, _ in accepted_entries]

    def _validate_warrant(self, warrant: Warrant) -> None:
        if warrant.validity_node not in self.state.artifacts:
            raise WellFormednessError(
                f"warrant {warrant.id}: validity_node {warrant.validity_node} not registered"
            )
        if warrant.commitment and warrant.commitment not in self.commitments:
            raise WellFormednessError(
                f"warrant {warrant.id}: commitment {warrant.commitment} not registered"
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
    ) -> Event:
        event = Event(
            seq=self._next_seq,
            ts=datetime.now(timezone.utc).isoformat(),
            rule=rule,
            inputs=inputs,
            outputs=outputs,
            llm=llm,
        )
        event.state_diff = self._apply_event(event)
        self.log.append(event)
        return event

    def _apply_event(self, event: Event) -> StateDiff:
        pre_att = set(self.state.att)
        pre_dep = set(self.state.dep)
        pre_status = dict(self.state.status)
        a_add: list[str] = []
        pi_add: list[str] = []
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
                for pid in event.inputs:
                    if pid in self.state.problems and (obj.id, pid) not in self.state.addr:
                        self.state.addr.append((obj.id, pid))
        self._adjudicate()
        self._next_seq = event.seq + 1
        return StateDiff(
            att_add=sorted(set(self.state.att) - pre_att),
            dep_add=sorted(set(self.state.dep) - pre_dep),
            a_add=a_add,
            pi_add=pi_add,
            status_changed=sorted(
                i for i in self.state.artifacts if pre_status.get(i) != self.state.status.get(i)
            ),
        )

    # ------------------------------------------------------------------ #
    # Adjudication (Adj: after any registration, spec §3/§4)             #
    # ------------------------------------------------------------------ #

    def _adjudicate(self) -> None:
        nodes = set(self.state.artifacts)
        att = build_att(self.state.artifacts, self.warrants, self.commitments)
        dep = build_dep(self.state.artifacts)
        final = final_labels(compute_label0(nodes, att), dep)
        self.state.att = sorted(att)
        self.state.dep = sorted(dep)
        # Insertion (= registration) order keeps serialization deterministic.
        self.state.status = {i: final[i] for i in self.state.artifacts}
        self.state.conn = conn_map(dep, self.state.status)
