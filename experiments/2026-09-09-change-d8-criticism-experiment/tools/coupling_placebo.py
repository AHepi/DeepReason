#!/usr/bin/env python3
"""The coupling measure, per arm, with W2's placebo column — SPEC S9, R22.

    python coupling_placebo.py <root> [<root> ...] --out FILE [--label ARM=ROOT]
    python coupling_placebo.py --reproduce-w2

This is a DRIVER, not a second measurement. The measurement is W2's own,
copied into `w2_census.py` and `w2_q5.py` with exactly one line changed in
each (the repo-root computation, because the files sit one directory deeper
here). What this adds is the per-arm table the tranche reports and a typed
empty case; what it must never add is an opinion about a rate.

WHY THE PLACEBO IS THE WHOLE POINT. Candidates are generated in batches, so
the candidate following a criticism is usually a fresh construction that
would have differed anyway. Every rate is therefore computed twice — once on
the candidate AFTER the criticism, once on the candidate BEFORE it, which
cannot have been influenced by it — and only the DIFFERENCE is reported as
evidence. An after-rate quoted without its placebo is an artifact, which is
the finding W2 exists to have made
(`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`).

The two operationalizations are NOT averaged. R1 (mechanical) is exact: the
respect is the commitment the target failed, re-evaluated on the next
candidate's own bytes. R2 (prose-quote) is a declared proxy: the respect is
the span the critic quoted verbatim. They measure different criticisms and
carry different denominators, so they are reported side by side and never
folded into one headline.

An arm whose root carries no measurable criticism prints `n=0` and NO rate.
A rate over an empty denominator is not zero; it does not exist, and printing
one would invent evidence the record does not carry.

Reads every root READ-ONLY (`dr-drive-harness` §5: a writable open repairs,
i.e. destroys, the evidence a reader opened it to look at).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]

# The two roots W2 published, and the committed outputs the reproduction is
# checked against. Immutable, `git ls-files` knows them, and the check
# therefore survives this session (dr-execute-step, durable-tests rule 1).
W2 = REPO / "experiments/2026-08-26-run-anatomy-w2-criticism"
W2_CASES = (
    ("P-R1", REPO / "experiments/2026-08-25-poietics-program/run", W2 / "pr1_q5.json"),
    ("P-C1", REPO / "experiments/2026-08-25-change-constructive-frontier/run",
     W2 / "pc1_q5.json"),
)
# P-C1's "helped by the run's own measure" is the tranche's own exact rational
# checker; P-R1 has no scalar score and falls back to SURVIVAL. The fallback is
# what this tranche's own composition roots will use, so the reproduction
# exercises both paths.
W2_CHECKERS = {"P-C1": REPO / "experiments/2026-08-25-change-constructive-frontier"}

RATE_KEYS = (
    "CouplingRate", "PlaceboRate", "CouplingRate_minus_Placebo",
    "RepairRate", "NeglectRate",
)
OPERATIONALIZATIONS = ("R1_mechanical", "R2_prose_quote")


def measure_root(root: pathlib.Path, checker_dir: pathlib.Path | None = None) -> dict:
    """Run W2's census then W2's rates over one root, in-process."""

    sys.path.insert(0, str(HERE))
    import w2_census  # noqa: PLC0415
    import w2_q5  # noqa: PLC0415

    census = w2_census.census(root)
    return w2_q5.rates(root, census, checker_dir)


def _pct(value) -> str:
    return "—" if value is None else f"{100 * value:.1f}%"


def _pp(value) -> str:
    return "—" if value is None else f"{100 * value:+.1f} pp"


def render_arm_table(rows: list[tuple[str, str, dict]]) -> str:
    """The reported table. The difference column is the only evidence column
    and is marked as such in the header, not in a footnote a reader may skip."""

    out = [
        "| Arm | Root | Operationalization | n | Coupling | Placebo | "
        "**Coupling − Placebo** (the evidence) | Repair | Neglect |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for label, root, result in rows:
        for op in OPERATIONALIZATIONS:
            block = result.get(op) or {}
            n = block.get("denominator_measurable") or 0
            if not n:
                out.append(
                    f"| {label} | {root} | {op} | **n=0** | — | — | — | — | — |"
                )
                continue
            out.append(
                f"| {label} | {root} | {op} | {n} | "
                f"{_pct(block.get('CouplingRate'))} | "
                f"{_pct(block.get('PlaceboRate'))} | "
                f"**{_pp(block.get('CouplingRate_minus_Placebo'))}** | "
                f"{_pct(block.get('RepairRate'))} | "
                f"{_pct(block.get('NeglectRate'))} |"
            )
    return "\n".join(out)


def reproduce_w2(tolerance_pp: float = 0.1) -> int:
    """Re-derive W2's published table and compare to its committed outputs.

    The tolerance is on PERCENTAGE POINTS, and it exists for float formatting
    only. A disagreement is a failure of this copy, not a rounding note: the
    two roots are immutable and the committed JSON is the sealed answer.
    """

    failures, lines = [], []
    for label, root, expected_path in W2_CASES:
        expected = json.loads(expected_path.read_text())
        got = measure_root(root, W2_CHECKERS.get(label))
        for op in OPERATIONALIZATIONS:
            for key in RATE_KEYS + ("denominator_measurable", "coupled", "helped"):
                want, have = expected[op].get(key), got[op].get(key)
                if want is None or have is None:
                    ok = want is have
                    delta = "both-absent" if ok else f"{want!r} vs {have!r}"
                elif key in RATE_KEYS:
                    ok = abs(100 * (want - have)) <= tolerance_pp
                    delta = f"{100 * want:.4f} vs {100 * have:.4f} pp"
                else:
                    ok = want == have
                    delta = f"{want} vs {have}"
                lines.append(f"  {'OK  ' if ok else 'FAIL'} {label} {op}.{key}: {delta}")
                if not ok:
                    failures.append(f"{label}.{op}.{key}: {delta}")
        lines.append(render_arm_table([(label, root.name, got)]))
    print("\n".join(lines))
    if failures:
        print(f"\nREPRODUCTION FAILED on {len(failures)} field(s):")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("\nREPRODUCTION OK: every rate, denominator and count matches W2's "
          "committed output within 0.1 pp.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="*", help="run roots to measure")
    parser.add_argument("--label", action="append", default=[],
                        metavar="ARM=ROOT", help="name an arm for a root")
    parser.add_argument("--out", default=None, help="write the JSON here")
    parser.add_argument("--reproduce-w2", action="store_true",
                        help="re-derive W2's published table and compare")
    args = parser.parse_args()

    if args.reproduce_w2:
        return reproduce_w2()
    if not args.roots and not args.label:
        parser.error("give at least one root, or --reproduce-w2")

    named = [tuple(spec.split("=", 1)) for spec in args.label]
    named += [(pathlib.Path(r).name, r) for r in args.roots]
    # A root named both by --label and positionally is ONE root, not two. The
    # duplicate row is not merely untidy: a reader counting rows would read one
    # measurement as two independent ones.
    seen, deduped = set(), []
    for label, raw in named:
        key = str(pathlib.Path(raw).resolve())
        if key in seen:
            continue
        seen.add(key)
        deduped.append((label, raw))
    rows, payload = [], {"schema": "coupling-placebo.v1", "arms": {}}
    for label, raw in deduped:
        root = pathlib.Path(raw).resolve()
        result = measure_root(root)
        rows.append((label, root.name, result))
        payload["arms"][label] = {"root": str(root), "rates": result}
    print(render_arm_table(rows))
    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
