#!/usr/bin/env python3
"""Q1 probe A -- the critic-side citation channel, counted from the record.

Reads each committed P-T1 root's log.jsonl directly (no `deepreason` import, so
the count cannot inherit a reader's opinion) and answers:

  1. how many citation Measure events of each side reached the record.
     Conjecture side files `evidence-citation:<CODE>` (rules/conj.py:2562);
     critic side files `premise-citation:<CODE>` (rules/crit.py:1378). This is
     the same measure milestone_census.py uses for M2.
  2. how many REFUTED artifacts each PROBLEM accumulated. That count is the
     quantity the critic-side channel's invitation gate reads:
     `premise_work_invited` (src/deepreason/premises.py:625-645) returns True
     only when a problem carries >= PREMISE_INVITE_AFTER (=2) refuted
     candidates and no attribution is already standing.
  3. whether ANY problem in the run ever met that threshold -- i.e. whether the
     critic-side citation channel was ever OPEN for a single dispatch.

Usage: q1_citation_census.py <root> [<root> ...]
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PREMISE_INVITE_AFTER = 2  # src/deepreason/premises.py:68


def events(root: Path):
    with (root / "log.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def census(root: Path) -> dict:
    sides = Counter()
    codes = Counter()
    rules = Counter()
    addr: dict[str, str] = {}          # artifact id -> problem id
    status: dict[str, str] = {}        # artifact id -> latest status
    premise_events = []
    for ev in events(root):
        rules[ev.get("rule", "")] += 1
        for item in ev.get("inputs") or []:
            if not isinstance(item, str):
                continue
            if item.startswith("evidence-citation:"):
                sides["evidence-citation"] += 1
                codes["conjecture/" + item.split(":", 1)[1]] += 1
            elif item.startswith("premise-citation:"):
                sides["premise-citation"] += 1
                codes["critic/" + item.split(":", 1)[1]] += 1
                premise_events.append(ev.get("seq"))
            elif item.startswith("premise-"):
                sides[item.split(":", 1)[0]] += 1
        diff = ev.get("state_diff") or {}
        for entry in diff.get("addr+") or []:
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                addr[entry[0]] = entry[1]
        for entry in diff.get("status_changed") or []:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                status[entry[0]] = entry[-1]
            elif isinstance(entry, dict):
                aid = entry.get("id") or entry.get("artifact")
                if aid:
                    status[aid] = entry.get("to") or entry.get("status")

    refuted_by_problem = Counter()
    for aid, pid in addr.items():
        if str(status.get(aid, "")).upper().endswith("REFUTED"):
            refuted_by_problem[pid] += 1

    invited = {p: c for p, c in refuted_by_problem.items() if c >= PREMISE_INVITE_AFTER}
    return {
        "root": root.name,
        "citation_measures": dict(sides),
        "citation_codes": dict(codes),
        "critic_side_verified": codes.get("critic/EVIDENCE_CITATION_VERIFIED", 0),
        "conjecture_side_verified": codes.get("conjecture/EVIDENCE_CITATION_VERIFIED", 0),
        "premise_citation_event_seqs": premise_events,
        "artifacts_addressed": len(addr),
        "problems": len(set(addr.values())),
        "refuted_total": sum(refuted_by_problem.values()),
        "refuted_by_problem": dict(refuted_by_problem.most_common()),
        "max_refuted_on_one_problem": max(refuted_by_problem.values(), default=0),
        "problems_meeting_invite_threshold": invited,
        "critic_channel_ever_open": bool(invited),
        "status_values_seen": sorted({str(v) for v in status.values()}),
        "rule_counts": dict(rules.most_common(20)),
    }


def main() -> int:
    print(json.dumps([census(Path(a)) for a in sys.argv[1:]], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
