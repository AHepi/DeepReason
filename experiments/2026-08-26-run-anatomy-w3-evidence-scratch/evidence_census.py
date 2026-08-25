#!/usr/bin/env python3
"""Census what a run's BOUND EVIDENCE was actually used for, versus carried.

Run-anatomy program, measurement tranche W3, census (1). Reads committed run
roots READ-ONLY (dr-drive-harness §5: a writable open repairs, i.e. destroys,
the evidence) and forms no opinion the record does not carry.

Where every number comes from, so each is re-derivable by anyone holding a
root:

  the dossier          `evidence-dossier.json` via `amendment.state.dossier_union`
                       -- sources (`source_locator`, `content_sha256`) and
                       `AdmissionBlockV1` blocks (`id`, `title`, `kind`,
                       `tier`, byte span). A block IS the section: the P-R1
                       dossier admits 623 blocks of `kind="section"`, each
                       carrying the heading it was cut at.

  a citation           a `Measure` event whose first input is
                       `evidence-citation:<CODE>` (conjecture side, filed by
                       `rules/conj.py:2408`) or `premise-citation:<CODE>`
                       (critic side, `rules/crit.py:1368`). The conjecture
                       form carries `[tag, block, artifact_id, problem_id]`;
                       the critic form carries `[tag, block, problem_id]` and
                       NO artifact id -- an asymmetry this census reports
                       rather than papers over.

  the cycle            the 12 `Measure` events tagged `cycle` announce the
                       start of cycle N with the problem selected for it.
                       Cycle N therefore spans `[seq(N), seq(N+1))`.

  the seat             the nearest PRECEDING log event carrying a non-null
                       `llm` block: its `role`, `model`, and
                       `attempt_trace[0].seat`/`contract_id`. Seats are keyed
                       by instance, not role (CLAUDE.md, the signal-registry
                       law), so the seat index is carried through.

  what was SHOWN       `workflow-context-pack-plan-v1` objects with
                       `plan_kind="dossier"` -- the render receipt naming
                       every item planned into a pack and its `planned_bytes`.
                       "Never cited" and "never shown" are different facts and
                       are reported separately.

  citation quality     the model's own raw response, recovered from the blob
                       named by the `llm.raw_ref` of the call. A claimed ref
                       carrying a `quote` is checked byte-true here, by
                       `evidence.citations.canonical_block_text`, against the
                       admitted bytes; a ref with no quote resolved a handle
                       and quoted nothing. The typed Measure event records
                       only the outcome CODE, never the `quoted` flag, so this
                       distinction is recoverable only from the raw blob --
                       stated in the output as a provenance caveat.

Usage:  python evidence_census.py [ROOT ...]     (default: every root under
        experiments/ carrying at least one citation Measure event)
Writes evidence_census.json beside this file. Exit 0 on a completed census.
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter, defaultdict

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from deepreason.evidence.citations import (  # noqa: E402
    EVIDENCE_CITATION_VERIFIED,
    CitationIntegrityError,
    canonical_block_text,
)
from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402

CITATION_TAGS = ("evidence-citation:", "premise-citation:")
SIDE_NAME = {
    "evidence-citation": "conjecture-side",
    "premise-citation": "critic-side",
}


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


def _cycle_index(events: list[dict]) -> list[tuple[int, int, str]]:
    """(start_seq, cycle, problem_id) for each cycle, in order."""
    marks = []
    for e in events:
        ins = e.get("inputs") or []
        if e.get("rule") == "Measure" and ins and ins[0] == "cycle":
            try:
                marks.append((e["seq"], int(ins[1]), str(ins[2]) if len(ins) > 2 else ""))
            except (ValueError, IndexError):
                continue
    return marks


def _cycle_of(marks, seq: int):
    cycle = None
    for start, n, _problem in marks:
        if seq >= start:
            cycle = n
        else:
            break
    return cycle


def _seat_index(events: list[dict]) -> list[tuple[int, dict]]:
    """(seq, seat-facts) for every log event that carries an llm call."""
    out = []
    for e in events:
        llm = e.get("llm")
        if not isinstance(llm, dict):
            continue
        trace = (llm.get("attempt_trace") or [{}])[0]
        out.append((
            e["seq"],
            {
                "role": llm.get("role"),
                "model": llm.get("model"),
                "seat": trace.get("seat"),
                "contract_id": trace.get("contract_id"),
                "raw_ref": llm.get("raw_ref"),
                "prompt_ref": llm.get("prompt_ref"),
                "tokens": llm.get("tokens"),
            },
        ))
    return out


def _seat_at(seats, seq: int):
    """The seat whose call most recently preceded this seq."""
    found = None
    for s, facts in seats:
        if s <= seq:
            found = facts
        else:
            break
    return found or {}


def _dossier_maps(harness):
    from deepreason.amendment.state import dossier_union

    sources: dict[str, dict] = {}
    blocks: dict[str, dict] = {}
    for dossier in dossier_union(harness.root):
        for src in dossier.sources:
            sources[src.content_sha256] = {
                "id": src.id,
                "locator": src.source_locator,
                "name": pathlib.PurePath(src.source_locator.replace("\\", "/")).name,
                "byte_count": src.byte_count,
            }
        for block in getattr(dossier, "blocks", ()) or ():
            blocks[block.id] = {
                "id": block.id,
                "source_sha256": block.source_sha256,
                "kind": block.kind,
                "tier": block.tier,
                "title": getattr(block, "title", None),
                "bytes": (block.span_end or 0) - (block.span_start or 0),
            }
    return sources, blocks


def _pack_receipts(root: pathlib.Path) -> dict:
    """Every context-pack plan, joined to the WORK that requested it.

    Two traps the record punishes anyone who skips this join for, both found
    by this census and both stated here so the next reader does not repeat
    them:

    1. `plan_kind="dossier"` does NOT carry the attached dossier. Its items
       are the run's OWN ARTIFACTS, aliased `SRC_###`. The attached
       documents are exposed by `plan_kind="citable"` under `EVD_###`
       aliases, and the block a citation resolves against is that plan's
       `object_ref`.
    2. A plan names no role. The role is recovered by joining
       `plan.work_id` to `workflow-work-preparation-v1.id` and reading its
       `route_lease.role` -- without which "the critic was never shown the
       evidence" and "the critic was shown it and did not cite it" are
       indistinguishable, and they are the whole question.
    """
    work: dict[str, tuple] = {}
    wd = root / "objects" / "workflow-work-preparation-v1"
    if wd.is_dir():
        for f in sorted(wd.glob("*.json")):
            try:
                d = json.loads(f.read_text())["data"]
            except (json.JSONDecodeError, KeyError, OSError):
                continue
            work[d.get("id")] = (
                (d.get("route_lease") or {}).get("role"),
                d.get("contract_id"),
                d.get("task_kind"),
            )

    plans = []
    d = root / "objects" / "workflow-context-pack-plan-v1"
    if not d.is_dir():
        return {"by_kind": {}, "exposure": {}, "unjoined_plans": 0}
    unjoined = 0
    for f in sorted(d.glob("*.json")):
        try:
            data = json.loads(f.read_text())["data"]
        except (json.JSONDecodeError, KeyError, OSError):
            continue
        role, contract, task = work.get(data.get("work_id"), (None, None, None))
        if role is None:
            unjoined += 1
        plans.append((data, role, contract, task))

    by_kind = defaultdict(lambda: {"plans": 0, "rendered_bytes": 0,
                                   "by_role": Counter(), "items": 0})
    exposure = defaultdict(lambda: Counter())          # object_ref -> role count
    exposure_bytes = Counter()
    for data, role, _contract, task in plans:
        kind = data.get("plan_kind") or "<unset>"
        b = by_kind[kind]
        b["plans"] += 1
        b["rendered_bytes"] += int(data.get("rendered_bytes") or 0)
        b["by_role"][f"{role}/{task}"] += 1
        for item in data.get("items") or ():
            b["items"] += 1
            if kind == "citable" and item.get("namespace") == "evidence":
                ref = item.get("object_ref") or ""
                exposure[ref][role or "<unjoined>"] += 1
                # `planned_bytes` is filled on the FIRST item of a plan only
                # (1193 of P-R1's 1238 citable items carry 0), so it cannot
                # price a single block. The caller prices exposure by the
                # block's own admitted span instead.
                exposure_bytes[ref] += int(item.get("planned_bytes") or 0)

    return {
        "by_kind": {
            k: {
                "plans": v["plans"],
                "rendered_bytes": v["rendered_bytes"],
                "items": v["items"],
                "by_role": dict(v["by_role"]),
            }
            for k, v in by_kind.items()
        },
        "exposure": {k: dict(v) for k, v in exposure.items()},
        "exposure_bytes": dict(exposure_bytes),
        "unjoined_plans": unjoined,
    }


def _load_raw(harness, raw_ref):
    """A model's raw response, tolerating the markdown fence it sometimes wraps.

    30 of P-R1's 163 provider responses arrive as ```json ... ``` rather than
    bare JSON. The harness's own repair path already accepts them, so a census
    that refused them would under-report the very refs it is counting.
    """
    body = harness.blobs.get(raw_ref)
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
        return json.loads(stripped)
    raise ValueError("not JSON and not a fenced JSON block")


def _claimed_refs(harness, seats):
    """Every evidence ref the models CLAIMED, recovered from raw response blobs.

    The typed Measure event records the outcome code but not whether the model
    supplied a quote. That fact lives only in the raw response, so it is read
    back here and each quote re-checked byte-true against admitted bytes.
    """
    claimed = []
    unreadable = 0
    for seq, facts in seats:
        raw_ref = facts.get("raw_ref")
        if not raw_ref:
            continue
        try:
            body = _load_raw(harness, raw_ref)
        except Exception:  # noqa: BLE001 - unparseable raw is a counted outcome
            unreadable += 1
            continue
        if not isinstance(body, dict):
            unreadable += 1
            continue
        for cand in body.get("candidates") or ():
            if not isinstance(cand, dict):
                continue
            for ref in cand.get("evidence_refs") or ():
                if isinstance(ref, dict):
                    claimed.append((seq, facts, "candidate", ref))
        for case in body.get("cases") or ():
            if not isinstance(case, dict):
                continue
            for ref in case.get("premise_evidence") or ():
                if isinstance(ref, dict):
                    claimed.append((seq, facts, "premise", ref))
    return claimed, unreadable


def _resolve(block_ref: str, blocks: dict) -> list[str]:
    if block_ref in blocks:
        return [block_ref]
    return [bid for bid in blocks if bid.startswith(block_ref)]


def census_root(root: pathlib.Path) -> dict:
    events = _events(root)
    if not events:
        return {"root": str(root), "record_present": False}

    harness = Harness(root, read_only=True)
    sources, blocks = _dossier_maps(harness)
    marks = _cycle_index(events)
    seats = _seat_index(events)
    state = harness.state

    # ---- the citations the record TYPED -------------------------------
    citations = []
    for e in events:
        if e.get("rule") != "Measure":
            continue
        ins = e.get("inputs") or []
        if not ins or not isinstance(ins[0], str):
            continue
        if not ins[0].startswith(CITATION_TAGS):
            continue
        side_tag, code = ins[0].split(":", 1)
        block_id = ins[1] if len(ins) > 1 else None
        artifact_id = ins[2] if side_tag == "evidence-citation" and len(ins) > 2 else None
        problem_id = ins[3] if side_tag == "evidence-citation" and len(ins) > 3 else (
            ins[2] if len(ins) > 2 else None
        )
        seat = _seat_at(seats, e["seq"])
        blk = blocks.get(block_id or "")
        src = sources.get((blk or {}).get("source_sha256", ""), {})
        citations.append({
            "seq": e["seq"],
            "cycle": _cycle_of(marks, e["seq"]),
            "side": SIDE_NAME[side_tag],
            "code": code,
            "verified": code == EVIDENCE_CITATION_VERIFIED,
            "block_id": block_id,
            "block_title": (blk or {}).get("title"),
            "resolves_to_dossier_block": blk is not None,
            "source": src.get("name", "<unresolved>"),
            "artifact_id": artifact_id,
            "problem_id": problem_id,
            "seat_role": seat.get("role"),
            "seat_model": seat.get("model"),
            "seat_index": seat.get("seat"),
            "seat_contract": seat.get("contract_id"),
        })

    verified = [c for c in citations if c["verified"]]

    # ---- per document and per section ---------------------------------
    per_source = defaultdict(lambda: defaultdict(int))
    per_block = defaultdict(lambda: defaultdict(int))
    for c in verified:
        per_source[c["source"]]["total"] += 1
        per_source[c["source"]][c["side"]] += 1
        per_source[c["source"]][f"cycle{c['cycle']}"] += 1
        if c["block_id"]:
            per_block[c["block_id"]]["total"] += 1
            per_block[c["block_id"]][c["side"]] += 1

    source_rows = []
    for digest, meta in sources.items():
        blk_ids = [b for b, v in blocks.items() if v["source_sha256"] == digest]
        cited = [b for b in blk_ids if per_block.get(b)]
        counts = per_source.get(meta["name"], {})
        source_rows.append({
            "source": meta["name"],
            "source_id": meta["id"],
            "bytes": meta["byte_count"],
            "blocks_admitted": len(blk_ids),
            "blocks_cited": len(cited),
            "blocks_never_cited": len(blk_ids) - len(cited),
            "verified_citations": counts.get("total", 0),
            "conjecture_side": counts.get("conjecture-side", 0),
            "critic_side": counts.get("critic-side", 0),
            "by_cycle": {
                k.removeprefix("cycle"): v
                for k, v in sorted(counts.items()) if k.startswith("cycle")
            },
        })
    source_rows.sort(key=lambda r: (-r["verified_citations"], r["source"]))

    receipts = _pack_receipts(root)
    _exposure = receipts.get("exposure", {})
    block_rows = [
        {
            "block_id": bid,
            "times_exposed": sum(_exposure.get(bid, {}).values()),
            "exposed_to": dict(_exposure.get(bid, {})),
            "source": sources.get(meta["source_sha256"], {}).get("name", "?"),
            "title": meta["title"],
            "bytes": meta["bytes"],
            "citations": per_block.get(bid, {}).get("total", 0),
            "conjecture_side": per_block.get(bid, {}).get("conjecture-side", 0),
            "critic_side": per_block.get(bid, {}).get("critic-side", 0),
        }
        for bid, meta in blocks.items()
    ]
    block_rows.sort(key=lambda r: (-r["citations"], r["source"], r["title"] or ""))

    never_cited_bytes = sum(r["bytes"] for r in block_rows if r["citations"] == 0)
    all_block_bytes = sum(r["bytes"] for r in block_rows)

    # ---- what was SHOWN, and what it cost -----------------------------
    exposure = receipts.get("exposure", {})
    exposure_bytes = receipts.get("exposure_bytes", {})
    shown_blocks = set(exposure)
    shown_by_critic = {b for b, r in exposure.items()
                       if r.get("argumentative_critic")}
    shown_by_conj = {b for b, r in exposure.items() if r.get("conjecturer")}
    cited_blocks = {b for b in per_block if per_block[b].get("total")}
    _has_citable = bool(receipts.get("by_kind", {}).get("citable"))

    # ---- citation quality: quoted-and-byte-true vs handle-only --------
    claimed, unreadable_raw = _claimed_refs(harness, seats)
    quality = Counter()
    quote_depths: list[int] = []
    quote_failures = []
    quoted_exemplars = []
    for seq, facts, kind, ref in claimed:
        block_ref = str(ref.get("block") or "")
        quote = ref.get("quote")
        matches = _resolve(block_ref, blocks)
        if len(matches) != 1:
            quality["claimed a ref that resolves to no single admitted block"] += 1
            quote_failures.append({
                "seq": seq, "kind": kind, "block_ref": block_ref,
                "role": facts.get("role"), "matches": len(matches),
                "quote_head": (quote or "")[:120],
            })
            continue
        meta = blocks[matches[0]]
        if quote is None:
            quality["resolved a handle, quoted nothing"] += 1
            continue
        try:
            source_bytes = harness.blobs.get(meta["source_sha256"])
            canonical = canonical_block_text(
                next(
                    b for b in _all_blocks(harness) if b.id == matches[0]
                ),
                source_bytes,
            )
        except (CitationIntegrityError, KeyError, OSError, StopIteration):
            quality["quoted a block whose admitted bytes are unrecoverable"] += 1
            continue
        folded_q, folded_c = _folded(quote), _folded(canonical)
        if folded_q and folded_q in folded_c:
            end = folded_c.index(folded_q) + len(folded_q)
            quote_depths.append(end)
        if quote.encode() in canonical.encode():
            quality["quoted and byte-true"] += 1
            if len(quoted_exemplars) < 12:
                quoted_exemplars.append({
                    "seq": seq, "role": facts.get("role"), "kind": kind,
                    "source": sources.get(meta["source_sha256"], {}).get("name"),
                    "block_title": meta["title"], "quote": quote[:400],
                })
        elif _folded(quote) and _folded(quote) in _folded(canonical):
            quality["quoted, true only after folding whitespace"] += 1
        else:
            quality["quoted text that is NOT in the block"] += 1
            quote_failures.append({
                "seq": seq, "kind": kind, "block_ref": block_ref,
                "role": facts.get("role"),
                "quote_head": quote[:200],
                "block_title": meta["title"],
            })

    # ---- citation -> outcome (CORRELATION, reported as such) ----------
    citing_artifacts = {c["artifact_id"] for c in verified if c["artifact_id"]}
    result = {}
    rp = root / "run-result.json"
    if rp.is_file():
        try:
            result = json.loads(rp.read_text())
        except json.JSONDecodeError:
            result = {}
    survivors = set(result.get("survivors") or ())

    conjectured = {}
    for aid, artifact in state.artifacts.items():
        prov = getattr(artifact, "provenance", None)
        role = getattr(prov, "role", None) if prov else None
        conjectured[aid] = role
    outcome = {"citing": Counter(), "non_citing": Counter()}
    for aid, role in conjectured.items():
        if role != "conjecturer":
            continue
        bucket = "citing" if aid in citing_artifacts else "non_citing"
        st = state.status.get(aid)
        outcome[bucket]["total"] += 1
        outcome[bucket][
            st.value if isinstance(st, Status) else str(st)
        ] += 1
        if aid in survivors:
            outcome[bucket]["survivor"] += 1

    def _rate(b):
        t = outcome[b]["total"] or 1
        return {
            "n": outcome[b]["total"],
            "accepted": outcome[b].get("accepted", 0),
            "refuted": outcome[b].get("refuted", 0),
            "survivors": outcome[b].get("survivor", 0),
            "survival_rate": round(outcome[b].get("survivor", 0) / t, 4),
            "acceptance_rate": round(outcome[b].get("accepted", 0) / t, 4),
        }

    # ---- the critic side, characterised ------------------------------
    critic_claims = [
        (seq, facts, ref) for seq, facts, kind, ref in claimed if kind == "premise"
    ]
    critic_targets = Counter()
    critic_examples = []
    for seq, facts, ref in critic_claims:
        block_ref = str(ref.get("block") or "")
        matches = _resolve(block_ref, blocks)
        if len(matches) == 1:
            critic_targets["a dossier block"] += 1
            label = "dossier block"
        elif any(a.startswith(block_ref) for a in state.artifacts):
            critic_targets["an ARTIFACT in the run (not the dossier)"] += 1
            label = "artifact"
        elif any(str(p).endswith(block_ref) or block_ref in str(p)
                 for p in state.status):
            critic_targets["something else in run state"] += 1
            label = "run state"
        else:
            critic_targets["an id that is neither a dossier block nor an artifact"] += 1
            label = "unresolved"
        if len(critic_examples) < 20:
            critic_examples.append({
                "seq": seq, "cycle": _cycle_of(marks, seq),
                "block_ref": block_ref, "resolves_to": label,
                "quote": (ref.get("quote") or "")[:300],
            })

    return {
        "root": str(root),
        "record_present": True,
        "run_id": result.get("run_id") or (root / "run-status.json").is_file() and
        json.loads((root / "run-status.json").read_text()).get("run_id"),
        "events": len(events),
        "cycles": len(marks),
        "dossier": {
            "sources": len(sources),
            "blocks": len(blocks),
            "block_bytes_total": all_block_bytes,
        },
        "citations": {
            "measure_events": len(citations),
            "verified": len(verified),
            "unverified": len(citations) - len(verified),
            "by_code": dict(Counter(c["code"] for c in citations)),
            "by_side": dict(Counter(c["side"] for c in citations)),
            "verified_by_side": dict(Counter(c["side"] for c in verified)),
            "verified_by_cycle": dict(sorted(
                Counter(str(c["cycle"]) for c in verified).items(),
                key=lambda kv: int(kv[0]) if kv[0].isdigit() else -1)),
            "verified_by_seat": dict(Counter(
                f"{c['seat_role']}/{c['seat_model']}/seat{c['seat_index']}"
                for c in verified)),
        },
        "per_source": source_rows,
        "per_section_top": block_rows[:40],
        "per_section_all": block_rows,
        "dead_weight": {
            "blocks_admitted": len(blocks),
            "blocks_ever_cited": sum(1 for r in block_rows if r["citations"]),
            "blocks_never_cited": sum(1 for r in block_rows if not r["citations"]),
            "never_cited_bytes": never_cited_bytes,
            "never_cited_byte_share": round(
                never_cited_bytes / all_block_bytes, 4) if all_block_bytes else None,
            "sources_ever_cited": sum(1 for r in source_rows if r["verified_citations"]),
            "sources_never_cited": [
                r["source"] for r in source_rows if not r["verified_citations"]],
        },
        "packs": {
            "by_kind": receipts.get("by_kind", {}),
            "unjoined_plans": receipts.get("unjoined_plans", 0),
            "note": (
                "plan_kind='dossier' carries the run's OWN ARTIFACTS aliased "
                "SRC_###, not the attached documents; the attached documents "
                "are exposed by plan_kind='citable' under EVD_### aliases"
            ),
        },
        "exposure_vs_citation": {
            "exposure_regime": (
                "citable-legend"
                if receipts.get("by_kind", {}).get("citable")
                else ("dossier-pack-only" if receipts.get("by_kind")
                      else "no pack plans typed in this root")
            ),
            "regime_note": (
                "TWO regimes exist across the committed record and they are "
                "not comparable. Under 'citable-legend' the models see at most "
                "`maximum_blocks=32` blocks as `excerpt_chars=160` excerpts "
                "under EVD_### aliases, and the exposure gate is live "
                "(EVIDENCE_REF_NOT_EXPOSED can fire). Under "
                "'dossier-pack-only' there is no citable legend: the dossier "
                "pack renders SOURCE text under SRC_### aliases, no exposed "
                "set is computed, and quotes may reach arbitrarily deep into a "
                "document. A root with no pack plans typed cannot answer the "
                "exposure question at all, and reports null rather than zero."
            ),
            "blocks_admitted": len(blocks),
            "blocks_ever_exposed": len(shown_blocks) if _has_citable else None,
            "blocks_never_exposed": (len(blocks) - len(shown_blocks & set(blocks))) if _has_citable else None,
            "blocks_exposed_to_conjecturer": len(shown_by_conj) if _has_citable else None,
            "blocks_exposed_to_critic": len(shown_by_critic) if _has_citable else None,
            "blocks_ever_cited": len(cited_blocks),
            "exposed_and_cited": len(shown_blocks & cited_blocks) if _has_citable else None,
            "exposed_and_never_cited": len(shown_blocks - cited_blocks) if _has_citable else None,
            "cited_without_being_exposed": sorted(cited_blocks - shown_blocks),
            "citable_pack_rendered_bytes": receipts.get("by_kind", {})
                .get("citable", {}).get("rendered_bytes", 0),
            "exposures_total": sum(sum(v.values()) for v in exposure.values()),
            "exposures_of_never_cited_blocks": sum(
                sum(v.values()) for k, v in exposure.items()
                if k not in cited_blocks),
            "admitted_bytes_exposed_at_least_once": sum(
                blocks[b]["bytes"] for b in shown_blocks if b in blocks),
            "admitted_bytes_never_exposed": sum(
                m["bytes"] for b, m in blocks.items() if b not in shown_blocks),
            "share_of_exposures_spent_on_never_cited_blocks": round(
                sum(sum(v.values()) for k, v in exposure.items()
                    if k not in cited_blocks)
                / max(1, sum(sum(v.values()) for v in exposure.values())), 4),
            "pricing_caveat": (
                "`planned_bytes` is populated on the FIRST item of a pack plan "
                "only (1193 of P-R1's 1238 citable items carry 0), so a "
                "per-block pack price is NOT typed. The honest price is the "
                "citable packs' own `rendered_bytes` total, split by the share "
                "of exposures spent on blocks nothing ever cited. Pricing by "
                "admitted span bytes would overstate it several-fold, because "
                "the legend renders a 160-char excerpt, not the block."),
            "reading": (
                "a block that was never EXPOSED could not be cited; a block "
                "exposed and never cited is the dossier's paid-for dead "
                "weight. The two are different findings and are never merged."
            ),
        },
        "citation_quality": {
            "claimed_refs_recovered_from_raw": len(claimed),
            "unreadable_raw_responses": unreadable_raw,
            "breakdown": dict(quality),
            "failures": quote_failures[:25],
            "quoted_exemplars": quoted_exemplars,
            "excerpt_reach": _excerpt_reach(quote_depths),
            "caveat": (
                "the typed Measure event records the outcome CODE only; the "
                "quoted/unquoted split is recoverable ONLY from the raw "
                "response blob named by llm.raw_ref"
            ),
        },
        "citation_and_outcome": {
            "citing": _rate("citing"),
            "non_citing": _rate("non_citing"),
            "reading": (
                "CORRELATION ONLY. Citing and non-citing conjectures are not "
                "randomised: they differ in seat, cycle, problem and content, "
                "and the run selects what to criticise. No causal claim."
            ),
        },
        "critic_side": {
            "typed_premise_citation_measures": sum(
                1 for c in citations if c["side"] == "critic-side"),
            "typed_and_verified": sum(
                1 for c in verified if c["side"] == "critic-side"),
            "claimed_premise_refs_in_raw": len(critic_claims),
            "what_the_critic_actually_referenced": dict(critic_targets),
            "examples": critic_examples,
        },
    }


def _all_blocks(harness):
    from deepreason.amendment.state import dossier_union

    for dossier in dossier_union(harness.root):
        for block in getattr(dossier, "blocks", ()) or ():
            yield block


def _excerpt_reach(depths: list[int]) -> dict:
    """How deep into a block the models' verified quotes actually reach.

    `evidence.render.citable_legend` shows each block as an excerpt of
    `excerpt_chars=160` and shows at most `maximum_blocks=32` blocks. A
    verified quote whose end position is <= 160 is consistent with the model
    having quoted the EXCERPT rather than the document; one reaching beyond
    160 could only have come from bytes the legend never rendered. The two
    are not the same claim about engagement with the evidence, so the census
    separates them instead of reporting one "byte-checked" total.
    """
    if not depths:
        return {"verified_quotes": 0}
    ordered = sorted(depths)
    mid = len(ordered) // 2
    median = (ordered[mid] if len(ordered) % 2
              else (ordered[mid - 1] + ordered[mid]) / 2)
    within = sum(1 for d in ordered if d <= 160)
    return {
        "verified_quotes": len(ordered),
        "legend_excerpt_chars": 160,
        "legend_maximum_blocks": 32,
        "end_position_min": ordered[0],
        "end_position_median": median,
        "end_position_max": ordered[-1],
        "ending_within_the_excerpt": within,
        "reaching_beyond_the_excerpt": len(ordered) - within,
        "share_within_the_excerpt": round(within / len(ordered), 4),
        "reading": (
            "a quote ending within 160 chars is consistent with quoting the "
            "legend excerpt rather than the admitted document; only a quote "
            "reaching beyond 160 proves the model saw bytes the excerpt did "
            "not carry"
        ),
    }


def _folded(text: str) -> str:
    return " ".join(text.split())


def _default_roots() -> list[pathlib.Path]:
    roots = []
    for log in sorted((REPO / "experiments").rglob("log.jsonl")):
        try:
            body = log.read_text(errors="replace")
        except OSError:
            continue
        if "evidence-citation:" in body or "premise-citation:" in body:
            roots.append(log.parent)
    return roots


def main() -> int:
    roots = [pathlib.Path(a) for a in sys.argv[1:]] or _default_roots()
    reports = []
    for root in roots:
        try:
            reports.append(census_root(root))
        except Exception as exc:  # noqa: BLE001 - a failed root is a datum
            reports.append({"root": str(root), "error": f"{type(exc).__name__}: {exc}"})
    out = TRANCHE / "evidence_census.json"
    out.write_text(json.dumps(
        {"roots": reports, "root_count": len(reports)},
        indent=2, sort_keys=True, default=str) + "\n")
    for r in reports:
        if "error" in r:
            print(f"ERROR {r['root']}: {r['error']}")
            continue
        if not r.get("record_present"):
            print(f"NO RECORD {r['root']}")
            continue
        c, d = r["citations"], r["dead_weight"]
        print(f"{pathlib.Path(r['root']).as_posix():78s} "
              f"src={r['dossier']['sources']:3d} blk={r['dossier']['blocks']:4d} "
              f"cit={c['measure_events']:4d} ok={c['verified']:4d} "
              f"cited-blk={d['blocks_ever_cited']:4d} "
              f"dead={d['never_cited_byte_share']}")
    print(f"\nreport {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
