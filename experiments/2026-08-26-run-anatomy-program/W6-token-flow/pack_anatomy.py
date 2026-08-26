"""W6 — pack anatomy: what the prompt side of the bill was actually spent on.

Read-only.  Reads every provider call's PROMPT BLOB out of the committed
roots and splits it into the parts the renderer itself emitted, then sizes
each part with the allocator's own estimator.  Writes:

    PACK_ANATOMY.json      per-contract and per-section rollups, all roots
    PACK_SAMPLES.json      the sampled packs for the two priority roots
    PACK_GROWTH.json       mean pack size by cycle, per root

WHY THE BLOB AND NOT A LOGGED TABLE.  `AllocationResult.accounting()` in
`src/deepreason/packs/allocate.py` computes exactly the per-section table
this window wants -- target, allocated, per-section tokens, dropped flags,
mandatory overflow -- and NOTHING PERSISTS IT.  A search of every committed
root finds no `mandatory_overflow` and no `allocated_tokens` in any log,
object or blob.  So the section table is re-derived from the rendered
prompt, which the allocator emits as `## <section id>\\n<view>` blocks
joined by a blank line (`allocate_pack`, final loop).

WHAT THAT COSTS, STATED SO IT IS NOT MISTAKEN FOR EXACT.  A section the
allocator DROPPED leaves no header and no placeholder, so it is invisible
here (`DR-CON-packs-and-token-economy`, "NO SILENT CAPS").  This instrument
therefore reports what the model was SHOWN.  It cannot report what the
budget cut, and it does not guess.

THE UNIVERSAL SPLIT.  Every prompt, on every contract, has the same three
part shape, because `LLMAdapter._render_request` assembles it that way:

    role-preamble           the seat's standing instruction
    output-contract-schema  the line after "Respond with ONLY a JSON
                            object conforming to this JSON Schema"
    pack-body               everything the epistemic state contributed

Only the pack body varies with the run.  The first two are the harness's
fixed per-call toll, and separating them is the point: they are the tokens
a run pays merely to ask.

`batch-critic.v2` is NOT on the pack IR (`render_batch_crit_pack` clips
aggregately), so it has no `## ` sections at all.  Its three-part split is
still exact; its body is reported as one block and labelled as such rather
than being silently absent from the section table.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(PROGRAM, "..", ".."))

SCHEMA_CUE = "Respond with ONLY a JSON object conforming to this JSON Schema"

# Section id -> what kind of context it is.  The operator's question is
# "how much of this is protocol boilerplate vs evidence vs prior candidates
# vs criticism", so the kinds answer exactly that and nothing else.  Every
# id declared by `render_conj_pack` and `render_crit_pack` is assigned; an
# unseen id lands in "unassigned" loudly.
SECTION_KIND = {
    # the ask itself -- what the seat must return, and in what shape
    "output-contract": "protocol",
    "mandatory-interface": "protocol",
    "machine-evaluation-boundary": "protocol",
    "context-withheld": "protocol",
    # the frame -- the question and the commitments every answer faces
    "problem": "frame",
    "problem-context": "frame",
    "criteria": "frame",
    "target-commitments": "frame",
    # admitted evidence
    "citable-evidence-blocks": "evidence",
    "frozen-evidence-context": "evidence",
    "capability-result-context": "evidence",
    # what has already been said -- prior artifacts and their support
    "neighbourhood": "prior-candidates",
    "crossover": "prior-candidates",
    "target": "prior-candidates",
    "target-support-chain": "prior-candidates",
    "target-support-content": "prior-candidates",
    # criticism already standing, and the openings offered against it
    "standing-attacks": "criticism",
    "counterexample-recourse": "criticism",
    "premise-invitation": "criticism",
    # how to generate, rather than what is true
    "school-stance": "steering",
    "complement-directive": "steering",
    "diversity-specifications": "steering",
    "active-properties": "steering",
    "experimental-generation-context": "steering",
    "scratch-advisory-context": "steering",
    "frame-slice": "steering",
    "frame-crisis": "steering",
}


def approximate_tokens(text: str) -> int:
    """The allocator's own estimator, copied so the numbers are comparable.

    `src/deepreason/packs/allocate.py::approximate_tokens`.  Reproduced
    rather than imported so this instrument re-derives a budgeting decision
    with the same arithmetic that made it, and keeps doing so if the import
    surface moves.  The copy is asserted equal to the import at startup.
    """
    return max(1, (len(text) + 3) // 4)


def blob(root: str, ref: str) -> str | None:
    p = os.path.join(root, "blobs", ref[:2], ref)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def split_prompt(text: str) -> dict:
    """role-preamble / output-contract-schema / pack-body, then sections."""
    lines = text.split("\n")
    cue = next((i for i, l in enumerate(lines) if l.startswith(SCHEMA_CUE)), None)
    if cue is None:
        preamble, schema, body_start = "\n".join(lines), "", len(lines)
    else:
        preamble = "\n".join(lines[:cue])
        # the schema is the cue line plus every line up to the first blank
        end = cue + 1
        while end < len(lines) and lines[end].strip():
            end += 1
        schema = "\n".join(lines[cue:end])
        body_start = end
    body_lines = lines[body_start:]
    body = "\n".join(body_lines)

    sections: list[dict] = []
    cur_id, cur: list[str] = None, []
    lead: list[str] = []
    for line in body_lines:
        if line.startswith("## ") and len(line) > 3 and " " not in line[3:].strip():
            if cur_id is not None:
                sections.append({"id": cur_id, "text": "\n".join(cur)})
            cur_id, cur = line[3:].strip(), []
        elif cur_id is None:
            lead.append(line)
        else:
            cur.append(line)
    if cur_id is not None:
        sections.append({"id": cur_id, "text": "\n".join(cur)})

    out_sections = []
    for s in sections:
        out_sections.append({
            "id": s["id"],
            "kind": SECTION_KIND.get(s["id"], "unassigned"),
            "chars": len(s["text"]),
            "tokens_est": approximate_tokens(s["text"]),
        })
    unsectioned = "\n".join(lead).strip()
    return {
        "preamble_chars": len(preamble),
        "preamble_tokens_est": approximate_tokens(preamble),
        "schema_chars": len(schema),
        "schema_tokens_est": approximate_tokens(schema),
        "body_chars": len(body),
        "body_tokens_est": approximate_tokens(body),
        "sectioned": bool(out_sections),
        "sections": out_sections,
        "unsectioned_body_chars": len(unsectioned),
        "unsectioned_body_tokens_est": approximate_tokens(unsectioned) if unsectioned else 0,
        "total_chars": len(text),
        "total_tokens_est": approximate_tokens(text),
    }


def main() -> int:
    from deepreason.packs.allocate import approximate_tokens as upstream
    for probe in ("", "x", "x" * 4001, "y" * 12345):
        assert upstream(probe) == approximate_tokens(probe), (
            "the copied estimator no longer matches "
            "deepreason.packs.allocate.approximate_tokens"
        )

    rows = [json.loads(l) for l in open(os.path.join(HERE, "FLOW_CALLS.jsonl"))]
    by_root: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_root[r["root"]].append(r)

    # the prompt_ref lives on the log event, not on the flow row; index it
    prompt_ref: dict[tuple[str, int], str] = {}
    for root in by_root:
        for line in open(os.path.join(REPO, root, "log.jsonl")):
            e = json.loads(line)
            if e.get("llm"):
                prompt_ref[(root, e["seq"])] = e["llm"]["prompt_ref"]

    per_call: list[dict] = []
    missing = 0
    for root, rs in by_root.items():
        abs_root = os.path.join(REPO, root)
        for r in rs:
            ref = prompt_ref.get((root, r["seq"]))
            text = blob(abs_root, ref) if ref else None
            if text is None:
                missing += 1
                continue
            an = split_prompt(text)
            per_call.append({
                "root": root, "seq": r["seq"], "cycle": r["cycle"],
                "contract_id": r["contract_id"], "purpose_detail": r["purpose_detail"],
                "call_kind": r["call_kind"], "role": r["role"], "seat": r["seat"],
                "provider_prompt_tokens": r["prompt_tokens"],
                "provider_completion_tokens": r["completion_tokens"],
                **an,
            })

    # per-contract rollup: where the prompt-side bill goes, part by part
    by_contract: dict[str, dict] = {}
    for c in per_call:
        a = by_contract.setdefault(c["contract_id"], {
            "calls": 0, "preamble_tokens_est": 0, "schema_tokens_est": 0,
            "body_tokens_est": 0, "total_tokens_est": 0,
            "provider_prompt_tokens": 0, "sectioned_calls": 0,
        })
        a["calls"] += 1
        a["sectioned_calls"] += 1 if c["sectioned"] else 0
        for k in ("preamble_tokens_est", "schema_tokens_est", "body_tokens_est",
                  "total_tokens_est"):
            a[k] += c[k]
        a["provider_prompt_tokens"] += c["provider_prompt_tokens"] or 0
    for cid, a in by_contract.items():
        t = a["total_tokens_est"] or 1
        a["preamble_share"] = round(a["preamble_tokens_est"] / t, 4)
        a["schema_share"] = round(a["schema_tokens_est"] / t, 4)
        a["body_share"] = round(a["body_tokens_est"] / t, 4)
        a["fixed_toll_share"] = round(
            (a["preamble_tokens_est"] + a["schema_tokens_est"]) / t, 4)
        a["estimator_vs_provider"] = (
            round(a["total_tokens_est"] / a["provider_prompt_tokens"], 4)
            if a["provider_prompt_tokens"] else None
        )
        a["mean_prompt_tokens_est_per_call"] = round(t / a["calls"], 1)

    # per-section rollup, over the IR packs only
    by_section: dict[str, dict] = {}
    by_kind: dict[str, dict] = {}
    for c in per_call:
        for s in c["sections"]:
            a = by_section.setdefault(s["id"], {"kind": s["kind"], "appearances": 0,
                                                "tokens_est": 0})
            a["appearances"] += 1
            a["tokens_est"] += s["tokens_est"]
            k = by_kind.setdefault(s["kind"], {"appearances": 0, "tokens_est": 0})
            k["appearances"] += 1
            k["tokens_est"] += s["tokens_est"]
    sect_total = sum(a["tokens_est"] for a in by_section.values()) or 1
    for a in by_section.values():
        a["share_of_sectioned_body"] = round(a["tokens_est"] / sect_total, 4)
        a["mean_tokens_est"] = round(a["tokens_est"] / a["appearances"], 1)
    for a in by_kind.values():
        a["share_of_sectioned_body"] = round(a["tokens_est"] / sect_total, 4)

    # growth: mean prompt size by cycle, per root and per contract
    growth: dict[str, dict] = {}
    for c in per_call:
        g = growth.setdefault(c["root"], {})
        key = f"{c['contract_id']}|cycle={c['cycle']}"
        a = g.setdefault(key, {"calls": 0, "prompt_tokens_est": 0,
                               "provider_prompt_tokens": 0, "body_tokens_est": 0})
        a["calls"] += 1
        a["prompt_tokens_est"] += c["total_tokens_est"]
        a["body_tokens_est"] += c["body_tokens_est"]
        a["provider_prompt_tokens"] += c["provider_prompt_tokens"] or 0
    for g in growth.values():
        for a in g.values():
            a["mean_prompt_tokens_est"] = round(a["prompt_tokens_est"] / a["calls"], 1)
            a["mean_body_tokens_est"] = round(a["body_tokens_est"] / a["calls"], 1)
            a["mean_provider_prompt_tokens"] = round(
                a["provider_prompt_tokens"] / a["calls"], 1)

    # the sampled packs, for the two priority roots, spread across cycles
    PRIORITY = [
        "experiments/2026-08-25-change-constructive-frontier/run",
        "experiments/2026-08-25-poietics-program/run",
    ]
    samples: dict[str, list[dict]] = {}
    for root in PRIORITY:
        calls = sorted([c for c in per_call if c["root"] == root],
                       key=lambda c: c["seq"])
        if not calls:
            continue
        # one per distinct cycle where possible, then fill by even spacing,
        # so the sample spans the run rather than clustering at its start
        picked: list[dict] = []
        seen_cycles: set = set()
        for c in calls:
            if c["cycle"] not in seen_cycles:
                seen_cycles.add(c["cycle"])
                picked.append(c)
        if len(picked) < 10:
            step = max(1, len(calls) // 10)
            for c in calls[::step]:
                if c not in picked:
                    picked.append(c)
        picked = sorted(picked, key=lambda c: c["seq"])[:16]
        samples[root] = picked

    json.dump({
        "schema": "run-anatomy.w6.pack-anatomy.v1",
        "regenerate": "python3 pack_anatomy.py  (after flow.py)",
        "calls_analysed": len(per_call),
        "prompt_blobs_missing": missing,
        "estimator": "deepreason.packs.allocate.approximate_tokens, (len+3)//4",
        "by_contract": dict(sorted(by_contract.items(),
                                   key=lambda kv: -kv[1]["total_tokens_est"])),
        "by_section": dict(sorted(by_section.items(),
                                  key=lambda kv: -kv[1]["tokens_est"])),
        "by_section_kind": dict(sorted(by_kind.items(),
                                       key=lambda kv: -kv[1]["tokens_est"])),
        "sectioned_calls": sum(1 for c in per_call if c["sectioned"]),
        "unsectioned_calls": sum(1 for c in per_call if not c["sectioned"]),
        "unsectioned_contracts": dict(Counter(
            c["contract_id"] for c in per_call if not c["sectioned"])),
    }, open(os.path.join(HERE, "PACK_ANATOMY.json"), "w"), indent=1)

    json.dump({
        "schema": "run-anatomy.w6.pack-growth.v1",
        "regenerate": "python3 pack_anatomy.py  (after flow.py)",
        "note": "cycle is assigned from progress.jsonl cumulative token marks; "
                "see flow.py::assign_cycle. A cycle one past the last mark is "
                "the tail the run never completed.",
        "roots": growth,
    }, open(os.path.join(HERE, "PACK_GROWTH.json"), "w"), indent=1)

    json.dump({
        "schema": "run-anatomy.w6.pack-samples.v1",
        "regenerate": "python3 pack_anatomy.py  (after flow.py)",
        "samples": samples,
    }, open(os.path.join(HERE, "PACK_SAMPLES.json"), "w"), indent=1)

    print(f"{len(per_call)} packs analysed, {missing} prompt blobs missing")
    print(f"sectioned: {sum(1 for c in per_call if c['sectioned'])}, "
          f"unsectioned: {sum(1 for c in per_call if not c['sectioned'])}")
    unassigned = by_kind.get("unassigned")
    if unassigned:
        print(f"WARNING: {unassigned['appearances']} section appearances unassigned")
    for root, picked in samples.items():
        print(f"  sampled {len(picked)} packs from {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
