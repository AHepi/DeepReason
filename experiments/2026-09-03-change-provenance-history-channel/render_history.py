"""Render the PROTOTYPE history section for the M1 H1 and M3 C1 arms.

OFFLINE. Reads a run root READ-ONLY and writes a text block that
`deepreason scratch add --file` injects into the home's advisory scratchpad,
where the ordinary attention pack can surface it. No file under `src/` is
touched, which is the window instruction's own constraint on these arms and
the reason a positive M1 licenses "history content helps" rather than "the
query surface works" (PREREG.md residue #2).

The root is opened with `Harness(root, read_only=True)`. That is not a
stylistic choice: CLAUDE.md records that a writable open REPAIRS a root, which
destroys the evidence being measured.

## What goes in each section, fixed in PREREG.md before any arm ran

M1 (`--mode conjecturer`), in this order and nothing else:

  1. every artifact on the target problem whose status is REFUTED, with its
     claim and the attacking artifact that carries the refutation;
  2. every FAILED attack -- an attack edge whose target is NOT refuted;
  3. no winning lineage, no accepted claim the seat would otherwise not see.

That composition IS the anti-attractor hypothesis (monitor's reading point 4,
the operator's R8) turned into a fixed render, so M1 tests it instead of
assuming it. Showing the winner is what a basin attractor would look like, so
the winner is exactly what is withheld.

M3 (`--mode critic`): the target's rebuttal and discharge history -- for each
artifact under criticism, the objections already raised against it and whether
each was discharged. A critic today sees none of this: `rules/crit.py` carries
no context-policy, context-request or retrieval-channel path at all.

## Two instruments, cross-checked rather than trusted

The artifact->problem map is read from `state.addr`. `measure_diversity_per_problem.py`
derives the same map independently from `Conj` events in the log. `--check-map`
compares them and reports disagreement rather than silently preferring one; on
the frontier root both give 259 entries.

## The cap

4,000 characters, and it is a JUDGEMENT anchored to a measurement rather than
a measurement itself (PREREG.md residue #6). `conjecturer.turn.v6` prompts on
committed roots run 19,976-26,867 chars of which 60.0-81.4% is the JSON schema
(`SCHEMA_SHARE.txt`), leaving roughly 5,000-11,000 chars for everything else.
Truncation is reported in the block itself, never silent: a section that
silently dropped its tail would make the arm unfalsifiable.

Usage:
    render_history.py <run-root> --mode conjecturer|critic [--problem ID]
                      [--cap 4000] [--out FILE] [--check-map]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CAP_DEFAULT = 4000

# Per-claim cap. Without it one long artifact eats the whole section: the
# frontier root carries claims that are multi-line POINT lists hundreds of
# characters long, and a single one of those would crowd out every other
# entry, turning "what has already been refuted" into "one thing has been
# refuted". Truncation is marked in the text, never silent.
CLAIM_CAP = 240


def _claim(state, artifact_id: str) -> str:
    """The artifact's claim text, or a typed absence -- never a guess.

    An inline body that is not JSON is USED AS TEXT rather than discarded, and
    that is a correction the record forced. Criticism artifacts store plain
    prose -- "critic: frontier-wellformed@v1 failed on 170213d1670b" -- so an
    earlier version of this function returned "(inline body is not JSON)" for
    400 of 400 attackers sampled on the pc2-rematch root. The "refuted by" and
    "objection" lines, which are half of what these sections exist to show,
    were therefore empty of content while looking populated.
    """
    art = state.artifacts.get(artifact_id)
    if art is None:
        return "(artifact not in state)"
    ref = getattr(art, "content_ref", "") or ""
    if not ref.startswith("inline:"):
        return f"(content not inline: {ref[:40]})"
    raw = ref[len("inline:") :]
    try:
        body = json.loads(raw)
    except Exception:  # noqa: BLE001
        body = None
    if isinstance(body, dict):
        claim = body.get("claim") or body.get("content") or ""
    else:
        claim = raw
    claim = " ".join(str(claim).split())
    if not claim:
        return "(no claim text)"
    if len(claim) > CLAIM_CAP:
        claim = claim[: CLAIM_CAP - 3].rstrip() + "..."
    return claim


def _status(state, artifact_id: str) -> str:
    value = state.status.get(artifact_id)
    return getattr(value, "name", str(value)) if value is not None else "UNSET"


def _seed_problem(state) -> str | None:
    for pid in state.problems:
        if str(pid).startswith("question-"):
            return str(pid)
    return None


def _conj_map_from_log(root: Path) -> dict[str, str]:
    """The independent map, for --check-map."""
    mapping: dict[str, str] = {}
    log = root / "log.jsonl"
    if not log.exists():
        return mapping
    with log.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("rule") != "Conj":
                continue
            inputs = event.get("inputs") or []
            if not inputs:
                continue
            for artifact in (event.get("state_diff") or {}).get("A+", []):
                mapping[artifact] = inputs[0]
    return mapping


def _addr_map(state) -> dict[str, str]:
    """artifact -> problem, from `state.addr`.

    `addr` materializes as a LIST of (artifact, problem) pairs rather than a
    mapping, so it is converted here in one place instead of being indexed as
    a dict at three call sites.
    """
    return {str(a): str(p) for a, p in state.addr}


def _on_problem(state, problem: str | None) -> set[str]:
    if problem is None:
        return set(state.status)
    return {a for a, p in _addr_map(state).items() if p == problem}


def _conjecturer_section(state, problem: str | None) -> list[str]:
    scope = _on_problem(state, problem)
    attacks = [(a, t) for (a, t) in state.att if t in scope]

    refuted = sorted(a for a in scope if _status(state, a) == "REFUTED")
    attacker_of: dict[str, list[str]] = {}
    for attacker, target in attacks:
        attacker_of.setdefault(target, []).append(attacker)

    lines: list[str] = []
    lines.append("WHAT HAS ALREADY BEEN REFUTED ON THIS PROBLEM")
    lines.append(
        "These claims were proposed and did NOT survive criticism. They are "
        "shown so they are not proposed again in another form. The claims that "
        "DID survive are deliberately not listed here."
    )
    if not refuted:
        lines.append("  (nothing refuted yet)")
    for artifact in refuted:
        lines.append(f"  - REFUTED: {_claim(state, artifact)}")
        for attacker in sorted(attacker_of.get(artifact, []))[:2]:
            lines.append(f"      refuted by: {_claim(state, attacker)}")

    failed = sorted(
        (a, t) for (a, t) in attacks if _status(state, t) != "REFUTED"
    )
    lines.append("")
    lines.append("ATTACKS THAT WERE TRIED AND DID NOT LAND")
    lines.append(
        "These objections were raised and failed to change the target's "
        "status. Raising them again is unlikely to be productive."
    )
    if not failed:
        lines.append("  (no failed attacks yet)")
    for attacker, target in failed:
        lines.append(f"  - objection: {_claim(state, attacker)}")
        lines.append(f"      against : {_claim(state, target)}")
        lines.append(f"      outcome : target is {_status(state, target)}")
    return lines


def _critic_section(state, problem: str | None) -> list[str]:
    scope = _on_problem(state, problem)
    attacks = [(a, t) for (a, t) in state.att if t in scope]
    by_target: dict[str, list[str]] = {}
    for attacker, target in attacks:
        by_target.setdefault(target, []).append(attacker)

    lines: list[str] = []
    lines.append("OBJECTIONS ALREADY RAISED AGAINST THESE TARGETS")
    lines.append(
        "For each target, the objections already made and how each turned out. "
        "An objection marked SUSTAINED changed the target's status; one marked "
        "NOT SUSTAINED did not, and the target answered it."
    )
    if not by_target:
        lines.append("  (no objections recorded yet)")
    for target in sorted(by_target):
        lines.append(f"  TARGET: {_claim(state, target)}")
        lines.append(f"    current status: {_status(state, target)}")
        sustained = _status(state, target) == "REFUTED"
        for attacker in sorted(by_target[target]):
            mark = "SUSTAINED" if sustained else "NOT SUSTAINED"
            lines.append(f"    - [{mark}] {_claim(state, attacker)}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--mode", choices=("conjecturer", "critic"), required=True)
    parser.add_argument("--problem", default=None)
    parser.add_argument("--cap", type=int, default=CAP_DEFAULT)
    parser.add_argument("--out", default=None)
    parser.add_argument("--check-map", action="store_true")
    args = parser.parse_args()

    from deepreason.harness import Harness

    root = Path(args.root)
    harness = Harness(root, read_only=True)
    state = harness.state

    if args.check_map:
        from_log = _conj_map_from_log(root)
        from_state = _addr_map(state)
        both = set(from_log) & set(from_state)
        disagree = sorted(a for a in both if from_log[a] != from_state[a])
        print(
            json.dumps(
                {
                    "probe": "ARTIFACT_PROBLEM_MAP_AGREEMENT_V1",
                    "from_state_addr": len(from_state),
                    "from_conj_events": len(from_log),
                    "in_both": len(both),
                    "disagreements": len(disagree),
                    "only_in_log": len(set(from_log) - set(from_state)),
                    "only_in_state": len(set(from_state) - set(from_log)),
                },
                indent=2,
            )
        )
        return 0

    problem = args.problem or _seed_problem(state)
    header = [
        "=== PRIOR HISTORY ON THIS PROBLEM (advisory, non-grounding) ===",
        f"problem: {problem}",
        "This is a record of what has already been tried. It is advisory "
        "material, not evidence, and it decides nothing.",
        "",
    ]
    body = (
        _conjecturer_section(state, problem)
        if args.mode == "conjecturer"
        else _critic_section(state, problem)
    )
    text = "\n".join(header + body)

    truncated = False
    if len(text) > args.cap:
        text = text[: args.cap - 120].rstrip()
        truncated = True
        text += (
            "\n\n[TRUNCATED at the pre-registered "
            f"{args.cap}-character cap; earlier entries shown, later ones omitted]"
        )

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(
            json.dumps(
                {
                    "wrote": args.out,
                    "mode": args.mode,
                    "problem": problem,
                    "chars": len(text),
                    "cap": args.cap,
                    "truncated": truncated,
                },
                indent=2,
            )
        )
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
