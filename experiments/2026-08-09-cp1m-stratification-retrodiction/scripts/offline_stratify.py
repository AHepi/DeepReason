"""CP1-M offline stratification pass (no live calls).

Resolves claim text for all 1941 patrol_hits.jsonl rows + a deterministic
150-row non-hit control sample from patrol_results.jsonl, via the SAME
offline loader phase2_patrol.py used (Harness(root, read_only=True) +
programs.content_text) -- no network, no model call.

Produces a heuristic (regex/keyword) FIRST-PASS classification of each
pair into a stratum-eligibility signal. This is NOT the final stratum
assignment -- it exists only to size the strata before any live call is
pre-registered, per CLAUDE.md's "pre-register ... before any call." Final
S-mech/S-truth/S-formal/S-judgment assignment happens per-pair during the
live phases themselves.
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys

REPO = pathlib.Path("/home/user/DeepReason")
PILOT = REPO / "experiments/2026-08-08-corpus-enrichment-patrol-pilot"
sys.path.insert(0, str(REPO / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.programs import content_text  # noqa: E402

HITS = [json.loads(l) for l in (PILOT / "patrol_hits.jsonl").read_text().splitlines()]
RESULTS = [json.loads(l) for l in (PILOT / "patrol_results.jsonl").read_text().splitlines()]
NON_HITS = [r for r in RESULTS if r.get("is_hit") is False and r.get("error") is None]

print(f"hits={len(HITS)} results={len(RESULTS)} non_hit_pool={len(NON_HITS)}")

# Deterministic 150-row control sample from the non-hit pool, seeded on
# content (not wall-clock) so this is reproducible.
seed = int.from_bytes(
    __import__("hashlib").sha256(b"cp1m-control-sample-v1").digest()[:8], "big"
)
rng = random.Random(seed)
control_sample = sorted(
    rng.sample(range(len(NON_HITS)), 150), key=lambda i: i
)
controls = [NON_HITS[i] for i in control_sample]
print(f"controls sampled: {len(controls)}")

_harness_cache: dict[str, Harness] = {}


def get_harness(root: str) -> Harness | None:
    if root not in _harness_cache:
        try:
            _harness_cache[root] = Harness(pathlib.Path(root), read_only=True)
        except Exception as exc:  # noqa: BLE001
            print(f"UNOPENABLE root={root} error={type(exc).__name__}: {exc}")
            _harness_cache[root] = None
    return _harness_cache[root]


def claim_text(root: str, artifact_id: str) -> str | None:
    h = get_harness(root)
    if h is None:
        return None
    art = h.state.artifacts.get(artifact_id)
    if art is None:
        return None
    return content_text(art, h.blobs)


# --- heuristic classifiers (first-pass sizing only) ---
RULE_PAT = re.compile(r"\bRule\s*\d+\b", re.IGNORECASE)
NUMERIC_ASSERTION = re.compile(r"\b\d+(\.\d+)?\b")
COUNT_WORDS = re.compile(
    r"\b(pieces?|cuts?|counts?|total|sum|width|length|cycles?|steps?|tour|"
    r"nodes?|edges?|permutation|distance|iterations?|pattern|periodic|"
    r"linear|nonlinear)\b",
    re.IGNORECASE,
)


def mech_eligible(claim_a: str | None, claim_b: str | None) -> bool:
    """First-pass heuristic: either claim reads as an executable/countable
    assertion (a number tied to a countable/computable noun, or a named
    CA rule claim)."""
    for c in (claim_a, claim_b):
        if not c:
            continue
        if RULE_PAT.search(c):
            return True
        if NUMERIC_ASSERTION.search(c) and COUNT_WORDS.search(c):
            return True
    return False


def rows_with_text(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        ca = claim_text(r["root"], r["artifact_a"])
        cb = claim_text(r["root"], r["artifact_b"])
        out.append({**r, "_claim_a": ca, "_claim_b": cb})
    return out


hit_rows = rows_with_text(HITS)
control_rows = rows_with_text(controls)

unresolved_hits = [r for r in hit_rows if r["_claim_a"] is None or r["_claim_b"] is None]
unresolved_controls = [r for r in control_rows if r["_claim_a"] is None or r["_claim_b"] is None]
print(f"hits with unresolved claim text: {len(unresolved_hits)}")
print(f"controls with unresolved claim text: {len(unresolved_controls)}")

mech_hits = [r for r in hit_rows if mech_eligible(r["_claim_a"], r["_claim_b"])]
mech_controls = [r for r in control_rows if mech_eligible(r["_claim_a"], r["_claim_b"])]
print(f"S-mech-eligible hits (heuristic): {len(mech_hits)}/{len(hit_rows)}")
print(f"S-mech-eligible controls (heuristic): {len(mech_controls)}/{len(control_rows)}")

rule_family_hits = [r for r in hit_rows if RULE_PAT.search(r.get("reason", ""))]
print(f"rule-family hits (reason mentions RuleNNN): {len(rule_family_hits)}")
rule184 = [r for r in rule_family_hits if re.search(r"rule\s*184", r.get("reason", ""), re.I)]
print(f"  of which Rule-184-family: {len(rule184)}")

out_dir = REPO / "experiments/2026-08-09-cp1m-stratification-retrodiction"
out_dir.mkdir(exist_ok=True)


def dump(rows: list[dict], path: pathlib.Path):
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")


dump(hit_rows, out_dir / "hits_with_claims.jsonl")
dump(control_rows, out_dir / "controls_150.jsonl")

summary = {
    "hits_total": len(HITS),
    "non_hit_pool_total": len(NON_HITS),
    "controls_sampled": len(controls),
    "control_sample_seed": "sha256('cp1m-control-sample-v1')[:8] big-endian int",
    "hits_unresolved_claim_text": len(unresolved_hits),
    "controls_unresolved_claim_text": len(unresolved_controls),
    "distinct_roots_in_hits": len({r["root"] for r in HITS}),
    "s_mech_eligible_hits_heuristic": len(mech_hits),
    "s_mech_eligible_controls_heuristic": len(mech_controls),
    "rule_family_hits_reason_mentions_rule": len(rule_family_hits),
    "rule_184_family_hits": len(rule184),
}
(out_dir / "offline_stratification_summary.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(summary, indent=2, sort_keys=True))
