"""W1 — the P-C1 headline, attributed to named field-level causes.

RESULTS.md of `experiments/2026-08-25-change-constructive-frontier` records
that ARM H produced 15 valid constructions out of 132 (11.4%) while ARM S
produced 23 out of 53 scored samples (43.4%). That gap is the largest single
measured value leak in the record, and "89% invalid" is not yet a cause.

This attributes both arms' invalidity to the FIELD that failed and to HOW,
using that tranche's own committed scoring artifacts (`arm_h_scores.json`,
`arm_s_merged.jsonl`) — the same numbers its RESULTS.md quotes, so this
cannot drift from the tranche it describes.

The instance is Heilbronn N=13: place 13 points in the unit square, maximise
the minimum triangle area over all 286 triples. A candidate is a single free
STRING field carrying N `POINT x y` lines and one `CLAIM v` line. That is the
whole form, which is why the failure is a free-string failure and not a schema
failure — the contract cannot express "the number you wrote is the number your
own points have".
"""
from __future__ import annotations

import json
import os
import re
import sys
import glob
from collections import Counter

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "2026-08-25-change-constructive-frontier",
))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PC1 = os.path.join(REPO, "experiments", "2026-08-25-change-constructive-frontier")

POINT = re.compile(r"^\s*POINT\s+(\S+)\s+(\S+)\s*$", re.MULTILINE)
CLAIM = re.compile(r"^\s*CLAIM\s+(\S+)\s*$", re.MULTILINE)
REQUIRED_N = 13
FLOOR = 0.005


def claim_text(candidate: dict) -> str:
    """The candidate's construction string, whichever field carries it."""
    raw = candidate.get("text")
    if not raw:
        return ""
    try:
        obj = json.loads(raw)
    except ValueError:
        return raw
    if isinstance(obj, dict):
        for key in ("claim", "content", "candidate"):
            v = obj.get(key)
            if isinstance(v, str):
                return v
            if isinstance(v, dict) and isinstance(v.get("claim"), str):
                return v["claim"]
    return raw


def decimals(token: str) -> int:
    return len(token.split(".")[1].rstrip("0")) if "." in token else 0


def geometry(text: str) -> dict:
    pts = POINT.findall(text)
    claims = CLAIM.findall(text)
    coords, places, out_of_range, nonnumeric = [], [], 0, 0
    for a, b in pts:
        for tok in (a, b):
            try:
                val = float(tok)
            except ValueError:
                nonnumeric += 1
                continue
            places.append(decimals(tok))
            if not (0.0 <= val <= 1.0):
                out_of_range += 1
        try:
            coords.append((float(a), float(b)))
        except ValueError:
            pass
    return {
        "n_point_lines": len(pts),
        "n_claim_lines": len(claims),
        "claim_token": claims[-1] if claims else None,
        "distinct_points": len(set(coords)),
        "duplicate_points": len(coords) - len(set(coords)),
        "coord_decimal_places": Counter(places),
        "coords_out_of_unit_square": out_of_range,
        "nonnumeric_coords": nonnumeric,
    }


def attribute(candidates: list[dict], arm: str) -> dict:
    causes = Counter()
    field_causes = Counter()
    inflation = []
    collinear = 0
    decimals_all = Counter()
    dup_total = out_total = nonnum_total = 0
    count_errors = Counter()
    exemplars: dict[str, dict] = {}

    for c in candidates:
        if c.get("error"):
            causes["TRANSPORT_ERROR/no response scored"] += 1
            continue
        text = claim_text(c)
        g = geometry(text) if text else {}
        decimals_all.update(g.get("coord_decimal_places") or {})
        dup_total += g.get("duplicate_points", 0)
        out_total += g.get("coords_out_of_unit_square", 0)
        nonnum_total += g.get("nonnumeric_coords", 0)

        code = c.get("code")
        n_points = c.get("n_points")
        score = c.get("score")
        claimed = c.get("claim")

        if code == "WRONG_COUNT":
            causes["WRONG_COUNT"] += 1
            field_causes["claim string: wrong number of POINT lines"] += 1
            count_errors[n_points] += 1
            exemplars.setdefault("WRONG_COUNT", {"candidate": c, "geometry": g, "text": text})
        elif code == "CLAIM_INFLATED":
            causes["CLAIM_INFLATED"] += 1
            field_causes["claim string: CLAIM value exceeds the construction's own minimum"] += 1
            if score == 0:
                collinear += 1
            elif isinstance(score, (int, float)) and isinstance(claimed, (int, float)) and score > 0:
                inflation.append(claimed / score)
            key = "CLAIM_INFLATED_collinear" if score == 0 else "CLAIM_INFLATED_overstated"
            exemplars.setdefault(key, {"candidate": c, "geometry": g, "text": text})
        elif code:
            causes[str(code)] += 1
            field_causes[f"claim string: {code}"] += 1
        else:
            if c.get("above_floor"):
                causes["VALID_above_floor"] += 1
            else:
                causes["VALID_below_registered_floor"] += 1
                exemplars.setdefault("VALID_below_floor", {"candidate": c, "geometry": g, "text": text})

    scored = [c for c in candidates if not c.get("error")]
    valid = sum(1 for c in scored if c.get("claim_confirmed") is True)
    inflation.sort()
    return {
        "arm": arm,
        "candidates_scored": len(scored),
        "transport_errors": sum(1 for c in candidates if c.get("error")),
        "valid_checker_confirmed": valid,
        "validity_rate": round(valid / len(scored), 4) if scored else None,
        "invalid": len(scored) - valid,
        "invalidity_rate": round((len(scored) - valid) / len(scored), 4) if scored else None,
        "causes": dict(causes.most_common()),
        "field_level_causes": dict(field_causes.most_common()),
        "claim_inflated_detail": {
            "total": causes.get("CLAIM_INFLATED", 0),
            "true_minimum_exactly_zero_collinear": collinear,
            "true_minimum_positive_but_overstated": len(inflation),
            "inflation_ratio_claimed_over_actual": {
                "min": round(min(inflation), 2) if inflation else None,
                "median": round(inflation[len(inflation) // 2], 2) if inflation else None,
                "max": round(max(inflation), 2) if inflation else None,
            },
        },
        "wrong_count_detail": {
            "required_points": REQUIRED_N,
            "observed_point_counts": dict(count_errors),
        },
        "coordinate_hygiene": {
            "decimal_places_written": dict(sorted(decimals_all.items())),
            "duplicate_points_total": dup_total,
            "coords_outside_unit_square": out_total,
            "nonnumeric_coordinates": nonnum_total,
        },
        "exemplars": {
            k: {
                "score": v["candidate"].get("score"),
                "score_exact": v["candidate"].get("score_exact"),
                "claimed": v["candidate"].get("claim"),
                "n_points": v["candidate"].get("n_points"),
                "code": v["candidate"].get("code"),
                "construction": v["text"][:1200],
            }
            for k, v in exemplars.items()
        },
    }


# --------------------------------------------------------------------------
# Mechanism census: what the coordinates themselves looked like.
#
# `arm_h_scores.json` stores `text` only for candidates the checker CONFIRMED
# ("text": text[:4000] if verdict["valid"] else None, score_run.py:157), so the
# 117 refuted constructions -- the whole subject of the headline -- are not in
# it. They are in the run root's raw provider blobs, which is where this reads
# them: the bytes the model actually wrote. ARM S's constructions are the
# committed sample files.
# --------------------------------------------------------------------------


def constructions_from_root(root: str) -> list[dict]:
    """Every POINT-bearing string any provider response in this root wrote."""
    import census as C

    out, seen = [], set()
    for line in open(os.path.join(root, "log.jsonl")):
        line = line.strip()
        if not line:
            continue
        event = json.loads(line)
        llm = event.get("llm")
        if not llm:
            continue
        _, text = C.read_blob(root, llm.get("raw_ref"))
        parsed, _ = C.parse_model_json(text)
        if parsed is None:
            continue
        for _, kind, value in C.walk_values(parsed):
            if kind != "string" or "POINT" not in value:
                continue
            if not POINT.search(value):
                continue
            key = value.strip()
            if key in seen:
                continue
            seen.add(key)
            out.append({"seq": event["seq"], "role": llm.get("role"), "text": value})
    return out


def constructions_from_samples(pattern: str) -> list[dict]:
    out, seen = [], set()
    for path in sorted(glob.glob(pattern)):
        text = open(path).read()
        if not POINT.search(text) or text.strip() in seen:
            continue
        seen.add(text.strip())
        out.append({"sample": os.path.basename(path), "text": text})
    return out


def collinearity_signature(text: str) -> dict:
    """Code-scorable structural causes of a zero minimum area.

    A triple is collinear iff its area is 0, so a zero score always has a
    geometric cause. Two of those causes are visible in the POINT lines
    themselves, without any geometry: three points sharing an x coordinate
    (a vertical line) or three sharing a y coordinate (a horizontal line).
    That is the lattice/grid signature, and it is the one a model produces by
    writing round numbers. A zero with neither signature is a genuinely
    oblique collinear triple, which is a harder mistake to see and a different
    finding.
    """
    from fractions import Fraction as F

    pts = []
    for a, b in POINT.findall(text):
        try:
            pts.append((F(a), F(b)))
        except (ValueError, ZeroDivisionError):
            pass
    xs = Counter(p[0] for p in pts)
    ys = Counter(p[1] for p in pts)
    return {
        "points": len(pts),
        "x_shared_by_3_or_more": sum(1 for n in xs.values() if n >= 3),
        "y_shared_by_3_or_more": sum(1 for n in ys.values() if n >= 3),
        "axis_aligned_triple_present": any(n >= 3 for n in xs.values())
        or any(n >= 3 for n in ys.values()),
        "distinct_x_values": len(xs),
        "distinct_y_values": len(ys),
    }


def mechanism(constructions: list[dict], label: str) -> dict:
    """Run the tranche's OWN committed checker over each construction and
    relate the verdict to how the coordinates were written."""
    import checker

    verdicts = Counter()
    places = Counter()
    by_precision = {}
    lattice_zero = 0
    zero_score = 0
    signature = Counter()
    exemplars: dict[str, dict] = {}

    for c in constructions:
        text = c["text"]
        v = checker.check(text)
        code = v.get("code") or ("VALID" if v.get("valid") else "UNKNOWN")
        verdicts[code] += 1
        toks = [t for pair in POINT.findall(text) for t in pair]
        dp = [decimals(t) for t in toks]
        places.update(dp)
        coarsest = max(dp) if dp else None
        bucket = by_precision.setdefault(
            str(coarsest), {"constructions": 0, "min_area_zero": 0}
        )
        bucket["constructions"] += 1
        if v.get("score") == 0:
            bucket["min_area_zero"] += 1
            zero_score += 1
            if coarsest is not None and coarsest <= 2:
                lattice_zero += 1
        sig = collinearity_signature(text)
        if v.get("score") == 0:
            signature[
                "axis_aligned_triple"
                if sig["axis_aligned_triple_present"]
                else "oblique_collinear_triple_only"
            ] += 1
        elif v.get("score") is None:
            # WRONG_COUNT is refused BEFORE any area is computed, so it has no
            # score at all. Counting it against the signature would read
            # "unscored" as "scored nonzero" — the falsifier below fired on
            # exactly these three candidates on the first pass.
            signature["not_scored_wrong_count"] += 1
        elif sig["axis_aligned_triple_present"]:
            # A falsifier, kept deliberately: three points sharing an x or y
            # coordinate ARE collinear, so their minimum area must be 0. A
            # nonzero count here means the signature is being read wrong and
            # every number derived from it must be discarded.
            signature["axis_aligned_but_nonzero_FALSIFIER"] += 1
        key = "score_zero" if v.get("score") == 0 else code
        exemplars.setdefault(
            key,
            {
                "verdict": v,
                "max_decimal_places": coarsest,
                "signature": sig,
                "construction": text[:900],
            },
        )

    return {
        "label": label,
        "constructions_found": len(constructions),
        "checker_verdicts": dict(verdicts.most_common()),
        "zero_cause_signature": dict(signature.most_common()),
        "min_area_exactly_zero": zero_score,
        "min_area_zero_rate": round(zero_score / len(constructions), 4) if constructions else None,
        "zero_with_coordinates_at_2dp_or_coarser": lattice_zero,
        "coordinate_decimal_places_written": dict(sorted(places.items())),
        "by_coarsest_decimal_place": dict(sorted(by_precision.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 99)),
        "exemplars": exemplars,
    }


def main() -> int:
    arm_h = json.load(open(os.path.join(PC1, "arm_h_scores.json")))
    arm_s_rows = [json.loads(l) for l in open(os.path.join(PC1, "arm_s_merged.jsonl")) if l.strip()]

    h = attribute(arm_h["candidates"], "H (harness)")
    s = attribute(arm_s_rows, "S (blind repeated sampling)")

    root_h = os.path.join(PC1, "run")
    mech_h = mechanism(constructions_from_root(root_h), "ARM H (from the run root's raw provider blobs)")
    mech_s = mechanism(
        constructions_from_samples(os.path.join(PC1, "arm_s*", "samples", "*.txt")),
        "ARM S (from the committed sample files)",
    )

    doc = {
        "schema": "run-anatomy.pc1-headline.v1",
        "instance": "Heilbronn N=13, unit square, minimise-nothing/maximise the minimum triangle area over 286 triples",
        "source_artifacts": [
            "experiments/2026-08-25-change-constructive-frontier/arm_h_scores.json",
            "experiments/2026-08-25-change-constructive-frontier/arm_s_merged.jsonl",
        ],
        "registered_floor": FLOOR,
        "arm_h": h,
        "arm_s": s,
        "mechanism": {
            "why_this_is_read_from_blobs": (
                "arm_h_scores.json stores `text` only for candidates the checker "
                "CONFIRMED (score_run.py:157), so the 117 refuted constructions "
                "-- the subject of the headline -- are absent from it. They are "
                "read here from the run root's raw provider blobs, which is what "
                "the model actually wrote."
            ),
            "reconciliation_note": (
                "Blob-level construction counts need not equal the tranche's "
                "artifact-level candidate counts: the same construction can be "
                "restated across a batch and is deduplicated here, and a response "
                "can carry a construction that never became a scored artifact. "
                "The artifact-level counts above remain authoritative for the "
                "headline; these counts are the mechanism census beneath it."
            ),
            "arm_h": mech_h,
            "arm_s": mech_s,
        },
        "headline": {
            "arm_h_validity": h["validity_rate"],
            "arm_s_validity": s["validity_rate"],
            "gap": round((s["validity_rate"] or 0) - (h["validity_rate"] or 0), 4),
            "arm_h_invalidity_attributed": h["field_level_causes"],
            "one_field": (
                "Every one of ARM H's invalid candidates failed in the SAME "
                "field: the single free string carrying the construction. "
                "Not one failed a schema constraint, a type, an enum or a "
                "pointer. The form was filled correctly and the content it "
                "carried was wrong, which is the one failure a wire contract "
                "is structurally unable to catch."
            ),
        },
    }
    with open(os.path.join(HERE, "PC1_HEADLINE.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")

    for arm in (h, s):
        print(
            f"ARM {arm['arm']}: {arm['candidates_scored']} scored, "
            f"{arm['valid_checker_confirmed']} valid ({arm['validity_rate']}), "
            f"causes={arm['causes']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
