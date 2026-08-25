#!/usr/bin/env python3
"""Decide P-C1's registered milestones from typed outcomes and checker output.

PREREG.md §6 registered three milestones before launch. This instrument
reads them out of the record and the checker and nothing else. It forms no
opinion either source does not carry (REQUEST.md R4).

  M1  best valid checker-confirmed score, per arm        REQUIRED (ARM H >= 1 valid)
  M2  count of checker-refuted claims                    REQUIRED (>= 1)
  M3  a construction PATTERN that transfers              REPORTED, NOT SCORED

WHERE EACH VERDICT COMES FROM.

  M1  `score_run.py`'s exact-rational scoring of ARM H's artifacts, and
      `arm_s/summary.json` for ARM S. Both use the SAME `checker.py`, which
      is what makes the two numbers comparable at all.
  M2  the same scoring pass, split three ways -- structurally invalid,
      inflated claim, and valid-but-below-floor. The split matters: an
      invalid construction broke the rules, a below-floor one obeyed them
      and lost, and conflating them would overstate how much rule-breaking
      the criticism caught.
  M3  a mechanical census of recurring construction vocabulary across
      VALID candidates. This is deliberately weak and is REPORTED, NOT
      SCORED (R24c): naming a pattern is not evidence that the pattern did
      any work, and no threshold is attached to it. It exists so a reader
      can see what the run talked about, not so the run can pass something.

SURVIVOR COUNTS ARE CONJECTURE-ONLY (R31): the raw figure inflates with
import-role admission records (poietics P4, parked). Both are printed and
the raw one is labelled.

Exit 0 when M1 and M2 hold; 1 otherwise. That code is NOT the tranche's
verdict -- PREREG.md §5 is -- but a non-zero exit means a REQUIRED
milestone is unmet and RESULTS.md must record a negative.

Usage:  python milestone_census.py [arm_h_scores.json] [arm_s/summary.json]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Construction vocabulary. Each entry is a family of spellings for ONE idea,
# so a candidate saying "concentric rings" and one saying "two shells" count
# as the same pattern rather than two.
PATTERN_TERMS = {
    "avoid-collinearity": ("collinear", "colinear", "straight line", "degenerate", "three in a row"),
    "rings-or-shells": ("ring", "shell", "concentric", "annul", "circle of"),
    "perturbed-lattice": ("lattice", "grid", "perturb", "jitter", "offset row"),
    "boundary-loading": ("boundary", "edge of the square", "corner", "perimeter"),
    "golden-or-irrational": ("golden", "irrational", "phi", "fibonacci", "sunflower", "spiral"),
    "greedy-or-local": ("greedy", "local search", "hill", "refine", "iterate", "nudge"),
    "symmetry-breaking": ("symmetry break", "break the symmetry", "asymmetr", "tilt", "rotate slightly"),
    "min-triangle-targeting": ("smallest triangle", "binding triple", "critical triple", "worst triple"),
}


def _load(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def census(h: dict, s: dict) -> dict:
    candidates = h.get("candidates") or []
    valid = [c for c in candidates if c.get("valid")]

    best_h = h.get("best_score")
    best_s = s.get("best_score")

    # ---- M1 -------------------------------------------------------------
    m1 = {
        "milestone": "M1 best valid checker-confirmed score, per arm",
        "required": True,
        "arm_h_best": best_h,
        "arm_h_best_exact": h.get("best_score_exact"),
        "arm_h_valid_count": h.get("n_valid"),
        "arm_s_best": best_s,
        "arm_s_best_exact": s.get("best_score_exact"),
        "arm_s_valid_count": s.get("n_valid"),
        # REQUIRED is on ARM H producing a valid construction at all. A run
        # with none says nothing about either hypothesis.
        "met": bool(h.get("n_valid")),
    }

    # ---- M2 -------------------------------------------------------------
    by_code = h.get("refutations_by_code") or {}
    m2 = {
        "milestone": "M2 checker-refuted claims (criticism doing countable work)",
        "required": True,
        "total_refuted": h.get("n_refuted"),
        "structurally_invalid": sum(
            v for k, v in by_code.items()
            if k in ("WRONG_COUNT", "OUT_OF_SQUARE", "DUPLICATE_POINT", "NO_CLAIM")
        ),
        "claim_inflated": by_code.get("CLAIM_INFLATED", 0),
        "valid_but_below_floor": h.get("n_below_floor"),
        "by_code": by_code,
        "met": bool(h.get("n_refuted")),
    }

    # ---- M3 -------------------------------------------------------------
    hits: dict[str, int] = {}
    for name, terms in PATTERN_TERMS.items():
        hits[name] = sum(
            1
            for c in valid
            if any(t in (c.get("text") or "").lower() for t in terms)
        )
    m3 = {
        "milestone": "M3 a construction pattern that transfers across candidates",
        "required": False,
        "scored": False,
        "note": (
            "REPORTED, NOT SCORED (R24c). Naming a pattern is not evidence "
            "the pattern did any work. No threshold is attached."
        ),
        "valid_candidates_examined": len(valid),
        "pattern_mentions": hits,
        "text_available": any(c.get("text") for c in valid),
    }

    # ---- the margin (PREREG §5) ------------------------------------------
    margin = None
    if best_h is not None and best_s is not None:
        margin = best_h - best_s
    t_h, t_s = h.get("tokens_spent"), s.get("tokens_spent")
    matched = None
    if t_h and t_s:
        matched = t_s >= 0.95 * t_h

    return {
        "M1": m1,
        "M2": m2,
        "M3": m3,
        "margin": {
            "arm_h_best": best_h,
            "arm_s_best": best_s,
            "margin_h_minus_s": margin,
            # PREREG §5: value is claimed ONLY on best_H > best_S. Equality
            # is not a margin.
            "harness_claims_value": bool(
                margin is not None and margin > 0
            ),
            "arm_h_tokens": t_h,
            "arm_s_tokens": t_s,
            "budget_matched_per_S9": matched,
            "comparison_admissible": bool(matched),
        },
        "survivors_raw_INFLATED_see_P4": h.get("survivors_raw_INFLATED_see_P4"),
        "survivors_generative_only": h.get("survivors_generative_only"),
        "run_state": h.get("state"),
        "run_stop_reason": h.get("stop_reason"),
    }


def main() -> int:
    h = _load(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "arm_h_scores.json"))
    s = _load(pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else HERE / "arm_s" / "summary.json"))
    report = census(h, s)
    (HERE / "milestones.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    unmet = [k for k in ("M1", "M2") if not report[k]["met"]]
    if unmet:
        print(f"\nREQUIRED milestone(s) UNMET: {', '.join(unmet)}", file=sys.stderr)
        return 1
    print("\nM1 and M2 met; M3 reported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
