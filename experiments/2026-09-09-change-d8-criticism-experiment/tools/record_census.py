#!/usr/bin/env python3
"""What each arm's RECORD says about criticism — SPEC S10, R23.

    python record_census.py <root> [<root> ...] [--label ARM=ROOT] [--out FILE]

Four things, per arm, and nothing else:

  attack edges minted     `state.att`, the harness's own fixpoint
  warrants by ROAD        demonstrative vs argumentative, from each warrant's
                          own `type` — the split that decides whether anything
                          a MODEL wrote ever moved a status, or whether every
                          status change came from a mechanical verdict
  refutations             artifacts whose final Status is REFUTED
  evidence states         open / supported / refuted / contested, READ from
                          `deepreason results --json` and never re-derived

THE WARRANT SPLIT IS THE POINT OF THIS INSTRUMENT. `DR-CON-warrants-and-attacks`
states the chain as: no warrant, no edge, no REFUTED. So counting attack edges
without splitting the warrants behind them answers nothing about criticism —
the two priority roots the 2026-09-08 audit examined had 118 and 345 edges and
ZERO argumentative warrants among them, which is the difference between "the
run criticised a lot" and "nothing a critic seat wrote changed anything"
(`AUDIT_REPORT.md` 2.3a).

WHY THE EVIDENCE STATES ARE READ AND NOT COMPUTED. `deepreason results --json`
already derives them, and a second derivation here would be a second thing to
keep in agreement with the first. The tranche's own check asserts this census
agrees with that surface byte for byte; if it ever disagrees, the surface is
right and this file is wrong.

Opens every root READ-ONLY: a writable open REPAIRS a record, which destroys
the evidence a reader opened it to look at (`dr-drive-harness` 5).
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "src"))

EVIDENCE_STATES = ("open", "supported", "refuted", "contested")


def _status_name(value) -> str:
    return str(value).split(".")[-1].upper()


def evidence_states(root: pathlib.Path) -> dict:
    """Read the four derived readings off the ONE retrieval surface.

    Absence is typed, never guessed: a root whose results surface carries no
    evidence-state block returns `None` per state with the reason beside it,
    because every committed root predates some field and a census that treated
    absence as zero would report a run that recorded nothing as a run that
    found nothing (`dr-execute-step`, durable-probe rule 5).
    """

    proc = subprocess.run(
        [sys.executable, "-m", "deepreason", "results", str(root), "--json"],
        capture_output=True, text=True, cwd=REPO,
    )
    if proc.returncode != 0:
        return {"read": False, "why": f"results exited {proc.returncode}",
                "counts": {state: None for state in EVIDENCE_STATES}}
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        return {"read": False, "why": f"results emitted no JSON: {error}",
                "counts": {state: None for state in EVIDENCE_STATES}}
    block = (payload.get("evidence_states") or {}).get("counts")
    if not isinstance(block, dict):
        return {"read": False, "why": "this root's results carry no evidence_states.counts",
                "counts": {state: None for state in EVIDENCE_STATES}}
    return {"read": True, "why": None,
            "counts": {state: block.get(state) for state in EVIDENCE_STATES}}


def warrants_by_road(warrants) -> collections.Counter:
    """Split warrants by the road that minted them.

    Pure, and separated from `census` deliberately so it can be exercised on
    BOTH roads. It cannot be exercised on both from any committed root: across
    the 20 most criticism-heavy roots in this repository the split is 1 141
    demonstrative and ZERO argumentative (measured 2026-09-09), so a live root
    can only ever drive the demonstrative branch. A column that has never
    returned a non-zero value is a column that cannot be told from a broken
    one, which is why the tranche's own test drives this function with an
    argumentative warrant and asserts the count moves.
    """

    return collections.Counter(
        str(getattr(w.type, "value", w.type)) for w in warrants.values()
    )


def census(root: pathlib.Path) -> dict:
    from deepreason.harness import Harness  # noqa: PLC0415

    harness = Harness(root, read_only=True)
    state = harness.state
    warrants = dict(harness.warrants)

    by_road = warrants_by_road(warrants)
    statuses = collections.Counter(_status_name(v) for v in state.status.values())
    # An artifact carrying an argumentative warrant is one a MODEL's case moved.
    # Reported separately from the road count because a road with warrants and
    # no refutations is a different fact from a road with neither.
    argumentative_targets = {
        w.target for w in warrants.values()
        if str(getattr(w.type, "value", w.type)) == "argumentative"
    }
    return {
        "root": str(root),
        "attack_edges": len(state.att),
        "warrants_total": len(warrants),
        "warrants_by_road": {
            "demonstrative": by_road.get("demonstrative", 0),
            "argumentative": by_road.get("argumentative", 0),
        },
        "argumentative_warrant_targets": len(argumentative_targets),
        "refutations": statuses.get("REFUTED", 0),
        "statuses": dict(statuses),
        "evidence_states": evidence_states(root),
    }


def render_census_table(rows: list[tuple[str, dict]]) -> str:
    out = [
        "| Arm | Attack edges | Warrants: demonstrative | Warrants: argumentative | "
        "Refutations | open | supported | refuted | contested |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for label, data in rows:
        roads = data["warrants_by_road"]
        counts = data["evidence_states"]["counts"]
        cells = [str(counts[s]) if counts[s] is not None else "—"
                 for s in EVIDENCE_STATES]
        out.append(
            f"| {label} | {data['attack_edges']} | {roads['demonstrative']} | "
            f"**{roads['argumentative']}** | {data['refutations']} | "
            + " | ".join(cells) + " |"
        )
    out.append("")
    out.append("The argumentative column is bold because it is the one that answers "
               "the question: a zero there means no status in this arm was moved by "
               "anything a critic seat wrote, however many edges the run minted.")
    for label, data in rows:
        if not data["evidence_states"]["read"]:
            out.append(f"NOTE {label}: evidence states unread — "
                       f"{data['evidence_states']['why']}")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="*")
    parser.add_argument("--label", action="append", default=[], metavar="ARM=ROOT")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    named = [tuple(spec.split("=", 1)) for spec in args.label]
    named += [(pathlib.Path(r).name, r) for r in args.roots]
    if not named:
        parser.error("give at least one root")

    seen, rows, payload = set(), [], {"schema": "record-census.v1", "arms": {}}
    for label, raw in named:
        root = pathlib.Path(raw).resolve()
        if str(root) in seen:
            continue
        seen.add(str(root))
        data = census(root)
        rows.append((label, data))
        payload["arms"][label] = data
    print(render_census_table(rows))
    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
