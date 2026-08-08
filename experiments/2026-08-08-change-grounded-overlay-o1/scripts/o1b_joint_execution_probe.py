"""O1b — joint-execution unsatisfiability probe (SPEC.md S7,
GROUNDED_OVERLAY_PREPLAN.md Rung O1). Read-only over the record; the
dynamic-fuzz half genuinely EXECUTES candidate source through
oracle.run (SPEC.md's own reuse instruction — "the harness's own
read-only readers"), but mutates no typed record and opens no root
except read-only.

"Machine-comparable input gates" (SPEC.md A4): restricted to pairs of
ACCEPTED, formally_backed artifacts answering the SAME problem, each
carrying an exec-oracle commitment (`program:exec_oracle`) with an
IDENTICAL entry name — the only place today where an admissible input
domain is machine-legible as a concrete, comparable set (the commitment's
own frozen {entry, tests} spec). Every other formally-backed pair is
EXCLUDED and counted with its reason, never guessed into a verdict.
"""

import itertools
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from overlay_common import corpus, open_root  # noqa: E402

from deepreason import oracle  # noqa: E402
from deepreason.canonical import canonical_json  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402
from deepreason.programs import content_text  # noqa: E402
from deepreason.rules.warrants import formally_backed  # noqa: E402

MAX_FUZZ_SAMPLES = 32
# Root-level bounds (SPEC.md S7's own "bounded budget, typed
# INCONCLUSIVE when it dies"): a root with many comparable pairs must
# not turn into an unbounded subprocess fan-out.
MAX_DYNAMIC_PROBES_PER_ROOT = 15
ROOT_WALLCLOCK_BUDGET_S = 60
_SENTINEL = "__O1B_NEVER_MATCHES_SENTINEL__"


def _exec_oracle_commitments(harness, aid):
    art = harness.state.artifacts[aid]
    out = []
    for cid in art.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None:
            continue
        if kappa.eval == f"program:{oracle.EXEC_PROGRAM}":
            spec = oracle._load_spec(kappa.budget)
            if spec.get("entry") and spec.get("tests"):
                out.append((cid, spec))
    return out


def _mutate(value):
    """Deterministic, bounded mutations of one literal argument value."""
    if isinstance(value, bool):
        return [not value]
    if isinstance(value, int):
        return [value + 1, value - 1, 0]
    if isinstance(value, float):
        return [value + 1.0, value - 1.0]
    if isinstance(value, str):
        return [value + "x", value[:-1]] if value else ["x"]
    if isinstance(value, list):
        muts = []
        if value:
            muts.append(list(reversed(value)))
            muts.append(value[:-1])
        muts.append(value + value[-1:] if value else [0])
        return muts
    return []


def _candidate_inputs(tests_a, tests_b):
    seeds = [t["in"] for t in tests_a] + [t["in"] for t in tests_b]
    seen = {canonical_json(s) for s in seeds}
    candidates = []
    for seed in seeds:
        for i, arg in enumerate(seed):
            for mutant in _mutate(arg):
                cand = list(seed)
                cand[i] = mutant
                key = canonical_json(cand)
                if key not in seen:
                    seen.add(key)
                    candidates.append(cand)
                if len(candidates) >= MAX_FUZZ_SAMPLES:
                    return candidates
    return candidates


def _run_and_get(source, entry, candidate):
    try:
        verdict, detail = oracle.run(source, entry, [{"in": candidate, "out": _SENTINEL}])
    except Exception as error:  # noqa: BLE001 - a probe failure is INCONCLUSIVE, not a crash
        return None, f"raised {type(error).__name__}: {error}"
    if "got" not in detail:
        return None, detail.get("error", "no got field")
    return detail["got"], None


def _literal_overlap_contradiction(spec_a, spec_b):
    table_a = {canonical_json(t["in"]): (t["in"], t["out"]) for t in spec_a["tests"]}
    table_b = {canonical_json(t["in"]): (t["in"], t["out"]) for t in spec_b["tests"]}
    for key in table_a.keys() & table_b.keys():
        in_a, out_a = table_a[key]
        _, out_b = table_b[key]
        if canonical_json(out_a) != canonical_json(out_b):
            return in_a, out_a, out_b
    return None


def analyze_root(root: pathlib.Path) -> dict:
    harness = open_root(root)
    accepted_formally_backed = [
        aid
        for aid, status in harness.state.status.items()
        if status == Status.ACCEPTED and formally_backed(harness, aid)
    ]
    addr_by_artifact: dict = {}
    for aid, pid in harness.state.addr:
        addr_by_artifact.setdefault(aid, set()).add(pid)

    comparable_pairs = []
    excluded = []
    for a, b in itertools.combinations(sorted(accepted_formally_backed), 2):
        problems_a = addr_by_artifact.get(a, set())
        problems_b = addr_by_artifact.get(b, set())
        shared_problems = problems_a & problems_b
        if not shared_problems:
            excluded.append((a, b, "no shared problem"))
            continue
        specs_a = _exec_oracle_commitments(harness, a)
        specs_b = _exec_oracle_commitments(harness, b)
        if not specs_a or not specs_b:
            excluded.append((a, b, "not both exec-oracle-class"))
            continue
        matched = [
            (cid_a, spec_a, cid_b, spec_b)
            for cid_a, spec_a in specs_a
            for cid_b, spec_b in specs_b
            if spec_a["entry"] == spec_b["entry"]
        ]
        if not matched:
            excluded.append((a, b, "no identical exec-oracle entry name"))
            continue
        comparable_pairs.append((a, b, matched[0]))

    probe_results = []
    root_deadline = time.monotonic() + ROOT_WALLCLOCK_BUDGET_S
    dynamic_probes_run = 0
    for a, b, (cid_a, spec_a, cid_b, spec_b) in comparable_pairs:
        contradiction = _literal_overlap_contradiction(spec_a, spec_b)
        if contradiction is not None:
            in_value, out_a, out_b = contradiction
            probe_results.append(
                {
                    "pair": (a, b),
                    "commitments": (cid_a, cid_b),
                    "verdict": "CONTRADICTION",
                    "evidence": {"in": in_value, "out_a": out_a, "out_b": out_b},
                }
            )
            continue

        # Root-level bounded budget (SPEC.md S7's own "bounded budget,
        # typed INCONCLUSIVE when it dies" — a single root with many
        # comparable pairs must not turn into an unbounded subprocess
        # fan-out): once the wall-clock or pair-count budget is spent,
        # every REMAINING comparable pair is reported INCONCLUSIVE
        # rather than silently skipped or run to a hang.
        if dynamic_probes_run >= MAX_DYNAMIC_PROBES_PER_ROOT or time.monotonic() > root_deadline:
            probe_results.append(
                {
                    "pair": (a, b),
                    "commitments": (cid_a, cid_b),
                    "verdict": "INCONCLUSIVE",
                    "evidence": {"reason": "root-level dynamic-probe budget exhausted"},
                }
            )
            continue
        dynamic_probes_run += 1

        candidates = _candidate_inputs(spec_a["tests"], spec_b["tests"])
        if not candidates:
            probe_results.append(
                {
                    "pair": (a, b),
                    "commitments": (cid_a, cid_b),
                    "verdict": "INCONCLUSIVE",
                    "evidence": {"reason": "no seed inputs to mutate"},
                }
            )
            continue

        source_a = content_text(harness.state.artifacts[a], harness.blobs)
        source_b = content_text(harness.state.artifacts[b], harness.blobs)
        entry = spec_a["entry"]
        agreements, disagreements, errors = [], [], 0
        for cand in candidates:
            got_a, err_a = _run_and_get(source_a, entry, cand)
            got_b, err_b = _run_and_get(source_b, entry, cand)
            if err_a is not None or err_b is not None:
                errors += 1
                continue
            if got_a == got_b:
                agreements.append({"in": cand, "got": got_a})
            else:
                disagreements.append({"in": cand, "got_a": got_a, "got_b": got_b})

        valid = len(agreements) + len(disagreements)
        if valid == 0:
            probe_results.append(
                {
                    "pair": (a, b),
                    "commitments": (cid_a, cid_b),
                    "verdict": "INCONCLUSIVE",
                    "evidence": {"reason": f"{errors} sandbox errors, 0 valid comparisons"},
                }
            )
        elif agreements:
            probe_results.append(
                {
                    "pair": (a, b),
                    "commitments": (cid_a, cid_b),
                    "verdict": "SATISFIABLE",
                    "evidence": {"witness": agreements[0], "sampled": valid},
                }
            )
        else:
            probe_results.append(
                {
                    "pair": (a, b),
                    "commitments": (cid_a, cid_b),
                    "verdict": "LOOKS_UNSATISFIABLE",
                    "evidence": {"disagreements_sample": disagreements[:5], "sampled": valid},
                }
            )

    return {
        "root": str(root),
        "accepted_formally_backed_count": len(accepted_formally_backed),
        "comparable_pair_count": len(comparable_pairs),
        "excluded_pair_count": len(excluded),
        "excluded_reasons": [{"pair": (a, b), "reason": r} for a, b, r in excluded],
        "probe_results": probe_results,
    }


def main():
    for root in corpus():
        try:
            result = analyze_root(root)
        except Exception as error:  # noqa: BLE001 - a per-root failure must not kill the sweep
            print(f"{root} ERROR {type(error).__name__}: {error}")
            continue
        verdicts = [r["verdict"] for r in result["probe_results"]]
        print(
            f"{root} accepted_formally_backed={result['accepted_formally_backed_count']} "
            f"comparable_pairs={result['comparable_pair_count']} "
            f"excluded={result['excluded_pair_count']} "
            f"verdicts={verdicts}"
        )


if __name__ == "__main__":
    main()
