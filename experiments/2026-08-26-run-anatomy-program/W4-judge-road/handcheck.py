#!/usr/bin/env python3
"""W4 Q4: the INDEPENDENT re-derivation behind the 60-row hand sample.

This file imports NOTHING from `deepreason`. That is the point: W2's
mechanical check re-ran `deepreason.programs.evaluate`, the very evaluator
that wrote the verdicts, so a bug in it would have reproduced itself on
both sides and read as 463/463 correct. Here the two predicate families
are re-implemented from the commitment's own `eval` text, in ordinary
Python, by a second author.

It also emits the DECISIVE FACT for every row -- the collinear or
near-degenerate triple for the geometric family, the matched terms for the
term-count family -- because that is what a reader can actually check by
eye. A row's ruling in ADJUDICATION_SAMPLE.md is made against the decisive
fact and the artifact bytes, not against this script's boolean.

A `fail` verdict means the commitment's predicate evaluated FALSE on the
artifact's content (`rules/warrants.py::register_fail_warrant`: each
`fail` packages a demonstrative warrant). So:

    ruling = correct    when independent_predicate is False and verdict is fail
    ruling = incorrect  when independent_predicate is True  and verdict is fail
    ruling = ambiguous  when the predicate's own text leaves the outcome
                        genuinely underdetermined on these bytes

Writes handcheck.json.
"""
from __future__ import annotations

import ast
import json
import re
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "verdict_sample.json"
OUT = HERE / "handcheck.json"

POINT_RE = re.compile(r"POINT[ \t]+([0-9]*\.?[0-9]+)[ \t]+([0-9]*\.?[0-9]+)")
CLAIM_RE = re.compile(r"CLAIM[ \t]+([-+0-9.eE]+)")


def terms_from_eval(expr: str) -> tuple[list[tuple[tuple[str, ...], int]], int]:
    """Pull the (term tuple, floor) pairs out of a term-count predicate.

    Parsed from the `eval` text with `ast`, not retyped: a retyped term
    list is a second source of truth and the first thing to drift.
    `any(...)` clauses become floor 1, `sum(...) >= n` clauses floor n,
    and a bare `'literal' in content.lower()` clause becomes a one-term
    tuple at floor 1.

    Returns the clauses AND the number of top-level conjuncts the
    expression actually has, so the caller can refuse to rule when the two
    disagree. That guard is not decoration: the first version of this
    function handled only `any` and `sum` and silently dropped the bare
    `'refuted if' in content.lower()` conjunct of
    `relation-form@578e42df713e`, reconstructing a two-clause predicate as
    one clause. The ruling happened to survive because the dropped clause
    was the TRUE one -- had it been the false one, this file would have
    reported a correct verdict as incorrect and never said why.
    """
    body = expr.split("predicate:", 1)[1]
    tree = ast.parse(body, mode="eval").body
    clauses: list[tuple[tuple[str, ...], int]] = []
    conjuncts = (
        len(tree.values)
        if isinstance(tree, ast.BoolOp) and isinstance(tree.op, ast.And)
        else 1
    )

    def literal_tuple(node) -> tuple[str, ...] | None:
        try:
            value = ast.literal_eval(node)
        except (ValueError, SyntaxError):
            return None
        return tuple(value) if isinstance(value, tuple) else None

    def visit(node) -> None:
        if isinstance(node, ast.BoolOp):
            for item in node.values:
                visit(item)
            return
        if isinstance(node, ast.Compare) and isinstance(node.ops[0], ast.In):
            try:
                literal = ast.literal_eval(node.left)
            except (ValueError, SyntaxError):
                return
            if isinstance(literal, str):
                clauses.append(((literal,), 1))
            return
        if isinstance(node, ast.Compare) and isinstance(node.ops[0], ast.GtE):
            floor = ast.literal_eval(node.comparators[0])
            call = node.left
            if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "sum":
                comp = call.args[0]
                for gen in comp.generators:
                    terms = literal_tuple(gen.iter)
                    if terms:
                        clauses.append((terms, int(floor)))
            return
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "any":
            comp = node.args[0]
            for gen in comp.generators:
                terms = literal_tuple(gen.iter)
                if terms:
                    clauses.append((terms, 1))
            return

    visit(tree)
    return clauses, conjuncts


def check_terms(content: str, expr: str) -> dict:
    lowered = content.lower()
    clauses, conjuncts = terms_from_eval(expr)
    if len(clauses) != conjuncts:
        # The reconstruction is incomplete. Refuse to rule rather than rule
        # on a predicate this file does not fully model.
        return {
            "family": "term-count",
            "predicate_holds": None,
            "clauses": [],
            "unreconstructed": (
                f"parsed {len(clauses)} clauses from {conjuncts} top-level "
                "conjuncts"
            ),
        }
    detail = []
    holds = True
    for terms, floor in clauses:
        found = [t for t in terms if t in lowered]
        detail.append({"floor": floor, "found": found, "n_found": len(found),
                       "clause_holds": len(found) >= floor})
        holds = holds and len(found) >= floor
    return {"family": "term-count", "predicate_holds": holds,
            "conjuncts": conjuncts, "clauses": detail}


def min_triangle_area(points: list[tuple[float, float]]) -> tuple[float, tuple]:
    best = None
    witness = ()
    for a, b, c in combinations(sorted(points), 3):
        area = abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2.0
        if best is None or area < best:
            best, witness = area, (a, b, c)
    return (best if best is not None else float("nan")), witness


def check_geometry(content: str, commitment: str) -> dict:
    raw = POINT_RE.findall(content)
    points = sorted((float(a), float(b)) for a, b in raw)
    n = len(points)
    distinct = len(set(points))
    in_unit = all(0.0 <= c <= 1.0 for p in points for c in p)
    result = {
        "family": "geometry",
        "n_points": n,
        "n_distinct": distinct,
        "all_in_unit_square": in_unit,
        "thirteen_distinct_points": n == 13 and distinct == 13,
    }
    if n != 13 or distinct != 13 or not in_unit:
        # `all(... for raw in [...])` over a one-element list: a failed
        # shape clause makes the whole predicate False, and the area terms
        # are never reached. Recorded as the decisive fact.
        result["predicate_holds"] = False
        result["decisive"] = (
            f"shape clause fails: {n} POINT lines, {distinct} distinct, "
            f"all in [0,1]^2 = {in_unit}"
        )
        return result
    area, witness = min_triangle_area(points)
    result["min_triangle_area"] = area
    result["min_area_witness"] = [list(p) for p in witness]
    if commitment == "frontier-wellformed@v1":
        result["predicate_holds"] = True
        result["decisive"] = "13 distinct points inside the unit square"
    elif commitment == "frontier-above-floor@v1":
        result["floor"] = 0.005
        result["predicate_holds"] = area >= 0.005
        result["decisive"] = (
            f"min triangle area {area!r} vs floor 0.005, witness {witness}"
        )
    elif commitment == "frontier-claim-honest@v1":
        claims = CLAIM_RE.findall(content)
        result["claims"] = claims
        if not claims:
            result["predicate_holds"] = False
            result["decisive"] = "no CLAIM line: len(cl) > 0 fails"
        else:
            claimed = float(claims[-1])
            result["claimed"] = claimed
            result["predicate_holds"] = area >= claimed - 1e-12
            result["decisive"] = (
                f"min triangle area {area!r} vs CLAIM {claimed!r}, "
                f"witness {witness}"
            )
    else:  # pragma: no cover - guard
        result["predicate_holds"] = None
        result["decisive"] = f"unhandled commitment {commitment}"
    return result


def main() -> int:
    payload = json.loads(SAMPLE.read_text())
    rows = []
    for root_name, root in payload["roots"].items():
        for entry in root["sample"]:
            content = entry["content"] or ""
            expr = entry["eval"]
            if entry["commitment"].startswith("frontier-"):
                check = check_geometry(content, entry["commitment"])
            elif "predicate:" in expr and "POINT" not in expr:
                check = check_terms(content, expr)
            else:  # pragma: no cover - guard
                check = {"family": "unhandled", "predicate_holds": None}
            verdict = entry["recorded_verdict"]
            holds = check.get("predicate_holds")
            if holds is None:
                ruling = "ambiguous"
            elif verdict == "fail":
                ruling = "correct" if holds is False else "incorrect"
            else:
                ruling = "correct" if holds is True else "incorrect"
            rows.append(
                {
                    "root": root_name,
                    "seq": entry["seq"],
                    "commitment": entry["commitment"],
                    "target": entry["target"],
                    "recorded_verdict": verdict,
                    "independent_predicate_holds": holds,
                    "ruling": ruling,
                    "target_status_final": entry["target_status_final"],
                    "commitment_in_target_interface": entry[
                        "commitment_in_target_interface"
                    ],
                    "warrant_materialized_attack_edge": entry[
                        "warrant_materialized_attack_edge"
                    ],
                    "content_chars": entry["content_chars"],
                    "check": check,
                }
            )
    tally: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = tally.setdefault(row["root"], {})
        bucket[row["ruling"]] = bucket.get(row["ruling"], 0) + 1
    OUT.write_text(
        json.dumps(
            {"schema": "w4.handcheck.v1", "tally": tally, "rows": rows},
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(tally, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
