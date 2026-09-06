"""What the organiser actually did with the room, read from ARM R's record.

A READER, written after the launch and affecting no sealed rule (PREREG's
decision rule is `analyse_organiser.py`'s alone): it reports, from the run
root only, the facts R35 asks for --

  * which room conjectures were carried (a candidate's verified citations
    resolved back to the attachment's records through CONVERSION.json), and
    beside it which were REACHED -- named by a verified citation of the
    conjecture's own block or of a proposal or objection about it, which the
    legend's cap does not throttle the same way;
  * how many counterconditions became commitments the artifacts carry;
  * the citation-check measures the record holds, by code;
  * per-seat spend and the cycle the budget ended in.

No model, no provider, no writes to the root.

    python tools/organiser_census.py <root> [--json OUT]
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TRANCHE = HERE.parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO))
CONVERSION = TRANCHE / "attachment" / "CONVERSION.json"


def census(root: pathlib.Path) -> dict:
    from deepreason.evidence.state import load_evidence_dossier, load_run_input
    from deepreason.harness import Harness
    from deepreason.ontology import Status

    harness = Harness(root, read_only=True)
    state = harness.state
    run_input = load_run_input(root)
    seed_id = run_input.problem.id
    dossier = load_evidence_dossier(root)

    # Which admission block is which room record. The attachment's headers no
    # longer carry a record id (P7 road A), so the map is by the BODY's own
    # sha256 -- the paragraph under the header line, which CONVERSION.json
    # records per room record. That is stronger than the old header match and
    # works on either attachment: the bodies never changed.
    conversion = json.loads(CONVERSION.read_text())
    records = {r["body_sha256"]: r for r in conversion["records"]}
    by_record_id = {r["id"]: r for r in conversion["records"]}
    block_record: dict[str, dict] = {}
    for block in dossier.blocks:
        try:
            body = harness.blobs.get(block.source_sha256)
        except Exception:  # noqa: BLE001 - a block whose bytes are not recoverable
            continue
        text = body[block.span_start:block.span_end].decode("utf-8", "replace")
        _, _, paragraph = text.partition("\n")
        for candidate in (paragraph, paragraph.rstrip("\n")):
            found = records.get(hashlib.sha256(candidate.encode("utf-8")).hexdigest())
            if found is not None:
                block_record[block.id] = found
                break
    # Citation checks from the record.
    codes = collections.Counter()
    cited_blocks: dict[str, set] = collections.defaultdict(set)
    for event in harness.log.read():
        if not event.inputs or not event.inputs[0].startswith("evidence-citation:"):
            continue
        code = event.inputs[0].split(":", 1)[1]
        codes[code] += 1
        if code == "EVIDENCE_CITATION_VERIFIED" and len(event.inputs) > 2:
            cited_blocks[event.inputs[2]].add(event.inputs[1])

    addressed: dict[str, set] = collections.defaultdict(set)
    for artifact_id, problem_id in state.addr:
        addressed[artifact_id].add(problem_id)
    carried_rooms: set[str] = set()
    reached_rooms: set[str] = set()
    positions = []
    for artifact_id, artifact in state.artifacts.items():
        if artifact.provenance.role.value != "conjecturer":
            continue
        commitments = [c for c in artifact.interface.commitments if c.startswith("reason-counter@")]
        rooms = {
            block_record[b]["id"][:8]
            for b in cited_blocks.get(artifact_id, ())
            if b in block_record and block_record[b]["kind"] == "conjecture"
        }
        carried_rooms |= rooms
        # A conjecture is REACHED when any verified citation names it -- the
        # conjecture's own block, or a proposal or objection written about it.
        # The legend shows a hash-ordered 32 of the 97 blocks (PARKED P2), and
        # on this attachment only 4 of the 12 conjecture blocks are in it, so
        # the strict count above is capped by the legend rather than by the
        # seat. This second count is not capped that way and is reported
        # beside it, never instead of it.
        reached = set(rooms)
        for b in cited_blocks.get(artifact_id, ()):
            record = block_record.get(b)
            if record is None:
                continue
            target = record["id"] if record["kind"] == "conjecture" else record["about"]
            if target in by_record_id and by_record_id[target]["kind"] == "conjecture":
                reached.add(target[:8])
        reached_rooms |= reached
        positions.append(
            {
                "id": artifact_id[:12],
                "seed": seed_id in addressed.get(artifact_id, ()),
                "status": (state.status.get(artifact_id).value if state.status.get(artifact_id) else None),
                "counterconditions": len(commitments),
                "room_conjectures_cited": sorted(rooms),
                "room_conjectures_reached": sorted(reached),
                "verified_citations": len(cited_blocks.get(artifact_id, ())),
            }
        )

    seats = collections.defaultdict(lambda: {"calls": 0, "tokens": 0})
    conjecturer_calls = []
    for event in harness.log.read():
        llm = getattr(event, "llm", None)
        if llm is None:
            continue
        seats[llm.role]["calls"] += 1
        seats[llm.role]["tokens"] += int(llm.tokens or 0)
        if llm.role == "conjecturer":
            conjecturer_calls.append(int(llm.tokens or 0))

    status = json.loads((root / "run-status.json").read_text()) if (root / "run-status.json").exists() else {}
    seed_positions = [p for p in positions if p["seed"]]
    return {
        "schema": "organiser-census.v1",
        "root": str(root),
        "run": {k: status.get(k) for k in ("state", "stop_reason", "cycle", "token_spend", "token_limit")},
        "seats": {role: dict(v) for role, v in sorted(seats.items())},
        "conjecturer_call_tokens": conjecturer_calls,
        "room_conjectures_carried": sorted(carried_rooms),
        "room_conjectures_reached": sorted(reached_rooms),
        "room_conjectures_available": sum(1 for r in records.values() if r["kind"] == "conjecture"),
        "citation_checks": dict(codes),
        "positions_total": len(positions),
        "positions_on_seed": len(seed_positions),
        "counterconditions_registered": sum(p["counterconditions"] for p in positions),
        "counterconditions_on_seed": sum(p["counterconditions"] for p in seed_positions),
        "accepted_on_seed": sum(1 for p in seed_positions if p["status"] == "accepted"),
        "refuted_on_seed": sum(1 for p in seed_positions if p["status"] == "refuted"),
        "positions": positions,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    out = census(pathlib.Path(args.root))
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    summary = {k: v for k, v in out.items() if k != "positions"}
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
