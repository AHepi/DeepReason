"""M2 — the driver: propose -> gate -> check -> log -> rotate (MINI_PLAN §3.7).

Session is the registration layer: every mutation is an event whose outputs
are parent-schema object records, so the root graduates to DeepReason by
pointing ``Harness(root)`` at it — no data conversion (G6). Refutation is
expressed the parent's way (nu artifact + demonstrative warrant + carrier),
which is exactly what makes v0 status a special case of parent adjudication.

Stop conditions: budget death, queue exhausted, all problems dry. Never
loop a dry problem — that is the measured 4.3x token burn.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from minireason import call as llm
from minireason import checks, gate, rotate
from minireason.log import (BlobStore, Call, Event, EventLog, ObjectStore, State,
                            apply_event, artifact_id, canonical_json)


class Candidate(BaseModel):
    content: str
    typicality: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("content", mode="before")
    @classmethod
    def _coerce(cls, value):
        # Models asked for skeleton content often emit the skeleton as a JSON
        # object instead of an embedded string — accept it canonically.
        return json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value


class ConjOut(BaseModel):
    candidates: list[Candidate] = Field(min_length=1)


class Session:
    """Open (or create) a mini root; state is replayed from the log."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.blobs = BlobStore(self.root / "blobs")
        self.objects = ObjectStore(self.root / "objects")
        self.log = EventLog(self.root / "log.jsonl")
        self.state = State()
        for event in self.log.read():
            apply_event(self.state, event, self.objects)

    def commit(self, rule: str, inputs: list[str], outputs: list[str],
               spend: Call | None = None) -> Event:
        event = Event(seq=self.log.next_seq,
                      ts=datetime.now(timezone.utc).isoformat(),
                      rule=rule, inputs=inputs, outputs=outputs, llm=spend)
        self.log.append(event)
        apply_event(self.state, event, self.objects)
        return event

    def measure(self, inputs: list[str], spend: Call | None = None) -> Event:
        return self.commit("Measure", inputs, [], spend)

    def spawn_problem(self, pid: str, description: str) -> None:
        if pid in self.state.problems:
            return
        self.objects.put("problem", pid, {
            "id": pid, "description": description, "criteria": [],
            "provenance": {"trigger": "seed", "from": []}})
        self.commit("Spawn", [], [pid])

    def register_commitments(self, commitments: list[dict]) -> None:
        new = [c for c in commitments if c["id"] not in self.state.commitments]
        for c in new:
            self.objects.put("commitment", c["id"], c)
        if new:
            self.commit("Register", [], [c["id"] for c in new])

    def register_candidates(self, entries: list[tuple[str, str, list[dict]]],
                            problem_id: str, stance: str,
                            spend: Call | None) -> list[str]:
        """entries: (artifact_id, content, checks). One Conj event carries
        every admitted candidate of the gamma-call (parent batching), and
        the call's spend — every token on the log exactly once (G1)."""
        ids = []
        for aid, content, cks in entries:
            self.objects.put("artifact", aid, {
                "id": aid, "content_ref": f"inline:{content}", "codec": "utf8",
                "interface": {"commitments": [c["id"] for c in cks], "refs": []},
                "warrants": [],
                "provenance": {"role": "conjecturer", "school": stance,
                               "event_seq": self.log.next_seq}})
            ids.append(aid)
        self.commit("Conj", [problem_id], ids, spend)
        return ids

    def refute(self, target: str, failures: list[dict]) -> None:
        """Register the parent-shaped refutation: nu (the check is sound &
        relevant) + demonstrative warrant + carrier. Grounded semantics then
        labels the target refuted in BOTH systems."""
        cid = failures[0]["commitment"]
        nu_content = f"nu: check {cid} is sound and relevant for {target[:12]}"
        nu_id = artifact_id(f"inline:{nu_content}", "utf8", {"commitments": [], "refs": []})
        self.objects.put("artifact", nu_id, {
            "id": nu_id, "content_ref": f"inline:{nu_content}", "codec": "utf8",
            "interface": {"commitments": [], "refs": []}, "warrants": [],
            "provenance": {"role": "critic", "school": None,
                           "event_seq": self.log.next_seq}})
        wid = f"w-{cid}-{target[:12]}"
        self.objects.put("warrant", wid, {
            "id": wid, "target": target, "type": "demonstrative",
            "commitment": cid, "verdict": "fail",
            "trace_ref": self.blobs.put(canonical_json(failures)),
            "validity_node": nu_id})
        carrier_content = f"check-refuter: {cid} fails on {target[:12]}"
        carrier_id = artifact_id(f"inline:{carrier_content}", "utf8",
                                 {"commitments": [], "refs": []})
        self.objects.put("artifact", carrier_id, {
            "id": carrier_id, "content_ref": f"inline:{carrier_content}",
            "codec": "utf8", "interface": {"commitments": [], "refs": []},
            "warrants": [wid],
            "provenance": {"role": "critic", "school": None,
                           "event_seq": self.log.next_seq}})
        self.commit("Crit", [], [nu_id, wid, carrier_id])

    def rotate_stance(self, rotation: rotate.Rotation, reason: str) -> None:
        old = rotation.stance
        stance = rotation.rotate()
        content = json.dumps({"school_policy": {
            "school": stance, "stance": rotate.STANCE_LIBRARY[stance]}}, sort_keys=True)
        pid = artifact_id(f"inline:{content}", "json", {"commitments": [], "refs": []})
        if pid not in self.state.artifacts:  # succession, not duplication
            self.objects.put("artifact", pid, {
                "id": pid, "content_ref": f"inline:{content}", "codec": "json",
                "interface": {"commitments": [], "refs": []}, "warrants": [],
                "provenance": {"role": "seed", "school": stance,
                               "event_seq": self.log.next_seq}})
            self.commit("Reseed", [], [pid])
        self.measure(["intervention:reseed", f"school:{old}", reason])

    def survivors(self, problem_id: str) -> list[str]:
        refuted = self.state.refuted
        return [a for a, p in self.state.addr if p == problem_id and a not in refuted]


def _neighbourhood(session: Session, problem_id: str, k: int) -> str:
    texts = []
    for aid in session.survivors(problem_id)[-k:]:
        content = session.state.artifacts[aid]["content_ref"][len("inline:"):]
        texts.append(f"- [{aid[:12]}] {content[:300]}")
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
        '"predicate:<python expression over the variable content>" for mechanically '
        'checkable cases or "rubric:std" otherwise. A candidate that forbids nothing '
        "is refuted on arrival.\n\n"
        f"PROBLEM: {description}\n"
        + (f"\nRECENT SURVIVORS (do not repeat; differ substantively):\n{neighbourhood}\n"
           if neighbourhood else "")
    )


def run(problems: list[tuple[str, str]], endpoint, budget: int, root: Path | str,
        vs_k: int = 6, neighbourhood: int = 8,
        stance_decay: int = rotate.STANCE_DECAY, turnover_k: int = rotate.TURNOVER_K,
        window: int = 20, orbit_floor: int = 5, retry_max: int = 2,
        max_cycles: int = 1000) -> dict:
    """Drive (pid, description) problems until budget death, queue
    exhaustion, or global dryness. Returns the run summary; the log at
    ``root`` is the real output."""
    session = Session(root)
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
            try:
                out, spend = llm.call(endpoint, prompt, ConjOut, meter,
                                      session.blobs, retry_max, role="conjecturer")
            except llm.BudgetExceeded as e:
                if e.spend:  # exhaustion mid-retry still carries spend (G1)
                    session.measure(["budget-exhausted"], e.spend)
                stop = "budget"
                queue = []
                break
            except llm.SchemaError as e:
                session.measure(["dropped-call"], e.spend)
                rotation.tick()
                turnover.draw(0)
                continue
            except llm.EndpointError as e:
                if e.spend:
                    session.measure(["dropped-call"], e.spend)
                stop = "endpoint-error"
                queue = []
                break
            admitted: list[tuple[str, str, list[dict]]] = []
            for candidate in out.candidates[:vs_k]:
                content = candidate.content
                cks = checks.compile_checks(content)
                aid = artifact_id(f"inline:{content}", "utf8",
                                  {"commitments": [c["id"] for c in cks], "refs": []})
                ok, reason = gate.check(aid, content, session.state)
                if not ok:
                    session.measure([f"gate:{reason}"])
                    continue
                if aid in session.state.artifacts or any(a == aid for a, _, _ in admitted):
                    continue  # dedupe of live content: skipped, never gated
                admitted.append((aid, content, cks))
            if admitted:
                for _, _, cks in admitted:
                    session.register_commitments(cks)
                session.register_candidates(admitted, pid, rotation.stance, spend)
                for aid, content, cks in admitted:
                    failures = checks.run_checks(content, cks)
                    if failures:
                        session.refute(aid, failures)
            else:
                session.measure(["all-blocked"], spend)  # spend lands exactly once
            new_survivors = sum(
                1 for aid, _, _ in admitted if aid not in session.state.refuted)
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
    return {
        "stop": stop if stop != "queue-exhausted" or not queue else "max-cycles",
        "cycles": cycles,
        "problems": {p: len(session.survivors(p)) for p in session.state.problems},
        "refuted": len(session.state.refuted),
        "gate_blocks": len(gate.gate_blocks(session.state.events, len(session.state.events))),
        "rotations": rotation.rotations,
        "tokens": meter.snapshot(),
        "meter_equals_log": meter.total == logged,
        "logged_tokens": logged,
    }
