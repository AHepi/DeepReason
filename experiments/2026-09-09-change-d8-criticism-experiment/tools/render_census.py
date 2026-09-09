#!/usr/bin/env python3
"""Did criticism actually REACH the seat that writes the next candidate? — R6, R9.

    python render_census.py <root> [<root> ...] [--section dr.open-criticisms]

This is the check the 2026-09-08 audit's §2.3a makes unavoidable. Criticism that
is recorded and routed nowhere does no causal work, and in the two roots that
audit examined **0 of 196 model-written attacks were ever exposed to a later
conjecture dispatch** — so every earlier statement about what criticism achieved
was a statement about criticism that could not have achieved anything.

PLANNED IS NOT RENDERED, and the distinction is the whole point of reading the
receipts rather than the configuration. Each `workflow-context-section-plan-v1`
record carries, per section, a `plugin_id`, a `disposition` and a
`rendered_bytes`. A section can be NAMED in a plan and still be dropped by the
allocator or render empty. Counting plans that merely mention the plugin would
report a channel as live while it carried nothing — which is exactly the failure
mode this census exists to detect, so it reports both numbers and never one.

Reads every root READ-ONLY: a writable open repairs, i.e. destroys, a record.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

PLANS = "workflow-context-section-plan-v1"
DEFAULT_SECTION = "dr.open-criticisms"


def census_one(root: pathlib.Path, plugin_id: str) -> dict:
    directory = root / "objects" / PLANS
    if not directory.is_dir():
        return {"root": str(root), "plans": 0, "named": 0, "rendered": 0,
                "rendered_bytes_total": 0, "dispositions": {},
                "why": f"no {PLANS} records in this root"}
    plans = named = rendered = total_bytes = 0
    dispositions: collections.Counter = collections.Counter()
    layouts: collections.Counter = collections.Counter()
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        data = payload.get("data", payload)
        plans += 1
        layouts[str(data.get("layout_id"))] += 1
        for section in data.get("sections") or ():
            if section.get("plugin_id") != plugin_id:
                continue
            named += 1
            disposition = str(section.get("disposition"))
            dispositions[disposition] += 1
            # RENDERED means both: the disposition says so AND bytes actually
            # went out. Either alone can be true while the seat saw nothing.
            byte_count = int(section.get("rendered_bytes") or 0)
            if disposition == "rendered" and byte_count > 0:
                rendered += 1
                total_bytes += byte_count
    return {
        "root": str(root), "plans": plans, "named": named, "rendered": rendered,
        "rendered_bytes_total": total_bytes,
        "dispositions": dict(dispositions),
        "layouts": dict(layouts),
        "reached_the_next_candidate": rendered > 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("roots", nargs="+")
    ap.add_argument("--section", default=DEFAULT_SECTION)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rows = [census_one(pathlib.Path(r).resolve(), args.section) for r in args.roots]
    print(f"| Root | plans | plans NAMING {args.section} | plans where it RENDERED | bytes |")
    print("|---|---|---|---|---|")
    for row in rows:
        print(f"| {pathlib.Path(row['root']).name} | {row['plans']} | {row['named']} | "
              f"**{row['rendered']}** | {row['rendered_bytes_total']} |")
    print()
    print("The RENDERED column is the load-bearing one: a section can be named in "
          "a plan and dropped by the allocator or render empty, and a census "
          "counting names would report a channel as live while it carried nothing.")
    for row in rows:
        if row.get("dispositions"):
            print(f"  {pathlib.Path(row['root']).name} dispositions: {row['dispositions']}")
        if row.get("why"):
            print(f"  {pathlib.Path(row['root']).name}: {row['why']}")
    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps({"schema": "render-census.v1", "section": args.section,
                        "rows": rows}, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
    return 0 if all(r["reached_the_next_candidate"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
