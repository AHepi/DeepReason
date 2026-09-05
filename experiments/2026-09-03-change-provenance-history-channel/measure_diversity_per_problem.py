"""D1-D5 over admitted conjectures, GROUPED BY PROBLEM (C11).

Derived from `experiments/2026-09-02-full-harness-diversity/measure_diversity.py`
on branch `claude/model-profile-registry-opkgal` (cited, not merged -- C9).
D1-D5 are that file's measures, unchanged in definition.  What changes is the
UNIT.

## Why the unit changed, and what measuring it actually showed

C11 directs that diversity be measured per problem, seed-question candidates
only, because "the pooled D5 on that branch carries an unexamined cross-problem
confound".  The mechanism would be this: the parent script pools every artifact
in a root and takes pairwise distances over the pool, so a conjecture answering
"is the pragmatic preference defensible" is compared against one answering
"audit:ritual", and their unrelated vocabularies score as diversity.  The pooled
number would then rise with the number of PROBLEMS rather than with the spread
of answers to any one of them.

MEASURED, and the premise did not reproduce.  `--confound` mode was run over
five committed roots carrying 788 claim-bearing conjectures
(`CONFOUND_CHECK.txt`).  On every one of them the pooled and per-problem
numbers are IDENTICAL to full float precision.  The reason is visible in the
per-problem disposition the mode prints: sub-problems DO receive `Conj` output
-- `audit:ritual` takes 96 artifacts, four `conn:` problems take 42 between
them -- but every one of those artifacts has an inline body that is not JSON,
so no `claim` can be read off it and no pairwise lexical or semantic measure
can include it.  100% of claim-bearing conjectures in every committed root sit
on the seed problem.

So the confound cannot arise on any record this tree can re-derive.  Two things
follow, and neither is "ignore C11".  First, the instruction is followed
anyway: the seed-only unit is the more conservative one, it costs nothing, and
it is correct in advance of any run that DOES put claims on a sub-problem --
which no committed root does yet, but the arms this tranche launches are not
committed roots.  Second, and this is the part worth recording: C11's premise
is not merely unconfirmed, it is UNVERIFIABLE from the record.  The
full-harness-diversity run whose pooled D5 is at issue never committed its run
root -- only `RESULTS.md`, the measure script and the prereg are on that branch
-- so that D5 of 0.702 cannot be re-derived by anyone, with either unit.  That
branch's own RESULTS.md attributes the number to on-topic-ness rather than to
pooling, and offers a claim-level reading for it.

Note the direction, because it matters for how the finding is used: if pooling
inflated D5, the full engine's 0.702 would be an OVERestimate, and its true
per-problem spread would be narrower still.  The confound, had it been real,
would have strengthened that branch's conclusion rather than overturned it.

## The unit here

One problem's admitted conjectures.  The artifact->problem map is derived from
the log, not guessed: a `Conj` event carries `inputs[0]` = the problem id and
`state_diff["A+"]` = the artifacts it produced.  Artifacts from `Refl`,
`Register` and `Crit` are NOT conjecture candidates and are excluded, which the
parent script also did by requiring a `claim` field.

Only the SEED problem's candidates are reported for the M1/M3 comparison, per
C11 ("seed-question candidates only"); the other problems are printed beneath
so nothing is hidden.

Usage:
    measure_diversity_per_problem.py <run-root> [<run-root> ...]
    measure_diversity_per_problem.py --confound <run-root>
"""

from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys


def _artifact_problem_map(root: pathlib.Path) -> dict[str, str]:
    """artifact id -> problem id, from Conj events only."""
    mapping: dict[str, str] = {}
    log = root / "log.jsonl"
    if not log.exists():
        return mapping
    with log.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("rule") != "Conj":
                continue
            inputs = event.get("inputs") or []
            if not inputs:
                continue
            problem = inputs[0]
            for artifact in (event.get("state_diff") or {}).get("A+", []):
                mapping[artifact] = problem
    return mapping


def _seed_problem(root: pathlib.Path) -> str | None:
    """The operator's seed question, which always spawns first (Spawn, seq order)."""
    log = root / "log.jsonl"
    if not log.exists():
        return None
    with log.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            for pid in (event.get("state_diff") or {}).get("Π+", []):
                if str(pid).startswith("question-"):
                    return str(pid)
    return None


def conjectures(root: pathlib.Path, stances: dict | None = None) -> list[dict]:
    """Every candidate carrying a claim, tagged with its problem.

    The `claim` -> `content` fallback is the parent script's own correction:
    40 of 82 candidates in the mini-as-generator tranche used `content`, and
    reading only `claim` produced empty strings and artefactual diversity.
    """
    stances = {} if stances is None else stances
    problem_of = _artifact_problem_map(root)
    rows: list[dict] = []
    for path in sorted((root / "objects" / "artifact").rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))["data"]
        except Exception:  # noqa: BLE001
            continue
        ref = data.get("content_ref", "")
        if not ref.startswith("inline:"):
            continue
        try:
            body = json.loads(ref[len("inline:") :])
        except Exception:  # noqa: BLE001
            continue
        claim = body.get("claim") or body.get("content") or ""
        if not claim:
            if "school_policy" in body:
                stances[body["school_policy"].get("school")] = body["school_policy"].get(
                    "stance"
                )
            continue
        artifact_id = data.get("id") or path.stem
        rows.append(
            {
                "id": artifact_id,
                "problem": problem_of.get(artifact_id),
                "school": (data.get("provenance") or {}).get("school"),
                "claim": claim,
                "scope": body.get("scope") or {},
            }
        )
    return rows


def tokens(text: str) -> set[str]:
    return {w.strip(".,;:()\"'").lower() for w in text.split() if len(w) > 3}


def jaccard_distance(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 1.0
    return 1.0 - len(a & b) / len(a | b)


def _d4(rows: list[dict]) -> float | None:
    toks = [tokens(r["claim"]) for r in rows]
    pairs = list(itertools.combinations(range(len(rows)), 2))
    if not pairs:
        return None
    return sum(jaccard_distance(toks[i], toks[j]) for i, j in pairs) / len(pairs)


def _d5(rows: list[dict]) -> float | None:
    """Mean pairwise cosine distance over embedded claims, or None if no backend.

    Reported as NOT MEASURED rather than silently skipped, per the parent
    prereg: a ~523 MB download is not started mid-measurement.

    The import path and the call signature are BOTH load-bearing and both were
    wrong on the first live run of this instrument. `build_embedder` lives at
    `deepreason.llm.embedder`, not `deepreason.embedder`, and it takes the
    model name -- `ops.make_embedder` passes `config.EMBEDDER_MODEL`. Calling
    it wrongly raised ImportError, which this function catches, so D5 printed
    "NOT MEASURED (no embedder backend)" on a container where the weights were
    already warmed and D5 was perfectly measurable. A broad `except` around an
    optional dependency will report a TYPO as an absent feature; the model name
    is therefore echoed on the failure path so the next reader can tell the two
    apart.
    """
    if len(rows) < 2:
        return None
    try:
        from deepreason.config import Config
        from deepreason.llm.embedder import build_embedder, cosine

        model = Config().EMBEDDER_MODEL
        if not model:
            return None
        embedder = build_embedder(model)
        vectors = [embedder.embed(r["claim"]) for r in rows]
    except Exception as exc:  # noqa: BLE001
        print(f"  [D5 unavailable: {type(exc).__name__}: {str(exc)[:120]}]")
        return None

    pairs = list(itertools.combinations(range(len(rows)), 2))
    return sum(1.0 - cosine(vectors[i], vectors[j]) for i, j in pairs) / len(pairs)


def _near_duplicate_rate(rows: list[dict], threshold: float = 0.20) -> float | None:
    """Share of PAIRS whose lexical distance is below `threshold`.

    Registered here rather than chosen later: 0.20 Jaccard distance means the
    two claims share 80% of their content words, which is restatement.
    """
    toks = [tokens(r["claim"]) for r in rows]
    pairs = list(itertools.combinations(range(len(rows)), 2))
    if not pairs:
        return None
    close = sum(1 for i, j in pairs if jaccard_distance(toks[i], toks[j]) < threshold)
    return close / len(pairs)


def _block(label: str, rows: list[dict], indent: str = "  ") -> None:
    n = len(rows)
    print(f"{indent}--- {label}  (n={n}) ---")
    if n == 0:
        print(f"{indent}  no conjectures")
        return
    print(f"{indent}D1 count               : {n}")
    schools = [r["school"] for r in rows]
    distinct = sorted({s for s in schools if s})
    top = max((schools.count(s) for s in distinct), default=0)
    print(f"{indent}D2 stance spread       : {len(distinct)} distinct {distinct}")
    print(f"{indent}   largest school share: {top}/{n} = {top / n:.0%}")
    covers = [t for r in rows for t in (r["scope"].get("covers") or [])]
    print(
        f"{indent}D3 subject spread      : {len(set(covers))} distinct covers "
        f"over {len(covers)} slots"
    )
    d4 = _d4(rows)
    print(f"{indent}D4 lexical distinctness: {'n/a' if d4 is None else f'{d4:.3f}'}")
    d5 = _d5(rows)
    print(
        f"{indent}D5 semantic distinctness: "
        f"{'NOT MEASURED (no embedder backend)' if d5 is None else f'{d5:.3f}'}"
    )
    nd = _near_duplicate_rate(rows)
    print(
        f"{indent}ND near-duplicate rate : "
        f"{'n/a' if nd is None else f'{nd:.3f}'}  (pairs below 0.20 Jaccard distance)"
    )


def survivors_only(root: pathlib.Path, rows: list[dict]) -> list[dict]:
    """Keep only the conjectures the record says came through something.

    The progress law (CLAUDE.md, 2026-09-03) makes "survivors harder to vary"
    the success criterion, and `accepted` cannot answer that: an artifact
    nobody attacked carries the same label as one that beat off a warranted
    attack. `DR-CON-evidence-states` is the derivation; this filter only
    consumes it, and refuses rather than guesses if the reading cannot be
    built, because silently measuring the unfiltered pool under a
    survivors-only flag would report the wrong number under the right name.
    """
    from deepreason.harness import Harness
    from deepreason.views.evidence_states import EvidenceState, evidence_states

    readings = evidence_states(Harness(root, read_only=True))
    kept = [r for r in rows if readings.get(r["id"]) is EvidenceState.SUPPORTED]
    print(
        f"  [--survivors-only] {len(kept)} of {len(rows)} conjectures came "
        f"through an attack or a trial that ruled; the rest are untested, "
        f"contested, or fell"
    )
    return kept


def report(root: pathlib.Path, *, survivors: bool = False) -> None:
    rows = conjectures(root)
    seed = _seed_problem(root)
    print(f"\n=== {root} ===")
    print(f"seed problem: {seed}")
    if survivors:
        rows = survivors_only(root, rows)
    by_problem: dict[str | None, list[dict]] = {}
    for row in rows:
        by_problem.setdefault(row["problem"], []).append(row)
    if seed in by_problem:
        _block(f"SEED PROBLEM {seed}  [the M1/M3 comparison unit]", by_problem[seed])
    for pid, group in sorted(by_problem.items(), key=lambda kv: str(kv[0])):
        if pid == seed:
            continue
        _block(f"other problem {pid}", group)


def _disposition(root: pathlib.Path) -> dict[str, dict[str, int]]:
    """Per problem, why each Conj-produced artifact was kept or dropped.

    Without this the confound report cannot distinguish "this problem produced
    no conjectures" from "this instrument dropped them", and those are very
    different findings.  The first version of this script reported the former
    when the truth was neither: sub-problem artifacts exist, and their inline
    bodies are not JSON, so no `claim` can be read off them and no pairwise
    lexical or semantic measure can include them.
    """
    problem_of = _artifact_problem_map(root)
    out: dict[str, dict[str, int]] = {}
    for path in (root / "objects" / "artifact").rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))["data"]
        except Exception:  # noqa: BLE001
            continue
        aid = data.get("id")
        if aid not in problem_of:
            continue
        bucket = out.setdefault(problem_of[aid], {})
        ref = data.get("content_ref", "")
        if not ref.startswith("inline:"):
            key = "not-inline"
        else:
            try:
                body = json.loads(ref[len("inline:") :])
            except Exception:  # noqa: BLE001
                key = "inline-not-json"
            else:
                key = (
                    "claim"
                    if body.get("claim")
                    else ("content" if body.get("content") else "no-claim-no-content")
                )
        bucket[key] = bucket.get(key, 0) + 1
    return out


def confound(root: pathlib.Path) -> None:
    """C11's premise, measured on a committed root rather than assumed."""
    rows = conjectures(root)
    seed = _seed_problem(root)
    by_problem: dict[str | None, list[dict]] = {}
    for row in rows:
        by_problem.setdefault(row["problem"], []).append(row)
    pooled_d4 = _d4(rows)
    pooled_nd = _near_duplicate_rate(rows)
    seed_rows = by_problem.get(seed, [])
    seed_d4 = _d4(seed_rows)
    seed_nd = _near_duplicate_rate(seed_rows)

    disposition = _disposition(root)
    print(f"=== CROSS-PROBLEM CONFOUND on {root} ===")
    print(f"  seed problem                   : {seed}")
    print(f"  problems RECEIVING Conj output : {len(disposition)}")
    print(f"  problems with COMPARABLE claims: {len(by_problem)}")
    print("  per-problem artifact disposition (why each was kept or dropped):")
    for pid, buckets in sorted(disposition.items(), key=lambda kv: str(kv[0])):
        tag = "SEED" if pid == seed else "sub "
        detail = ", ".join(f"{k}={v}" for k, v in sorted(buckets.items()))
        print(f"      [{tag}] {pid}: {detail}")
    print(f"  claim-bearing conjectures pooled: {len(rows)}")
    print(f"  claim-bearing on the seed problem: {len(seed_rows)}")
    print(f"  D4 pooled (parent script unit) : {pooled_d4}")
    print(f"  D4 seed problem only (C11 unit): {seed_d4}")
    if pooled_d4 is not None and seed_d4 is not None:
        print(f"  D4 inflation from pooling      : {pooled_d4 - seed_d4:+.6f}")
    print(f"  near-dup pooled                : {pooled_nd}")
    print(f"  near-dup seed only             : {seed_nd}")
    if pooled_d4 is None or seed_d4 is None:
        verdict = "UNDECIDABLE on this root (too few claim-bearing conjectures)"
    elif pooled_d4 > seed_d4:
        verdict = "pooling INFLATES diversity -- C11's premise confirmed on this root"
    elif pooled_d4 < seed_d4:
        verdict = "pooling DEFLATES diversity -- opposite of C11's premise"
    else:
        verdict = (
            "pooled and per-problem are IDENTICAL -- the confound cannot arise "
            "on this root, because no sub-problem produced a claim-bearing conjecture"
        )
    print(f"\n  VERDICT: {verdict}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+")
    parser.add_argument("--confound", action="store_true")
    parser.add_argument(
        "--survivors-only", action="store_true",
        help="restrict to artifacts the record says came through an attack or "
             "a trial that ruled (DR-CON-evidence-states SUPPORTED), so the "
             "progress law's 'survivors' can be compared on survivors alone. "
             "Default OFF: without it this instrument behaves exactly as before",
    )
    args = parser.parse_args()
    for raw in args.roots:
        root = pathlib.Path(raw)
        if args.confound:
            confound(root)
        else:
            report(root, survivors=args.survivors_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
