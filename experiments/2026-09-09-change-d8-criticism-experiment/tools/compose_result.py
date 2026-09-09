"""The judged unit: a run's composed result, derived from the ROOT with no
model in the loop (SPEC S16/S17, R17; PREREG §4).

    python compose_result.py <root> [--out FILE] [--json FILE]
    python compose_result.py --self-test

The unit is the seed problem's positions at the terminal, read the way
`deepreason findings` reads them: every conjecturer artifact addressed to the
operator's question, by status. An ACCEPTED position is rendered as its
claim, its mechanism, the refutation conditions it committed to (the
counterconditions of its envelope, which admission registered as the
commitments the artifact carries), and its stated uncertainties. A REFUTED
position is listed with the case that refuted it (the attacker's claim text,
from the attack edges the record holds). Nothing is chosen, ranked or
paraphrased: a survivor is a survivor because the record says so, and the
composition is a deterministic rendering of that record.

What it does NOT do: reach a provider (no transport of any kind is imported
here), weigh positions, or read derived problems' positions as
answers to the question (they answer sub-questions; their count is reported
in the footer so a reader can see how much of the run's work lies outside the
unit).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
SELF_TEST_ROOT = (
    REPO / "experiments/2026-09-03-change-provenance-history-channel/runs/home-m1/runs/"
    "run-ad41064484366337ed61a9d5a58de58f"
)


def _claim_body(artifact) -> dict | None:
    content = artifact.content_ref.removeprefix("inline:")
    try:
        value = json.loads(content)
    except (TypeError, ValueError):
        return {"claim": str(content)}
    if not isinstance(value, dict) or "school_policy" in value:
        return None
    if value.get("schema") in {"attached-source-record.v1"}:
        return None
    if not any(isinstance(value.get(k), str) and value[k].strip() for k in ("claim", "content", "statement")):
        return None
    return value


def _position_block(index: int, body: dict) -> list[str]:
    """One surviving position, rendered once.

    Called by the composed text AND by --per-position, so a per-position unit
    is byte-identical to its own paragraph inside the composed unit. Two
    renderers would let the secondary comparison drift away from the primary
    one silently, which is exactly the drift the secondary comparison exists
    to be immune from.
    """

    claim = body.get("claim") or body.get("content") or body.get("statement") or ""
    block = [f"{index}. {claim.strip()}"]
    mechanism = (body.get("mechanism") or "").strip()
    if mechanism:
        block.append(f"   Mechanism: {mechanism}")
    counters = [c.get("case", "") for c in body.get("counterconditions") or [] if isinstance(c, dict)]
    if counters:
        block.append("   Refuted if:")
        for case in counters:
            block.append(f"   - {case.strip()}")
    uncertainties = [u for u in body.get("uncertainties") or [] if isinstance(u, str) and u.strip()]
    if uncertainties:
        block.append("   Uncertainties: " + " | ".join(u.strip() for u in uncertainties))
    return block


def compose(root: pathlib.Path) -> tuple[str, dict]:
    from deepreason.evidence.state import load_run_input
    from deepreason.harness import Harness
    from deepreason.ontology import Status

    harness = Harness(root, read_only=True)
    state = harness.state
    run_input = load_run_input(root)
    seed_id = run_input.problem.id
    question = run_input.problem.description
    addressed: dict[str, set[str]] = {}
    for artifact_id, problem_id in state.addr:
        addressed.setdefault(artifact_id, set()).add(problem_id)
    attackers: dict[str, list[str]] = {}
    for attacker, target in state.att:
        attackers.setdefault(target, []).append(attacker)

    def order_key(artifact_id):
        return state.artifacts[artifact_id].provenance.event_seq

    seed_positions = sorted(
        (
            aid for aid, art in state.artifacts.items()
            if art.provenance.role.value == "conjecturer" and seed_id in addressed.get(aid, ())
        ),
        key=order_key,
    )
    derived_positions = [
        aid for aid, art in state.artifacts.items()
        if art.provenance.role.value == "conjecturer" and seed_id not in addressed.get(aid, ())
    ]
    accepted, refuted, other = [], [], []
    for aid in seed_positions:
        status = state.status.get(aid)
        body = _claim_body(state.artifacts[aid])
        if body is None:
            continue
        row = (aid, body, status)
        if status == Status.ACCEPTED:
            accepted.append(row)
        elif status == Status.REFUTED:
            refuted.append(row)
        else:
            other.append(row)

    lines = [f"QUESTION: {question}", ""]
    lines.append(f"SURVIVING POSITIONS ({len(accepted)}):")
    per_position = []
    for index, (aid, body, _status) in enumerate(accepted, 1):
        block = _position_block(index, body)
        per_position.append({"index": index, "artifact": aid,
                             "text": "\n".join(block).rstrip() + "\n"})
        lines.extend(block)
        lines.append("")
    lines.append(f"REFUTED POSITIONS ({len(refuted)}):")
    for index, (aid, body, _status) in enumerate(refuted, 1):
        claim = body.get("claim") or body.get("content") or body.get("statement") or ""
        lines.append(f"{index}. {claim.strip()}")
        for attacker in attackers.get(aid, []):
            attacker_body = _claim_body(state.artifacts[attacker]) if attacker in state.artifacts else None
            if attacker_body:
                case = attacker_body.get("claim") or attacker_body.get("content") or attacker_body.get("case") or ""
                if case:
                    lines.append(f"   Refuted by: {str(case).strip()}")
        lines.append("")
    if other:
        lines.append(f"SUSPENDED POSITIONS ({len(other)}): " + "; ".join(
            (b.get("claim") or b.get("content") or "").strip()[:200] for _a, b, _s in other
        ))
        lines.append("")
    lines.append(
        f"(Positions on {len(set(p for ids in addressed.values() for p in ids) - {seed_id})} derived "
        f"sub-questions, {len(derived_positions)} in all, are not part of this answer.)"
    )
    text = "\n".join(lines).rstrip() + "\n"
    summary = {
        "schema": "composed-result.v1",
        "root": str(root),
        "seed_problem": seed_id,
        "seed_positions": len(seed_positions),
        "accepted": len(accepted),
        "refuted": len(refuted),
        "suspended": len(other),
        "derived_positions": len(derived_positions),
        "chars": len(text),
    }
    return text, summary, per_position


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--per-position", default=None, metavar="DIR",
                    help="write each surviving position as its own unit (R19)")
    args = ap.parse_args()
    root = SELF_TEST_ROOT if args.self_test else pathlib.Path(args.root or "")
    if not (root / "log.jsonl").exists():
        print(f"not a run root: {root}", file=sys.stderr)
        return 2
    text, summary, per_position = compose(root)
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding="utf-8")
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if args.per_position:
        out_dir = pathlib.Path(args.per_position)
        out_dir.mkdir(parents=True, exist_ok=True)
        # Named by ORDINAL, which `order_key` already fixed, never by artifact
        # id: a filename that renumbered when a lower-sorting position arrived
        # is the one thing a stable unit may not do.
        for unit in per_position:
            (out_dir / f"position-{unit['index']:02d}.txt").write_text(
                unit["text"], encoding="utf-8")
        (out_dir / "UNITS.json").write_text(
            json.dumps({"schema": "per-position-units.v1", "root": str(root),
                        "units": [{"index": u["index"], "artifact": u["artifact"],
                                   "chars": len(u["text"])} for u in per_position]},
                       indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if args.self_test:
        print(f"self-test: {summary['accepted']} surviving, {summary['refuted']} refuted, "
              f"{summary['chars']} chars, seed positions {summary['seed_positions']}")
        return 0 if summary["seed_positions"] > 0 else 1
    if not args.out:
        sys.stdout.write(text)
    print(json.dumps(summary, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
