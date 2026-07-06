"""M3 — the calibrated instrument (MINI_PLAN §3.6; parent design aac313a1af55).

Offline tool, NOT in the loop: evaluation is a measurement you run ON a
finished log, never a step that gates registration. Naive pairwise judging
measured unusable (8/9 votes discarded to position bias); this instrument's
control gates measured +0.478/+0.909/+0.841 across three problems with
zero abstentions in 72 calls. Components, all measured: criterion-level
forced choice (schema-enforced completeness), both presentation orders,
verbosity penalty min(0.3, 0.1*(ratio-1)), a deterministically degraded
control pair gating instrument validity (margin >= +0.2 or the scoring run
is VOID), per-order disagreement reported.

Seat calibration is provider-specific: re-certify seats with the planted-
flaw battery (``certify_seat``) before trusting scores on a new deployment.
"""

from typing import Literal

from pydantic import BaseModel

from minireason import call as llm

CRITERIA = [
    ("mechanism_specificity",
     "names a concrete causal mechanism rather than gesturing at one"),
    ("falsifiability",
     "makes claims that identifiable evidence could in principle refute"),
    ("scope_discipline",
     "claims no more than its mechanism actually supports"),
    ("internal_coherence",
     "parts support each other; no internal contradiction"),
    ("evidential_grounding",
     "points to specific, checkable evidence for its claims"),
]

DEGRADE_SENTENCE = (
    " In conclusion, the true mechanism here is ultimately unknowable and "
    "no conceivable evidence could ever bear on this account."
)

MARGIN_POINT = 0.15   # |margin| above this scores a point for a side
CONTROL_GATE = 0.2    # control-pair margin below this voids the run


class CriterionChoices(BaseModel):
    """One forced choice per fixed criterion — a seat cannot skip the
    criteria it finds hard."""

    mechanism_specificity: Literal["A", "B", "tie"]
    falsifiability: Literal["A", "B", "tie"]
    scope_discipline: Literal["A", "B", "tie"]
    internal_coherence: Literal["A", "B", "tie"]
    evidential_grounding: Literal["A", "B", "tie"]


def degrade(text: str) -> str:
    """The control pair's constructed-worse artifact: truncate to 55% and
    append an unfalsifiability sentence. Deterministic, so replayable."""
    return text[: int(len(text) * 0.55)] + DEGRADE_SENTENCE


def verbosity_penalty(len_a: int, len_b: int) -> float:
    lo, hi = min(len_a, len_b), max(len_a, len_b)
    if lo == 0 or lo == hi:
        return 0.0
    return min(0.3, 0.1 * (hi / lo - 1))


def _rel(choice: str, x_is: str) -> int:
    # +1 when the X side (harness slot) wins the criterion.
    if choice == "tie":
        return 0
    return 1 if choice == x_is else -1


def score_orders(c1: dict, c2: dict, len_x: int, len_y: int) -> dict:
    """Pure scoring math over one seat's two orderings (X-as-A, X-as-B) —
    byte-compatible with the parent's committed instrument reports."""
    rel1 = {k: _rel(v, "A") for k, v in c1.items()}
    rel2 = {k: _rel(v, "B") for k, v in c2.items()}
    disagree = sum(rel1[k] != rel2[k] for k in rel1) / len(rel1)
    raw = (sum(rel1.values()) + sum(rel2.values())) / (2 * len(rel1))
    penalty = verbosity_penalty(len_x, len_y)
    adjusted = raw - penalty if len_x > len_y else raw + penalty
    adjusted = max(-1.0, min(1.0, adjusted))
    return {"raw": round(raw, 4), "adjusted": round(adjusted, 4),
            "order_disagreement": round(disagree, 4)}


def aggregate(seat_rows: dict[str, dict]) -> tuple[float | None, str]:
    """(margin, point) across seats; errored seats abstain."""
    scores = [r["adjusted"] for r in seat_rows.values() if r.get("adjusted") is not None]
    if not scores:
        return None, "abstain"
    margin = sum(scores) / len(scores)
    point = ("harness" if margin > MARGIN_POINT
             else "solo" if margin < -MARGIN_POINT else "tie")
    return round(margin, 4), point


def _judge_prompt(rubric: str, first: str, second: str) -> str:
    criteria_block = "\n".join(f"- {name}: {desc}" for name, desc in CRITERIA)
    return (
        f"STANDARD (both candidates answer the same problem and will be "
        f"judged against it):\n{rubric}\n\n"
        f"CRITERIA (each decomposes the standard):\n{criteria_block}\n\n"
        f"CANDIDATE A:\n{first}\n\nCANDIDATE B:\n{second}\n\n"
        "QUESTION: for EACH criterion separately, which candidate better "
        "satisfies THAT criterion alone, judged on content only? Answer A, "
        "B, or tie per criterion. Do NOT pick an overall winner; judge each "
        "criterion on its own."
    )


def score_pair(seats: dict[str, object], x_text: str, y_text: str, rubric: str,
               meter: llm.TokenMeter, blobs, retry_max: int = 2) -> dict:
    """Score one (X, Y) pair across seats, both presentation orders each."""
    seat_rows: dict[str, dict] = {}
    for seat_name, endpoint in seats.items():
        try:
            o1, _ = llm.call(endpoint, _judge_prompt(rubric, x_text, y_text),
                             CriterionChoices, meter, blobs, retry_max, role="judge")
            o2, _ = llm.call(endpoint, _judge_prompt(rubric, y_text, x_text),
                             CriterionChoices, meter, blobs, retry_max, role="judge")
        except (llm.SchemaError, llm.EndpointError) as e:
            seat_rows[seat_name] = {"score": None, "error": str(e)[:120]}
            continue  # a seat that errors abstains; it must not kill the panel
        c1, c2 = o1.model_dump(), o2.model_dump()
        seat_rows[seat_name] = {"orders": [c1, c2],
                                **score_orders(c1, c2, len(x_text), len(y_text))}
    margin, point = aggregate(seat_rows)
    return {"len_x": len(x_text), "len_y": len(y_text),
            "verbosity_penalty": round(verbosity_penalty(len(x_text), len(y_text)), 4),
            "penalized_side": "X" if len(x_text) > len(y_text) else "Y",
            "seats": seat_rows, "margin": margin, "point": point}


def score_run(seats: dict, pairs: list[tuple[str, str, str]], rubric: str,
              meter: llm.TokenMeter, blobs, retry_max: int = 2) -> dict:
    """Full scoring run: the given (label, X, Y) pairs plus the mandatory
    degraded control (X = undegraded first Y, Y = degraded). The control
    gate decides whether the scores mean anything at all."""
    rows = []
    for label, x_text, y_text in pairs:
        rows.append({"pair": label,
                     **score_pair(seats, x_text, y_text, rubric, meter, blobs, retry_max)})
    control_src = pairs[0][2]
    rows.append({"pair": "control",
                 **score_pair(seats, control_src, degrade(control_src), rubric,
                              meter, blobs, retry_max)})
    real = [r for r in rows if r["pair"] != "control"]
    control = rows[-1]
    points = {"harness": sum(r["point"] == "harness" for r in real),
              "solo": sum(r["point"] == "solo" for r in real),
              "tie": sum(r["point"] == "tie" for r in real)}
    outcome = ("harness_wins" if points["harness"] >= 2
               else "solo_wins" if points["solo"] >= 2 else "inconclusive")
    gate_pass = control["margin"] is not None and control["margin"] >= CONTROL_GATE
    disagreements = [s["order_disagreement"] for r in rows for s in r["seats"].values()
                     if s.get("order_disagreement") is not None]
    return {"instrument_valid": gate_pass, "control_pair": control,
            "verdict": outcome if gate_pass else "instrument_failed_control_gate",
            "ab_outcome_if_valid": outcome, "pair_points": points,
            "mean_order_disagreement": (round(sum(disagreements) / len(disagreements), 4)
                                        if disagreements else None),
            "pairs": rows, "scoring_tokens": meter.snapshot()}


# --- trimmed planted-flaw battery (MINI_PLAN §6 risk 2) ----------------------
# Ground truth by construction: new deployments re-certify seats before any
# score is trusted. Subset of the parent's 12+12 battery.

FLAW_RUBRIC = (
    "An argument violates this standard iff its stated reasoning contains a "
    "definite logical or factual error that undermines its conclusion: "
    "circular justification, equivocation, a formally invalid inference, a "
    "false premise, an unsupported causal leap, or a probability error. A "
    "valid argument with true premises does NOT violate the standard."
)

PLANTED = [  # (text, is_flawed)
    ("The Bible is true because it is the word of God, and we know it is the "
     "word of God because the Bible itself says so.", True),
    ("If it rains, the street gets wet. The street is wet. Therefore it rained.", True),
    ("A feather is light. Whatever is light cannot be dark. Therefore a "
     "feather cannot be dark.", True),
    ("Since 7 times 8 equals 54, and 54 is even, the product of 7 and 8 is even.", True),
    ("The rooster crows immediately before sunrise. Therefore the rooster's "
     "crowing causes the sun to rise.", True),
    ("The recipe needs 3 eggs per cake and we have 10 eggs, so we can bake 4 "
     "whole cakes.", True),
    ("All squares are rectangles. All rectangles are quadrilaterals. "
     "Therefore all squares are quadrilaterals.", False),
    ("7 times 8 equals 56, and 56 is even, so the product of 7 and 8 is even.", False),
    ("The key is either in the drawer or in the coat. It is not in the "
     "drawer. Therefore it is in the coat.", False),
    ("The recipe needs 3 eggs per cake and we have 10 eggs, so we can bake "
     "at most 3 whole cakes.", False),
    ("If the tank is empty, the engine stops. The tank is empty. Therefore "
     "the engine stops.", False),
    ("The angles of a triangle sum to 180 degrees. Two of them are 90 and "
     "60, so the third is 30 degrees.", False),
]


class FlawRuling(BaseModel):
    violates: bool


def certify_seat(endpoint, meter: llm.TokenMeter, blobs,
                 retry_max: int = 2, err_max: float = 0.25) -> dict:
    """Planted-flaw error rate for one seat; a seat above ``err_max`` must
    not judge anything. Errored items count as errors (abstention is not
    accuracy)."""
    errors = 0
    for text, is_flawed in PLANTED:
        prompt = (f"STANDARD:\n{FLAW_RUBRIC}\n\nARGUMENT:\n{text}\n\n"
                  "QUESTION: does the argument violate the standard?")
        try:
            ruling, _ = llm.call(endpoint, prompt, FlawRuling, meter, blobs,
                                 retry_max, role="judge")
            errors += int(ruling.violates != is_flawed)
        except (llm.SchemaError, llm.EndpointError):
            errors += 1
    rate = errors / len(PLANTED)
    return {"planted_flaw_error_rate": round(rate, 4), "n": len(PLANTED),
            "passes": rate <= err_max}
