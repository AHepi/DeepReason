#!/usr/bin/env python3
"""Analyse the STEP 1 arms — by CALLING the committed instruments.

`SPEC.md` S12.3 names four measures and says none is invented here. This
script therefore reimplements nothing: admission rate comes from this
directory's own `census_conjecturer_failures.py`, and M1/M2/M3 come from
`experiments/2026-08-28-diversity-generation/analyse.py`. A second
implementation of a measure is a second answer to the same question, and the
record would then have two numbers and no way to choose.

`--self-test` proves the wiring without any roots, so the instrument is
committed already known to work rather than debugged in the tranche that needs
it.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
DIVERSITY = REPO / "experiments" / "2026-08-28-diversity-generation" / "analyse.py"
CENSUS = HERE / "census_conjecturer_failures.py"

# Provenance, and therefore never shown to a judge (PREREG §7).
PROVENANCE_FIELDS = ("layout_id", "form_id", "shell_id", "arm", "plugin_id")


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blind(record: dict) -> dict:
    """Omit provenance ENTIRELY — never blank it.

    `docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` measured that a
    present-but-blank slot draws MORE attention than a filled one, so a
    blanking implementation would be worse than none.
    """

    return {k: v for k, v in record.items() if k not in PROVENANCE_FIELDS}


def survivors_only(roots: list[str]) -> dict[str, list[str]]:
    """Per root, the artifacts the record says came through something.

    `PREREG.md` §7 blinds provenance; this filter reads no provenance at all —
    only `DR-CON-evidence-states`, which is derived from attack edges, warrants
    and trial outcomes. It refuses rather than guesses if a root's reading
    cannot be built, because measuring the unfiltered pool under a
    survivors-only flag would report the wrong number under the right name.
    """
    from deepreason.harness import Harness
    from deepreason.views.evidence_states import EvidenceState, evidence_states

    kept: dict[str, list[str]] = {}
    for raw in roots:
        readings = evidence_states(Harness(pathlib.Path(raw), read_only=True))
        kept[raw] = sorted(
            aid for aid, reading in readings.items()
            if reading is EvidenceState.SUPPORTED
        )
    return kept


def self_test() -> int:
    assert CENSUS.exists(), CENSUS
    assert DIVERSITY.exists(), DIVERSITY
    # The committed instruments are importable, so the analysis will not
    # discover a broken dependency after the roots exist.
    for path, name in ((CENSUS, "census"), (DIVERSITY, "diversity")):
        assert _load(path, name) is not None, path
    blinded = blind({"claim": "x", "layout_id": "L", "form_id": "F", "arm": "A1"})
    assert blinded == {"claim": "x"}, blinded
    assert not set(blinded) & set(PROVENANCE_FIELDS)
    print("ok")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--roots", nargs="*", default=[])
    parser.add_argument(
        "--survivors-only", action="store_true",
        help="restrict to artifacts the record says came through an attack or "
             "a trial that ruled (DR-CON-evidence-states SUPPORTED), so the "
             "progress law's 'survivors' can be compared against B0 on "
             "survivors alone. Default OFF: without it this instrument behaves "
             "exactly as before",
    )
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return self_test()
    if not args.roots:
        raise SystemExit(
            "no roots. STEP 1 has not run: PREREG.md §8 says so, and this "
            "instrument does not invent numbers for arms that do not exist."
        )
    census = _load(CENSUS, "census")
    diversity = _load(DIVERSITY, "diversity")
    print(f"census: {census.__name__}, diversity: {diversity.__name__}")
    print(f"roots: {len(args.roots)}")
    if args.survivors_only:
        kept = survivors_only(args.roots)
        total = sum(len(ids) for ids in kept.values())
        print(f"survivors-only: {total} artifacts came through an attack or a "
              f"trial that ruled")
        for raw in args.roots:
            print(f"  {raw}: {len(kept[raw])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
