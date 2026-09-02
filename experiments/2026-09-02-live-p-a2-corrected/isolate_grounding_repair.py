#!/usr/bin/env python3
"""Which of P-A2's corrections costs the grounding-repair contract?

P-A2's qualification moved EXACTLY ONE pair against P-A1's:

    grounding_reviewer / groundingrepairwirev1.direct.v1 / glm-5.3
        P-A1  20/20 eventual_valid
        P-A2   5/20, VALUE_ERROR x15, 19 required

Every other pair -- including six other glm-5.3 contracts -- is 20/20 in
both. So the corrections cost one contract, and the record cannot say WHICH
correction did it, because P-A2 moved three things about this seat at once
(reasoning low, cap 32768, split protocol off).

This isolates them by exercising ONLY that pair, through the doctor's own
per-case entry point, against four manifests that differ in exactly the
fields under suspicion. Four cells, `--cases` calls each; the operator law
that tokens are cheap and the agent is not is why this is measured rather
than argued.

    A  pa2-current     reasoning low     cap 32768   split off   (P-A2)
    B  pa1-baseline    reasoning unset   cap 49152   split auto  (P-A1)
    C  low-only        reasoning low     cap 32768   split auto
    D  split-off-only  reasoning unset   cap 49152   split off

A vs C isolates the SPLIT PROTOCOL. A vs D isolates reasoning+cap together.
B is the control that must reproduce P-A1, and if B fails the whole
comparison is void -- provider drift, not our change.

The doctor's own `production_contract_pairs` and
`exercise_production_contract_case` are IMPORTED, never reimplemented, so
this probe cannot drift from the gate it explains.

Usage:  python -u isolate_grounding_repair.py [--cases N] [--cells A,B,C,D]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import tempfile

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

CONTRACT = "groundingrepairwirev1.direct.v1"

# Each cell is (label, glm_reasoning, glm_max_tokens, split_protocol).
CELLS: dict[str, tuple[str, str | None, int, str]] = {
    "A": ("pa2-current    (low / 32768 / split off)", "low", 32768, "off"),
    "B": ("pa1-baseline   (unset / 49152 / split auto)", None, 49152, "auto"),
    "C": ("low-only       (low / 32768 / split auto)", "low", 32768, "auto"),
    "D": ("split-off-only (unset / 49152 / split off)", None, 49152, "off"),
}


def _variant_config(reasoning: str | None, max_tokens: int, split: str) -> pathlib.Path:
    """P-A2's committed config with only the three fields under test moved."""
    import yaml

    data = yaml.safe_load((TRANCHE / "run-config.yaml").read_text())
    data["SPLIT_BUDGET_SEAT_PROTOCOL"] = split
    # Every glm-5.3 seat, found by MODEL rather than by role, so a seat added
    # later is not silently left on the old setting.
    def _fix(spec):
        if isinstance(spec, dict) and spec.get("model") == "glm-5.3":
            spec["max_tokens"] = max_tokens
            if reasoning is None:
                spec.pop("reasoning", None)
            else:
                spec["reasoning"] = reasoning
    for value in data.get("roles", {}).values():
        for spec in (value if isinstance(value, list) else [value]):
            _fix(spec)
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".yaml", delete=False, dir=tempfile.gettempdir()
    )
    yaml.safe_dump(data, handle, sort_keys=False)
    handle.close()
    return pathlib.Path(handle.name)


def run_cell(label: str, reasoning, max_tokens, split, cases: int) -> dict:
    import build_manifest_pa2 as builder
    from deepreason.cli.doctor import (
        exercise_production_contract_case,
        production_contract_pairs,
    )
    from deepreason.run_manifest import load_run_manifest

    config_path = _variant_config(reasoning, max_tokens, split)
    # Roots live beside the tranche and are removed after the cell, so a
    # failed probe leaves nothing behind for a later run to trip over.
    root = TRANCHE / ".isolate-roots" / label.split()[0]
    shutil.rmtree(root, ignore_errors=True)
    builder.build(root, config_path=config_path)
    # The FILE, not the root: load_run_manifest stats its argument and a
    # directory fails the regular-file check as MANIFEST_FILE_UNSAFE.
    manifest = load_run_manifest(root / "run-manifest.json")

    pairs = [p for p in production_contract_pairs(manifest) if p.contract_id == CONTRACT]
    if len(pairs) != 1:
        raise SystemExit(f"expected exactly one {CONTRACT} pair, got {len(pairs)}")
    pair = pairs[0]

    valid = 0
    first_pass = 0
    codes: dict[str, int] = {}
    for index in range(cases):
        result = exercise_production_contract_case(manifest, pair, index)
        valid += int(result.eventual_valid)
        first_pass += int(result.first_pass_valid)
        if not result.eventual_valid:
            codes[result.failure_code] = codes.get(result.failure_code, 0) + 1
        print(
            f"    case {index:02d}: eventual_valid={result.eventual_valid} "
            f"first_pass={result.first_pass_valid} repairs={result.repair_count} "
            f"code={result.failure_code or '-'}",
            flush=True,
        )
    shutil.rmtree(root.parent, ignore_errors=True)
    config_path.unlink(missing_ok=True)
    return {
        "label": label,
        "reasoning": reasoning,
        "max_tokens": max_tokens,
        "split": split,
        "cases": cases,
        "eventual_valid": valid,
        "first_pass_valid": first_pass,
        "failure_codes": codes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=10)
    parser.add_argument("--cells", default="A,B,C,D")
    args = parser.parse_args()

    results = []
    for key in [c.strip() for c in args.cells.split(",") if c.strip()]:
        label, reasoning, max_tokens, split = CELLS[key]
        print(f"\n=== CELL {key}: {label} ===", flush=True)
        results.append({"cell": key, **run_cell(label, reasoning, max_tokens, split, args.cases)})

    print("\n" + "=" * 78)
    print(f"{'cell':5s} {'configuration':45s} {'valid':>7s} {'1st':>5s}  codes")
    for row in results:
        print(
            f"{row['cell']:5s} {row['label']:45s} "
            f"{row['eventual_valid']:>3d}/{row['cases']:<3d} "
            f"{row['first_pass_valid']:>5d}  {row['failure_codes'] or ''}"
        )
    (TRANCHE / "isolate_grounding_repair.json").write_text(
        json.dumps(results, indent=1, sort_keys=True) + "\n"
    )
    print(f"\nwritten: {TRANCHE / 'isolate_grounding_repair.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
