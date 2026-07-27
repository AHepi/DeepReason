"""Bronze repertoire v2 scorer
(prereg: experiments/bronze_repertoire_v2_prereg.yaml + amendment 1).

FROZEN BEFORE UNBLINDING: this file is committed before any arm's outputs
are read. Two instruments:

1. Mechanism-class coder: deterministic ordered keyword rules over
   claim+mechanism text. First matching class wins. Classes drawn from the
   published historiography plus an explicit other bucket. Used for P2
   (coverage differences across arms) and reported per arm.

2. Distinctness rule for P1: admitted conjectures collapsed by nomic
   near-duplication at the paraphrase margin (0.19, the committed embedder
   calibration reference) - greedy clustering over the admitted set in
   content-hash order, per-item distances persisted. "Admitted distinct-
   mechanism count" = number of clusters.

P1 baselines (bronze flat v1 admitted substantive conjectures): deepseek 6,
qwen 3, kimi 4; the gpt-oss arm (no v1 stream) is compared against the v1
mean of 4.33. P3 near-duplicate rate = 1 - clusters/admitted over the FULL
emitted population per arm, same radius.
"""
from __future__ import annotations

import itertools
import json
import re
from pathlib import Path

import numpy as np

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.embedder import NeuralEmbedder

ROOTS = {
    "deepseek-v4-pro": Path("runs/rep_v2/deepseek-v4-pro"),
    "qwen3.5:397b": Path("runs/rep_v2/qwen3_5_397b"),
    "kimi-k2.6": Path("runs/rep_v2/kimi-k2_6"),
    "gpt-oss:120b": Path("runs/rep_v2/gpt-oss_120b"),
}
P1_BASELINE = {"deepseek-v4-pro": 6, "qwen3.5:397b": 3, "kimi-k2.6": 4,
               "gpt-oss:120b": 13 / 3}
PARAPHRASE_MARGIN = 0.19
OUT = Path("experiments/results/bronze_repertoire_v2_report.json")

# Ordered: first match wins. Patterns matched case-insensitively against
# claim + mechanism text.
MECHANISM_CLASSES = [
    ("earthquake", r"earthquake|seismic|quake storm"),
    ("pandemic-disease", r"pandemic|plague|epidemic|disease|pathogen|zoonotic"),
    ("climate-drought", r"drought|climate|megadrought|3\.2\s*ka|aridif|rainfall|famine"),
    ("iron-technology", r"iron[- ]?work|ironworking|iron technology|ferrous"),
    ("military-technology", r"infantry|chariot|javelin|military technolog|tactic|weapon"),
    ("internal-revolt", r"revolt|rebellion|uprising|lower[- ]class|peasant|class conflict"),
    ("migration-invasion", r"sea peoples?|migrat|invasion|raiders?|displaced"),
    ("trade-resource-disruption", r"tin|copper suppl|trade route|supply chain|bronze trade|resource"),
    ("systems-network-collapse", r"network|interdepend|systemic|cascade|tightly coupled|palatial (economy|system)"),
    ("elite-legitimacy", r"legitimacy|elite|ideolog|religio|ritual|prestige"),
    ("other", r"."),
]


def code_mechanism(text: str) -> str:
    lowered = text.lower()
    for name, pattern in MECHANISM_CLASSES:
        if re.search(pattern, lowered):
            return name
    return "other"


def conjecture_texts(harness) -> list[dict]:
    rows = []
    for aid, artifact in harness.state.artifacts.items():
        if artifact.provenance.role.value != "conjecturer":
            continue
        ref = artifact.content_ref
        if not ref.startswith("inline:"):
            continue
        try:
            content = json.loads(ref[7:])
        except ValueError:
            content = {}
        text = (str(content.get("claim", "")) + " "
                + str(content.get("mechanism", ""))).strip()
        if not text:
            continue
        rows.append({"id": aid, "text": text[:4000],
                     "status": harness.state.status[aid].value})
    return rows


def emitted_texts(root: Path, harness) -> list[str]:
    texts = []
    for line in open(root / "log.jsonl"):
        event = json.loads(line)
        llm = event.get("llm")
        if not llm or llm.get("role") != "conjecturer":
            continue
        for ref in dict.fromkeys(
            [llm.get("raw_ref")]
            + [a.get("raw_ref") for a in llm.get("attempt_trace") or []]
        ):
            if not ref:
                continue
            try:
                raw = harness.blobs.get(ref)
                raw = raw.decode() if isinstance(raw, bytes) else raw
                from deepreason.llm.repair import parse_one_json_value
                data = json.loads(parse_one_json_value(raw).text)
                if isinstance(data, str):
                    data = json.loads(data)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            candidates = data.get("candidates")
            if not isinstance(candidates, list):
                # Bare skeleton response (census extract_candidates parity).
                if "claim" in data and "mechanism" in data:
                    candidates = [{"content": data}]
                else:
                    continue
            for candidate in candidates:
                content = candidate.get("content")
                if isinstance(content, (dict, list)):
                    content = json.dumps(content, sort_keys=True)
                if not isinstance(content, str):
                    continue
                try:
                    parsed = json.loads(content)
                    text = (str(parsed.get("claim", "")) + " "
                            + str(parsed.get("mechanism", ""))).strip()
                except ValueError:
                    text = content.strip()
                if text:
                    texts.append(text[:4000])
    return texts


def greedy_clusters(texts: list[str], embedder, radius: float):
    if not texts:
        return [], {}
    vectors = [np.array(embedder.embed(t)) for t in texts]

    def dist(a, b):
        return float(1 - (a @ b) / ((a @ a) ** 0.5 * (b @ b) ** 0.5))

    centers: list[int] = []
    assignment: dict[int, int] = {}
    for index in range(len(texts)):
        for center in centers:
            if dist(vectors[index], vectors[center]) <= radius:
                assignment[index] = center
                break
        else:
            centers.append(index)
            assignment[index] = index
    return centers, assignment


def main() -> None:
    embedder = NeuralEmbedder()
    report = {
        "schema": "deepreason-bronze-repertoire-v2",
        "prereg": "experiments/bronze_repertoire_v2_prereg.yaml",
        "instruments_frozen_before_unblinding": True,
        "paraphrase_margin": PARAPHRASE_MARGIN,
        "arms": {},
    }
    for arm, root in ROOTS.items():
        ver = verify_root(root)
        harness = Harness(root)
        admitted = conjecture_texts(harness)
        admitted_sorted = sorted(admitted, key=lambda r: r["id"])
        centers, _ = greedy_clusters(
            [r["text"] for r in admitted_sorted], embedder, PARAPHRASE_MARGIN)
        emitted = emitted_texts(root, harness)
        emitted_sorted = sorted(set(emitted))
        e_centers, _ = greedy_clusters(emitted_sorted, embedder, PARAPHRASE_MARGIN)
        classes = {}
        for row in admitted_sorted:
            cls = code_mechanism(row["text"])
            classes[cls] = classes.get(cls, 0) + 1
        emitted_classes = {}
        for text in emitted_sorted:
            cls = code_mechanism(text)
            emitted_classes[cls] = emitted_classes.get(cls, 0) + 1
        near_dup_rate = (
            1 - len(e_centers) / len(emitted_sorted) if emitted_sorted else None
        )
        report["arms"][arm] = {
            "verify_root_violations": ver["violations"],
            "tokens": ver["stats"]["logged_tokens"],
            "admitted_conjectures": len(admitted_sorted),
            "admitted_distinct_mechanism_count": len(centers),
            "p1_baseline_3x": round(3 * P1_BASELINE[arm], 2),
            "admitted_mechanism_classes": dict(sorted(classes.items())),
            "emitted_unique": len(emitted_sorted),
            "emitted_distinct_clusters": len(e_centers),
            "emitted_mechanism_classes": dict(sorted(emitted_classes.items())),
            "emitted_near_dup_rate": (
                round(near_dup_rate, 3) if near_dup_rate is not None else None
            ),
            "statuses": {
                s: sum(1 for r in admitted_sorted if r["status"] == s)
                for s in {r["status"] for r in admitted_sorted}
            },
        }

    arms = report["arms"]
    p1 = {a: v["admitted_distinct_mechanism_count"] >= v["p1_baseline_3x"]
          for a, v in arms.items()}
    class_sets = {a: {c for c, n in v["emitted_mechanism_classes"].items() if n}
                  for a, v in arms.items()}
    p2 = any(
        class_sets[a] - class_sets[b]
        for a, b in itertools.permutations(class_sets, 2)
    )
    p3_rates = {a: v["emitted_near_dup_rate"] for a, v in arms.items()}
    p3 = all(r is not None and r < 0.5 for r in p3_rates.values())
    p3_falsifier = any(r is not None and r >= 0.7 for r in p3_rates.values())
    report["verdicts"] = {
        "P1": "CONFIRMED" if all(p1.values()) else "REFUTED",
        "P1_per_arm": p1,
        "P2": "CONFIRMED" if p2 else "REFUTED",
        "P3": "CONFIRMED" if p3 else "REFUTED",
        "P3_falsifier_triggered": p3_falsifier,
        "P3_rates": p3_rates,
    }
    report["mechanism_novelty"] = "not_measured (requires frozen literature baseline and blind coding protocol per prereg)"
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps(report["verdicts"], indent=1))
    print(json.dumps({a: {k: v[k] for k in (
        "admitted_conjectures", "admitted_distinct_mechanism_count",
        "emitted_unique", "emitted_near_dup_rate", "tokens")}
        for a, v in arms.items()}, indent=1))


if __name__ == "__main__":
    main()
