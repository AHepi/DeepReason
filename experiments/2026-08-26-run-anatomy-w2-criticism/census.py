#!/usr/bin/env python3
"""W2 criticism census — the ONE instrument every number in RESULTS.md comes from.

GOAL.md dimensions 1-5.  Opens the root READ-ONLY (`dr-drive-harness` §5:
a writable open repairs, i.e. destroys, the evidence) and emits one record
per criticism DISPATCH and one per mechanical criticism EVENT, plus the
conjecture lineage in temporal order that the Q5 rates are measured over.

IT FORMS NO OPINION.  Every field is read from a typed record
(`log.jsonl`, `objects/`, `evidence-dossier.json`) or RE-DERIVED by the
harness's own evaluator, `deepreason.programs.evaluate`.  Where a
classification is a judgement, the rule that fired is written beside the
verdict so a reader can reject the rule without re-reading 207 criticisms.

THE LINKS ARE THE RECORD'S OWN, NOT ADJACENCY.
  * criticism -> target:   `workflow-work-preparation-v1.target_refs`
  * dispatch  -> what the model saw: `workflow-context-exposure-v2.exposed_items`
  * dispatch  -> what the model said: `workflow-provider-attempt-v1.raw_ref`
  * case text -> registered artifact: normalized-prefix match on the body
    (the registered artifact TRUNCATES a long case, so the match is a
    prefix match and its length is declared below, not tuned)
  * warrant   -> commitment/target:   `objects/warrant/`

`workflow-semantic-admission-v1.admitted_refs` is deliberately NOT used as
the dispatch->artifact link: in both priority roots those refs resolve to
nothing on disk (checked, 0 of 163 in P-R1), so joining on them would drop
every criticism.  That is recorded as a finding, not worked around silently.

Usage:  python census.py <root> <out.json>
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402

# A quoted span shorter than this is not evidence of quotation: "the",
# "1/9" and "condition" all occur in both texts by coincidence.  Declared,
# not tuned; there is deliberately no flag for it.
QUOTE_MIN = 30
# The registered criticism artifact truncates a long case body, so the case
# text is matched to it on a normalized prefix of this length.
PREFIX_MATCH = 120

# A straight apostrophe is a possessive far more often than a quotation
# mark ("the target's claim"), so a straight-single-quoted span counts only
# when the opener follows a boundary and the closer is not mid-word.  Read
# naively, `'` pairs turn every possessive into a bogus "misquote", which is
# the defect this pattern exists to avoid.
# The length floor is applied AFTER matching, never inside the pattern: a
# floor inside it forces the lazy quantifier past the real closing quote
# and manufactures 200-character "quotes" that span three real ones.
_QUOTE_RE = re.compile(
    r"(?<![\w’'])[‘']([^‘’\n]{1,300}?)['’](?![\w])"
    r"|[“\"]([^“”\"\n]{1,300}?)[”\"]"
)


_EDGE_PUNCT = " \t\n.,;:!?—–-\"'‘’“”()"


def _trim(s: str) -> str:
    """Edge punctuation is the critic's sentence, not the quotation: a critic
    that writes `... 'a clean 1-of-9 loss.'` has quoted accurately and put its
    own full stop inside the marks.  Counting that as a misquote measures
    typography."""
    return _norm(s).strip(_EDGE_PUNCT)


def _found_in(hay: str, quote: str) -> bool:
    """Is `quote` present in `hay`, allowing the elision a real quotation uses?
    `A ... B` is quoted accurately when A and B both occur, in that order.
    Requiring the ellipsis literally would count every properly elided
    quotation as a fabrication."""
    q = _trim(quote)
    if not q:
        return False
    if q in hay:
        return True
    parts = [_trim(x) for x in re.split(r"\s*(?:\.\.\.|…)\s*", q)]
    parts = [x for x in parts if len(x) >= 12]
    if len(parts) < 2:
        return False
    pos = 0
    for part in parts:
        hit = hay.find(part, pos)
        if hit < 0:
            return False
        pos = hit + len(part)
    return True


def _norm(s: str) -> str:
    """Whitespace-insensitive comparison: a critic that re-wraps a quote has
    not misquoted it, and a census that says otherwise measures line breaks."""
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _quotes(text: str) -> list[str]:
    out = []
    for m in _QUOTE_RE.finditer(text or ""):
        span = m.group(1) or m.group(2)
        if span and len(span) >= QUOTE_MIN:
            out.append(span)
    return out


def _strip_fence(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _load_objects(root: pathlib.Path, kind: str) -> list[dict]:
    d = root / "objects" / kind
    if not d.is_dir():
        return []
    return [json.load(p.open())["data"] for p in d.glob("*.json")]


def _dossier(root: pathlib.Path) -> dict:
    """Block id -> {text, title, source}.  Blocks carry a span into a source
    file, not a copy of their bytes, so the text is reconstructed and each
    reconstruction is confirmed against the block's own `text_sha256`.  A
    block whose text cannot be confirmed is reported as unreconstructed
    rather than quoted."""
    path = root / "evidence-dossier.json"
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text())
    sources: dict[str, pathlib.Path] = {}
    for cand in (root.parent / "record").rglob("*"):
        if cand.is_file():
            sources.setdefault(hashlib.sha256(cand.read_bytes()).hexdigest(), cand)
    out: dict[str, dict] = {}
    for b in doc.get("blocks", []):
        src = sources.get(b.get("source_sha256"))
        text = None
        if src is not None:
            try:
                raw = src.read_bytes()[b["span_start"]:b["span_end"]].decode("utf8")
                if hashlib.sha256(raw.encode()).hexdigest() == b.get("text_sha256"):
                    text = raw
            except Exception:  # noqa: BLE001 - an unreadable span is an absence
                text = None
        out[b["id"]] = {"text": text, "title": b.get("title"), "kind": b.get("kind")}
    return out


def census(root: pathlib.Path) -> dict:
    harness = Harness(root, read_only=True)
    state = harness.state

    text_of: dict[str, str] = {}
    role_of: dict[str, str] = {}
    for aid, art in state.artifacts.items():
        try:
            text_of[aid] = programs.content_text(art, harness.blobs)
        except Exception:  # noqa: BLE001
            text_of[aid] = ""
        role = str(getattr(getattr(art, "provenance", None), "role", "") or "")
        role_of[aid] = role.split(".")[-1].lower()

    status = {a: str(s).split(".")[-1].lower() for a, s in state.status.items()}
    att = {tuple(e) for e in state.att}
    warrants = dict(harness.warrants)
    commitments = dict(harness.commitments)
    dossier = _dossier(root)

    problem_doc = json.loads((root / "problem.json").read_text()) \
        if (root / "problem.json").is_file() else {}
    run_input = json.loads((root / "run-input.json").read_text()) \
        if (root / "run-input.json").is_file() else {}
    problem_hay = _norm(
        json.dumps(problem_doc, ensure_ascii=False) + " "
        + json.dumps(run_input, ensure_ascii=False)
    )

    events = [json.loads(l) for l in (root / "log.jsonl").read_text().splitlines() if l.strip()]
    # artifact id -> the seq of the event that first put it on the record
    first_seq: dict[str, int] = {}
    for ev in events:
        for out in ev.get("outputs", []):
            if isinstance(out, str) and not out.startswith(("w:", "sha256:")):
                first_seq.setdefault(out, ev["seq"])

    preps = {d["id"]: d for d in _load_objects(root, "workflow-work-preparation-v1")}
    exposures: dict[str, dict] = {}
    for d in _load_objects(root, "workflow-context-exposure-v2"):
        exposures[d["work_id"]] = d
    attempts: dict[str, list[dict]] = collections.defaultdict(list)
    for d in _load_objects(root, "workflow-provider-attempt-v1"):
        attempts[d["work_id"]].append(d)

    # normalized-prefix index over registered bodies, for case -> artifact
    prefix_index: dict[str, str] = {}
    for aid, body in text_of.items():
        key = _norm(body)[:PREFIX_MATCH]
        if key:
            prefix_index.setdefault(key, aid)

    dispatches = []
    for work_id, prep in sorted(preps.items()):
        if prep.get("task_kind") != "criticism":
            continue
        payload = prep.get("task_payload_value") or {}
        lease = prep.get("route_lease") or {}
        targets = list(prep.get("target_refs") or [])
        target = targets[0] if targets else None
        target_text = text_of.get(target) if target else None

        exposure = exposures.get(work_id) or {}
        items = exposure.get("exposed_items") or []
        exposed_refs = {it.get("object_ref") for it in items}
        exposed_aliases = {it.get("alias"): it.get("object_ref") for it in items}
        exposed_evidence_text = {
            it.get("object_ref"): (dossier.get(it.get("object_ref")) or {}).get("text")
            for it in items
            if it.get("namespace") == "evidence"
        }
        # every exposed item's body, whatever its namespace: a source item is
        # a registered artifact, an evidence item is a dossier block
        exposed_text = {
            it.get("object_ref"): (
                text_of.get(it.get("object_ref"))
                or (dossier.get(it.get("object_ref")) or {}).get("text")
            )
            for it in items
        }

        for attempt in sorted(attempts.get(work_id, []), key=lambda a: a.get("attempt_index", 0)):
            raw_ref = attempt.get("raw_ref")
            raw = ""
            if raw_ref:
                p = root / "blobs" / raw_ref[:2] / raw_ref
                if p.is_file():
                    raw = p.read_text()
            parsed: dict | None
            try:
                parsed = json.loads(_strip_fence(raw))
            except Exception:  # noqa: BLE001
                parsed = None

            base = {
                "work_id": work_id,
                "attempt_index": attempt.get("attempt_index"),
                "contract_id": prep.get("contract_id"),
                "dispatch_authority": payload.get("dispatch_authority"),
                "seat": lease.get("seat"),
                "seat_role": lease.get("role"),
                "endpoint": lease.get("endpoint_id"),
                "target": target,
                "target_role": role_of.get(target) if target else None,
                "target_status": status.get(target) if target else None,
                "n_exposed": len(items),
                "exposed_namespaces": dict(
                    collections.Counter(it.get("namespace") for it in items)
                ),
                "prompt_tokens": attempt.get("prompt_tokens"),
                "completion_tokens": attempt.get("completion_tokens"),
                "provider_outcome": attempt.get("outcome"),
            }
            if parsed is None:
                dispatches.append({**base, "outcome": "unparsed_reply",
                                   "raw_len": len(raw)})
                continue
            cases = parsed.get("cases") or []
            if not cases:
                dispatches.append({**base, "outcome": "no_case"})
                continue
            for case in cases:
                # the model spelled the key `preise` in three P-C1 replies;
                # both spellings are read, and which one was used is recorded
                premise = case.get("premise")
                premise_key = "premise"
                if premise in (None, "") and case.get("preise") not in (None, ""):
                    premise, premise_key = case.get("preise"), "preise"
                if not case.get("attack"):
                    dispatches.append({**base, "outcome": "declined",
                                       "target_alias": case.get("target_alias")})
                    continue
                case_text = case.get("case") or ""
                aid = prefix_index.get(_norm(case_text)[:PREFIX_MATCH])
                carried = []
                if aid is not None:
                    carried = [w for w in harness.carried_warrant_ids(aid)] \
                        if hasattr(harness, "carried_warrant_ids") else []

                # quotes OF THE TARGET, byte-checked against the target body
                hay = _norm(target_text or "")
                # A quote that misses the target is only a MISQUOTE if the
                # critic was quoting the target.  The problem statement and
                # every other exposed item are in the same prompt, so both
                # are checked before a miss is called a miss.
                qrows = []
                for q in _quotes(f"{case_text}\n{premise or ''}"):
                    nq = _norm(q)
                    qrows.append({
                        "quote": q,
                        "verbatim_in_target": nq in hay,
                        "trimmed_in_target": _found_in(hay, q),
                        "verbatim_in_problem": nq in problem_hay,
                        "trimmed_in_problem": _found_in(problem_hay, q),
                        "verbatim_in_any_exposed": any(
                            nq in _norm(t) for t in exposed_text.values() if t
                        ),
                        "trimmed_in_any_exposed": any(
                            _found_in(_norm(t), q) for t in exposed_text.values() if t
                        ),
                    })
                # evidence citations, byte-checked against the dossier AND
                # against what this dispatch was actually shown
                erows = []
                for e in (case.get("premise_evidence") or []):
                    ref = str(e.get("block") or "")
                    quote = e.get("quote") or ""
                    hit = None
                    if ref in dossier:
                        hit = ref
                    else:
                        cands = [b for b in dossier if b.startswith(ref)] if len(ref) >= 8 else []
                        hit = cands[0] if len(cands) == 1 else None
                    btext = (dossier.get(hit) or {}).get("text") if hit else None
                    erows.append({
                        "cited": ref,
                        "resolves_to_block": hit,
                        "in_dossier": hit is not None,
                        "was_exposed_to_this_dispatch": bool(hit and hit in exposed_refs),
                        "cited_ref_is_an_exposure_alias": ref in exposed_aliases,
                        "quote_verbatim_in_cited_block": (
                            bool(btext) and _norm(quote) in _norm(btext)
                        ) if hit else None,
                        "quote_verbatim_in_any_exposed_block": any(
                            t and _norm(quote) in _norm(t)
                            for t in exposed_evidence_text.values()
                        ),
                        "quote_verbatim_in_target": _norm(quote) in hay if quote else None,
                        "quote_verbatim_in_problem": (
                            _norm(quote) in problem_hay if quote else None
                        ),
                        "quote": quote,
                    })
                dispatches.append({
                    **base,
                    "outcome": "attack",
                    "target_alias": case.get("target_alias"),
                    "premise_key": premise_key,
                    "has_premise": bool(premise),
                    "has_counterexample": bool(case.get("counterexample")),
                    "case_len": len(case_text),
                    "case_text": case_text,
                    "premise_text": premise,
                    "registered_artifact": aid,
                    "registered": aid is not None,
                    "crit_seq": first_seq.get(aid) if aid else None,
                    "warrants_carried": carried,
                    "attacks_target_in_att": bool(aid and target and (aid, target) in att),
                    "quotes_of_target": qrows,
                    "evidence_citations": erows,
                })

    # Mechanical criticism: every Crit event that carried a warrant.  The
    # warrant's verdict is RE-DERIVED with the harness's own evaluator on
    # the target's own bytes; nothing here trusts the stored verdict.
    mechanical = []
    for ev in events:
        if ev.get("rule") != "Crit":
            continue
        wids = [o for o in ev["outputs"] if str(o).startswith("w:")]
        aids = [o for o in ev["outputs"] if not str(o).startswith("w:")]
        for wid in wids:
            w = warrants.get(wid)
            row: dict = {"seq": ev["seq"], "warrant": wid,
                         "crit_artifact": aids[0] if aids else None}
            if w is None:
                mechanical.append({**row, "row": "unverifiable",
                                   "why": "warrant id not registered"})
                continue
            kid = getattr(w, "commitment", None)
            k = commitments.get(kid) if kid else None
            tgt = state.artifacts.get(w.target)
            row.update({
                "commitment": kid,
                "target": w.target,
                "target_status": status.get(w.target),
                "warrant_type": str(getattr(w, "type", "")).split(".")[-1].lower(),
                "claimed_verdict": str(getattr(w, "verdict", "")).split(".")[-1].lower(),
                "attacks_target_in_att": bool(aids and (aids[0], w.target) in att),
            })
            if kid is None:
                mechanical.append({**row, "row": "unverifiable",
                                   "why": "warrant names no commitment"})
                continue
            if k is None:
                mechanical.append({**row, "row": "attacked-nonexistent",
                                   "why": "commitment id absent from the run registry"})
                continue
            row["eval"] = k.eval
            row["in_target_interface"] = kid in list(
                getattr(getattr(tgt, "interface", None), "commitments", []) or []
            ) if tgt is not None else None
            if tgt is None:
                mechanical.append({**row, "row": "unverifiable",
                                   "why": "target artifact not registered"})
                continue
            try:
                verdict, _ = programs.evaluate(k, tgt, harness.blobs)
                rederived = str(verdict).split(".")[-1].lower()
            except Exception as e:  # noqa: BLE001
                mechanical.append({**row, "row": "unverifiable",
                                   "why": f"re-evaluation raised: {e}"})
                continue
            row["rederived_verdict"] = rederived
            row["row"] = "correct" if rederived == row["claimed_verdict"] else "misquoted"
            mechanical.append(row)

    # Conjecture lineage in TEMPORAL order.  A candidate is an artifact a
    # CONJECTURE dispatch put on the record; the Q5 rates walk this list.
    prep_of_seq: list[dict] = []
    for work_id, prep in preps.items():
        if prep.get("task_kind") not in ("conjecture", "repair"):
            continue
        lease = prep.get("route_lease") or {}
        prep_of_seq.append({"work_id": work_id, "kind": prep.get("task_kind"),
                            "seat": lease.get("seat"), "role": lease.get("role"),
                            "endpoint": lease.get("endpoint_id")})

    lineage = []
    for ev in events:
        if ev.get("rule") not in ("Conj", "Register", "Spawn", "Scratch"):
            continue
        for out in ev.get("outputs", []):
            if not isinstance(out, str) or out.startswith(("w:", "sha256:")):
                continue
            if out not in text_of or first_seq.get(out) != ev["seq"]:
                continue
            if role_of.get(out) not in ("conjecturer", "variator", "synthesizer"):
                continue
            lineage.append({
                "artifact": out,
                "seq": ev["seq"],
                "rule": ev["rule"],
                "role": role_of.get(out),
                "status": status.get(out),
                "len": len(text_of.get(out, "")),
            })
    lineage.sort(key=lambda r: r["seq"])

    return {
        "root": str(root),
        "problem_criteria": [
            {"id": c.get("id"), "eval": c.get("eval")}
            for c in (problem_doc.get("criteria") or [])
        ],
        "quote_min": QUOTE_MIN,
        "prefix_match": PREFIX_MATCH,
        "rules": dict(collections.Counter(e.get("rule") for e in events)),
        "n_events": len(events),
        "n_artifacts": len(state.artifacts),
        "n_warrants": len(warrants),
        "n_att_edges": len(att),
        "n_dossier_blocks": len(dossier),
        "n_dossier_blocks_reconstructed": sum(1 for b in dossier.values() if b["text"]),
        "status_counts": dict(collections.Counter(status.values())),
        "dispatches": dispatches,
        "mechanical": mechanical,
        "lineage": lineage,
        "att": sorted([list(e) for e in att]),
        "status": status,
        "role": role_of,
    }


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    out = pathlib.Path(sys.argv[2])
    data = census(root)
    out.write_text(json.dumps(data, indent=1, sort_keys=True))
    d = collections.Counter(x["outcome"] for x in data["dispatches"])
    print(f"{root}\n  dispatches: {dict(d)}\n  mechanical: {len(data['mechanical'])}"
          f"\n  lineage: {len(data['lineage'])} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
