"""M3's two record-derived measures: re-raised objections, and sustain rate.

Written BEFORE the M3 arms finished, so the thresholds cannot be chosen to suit
a result. Both measures are counted from the typed record; neither is judged.
The third M3 measure, blind-judged case sharpness, is NOT here -- it needs the
committed three-judge protocol and is reported separately or as NOT MEASURED.

## RE-RAISED ALREADY-REBUTTED OBJECTIONS

`PREREG.md` §3 fixes this: an objection is "already rebutted" when a prior
criticism on the same target did NOT change that target's status, and a later
objection on the same target is a "re-raise" when it matches an earlier one
above **0.80 Jaccard similarity** on content tokens. That is the same 0.20
distance threshold the near-duplicate rate already uses, deliberately, so the
tranche carries one similarity constant rather than two tunable ones.

Ordering comes from the log, not from file order: an attack's position is the
sequence number of the event that created the attacking artifact. Without that
the measure would count unordered pairs and could not tell a re-raise from the
original.

## SUSTAIN RATE

The share of attacked targets that ended REFUTED. An objection that changed its
target's status was sustained; one that did not was answered or ignored. This
is read from `state.status` and `state.att`, never from prose.

## What neither measure is

Neither reads whether an objection is GOOD. A critic that raises one devastating
objection and a critic that raises twelve weak ones can produce the same
numbers. That is why the registered protocol pairs them with blind judging, and
why a result on these two alone is reported as partial.

Usage: measure_criticism.py <run-root> [<run-root> ...]
"""

from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys

RESTATEMENT_SIMILARITY = 0.80  # == the 0.20 distance used by the near-dup rate


def _tokens(text: str) -> set[str]:
    return {w.strip(".,;:()\"'").lower() for w in text.split() if len(w) > 3}


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _creation_seq(root: pathlib.Path) -> dict[str, int]:
    """artifact id -> seq of the event that created it, for ordering attacks."""
    out: dict[str, int] = {}
    log = root / "log.jsonl"
    if not log.exists():
        return out
    with log.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            seq = event.get("seq")
            for artifact in (event.get("state_diff") or {}).get("A+", []):
                out.setdefault(str(artifact), int(seq or 0))
    return out


def _claim(state, artifact_id: str) -> str:
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
        return " ".join(str(body.get("claim") or body.get("content") or "").split())
    return " ".join(str(raw).split())


def report(root: pathlib.Path) -> dict:
    from deepreason.harness import Harness

    state = Harness(root, read_only=True).state
    seq = _creation_seq(root)

    by_target: dict[str, list[str]] = {}
    for attacker, target in state.att:
        by_target.setdefault(str(target), []).append(str(attacker))

    targets = len(by_target)
    attacks = sum(len(v) for v in by_target.values())
    refuted_targets = sum(
        1
        for t in by_target
        if getattr(state.status.get(t), "name", None) == "REFUTED"
    )

    # Re-raises: within one target, a LATER objection that restates an EARLIER
    # one which did not change the target's status.
    re_raised = 0
    comparable = 0
    for target, attackers in by_target.items():
        sustained = getattr(state.status.get(target), "name", None) == "REFUTED"
        ordered = sorted(attackers, key=lambda a: seq.get(a, 0))
        toks = [(_a, _tokens(_claim(state, _a))) for _a in ordered]
        for (i, (_a, ta)), (j, (_b, tb)) in itertools.combinations(
            list(enumerate(toks)), 2
        ):
            if not ta or not tb:
                continue
            comparable += 1
            # only an EARLIER objection that failed can be "already rebutted"
            if not sustained and _similarity(ta, tb) >= RESTATEMENT_SIMILARITY:
                re_raised += 1

    return {
        "root": str(root),
        "attacked_targets": targets,
        "attack_edges": attacks,
        "targets_refuted": refuted_targets,
        "sustain_rate": (refuted_targets / targets) if targets else None,
        "comparable_objection_pairs": comparable,
        "re_raised_pairs": re_raised,
        "re_raise_rate": (re_raised / comparable) if comparable else None,
        "restatement_similarity_threshold": RESTATEMENT_SIMILARITY,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+")
    args = parser.parse_args()
    for raw in args.roots:
        r = report(pathlib.Path(raw))
        print(f"\n=== {r['root']} ===")
        print(f"  attacked targets            : {r['attacked_targets']}")
        print(f"  attack edges                : {r['attack_edges']}")
        print(f"  targets ending REFUTED      : {r['targets_refuted']}")
        sr = r["sustain_rate"]
        print(f"  SUSTAIN RATE                : {'n/a' if sr is None else f'{sr:.3f}'}")
        print(f"  comparable objection pairs  : {r['comparable_objection_pairs']}")
        print(f"  re-raised pairs             : {r['re_raised_pairs']}")
        rr = r["re_raise_rate"]
        print(f"  RE-RAISE RATE               : {'n/a' if rr is None else f'{rr:.3f}'}")
        print(
            f"  (restatement threshold {r['restatement_similarity_threshold']} "
            "Jaccard similarity, fixed before the arms finished)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
