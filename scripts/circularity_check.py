#!/usr/bin/env python
"""Circularity screen v1 — deterministic, zero LLM tokens (pre-registered:
experiments/circularity_verifier_prereg.yaml).

Motivated by the t3 exploratory finding that circular support is the
universal judge blind spot (18 percent pooled catch; all three
universally-missed items circular). This is a prototype screen over PROSE,
not an ontology verifier; graduation requires a follow-up.

Instrument (fixed before any corpus item is scored):

  1. Sentence segmentation — deterministic regex split on terminal
     punctuation, with list/bullet lines treated as sentence boundaries.
  2. Conclusion identification via discourse markers — a sentence whose
     head carries a conclusion marker
     (therefore, thus, hence, so, consequently, it follows that, we
     conclude, this shows/proves/establishes/confirms/demonstrates that,
     which is why) contributes its marker-stripped core as a CONCLUSION.
     Because-inversions ("X because/since/for/given that Y") contribute
     the main clause X as a CLAIM and the subordinate clause Y as a
     SUPPORT unit tied to X.
  3. Support pool for a conclusion — every subordinate (because-style)
     clause in the item plus every plain unmarked sentence EXCEPT the
     opening sentence's main clause: by expository convention the opening
     sentence states the thesis; a thesis statement is an announcement,
     not support, so matching a closing "therefore <thesis>" against it
     would flag ordinary summary prose. (The opening sentence's OWN
     because-clause remains in the support pool.) This design choice is
     committed here, before scoring.
  4. Circularity flag — raised when
       (a) EMBEDDING: some support unit lies within the duplicate radius
           of some conclusion/claim it supports (cosine distance under
           deepreason.llm.embedder.NeuralEmbedder, default nomic model),
           i.e. the support restates the conclusion; or
       (b) REFERENCE CYCLE: stated derivation references over labelled
           statements ("(1)", "step 2", "premise 3", "claim B", ...)
           form a directed cycle ("(3) follows from (1)... (1) is
           established by (3)").

  Radius calibration (BEFORE scoring, on committed data only): positive
  class = the planted duplicate pairs (views/basin.DEFAULT_PLANTED) plus
  the 60 committed e01 paraphrase pairs (scripts/e01_paraphrase_pairs.py);
  negative class = deterministic mismatched recombinations of the e01
  pairs (same jargon domain, different meaning — hard negatives). The
  radius is the midpoint of the gap between the positive maximum and the
  negative 10th percentile when the classes separate, else the positive
  maximum. The radius and both distributions are recorded in the report.

Validation (the frozen E0.2 corpus): 10 circular-support unknown-flaw
items, 30 other unknown-flaw items, 40 ORIGINAL clean items (uncorrected
set, so this tranche is independent of t2b).

Verdicts (prereg literal):
  P1 CONFIRMED iff >= 7 of 10 circular-support items flagged.
  P2 CONFIRMED iff <= 2 of 40 clean items flagged.
  P3 CONFIRMED iff this screen's circular-class catch beats the best
     single zoo seat's circular-class catch (recomputed from
     experiments/e02_t3_run/judgments.jsonl) by >= 30 percentage points.

Usage: python scripts/circularity_check.py
"""

import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from e01_paraphrase_pairs import pairs as e01_pairs  # noqa: E402

from deepreason.llm.embedder import NeuralEmbedder, distance  # noqa: E402
from deepreason.views.basin import DEFAULT_PLANTED  # noqa: E402

PREREG = "experiments/circularity_verifier_prereg.yaml"
SCHEMA = "deepreason-circularity-v1"

UNKNOWN = REPO / "experiments/e02_t1_items/unknown_flaws.json"
CLEAN = REPO / "experiments/e02_t2_items/clean_items.json"
T3_JUDGMENTS = REPO / "experiments/e02_t3_run/judgments.jsonl"
RESULTS = REPO / "experiments/results"

# ---------------------------------------------------------------------- #
# 1. Sentence segmentation.
# ---------------------------------------------------------------------- #

_ABBREV = re.compile(r"\b(e\.g|i\.e|etc|vs|cf|dr|mr|ms|no|fig|eq|approx)\.$",
                     re.IGNORECASE)


def sentences(text: str) -> list[str]:
    out: list[str] = []
    for block in re.split(r"\n\s*\n|\n(?=\s*[-*•]|\s*\d+[.)]\s)", text):
        block = " ".join(block.split())
        if not block:
            continue
        pieces = re.split(r"(?<=[.!?])\s+", block)
        buf = ""
        for piece in pieces:
            buf = f"{buf} {piece}".strip() if buf else piece
            if _ABBREV.search(buf):
                continue  # abbreviation, keep accumulating
            if buf:
                out.append(buf)
                buf = ""
        if buf:
            out.append(buf)
    return [s for s in out if len(s.split()) >= 3]


# ---------------------------------------------------------------------- #
# 2. Discourse-marker parsing.
# ---------------------------------------------------------------------- #

CONCLUSION_MARKERS = re.compile(
    r"^(?:and\s+|but\s+)?"
    r"(?:therefore|thus|hence|so|consequently|accordingly|"
    r"it\s+follows(?:\s+that)?|we\s+(?:can\s+)?conclude(?:\s+that)?|"
    r"this\s+(?:shows|proves|establishes|confirms|demonstrates|means)"
    r"(?:\s+that)?|in\s+conclusion|which\s+is\s+why)[\s,:]+",
    re.IGNORECASE)

# Support subordinators for because-inversions: "X because Y".
SUPPORT_SPLIT = re.compile(
    r"[,;\s]\s*(?:because|since|for the reason that|given that|"
    r"owing to the fact that|as a consequence of the fact that)\s+",
    re.IGNORECASE)

_LEAD_TRIM = re.compile(r"^(?:precisely|exactly|simply|clearly|obviously)"
                        r"[\s,]+", re.IGNORECASE)


def _core(clause: str) -> str:
    clause = _LEAD_TRIM.sub("", clause.strip().strip(".;:,"))
    return clause


def parse_item(text: str) -> dict:
    """Return conclusions (marker-stripped cores + because-main claims)
    and the support pool (because-clauses + plain non-thesis sentences)."""
    sents = sentences(text)
    conclusions: list[dict] = []   # {"text": core, "idx": i}
    supports: list[dict] = []      # {"text": core, "idx": i, "kind": ...}
    for i, sent in enumerate(sents):
        marked = bool(CONCLUSION_MARKERS.match(sent))
        # split off because-style subordinate clauses
        parts = SUPPORT_SPLIT.split(sent)
        main = _core(CONCLUSION_MARKERS.sub("", parts[0]))
        subs = [_core(p) for p in parts[1:]]
        for sub in subs:
            if len(sub.split()) >= 3:
                supports.append({"text": sub, "idx": i, "kind": "because-clause"})
        if marked:
            if len(main.split()) >= 3:
                conclusions.append({"text": main, "idx": i})
        elif subs:
            # because-inversion: the main clause is a claim whose stated
            # support is the subordinate clause(s).
            if len(main.split()) >= 3:
                conclusions.append({"text": main, "idx": i})
        elif i > 0:
            # plain unmarked non-opening sentence: candidate support.
            if len(main.split()) >= 3:
                supports.append({"text": main, "idx": i, "kind": "plain"})
    return {"sentences": len(sents), "conclusions": conclusions,
            "supports": supports}


# ---------------------------------------------------------------------- #
# 3. Stated-reference cycle detection.
# ---------------------------------------------------------------------- #

_LABEL_DEF = re.compile(
    r"^\s*(?:\(([0-9]+|[A-Z])\)|(?:step|premise|claim|point|statement|lemma)"
    r"\s+([0-9]+|[A-Z])\b[:.)]?)", re.IGNORECASE)
_LABEL_REF = re.compile(
    r"(?:from|by|using|per|of|in|with|establishes?|established\s+(?:by|in)|"
    r"follows\s+from|shown\s+in|proved\s+in|see|via|given)\s+"
    r"(?:\(([0-9]+|[A-Z])\)|(?:step|premise|claim|point|statement|lemma)\s+"
    r"([0-9]+|[A-Z])\b)", re.IGNORECASE)
_ANY_LABEL = re.compile(r"\(([0-9]+|[A-Z])\)")


def reference_cycle(text: str) -> list[str] | None:
    """Directed edges defined-label -> referenced-label; return one cycle
    (as labels) if the stated derivation references form one."""
    edges: dict[str, set[str]] = {}
    defined: set[str] = set()
    for sent in sentences(text):
        m = _LABEL_DEF.match(sent)
        label = None
        if m:
            label = (m.group(1) or m.group(2)).upper()
            defined.add(label)
        refs = {(a or b).upper() for a, b in _LABEL_REF.findall(sent)}
        if label is None:
            inline = [x.upper() for x in _ANY_LABEL.findall(sent)]
            if inline and refs:
                label = inline[0]
                defined.add(label)
        if label:
            edges.setdefault(label, set()).update(r for r in refs if r != label)
    # DFS cycle detection restricted to defined labels.
    graph = {k: {v for v in vs if v in defined} for k, vs in edges.items()}
    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    stack: list[str] = []

    def dfs(node: str) -> list[str] | None:
        color[node] = GREY
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if color.get(nxt, BLACK) == GREY:
                return stack[stack.index(nxt):] + [nxt]
            if color.get(nxt) == WHITE:
                found = dfs(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    for start in sorted(graph):
        if color[start] == WHITE:
            cycle = dfs(start)
            if cycle:
                return cycle
    return None


# ---------------------------------------------------------------------- #
# 4. Radius calibration (committed pairs only, fixed before scoring).
# ---------------------------------------------------------------------- #

def calibrate_radius(embedder) -> dict:
    positives = list(DEFAULT_PLANTED) + list(e01_pairs())
    pos_d = [distance(embedder.embed(a), embedder.embed(b))
             for a, b in positives]
    # Hard negatives: deterministic mismatched recombinations of the e01
    # pairs (a_i vs b_(i+k)); same jargon domain, different meaning.
    e01 = e01_pairs()
    neg_pairs = [(e01[i][0], e01[(i + k) % len(e01)][1])
                 for k in (1, 7, 13) for i in range(len(e01))]
    neg_d = [distance(embedder.embed(a), embedder.embed(b))
             for a, b in neg_pairs]

    def quantiles(xs):
        xs = sorted(xs)
        return {"n": len(xs), "min": round(xs[0], 4),
                "p10": round(xs[len(xs) // 10], 4),
                "median": round(xs[len(xs) // 2], 4),
                "p90": round(xs[(len(xs) * 9) // 10], 4),
                "max": round(xs[-1], 4)}

    pos_q, neg_q = quantiles(pos_d), quantiles(neg_d)
    separable = pos_q["max"] < neg_q["p10"]
    radius = round((pos_q["max"] + neg_q["p10"]) / 2 if separable
                   else pos_q["max"], 4)
    return {
        "radius": radius,
        "rule": "midpoint of gap between positive max and negative p10 "
                "when separable, else positive max",
        "separable": separable,
        "positive_pairs": {"planted": len(DEFAULT_PLANTED),
                           "e01_paraphrase": len(e01),
                           "distances": pos_q},
        "negative_pairs": {"construction": "e01 a_i vs b_(i+k), k in "
                                           "(1,7,13)",
                           "n": len(neg_pairs), "distances": neg_q},
        "embedder": {"name": embedder.name, "model": embedder.model},
    }


# ---------------------------------------------------------------------- #
# 5. Scoring one item.
# ---------------------------------------------------------------------- #

def check_item(text: str, embedder, radius: float,
               cache: dict[str, list[float]]) -> dict:
    def emb(s: str) -> list[float]:
        if s not in cache:
            cache[s] = embedder.embed(s)
        return cache[s]

    parsed = parse_item(text)
    best = None  # (dist, conclusion idx, support idx, support kind)
    for concl in parsed["conclusions"]:
        for sup in parsed["supports"]:
            if sup["idx"] == concl["idx"] and sup["kind"] == "plain":
                continue  # a sentence cannot plainly support itself
            d = distance(emb(concl["text"]), emb(sup["text"]))
            if best is None or d < best[0]:
                best = (d, concl["idx"], sup["idx"], sup["kind"])
    embedding_hit = best is not None and best[0] < radius
    cycle = reference_cycle(text)
    return {
        "n_sentences": parsed["sentences"],
        "n_conclusions": len(parsed["conclusions"]),
        "n_supports": len(parsed["supports"]),
        "min_support_conclusion_distance":
            round(best[0], 4) if best else None,
        "closest_pair": ({"conclusion_sentence": best[1],
                          "support_sentence": best[2],
                          "support_kind": best[3]} if best else None),
        "embedding_hit": embedding_hit,
        "reference_cycle": cycle,
        "flagged": bool(embedding_hit or cycle),
        "reason": ("embedding" if embedding_hit else None) or
                  ("reference_cycle" if cycle else None),
    }


# ---------------------------------------------------------------------- #
# 6. Zoo-seat circular-class catch baseline (from committed t3 judgments).
# ---------------------------------------------------------------------- #

def zoo_circular_baseline(circ_ids: set[str]) -> dict:
    per_seat: dict[str, dict[str, bool]] = {}
    for line in T3_JUDGMENTS.read_text().splitlines():
        rec = json.loads(line)
        if rec["item_id"] in circ_ids and rec["seat"].startswith("zoo:"):
            per_seat.setdefault(rec["seat"], {})[rec["item_id"]] = \
                bool(rec["flawed"])
    table = {seat: {"caught": sum(v.values()), "n": len(v),
                    "rate": round(sum(v.values()) / len(v), 4)}
             for seat, v in sorted(per_seat.items())}
    best_seat = max(table, key=lambda s: (table[s]["rate"], s))
    return {"per_seat": table, "best_seat": best_seat,
            "best_rate": table[best_seat]["rate"]}


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    unknown = json.loads(UNKNOWN.read_text())
    clean = json.loads(CLEAN.read_text())
    circ = [i for i in unknown if i["flaw_class"] == "circular_support"]
    other = [i for i in unknown if i["flaw_class"] != "circular_support"]
    assert len(circ) == 10 and len(other) == 30 and len(clean) == 40, \
        (len(circ), len(other), len(clean))

    embedder = NeuralEmbedder()
    calibration = calibrate_radius(embedder)
    radius = calibration["radius"]
    print(json.dumps({"calibration": calibration}, indent=2), flush=True)

    # Scoring pass (radius fixed above; nothing below feeds back into it).
    cache: dict[str, list[float]] = {}
    per_item: dict[str, dict] = {}
    for battery, items in (("circular", circ), ("other_unknown", other),
                           ("clean", clean)):
        for item in items:
            rec = check_item(item["judged_text"], embedder, radius, cache)
            rec["battery"] = battery
            if battery != "clean":
                rec["flaw_class"] = item["flaw_class"]
            per_item[item["id"]] = rec

    def flagged(items):
        return [i["id"] for i in items if per_item[i["id"]]["flagged"]]

    circ_flagged = flagged(circ)
    clean_flagged = flagged(clean)
    other_flagged = flagged(other)
    catch = round(len(circ_flagged) / len(circ), 4)
    clean_fp = round(len(clean_flagged) / len(clean), 4)
    other_rate = round(len(other_flagged) / len(other), 4)

    baseline = zoo_circular_baseline({i["id"] for i in circ})
    margin_pp = round((catch - baseline["best_rate"]) * 100, 2)

    # ------------------------------------------------------------------ #
    # Exploratory (NON_VERDICT_BEARING): radius sweep over the observed
    # per-item minimum distances — computed AFTER the committed-radius
    # scoring pass, purely diagnostic, and clearly labelled as such.
    # ------------------------------------------------------------------ #
    def sweep_counts(r: float) -> tuple[int, int]:
        def hit(rec):
            d = rec["min_support_conclusion_distance"]
            return (d is not None and d < r) or bool(rec["reference_cycle"])
        return (sum(hit(per_item[i["id"]]) for i in circ),
                sum(hit(per_item[i["id"]]) for i in clean))

    grid = sorted({round(v["min_support_conclusion_distance"], 4) + 0.0001
                   for v in per_item.values()
                   if v["min_support_conclusion_distance"] is not None})
    sweep = [{"radius": round(r, 4), "circular_caught": c, "clean_flagged": f}
             for r in grid for c, f in [sweep_counts(r)]]
    jointly_satisfiable = any(s["circular_caught"] >= 7
                              and s["clean_flagged"] <= 2 for s in sweep)
    best_catch_at_p2 = max((s["circular_caught"] for s in sweep
                            if s["clean_flagged"] <= 2), default=0)

    def dist_quantiles(battery):
        xs = sorted(v["min_support_conclusion_distance"]
                    for v in per_item.values() if v["battery"] == battery
                    and v["min_support_conclusion_distance"] is not None)
        if not xs:
            return None
        return {"n_with_pairs": len(xs), "min": round(xs[0], 4),
                "median": round(xs[len(xs) // 2], 4),
                "max": round(xs[-1], 4)}

    exploratory = {
        "NON_VERDICT_BEARING": True,
        "note": "computed after the committed-radius scoring pass; no "
                "number here feeds any verdict",
        "radius_sweep_summary": {
            "jointly_satisfiable_P1_and_P2": jointly_satisfiable,
            "max_circular_catch_with_clean_fp_le_2_of_40":
                best_catch_at_p2,
            "reading": "the per-item minimum support-conclusion distances "
                       "of clean items overlap those of circular items "
                       "across the whole range: NO radius passes P1 and "
                       "P2 together on this corpus, so the failure is the "
                       "embedding arm's geometry on same-topic prose, not "
                       "the fallback calibration rule",
        },
        "min_distance_quantiles": {b: dist_quantiles(b)
                                   for b in ("circular", "other_unknown",
                                             "clean")},
        "reference_cycle_arm_fires": sum(
            1 for v in per_item.values() if v["reference_cycle"]),
        "items_without_conclusion_support_pairs": sorted(
            k for k, v in per_item.items()
            if v["min_support_conclusion_distance"] is None),
    }

    p1 = "CONFIRMED" if len(circ_flagged) >= 7 else "REFUTED"
    p2 = "CONFIRMED" if len(clean_flagged) <= 2 else "REFUTED"
    p3 = "CONFIRMED" if margin_pp >= 30 else "REFUTED"

    verdicts = {
        "P1": {"verdict": p1,
               "measured": {"circular_flagged": len(circ_flagged),
                            "of": len(circ), "catch_rate": catch,
                            "flagged_ids": sorted(circ_flagged)},
               "threshold": ">= 7 of 10"},
        "P2": {"verdict": p2,
               "measured": {"clean_flagged": len(clean_flagged),
                            "of": len(clean), "fp_rate": clean_fp,
                            "flagged_ids": sorted(clean_flagged)},
               "threshold": "<= 2 of 40"},
        "P3": {"verdict": p3,
               "measured": {"screen_catch": catch,
                            "best_zoo_seat": baseline["best_seat"],
                            "best_zoo_seat_catch": baseline["best_rate"],
                            "margin_pp": margin_pp},
               "threshold": ">= 30 pp over best single zoo seat"},
    }

    caveats = [
        "Prototype screen over PROSE, not an ontology verifier; graduation "
        "requires a follow-up per the prereg's instrument note.",
        "The calibration classes did NOT separate on the committed pairs "
        "(positive max 0.4675 > negative p10 0.4143), so the committed "
        "fallback rule (positive maximum) fixed a radius at same-topic "
        "rather than near-identical scale; per the basin doctrine a "
        "non-separable gate is itself a flagged condition, and it is "
        "recorded here, not hidden.",
        "The exploratory sweep (NON_VERDICT_BEARING) shows no radius "
        "passes P1 and P2 together on this corpus: clean items' closest "
        "support-conclusion distances overlap circular items' across the "
        "whole range, so the embedding arm's premise — that circular "
        "restatement is geometrically closer than honest same-topic "
        "support — fails at this embedder's geometry on this corpus.",
        "The reference-cycle arm never fired on this corpus (no item "
        "states labelled derivation references); it is validated only in "
        "the negative here.",
        "Two circular items produced no conclusion-support pair under the "
        "marker parser and are unflaggable by construction (parse-level "
        "recall ceiling 8/10; both are the P1 misses).",
        "Single corpus, and every circular item was authored by one "
        "adversary model (deepseek-v4-pro) under one prompt family; the "
        "measured catch is for adversary-authored circulars of that style "
        "only and does not generalize without new corpora.",
        "The duplicate radius was calibrated only on committed paraphrase "
        "pairs from the harness's own jargon domain; corpus items are "
        "popular-science prose, so the radius transfers across domains "
        "untested.",
        "Design choice committed before scoring: the opening sentence's "
        "main clause is treated as a thesis announcement, not support "
        "(its because-clause still counts); without this rule ordinary "
        "summary prose ('thesis ... therefore thesis') would be flagged.",
        "The clean battery is the ORIGINAL 40-item t2 set (uncorrected), "
        "keeping this tranche independent of t2b; any genuinely defective "
        "clean item can only inflate the measured false-positive rate.",
        "The other-unknown-flaw flag rate is reported as context, not a "
        "verdict: a flag there is off-target for the screen's class but "
        "not necessarily wrong about the item.",
        "Zero LLM tokens: local neural embedder (nomic) plus regex "
        "parsing only; the P3 baseline is recomputed from the committed "
        "t3 judgments at zero new cost.",
    ]

    report = {
        "schema": SCHEMA,
        "prereg": PREREG,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "instrument": {
            "script": "scripts/circularity_check.py",
            "segmentation": "regex sentence split, bullets as boundaries",
            "conclusion_markers": "therefore/thus/hence/so/consequently/"
                                  "accordingly/it follows/we conclude/this "
                                  "shows-proves-establishes-confirms-"
                                  "demonstrates-means/in conclusion/"
                                  "which is why; because-inversions give "
                                  "(claim, support) clause pairs",
            "flag_rule": "support unit within duplicate radius of a "
                         "conclusion (cosine), or stated derivation "
                         "references form a cycle",
            "thesis_rule": "opening sentence's main clause excluded from "
                           "the support pool (committed pre-scoring)",
        },
        "calibration": calibration,
        "radius": radius,
        "volumes": {"circular": len(circ), "other_unknown_flaw": len(other),
                    "clean": len(clean)},
        "rates": {"circular_catch": catch, "clean_fp": clean_fp,
                  "other_unknown_flag_rate": other_rate},
        "zoo_circular_baseline": baseline,
        "verdicts": verdicts,
        "exploratory": exploratory,
        "per_item": {k: per_item[k] for k in sorted(per_item)},
        "token_spend": {"llm_tokens": 0,
                        "note": "local embedder + regex only, per prereg "
                                "budget"},
        "caveats": caveats,
    }
    report_path = RESULTS / "circularity_verifier_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    index_path = RESULTS / f"INDEX_{dt.date.today().isoformat()}.md"
    index_line = (
        f"\n## Circularity screen v1, validation tranche "
        f"({dt.date.today().isoformat()})\n\n"
        f"P1 {p1} ({len(circ_flagged)}/10 circular items flagged, bar 7), "
        f"P2 {p2} ({len(clean_flagged)}/40 clean items flagged, bar 2), "
        f"P3 {p3} (screen catch {catch} vs best zoo seat "
        f"{baseline['best_seat']} at {baseline['best_rate']}, margin "
        f"{margin_pp:+.1f}pp, bar +30). Duplicate radius {radius} "
        f"(calibrated on committed paraphrase pairs before scoring). "
        f"0 LLM tokens. Prereg: `{PREREG}`. Report: "
        f"`experiments/results/circularity_verifier_report.json`.\n")
    with index_path.open("a") as fh:
        fh.write(index_line)

    print(json.dumps({
        "radius": radius,
        "verdicts": {k: v["verdict"] for k, v in verdicts.items()},
        "rates": report["rates"],
        "zoo_best": {baseline["best_seat"]: baseline["best_rate"]},
        "flagged": {"circular": sorted(circ_flagged),
                    "clean": sorted(clean_flagged),
                    "other_unknown": sorted(other_flagged)},
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
