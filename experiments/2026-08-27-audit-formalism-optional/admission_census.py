"""Part 2 (admission leg) — what fraction of the candidates a model WROTE
became artifacts, split by whether the candidate offered formal backing.

    python experiments/2026-08-27-audit-formalism-optional/admission_census.py

Writes ADMISSION_CENSUS.json.

The P-C2b incident asked one question the artifact-level record cannot answer:
between "the model wrote it" and "the harness scored it", what falls out, and
does KIND decide which?  This walks every conjecturer provider response in a
root's `log.jsonl`, counts the candidate objects inside it, and compares that
to the artifacts the `Conj` rule actually minted.

## The candidate-side kind signal

A conjecturer candidate can offer formal backing in exactly one way that is
visible in its own wire output: `checker_specs` (D2 rev 2 — an executable
checker attached to the candidate's own prose), or, on the skeleton path, a
forbidden case carrying `checker_spec`.  Everything else it writes is prose.
So each candidate is `offers_checker` or not, and the admission comparison is
made across that split.

The denominator is deliberately the model's OWN output, parsed from the raw
blob, not the wire-validated object: a candidate that never survived wire
validation is precisely the population the incident was about.
"""

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
W1 = os.path.join(REPO, "experiments/2026-08-26-run-anatomy-program/W1-form-census")
sys.path.insert(0, W1)


def _walk_candidates(parsed):
    """Every candidate-shaped object in a parsed provider response.

    Shapes seen live: {"candidates": [...]} (turn contracts) and
    {"candidate": {...}} (the atomic single-candidate contract).
    """
    found = []
    if isinstance(parsed, dict):
        if isinstance(parsed.get("candidates"), list):
            found += [c for c in parsed["candidates"] if isinstance(c, dict)]
        if isinstance(parsed.get("candidate"), dict):
            found.append(parsed["candidate"])
        for value in parsed.values():
            if isinstance(value, (dict, list)) and value is not parsed:
                found += _walk_candidates(value)
    elif isinstance(parsed, list):
        for item in parsed:
            found += _walk_candidates(item)
    # de-duplicate by canonical bytes; a nested walk can see one object twice
    seen, unique = set(), []
    for candidate in found:
        key = json.dumps(candidate, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _offers_checker(candidate):
    specs = candidate.get("checker_specs")
    if isinstance(specs, (list, tuple)) and any(s for s in specs):
        return True
    for case in candidate.get("forbidden") or ():
        if isinstance(case, dict) and case.get("checker_spec"):
            return True
    for cc in candidate.get("counterconditions") or ():
        if isinstance(cc, dict) and cc.get("checker_spec"):
            return True
    return False


def census_root(rel):
    import census as W1C
    from deepreason.harness import Harness
    from deepreason.ontology import Rule

    root = os.path.join(REPO, rel)
    written = Counter()          # (offers_checker,) -> candidates the model wrote
    calls = Counter()            # wire outcome per conjecturer call
    for line in open(os.path.join(root, "log.jsonl")):
        line = line.strip()
        if not line:
            continue
        event = json.loads(line)
        llm = event.get("llm")
        if not llm or llm.get("role") != "conjecturer":
            continue
        trace = llm.get("attempt_trace") or []
        wire_valid = any(bool(a.get("valid")) for a in trace) if trace else None
        calls["total"] += 1
        calls["wire_valid" if wire_valid else "wire_invalid_or_unknown"] += 1
        _path, text = W1C.read_blob(root, llm.get("raw_ref"))
        parsed, _err = W1C.parse_model_json(text)
        if parsed is None:
            calls["unparseable_blob"] += 1
            continue
        for candidate in _walk_candidates(parsed):
            written["with_checker" if _offers_checker(candidate) else "prose_only"] += 1

    harness = Harness(root, read_only=True)
    minted = Counter()
    conj_events = 0
    for event in harness.log.read():
        if event.rule is not Rule.CONJ:
            continue
        conj_events += 1
        for aid in event.state_diff.a_add:
            artifact = harness.state.artifacts.get(aid)
            if artifact is None:
                continue
            from deepreason import programs
            carried = [harness.commitments[c]
                       for c in artifact.interface.commitments
                       if c in harness.commitments]
            minted["battery_carrying" if any(programs.evaluable(k) for k in carried)
                   else "prose_only"] += 1

    return {
        "root": rel,
        "conjecturer_calls": dict(calls),
        "conj_events": conj_events,
        "candidates_written": dict(written),
        "artifacts_minted": dict(minted),
        "candidates_written_total": sum(written.values()),
        "artifacts_minted_total": sum(minted.values()),
    }


def main():
    census = json.load(open(os.path.join(HERE, "KIND_CENSUS.json")))
    out, failed = [], []
    for entry in census["roots"]:
        rel = entry["root"]
        try:
            doc = census_root(rel)
        except Exception as error:
            failed.append({"root": rel, "error": f"{type(error).__name__}: {error}"})
            print(f"FAILED {rel}: {type(error).__name__}: {error}", file=sys.stderr)
            continue
        doc["label"] = entry.get("label")
        out.append(doc)
        print(f"ok wrote={doc['candidates_written_total']:5d} "
              f"minted={doc['artifacts_minted_total']:5d}  {rel}", file=sys.stderr)

    json.dump({
        "schema": "formalism-audit.admission-census.v1",
        "roots_read": len(out),
        "roots_failed": failed,
        "roots": out,
    }, open(os.path.join(HERE, "ADMISSION_CENSUS.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
