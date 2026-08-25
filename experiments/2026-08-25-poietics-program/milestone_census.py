#!/usr/bin/env python3
"""Decide P-R1's registered milestones from the TYPED record alone.

PREREG.md §5 registered three milestones before launch. This instrument
reads them out of the record and nothing else -- no prose is consulted, and
this script forms no opinion the record does not carry.

  M1  accepted conjectures proposing a mechanism   REQUIRED
  M2  criticism citing a byte-checked dossier block  REQUIRED
  M3  the section-14 corrections cited against a withdrawn number
                                                   REQUIRED IF TRIGGERED

Where each verdict comes from:

  M1  the run's terminal result gives accepted and survivor sets; each
      survivor's own bytes are then re-evaluated against
      `poietics-installation-mechanism@v1` with the SAME `programs.evaluate`
      the run used.  Re-deriving rather than trusting a stored warrant is
      deliberate: the verdict is then reproducible by anyone holding the
      root.
  M2  citation outcomes reach the record as Measure events whose first
      input is `evidence-citation:<CODE>` (conjecture side,
      `rules/conj.py`) or `premise-citation:<CODE>` (critic side,
      `rules/crit.py`).  Only `EVIDENCE_CITATION_VERIFIED` counts -- an
      unverified citation is recorded evidence of a failed citation, not of
      an engaged one.  The block id is mapped back to its source file
      through the dossier's `source_sha256`.
  M3  conditional.  Its trigger is an accepted artifact containing a
      withdrawn figure.  UNTRIGGERED is neither a pass nor a failure, and
      the exit code below treats it that way.

Opens the root READ-ONLY (dr-drive-harness §5: a writable open repairs,
i.e. destroys, the evidence).

Exit 0 when M1 and M2 hold and M3 is met-or-untriggered; 1 otherwise. That
code is NOT the tranche's verdict -- PREREG.md §6 is -- but a non-zero exit
means a REQUIRED milestone is unmet and RESULTS.md must record a negative.

Usage:  python milestone_census.py <root> [out.json]
"""
from __future__ import annotations

import json
import pathlib
import sys

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

from build_manifest_pr1 import CRITERIA  # noqa: E402
from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402

MECHANISM_CRITERION = "poietics-installation-mechanism@v1"
VERIFIED = "EVIDENCE_CITATION_VERIFIED"

# PREREG.md §5 M3. The record's README names exactly these two withdrawn
# figures; the third string is the shape the second one is usually quoted in.
WITHDRAWN_FIGURES = ("6/6 held", "6/6", "59 caught", "59/3", "3 survived")

# report/14, by content digest. Derived, not typed in: the dossier's source
# ids are a prefix of the file's sha256, so this stays true across rebuilds.
SECTION_14 = "record/report/14_CORRECTIONS_AND_WITHDRAWN_CLAIMS.md"


def _read_json(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _terminal_result(root: pathlib.Path) -> dict:
    """The run's terminal facts, assembled from the files that own each.

    No single file carries all three. ``run-result.json`` owns the survivor
    set, ``run-status.json`` owns the cycle and the activity that ended it,
    and ``run-stop.json`` owns the typed stop reason. Reading only the first
    one that exists -- which an earlier draft of this script did -- silently
    reported ``stop_reason=None`` for a run that had a perfectly good one.
    """

    result = dict(_read_json(root / "run-result.json"))
    status = _read_json(root / "run-status.json")
    stop = _read_json(root / "run-stop.json")
    result.setdefault("state", status.get("state") or status.get("phase"))
    result["stop_reason"] = (
        stop.get("reason")
        or result.get("stop_reason")
        or status.get("activity")
    )
    result["cycle"] = result.get("cycle") or status.get("cycle")
    return result


def _source_by_digest(harness) -> dict[str, str]:
    """content_sha256 -> file name, for every source in every bound dossier."""

    from deepreason.amendment.state import dossier_union

    mapping: dict[str, str] = {}
    for dossier in dossier_union(harness.root):
        for source in dossier.sources:
            mapping[source.content_sha256] = source.source_locator
    return mapping


def _block_source(harness) -> dict[str, str]:
    """block id -> content_sha256 of the source it was cut from."""

    from deepreason.amendment.state import dossier_union

    mapping: dict[str, str] = {}
    for dossier in dossier_union(harness.root):
        for block in getattr(dossier, "blocks", ()) or ():
            mapping[block.id] = block.source_sha256
    return mapping


def census(root: pathlib.Path) -> dict:
    harness = Harness(root, read_only=True)
    state = harness.state
    result = _terminal_result(root)

    accepted = [
        aid for aid, status in state.status.items() if status == Status.ACCEPTED
    ]
    survivors = list(result.get("survivors") or ()) or accepted

    # ---- M1 -------------------------------------------------------------
    mechanism = next(
        (c for c in CRITERIA if c.id == MECHANISM_CRITERION), None
    )
    m1_artifacts = []
    if mechanism is not None:
        for aid in survivors:
            artifact = state.artifacts.get(aid)
            if artifact is None:
                continue
            verdict, _ = programs.evaluate(mechanism, artifact, harness.blobs)
            if verdict == programs.PASS:
                m1_artifacts.append(aid)
    m1 = {
        "milestone": "M1 accepted conjectures proposing a mechanism",
        "required": True,
        "accepted_count": len(accepted),
        "survivor_count": len(survivors),
        "criterion": MECHANISM_CRITERION,
        "survivors_passing": m1_artifacts,
        "met": bool(accepted) and bool(survivors) and bool(m1_artifacts),
    }

    # ---- M2 -------------------------------------------------------------
    by_digest = _source_by_digest(harness)
    block_source = _block_source(harness)
    record_digests = {
        digest
        for digest, locator in by_digest.items()
        if "/record/" in locator.replace("\\", "/")
    }

    verified_citations = []
    for line in (root / "log.jsonl").read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("rule") != "Measure":
            continue
        inputs = event.get("inputs") or []
        if not inputs or not isinstance(inputs[0], str):
            continue
        tag = inputs[0]
        if not tag.startswith(("evidence-citation:", "premise-citation:")):
            continue
        if not tag.endswith(VERIFIED):
            continue
        block_id = inputs[1] if len(inputs) > 1 else None
        digest = block_source.get(block_id or "")
        verified_citations.append({
            "seq": event.get("seq"),
            "side": tag.split(":", 1)[0],
            "block_id": block_id,
            "source": by_digest.get(digest or "", "<unresolved>"),
            "in_record": digest in record_digests,
        })

    m2_hits = [c for c in verified_citations if c["in_record"]]
    m2 = {
        "milestone": "M2 criticism citing a byte-checked dossier block",
        "required": True,
        "verified_citations_total": len(verified_citations),
        "verified_citations_into_record": len(m2_hits),
        "sources_cited": sorted({c["source"] for c in m2_hits}),
        "critic_side_hits": sum(
            1 for c in m2_hits if c["side"] == "premise-citation"
        ),
        "met": bool(m2_hits),
    }

    # ---- M3 -------------------------------------------------------------
    leaning = []
    for aid in accepted:
        artifact = state.artifacts.get(aid)
        if artifact is None:
            continue
        try:
            text = harness.blobs.get(artifact.content_ref).decode(
                "utf-8", errors="replace"
            )
        except Exception:  # pragma: no cover - unreadable blob is not a lean
            continue
        found = [f for f in WITHDRAWN_FIGURES if f.lower() in text.lower()]
        if found:
            leaning.append({"artifact": aid, "figures": found})

    section_14_digest = next(
        (d for d, loc in by_digest.items() if loc.endswith(SECTION_14.split("/")[-1])),
        None,
    )
    cited_14 = [
        c for c in verified_citations
        if block_source.get(c["block_id"] or "") == section_14_digest
    ]
    m3 = {
        "milestone": "M3 the section-14 corrections cited against a withdrawn number",
        "required_if_triggered": True,
        "triggered": bool(leaning),
        "conjectures_leaning_on_a_withdrawn_figure": leaning,
        "section_14_citations": len(cited_14),
        "met": bool(cited_14) if leaning else None,
        "status": (
            "UNTRIGGERED (neither a pass nor a failure -- PREREG.md §5)"
            if not leaning
            else ("MET" if cited_14 else "UNMET")
        ),
    }

    holds = m1["met"] and m2["met"] and (m3["met"] is not False)
    return {
        "root": str(root),
        "state": result.get("state"),
        "stop_reason": result.get("stop_reason") or result.get("reason"),
        "M1": m1,
        "M2": m2,
        "M3": m3,
        "required_milestones_hold": holds,
    }


def main() -> int:
    if not 2 <= len(sys.argv) <= 3:
        print("usage: milestone_census.py <root> [out.json]", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) == 3 else TRANCHE / "milestones.json"
    report = census(root)
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

    m1, m2, m3 = report["M1"], report["M2"], report["M3"]
    print(f"state={report['state']} stop_reason={report['stop_reason']}")
    print(f"M1 {'MET' if m1['met'] else 'UNMET'}  "
          f"accepted={m1['accepted_count']} survivors={m1['survivor_count']} "
          f"passing {m1['criterion']}: {len(m1['survivors_passing'])}")
    print(f"M2 {'MET' if m2['met'] else 'UNMET'}  "
          f"verified citations {m2['verified_citations_total']}, "
          f"into the record {m2['verified_citations_into_record']} "
          f"(critic side {m2['critic_side_hits']})")
    if m2["sources_cited"]:
        for source in m2["sources_cited"]:
            print(f"      cited: {source}")
    print(f"M3 {m3['status']}  "
          f"conjectures leaning on a withdrawn figure: "
          f"{len(m3['conjectures_leaning_on_a_withdrawn_figure'])}, "
          f"section-14 citations: {m3['section_14_citations']}")
    print(f"\nrequired milestones hold: {report['required_milestones_hold']}")
    print(f"report {out}")
    return 0 if report["required_milestones_hold"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
