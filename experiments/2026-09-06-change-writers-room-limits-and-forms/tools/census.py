"""A census of what a writer's-room run EJECTED. PREREG_CENSUS.md (S4).

Reads the ROOT only. No verdict on quality: counts, shapes, duplicates, and
whether every seat read its whole brief. The commitment seat first.

    python census.py <root> [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "mini"))

COMMITMENT_MARKERS = {
    "refuted-if": r"\brefut|\bfalsif",
    "forbids": r"\bforbid",
    "must-not": r"\bmust not\b|\bcannot\b|\bprohibit",
    "predicts": r"\bpredict|\bwould be observed|\bexpect",
}


def grams(text: str, n: int = 6) -> set[tuple[str, ...]]:
    w = re.findall(r"\w+", text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def blob(root: pathlib.Path, ref: str) -> str:
    return (root / "blobs" / ref[:2] / ref).read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    root = pathlib.Path(a.root)

    from minireason.loop import Session
    from minireason.records import mini_records
    from minireason.seats import COMMITMENT_DIRECTIVE, CONJECTURER_DIRECTIVE, CRITIC_DIRECTIVE

    session = Session(root)
    events = list(session.state.events)
    arts = {
        art.id: art.content_ref[len("inline:"):]
        for art in session.harness.state.artifacts.values()
        if getattr(art.provenance.role, "value", art.provenance.role) == "conjecturer"
    }
    recs = list(mini_records(session))
    out: dict = {"schema": "wr-census.v1", "root": str(root), "seats": {}, "briefs": [], "outputs": []}

    # --- every brief: did the seat read its whole instruction? ---
    tails = {
        "conjecturer": CONJECTURER_DIRECTIVE.rsplit("{vs_k}", 1)[-1].strip(),
        "critic": CRITIC_DIRECTIVE[-60:],
        "commitment": COMMITMENT_DIRECTIVE[-60:],
    }
    limit_by_seq = {}
    for e in events:
        ins = list(e.inputs)
        if ins and ins[0] == "mini:brief-clipped":
            limit_by_seq[e.seq] = ins
    intact = 0
    for e in events:
        if e.llm is None:
            continue
        ins = list(e.inputs)
        rule = getattr(e.rule, "value", e.rule)
        seat = "conjecturer" if rule == "Conj" else None
        if seat is None:
            kind = next((i[len("kind:"):] for i in ins if i.startswith("kind:")), "")
            seat = {"mini.criticism.v1": "critic", "mini.commitment-proposal.v1": "commitment"}.get(kind, "conjecturer")
        brief = blob(root, e.llm.prompt_ref)
        body = brief.split("SYNTAX EXAMPLE", 1)[-1]
        ok = tails[seat] in body
        intact += ok
        out["briefs"].append({"seq": e.seq, "seat": seat, "chars": len(brief), "tokens": e.llm.tokens, "directive_intact": ok})
    out["briefs_total"] = len(out["briefs"])
    out["briefs_directive_intact"] = intact
    out["brief_clipped_markers"] = sum(1 for e in events for i in e.inputs if i == "mini:brief-clipped")

    # --- outputs by seat ---
    def add(seat, ident, text, about=None):
        out["outputs"].append({"seat": seat, "id": ident, "about": about, "chars": len(text), "text": text})

    for aid, text in arts.items():
        add("conjecturer", aid, text)
    for r in recs:
        seat = {"mini.criticism.v1": "critic", "mini.commitment-proposal.v1": "commitment"}.get(r.kind, r.kind)
        add(seat, r.ref, r.content, about=r.about[0] if r.about else None)

    G = {o["id"]: grams(o["text"]) for o in out["outputs"]}
    for o in out["outputs"]:
        o["on_target"] = (o["about"] in arts) if o["about"] is not None else None
        o["commitment_markers"] = [k for k, p in COMMITMENT_MARKERS.items() if re.search(p, o["text"], re.I)]
        # STRICT shape: the FIRST sentence binds the conjecture ("must be
        # refuted if", "forbids", "must not", "cannot", "predicts"). An essay
        # that merely mentions refutation in passing does not pass this.
        first = re.split(r"(?<=[.;:])\s", o["text"].strip(), 1)[0][:240]
        o["first_sentence_binds"] = bool(re.search(r"\b(must|forbid|refut|falsif|cannot|predict|prohibit)", first, re.I))
        others = [p for p in out["outputs"] if p["id"] != o["id"]]
        o["exact_duplicate_of"] = [p["id"][:8] for p in others if p["text"] == o["text"]]
        o["near_duplicate_of"] = [p["id"][:8] for p in others if p["id"] not in o["exact_duplicate_of"] and len(G[o["id"]] & G[p["id"]]) >= 3]
        o["echoes_target"] = (len(G[o["id"]] & grams(arts[o["about"]])) >= 3) if o["about"] in arts else None

    for seat in ("commitment", "critic", "conjecturer"):
        rows = [o for o in out["outputs"] if o["seat"] == seat]
        calls = [b for b in out["briefs"] if b["seat"] == seat]
        chars = [o["chars"] for o in rows] or [0]
        out["seats"][seat] = {
            "calls": len(calls),
            "outputs": len(rows),
            "tokens": sum(b["tokens"] for b in calls),
            "chars_min_mean_max": [min(chars), round(statistics.mean(chars)), max(chars)],
            "on_target": sum(1 for o in rows if o["on_target"]),
            "commitment_shaped": sum(1 for o in rows if o["commitment_markers"]),
            "first_sentence_binds": sum(1 for o in rows if o["first_sentence_binds"]),
            "exact_duplicates": sum(1 for o in rows if o["exact_duplicate_of"]),
            "near_duplicates": sum(1 for o in rows if o["near_duplicate_of"]),
            "echo_target": sum(1 for o in rows if o["echoes_target"]),
        }

    print("WR_CENSUS_V1", root.name)
    print(f"  briefs: {out['briefs_total']}  directive intact: {intact}  clipped markers: {out['brief_clipped_markers']}")
    print(f"  {'seat':<12}{'calls':>6}{'outputs':>8}{'tokens':>8}  {'chars min/mean/max':<20}{'on-target':>10}{'mentions':>9}{'binds-1st':>10}{'exact-dup':>10}{'near-dup':>9}{'echo':>6}")
    for seat, s in out["seats"].items():
        na = seat == "conjecturer"
        print(f"  {seat:<12}{s['calls']:>6}{s['outputs']:>8}{s['tokens']:>8}  {'/'.join(map(str, s['chars_min_mean_max'])):<20}"
              f"{('-' if na else s['on_target']):>10}{s['commitment_shaped']:>9}{s['first_sentence_binds']:>10}{s['exact_duplicates']:>10}{s['near_duplicates']:>9}{('-' if na else s['echo_target']):>6}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
