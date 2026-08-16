#!/usr/bin/env python3
"""The A/B probe that decides whether the builder or the tests are wrong.

Recompiles the grounded tranche's own configuration (its committed
``build_manifest.py``) three times and prints the digest chain each time:

    evidence_dossier_digest -> run_input_digest -> manifest_sha256

BASELINE   the working tree untouched
B-PROBE    one comment line appended to a map document that is NOT one of
           the configuration's six DOSSIER_PATHS
A-PROBE    the same line appended to ``docs/map/SUB-adjudication.md``,
           which IS one of them -- compiled twice, to separate "the input
           moved" from "compilation is non-deterministic"

Hypothesis (a) -- identity is a content address over declared inputs, the
builder is right and the tests pin a constant against mutable inputs --
predicts B-PROBE identical to BASELINE and A-PROBE different in all three
digests but equal to itself. Hypothesis (b) -- map bytes reach identity
through some undeclared path -- predicts B-PROBE differing from BASELINE.

Read-only with respect to git: both probe files are restored from the
bytes read before the edit, in a ``finally``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
GROUNDED = REPO / "experiments/2026-08-12-live-grounded-extension-expansion"

IN_DOSSIER = REPO / "docs/map/SUB-adjudication.md"
NOT_IN_DOSSIER = REPO / "docs/map/SUB-scheduler.md"
PROBE_LINE = b"\n<!-- diagnostic probe: appended by probe_digests.py -->\n"

KEYS = ("evidence_dossier_digest", "run_input_digest", "manifest_sha256")


def _builder():
    target = GROUNDED / "build_manifest.py"
    spec = importlib.util.spec_from_file_location("grounded_build_manifest", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _compile(builder) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        root.mkdir()
        summary = builder.build(root)
    return {key: summary[key] for key in KEYS}


def _show(label: str, digests: dict[str, str]) -> None:
    print(f"--- {label}")
    for key in KEYS:
        print(f"    {key:24s} {digests[key]}")


def _dossier_census() -> None:
    """The committed record's own claim about what the six sources are."""

    dossier = json.loads((GROUNDED / "run/evidence-dossier.json").read_text())
    recorded = {source["content_sha256"] for source in dossier["sources"]}
    builder = _builder()
    print("--- committed record vs live paths (evidence-dossier.json)")
    for path in builder.DOSSIER_PATHS:
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        verdict = "MATCH " if digest in recorded else "DIFFER"
        print(f"    {verdict} {digest[:16]}  {Path(path).relative_to(REPO)}")


def main() -> int:
    _dossier_census()
    builder = _builder()

    baseline = _compile(builder)
    _show("BASELINE (clean tree)", baseline)

    original = NOT_IN_DOSSIER.read_bytes()
    try:
        NOT_IN_DOSSIER.write_bytes(original + PROBE_LINE)
        b_probe = _compile(builder)
    finally:
        NOT_IN_DOSSIER.write_bytes(original)
    _show(f"B-PROBE (edited {NOT_IN_DOSSIER.name}, NOT in dossier)", b_probe)

    original = IN_DOSSIER.read_bytes()
    try:
        IN_DOSSIER.write_bytes(original + PROBE_LINE)
        a_probe = _compile(builder)
        a_probe_again = _compile(builder)
    finally:
        IN_DOSSIER.write_bytes(original)
    _show(f"A-PROBE (edited {IN_DOSSIER.name}, IN dossier)", a_probe)
    _show("A-PROBE recompiled (determinism under the same input)", a_probe_again)

    b_moved = b_probe != baseline
    a_moved = a_probe != baseline
    deterministic = a_probe == a_probe_again
    print("--- verdict")
    print(f"    non-dossier edit moved identity : {b_moved}   (hypothesis (b) iff True)")
    print(f"    dossier edit moved identity     : {a_moved}")
    print(f"    determinism under fixed input   : {deterministic}")
    if not b_moved and a_moved and deterministic:
        print("    => hypothesis (a): identity consumes ONLY declared inputs.")
        return 0
    print("    => NOT hypothesis (a). Return to dr-diagnose.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
