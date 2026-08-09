"""Phase 4 step 2: run the three independent re-judgment checks
(pair-order-swapped, skeptic-framed, verbatim-repeat) on every sampled
pair, using the SAME bounded-call mechanism as the sibling's own
phase2_patrol.py (OpenAICompatEndpoint, glm-5.2, temperature=0.0,
max_tokens=300, timeout=60, reasoning=none, json_mode=True). Fetches
enriched-half roots read-only from the sibling branch on demand (never
checked out, never merged) if not already present locally.

Usage: python3 phase4_rejudge.py SAMPLE_JSON OUT_JSON [--kind hit|non_hit]
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SIBLING_BRANCH = "origin/claude/corpus-enrichment-patrol-pilot-f4khnk"

ORIGINAL_PROMPT_TEMPLATE = """You are given two claims (A and B), both currently accepted as
true within the reasoning record they come from. Judge ONLY
whether A and B, read together, assert something that cannot both
be true -- a genuine contradiction between them. Do not evaluate
whether either claim is correct on its own; judge mutual
consistency only.

Claim A: {claim_a}

Claim B: {claim_b}

Respond with EXACTLY one JSON object and nothing else:
{{"contradiction": true or false, "confidence": a number from 0.0
to 1.0, "reason": "one sentence, at most 200 characters"}}"""

SKEPTIC_PROMPT_TEMPLATE = """You are given two claims (A and B), both currently accepted as
true within the reasoning record they come from. Argue that A and
B are CONSISTENT -- find any reasonable reading under which both
can be true together. Only if you find NO consistent reading
exists at all, say so.

Claim A: {claim_a}

Claim B: {claim_b}

Respond with EXACTLY one JSON object and nothing else:
{{"contradiction": true or false, "confidence": a number from 0.0
to 1.0, "reason": "one sentence, at most 200 characters"}}"""

CONFIDENCE_THRESHOLD = 0.6
FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def make_endpoint():
    import os

    from deepreason.llm.endpoints import OpenAICompatEndpoint

    return OpenAICompatEndpoint(
        base_url="https://ollama.com/v1",
        model="glm-5.2",
        api_key=os.environ.get("OLLAMA_API_KEY"),
        temperature=0.0,
        max_tokens=300,
        timeout_s=60,
        json_mode=True,
        reasoning="none",
    )


def robust_parse(raw: str):
    """Unlike Phase 2's own parser, strips a markdown fence before
    parsing -- fixes, for THIS phase's own calls only, the defect
    inherited (not caused) from Phase 2's data (PREREG-P4.yaml)."""
    if raw is None:
        return None
    text = raw.strip()
    m = FENCE_RE.match(text)
    if m:
        text = m.group(1)
    try:
        obj = json.loads(text)
        contradiction = obj["contradiction"]
        confidence = float(obj["confidence"])
        reason = str(obj["reason"])[:200]
        if not isinstance(contradiction, bool):
            raise ValueError("contradiction not bool")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("confidence out of range")
        return {"contradiction": contradiction, "confidence": confidence, "reason": reason}
    except Exception:  # noqa: BLE001
        return None


def ensure_root_local(root_str: str) -> Path:
    root = Path(root_str)
    if root.exists():
        return root
    # enriched-half root not yet in this tree -- fetch read-only
    rel = root.relative_to(REPO)
    print(f"fetching read-only from sibling branch: {rel}", file=sys.stderr)
    # git archive to a tar stream piped into tar -x at REPO root
    proc1 = subprocess.Popen(
        ["git", "archive", SIBLING_BRANCH, str(rel)], cwd=REPO, stdout=subprocess.PIPE
    )
    subprocess.run(["tar", "-x", "-C", str(REPO)], stdin=proc1.stdout, check=True)
    proc1.wait()
    if not root.exists():
        raise RuntimeError(f"fetch did not produce {root}")
    return root


def claim_text(root: Path, artifact_id: str) -> str:
    from deepreason.harness import Harness
    from deepreason.programs import content_text

    harness = Harness(root, read_only=True)
    return content_text(harness.state.artifacts[artifact_id], harness.blobs)


def call_check(endpoint, template: str, claim_a: str, claim_b: str) -> dict:
    prompt = template.format(claim_a=claim_a, claim_b=claim_b)
    t0 = time.monotonic()
    try:
        raw = endpoint.complete(prompt)
        error = None
    except Exception as exc:  # noqa: BLE001
        raw = None
        error = f"{type(exc).__name__}: {exc}"
    elapsed = round(time.monotonic() - t0, 3)
    parsed = robust_parse(raw) if raw is not None else None
    satisfies_hit_rule = bool(parsed and parsed["contradiction"] and parsed["confidence"] >= CONFIDENCE_THRESHOLD)
    return {
        "raw_response": raw,
        "parsed": parsed,
        "error": error,
        "elapsed_s": elapsed,
        "satisfies_hit_rule": satisfies_hit_rule,
    }


def main() -> None:
    sample_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    kind = "hit"
    if "--kind" in sys.argv:
        kind = sys.argv[sys.argv.index("--kind") + 1]

    sample = json.loads(sample_path.read_text())
    records = sample["hit_sample"] if kind == "hit" else sample["non_hit_sample"]

    endpoint = make_endpoint()
    results = []
    for i, row in enumerate(records):
        root = ensure_root_local(row["root"])
        claim_a = claim_text(root, row["artifact_a"])
        claim_b = claim_text(root, row["artifact_b"])

        check_a = call_check(endpoint, ORIGINAL_PROMPT_TEMPLATE, claim_b, claim_a)  # SWAPPED
        check_b = call_check(endpoint, SKEPTIC_PROMPT_TEMPLATE, claim_a, claim_b)
        check_c = call_check(endpoint, ORIGINAL_PROMPT_TEMPLATE, claim_a, claim_b)  # verbatim repeat

        original_satisfies = bool(row.get("is_hit"))
        entry = {
            "root": row["root"],
            "problem_id": row["problem_id"],
            "artifact_a": row["artifact_a"],
            "artifact_b": row["artifact_b"],
            "corpus_half": row.get("corpus_half"),
            "original_is_hit": original_satisfies,
            "original_parsed": row.get("parsed"),
            "check_a_pair_swapped": check_a,
            "check_b_skeptic_framed": check_b,
            "check_c_verbatim_repeat": check_c,
        }
        if kind == "hit":
            all_agree = (
                check_a["satisfies_hit_rule"]
                and check_b["satisfies_hit_rule"]
                and check_c["satisfies_hit_rule"]
            )
            entry["validates"] = all_agree
        else:
            any_flip = (
                check_a["satisfies_hit_rule"]
                or check_b["satisfies_hit_rule"]
                or check_c["satisfies_hit_rule"]
            )
            entry["false_negative_flip"] = any_flip
        results.append(entry)
        print(f"[{i+1}/{len(records)}] {kind} root={Path(row['root']).name} done", file=sys.stderr)

    out_path.write_text(json.dumps({"kind": kind, "results": results}, indent=2, sort_keys=True))
    print(f"wrote {len(results)} re-judgment records -> {out_path}")


if __name__ == "__main__":
    main()
