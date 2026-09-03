"""M3, measured properly: read the objections that did NOT land.

This REPLACES `measure_criticism.py`, whose measures were saturated
(sustain rate 1.000 on every root) and undefined (re-raise rate n/a). PARKED P7
attributed that to the record: "criticism that warrants nothing leaves no trace
in `att` at all". The first half is right and the second half was WRONG, and the
correction matters more than the original finding.

## What the record actually keeps

`rules/crit.py`'s `observe_only` path registers a not-landed objection as a
**critic-role artifact with NO warrants**, and writes a
`["scrutiny", target, critic]` Measure event. Its own docstring says so: "the
case is scrutiny evidence, never a status change ... Registers the case as a
critic-role artifact with NO warrants". So a failed objection is fully
recorded — target, text and all. It is simply not in `att`, because `att` is
the LANDED-attack relation and `crit.py` says "a bare verdict is never an edge".

Measured on the two M3 arms, which is what settles it:

    C0P blind      52 critic artifacts:  3 warranted, 49 unwarranted; 46 scrutiny events
    C1I informed   38 critic artifacts:  1 warranted, 37 unwarranted; 36 scrutiny events

So criticism is ABUNDANT and landing is RARE. The old instrument was reading
only the 3 and the 1, which is why it saw a saturated 1.000 sustain rate: every
edge in `att` is by construction an attack that landed. It was measuring its own
definition.

## The measures this instrument reports

**LAND RATE** — warranted objections / all objections. The old "sustain rate"
asked "of the attacks that landed, how many landed?", which can only be 1.000.
This asks the question that was meant: of everything the critic raised, how much
stuck.

**RE-RAISE RATE** — over targets carrying two or more objections, the share of
later objections that restate an earlier one on the same target, at the 0.80
Jaccard similarity fixed before the arms finished. Now computable: the arms have
35 and 25 scrutinised targets, some with two objections each.

**OBJECTION VOLUME** — how much criticism was raised at all. Not
pre-registered, reported as descriptive.

Usage: measure_criticism_v2.py <run-root> [<run-root> ...]
"""

from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys

RESTATEMENT_SIMILARITY = 0.80


def _tokens(text: str) -> set[str]:
    return {w.strip(".,;:()\"'").lower() for w in text.split() if len(w) > 3}


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _text(state, artifact_id: str) -> str:
    art = state.artifacts.get(artifact_id)
    if art is None:
        return ""
    ref = getattr(art, "content_ref", "") or ""
    if not ref.startswith("inline:"):
        return ""
    raw = ref[len("inline:") :]
    try:
        body = json.loads(raw)
    except Exception:  # noqa: BLE001
        return " ".join(raw.split())
    if isinstance(body, dict):
        return " ".join(
            str(body.get("claim") or body.get("content") or body.get("case") or "").split()
        )
    return " ".join(str(body).split())


def report(root: pathlib.Path) -> None:
    from deepreason.harness import Harness

    state = Harness(root, read_only=True).state

    # every objection, landed or not, with the target it was aimed at
    scrutiny: list[tuple[str, str]] = []  # (target, critic artifact)
    for line in (root / "log.jsonl").open(encoding="utf-8"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        inputs = event.get("inputs") or []
        if event.get("rule") == "Measure" and inputs and inputs[0] == "scrutiny":
            scrutiny.append((str(inputs[1]), str(inputs[2])))

    landed = [(a, t) for a, t in state.att]
    n_landed, n_scrutiny = len(landed), len(scrutiny)
    total = n_landed + n_scrutiny

    by_target: dict[str, list[str]] = {}
    for target, critic in scrutiny:
        by_target.setdefault(target, []).append(critic)

    # re-raise: on targets with 2+ objections, do later ones restate earlier ones
    pairs = restated = 0
    for target, critics in by_target.items():
        if len(critics) < 2:
            continue
        texts = [_tokens(_text(state, c)) for c in critics]
        for i, j in itertools.combinations(range(len(texts)), 2):
            if not texts[i] or not texts[j]:
                continue
            pairs += 1
            restated += _similarity(texts[i], texts[j]) >= RESTATEMENT_SIMILARITY

    print(f"\n=== {root} ===")
    print(f"  objections raised, total       : {total}")
    print(f"    landed (warranted, in att)   : {n_landed}")
    print(f"    not landed (scrutiny events) : {n_scrutiny}")
    print(
        f"  LAND RATE                      : "
        f"{n_landed / total:.3f}" if total else "  LAND RATE : n/a"
    )
    print(f"  distinct targets scrutinised   : {len(by_target)}")
    print(f"  comparable objection pairs     : {pairs}")
    print(
        f"  RE-RAISE RATE                  : "
        f"{restated / pairs:.3f}" if pairs else "  RE-RAISE RATE : n/a (no target carries 2 objections)"
    )
    print(
        f"  (restatement threshold {RESTATEMENT_SIMILARITY} Jaccard similarity, "
        "fixed before the arms finished)"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+")
    a = ap.parse_args()
    for r in a.roots:
        report(pathlib.Path(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
