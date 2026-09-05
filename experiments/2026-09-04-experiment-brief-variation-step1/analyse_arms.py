"""The arm comparison — by CALLING the committed instruments, never rebuilding.

`analyse_form_arms.py` in the parent tranche states the rule this file obeys:
"A second implementation of a measure is a second answer to the same question,
and the record would then have two numbers and no way to choose." So every
estimator here is IMPORTED:

  * length bias, the length-adjusted arm term, the permutation p and the
    quintile stratification come from
    `experiments/2026-09-03-change-provenance-history-channel/
    analyse_length_bias.py`. Its own `main()` hard-codes the M1/M3 arm labels,
    so this file drives its FUNCTIONS over this tranche's pairs. The
    estimators are its, byte for byte.
  * the candidate pool and the blind score join come from this tranche's
    `judge.py` outputs, which are the copied protocol's own files.

PREREG.md §5 requires all three views of every comparison, and this prints all
three every time: raw, length-adjusted with its p, and quintile-held. §7's
verdict may quote only the adjusted figure, so the raw one is never printed
alone.

Usage:
    python analyse_arms.py            # every comparison + the decision rule
    python analyse_arms.py --self-test  # wiring only; needs no roots
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
PARENT = REPO / "experiments" / "2026-09-03-change-provenance-history-channel"
DIVERSITY = REPO / "experiments" / "2026-08-28-diversity-generation" / "analyse.py"
CENSUS = REPO / "experiments" / "2026-09-03-change-conjecturer-pluggable-interface" / "census_conjecturer_failures.py"

# PREREG.md §3: byte-identical briefs. Any gap among these is scatter.
NULL_ARMS = ("A0", "A1P", "A2")
TREATMENTS = ("A1", "A3")


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows() -> list[tuple[str, float, float]]:
    """(arm, judged median of 15, characters) for every scored candidate."""

    blind = HERE / "blind"
    scores = json.loads((blind / "scores.json").read_text())
    keymap = json.loads((blind / "keymap.json").read_text())
    text = {
        json.loads(line)["bid"]: json.loads(line)["text"]
        for line in (blind / "candidates.jsonl").read_text().splitlines()
        if line.strip()
    }
    return [
        (keymap[bid]["arm"], float(entry["median"]), float(len(text[bid])))
        for bid, entry in scores.items()
        if not entry.get("failed")
    ]


def _relabel(data, members, label):
    return [(label if arm in members else arm, total, chars) for arm, total, chars in data]


def compare(lb, data, control: str, treat: str, *, quiet: bool = False):
    """One comparison, all three views. `lb` is the committed instrument."""

    pair = [row for row in data if row[0] in (control, treat)]
    if len({row[0] for row in pair}) < 2:
        return None
    # The committed `stratified` prints `label.split("-")[1]`, so its labels
    # must carry a hyphen. Prefixing here keeps that instrument BYTE-UNCHANGED
    # -- editing it to accept a new label shape would fork the estimator this
    # tranche exists to reuse.
    control, treat = f"arm-{control}", f"arm-{treat}"
    pair = [(f"arm-{row[0]}", row[1], row[2]) for row in pair]
    control_totals = [r[1] for r in pair if r[0] == control]
    treat_totals = [r[1] for r in pair if r[0] == treat]
    control_chars = [r[2] for r in pair if r[0] == control]
    treat_chars = [r[2] for r in pair if r[0] == treat]
    raw = statistics.mean(treat_totals) - statistics.mean(control_totals)
    coef, p, model_r2 = lb.arm_term(pair, treat)
    if quiet:
        # `stratified` prints its own quintile table; silence it for the
        # noise-floor sweep, which would otherwise print nine of them.
        import io
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            quint = lb.stratified(pair, control, treat)
    else:
        quint = lb.stratified(pair, control, treat)
    return {
        "control": control.removeprefix("arm-"),
        "treat": treat.removeprefix("arm-"),
        "n_control": len(control_totals),
        "n_treat": len(treat_totals),
        "mean_control": statistics.mean(control_totals),
        "mean_treat": statistics.mean(treat_totals),
        "best_control": max(control_totals),
        "best_treat": max(treat_totals),
        "chars_control": statistics.mean(control_chars),
        "chars_treat": statistics.mean(treat_chars),
        "chars_p": lb.perm_p(control_chars, treat_chars),
        "raw": raw,
        "adjusted": coef,
        "adjusted_p": p,
        "model_r2": model_r2,
        "quintile": quint,
    }


def _print(result) -> None:
    print(
        f"\n{result['treat']} vs {result['control']}  "
        f"(n {result['n_treat']} vs {result['n_control']})"
    )
    print(
        f"  mean judged     : {result['mean_control']:5.2f} -> "
        f"{result['mean_treat']:5.2f} of 15   best {result['best_control']:.1f} -> "
        f"{result['best_treat']:.1f}"
    )
    print(
        f"  candidate length: {result['chars_control']:.1f} -> "
        f"{result['chars_treat']:.1f} chars "
        f"({(result['chars_treat'] / result['chars_control'] - 1) * 100:+.1f}%)  "
        f"p={result['chars_p']:.4f}"
    )
    print(f"  raw gap         : {result['raw']:+.3f} of 15   [NEVER the verdict]")
    print(
        f"  length-adjusted : {result['adjusted']:+.3f} of 15  "
        f"p={result['adjusted_p']:.4f}  (model R^2 {result['model_r2']:.3f})"
        "   <- THE VERDICT FIGURE"
    )
    print(f"  quintile-held   : {result['quintile']:+.3f} of 15")


def self_test() -> int:
    assert (PARENT / "analyse_length_bias.py").exists()
    assert DIVERSITY.exists(), DIVERSITY
    assert CENSUS.exists(), CENSUS
    lb = _load(PARENT / "analyse_length_bias.py", "length_bias")
    for name in ("ols", "spearman", "r2", "arm_term", "perm_p", "stratified"):
        assert hasattr(lb, name), name
    # The estimators work on synthetic rows, so a broken import is found here
    # rather than after the arms have been paid for.
    data = [("C", 5.0 + i % 3, 200.0 + 10 * i) for i in range(30)]
    data += [("T", 7.0 + i % 3, 260.0 + 10 * i) for i in range(30)]
    out = compare(lb, data, "C", "T", quiet=True)
    assert out["n_control"] == 30 and out["n_treat"] == 30, out
    assert out["raw"] > 0, out
    print("ok — the committed estimators load and run")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return self_test()

    lb = _load(PARENT / "analyse_length_bias.py", "length_bias")
    data = rows()
    arms = sorted({row[0] for row in data})
    print("ARM_COMPARISON_V1")
    print(f"  candidates scored: {len(data)}   arms: {', '.join(arms)}")

    print("\nPER ARM")
    for arm in arms:
        totals = [row[1] for row in data if row[0] == arm]
        chars = [row[2] for row in data if row[0] == arm]
        print(
            f"  {arm:<5} n={len(totals):>3}  mean={statistics.mean(totals):5.2f}  "
            f"median={statistics.median(totals):5.2f}  best={max(totals):5.1f}  "
            f"chars={statistics.mean(chars):7.1f}"
        )

    print("\nDOES THE PANEL PAY FOR LENGTH? (pooled, all arms)")
    y = [row[1] for row in data]
    chars = [row[2] for row in data]
    print(f"  Spearman rho(chars, total) = {lb.spearman(chars, y):+.3f}")
    design = [[1.0, math.log(v)] for v in chars]
    beta = lb.ols(y, design)
    print(
        f"  total ~ {beta[0]:+.2f} {beta[1]:+.2f}*log(chars)   "
        f"R^2 = {lb.r2(y, design, beta):.3f}"
    )

    print("\n" + "=" * 70)
    print("NOISE FLOOR — arms whose briefs are byte-identical (PREREG §3.3)")
    print("=" * 70)
    floor = 0.0
    present = [arm for arm in NULL_ARMS if arm in arms]
    for i, control in enumerate(present):
        for treat in present[i + 1 :]:
            result = compare(lb, data, control, treat, quiet=True)
            if result is None:
                continue
            print(
                f"  {treat} vs {control}: adjusted {result['adjusted']:+.3f} "
                f"(p={result['adjusted_p']:.3f})  raw {result['raw']:+.3f}"
            )
            floor = max(floor, abs(result["adjusted"]))
    print(f"\n  d_noise = {floor:.3f} of 15  — no gap below this is called real")

    print("\n" + "=" * 70)
    print("EVERY ARM AGAINST B0 (the no-harness floor) — PREREG §1, §4")
    print("=" * 70)
    verdicts = {}
    if "B0" in arms:
        for arm in arms:
            if arm == "B0":
                continue
            result = compare(lb, data, "B0", arm)
            if result is None:
                continue
            _print(result)
            adjusted = result["adjusted"]
            if abs(adjusted) <= floor:
                verdict = "INCONCLUSIVE (inside the noise floor)"
            elif adjusted > 0:
                verdict = "BETTER than the single call"
            else:
                verdict = "NOT BETTER — a FAILED arm"
            verdicts[arm] = (adjusted, result["adjusted_p"], verdict)
            print(f"  VERDICT vs B0   : {verdict}")
    else:
        print("  B0 has not run. No verdict is available; PREREG §1 makes it "
              "the measure the law names.")

    print("\n" + "=" * 70)
    print("THE HISTORY DEFAULT — PREREG §7's rule, applied")
    print("=" * 70)
    pooled = _relabel(data, NULL_ARMS, "NULL")
    result = compare(lb, pooled, "NULL", "A1")
    if result is None:
        print("  A1 or the null pool is missing; no recommendation.")
    else:
        _print(result)
        d_hist = result["adjusted"]
        if d_hist > 0 and d_hist > floor:
            recommendation = "history ON by default"
        elif d_hist < 0 and abs(d_hist) > floor:
            recommendation = "history OFF by default; S10's ON is not supported"
        else:
            recommendation = (
                "NO CHANGE — the evidence does not separate history from scatter"
            )
        print(f"\n  d_hist  = {d_hist:+.3f} of 15   d_noise = {floor:.3f}")
        print(f"  RECOMMENDATION: {recommendation}")
        print("  (a recommendation only — R33: change no default yourself)")

    print("\n" + "=" * 70)
    print("A3 vs the null pool — PREREG §8 P2")
    print("=" * 70)
    result = compare(lb, pooled, "NULL", "A3")
    if result is not None:
        _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
