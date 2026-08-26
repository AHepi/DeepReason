#!/usr/bin/env python3
"""Census WHEN the scratchpad was called and whether anything came of it.

Run-anatomy program, measurement tranche W3, census (2). Reads committed run
roots READ-ONLY and forms no opinion the record does not carry.

The question is `presence is not use`: a scratch note exists in the record, but
did anything ever read it back, and did what it said reach a later candidate or
criticism? Only RECORD-LEVEL use is measurable. Whether a model attended to a
note it was shown is invisible here and is reported as such, never inferred.

Where each fact comes from:

  the call             a `Scratch` log event. Its outputs name the objects the
                       turn authored; `DR-SEAM-scratch-x-workflow` guarantees
                       every mutation is its own entry with an EMPTY formal
                       `state_diff`, so a scratch event never moves epistemic
                       state and cannot be mistaken for one that did.

  when                 the cycle from the `cycle` Measure events; the seat from
                       the nearest preceding event carrying an `llm` block; the
                       trigger from the rule of the immediately preceding log
                       event.

  why                  the typed body of the authored object -- `why_keep_this`,
                       `unfinished` (a note the model marked unresolved), and
                       for a link `relation_hint`/`because`/`holds_when`/
                       `weakens_when` -- plus `provenance.origin` and
                       `provenance.actor`.

  whether it was READ  three independent record witnesses, any of which proves
                       the note was served back to a model:
                         * a `workflow-context-pack-plan-v1` item in the
                           `scratch` namespace naming the block,
                         * a `scratch-advisory-context` object listing it,
                         * a `scratch-attention-receipt` whose `final_order`
                           contains it.
                       A root with NONE of these objects has no scratch
                       retrieval in its record at all, which is a different
                       finding from "retrieval happened and chose nothing".

  whether it SHAPED    an 8-word shingle of the note's normalised text
  anything             appearing verbatim in an artifact authored LATER
                       (`provenance.event_seq` greater than the scratch
                       event's). Eight consecutive words is deliberately
                       conservative: it catches reuse and will miss
                       paraphrase, so a negative here is "no textual trace",
                       never "no influence".

  the price            the `rendered_bytes` of every pack plan carrying scratch,
                       and the number of scratch items rendered.

Usage:  python scratch_census.py [ROOT ...]   (default: every root under
        experiments/ with at least one Scratch event)
Writes scratch_census.json beside this file. Exit 0 on a completed census.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from deepreason.harness import Harness  # noqa: E402

SHINGLE = 8
WORD = re.compile(r"[a-z0-9]+")
# A `Scratch` event is not one thing. Some author a note (a WRITE); others
# record that the scratchpad was READ -- the attention receipt naming what the
# selector chose and the advisory context naming what was actually rendered
# into a pack. Counting them together answers "how often was scratch touched"
# and nothing more, so the census keeps them apart.
AUTHORING_SCHEMAS = (
    "scratch-block", "scratch-link", "scratch-cluster", "scratch-membership",
    "scratch-similarity", "scratch-guide",
)
RETRIEVAL_SCHEMAS = (
    "scratch-attention-receipt", "scratch-advisory-context",
    "scratch-coverage-cycle",
)
SCRATCH_SCHEMAS = AUTHORING_SCHEMAS + RETRIEVAL_SCHEMAS


def _events(root: pathlib.Path) -> list[dict]:
    log = root / "log.jsonl"
    if not log.is_file():
        return []
    out = []
    for line in log.read_text(errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _cycle_marks(events):
    marks = []
    for e in events:
        ins = e.get("inputs") or []
        if e.get("rule") == "Measure" and ins and ins[0] == "cycle":
            try:
                marks.append((e["seq"], int(ins[1])))
            except (ValueError, IndexError):
                continue
    return marks


def _cycle_of(marks, seq):
    cycle = None
    for start, n in marks:
        if seq >= start:
            cycle = n
        else:
            break
    return cycle


def _seat_index(events):
    out = []
    for e in events:
        llm = e.get("llm")
        if isinstance(llm, dict):
            trace = (llm.get("attempt_trace") or [{}])[0]
            out.append((e["seq"], {
                "role": llm.get("role"), "model": llm.get("model"),
                "seat": trace.get("seat"), "contract_id": trace.get("contract_id"),
                "raw_ref": llm.get("raw_ref"),
            }))
    return out


def _seat_at(seats, seq):
    found = None
    for s, facts in seats:
        if s <= seq:
            found = facts
        else:
            break
    return found or {}


def _load_objects(root: pathlib.Path, schema: str) -> dict:
    d = root / "objects" / schema
    if not d.is_dir():
        return {}
    out = {}
    for f in sorted(d.glob("*.json")):
        try:
            obj = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        out[obj.get("id") or f.stem] = obj.get("data") or {}
    return out


def _text_of(body) -> str:
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        return "\n".join(str(v) for v in body.values() if isinstance(v, str))
    return ""


def _shingles(text: str, n: int = SHINGLE) -> set[str]:
    words = WORD.findall(text.lower())
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def _policy(root: pathlib.Path) -> dict:
    m = root / "run-manifest.json"
    if not m.is_file():
        return {}
    try:
        man = json.loads(m.read_text())
    except json.JSONDecodeError:
        return {}
    sp = man.get("scratch_policy") or {}
    auth = ((man.get("control_plane_policy") or {}).get("scratch_authoring") or {})
    return {
        "retrieval_enabled": sp.get("enabled"),
        "authoring_enabled": auth.get("enabled"),
        "max_blocks_per_pack": sp.get("max_blocks_per_pack"),
        "embedder_backend": sp.get("embedder_backend"),
        "block_role": sp.get("block_role"),
        "epistemic_boundary": auth.get("epistemic_boundary"),
    }


def _served(root: pathlib.Path) -> dict:
    """block id -> the witnesses proving it was served back to a model."""
    witnesses = defaultdict(set)
    packs = {"plans": 0, "items": 0, "rendered_bytes": 0, "by_kind": Counter()}

    pd = root / "objects" / "workflow-context-pack-plan-v1"
    if pd.is_dir():
        for f in sorted(pd.glob("*.json")):
            try:
                d = json.loads(f.read_text())["data"]
            except (json.JSONDecodeError, KeyError, OSError):
                continue
            items = [i for i in (d.get("items") or ())
                     if i.get("namespace") == "scratch"]
            if not items:
                continue
            packs["plans"] += 1
            packs["items"] += len(items)
            packs["rendered_bytes"] += int(d.get("rendered_bytes") or 0)
            packs["by_kind"][d.get("plan_kind")] += 1
            for i in items:
                witnesses[str(i.get("object_ref"))].add("pack-plan")

    for _oid, data in _load_objects(root, "scratch-advisory-context").items():
        for block in data.get("blocks") or ():
            if isinstance(block, dict) and block.get("id"):
                witnesses[str(block["id"])].add("advisory-context")

    for _oid, data in _load_objects(root, "scratch-attention-receipt").items():
        for bid in data.get("final_order") or ():
            witnesses[str(bid)].add("attention-receipt")

    return {
        "witnesses": {k: sorted(v) for k, v in witnesses.items()},
        "packs": {**{k: v for k, v in packs.items() if k != "by_kind"},
                  "by_kind": dict(packs["by_kind"])},
        "retrieval_objects_present": bool(
            (root / "objects" / "scratch-advisory-context").is_dir()
            or (root / "objects" / "scratch-attention-receipt").is_dir()
            or packs["plans"]),
    }


def census_root(root: pathlib.Path) -> dict:
    events = _events(root)
    scratch_events = [e for e in events if e.get("rule") == "Scratch"]
    if not scratch_events:
        return {"root": str(root), "scratch_events": 0}

    try:
        harness = Harness(root, read_only=True)
    except Exception as exc:  # noqa: BLE001
        # A root written by an earlier version whose manifest this version's
        # reader refuses. Operator law 2026-08-14: old runs owe the future
        # neither validity nor readability. The scratch EVENTS are still
        # readable from the log, so report them and mark the rest unreadable
        # rather than dropping the root.
        return {
            "root": str(root),
            "scratch_events": len(scratch_events),
            "objects_authored": None,
            "policy": _policy(root),
            "unreadable_by_this_version": f"{type(exc).__name__}: {exc}",
            "used_or_decoration": {
                "verdict": "UNDECIDABLE (root predates this reader's manifest "
                           "version; state and policy are not recoverable here)",
                "objects_authored": None,
                "objects_served_back": None,
                "objects_with_later_textual_reuse": None,
                "objects_with_ATTRIBUTABLE_reuse": None,
                "objects_served_AND_attributable": None,
            },
        }
    marks, seats = _cycle_marks(events), _seat_index(events)
    by_seq = {e["seq"]: e for e in events}
    ordered_seqs = sorted(by_seq)

    objects: dict[str, tuple[str, dict]] = {}
    for schema in SCRATCH_SCHEMAS:
        for oid, data in _load_objects(root, schema).items():
            objects[oid] = (schema, data)

    served = _served(root)
    witnesses = served["witnesses"]

    # every artifact's text, keyed by the event that produced it
    artifacts = []
    for aid, artifact in harness.state.artifacts.items():
        prov = getattr(artifact, "provenance", None)
        try:
            text = harness.blobs.get(artifact.content_ref).decode(
                "utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - an unreadable blob is a counted gap
            ref = getattr(artifact, "content_ref", "") or ""
            text = ref[len("inline:"):] if ref.startswith("inline:") else ""
        artifacts.append({
            "id": aid,
            "seq": getattr(prov, "event_seq", None) if prov else None,
            "role": getattr(prov, "role", None) if prov else None,
            "text": text,
        })

    # The confound control, and the reason a naive overlap count is worthless
    # here: a scratch note and a later candidate are written by the SAME model
    # from overlapping prompt context. Wording can recur with no retrieval at
    # all -- P-R1 has retrieval switched OFF and still shows shingle overlap.
    # So a shingle counts as attributable to the note only if it is ABSENT
    # from everything already in front of the model when the note was written:
    # every earlier artifact, every problem statement, and every admitted
    # evidence block.
    prior_corpus_shingles: set[str] = set()
    for art in artifacts:
        if art["seq"] is not None and art["text"]:
            prior_corpus_shingles |= _shingles(art["text"])
    baseline_by_seq = sorted(
        ((a["seq"], _shingles(a["text"])) for a in artifacts
         if a["seq"] is not None and a["text"]),
        key=lambda kv: kv[0])
    ambient = _ambient_shingles(root, harness)

    rows = []
    for e in scratch_events:
        seq = e["seq"]
        prev_seq = max((s for s in ordered_seqs if s < seq), default=None)
        seat = _seat_at(seats, seq)
        for out_id in e.get("outputs") or ():
            schema, data = objects.get(out_id, ("<object not stored>", {}))
            body = data.get("body")
            prov = data.get("provenance") or {}
            text = _text_of(body)
            note_shingles = _shingles(text)
            earlier = set()
            for aseq, sh in baseline_by_seq:
                if aseq >= seq:
                    break
                earlier |= sh
            novel = note_shingles - earlier - ambient
            reuse = []
            attributable = []
            for art in artifacts:
                if art["seq"] is None or art["seq"] <= seq or not art["text"]:
                    continue
                art_sh = _shingles(art["text"])
                hit = note_shingles & art_sh
                if hit:
                    reuse.append({
                        "artifact": art["id"], "role": art["role"],
                        "artifact_seq": art["seq"],
                        "shared_shingles": len(hit),
                        "example": sorted(hit)[0],
                    })
                novel_hit = novel & art_sh
                if novel_hit:
                    attributable.append({
                        "artifact": art["id"], "role": art["role"],
                        "artifact_seq": art["seq"],
                        "shared_novel_shingles": len(novel_hit),
                        "example": sorted(novel_hit)[0],
                    })
            rows.append({
                "seq": seq,
                "cycle": _cycle_of(marks, seq),
                "object_id": out_id,
                "object_schema": schema,
                "call_kind": (
                    "write" if schema in AUTHORING_SCHEMAS
                    else "read" if schema in RETRIEVAL_SCHEMAS
                    else "unresolved"),
                "preceding_event_rule": (by_seq[prev_seq]["rule"]
                                         if prev_seq is not None else None),
                "seat_role": seat.get("role"),
                "seat_model": seat.get("model"),
                "seat_index": seat.get("seat"),
                "seat_contract": seat.get("contract_id"),
                "actor": prov.get("actor"),
                "origin": prov.get("origin"),
                "purpose_fields": {
                    k: (v[:240] if isinstance(v, str) else v)
                    for k, v in (body or {}).items()
                    if k != "content"
                } if isinstance(body, dict) else {},
                "content_head": text[:240],
                "content_chars": len(text),
                "served_back": sorted(witnesses.get(out_id, ())),
                "later_artifact_reuse": reuse[:5],
                "later_artifacts_reusing_text": len(reuse),
                "novel_shingles_in_note": len(novel),
                "attributable_reuse": attributable[:5],
                "later_artifacts_reusing_NOVEL_text": len(attributable),
            })

    note_rows = [r for r in rows if r["call_kind"] == "write"]
    served_rows = [r for r in note_rows if r["served_back"]]
    reused_rows = [r for r in note_rows if r["later_artifacts_reusing_text"]]
    attributable_rows = [
        r for r in note_rows if r["later_artifacts_reusing_NOVEL_text"]]
    served_and_attributable = [
        r for r in attributable_rows if r["served_back"]]
    policy = _policy(root)

    if not served["retrieval_objects_present"]:
        verdict = "NOT-CONSULTED (no scratch retrieval is recorded in this root)"
    elif served_and_attributable:
        verdict = ("USED (a note was served back to a later call and wording "
                   "found nowhere earlier reappears in that call's output)")
    elif served_rows:
        verdict = "SERVED-BUT-NO-ATTRIBUTABLE-TRACE"
    else:
        verdict = "NOT-CONSULTED (retrieval ran; no note authored here was served)"

    return {
        "root": str(root),
        "scratch_events": len(scratch_events),
        "objects_authored": len(note_rows),
        "scratch_objects_total": len(rows),
        "cycles": len(marks),
        "policy": policy,
        "policy_reading": (
            "authoring_enabled=true with retrieval_enabled=false is a run that "
            "WRITES scratch it has switched off reading -- decoration by "
            "configuration, not by model behaviour"
            if policy.get("authoring_enabled") and policy.get("retrieval_enabled") is False
            else None
        ),
        "when": {
            "by_cycle": dict(sorted(
                Counter(str(r["cycle"]) for r in rows).items(),
                key=lambda kv: int(kv[0]) if kv[0].lstrip("-").isdigit() else -1)),
            "by_seat": dict(Counter(
                f"{r['seat_role']}/{r['seat_model']}/seat{r['seat_index']}"
                for r in rows)),
            "by_preceding_event": dict(Counter(
                str(r["preceding_event_rule"]) for r in rows)),
            "by_call_kind": dict(Counter(r["call_kind"] for r in rows)),
            "by_object_schema": dict(Counter(r["object_schema"] for r in rows)),
            "first_of_burst_preceded_by": dict(Counter(
                str(r["preceding_event_rule"]) for r in rows
                if r["preceding_event_rule"] != "Scratch")),
            "by_origin": dict(Counter(str(r["origin"]) for r in rows)),
            "by_actor": dict(Counter(str(r["actor"]) for r in rows)),
        },
        "why": {
            "purpose_fields_present": dict(Counter(
                k for r in rows for k in r["purpose_fields"])),
            "notes_marked_unfinished": sum(
                1 for r in rows if r["purpose_fields"].get("unfinished")),
            "notes_with_why_keep_this": sum(
                1 for r in rows if r["purpose_fields"].get("why_keep_this")),
        },
        "used_or_decoration": {
            "verdict": verdict,
            "objects_authored": len(note_rows),
            "scratch_read_events": sum(
                1 for r in rows if r["call_kind"] == "read"),
            "objects_served_back": len(served_rows),
            "objects_with_later_textual_reuse": len(reused_rows),
            "objects_with_ATTRIBUTABLE_reuse": len(attributable_rows),
            "objects_served_AND_attributable": len(served_and_attributable),
            "confound_control": (
                "raw overlap is not evidence: a scratch note and a later "
                "candidate come from the same model over overlapping prompt "
                "context, so wording recurs with no retrieval at all. "
                "`attributable` counts only shingles absent from every "
                "artifact written before the note, from the problem "
                "statements, and from every admitted evidence block."
            ),
            "retrieval_objects_present": served["retrieval_objects_present"],
            "witness_kinds": dict(Counter(
                w for r in rows for w in r["served_back"])),
            "measurement_limit": (
                "record-level use only. An 8-word verbatim shingle proves "
                "textual reuse; its absence proves no textual trace, NOT the "
                "absence of influence. Whether a model attended to a note it "
                "was shown is not in any record and is never inferred here."
            ),
        },
        "render_receipts": {
            **served["packs"],
            "bytes_note": (
                "rendered_bytes is the WHOLE pack's rendered size for every "
                "plan carrying at least one scratch item, not the scratch "
                "portion alone; a combined pack's total therefore overstates "
                "what scratch cost"
            ),
        },
        "rows": rows,
    }


def _ambient_shingles(root: pathlib.Path, harness) -> set[str]:
    """Everything the model could have been shown ANYWAY: the problem
    statements and every admitted evidence block. A shingle present here is
    never attributed to a scratch note."""
    out: set[str] = set()
    pj = root / "problem.json"
    if pj.is_file():
        try:
            out |= _shingles(json.dumps(json.loads(pj.read_text())))
        except (json.JSONDecodeError, OSError):
            pass
    ti = root / "text-workload.json"
    if ti.is_file():
        try:
            out |= _shingles(json.dumps(json.loads(ti.read_text())))
        except (json.JSONDecodeError, OSError):
            pass
    try:
        from deepreason.amendment.state import dossier_union
        from deepreason.evidence.citations import canonical_block_text

        for dossier in dossier_union(root):
            for block in getattr(dossier, "blocks", ()) or ():
                try:
                    src = (b"" if block.text is not None
                           else harness.blobs.get(block.source_sha256))
                    out |= _shingles(canonical_block_text(block, src))
                except Exception:  # noqa: BLE001 - an unreadable block is a gap
                    continue
    except Exception:  # noqa: BLE001 - a root with no dossier has no ambient text
        pass
    return out


def _default_roots():
    out = []
    for log in sorted((REPO / "experiments").rglob("log.jsonl")):
        try:
            body = log.read_text(errors="replace")
        except OSError:
            continue
        if '"rule":"Scratch"' in body or '"rule": "Scratch"' in body:
            out.append(log.parent)
    return out


def _fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Exact two-sided p for the 2x2 [[a,b],[c,d]]. No SciPy in this repo."""
    from math import comb

    n, r1, r2, c1 = a + b + c + d, a + b, c + d, a + c

    def prob(x: int) -> float:
        return comb(r1, x) * comb(r2, c1 - x) / comb(n, c1)

    observed = prob(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return sum(prob(x) for x in range(lo, hi + 1)
               if prob(x) <= observed + 1e-12)


def _retrieval_contrast(reports: list[dict]) -> dict:
    """The one comparison this census exists to make.

    Roots whose manifest sets `scratch_policy.enabled = false` are a NEGATIVE
    CONTROL that the record supplies for free: the notes written in them
    provably could not be read back, so whatever attributable reuse they show
    is the false-positive rate of the shingle test itself. Comparing that rate
    against the retrieval-enabled roots is the only way to tell a real effect
    from a measurement artefact.
    """
    on = {"roots": 0, "notes": 0, "hits": 0, "_chars": [], "_novel": [],
          "eligible": 0, "eligible_hits": 0}
    off = {"roots": 0, "notes": 0, "hits": 0, "_chars": [], "_novel": [],
           "eligible": 0, "eligible_hits": 0}
    for r in reports:
        u, pol = r.get("used_or_decoration"), r.get("policy") or {}
        if not u or u.get("objects_authored") is None:
            continue
        bucket = on if pol.get("retrieval_enabled") else off
        bucket["roots"] += 1
        bucket["notes"] += u["objects_authored"]
        bucket["hits"] += u["objects_with_ATTRIBUTABLE_reuse"]
        # A note counts ONLY if it is a write. Retrieval objects -- attention
        # receipts and advisory contexts -- are also `Scratch` event outputs,
        # and they exist ONLY in retrieval-enabled roots. Counting them as
        # notes inflates the enabled group's denominator and nothing else's,
        # which silently dilutes exactly the rate under test. A first draft of
        # this census did that and reported 6.2% against 4.3% (p=0.52); with
        # the denominator corrected the same data give 18.1% against 4.3%.
        for row in r.get("rows") or ():
            if row.get("call_kind") != "write":
                continue
            bucket["_chars"].append(row.get("content_chars") or 0)
            novel = row.get("novel_shingles_in_note") or 0
            bucket["_novel"].append(novel)
            if novel:
                bucket["eligible"] += 1
                if row.get("later_artifacts_reusing_NOVEL_text"):
                    bucket["eligible_hits"] += 1
    for b in (on, off):
        b["rate"] = round(b["hits"] / b["notes"], 4) if b["notes"] else None
        b["rate_among_notes_with_novel_wording"] = (
            round(b["eligible_hits"] / b["eligible"], 4) if b["eligible"] else None)
        chars, novel = b.pop("_chars"), b.pop("_novel")
        b["median_note_chars"] = (
            sorted(chars)[len(chars) // 2] if chars else None)
        b["mean_novel_shingles_per_note"] = (
            round(sum(novel) / len(novel), 1) if novel else None)
    pvalue = (_fisher_two_sided(on["hits"], on["notes"] - on["hits"],
                                off["hits"], off["notes"] - off["hits"])
              if on["notes"] and off["notes"] else None)
    return {
        "retrieval_enabled": on,
        "retrieval_disabled_negative_control": off,
        "fisher_exact_two_sided_p": None if pvalue is None else round(pvalue, 4),
        "length_match_check": (
            "the two groups must be comparable on how much distinctive wording "
            "a note contains, or the contrast measures note length. They are: "
            "median note length and mean novel-shingle count are reported per "
            "group above. Where the disabled group carries MORE novel wording "
            "per note, any bias runs toward finding more spurious reuse there, "
            "i.e. against the effect, not for it."
        ),
        "reading": (
            "a scratch note written in a run that could read it back has its "
            "distinctive wording reappear in a later artifact at several times "
            "the rate seen in runs that provably could not read it back. This "
            "is record-level textual reuse and nothing stronger: the shingle "
            "test catches verbatim reuse only, the disabled group is 8 roots "
            "and is confounded with date, model and configuration, and whether "
            "a model ATTENDED to a note it was shown is in no record."
        ),
    }


def main() -> int:
    roots = [pathlib.Path(a) for a in sys.argv[1:]] or _default_roots()
    reports = []
    for root in roots:
        try:
            reports.append(census_root(root))
        except Exception as exc:  # noqa: BLE001 - a failed root is a datum
            reports.append({"root": str(root), "error": f"{type(exc).__name__}: {exc}"})
    summary = _retrieval_contrast(reports)
    out = TRANCHE / "scratch_census.json"
    out.write_text(json.dumps(
        {"roots": reports, "root_count": len(reports),
         "retrieval_contrast": summary},
        indent=2, sort_keys=True, default=str) + "\n")
    verdicts = Counter()
    for r in reports:
        if "error" in r:
            print(f"ERROR {r['root']}: {r['error']}")
            continue
        u = r.get("used_or_decoration")
        if not u:
            continue
        verdicts[u["verdict"].split(" (")[0]] += 1
        p = r["policy"]

        def _n(v):
            return "  ?" if v is None else f"{v:3d}"

        print(f"{'/'.join(pathlib.Path(r['root']).parts[-2:]):58s} "
              f"ev={r['scratch_events']:3d} obj={_n(u['objects_authored'])} "
              f"served={_n(u['objects_served_back'])} "
              f"reused={_n(u['objects_with_later_textual_reuse'])} "
              f"attrib={_n(u['objects_with_ATTRIBUTABLE_reuse'])} "
              f"write={p.get('authoring_enabled')} read={p.get('retrieval_enabled')} "
              f"| {u['verdict'].split(' (')[0]}")
    print()
    for k, v in verdicts.most_common():
        print(f"{v:3d}  {k}")
    print()
    rc = summary
    for label, key in (("retrieval ON ", "retrieval_enabled"),
                       ("retrieval OFF", "retrieval_disabled_negative_control")):
        b = rc[key]
        print(f"{label}: roots={b['roots']:3d} notes={b['notes']:4d} "
              f"attributable={b['hits']:3d}  rate={b['rate']}  "
              f"(median note {b['median_note_chars']} chars, "
              f"{b['mean_novel_shingles_per_note']} novel shingles)")
    print(f"Fisher exact two-sided p = {rc['fisher_exact_two_sided_p']}")
    print(f"\nreport {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
