"""W1 — the coercion probe: what a seat does when the form forbids a hedge.

`docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md` records PhantomFill's
finding and its recommendation 2: "Add `insufficient_evidence` to every enum,
and then measure whether your seats take it." That measurement had never been
run on our own record. This runs it.

Three questions, all code-scorable, no judge:

1. WHICH of our required closed-vocabulary fields offer an escape value at
   all, and where one exists, how often is it taken? (EUR — Escape
   Utilization Rate.)
2. Where NO escape exists, does the hedge appear in the free string beside
   the forced field? That is the refusal tax paid where the form permits it,
   and it is measurable as the joint distribution of the forced field against
   hedge markers in its sibling prose.
3. Where the record itself STATED that omission was legal at a reference
   field, did the seat omit, or invent a value? (CFR — Coerced Fabrication
   Rate, on the one site where absence is the ground truth by construction.)

Reads only the per-root census output plus each root's raw response blobs.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import census as C  # noqa: E402

# Escape-shaped values: a vocabulary entry that means "I cannot answer this
# honestly" rather than naming an answer. Listed explicitly so the EUR number
# can be audited against the list that produced it.
ESCAPE_VALUES = {
    "unknown",
    "insufficient_evidence",
    "insufficient_data",
    "insufficient",
    "undetermined",
    "indeterminate",
    "not_applicable",
    "n/a",
    "none",
    "abstain",
    "no_verdict",
    "unclear",
    "need_context",
}


def load_census() -> list[dict]:
    d = os.path.join(HERE, "census")
    return [json.load(open(os.path.join(d, f))) for f in sorted(os.listdir(d)) if f.endswith(".json")]


def enum_escape_audit(agg: dict) -> dict:
    """Every enum-like field, and whether its observed vocabulary contains an
    escape value at all.

    HONEST LIMIT, stated where the number is: the vocabulary here is what the
    models WROTE, not what the contracts DECLARE. A field whose schema offers
    an escape no model ever chose looks identical to a field that offers none.
    So a field listed as `no_escape_value_observed` is a candidate for the
    coercion research's recommendation 2, not a proven forced choice — except
    where the contract is quoted alongside, as it is for the two below.
    """
    out = {}
    for field, vocab in agg["content"]["enum_like_fields"].items():
        total = sum(vocab.values())
        escapes = {k: v for k, v in vocab.items() if k.strip().lower() in ESCAPE_VALUES}
        out[field] = {
            "observations": total,
            "vocabulary": vocab,
            "escape_values_present": sorted(escapes),
            "escape_uses": sum(escapes.values()),
            "escape_utilization_rate": round(sum(escapes.values()) / total, 4) if total else None,
        }
    return out


def forced_field_vs_sibling_hedge(docs: list[dict]) -> dict:
    """Does the hedge move into the prose when the enum forbids one?

    `batch-critic.v2` requires a boolean `attack` per case and offers no third
    value. Beside it sits a free `case` string. If a seat that cannot say
    "I don't know" in the boolean says it in the prose instead, the joint
    distribution shows it: hedged prose under attack=true is an attack the
    seat's own words decline to make.
    """
    joint = Counter()
    breakdown = Counter()
    loose = Counter()
    exemplars: list[dict] = []
    false_positive_exemplars: list[dict] = []
    for d in docs:
        root = os.path.join(C.REPO, d["root"])
        for r in d["rows"]:
            if r["contract_id"] not in ("batch-critic.v2", "critic.atomic-target.v1"):
                continue
            if not r["valid_on_arrival"]:
                continue
            _, text = C.read_blob(root, r["raw_ref"])
            parsed, _ = C.parse_model_json(text)
            if not isinstance(parsed, dict):
                continue
            cases = parsed.get("cases")
            if cases is None and "attack" in parsed:
                cases = [parsed]
            if not isinstance(cases, list):
                continue
            for case in cases:
                if not isinstance(case, dict) or "attack" not in case:
                    continue
                attack = case.get("attack")
                prose = " ".join(
                    v for k, v in case.items() if isinstance(v, str) and k in ("case", "premise")
                )
                loose_hits = C.hedge_hits(prose)
                refusals = C.refusal_hits(prose)
                empty = not prose.strip()
                escape_token = (not empty) and prose.strip().lower() in ESCAPE_VALUES
                declined = bool(refusals) or escape_token or empty
                joint[(str(attack), declined)] += 1
                if attack is True:
                    if refusals:
                        breakdown["attack_true_self_referential_refusal"] += 1
                    elif escape_token:
                        breakdown["attack_true_case_is_escape_token"] += 1
                    elif empty:
                        breakdown["attack_true_case_empty"] += 1
                    else:
                        breakdown["attack_true_case_argued"] += 1
                if loose_hits:
                    loose[str(attack)] += 1
                if declined and attack is True and len(exemplars) < 25:
                    exemplars.append(
                        {
                            "root": d["root"],
                            "seq": r["seq"],
                            "model": r["model"],
                            "attack": attack,
                            "refusal_phrases": refusals,
                            "case_is_escape_token": escape_token,
                            "case_is_empty": empty,
                            "case": prose[:400],
                        }
                    )
                if loose_hits and not declined and len(false_positive_exemplars) < 6:
                    false_positive_exemplars.append(
                        {
                            "root": d["root"],
                            "seq": r["seq"],
                            "loose_markers": loose_hits,
                            "case": prose[:300],
                            "why_not_a_hedge": (
                                "the marker is the SUBSTANCE of the criticism "
                                "(the target provides no evidence / is unable to), "
                                "not the critic declining to make it"
                            ),
                        }
                    )
    total = sum(joint.values())
    attacked = sum(v for (a, _), v in joint.items() if a == "True")
    attacked_declined = joint.get(("True", True), 0)
    return {
        "cases_scored": total,
        "measure": (
            "A case counts as DECLINED only if its prose contains a phrase in "
            "which the SPEAKER declines (word-boundary matched) or the field is "
            "an escape token or empty. The loose hedge-marker list is reported "
            "separately and must not be read as a hedge rate."
        ),
        "joint_attack_x_declined_prose": {
            f"attack={a}, declined={h}": v for (a, h), v in joint.most_common()
        },
        "attacks_asserted": attacked,
        "attacks_whose_own_prose_declines": attacked_declined,
        "declined_attack_rate": round(attacked_declined / attacked, 4) if attacked else None,
        "attack_true_breakdown": dict(breakdown.most_common()),
        "note_on_attack_false": (
            "An attack=False case with empty prose is the CORRECT shape -- "
            "declining to attack needs no argument -- so the attack=False row "
            "of the joint table is not a finding. The finding is confined to "
            "attack=True."
        ),
        "loose_hedge_marker_hits_NOT_A_HEDGE_RATE": dict(loose.most_common()),
        "loose_marker_false_positive_exemplars": false_positive_exemplars,
        "exemplars": exemplars,
    }


def judge_form_filling(docs: list[dict]) -> dict:
    """How the judge seat filled its two-field form.

    `JudgeRuling` is `verdict` (enum: fail | pass) plus `decisive_point`
    (min_length 1). There is no third verdict, so a judge that cannot tell
    must still choose. This measures the choice and whether the prose beside
    it hedges — the same refusal-tax test, on the seat the operator has
    recorded standing suspicion of.
    """
    verdicts = Counter()
    hedged = Counter()
    lengths = Counter()
    exemplars: list[dict] = []
    for d in docs:
        root = os.path.join(C.REPO, d["root"])
        for r in d["rows"]:
            if r["contract_id"] != "judgeruling.direct.v1" or not r["valid_on_arrival"]:
                continue
            _, text = C.read_blob(root, r["raw_ref"])
            parsed, _ = C.parse_model_json(text)
            if not isinstance(parsed, dict):
                continue
            verdict = str(parsed.get("verdict"))
            point = parsed.get("decisive_point")
            verdicts[verdict] += 1
            if isinstance(point, str):
                lengths[min(len(point) // 50 * 50, 500)] += 1
                hits = C.refusal_hits(point)
                if hits:
                    hedged[verdict] += 1
                    if len(exemplars) < 15:
                        exemplars.append(
                            {
                                "root": d["root"],
                                "seq": r["seq"],
                                "model": r["model"],
                                "verdict": verdict,
                                "refusal_phrases": hits,
                                "decisive_point": point[:400],
                            }
                        )
    total = sum(verdicts.values())
    return {
        "rulings": total,
        "verdicts": dict(verdicts.most_common()),
        "no_third_verdict": "JudgeRuling declares enum [fail, pass]; there is no abstain value",
        "rulings_whose_decisive_point_declines": dict(hedged.most_common()),
        "declined_rate": round(sum(hedged.values()) / total, 4) if total else None,
        "decisive_point_length_buckets": dict(sorted(lengths.items())),
        "exemplars": exemplars,
    }


def main() -> int:
    docs = load_census()
    agg = json.load(open(os.path.join(HERE, "CENSUS_AGGREGATE.json")))

    doc = {
        "schema": "run-anatomy.coercion-probe.v1",
        "authority": "docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md recommendation 2",
        "escape_value_list": sorted(ESCAPE_VALUES),
        "hedge_marker_list_LOOSE_candidates_only": list(C.HEDGE_MARKERS),
        "self_referential_refusal_patterns": list(C.SELF_REFERENTIAL_REFUSAL),
        "enum_escape_audit": enum_escape_audit(agg),
        "coerced_fabrication": agg["coercion"],
        "forced_boolean_vs_sibling_prose": forced_field_vs_sibling_hedge(docs),
        "judge_form_filling": judge_form_filling(docs),
    }
    with open(os.path.join(HERE, "COERCION_PROBE.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")

    f = doc["forced_boolean_vs_sibling_prose"]
    j = doc["judge_form_filling"]
    print(f"critic cases scored: {f['cases_scored']}, attacks {f['attacks_asserted']}, "
          f"declined attacks {f['attacks_whose_own_prose_declines']} ({f['declined_attack_rate']})")
    print(f"judge rulings: {j['rulings']} {j['verdicts']}, declined {j['declined_rate']}")
    print(f"CFR: {doc['coerced_fabrication']['coerced_fabrication_rate']} "
          f"({doc['coerced_fabrication']['fabricated_handle']}/"
          f"{doc['coerced_fabrication']['escape_legal']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
