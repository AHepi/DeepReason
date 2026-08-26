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

# The JSON Schema is located STRUCTURALLY, not by its cue sentence.  The
# cue varies by contract family -- "Respond with ONLY a JSON object
# conforming to this JSON Schema" on the v6 wire contracts, "Return ONLY one
# JSON value matching this closed schema:" on the compact atomic ones -- and
# an instrument keyed to one sentence silently mis-splits the other family.
# Sizing it wrong is not a rounding error: on the atomic contracts it put
# the entire prompt into the fixed toll and reported a body of zero.
# A repair re-ask is a DIFFERENT PROMPT FORM, not a pack with a note on it:
# it carries the model's own rejected JSON back verbatim under CURRENT JSON,
# plus a diagnostic envelope, and no pack at all.  Reporting it inside the
# packed-prompt tables would attribute its whole cost to "unsectioned body"
# and hide what the run is actually re-sending.
# There are TWO repair forms, and both return the model's own rejected
# output: the PATCH form ("CURRENT JSON:" + "DIAGNOSTIC ENVELOPE:", asking
# for one JSON-pointer operation) and the FULL-VALUE form ("INVALID JSON:",
# asking for the whole corrected object back).
REPAIR_CURRENT = "CURRENT JSON:"
REPAIR_ENVELOPE = "DIAGNOSTIC ENVELOPE:"
REPAIR_INVALID = "INVALID JSON:"

SCHEMA_MIN_CHARS = 100
SCHEMA_KEYS = {"$defs", "properties", "anyOf", "allOf", "type", "items"}

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


def find_schema_line(lines: list[str]) -> int | None:
    """Index of the line carrying the output contract's JSON Schema.

    Located by shape -- a long line that parses as a JSON object carrying
    schema keys -- so the split holds across every contract family in the
    inventory rather than only the one whose cue sentence was sampled first.
    """
    for i, line in enumerate(lines):
        t = line.strip()
        if len(t) < SCHEMA_MIN_CHARS or not t.startswith("{") or not t.endswith("}"):
            continue
        try:
            obj = json.loads(t)
        except ValueError:
            continue
        if isinstance(obj, dict) and SCHEMA_KEYS & set(obj):
            return i
    return None


def is_section_header(line: str) -> bool:
    """`## <section id>` exactly as `allocate_pack` emits it.

    A section id is one token: the allocator writes `f"## {section.id}"` and
    PackSection ids are slugs.  Requiring a single token keeps a Markdown
    heading inside quoted model content from being read as a section.
    """
    if not line.startswith("## "):
        return False
    rest = line[3:].strip()
    return bool(rest) and " " not in rest


def split_repair(lines: list[str]) -> dict | None:
    """The repair re-ask form: preamble, the rejected JSON, the envelope."""
    cur = next((i for i, l in enumerate(lines) if l.strip() == REPAIR_CURRENT), None)
    env = next((i for i, l in enumerate(lines) if l.strip() == REPAIR_ENVELOPE), None)
    if cur is None or env is None or env < cur:
        inv = next((i for i, l in enumerate(lines) if l.strip() == REPAIR_INVALID), None)
        if inv is None:
            return None
        preamble = "\n".join(lines[:inv])
        current = "\n".join(lines[inv + 1:])
        return {
            "repair_form": "full-value",
            "preamble_chars": len(preamble),
            "preamble_tokens_est": approximate_tokens(preamble) if preamble else 0,
            "returned_rejected_json_chars": len(current),
            "returned_rejected_json_tokens_est": approximate_tokens(current) if current else 0,
            "diagnostic_envelope_chars": 0,
            "diagnostic_envelope_tokens_est": 0,
        }
    preamble = "\n".join(lines[:cur])
    current = "\n".join(lines[cur + 1:env])
    envelope = "\n".join(lines[env + 1:])
    return {
        "repair_form": "patch",
        "preamble_chars": len(preamble),
        "preamble_tokens_est": approximate_tokens(preamble) if preamble else 0,
        "returned_rejected_json_chars": len(current),
        "returned_rejected_json_tokens_est": approximate_tokens(current) if current else 0,
        "diagnostic_envelope_chars": len(envelope),
        "diagnostic_envelope_tokens_est": approximate_tokens(envelope) if envelope else 0,
    }


def split_prompt(text: str) -> dict:
    """Four parts: preamble, schema, interstitial, then the `## ` sections.

    preamble + schema is the FIXED TOLL -- what the run pays merely to ask,
    before any of its own state is shown.  The interstitial is what sits
    between the schema and the pack (alias legends, a syntax example, an
    atomic-slot directive); it is neither toll nor state, so it is reported
    on its own rather than folded into either.
    """
    lines = text.split("\n")
    repair = split_repair(lines)
    if repair is not None:
        return {
            "prompt_form": "repair-patch",
            "schema_located": False,
            "sectioned": False,
            "sections": [],
            "preamble_chars": repair["preamble_chars"],
            "preamble_tokens_est": repair["preamble_tokens_est"],
            "schema_chars": 0,
            "schema_tokens_est": 0,
            "interstitial_chars": (repair["returned_rejected_json_chars"]
                                   + repair["diagnostic_envelope_chars"]),
            "interstitial_tokens_est": (repair["returned_rejected_json_tokens_est"]
                                        + repair["diagnostic_envelope_tokens_est"]),
            "body_chars": 0,
            "body_tokens_est": 0,
            "total_chars": len(text),
            "total_tokens_est": approximate_tokens(text),
            "repair_form": repair["repair_form"],
            **{k: v for k, v in repair.items()
               if k.startswith(("returned_", "diagnostic_"))},
        }
    sidx = find_schema_line(lines)
    if sidx is None:
        preamble, schema, after = "", "", lines
    else:
        preamble = "\n".join(lines[:sidx])
        schema = lines[sidx]
        after = lines[sidx + 1:]

    first_section = next((i for i, l in enumerate(after) if is_section_header(l)), None)
    if first_section is None:
        interstitial, body_lines = "\n".join(after), []
    else:
        interstitial = "\n".join(after[:first_section])
        body_lines = after[first_section:]

    sections: list[dict] = []
    cur_id: str | None = None
    cur: list[str] = []
    for line in body_lines:
        if is_section_header(line):
            if cur_id is not None:
                sections.append({"id": cur_id, "text": "\n".join(cur)})
            cur_id, cur = line[3:].strip(), []
        else:
            cur.append(line)
    if cur_id is not None:
        sections.append({"id": cur_id, "text": "\n".join(cur)})

    out_sections = [{
        "id": s["id"],
        "kind": SECTION_KIND.get(s["id"], "unassigned"),
        "chars": len(s["text"]),
        "tokens_est": approximate_tokens(s["text"]),
    } for s in sections]

    def tok(t: str) -> int:
        return approximate_tokens(t) if t else 0

    return {
        "prompt_form": "packed" if out_sections else "flat",
        "schema_located": sidx is not None,
        "preamble_chars": len(preamble),
        "preamble_tokens_est": tok(preamble),
        "schema_chars": len(schema),
        "schema_tokens_est": tok(schema),
        "interstitial_chars": len(interstitial),
        "interstitial_tokens_est": tok(interstitial),
        "body_chars": sum(s["chars"] for s in out_sections),
        "body_tokens_est": sum(s["tokens_est"] for s in out_sections),
        "sectioned": bool(out_sections),
        "sections": out_sections,
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
            "trigger_kind": r.get("trigger_kind"),
                "provider_prompt_tokens": r["prompt_tokens"],
                "provider_completion_tokens": r["completion_tokens"],
                **an,
            })

    # per-contract rollup: where the prompt-side bill goes, part by part
    by_contract: dict[str, dict] = {}
    for c in per_call:
        a = by_contract.setdefault(c["contract_id"], {
            "calls": 0, "preamble_tokens_est": 0, "schema_tokens_est": 0,
            "interstitial_tokens_est": 0, "body_tokens_est": 0,
            "total_tokens_est": 0, "provider_prompt_tokens": 0,
            "sectioned_calls": 0, "schema_located_calls": 0,
        })
        a["calls"] += 1
        a["sectioned_calls"] += 1 if c["sectioned"] else 0
        a["schema_located_calls"] += 1 if c["schema_located"] else 0
        for k in ("preamble_tokens_est", "schema_tokens_est",
                  "interstitial_tokens_est", "body_tokens_est",
                  "total_tokens_est"):
            a[k] += c[k]
        a["provider_prompt_tokens"] += c["provider_prompt_tokens"] or 0
    for cid, a in by_contract.items():
        t = a["total_tokens_est"] or 1
        a["preamble_share"] = round(a["preamble_tokens_est"] / t, 4)
        a["schema_share"] = round(a["schema_tokens_est"] / t, 4)
        a["interstitial_share"] = round(a["interstitial_tokens_est"] / t, 4)
        a["body_share"] = round(a["body_tokens_est"] / t, 4)
        a["fixed_toll_share"] = round(
            (a["preamble_tokens_est"] + a["schema_tokens_est"]) / t, 4)
        a["estimator_vs_provider"] = (
            round(a["total_tokens_est"] / a["provider_prompt_tokens"], 4)
            if a["provider_prompt_tokens"] else None
        )
        a["mean_prompt_tokens_est_per_call"] = round(t / a["calls"], 1)

    # per-contract-AND-FORM rollup.  Mixing a contract's packed calls with
    # its repair re-asks averages two different prompts into one that does
    # not exist: the packed form is mostly schema, the repair form has no
    # schema at all.  The shares only mean something split.
    by_contract_form: dict[str, dict] = {}
    for c in per_call:
        k = f"{c['contract_id']} | {c['prompt_form']}"
        a = by_contract_form.setdefault(k, {
            "calls": 0, "preamble_tokens_est": 0, "schema_tokens_est": 0,
            "interstitial_tokens_est": 0, "body_tokens_est": 0,
            "total_tokens_est": 0, "provider_prompt_tokens": 0,
        })
        a["calls"] += 1
        for f in ("preamble_tokens_est", "schema_tokens_est",
                  "interstitial_tokens_est", "body_tokens_est",
                  "total_tokens_est"):
            a[f] += c[f]
        a["provider_prompt_tokens"] += c["provider_prompt_tokens"] or 0
    for a in by_contract_form.values():
        t = a["total_tokens_est"] or 1
        a["preamble_share"] = round(a["preamble_tokens_est"] / t, 4)
        a["schema_share"] = round(a["schema_tokens_est"] / t, 4)
        a["interstitial_share"] = round(a["interstitial_tokens_est"] / t, 4)
        a["body_share"] = round(a["body_tokens_est"] / t, 4)
        a["fixed_toll_share"] = round(
            (a["preamble_tokens_est"] + a["schema_tokens_est"]) / t, 4)
        a["mean_prompt_tokens_est_per_call"] = round(t / a["calls"], 1)
        a["mean_provider_prompt_tokens_per_call"] = round(
            a["provider_prompt_tokens"] / a["calls"], 1)

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
        # split by prompt form: a cycle that mixes packed first asks with
        # repair re-asks has a mean that describes neither, and the dip it
        # produces reads as a shrinking pack when nothing shrank
        key = f"{c['contract_id']}|{c['prompt_form']}|cycle={c['cycle']}"
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
        "by_contract_and_form": dict(sorted(
            by_contract_form.items(), key=lambda kv: -kv[1]["total_tokens_est"])),
        "by_section": dict(sorted(by_section.items(),
                                  key=lambda kv: -kv[1]["tokens_est"])),
        "by_section_kind": dict(sorted(by_kind.items(),
                                       key=lambda kv: -kv[1]["tokens_est"])),
        "sectioned_calls": sum(1 for c in per_call if c["sectioned"]),
        "unsectioned_calls": sum(1 for c in per_call if not c["sectioned"]),
        "unsectioned_contracts": dict(Counter(
            c["contract_id"] for c in per_call if not c["sectioned"])),
        "by_prompt_form": {
            form: {
                "calls": sum(1 for c in per_call if c["prompt_form"] == form),
                "prompt_tokens_est": sum(c["total_tokens_est"] for c in per_call
                                         if c["prompt_form"] == form),
                "provider_prompt_tokens": sum(c["provider_prompt_tokens"] or 0
                                              for c in per_call
                                              if c["prompt_form"] == form),
            }
            for form in ("packed", "flat", "repair-patch")
        },
        "repair_prompts": {
            "calls": sum(1 for c in per_call if c["prompt_form"] == "repair-patch"),
            "returned_rejected_json_tokens_est": sum(
                c.get("returned_rejected_json_tokens_est", 0) for c in per_call),
            "diagnostic_envelope_tokens_est": sum(
                c.get("diagnostic_envelope_tokens_est", 0) for c in per_call),
            "provider_prompt_tokens": sum(
                c["provider_prompt_tokens"] or 0 for c in per_call
                if c["prompt_form"] == "repair-patch"),
            "by_contract": dict(Counter(
                c["contract_id"] for c in per_call
                if c["prompt_form"] == "repair-patch")),
            "by_repair_form": dict(Counter(
                c.get("repair_form") for c in per_call
                if c["prompt_form"] == "repair-patch")),
            "note": "a repair re-ask sends the model its own rejected JSON "
                    "back verbatim plus a diagnostic envelope, and no pack",
        },
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
