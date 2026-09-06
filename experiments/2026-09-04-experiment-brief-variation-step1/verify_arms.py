"""Did each arm's brief differ IN THE LIVE RUN? Ask the record, not the rig.

`prove_arms.py` proves the arms differ on committed golden fixtures, offline.
That is necessary and not sufficient: it says the rig CAN change a brief, not
that it DID change the brief the seats were actually shown. This reads the
runs' own typed section receipts and reports, per arm, which section plugins
rendered and how many bytes each contributed.

The receipts are `workflow-context-section-plan-v1` records, written per
conjecturer dispatch by the tranche that made the brief pluggable. They carry
`plugin_id`, `section_id`, `disposition` and `rendered_bytes`, so the question
"was A1 really shown history" is answered by counting records rather than by
trusting an environment variable.

WHAT WOULD MAKE AN ARM VOID, and it is worth stating before the numbers:
  * A1 with zero rendered `dr.history.v1` sections is A0 wearing A1's label.
  * A3 with zero rendered `op.neighbourhood.v1` sections is the same failure.
  * A0, A1P or A2 with ANY `dr.history.v1` rendered would mean the noise-floor
    arms are not identical after all, and PREREG §3.3's floor is void.

Usage:
    python verify_arms.py            # every retired root under roots/
    python verify_arms.py <root>...  # named roots
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
WATCHED = ("dr.history.v1", "dr.neighbourhood", "op.neighbourhood.v1",
           "dr.active-properties")


def receipts(root: pathlib.Path):
    directory = root / "objects" / "workflow-context-section-plan-v1"
    if not directory.is_dir():
        return
    for path in sorted(directory.rglob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - a record this cannot read is named
            print(f"  UNPARSEABLE {path}")
            continue
        payload = record.get("data", record)
        text = json.dumps(payload)
        # The sections list is nested differently per writer version, so the
        # entries are found by shape rather than by a fixed path.
        for entry in _sections(payload):
            yield entry
        del text


def _sections(payload):
    if isinstance(payload, dict):
        if "plugin_id" in payload and "disposition" in payload:
            yield payload
            return
        for value in payload.values():
            yield from _sections(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _sections(item)


def report(root: pathlib.Path, label: str) -> dict:
    rendered = collections.Counter()
    dropped = collections.Counter()
    byte_total = collections.Counter()
    for entry in receipts(root):
        plugin = entry.get("plugin_id", "?")
        if entry.get("disposition") == "rendered":
            rendered[plugin] += 1
            byte_total[plugin] += int(entry.get("rendered_bytes") or 0)
        else:
            dropped[plugin] += 1
    print(f"\n{label}  ({root.name})")
    if not rendered and not dropped:
        print("  NO SECTION RECEIPTS — this root cannot answer the question")
        return {}
    for plugin in WATCHED:
        mark = "rendered" if rendered[plugin] else "never rendered"
        print(
            f"  {plugin:<24} {mark:<15} n={rendered[plugin]:>4}  "
            f"bytes={byte_total[plugin]:>7}   dropped={dropped[plugin]}"
        )
    return {
        "rendered": dict(rendered),
        "bytes": dict(byte_total),
        "dropped": dict(dropped),
    }


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        roots = [(pathlib.Path(a), pathlib.Path(a).name) for a in argv[1:]]
    else:
        roots = [
            (path, path.name.split("-run-")[0])
            for path in sorted((HERE / "roots").glob("*-run-*"))
        ]
    if not roots:
        raise SystemExit("no roots under roots/; no arm has completed")
    print("ARM_RECEIPT_CENSUS_V1  (from the runs' own typed section receipts)")
    out = {arm: report(root, arm) for root, arm in roots}

    problems = []
    for arm, data in out.items():
        got = data.get("rendered", {})
        if arm == "A1" and not got.get("dr.history.v1"):
            problems.append("A1 rendered no history — it is A0 wearing A1's label")
        if arm == "A3" and not got.get("op.neighbourhood.v1"):
            problems.append("A3 rendered no operator template — same failure")
        if arm in ("A0", "A1P", "A2") and got.get("dr.history.v1"):
            problems.append(f"{arm} rendered history — the noise floor is void")
    print()
    if problems:
        for line in problems:
            print("VOID: " + line)
        return 1
    print("every arm's record agrees with the arm it was launched as.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
