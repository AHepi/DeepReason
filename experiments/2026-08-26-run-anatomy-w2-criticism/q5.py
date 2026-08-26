#!/usr/bin/env python3
"""W2 — the Q5 causal-work rates, measured on our own records.

GOAL.md dimension 3.  Reads `<root>` READ-ONLY plus the census JSON that
`census.py` produced, and computes, per root:

    CouplingRate  of criticized candidates, the fraction whose seat's NEXT
                  candidate changed in the CRITICIZED RESPECT
    RepairRate    of those coupled changes, the fraction that helped by the
                  run's own measure
    NeglectRate   of criticized candidates, the fraction where the criticism
                  was carried on the record and the next candidate repeated
                  the criticized respect unchanged

"The criticized respect" is not a feeling, so it is operationalized twice
and both are reported.  Each operationalization states its own denominator;
they are NOT averaged into one headline, because they measure different
criticisms.

  R1 MECHANICAL — for a warrant-bearing criticism, the respect is THE
     COMMITMENT THE TARGET FAILED.  Coupled iff the next candidate PASSES
     that same commitment, re-evaluated by `deepreason.programs.evaluate`
     on the next candidate's own bytes.  This is exact.

  R2 PROSE-QUOTE — for an LLM attack that quoted the target verbatim, the
     respect is THE QUOTED SPAN.  Coupled iff no span the critic quoted
     accurately survives into the next candidate.  This is a proxy and is
     labelled one: a critic may attack something it never quoted, and a
     conjecturer may drop a phrase for reasons unrelated to the attack.
     An attack that quoted nothing accurately is NOT counted in R2's
     denominator at all — silently scoring it as neglect would inflate
     NeglectRate with cases the instrument cannot see.

EVERY RATE CARRIES A PLACEBO.  Candidates are generated in BATCHES, so the
candidate after a criticism is usually a fresh construction rather than a
revision of the criticized one, and it would "change in the criticized
respect" whether or not the criticism existed.  So each rate is computed
twice: once on the candidate AFTER the criticism, and once on the candidate
BEFORE it, which cannot have been influenced by it.  The DIFFERENCE is the
only part that is evidence of causal work; the after-rate alone is not.

AND EVERY RATE IS PRECEDED BY A CHANNEL CENSUS.  A criticism can only do
causal work if something that acts on it was shown it.  `exposure` counts,
per root, how many criticism artifacts were ever exposed to a later
conjecture dispatch (`workflow-context-exposure-v2.exposed_items`).  If that
count is zero the rates below are measuring coincidence, and the report must
say so rather than quoting a number.

"Helped by the run's own measure" is the run's own scoreboard, never this
census's opinion:
  * P-C1 (Heilbronn): the tranche's own exact rational checker, higher is
    better.  `checker.py` is imported from the tranche that registered it.
  * P-R1 (explanation): SURVIVAL — the next candidate's final Status is
    ACCEPTED.  That root has no scalar score; its own success measure is
    whether a conjecture stood at the end.

Usage:  python q5.py <root> <census.json> <out.json> [--checker <dir>]
"""
from __future__ import annotations

import bisect
import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason import programs  # noqa: E402
from deepreason.harness import Harness  # noqa: E402


def _norm_ok(text: str, quote: str) -> bool:
    import re
    n = lambda s: re.sub(r"\s+", " ", s or "").strip().lower()  # noqa: E731
    return n(quote).strip(" .,;:!?—–-\"'‘’“”()") in n(text)


def rates(root: pathlib.Path, census: dict, checker_dir: pathlib.Path | None) -> dict:
    harness = Harness(root, read_only=True)
    state = harness.state
    commitments = dict(harness.commitments)
    warrants = dict(harness.warrants)
    status = census["status"]

    text_of = {}
    for aid, art in state.artifacts.items():
        try:
            text_of[aid] = programs.content_text(art, harness.blobs)
        except Exception:  # noqa: BLE001
            text_of[aid] = ""

    checker = None
    if checker_dir is not None and (checker_dir / "checker.py").is_file():
        sys.path.insert(0, str(checker_dir))
        import checker as _checker  # noqa: PLC0415
        checker = _checker

    def score(aid: str):
        """The run's own scalar measure, or None where the run has none."""
        if checker is None:
            return None
        t = text_of.get(aid, "")
        if not checker.POINT_RE.search(t):
            return None
        v = checker.check(t)
        return v["score"] if v.get("valid") else None

    lineage = census["lineage"]
    seqs = [r["seq"] for r in lineage]

    def next_candidate(after_seq: int, exclude: str | None = None):
        i = bisect.bisect_right(seqs, after_seq)
        while i < len(lineage):
            if lineage[i]["artifact"] != exclude:
                return lineage[i]
            i += 1
        return None

    def prev_candidate(before_seq: int, exclude: str | None = None):
        """The placebo: a candidate that already existed when the criticism
        was written, so nothing it does can be the criticism's doing."""
        i = bisect.bisect_left(seqs, before_seq) - 1
        while i >= 0:
            if lineage[i]["artifact"] != exclude:
                return lineage[i]
            i -= 1
        return None

    # ---- the channel census: was any criticism ever shown to a conjecturer?
    import glob as _glob
    preps = {}
    for path in (root / "objects" / "workflow-work-preparation-v1").glob("*.json"):
        d = json.load(path.open())["data"]
        preps[d["id"]] = d
    role_of = {}
    for aid, art in state.artifacts.items():
        role_of[aid] = str(
            getattr(getattr(art, "provenance", None), "role", "") or ""
        ).split(".")[-1].lower()
    exposed_to_conjecture: set[str] = set()
    exposure_counts: collections.Counter = collections.Counter()
    exp_dir = root / "objects" / "workflow-context-exposure-v2"
    if exp_dir.is_dir():
        for path in exp_dir.glob("*.json"):
            d = json.load(path.open())["data"]
            prep = preps.get(d.get("work_id"))
            kind = (prep or {}).get("task_kind")
            for it in d.get("exposed_items") or []:
                ref = it.get("object_ref")
                exposure_counts[(kind, it.get("namespace"), role_of.get(ref, "non-artifact"))] += 1
                if kind == "conjecture" and role_of.get(ref) == "critic":
                    exposed_to_conjecture.add(ref)

    llm_crit_ids = {
        d.get("registered_artifact") for d in census["dispatches"]
        if d.get("outcome") == "attack" and d.get("registered_artifact")
    }
    mech_crit_ids = {
        m.get("crit_artifact") for m in census["mechanical"] if m.get("crit_artifact")
    }
    exposure = {
        "critic_artifacts_shown_to_a_conjecture_dispatch": sorted(exposed_to_conjecture),
        "n_shown": len(exposed_to_conjecture),
        "n_llm_attacks_shown": len(exposed_to_conjecture & llm_crit_ids),
        "n_llm_attacks_total": len(llm_crit_ids),
        "n_mechanical_shown": len(exposed_to_conjecture & mech_crit_ids),
        "n_mechanical_total": len(mech_crit_ids),
        "exposure_counts_by_task_namespace_role": {
            "|".join(str(x) for x in k): v for k, v in sorted(exposure_counts.items())
        },
    }

    # ---- R1, the mechanical respect -------------------------------------
    r1 = []
    for m in census["mechanical"]:
        if m.get("row") != "correct":
            continue
        kid, target = m.get("commitment"), m.get("target")
        k = commitments.get(kid)
        nxt = next_candidate(m["seq"], exclude=target)
        pre = prev_candidate(m["seq"], exclude=target)
        row = {
            "seq": m["seq"], "target": target, "commitment": kid,
            "next": (nxt or {}).get("artifact"), "next_seq": (nxt or {}).get("seq"),
            "placebo": (pre or {}).get("artifact"),
        }
        if pre is not None and k is not None:
            try:
                pv, _ = programs.evaluate(k, state.artifacts.get(pre["artifact"]),
                                          harness.blobs)
                row["placebo_passes"] = str(pv).split(".")[-1].lower() == "pass"
            except Exception:  # noqa: BLE001
                row["placebo_passes"] = None
        if nxt is None or k is None:
            r1.append({**row, "verdict": "no-next-candidate"})
            continue
        art = state.artifacts.get(nxt["artifact"])
        try:
            v, _ = programs.evaluate(k, art, harness.blobs)
            passed = str(v).split(".")[-1].lower() == "pass"
        except Exception as e:  # noqa: BLE001
            r1.append({**row, "verdict": "unevaluable", "why": str(e)})
            continue
        s_old, s_new = score(target), score(nxt["artifact"])
        r1.append({
            **row,
            "verdict": "coupled" if passed else "neglected",
            "next_status": status.get(nxt["artifact"]),
            "score_before": s_old, "score_after": s_new,
            "helped": (
                (s_new is not None and s_old is not None and s_new > s_old)
                if checker is not None
                else status.get(nxt["artifact"]) == "accepted"
            ),
        })

    # ---- R2, the prose-quote respect ------------------------------------
    r2 = []
    for d in census["dispatches"]:
        if d.get("outcome") != "attack":
            continue
        good = [q["quote"] for q in d.get("quotes_of_target", [])
                if q.get("trimmed_in_target")]
        seq = d.get("crit_seq")
        if seq is None:
            r2.append({"target": d.get("target"), "verdict": "unlocatable-in-log"})
            continue
        if not good:
            r2.append({"target": d.get("target"), "seq": seq,
                       "verdict": "no-verbatim-quote-to-track"})
            continue
        nxt = next_candidate(seq, exclude=d.get("target"))
        pre = prev_candidate(seq, exclude=d.get("target"))
        row = {"target": d.get("target"), "seq": seq, "n_quotes": len(good),
               "next": (nxt or {}).get("artifact"),
               "placebo": (pre or {}).get("artifact")}
        if pre is not None:
            ptext = text_of.get(pre["artifact"], "")
            row["placebo_passes"] = not any(_norm_ok(ptext, q) for q in good)
        if nxt is None:
            r2.append({**row, "verdict": "no-next-candidate"})
            continue
        ntext = text_of.get(nxt["artifact"], "")
        survived = [q for q in good if _norm_ok(ntext, q)]
        s_old, s_new = score(d.get("target")), score(nxt["artifact"])
        r2.append({
            **row,
            "quotes_surviving": len(survived),
            "verdict": "coupled" if not survived else "neglected",
            "next_status": status.get(nxt["artifact"]),
            "score_before": s_old, "score_after": s_new,
            "helped": (
                (s_new is not None and s_old is not None and s_new > s_old)
                if checker is not None
                else status.get(nxt["artifact"]) == "accepted"
            ),
        })

    def summarize(rows: list[dict]) -> dict:
        v = collections.Counter(r["verdict"] for r in rows)
        measurable = v["coupled"] + v["neglected"]
        coupled = [r for r in rows if r["verdict"] == "coupled"]
        helped = sum(1 for r in coupled if r.get("helped"))
        placebo = [r for r in rows
                   if r["verdict"] in ("coupled", "neglected")
                   and r.get("placebo_passes") is not None]
        p_changed = sum(1 for r in placebo if r["placebo_passes"])
        after = (v["coupled"] / measurable) if measurable else None
        before = (p_changed / len(placebo)) if placebo else None
        return {
            "verdicts": dict(v),
            "denominator_measurable": measurable,
            "CouplingRate": after,
            "NeglectRate": (v["neglected"] / measurable) if measurable else None,
            "RepairRate": (helped / len(coupled)) if coupled else None,
            "coupled": v["coupled"], "neglected": v["neglected"], "helped": helped,
            "PlaceboRate": before,
            "placebo_denominator": len(placebo),
            "CouplingRate_minus_Placebo": (
                (after - before) if (after is not None and before is not None) else None
            ),
        }

    # ---- did criticism ever precede a score improvement? -----------------
    #  The P-C1 question, asked of whatever root can answer it.
    trajectory = []
    best = None
    for r in lineage:
        s = score(r["artifact"])
        if s is not None and (best is None or s > best):
            best = s
            trajectory.append({"seq": r["seq"], "artifact": r["artifact"],
                               "new_best": s})
    crit_seqs = sorted(
        [m["seq"] for m in census["mechanical"]]
        + [d["crit_seq"] for d in census["dispatches"]
           if d.get("outcome") == "attack" and d.get("crit_seq") is not None]
    )
    improvements_after_criticism = []
    for imp in trajectory:
        prior = bisect.bisect_left(crit_seqs, imp["seq"])
        improvements_after_criticism.append({**imp, "criticisms_before": prior})

    return {
        "root": str(root),
        "n_lineage": len(lineage),
        "exposure": exposure,
        "R1_mechanical": summarize(r1),
        "R2_prose_quote": summarize(r2),
        "best_score_trajectory": improvements_after_criticism,
        "n_criticism_events_total": len(crit_seqs),
        "rows_R1": r1,
        "rows_R2": r2,
    }


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    census = json.loads(pathlib.Path(sys.argv[2]).read_text())
    out = pathlib.Path(sys.argv[3])
    checker_dir = None
    if "--checker" in sys.argv:
        checker_dir = pathlib.Path(sys.argv[sys.argv.index("--checker") + 1]).resolve()
    data = rates(root, census, checker_dir)
    out.write_text(json.dumps(data, indent=1, sort_keys=True))
    print(json.dumps({k: data[k] for k in
                      ("root", "exposure", "R1_mechanical", "R2_prose_quote",
                       "n_criticism_events_total")}, indent=1, default=str)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
