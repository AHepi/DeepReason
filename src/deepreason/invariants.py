"""Post-run invariant checker — the chaos battery's measuring instrument.

Every check is a hard property the spec promises regardless of how badly
the engine LLM behaves: replay determinism (§0), accounting totality
(every token on the log exactly once), graph well-formedness (§2), and
detection totality. ``verify_root`` returns named violations so a report
can say WHICH promise broke; the chaos battery treats every entry as a
bug candidate.
"""

from pathlib import Path

from deepreason.adjudication.edges import DependenceCycleError, build_dep, toposort
from deepreason.harness import Harness
from deepreason.ontology.state import Status


def verify_root(root: Path, meter_total: int | None = None) -> dict:
    """Run every invariant over the session at ``root``. Returns
    {"violations": [{"check", "detail"}, ...], "stats": {...}}."""
    violations: list[dict] = []

    def fail(check: str, detail: str) -> None:
        violations.append({"check": check, "detail": detail[:400]})

    # 1. Replay determinism: two independent materializations agree.
    try:
        h = Harness(root)
        if Harness(root).state.model_dump_json() != h.state.model_dump_json():
            fail("replay", "two replays of the same log produced different state")
    except Exception as e:  # noqa: BLE001 - an unopenable root is the finding
        return {"violations": [{"check": "open", "detail": repr(e)[:400]}], "stats": {}}

    events = list(h.log.read())

    # 2. Incremental transitions == from-scratch walk.
    try:
        if h.transitions() != Harness(root).transitions():
            fail("transitions", "incremental transitions diverge from a fresh walk")
    except Exception as e:  # noqa: BLE001
        fail("transitions", repr(e))

    # 3. Time-travel at sampled seqs must not crash.
    seqs = [e.seq for e in events]
    for seq in sorted({seqs[i * (len(seqs) - 1) // 4] for i in range(5)} if seqs else []):
        try:
            Harness.at(root, seq)
        except Exception as e:  # noqa: BLE001
            fail("time-travel", f"Harness.at(seq={seq}): {e!r}")

    # 4. Accounting: meter total == sum of logged call tokens; every
    #    llm-bearing event's prompt/raw blobs exist.
    logged = 0
    for e in events:
        if e.llm is None:
            continue
        logged += e.llm.tokens
        for ref, kind in ((e.llm.prompt_ref, "prompt"), (e.llm.raw_ref, "raw")):
            if not ref:
                continue
            try:
                h.blobs.get(ref)
            except KeyError:
                fail("blobs", f"event seq={e.seq}: {kind} blob {ref[:12]} missing")
    if meter_total is not None and logged != meter_total:
        fail("accounting",
             f"meter says {meter_total} tokens, log accounts for {logged} "
             f"(delta {meter_total - logged})")

    # 5. Graph well-formedness.
    for wid, w in h.warrants.items():
        if w.validity_node not in h.state.artifacts:
            fail("warrant-validity", f"{wid}: validity node not registered")
        if w.target not in h.state.artifacts:
            fail("warrant-target", f"{wid}: target not registered")
    for x, t in h.state.att:
        if x not in h.state.artifacts or t not in h.state.artifacts:
            fail("att-endpoints", f"dangling attack edge ({x[:12]}, {t[:12]})")
    try:
        toposort(set(h.state.artifacts), build_dep(h.state.artifacts))
    except DependenceCycleError as e:
        fail("dep-dag", str(e))
    for aid, status in h.state.status.items():
        if status not in (Status.ACCEPTED, Status.REFUTED):
            fail("status-domain", f"{aid[:12]}: {status}")
    for aid, pid in h.state.addr:
        if aid not in h.state.artifacts or pid not in h.state.problems:
            fail("addr", f"dangling addr pair ({aid[:12]}, {pid})")

    # 6. Event stream: seqs strictly consecutive from 0.
    if seqs != list(range(len(seqs))):
        fail("seq-stream", "event seqs are not consecutive from 0")

    # 7. Detection stays a total function over a messy log.
    try:
        from deepreason.capture.detection import raw_flags
        from deepreason.config import Config
        from deepreason.llm.embedder import HashingEmbedder

        raw_flags(h, HashingEmbedder(), Config())
    except Exception as e:  # noqa: BLE001
        fail("detection-total", repr(e))

    stats = {
        "events": len(events),
        "artifacts": len(h.state.artifacts),
        "problems": len(h.state.problems),
        "warrants": len(h.warrants),
        "accepted": sum(1 for s in h.state.status.values() if s == Status.ACCEPTED),
        "refuted": sum(1 for s in h.state.status.values() if s == Status.REFUTED),
        "logged_tokens": logged,
        "gate_blocks": sum(1 for e in events for i in e.inputs if i.startswith("gate:")),
        "trial_blocks": sum(1 for e in events for i in e.inputs
                            if i.startswith("trial-blocked:")),
        "dropped_calls": sum(1 for e in events if "dropped-call" in e.inputs),
        "interventions": sum(1 for e in events for i in e.inputs
                             if i.startswith("intervention:")),
        "reseeds": sum(1 for e in events if e.rule.value == "Reseed"),
        "max_problem_desc_len": max(
            (len(p.description) for p in h.state.problems.values()), default=0),
    }
    return {"violations": violations, "stats": stats}
