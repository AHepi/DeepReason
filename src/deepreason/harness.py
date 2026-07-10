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
    def __init__(self, root: Path | str, *, upto_seq: int | None = None) -> None:
        """Open (or create) a harness at ``root``; ``upto_seq`` truncates the
        replay for time-travel views (prefer the ``Harness.at`` spelling).

        Replay applies every event but adjudicates ONCE at the end: the
        grounded-extension fixpoint is a pure function of the final graph,
        so per-event adjudication during replay is discarded work (it made
        reopening an N-event log superlinear)."""
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = BlobStore(self.root / "blobs")
        self.objects = ObjectStore(self.root / "objects")
        self.log = EventLog(self.root / "log.jsonl")
        self._reset()
        for event in self.log.read(upto_seq=upto_seq):
            self._apply_event(event, adjudicate=False)
        self._adjudicate()

    _TAIL_CAP = 512  # bounded in-memory event tail (windows are ~CAPTURE_W)

    def _reset(self) -> None:
        self.state = EpistemicState()
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

    @classmethod
    def at(cls, root: Path | str, seq: int) -> "Harness":
        """Time-travel: the harness as of event ``seq`` (spec §1). Read-only —
        do not register into a truncated view."""
        return cls(root, upto_seq=seq)

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
                # A warrant's validity node may be an earlier artifact in this
                # same batch, not only one already in state (one Conj event can
                # carry both the nu and the critic that cites it).
                self._validate_warrant(w, known_artifacts=candidate)
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

    def record_measure(
        self,
        *,
        hv: dict[str, float] | None = None,
        reach: dict[str, float] | None = None,
        inputs: Iterable[str] = (),
        llm: LLMCall | None = None,
    ) -> Event:
        """Measure event (spec §3/§6): estimates steer attention, never
        status — they land in state.hv/state.reach only."""
        return self._commit(
            Rule.MEASURE,
            inputs=list(inputs),
            outputs=[],
            llm=llm,
            hv_set=hv or {},
            reach_set=reach or {},
        )

    def recent_events(self, window: int) -> list[Event]:
        """The last ``window`` events. Served from the bounded in-memory tail
        (populated by every _apply_event, live and replay) — capture detection
        calls this every cycle, and re-reading the JSONL log three times per
        cycle was measured quadratic. Falls back to a log read only when the
        window exceeds the tail."""
        if window <= len(self._tail) or self._next_seq <= len(self._tail):
            return self._tail[-window:]
        return list(self.log.read())[-window:]

    def embed_artifact(self, embedder, aid: str) -> list[float]:
        """Embed an artifact's content, cached: artifacts are immutable and
        content-addressed, so re-embedding the same id every cycle (capture
        metrics, the refuted index) is pure waste — and real money with an
        API embedder. Keyed by embedder type: embedders are deterministic
        functions, distinct types give distinct vectors."""
        from deepreason.programs import content_text

        key = (type(embedder).__name__, aid)
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
    ) -> Event:
        event = Event(
            seq=self._next_seq,
            ts=datetime.now(timezone.utc).isoformat(),
            rule=rule,
            inputs=inputs,
            outputs=outputs,
            llm=llm,
            state_diff=StateDiff(hv_set=hv_set or {}, reach_set=reach_set or {}),
        )
        event.state_diff = self._apply_event(event)
        self.log.append(event)
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
        if event.rule == Rule.REVEAL:
            # Reveal (§10.5): move sealed bytes from the holdout namespace
            # into the blob store — idempotent, so replay reproduces it.
            for aid in event.inputs:
                artifact = self.state.artifacts.get(aid)
                if artifact is None:
                    continue
                sealed = self.root / "holdout" / artifact.content_ref
                if sealed.exists():
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
                for pid in event.inputs:
                    if pid in self.state.problems and (obj.id, pid) not in self.state.addr:
                        self.state.addr.append((obj.id, pid))
        for aid, value in event.state_diff.hv_set.items():
            self.state.hv[aid] = value
        for aid, value in event.state_diff.reach_set.items():
            self.state.reach[aid] = value
        self._next_seq = event.seq + 1
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
