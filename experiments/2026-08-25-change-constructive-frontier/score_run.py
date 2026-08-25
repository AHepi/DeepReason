#!/usr/bin/env python3
"""Score ARM H's record with the EXACT checker, and count the refutations.

SPEC.md S3/S10, REQUEST.md R4, R24, R31.

WHAT THIS IS FOR.  The in-run battery (`criteria.py`) is float64 and is an
ADMISSION gate: it decides what the run accepts while the run is happening.
This script is the AUTHORITY for every number RESULTS.md quotes -- it
re-reads the record afterwards and scores every candidate with the exact
rational checker.  Two arithmetics, one of them authoritative, declared in
advance (A10).

IT FORMS NO OPINION.  Every figure below is either read from a typed
artifact or computed by `checker.py`.  Nothing here consults model prose
for a verdict, which is R4.

SURVIVOR COUNTS ARE QUOTED CONJECTURE-ONLY (R31).  The poietics tranche
recorded that survivor counts inflate with import-role admission records --
24 of its 82 "survivors" were the operator's own documents, not conjectures
(its RESULTS.md R1, parked as P4).  CLAUDE.md states the invariant plainly:
"import-role admission records never count as survivors."  This is a KNOWN
ISSUE to REPORT, not to diagnose or fix here, so the census reports both
figures side by side and labels the raw one as inflated.

Opens the root READ-ONLY -- dr-drive-harness §5: a writable open repairs,
i.e. destroys, the evidence.

Usage:  python score_run.py <root> [out.json]
"""
from __future__ import annotations

import json
import pathlib
import sys

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

import checker  # noqa: E402
from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402

# Roles whose artifacts are the MODEL'S OWN WORK.  An import-role record is
# an admitted document, not a proposal, and counting one as a survivor is
# the recorded defect this filter exists to avoid (R31).
GENERATIVE_ROLES = {"conjecturer", "variator", "synthesizer", "critic", "defender"}


def _read_json(path: pathlib.Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _tokens(root: pathlib.Path) -> dict:
    """Total tokens the run actually spent -- the quantity ARM S is matched
    against (SPEC.md S9).  Matching on the registered CAP would let an arm
    that under-spends look cheap; matching on measured spend cannot."""
    status = _read_json(root / "run-status.json")
    result = _read_json(root / "run-result.json")
    out = {
        "tokens_spent": (
            status.get("tokens_spent")
            or status.get("tokens")
            or result.get("tokens_spent")
        ),
        "token_budget": status.get("token_budget") or result.get("token_budget"),
        "cycles": status.get("cycle") or result.get("cycle"),
    }
    # progress.jsonl is the per-cycle ledger; its last line is the most
    # recent authoritative token count when run-status is terse.
    progress = root / "progress.jsonl"
    if progress.is_file():
        lines = [ln for ln in progress.read_text().splitlines() if ln.strip()]
        if lines:
            try:
                last = json.loads(lines[-1])
                out["progress_last"] = {
                    k: last.get(k)
                    for k in ("cycle", "phase", "state", "tokens", "tokens_spent")
                    if k in last
                }
                if out["tokens_spent"] is None:
                    out["tokens_spent"] = last.get("tokens") or last.get("tokens_spent")
            except json.JSONDecodeError:
                pass
    return out


def score(root: pathlib.Path) -> dict:
    harness = Harness(root, read_only=True)
    state = harness.state
    result = _read_json(root / "run-result.json")

    raw_survivors = list(result.get("survivors") or ())
    accepted = [a for a, s in state.status.items() if s == Status.ACCEPTED]

    candidates = []
    generative_survivors = []
    for aid, artifact in state.artifacts.items():
        role = str(getattr(getattr(artifact, "provenance", None), "role", "") or "")
        role = role.split(".")[-1].lower()
        if aid in raw_survivors and role in GENERATIVE_ROLES:
            generative_survivors.append(aid)

        text = programs.content_text(artifact, harness.blobs)
        # A "candidate" is an artifact that ATTEMPTED a construction, i.e.
        # one that declared at least one point line.  Prose that never tried
        # is not a refuted construction and must not be counted as one.
        if not checker.POINT_RE.search(text):
            continue
        verdict = checker.check(text)
        candidates.append(
            {
                "artifact": aid,
                "role": role,
                "accepted": aid in accepted,
                "survivor": aid in raw_survivors,
                **verdict,
            }
        )

    valid = [c for c in candidates if c["valid"]]
    refuted = [c for c in candidates if not c["valid"]]
    by_code: dict[str, int] = {}
    for c in refuted:
        by_code[str(c["code"])] = by_code.get(str(c["code"]), 0) + 1
    # A valid construction below the registered floor is refuted by the
    # battery too, and it is a DIFFERENT kind of refutation from an invalid
    # one: the model obeyed the rules and lost.  Counted separately.
    below_floor = [c for c in valid if not c.get("above_floor")]

    best = max(valid, key=lambda c: c["score"], default=None)

    return {
        "root": str(root),
        "arm": "H",
        "state": _read_json(root / "run-status.json").get("state"),
        "stop_reason": _read_json(root / "run-stop.json").get("reason"),
        **_tokens(root),
        "n_artifacts": len(state.artifacts),
        "n_candidates": len(candidates),
        "n_valid": len(valid),
        "n_refuted": len(refuted),
        "n_below_floor": len(below_floor),
        "refutations_by_code": by_code,
        "best_score": best["score"] if best else None,
        "best_score_exact": best["score_exact"] if best else None,
        "best_artifact": best["artifact"] if best else None,
        # R31: both figures, the raw one labelled.
        "survivors_raw_INFLATED_see_P4": len(raw_survivors),
        "survivors_generative_only": len(generative_survivors),
        "accepted_count": len(accepted),
        "candidates": sorted(
            candidates, key=lambda c: (-(c["score"] or 0), c["artifact"])
        ),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: score_run.py <root> [out.json]", file=sys.stderr)
        return 2
    report = score(pathlib.Path(sys.argv[1]))
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if len(sys.argv) > 2:
        pathlib.Path(sys.argv[2]).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
