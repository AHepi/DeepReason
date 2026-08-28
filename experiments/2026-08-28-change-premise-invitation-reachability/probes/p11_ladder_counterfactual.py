#!/usr/bin/env python3
"""P11 pricing probe -- what the LADDER rule would have cost, and bought.

Read-only. Replays a committed root with the harness's own time-travel reader
(`Harness.at(root, seq)`) at every `argumentative_critic` dispatch and asks two
questions of the state AS OF THAT SEQ, per problem:

  old   the shipped gate: `premise_work_invited` --
        no standing attribution AND refuted >= PREMISE_INVITE_AFTER
  new   the ladder: refuted >= PREMISE_INVITE_AFTER * (standing + 1)

The counterfactual is honest about exactly one thing and no more: it says on how
many dispatches each rule WOULD HAVE FOUND a problem standing an invitation,
given the history the run actually produced. It does not claim the run would
have gone the same way -- a re-invited critic that filed a premise changes the
graph downstream. Use it to price the channel's frequency, never to predict a
different run's outcome.

Cost side, measured from the same root's prompt bytes rather than estimated:
the invitation paragraph and the CITABLE EVIDENCE BLOCKS legend, in characters.

Usage: p11_ladder_counterfactual.py <root> [<root> ...]
"""
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, "src")
from deepreason.harness import Harness  # noqa: E402
from deepreason.premises import (  # noqa: E402
    PREMISE_INVITE_AFTER,
    standing_attributions,
)
from deepreason.ontology import Status  # noqa: E402

INVITED = 'state that presupposition in "premise"'
CITABLE = "CITABLE EVIDENCE BLOCKS"


def _gates(harness) -> dict:
    """Per problem: (refuted count, standing attributions, old gate, new gate)."""
    refuted = Counter()
    for aid, pid in harness.state.addr:
        if harness.state.status.get(aid) == Status.REFUTED:
            refuted[pid] += 1
    standing = Counter(pid for _, pid, _ in standing_attributions(harness))
    out = {}
    for pid in set(refuted) | set(standing) | set(harness.state.problems):
        r, s = refuted[pid], standing[pid]
        out[pid] = {
            "refuted": r,
            "standing": s,
            "old": s == 0 and r >= PREMISE_INVITE_AFTER,
            "new": r >= PREMISE_INVITE_AFTER * (s + 1),
        }
    return out


def _blob(root: pathlib.Path, ref: str) -> str:
    path = root / "blobs" / ref[:2] / ref
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def report(root: pathlib.Path) -> dict:
    dispatches = []
    invited_chars, uninvited_chars = [], []
    with (root / "log.jsonl").open() as fh:
        for line in fh:
            event = json.loads(line)
            llm = event.get("llm")
            if not llm or llm.get("role") != "argumentative_critic":
                continue
            ref = llm.get("prompt_ref")
            text = _blob(root, ref) if ref else ""
            was_invited = INVITED in text
            (invited_chars if was_invited else uninvited_chars).append(len(text))
            dispatches.append({"seq": event["seq"], "shown_invitation": was_invited})

    for row in dispatches:
        gates = _gates(Harness.at(root, row["seq"]))
        row["problems_open_old"] = sorted(p for p, g in gates.items() if g["old"])
        row["problems_open_new"] = sorted(p for p, g in gates.items() if g["new"])

    # The legend's own price, from the bytes of the first invited prompt.
    legend_chars = invitation_chars = None
    with (root / "log.jsonl").open() as fh:
        for line in fh:
            event = json.loads(line)
            llm = event.get("llm")
            if not llm or llm.get("role") != "argumentative_critic":
                continue
            text = _blob(root, llm.get("prompt_ref") or "")
            if INVITED not in text or CITABLE not in text:
                continue
            start = text.find(CITABLE)
            legend_chars = len(text) - start
            paragraph = text.rfind("\n\n", 0, start)
            invitation_chars = start - paragraph
            break

    open_old = sum(1 for d in dispatches if d["problems_open_old"])
    open_new = sum(1 for d in dispatches if d["problems_open_new"])
    return {
        "root": root.name,
        "critic_dispatches": len(dispatches),
        "shown_invitation": sum(1 for d in dispatches if d["shown_invitation"]),
        "dispatches_with_an_open_problem_old": open_old,
        "dispatches_with_an_open_problem_new": open_new,
        "invitation_paragraph_chars": invitation_chars,
        "citable_legend_chars": legend_chars,
        "median_uninvited_prompt_chars": (
            sorted(uninvited_chars)[len(uninvited_chars) // 2] if uninvited_chars else None
        ),
        "invited_prompt_chars": sorted(invited_chars),
        "per_dispatch": dispatches,
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2, sort_keys=True))
