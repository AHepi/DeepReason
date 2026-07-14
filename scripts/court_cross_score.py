"""Bronze court-cross v1 scorer (prereg + amendments 1-3).

Pure function of the checkpoints. P1: between-arm objection-rate spread
>= 25pp on the shared 85-item pool. P2: >= 30 percent of each arm's
objections dispute covers/excludes consistency rather than mechanism
substance (deterministic keyword rule, same lexicon as the interim check,
frozen with the pool). P3: seat-plus-order disagreement <= 0.15 per arm
(amendment 1 confound recorded).
"""
from __future__ import annotations

import json
from pathlib import Path

RUN = Path("experiments/court_cross_run")
OUT = Path("experiments/results/bronze_court_cross_v1_report.json")
ARMS = ["dsflash", "kimi", "mistral"]
SCOPE_KEYWORDS = ("scope", "covers", "excludes", "exclusion", "contradict")


def arm_stats(arm: str) -> dict:
    records = [json.loads(line) for line in open(RUN / f"arm_{arm}.jsonl")]
    n = len(records)
    objecting = [r for r in records if r.get("objects")]
    ruled = [r for r in objecting if r.get("rulings")]
    outcomes: dict[str, int] = {}
    for r in objecting:
        key = r.get("outcome") or "no_ruling"
        outcomes[key] = outcomes.get(key, 0) + 1
    disagreements = [r for r in ruled if r.get("seat_disagreement")]
    scope = sum(
        1 for r in objecting
        if r.get("objection")
        and any(k in r["objection"].lower() for k in SCOPE_KEYWORDS)
    )
    return {
        "n": n,
        "objections": len(objecting),
        "objection_rate": round(len(objecting) / n, 4),
        "outcomes": dict(sorted(outcomes.items())),
        "ruled": len(ruled),
        "seat_disagreement_rate": round(len(disagreements) / max(1, len(ruled)), 4),
        "scope_formalism_objections": scope,
        "scope_formalism_share": round(scope / max(1, len(objecting)), 4),
        "sustained": outcomes.get("sustain", 0),
    }


def main() -> None:
    arms = {arm: arm_stats(arm) for arm in ARMS}
    assert all(v["n"] == 85 for v in arms.values()), {a: v["n"] for a, v in arms.items()}
    rates = {a: v["objection_rate"] for a, v in arms.items()}
    spread_pp = round((max(rates.values()) - min(rates.values())) * 100, 2)
    p1 = spread_pp >= 25
    p2 = all(v["scope_formalism_share"] >= 0.30 for v in arms.values())
    p3 = all(v["seat_disagreement_rate"] <= 0.15 for v in arms.values())
    tokens = json.loads((RUN / "token_usage.json").read_text())
    report = {
        "schema": "deepreason-bronze-court-cross-v1",
        "prereg": "experiments/bronze_court_cross_v1_prereg.yaml",
        "pool": "experiments/court_cross_pool_v1.json (first 85 in frozen order, amendment 2)",
        "arms": arms,
        "verdicts": {
            "P1": "CONFIRMED" if p1 else "REFUTED",
            "P1_measured_spread_pp": spread_pp,
            "P2": "CONFIRMED" if p2 else "REFUTED",
            "P3": "CONFIRMED" if p3 else "REFUTED",
        },
        "tokens": {k: tokens[k] for k in ("prompt_tokens", "completion_tokens", "calls")
                   if k in tokens},
        "caveats": [
            "P3 measures seat-plus-order disagreement (amendment 1), not a pure order effect",
            "observe-only study: no status changed anywhere; verdict DISTRIBUTIONS are the outcome",
            "scope-formalism share uses a deterministic keyword rule; borderline objections not hand-adjudicated",
        ],
    }
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps(report["verdicts"], indent=1))
    print(json.dumps({a: {k: v[k] for k in (
        "objection_rate", "outcomes", "seat_disagreement_rate",
        "scope_formalism_share")} for a, v in arms.items()}, indent=1))


if __name__ == "__main__":
    main()
