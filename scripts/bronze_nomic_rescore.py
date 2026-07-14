"""Bronze Flat v1 deterministic offline nomic rescoring (phase F embedder_metrics).

The live roots stamped hashing-128 as the runtime embedder, so any nomic
number about this run is an OFFLINE claim. This program makes that claim
reproducible: it loads the repo's NeuralEmbedder (nomic-ai/nomic-embed-
text-v1.5, local CPU), records its full fingerprint, and scores

  (a) every emitted candidate (census corpus, claim+mechanism text) against
      each stream's first refuted conjecture, and
  (b) all pairwise distances among the registered substantive conjectures
      per stream,

persisting per-item values keyed by content sha256 / artifact id, the
calibration reference points from the committed embedder install
verification record (paraphrase margin 0.19, unrelated 0.60), and
aggregates. Pure function of the retained roots plus the model: rerunning
produces byte-identical JSON (sorted keys, no timestamps, one
generated_from_commit field).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from bronze_census import (  # noqa: E402
    RUNS_DIR,
    STREAMS,
    sha256_text,
    stream_candidate_contents,
)

from deepreason.harness import Harness  # noqa: E402
from deepreason.llm.embedder import NeuralEmbedder, distance  # noqa: E402

OUT_PATH = REPO / "experiments" / "results" / "bronze_flat_v1_nomic_rescore.json"
INLINE = "inline:"
ROUND = 6

# Calibration reference points from the committed embedder install
# verification record (experiments/results/embedder_install_verification.json
# and its INDEX_2026-07-13.md entry): planted paraphrases sit near 0.19,
# unrelated content near 0.60 on this model. These are reference points for
# reading the distances below, NOT gate thresholds; the live run's semantic
# gate never ran on this scale (NEAR_DUP_EPS was unset and the runtime
# embedder was hashing-128).
CALIBRATION_REFERENCE = {
    "paraphrase_margin": 0.19,
    "unrelated": 0.60,
    "source": "experiments/results/embedder_install_verification.json"
    " + experiments/results/INDEX_2026-07-13.md",
}


def skeleton_text(content: str) -> str:
    """claim+mechanism text for a candidate/conjecture content string.
    Accepts a strict JSON skeleton or a JSON object prefix (one retained
    registered conjecture carries trailing bytes after the object). Falls
    back to the whole content when no skeleton can be decoded."""
    obj = None
    try:
        obj = json.loads(content)
    except (ValueError, TypeError):
        stripped = content.lstrip()
        if stripped.startswith("{"):
            try:
                obj, _ = json.JSONDecoder().raw_decode(stripped)
            except ValueError:
                obj = None
    if isinstance(obj, dict) and "claim" in obj and "mechanism" in obj:
        return f"{obj['claim']}\n{obj['mechanism']}"
    return content


def is_substantive(content: str) -> bool:
    """A registered conjecture is substantive when its content decodes to a
    skeleton object with claim and mechanism."""
    return skeleton_text(content) != content


def registered_conjectures(stream: str) -> dict[str, str]:
    """artifact id -> inline content for registered conjecturer artifacts."""
    harness = Harness(str(RUNS_DIR / stream))
    out = {}
    for aid, art in harness.state.artifacts.items():
        if not (art.provenance and art.provenance.role == "conjecturer"):
            continue
        if art.content_ref.startswith(INLINE):
            out[aid] = art.content_ref[len(INLINE):]
    return out


def first_refuted_conjecture(stream: str) -> str:
    """Artifact id of the stream's first refuted registered conjecture,
    ordered by the seq of the Crit event that changed its status."""
    root = RUNS_DIR / stream
    harness = Harness(str(root))
    conj_ids = {
        aid
        for aid, art in harness.state.artifacts.items()
        if art.provenance and art.provenance.role == "conjecturer"
    }
    for line in (root / "log.jsonl").open():
        event = json.loads(line)
        if event["rule"] != "Crit":
            continue
        for aid in event["state_diff"].get("status_changed", []):
            status = harness.state.status.get(aid)
            if aid in conj_ids and getattr(status, "name", "") == "REFUTED":
                return aid
    raise RuntimeError(f"no refuted registered conjecture found in {stream}")


def rnd(value: float) -> float:
    """Round and normalize negative zero (self-distance can round to -0.0)."""
    return round(value, ROUND) + 0.0


def quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("empty")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def aggregates(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return {
        "max": rnd(ordered[-1]),
        "mean": rnd(sum(ordered) / len(ordered)),
        "min": rnd(ordered[0]),
        "n": len(ordered),
        "p10": rnd(quantile(ordered, 0.10)),
        "p25": rnd(quantile(ordered, 0.25)),
        "p50": rnd(quantile(ordered, 0.50)),
        "p75": rnd(quantile(ordered, 0.75)),
        "p90": rnd(quantile(ordered, 0.90)),
    }


def build_rescore() -> dict:
    embedder = NeuralEmbedder()
    probe = embedder.embed("dimension probe")
    fingerprint = dict(embedder.fingerprint())
    fingerprint["embedding_dim"] = len(probe)
    fingerprint["name"] = embedder.name

    cache: dict[str, list[float]] = {}

    def vec(text: str) -> list[float]:
        key = sha256_text(text)
        if key not in cache:
            cache[key] = embedder.embed(text)
        return cache[key]

    streams_out = {}
    all_corpus: list[float] = []
    all_pairwise: list[float] = []
    for stream in STREAMS:
        contents = stream_candidate_contents(stream)
        registered = registered_conjectures(stream)
        substantive = {
            aid: content
            for aid, content in registered.items()
            if is_substantive(content)
        }
        anchor_id = first_refuted_conjecture(stream)
        anchor_vec = vec(skeleton_text(registered[anchor_id]))

        corpus_to_first_refuted = {
            sha: rnd(distance(vec(skeleton_text(content)), anchor_vec))
            for sha, content in contents.items()
        }
        registered_to_first_refuted = {
            aid: rnd(distance(vec(skeleton_text(content)), anchor_vec))
            for aid, content in substantive.items()
        }
        pairwise = {}
        aids = sorted(substantive)
        for i, a in enumerate(aids):
            for b in aids[i + 1:]:
                pairwise[f"{a[:12]}:{b[:12]}"] = rnd(
                    distance(
                        vec(skeleton_text(substantive[a])),
                        vec(skeleton_text(substantive[b])),
                    )
                )

        corpus_values = list(corpus_to_first_refuted.values())
        pairwise_values = list(pairwise.values())
        all_corpus.extend(corpus_values)
        all_pairwise.extend(pairwise_values)
        streams_out[stream] = {
            "aggregates": {
                "corpus_to_first_refuted": aggregates(corpus_values),
                "registered_pairwise": aggregates(pairwise_values),
            },
            "corpus_size": len(contents),
            "corpus_to_first_refuted": corpus_to_first_refuted,
            "first_refuted_conjecture": anchor_id,
            "registered_pairwise": pairwise,
            "registered_substantive": sorted(substantive),
            "registered_to_first_refuted": registered_to_first_refuted,
        }

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()
    return {
        "aggregates_all_streams": {
            "corpus_to_first_refuted": aggregates(all_corpus),
            "registered_pairwise": aggregates(all_pairwise),
        },
        "calibration_reference": CALIBRATION_REFERENCE,
        "distance_metric": "cosine distance (1 - cosine similarity)",
        "embedder_fingerprint": fingerprint,
        "generated_from_commit": commit,
        "roots": {s: str((RUNS_DIR / s).relative_to(REPO)) for s in STREAMS},
        "rounding_decimals": ROUND,
        "runtime_embedder_note": "the live run stamped hashing-128; this file"
        " is the deterministic offline nomic rescoring required before any"
        " nomic distance may be quoted",
        "schema": "deepreason-bronze-flat-v1-nomic-rescore-v1",
        "streams": streams_out,
        "text_basis": "claim+mechanism for decodable skeletons, full content"
        " otherwise",
        "thresholds": {
            "NEAR_DUP_EPS_runtime": None,
            "paraphrase_margin_reference": CALIBRATION_REFERENCE["paraphrase_margin"],
            "unrelated_reference": CALIBRATION_REFERENCE["unrelated"],
        },
    }


def main() -> None:
    rescore = build_rescore()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(rescore, indent=2, sort_keys=True) + "\n")
    summary = {
        "aggregates_all_streams": rescore["aggregates_all_streams"],
        "embedder_fingerprint": rescore["embedder_fingerprint"],
        "streams": {
            s: {
                "aggregates": d["aggregates"],
                "corpus_size": d["corpus_size"],
                "first_refuted_conjecture": d["first_refuted_conjecture"],
            }
            for s, d in rescore["streams"].items()
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
