"""Root-level proof, offline: a real managed-path run whose configuration names
no embedder model records WHY on its own log.

The soak (`scripts/cycle_soak.py`) drives the one run path against the
deterministic stub and produces a real root. It compiles its manifest from the
case's own config, so its runs carry whatever `EMBEDDER_MODEL` that config
carries — which is how a plain `--case pc1` soak comes out on the NEURAL
backend and is the control arm here. This driver reruns the same case with one
line changed in the copied config, `EMBEDDER_MODEL: null`, which is the exact
condition `preparation._config_for_profile` forces on every managed
`deepreason reason`. The run is otherwise identical: same case, same stub, same
cycles, same budget.

Run: python -u experiments/2026-09-09-neural-embedder-fallback/verify_root_level.py
Exit 0 = the treatment root carries the typed record and the control root does
not. Exit 1 = it does not.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import cycle_soak  # noqa: E402

_original_loopback = cycle_soak._loopback_config


def _drop_the_embedder(source, dest, port):
    """The copied config, plus the one line the managed path forces."""
    import yaml

    written = _original_loopback(source, dest, port)
    document = yaml.safe_load(written.read_text())
    document["EMBEDDER_MODEL"] = None
    written.write_text(yaml.safe_dump(document, sort_keys=True))
    return written


def embedder_facts(root: Path) -> dict:
    from deepreason.application.results import embedder_line, embedder_summary_for_root

    summary = embedder_summary_for_root(root)
    stamps = []
    for line in (root / "log.jsonl").read_text().splitlines():
        event = json.loads(line)
        inputs = [str(v) for v in (event.get("inputs") or ())]
        if inputs and inputs[0].startswith("embedder"):
            stamps.append(inputs)
    return {"summary": summary, "stamps": stamps, "line": embedder_line(summary)}


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dr-embedder-verify")

    print("=" * 72)
    print("TREATMENT — the arms' condition: no embedder model in the config")
    print("=" * 72)
    cycle_soak._loopback_config = _drop_the_embedder
    try:
        rc = cycle_soak.main(
            ["--case", "pc1", "--cycles", "2", "--token-budget", "200000",
             "--out", str(out / "treatment"), "--keep"]
        )
    finally:
        cycle_soak._loopback_config = _original_loopback
    print(f"[soak exit {rc}; A4-cycles-reached fails at --cycles 2 by design]")

    facts = embedder_facts(out / "treatment" / "run")
    print()
    for stamp in facts["stamps"]:
        print("  record :", stamp[0])
        for field in stamp[1:]:
            print("         :", field)
    print("  results:", facts["line"])

    said = [s for s in facts["stamps"] if s[0] == "embedder-unconfigured"]
    stamped = [s for s in facts["stamps"] if s[0] == "embedder"]

    ok = True
    if len(said) != 1:
        print("\n  >> FAIL: expected exactly one embedder-unconfigured record, "
              f"found {len(said)}")
        ok = False
    elif said[0][1] != "nomic-ai/nomic-embed-text-v1.5" or not said[0][2]:
        print("\n  >> FAIL: the record does not name the model and the cause")
        ok = False
    if not stamped or not stamped[-1][1].startswith("hashing"):
        print("\n  >> FAIL: the run did not measure on the hashing scale")
        ok = False
    if ok:
        print("\n  >> the root says which scale it measured on AND why.")

    print()
    print("=" * 72)
    print("CONTROL — the same case unchanged, whose config keeps its model")
    print("=" * 72)
    rc = cycle_soak.main(
        ["--case", "pc1", "--cycles", "2", "--token-budget", "200000",
         "--out", str(out / "control"), "--keep"]
    )
    print(f"[soak exit {rc}; same A4 by design]")
    control = embedder_facts(out / "control" / "run")
    print()
    for stamp in control["stamps"]:
        print("  record :", stamp[0])
        for field in stamp[1:]:
            print("         :", field)
    print("  results:", control["line"])

    noise = [s for s in control["stamps"] if s[0] == "embedder-unconfigured"]
    if noise:
        print("\n  >> FAIL: a run that GOT its embedder must record no cause")
        ok = False
    elif control["summary"]["backend"] != "neural":
        print("\n  >> FAIL: the control did not reach the neural backend, so it "
              "is not a control for this comparison")
        ok = False
    else:
        print("\n  >> a run that got what it asked for records nothing extra.")

    print()
    print("=" * 72)
    print(f"VERDICT: {'PASS' if ok else 'FAIL'}")
    print("=" * 72)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
