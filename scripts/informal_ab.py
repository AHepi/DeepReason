#!/usr/bin/env python
"""Informal-domain A/B (experiments/informal_ab_prereg.yaml): full harness
vs raw generation at matched budget, scored blind by the calibrated judge
ensemble (pairwise + order swap + mandatory decisive_point).

  --solo   generate the solo arm (candidates to ~60k tokens + self-pick 3)
  --score  score harness top-3 vs solo top-3 (run after both arms exist)
  --score-instrument  rescore the SAME committed pairs with the harness-
           designed instrument (prereg amendment 2: criterion-level forced
           choice, calibrated seats, verbosity penalty, degraded control
           pair gating instrument validity)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # for live_run import

from pydantic import BaseModel, Field  # noqa: E402

from deepreason.harness import Harness  # noqa: E402
from deepreason.informal.skeleton import parse_skeleton  # noqa: E402
from deepreason.llm.adapter import LLMAdapter, SchemaRepairError  # noqa: E402
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter  # noqa: E402
from deepreason.llm.contracts import ConjecturerOutput, PairwiseRuling  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason.ontology import Status  # noqa: E402
from deepreason.storage.blobs import BlobStore  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SOLO_OUT = ROOT / "experiments" / "results" / "informal_ab_solo.json"
REPORT = ROOT / "experiments" / "results" / "informal_ab_report.json"

def _problem_and_rubric():
    """Seed the republic suite into a throwaway root and read back the
    problem description and std-hist rubric — bytes-identical to what the
    harness arm sees."""
    import tempfile

    from live_run import seed_republic
    from deepreason.informal.standards import resolve_standard, standard_body

    with tempfile.TemporaryDirectory() as td:
        h = Harness(Path(td) / "seed")
        seed_republic(h)
        problem = h.state.problems["pi-republic"]
        body = standard_body(h, resolve_standard(h, "std-hist"))
        return problem.description, body["rubric"]


class SelectOut(BaseModel):
    picks: list[int] = Field(min_length=1, max_length=3)


def run_solo(api_key: str, base_url: str, budget: int) -> int:
    description, rubric = _problem_and_rubric()
    gen = OpenAICompatEndpoint(base_url, "deepseek-v4-pro", api_key=api_key,
                               temperature=1.0, max_tokens=4000, json_mode=True,
                               reasoning="none")
    meter = TokenMeter(budget=budget)
    adapter = LLMAdapter({"conjecturer": gen, "judge": gen}, BlobStore(Path("runs/ab_solo_blobs")),
                         retry_max=2, meter=meter)
    pack = (f"PROBLEM: {description}\n\nSTANDARD std-hist (your work will be "
            f"judged against it):\n{rubric}")
    candidates: list[str] = []
    try:
        while meter.total < budget - 8_000:  # reserve room for self-selection
            out, _ = adapter.call("conjecturer", pack, ConjecturerOutput)
            candidates += [c.content for c in out.candidates]
            print(f"solo: {len(candidates)} candidates | spent {meter.total}", flush=True)
    except (TokenBudgetExceeded, SchemaRepairError, EndpointError) as e:
        print(f"solo generation stopped: {e}")
    skeletons = [c for c in candidates if parse_skeleton(c) is not None]
    pool = skeletons or candidates
    listing = "\n\n".join(f"CANDIDATE {i}:\n{c[:1500]}" for i, c in enumerate(pool))
    try:
        sel, _ = adapter.call(
            "judge",
            f"{pack}\n\nYou produced these candidates:\n{listing}\n\n"
            "QUESTION: pick the indices of your best 3 candidates, best first.",
            SelectOut,
        )
        picks = [i for i in sel.picks if 0 <= i < len(pool)][:3]
    except (TokenBudgetExceeded, SchemaRepairError, EndpointError) as e:
        print(f"self-selection failed ({e}); falling back to first 3")
        picks = list(range(min(3, len(pool))))
    top = [pool[i] for i in picks] or pool[:3]
    SOLO_OUT.write_text(json.dumps(
        {"n_candidates": len(candidates), "n_skeletons": len(skeletons),
         "picks": picks, "top3": top, "tokens": meter.snapshot()}, indent=2))
    print(f"solo arm done: {len(candidates)} candidates, top3 saved, "
          f"spent {meter.total}")
    return 0


def _harness_top3(root: Path) -> list[str]:
    from deepreason.programs import content_text

    h = Harness(root)
    addressed = {a for a, p in h.state.addr if p == "pi-republic"}
    survivors = [a for a in addressed if h.state.status.get(a) == Status.ACCEPTED]
    scored = []
    for aid in survivors:
        text = content_text(h.state.artifacts[aid], h.blobs)
        if parse_skeleton(text) is None:
            continue
        seq = h.state.artifacts[aid].provenance.event_seq or 0
        scored.append((-(h.state.hv.get(aid, 0.0)), seq, text))
    scored.sort()
    return [t for _, _, t in scored[:3]]


def run_score(api_key: str, base_url: str, crossfamily: bool = False) -> int:
    _, rubric = _problem_and_rubric()
    solo = json.loads(SOLO_OUT.read_text())
    harness_top = _harness_top3(Path("runs/ab_harness"))
    solo_top = solo["top3"]
    n_pairs = min(len(harness_top), len(solo_top))
    if n_pairs == 0:
        print("an arm produced no skeletons — recording inconclusive")
        REPORT.write_text(json.dumps({"outcome": "inconclusive",
                                      "reason": "empty arm",
                                      "harness_n": len(harness_top),
                                      "solo_n": len(solo_top)}, indent=2))
        return 0

    seats = {
        "pro/off": OpenAICompatEndpoint(base_url, "deepseek-v4-pro", api_key=api_key,
                                        temperature=0.0, max_tokens=2400,
                                        json_mode=True, reasoning="none"),
        "flash/default": OpenAICompatEndpoint(base_url, "deepseek-v4-flash",
                                              api_key=api_key, temperature=0.0,
                                              max_tokens=2400, json_mode=True),
    }
    if crossfamily:
        # §9 cross-family seat (calibrated: planted-flaw 0.0, verbosity 0.25).
        poolside_key = os.environ["POOLSIDE_API_KEY"]
        seats["laguna-m.1/default"] = OpenAICompatEndpoint(
            "https://inference.poolside.ai/v1", "poolside/laguna-m.1",
            api_key=poolside_key, temperature=0.0, max_tokens=2400, json_mode=True,
        )
    meter = TokenMeter(budget=40_000 if crossfamily else 25_000)
    pairs = []
    try:
        for rank in range(n_pairs):
            h_text, s_text = harness_top[rank], solo_top[rank]
            votes = {}
            for seat_name, endpoint in seats.items():
                adapter = LLMAdapter({"judge": endpoint}, BlobStore(Path("runs/ab_solo_blobs")),
                                     retry_max=2, meter=meter)

                def rule(first, second):
                    pack = (
                        f"STANDARD std-hist:\n{rubric}\n\n"
                        f"A:\n{first}\n\nB:\n{second}\n\n"
                        "QUESTION: which candidate better satisfies the "
                        "standard, judged on content only? winner=neither if "
                        "you cannot discriminate. decisive_point MUST quote a "
                        "span of a candidate."
                    )
                    ruling, _ = adapter.call("judge", pack, PairwiseRuling)
                    return ruling.winner

                try:
                    r1 = rule(h_text, s_text)   # harness is A
                    r2 = rule(s_text, h_text)   # swapped: harness is B
                except (SchemaRepairError, EndpointError) as e:
                    # A seat that errors abstains; it must not kill the panel.
                    votes[seat_name] = {"orders": None, "vote": None,
                                        "error": str(e)[:120]}
                    continue
                consistent = (r1, r2) in (("A", "B"), ("B", "A"))
                vote = None
                if consistent:
                    vote = "harness" if r1 == "A" else "solo"
                votes[seat_name] = {"orders": [r1, r2], "vote": vote}
            net = sum(1 if v["vote"] == "harness" else -1 if v["vote"] == "solo" else 0
                      for v in votes.values())
            pairs.append({"rank": rank, "votes": votes, "net": net,
                          "outcome": "harness" if net > 0 else "solo" if net < 0 else "tie"})
            print(f"pair {rank}: {pairs[-1]['outcome']} ({votes})", flush=True)
    except (TokenBudgetExceeded, SchemaRepairError, EndpointError) as e:
        print(f"scoring stopped early: {e}")

    wins = {"harness": sum(p["outcome"] == "harness" for p in pairs),
            "solo": sum(p["outcome"] == "solo" for p in pairs),
            "tie": sum(p["outcome"] == "tie" for p in pairs)}
    outcome = ("harness_wins" if wins["harness"] >= 2
               else "solo_wins" if wins["solo"] >= 2 else "inconclusive")
    out_path = (REPORT.with_name("informal_ab_crossfamily_report.json")
                if crossfamily else REPORT)
    out_path.write_text(json.dumps(
        {"experiment": "informal-ab (experiments/informal_ab_prereg.yaml)",
         "outcome": outcome, "pair_wins": wins, "pairs": pairs,
         "harness_top3": harness_top, "solo_top3": solo_top,
         "solo_meta": {k: solo[k] for k in ("n_candidates", "n_skeletons", "tokens")},
         "scoring_tokens": meter.snapshot()}, indent=2))
    print(f"\nOUTCOME: {outcome}  {wins}")
    return 0


# ---------------------------------------------------------------------
# Instrument stage (prereg AMENDMENT 2): design aac313a1af55 from
# instrument_designs.json — produced by the unrefereed pro drive on
# pi-instrument. Criterion-level forced choice replaces holistic winner-
# picking (the measured saturation mode); a deterministically degraded
# control pair gates instrument validity.

INSTRUMENT_REPORT = ROOT / "experiments" / "results" / "informal_ab_instrument_report.json"

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


class CriterionChoices(BaseModel):
    """One forced choice per fixed criterion — completeness is schema-
    enforced, so a seat cannot skip the criteria it finds hard."""

    mechanism_specificity: Literal["A", "B", "tie"]
    falsifiability: Literal["A", "B", "tie"]
    scope_discipline: Literal["A", "B", "tie"]
    internal_coherence: Literal["A", "B", "tie"]
    evidential_grounding: Literal["A", "B", "tie"]


def _degrade(text: str) -> str:
    """The control pair's constructed-worse artifact: truncated to 55% of
    characters + an appended unfalsifiability sentence violating the
    rubric. Deterministic, so the control is replayable."""
    return text[: int(len(text) * 0.55)] + DEGRADE_SENTENCE


def _verbosity_penalty(len_a: int, len_b: int) -> float:
    lo, hi = min(len_a, len_b), max(len_a, len_b)
    if lo == 0 or lo == hi:
        return 0.0
    return min(0.3, 0.1 * (hi / lo - 1))


def run_score_instrument(api_key: str, base_url: str) -> int:
    _, rubric = _problem_and_rubric()
    committed = json.loads(REPORT.read_text())
    harness_top = committed["harness_top3"]
    solo_top = committed["solo_top3"]

    # pairs: (label, X, Y) where X is the harness-slot side; positive
    # margins favor X. Control: X = undegraded, Y = degraded.
    pairs = [(f"rank{r}", harness_top[r], solo_top[r])
             for r in range(min(len(harness_top), len(solo_top)))]
    pairs.append(("control", solo_top[0], _degrade(solo_top[0])))

    seats = {
        "pro/off": OpenAICompatEndpoint(base_url, "deepseek-v4-pro", api_key=api_key,
                                        temperature=0.0, max_tokens=2400,
                                        json_mode=True, reasoning="none"),
        "flash/default": OpenAICompatEndpoint(base_url, "deepseek-v4-flash",
                                              api_key=api_key, temperature=0.0,
                                              max_tokens=2400, json_mode=True),
        "laguna-m.1/default": OpenAICompatEndpoint(
            "https://inference.poolside.ai/v1", "poolside/laguna-m.1",
            api_key=os.environ["POOLSIDE_API_KEY"], temperature=0.0,
            max_tokens=2400, json_mode=True),
    }
    criteria_block = "\n".join(
        f"- {name}: {desc}" for name, desc in CRITERIA)
    meter = TokenMeter(budget=45_000)
    blobs = BlobStore(Path("runs/ab_solo_blobs"))

    def judge_once(adapter, first: str, second: str) -> dict[str, str]:
        pack = (
            f"STANDARD std-hist (both candidates answer the same problem "
            f"and will be judged against it):\n{rubric}\n\n"
            f"CRITERIA (each decomposes the standard):\n{criteria_block}\n\n"
            f"CANDIDATE A:\n{first}\n\nCANDIDATE B:\n{second}\n\n"
            "QUESTION: for EACH criterion separately, which candidate "
            "better satisfies THAT criterion alone, judged on content "
            "only? Answer A, B, or tie per criterion. Do NOT pick an "
            "overall winner; judge each criterion on its own."
        )
        out, _ = adapter.call("judge", pack, CriterionChoices)
        return {name: getattr(out, name) for name, _ in CRITERIA}

    def rel(choice: str, x_is: str) -> int:
        # +1 when the harness-slot side X wins the criterion.
        if choice == "tie":
            return 0
        return 1 if choice == x_is else -1

    results = []
    try:
        for label, x_text, y_text in pairs:
            penalty = _verbosity_penalty(len(x_text), len(y_text))
            x_longer = len(x_text) > len(y_text)
            seat_rows = {}
            for seat_name, endpoint in seats.items():
                adapter = LLMAdapter({"judge": endpoint}, blobs,
                                     retry_max=2, meter=meter)
                try:
                    c1 = judge_once(adapter, x_text, y_text)  # X is A
                    c2 = judge_once(adapter, y_text, x_text)  # X is B
                except (SchemaRepairError, EndpointError) as e:
                    seat_rows[seat_name] = {"score": None,
                                            "error": str(e)[:120]}
                    continue
                rel1 = {k: rel(v, "A") for k, v in c1.items()}
                rel2 = {k: rel(v, "B") for k, v in c2.items()}
                disagree = sum(rel1[k] != rel2[k] for k in rel1) / len(rel1)
                raw = (sum(rel1.values()) + sum(rel2.values())) / (2 * len(rel1))
                # Verbosity handicap: shift the longer artifact's margin
                # toward the shorter one (amendment 2 formula), clamped.
                adj = raw - penalty if x_longer else raw + penalty
                adj = max(-1.0, min(1.0, adj))
                seat_rows[seat_name] = {
                    "orders": [c1, c2], "raw": round(raw, 4),
                    "adjusted": round(adj, 4),
                    "order_disagreement": round(disagree, 4)}
            scores = [r["adjusted"] for r in seat_rows.values()
                      if r.get("adjusted") is not None]
            margin = sum(scores) / len(scores) if scores else None
            point = ("abstain" if margin is None
                     else "harness" if margin > 0.15
                     else "solo" if margin < -0.15 else "tie")
            results.append({"pair": label, "len_x": len(x_text),
                            "len_y": len(y_text),
                            "verbosity_penalty": round(penalty, 4),
                            "penalized_side": "X" if x_longer else "Y",
                            "seats": seat_rows,
                            "margin": None if margin is None else round(margin, 4),
                            "point": point})
            print(f"pair {label}: margin={margin} -> {point} "
                  f"(spent {meter.total})", flush=True)
    except TokenBudgetExceeded as e:
        print(f"instrument scoring stopped early: {e}")

    real = [r for r in results if r["pair"] != "control"]
    control = next((r for r in results if r["pair"] == "control"), None)
    points = {"harness": sum(r["point"] == "harness" for r in real),
              "solo": sum(r["point"] == "solo" for r in real),
              "tie": sum(r["point"] == "tie" for r in real)}
    outcome = ("harness_wins" if points["harness"] >= 2
               else "solo_wins" if points["solo"] >= 2 else "inconclusive")
    gate_pass = bool(control and control["margin"] is not None
                     and control["margin"] >= 0.2)
    disagreements = [s["order_disagreement"] for r in results
                     for s in r["seats"].values()
                     if s.get("order_disagreement") is not None]
    INSTRUMENT_REPORT.write_text(json.dumps(
        {"experiment": "informal-ab instrument stage "
                       "(prereg amendment 2, design aac313a1af55)",
         "instrument_valid": gate_pass,
         "control_pair": control,
         "verdict": outcome if gate_pass else "instrument_failed_control_gate",
         "ab_outcome_if_valid": outcome,
         "pair_points": points,
         "mean_order_disagreement": (round(sum(disagreements) / len(disagreements), 4)
                                     if disagreements else None),
         "pairs": results,
         "scoring_tokens": meter.snapshot()}, indent=2))
    print(f"\nCONTROL GATE: {'PASS' if gate_pass else 'FAIL'} "
          f"(margin={control['margin'] if control else None}, need >= +0.2)")
    print(f"VERDICT: {outcome if gate_pass else 'instrument_failed_control_gate'}"
          f"  points={points}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--score-instrument", action="store_true",
                        help="prereg amendment 2: criterion-level instrument")
    parser.add_argument("--crossfamily", action="store_true",
                        help="add the calibrated poolside seat (POOLSIDE_API_KEY)")
    parser.add_argument("--budget", type=int, default=65_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1
    if args.solo:
        return run_solo(api_key, args.base_url, args.budget)
    if args.score:
        return run_score(api_key, args.base_url, crossfamily=args.crossfamily)
    if args.score_instrument:
        return run_score_instrument(api_key, args.base_url)
    print("pass --solo, --score, or --score-instrument", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
