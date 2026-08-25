"""W1 — aggregate the per-root form census into the tables W1 owes.

Reads only `census/*.json` (produced by `census.py`) and the program's
`ROOT_INVENTORY.json`. Writes `CENSUS_AGGREGATE.json` and the two markdown
tables. Nothing here re-reads a run root, so an aggregate can never disagree
with the per-root census it summarizes.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.dirname(HERE)
CENSUS = os.path.join(HERE, "census")

# experiments/2026-08-22-fix-repair-patch-transport landed at
# 2026-08-22T16:09:24+00:00 (commit 97a964583, "absorb lossless patch transport
# spellings so a readable answer never costs a repair grant").
#
# The cut is the COMMIT TIMESTAMP, not the day. Cutting by day puts the two
# runs that MOTIVATED the fix -- reach-rich epoch 1 and its successor, both of
# which ran that morning -- on the wrong side of it, and a pre-fix run counted
# as post-fix would say the fix failed when it had not yet been written.
LOSSLESS_FIX_TS = "2026-08-22T16:09:24+00:00"
LOSSLESS_FIX_COMMIT = "97a964583"


def load_all() -> list[dict]:
    docs = []
    for name in sorted(os.listdir(CENSUS)):
        if name.endswith(".json"):
            docs.append(json.load(open(os.path.join(CENSUS, name))))
    return docs


def rate(num: int, den: int):
    return round(num / den, 4) if den else None


def main() -> int:
    docs = load_all()
    rows = [r | {"_root": d["root"], "_first_ts": d["first_ts"]} for d in docs for r in d["rows"]]

    by_contract = defaultdict(lambda: Counter())
    by_model = defaultdict(lambda: Counter())
    by_role_seat = defaultdict(lambda: Counter())
    by_attempt_index = defaultdict(lambda: Counter())
    failure_classes = Counter()
    failure_by_contract_field = Counter()
    failure_class_by_contract = Counter()
    truncation_by_model = defaultdict(lambda: Counter())

    for r in rows:
        cid, model = r["contract_id"], r["model"]
        for bucket, key in (
            (by_contract, cid),
            (by_model, model),
            (by_role_seat, f"{r['role']}#seat{r['seat']}"),
            (by_attempt_index, r["attempt_index"]),
        ):
            b = bucket[key]
            b["attempts"] += 1
            b["valid"] += int(r["valid_on_arrival"])
            b["repair_scoped"] += int(r["is_repair"])
            b["truncated"] += int(r["truncated"])
            b["unnatural_stop"] += int(r["natural_stop"] is False)
        tm = truncation_by_model[model]
        tm["attempts"] += 1
        tm["truncated"] += int(r["truncated"])
        tm["unnatural_stop"] += int(r["natural_stop"] is False)
        for f in r["failures"]:
            failure_classes[f["class"]] += 1
            failure_class_by_contract[(cid, f["class"])] += 1
            if f["field"]:
                failure_by_contract_field[(cid, f["field"], f["class"])] += 1

    for bucket in (by_contract, by_model, by_role_seat, by_attempt_index):
        for _, b in bucket.items():
            b["validity_rate"] = rate(b["valid"], b["attempts"])

    # ---- coercion: fabricate-or-escape at reference fields ----
    escape_legal = fabricated = 0
    handle_kinds = Counter()
    escape_followups = Counter()
    for d in docs:
        escape_legal += d["coercion"]["escape_legal"]
        fabricated += d["coercion"]["fabricated_handle"]
        handle_kinds.update(d["coercion"]["handle_kinds"])
        escape_followups.update(d["escape_followups"])

    # ---- the lossless-spelling class, before and after its fix ----
    spelling_pre, spelling_post = Counter(), Counter()
    roots_pre, roots_post = [], []
    for d in docs:
        ts = d["first_ts"] or ""
        target = (spelling_pre, roots_pre) if ts < LOSSLESS_FIX_TS else (spelling_post, roots_post)
        target[0].update(d["lossless_spelling_pointers"])
        target[1].append({"root": d["root"], "first_ts": ts,
                          "hits": sum(d["lossless_spelling_pointers"].values())})

    # ---- content classes ----
    enumish: dict[str, Counter] = defaultdict(Counter)
    field_kinds: dict[str, Counter] = defaultdict(Counter)
    hedges: dict[str, Counter] = defaultdict(Counter)
    precision: dict[str, Counter] = defaultdict(Counter)
    wire_shapes = Counter()
    wire_by_contract: dict[str, Counter] = defaultdict(Counter)
    hedge_exemplars, prose_exemplars = [], []
    for d in docs:
        c = d["content"]
        for k, v in c["string_vocabularies"].items():
            enumish[k].update(v)
        for k, v in c["field_kinds"].items():
            field_kinds[k].update(v)
        for k, v in c["string_hedges"].items():
            hedges[k].update(v)
        for k, v in c["numeric_precision"].items():
            precision[k].update(v)
        wire_shapes.update(c["wire_shapes"])
        for k, v in c["wire_shapes_by_contract"].items():
            wire_by_contract[k].update(v)
        hedge_exemplars.extend(c["hedge_exemplars"])
        prose_exemplars.extend(
            e | {"root": d["root"]} for e in c["prose_wrapped_exemplars"]
        )

    # An enum-like field: few distinct values, observed often enough that the
    # small vocabulary is a property of the FIELD and not of a thin sample.
    enum_fields = {
        k: dict(v.most_common())
        for k, v in enumish.items()
        if len(v) <= 6 and sum(v.values()) >= 20 and "<<long>>" not in v
    }

    # ---- repair fights ----
    fights = [f | {"_root": d["root"]} for d in docs for f in d["repair_fights"]]
    fights_by_contract = defaultdict(lambda: Counter())
    ladder_lengths = Counter()
    on_target = Counter()
    for f in fights:
        # A ladder is named by the contract it STARTED on; a decomposition can
        # move it to the atomic contract mid-ladder, and both are recorded in
        # `contract_ids`.
        b = fights_by_contract[f["contract_ids"][0]]
        b["ladders"] += 1
        b["calls_consumed"] += f["calls_consumed"]
        b[f"terminal:{f['terminal_status']}"] += 1
        if len(set(f["contract_ids"])) > 1:
            b["decomposed_mid_ladder"] += 1
        grant = (f.get("grant") or {}).get("maximum_provider_calls")
        if grant and f["calls_consumed"] >= grant:
            b["hit_grant_ceiling"] += 1
        ladder_lengths[f["calls_consumed"]] += 1
        for t in f["patch_verdicts"]:
            if t is not None:
                on_target[str(t)] += 1

    total = len(rows)
    valid = sum(1 for r in rows if r["valid_on_arrival"])
    agg = {
        "schema": "run-anatomy.form-census.aggregate.v1",
        "roots": len(docs),
        "attempts": total,
        "valid_on_arrival": valid,
        "validity_rate": rate(valid, total),
        "repair_scoped_attempts": sum(1 for r in rows if r["is_repair"]),
        "second_or_later_attempts": sum(1 for r in rows if (r["attempt_index"] or 0) > 0),
        "truncated_attempts": sum(1 for r in rows if r["truncated"]),
        "unnatural_stop_attempts": sum(1 for r in rows if r["natural_stop"] is False),
        "by_contract": {k: dict(v) for k, v in sorted(by_contract.items())},
        "by_model": {k: dict(v) for k, v in sorted(by_model.items())},
        "by_role_seat": {k: dict(v) for k, v in sorted(by_role_seat.items())},
        "by_attempt_index": {str(k): dict(v) for k, v in sorted(by_attempt_index.items(), key=lambda x: x[0] or 0)},
        "failure_classes": dict(failure_classes.most_common()),
        "failure_class_by_contract": [
            {"contract_id": c, "class": k, "count": n}
            for (c, k), n in failure_class_by_contract.most_common()
        ],
        "failure_by_contract_field": [
            {"contract_id": c, "field": f, "class": k, "count": n}
            for (c, f, k), n in failure_by_contract_field.most_common(120)
        ],
        "coercion": {
            "definition": (
                "escape_legal: reference-field diagnostics where the record "
                "itself states omission or an unknown handle was legal. "
                "fabricated_handle: of those, the ones where the model "
                "supplied a handle the record classifies as `unknown` -- it "
                "invented a value it was explicitly told it did not need. "
                "This is PhantomFill's CFR made code-scorable on our own "
                "record: absence was the legal answer, so a supplied value is "
                "a coerced fabrication with no judge involved."
            ),
            "escape_legal": escape_legal,
            "fabricated_handle": fabricated,
            "coerced_fabrication_rate": rate(fabricated, escape_legal),
            "observed_handle_kinds": dict(handle_kinds.most_common()),
            "escape_utilization_next_attempt": dict(escape_followups.most_common()),
        },
        "lossless_spelling": {
            "fix_commit_ts": LOSSLESS_FIX_TS,
            "fix_commit": LOSSLESS_FIX_COMMIT,
            "fix_tranche": "experiments/2026-08-22-fix-repair-patch-transport",
            "before_fix": dict(spelling_pre.most_common()),
            "before_fix_total": sum(spelling_pre.values()),
            "after_fix": dict(spelling_post.most_common()),
            "after_fix_total": sum(spelling_post.values()),
            "roots_before": sorted(roots_pre, key=lambda r: -r["hits"])[:12],
            "roots_after": sorted(roots_post, key=lambda r: -r["hits"])[:12],
        },
        "content": {
            "wire_shapes": dict(wire_shapes.most_common()),
            "wire_shapes_by_contract": {k: dict(v.most_common()) for k, v in sorted(wire_by_contract.items())},
            "enum_like_fields": enum_fields,
            "field_kinds": {k: dict(v.most_common()) for k, v in sorted(field_kinds.items())},
            "string_hedges": {k: dict(v.most_common()) for k, v in sorted(hedges.items())},
            "hedge_exemplars": hedge_exemplars[:60],
            "prose_wrapped_exemplars": prose_exemplars[:20],
            "numeric_precision": {
                k: dict(sorted(v.items(), key=lambda x: str(x[0])))
                for k, v in sorted(precision.items())
            },
        },
        "repair_fights": {
            "count": len(fights),
            "ladder_length_distribution": dict(sorted(ladder_lengths.items())),
            "calls_spent_in_ladders": sum(f["calls_consumed"] for f in fights),
            "repair_patch_verdicts": dict(on_target.most_common()),
            "by_contract": {k: dict(v) for k, v in sorted(fights_by_contract.items())},
        },
        "truncation_by_model": {k: dict(v) for k, v in sorted(truncation_by_model.items())},
    }

    with open(os.path.join(HERE, "CENSUS_AGGREGATE.json"), "w") as fh:
        json.dump(agg, fh, indent=1)
        fh.write("\n")

    write_tables(docs, agg)
    print(f"{len(docs)} roots, {total} attempts, {valid} valid ({agg['validity_rate']})")
    return 0


def write_tables(docs: list[dict], agg: dict) -> None:
    lines = [
        "# Per-root form census",
        "",
        "Machine-readable source: `CENSUS_PER_ROOT.json` and `census/<root>.json`.",
        "Re-derive with `python3 census.py && python3 aggregate.py`.",
        "",
        "`valid` counts attempts VALID ON ARRIVAL — the contract accepted the",
        "response as written, with no repair. `2nd+` counts attempts at workflow",
        "attempt index 1 or higher, i.e. calls the seat spent because an earlier",
        "call on the same work was not accepted. `cycle join` is `exact` only",
        "where the run recorded at least one completed cycle; where it is",
        "`none`, per-cycle numbers for that root must not be quoted.",
        "",
        "| root | run id | state / stop | attempts | valid | rate | 2nd+ | repair-scoped | trunc | cycle join |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for d in sorted(docs, key=lambda x: x["root"]):
        second = sum(1 for r in d["rows"] if (r["attempt_index"] or 0) > 0)
        lines.append(
            f"| `{d['root']}` | `{(d['run_id'] or '')[:16]}` | {d['state']} / {d['stop_reason']} "
            f"| {d['attempts']} | {d['valid_on_arrival']} | {d['validity_rate']} | {second} "
            f"| {d['repair_attempts']} | {d['truncated_attempts']} "
            f"| {'exact' if d['cycle_join_exact'] else 'none'} |"
        )
    with open(os.path.join(HERE, "PER_ROOT.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

    a = agg
    out = [
        "# Aggregate form census",
        "",
        f"Machine-readable source: `CENSUS_AGGREGATE.json`. "
        f"{a['roots']} roots, {a['attempts']} provider attempts.",
        "",
        "## Arrival validity by form (contract)",
        "",
        "| contract | attempts | valid on arrival | rate | repair-scoped | truncated |",
        "|---|---|---|---|---|---|",
    ]
    for cid, b in sorted(a["by_contract"].items(), key=lambda x: -x[1]["attempts"]):
        out.append(
            f"| `{cid}` | {b['attempts']} | {b['valid']} | {b['validity_rate']} "
            f"| {b['repair_scoped']} | {b['truncated']} |"
        )
    out += [
        "",
        "## Arrival validity by model",
        "",
        "| model | attempts | valid | rate | truncated | unnatural stop |",
        "|---|---|---|---|---|---|",
    ]
    for m, b in sorted(a["by_model"].items(), key=lambda x: -x[1]["attempts"]):
        out.append(
            f"| `{m}` | {b['attempts']} | {b['valid']} | {b['validity_rate']} "
            f"| {b['truncated']} | {b['unnatural_stop']} |"
        )
    out += [
        "",
        "## Arrival validity by role and seat instance",
        "",
        "| role#seat | attempts | valid | rate |",
        "|---|---|---|---|",
    ]
    for k, b in sorted(a["by_role_seat"].items(), key=lambda x: -x[1]["attempts"]):
        out.append(f"| `{k}` | {b['attempts']} | {b['valid']} | {b['validity_rate']} |")
    out += [
        "",
        "## What the seat spent its calls on",
        "",
        "| workflow attempt index | attempts | valid | rate |",
        "|---|---|---|---|",
    ]
    for k, b in a["by_attempt_index"].items():
        out.append(f"| {k} | {b['attempts']} | {b['valid']} | {b['validity_rate']} |")
    out += [
        "",
        "## How invalid arrivals failed",
        "",
        "Class names are the record's own diagnostic `code` wherever one exists.",
        "",
        "| failure class | count |",
        "|---|---|",
    ]
    for k, v in a["failure_classes"].items():
        out.append(f"| `{k}` | {v} |")
    out += [
        "",
        "## Which field failed, and how (top 40)",
        "",
        "| contract | field | class | count |",
        "|---|---|---|---|",
    ]
    for row in a["failure_by_contract_field"][:40]:
        out.append(
            f"| `{row['contract_id']}` | `{row['field'] or '(object-wide)'}` "
            f"| `{row['class']}` | {row['count']} |"
        )
    out += [
        "",
        "## How the JSON arrived",
        "",
        "| wire shape | count |",
        "|---|---|",
    ]
    for k, v in a["content"]["wire_shapes"].items():
        out.append(f"| `{k}` | {v} |")
    with open(os.path.join(HERE, "AGGREGATE.md"), "w") as fh:
        fh.write("\n".join(out) + "\n")


if __name__ == "__main__":
    sys.exit(main())
