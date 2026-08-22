"""Reach census over every committed run root (READ-ONLY).

Two independent passes, deliberately not sharing a reader:

  RECORDED  — parses <root>/log.jsonl as text and counts what the run
              ACTUALLY recorded: Measure events carrying ``reach_set`` or
              ``addr+``, and Measure events whose inputs start with
              ``reach-provisional``. This is the typed record and it is
              the authority for "did reach fire".

  RE-DERIVED — opens the root with the current reader
              (``Harness(root, read_only=True)``) and walks the same
              decision tree ``measures/reach.py::reach_sweep`` walks over
              the replayed FINAL state, attributing every (accepted
              artifact, foreign problem) pair to exactly one exit. This
              is the diagnosis for "and if not, why". It records nothing:
              ``record_measure`` is never called.

A root the current reader cannot open is OUT OF SCOPE (operator law
2026-08-14, "old runs owe the future nothing") — reported, not diagnosed.

Exits, in the order reach_sweep takes them:

  A-skip/status     artifact not ACCEPTED            (artifact-level)
  A-skip/unaddr     artifact addresses no problem    (artifact-level)
  E0 empty-own-battery
                    the reaching artifact declares no commitments of
                    its own, so it forbids nothing and grounds no reach
                    (operator ruling 2026-08-22, tranche
                    experiments/2026-08-22-change-reach-p5-rulings)
  E1 no-criteria    foreign problem has no criteria
  E2 non-qualifying no criterion is substantive-and-evaluable
  E3 no-novel       every qualifying criterion is already in the
                    artifact's own battery
  E4 criterion-fail some qualifying criterion does not PASS
  E5 coverage       all pass, but qualifying/total < coverage_min
                    -> PROVISIONAL
  HIT               all pass, coverage met -> FULL

E2 is sub-attributed: unregistered (criterion id absent from
harness.commitments), rubric, non-evaluable (unknown program), or
structural (in _STRUCTURAL_PROGRAMS).

The committed census outputs (census.json, census-verdicts.json) were
measured on 2026-08-21, BEFORE E0 existed; pairs this pass would now
attribute to E0 are distributed across E1..E5/HIT in those files. They
are left as measured rather than re-derived: they are the record of what
that reader saw on that day, and re-deriving them is a 96-root
measurement, not a vocabulary update.

Usage:
    python census.py            # cheap pass: stops each pair at E3
    python census.py --verdicts # also evaluates E4/E5/HIT (slower)
"""

import collections
import json
import pathlib
import sys
import time
import traceback

REPO = pathlib.Path(__file__).resolve().parents[2]
WITH_VERDICTS = "--verdicts" in sys.argv
COVERAGE_MIN = 0.5


def recorded_census(root: pathlib.Path) -> dict:
    """What the log itself says. Text-only; no reader involved."""
    out = collections.Counter()
    reach_pairs, prov_pairs = [], []
    for line in (root / "log.jsonl").read_text(errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except Exception:
            out["unparseable_lines"] += 1
            continue
        out["events"] += 1
        if event.get("rule") != "Measure":
            continue
        out["measures"] += 1
        inputs = event.get("inputs") or []
        if inputs and inputs[0] == "reach-provisional":
            out["reach_provisional_events"] += 1
            prov_pairs.append(tuple(inputs[1:3]))
        diff = event.get("state_diff") or {}
        reach_set = diff.get("reach_set") or {}
        addr_add = diff.get("addr+") or []
        if reach_set:
            out["reach_set_events"] += 1
            out["reach_nonzero_entries"] += sum(1 for v in reach_set.values() if v)
            out["reach_zero_entries"] += sum(1 for v in reach_set.values() if not v)
        if addr_add:
            out["measure_addr_events"] += 1
            out["measure_addr_pairs"] += len(addr_add)
            reach_pairs.extend(tuple(p) for p in addr_add)
    out["_full_hit_pairs"] = len(reach_pairs)
    return dict(out)


def rederived_census(root: pathlib.Path) -> dict:
    from deepreason import programs
    from deepreason.harness import Harness
    from deepreason.measures.reach import _STRUCTURAL_PROGRAMS, _substantive
    from deepreason.ontology.state import Status

    harness = Harness(root, read_only=True)
    state = harness.state

    addressed: dict[str, set[str]] = {}
    for aid, pid in state.addr:
        addressed.setdefault(aid, set()).add(pid)

    counts = collections.Counter()
    counts["artifacts_total"] = len(state.artifacts)
    counts["problems_total"] = len(state.problems)
    counts["addr_pairs"] = len(state.addr)
    counts["commitments_registered"] = len(harness.commitments)

    # criterion vocabulary over every problem, for the census table
    crit_kinds = collections.Counter()
    for problem in state.problems.values():
        for cid in problem.criteria:
            commitment = harness.commitments.get(cid)
            if commitment is None:
                crit_kinds["unregistered"] += 1
                continue
            kind, _, arg = commitment.eval.partition(":")
            if kind == "program" and arg in _STRUCTURAL_PROGRAMS:
                crit_kinds[f"structural:{arg}"] += 1
            elif kind == "program" and not programs.evaluable(commitment):
                crit_kinds[f"unknown-program:{arg}"] += 1
            elif kind == "program":
                crit_kinds[f"substantive-program:{arg}"] += 1
            elif kind == "rubric":
                crit_kinds["rubric"] += 1
            elif kind == "predicate":
                crit_kinds["substantive-predicate"] += 1
            else:
                crit_kinds[f"other:{kind}"] += 1

    qualifying_vocab: dict[str, dict] = {}
    gate_coverage = collections.Counter()

    candidates = []
    for aid, status in state.status.items():
        if status != Status.ACCEPTED:
            counts["A-skip/status"] += 1
            continue
        if aid not in addressed:
            counts["A-skip/unaddr"] += 1
            continue
        candidates.append(aid)
    counts["artifacts_candidate"] = len(candidates)

    verdict_cache: dict[tuple[str, str], str] = {}

    def verdict(cid: str, aid: str, artifact) -> str:
        key = (cid, aid)
        if key in verdict_cache:
            return verdict_cache[key]
        try:
            value, trace = programs.evaluate(
                harness.commitments[cid], artifact, harness.blobs
            )
        except Exception as error:  # NotEvaluable etc. — never a PASS
            value, trace = f"error:{type(error).__name__}", {}
        if "sandbox_abort" not in trace:
            verdict_cache[key] = value
        return value

    for aid in candidates:
        artifact = state.artifacts[aid]
        carried = set(artifact.interface.commitments)
        for pid, problem in state.problems.items():
            if pid in addressed[aid]:
                continue
            counts["pairs"] += 1
            # Kept in reach_sweep's own order: E0 is decided on the REACHING
            # artifact, before any foreign criterion is read, so attributing
            # it later would credit these pairs to an exit the sweep never
            # reached for them.
            if not carried:
                counts["E0 empty-own-battery"] += 1
                continue
            if not problem.criteria:
                counts["E1 no-criteria"] += 1
                continue
            qualifying = [
                c for c in problem.criteria
                if c in harness.commitments and _substantive(harness.commitments[c])
            ]
            if not qualifying:
                counts["E2 non-qualifying"] += 1
                for cid in problem.criteria:
                    commitment = harness.commitments.get(cid)
                    if commitment is None:
                        counts["_E2 sub:unregistered"] += 1
                    elif commitment.eval.startswith("rubric:"):
                        counts["_E2 sub:rubric"] += 1
                    elif not programs.evaluable(commitment):
                        counts["_E2 sub:non-evaluable"] += 1
                    else:
                        counts["_E2 sub:structural"] += 1
                continue
            if not (set(qualifying) - carried):
                counts["E3 no-novel"] += 1
                continue
            counts["reached-verdict-gate"] += 1
            coverage = len(qualifying) / len(problem.criteria)
            gate_coverage[f"{coverage:.2f}"] += 1
            if coverage >= COVERAGE_MIN:
                counts["gate/coverage-would-allow-full"] += 1
            else:
                counts["gate/coverage-caps-at-provisional"] += 1
            for cid in qualifying:
                row = qualifying_vocab.setdefault(
                    cid, {"eval": harness.commitments[cid].eval[:200], "gate_pairs": 0}
                )
                row["gate_pairs"] += 1
            if not WITH_VERDICTS:
                counts["E4+ not-evaluated"] += 1
                continue
            verdicts = [verdict(c, aid, artifact) for c in qualifying]
            if not all(v == programs.PASS for v in verdicts):
                counts["E4 criterion-fail"] += 1
                counts["_E4 first-nonpass:" + next(
                    v for v in verdicts if v != programs.PASS
                )] += 1
                continue
            if len(qualifying) / len(problem.criteria) < COVERAGE_MIN:
                counts["E5 coverage/provisional"] += 1
                continue
            counts["HIT full"] += 1

    counts["_crit_kinds"] = dict(crit_kinds.most_common())
    counts["_gate_coverage"] = dict(sorted(gate_coverage.items()))
    counts["_qualifying_vocab"] = qualifying_vocab
    return dict(counts)


def main() -> int:
    roots = sorted({p.parent for p in (REPO / "experiments").rglob("log.jsonl")})
    report = {"coverage_min": COVERAGE_MIN, "with_verdicts": WITH_VERDICTS, "roots": []}
    totals = collections.Counter()
    for root in roots:
        rel = str(root.relative_to(REPO))
        entry = {"root": rel, "recorded": recorded_census(root)}
        started = time.time()
        try:
            entry["rederived"] = rederived_census(root)
            entry["opens"] = True
        except Exception as error:
            entry["opens"] = False
            entry["open_error"] = f"{type(error).__name__}: {error}"
            entry["open_traceback"] = traceback.format_exc().splitlines()[-3:]
        entry["seconds"] = round(time.time() - started, 2)
        report["roots"].append(entry)
        print(
            f"{rel:78} opens={str(entry['opens']):5} "
            f"rec_reach={entry['recorded'].get('reach_set_events', 0)} "
            f"rec_addr_pairs={entry['recorded'].get('measure_addr_pairs', 0)} "
            f"rec_prov={entry['recorded'].get('reach_provisional_events', 0)} "
            + (
                " ".join(
                    f"{k}={v}" for k, v in entry.get("rederived", {}).items()
                    if not k.startswith("_") and k in (
                        "pairs", "E1 no-criteria", "E2 non-qualifying",
                        "E3 no-novel", "reached-verdict-gate",
                        "E4 criterion-fail", "E5 coverage/provisional", "HIT full",
                    )
                )
                if entry["opens"] else entry["open_error"][:60]
            ),
            flush=True,
        )
        for key, value in entry["recorded"].items():
            if isinstance(value, int):
                totals["recorded." + key] += value
        if entry["opens"]:
            totals["roots_open"] += 1
            for key, value in entry["rederived"].items():
                if isinstance(value, int):
                    totals["rederived." + key] += value
        else:
            totals["roots_out_of_scope"] += 1
    totals["roots_total"] = len(roots)
    report["totals"] = dict(sorted(totals.items()))
    out = pathlib.Path(__file__).with_name(
        "census-verdicts.json" if WITH_VERDICTS else "census.json"
    )
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("\n=== TOTALS ===")
    for key, value in sorted(totals.items()):
        print(f"  {key:44} {value}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
