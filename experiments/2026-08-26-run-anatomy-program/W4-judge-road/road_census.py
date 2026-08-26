#!/usr/bin/env python3
"""W4 Q2: walk the judge road, event by event, and name where each case died.

THE ROAD, as the code defines it. Two legs. Leg 1 is upstream, in
`rules/crit.py::_crit_argumentative_batch_result`; leg 2 is the trial
itself, in `informal/trial.py::_argument_trial_steps`. Each gate below is
transcribed from the source in source order, with the TYPED MARKER the
record leaves when a case terminates there. A gate with no marker is
marked `inferred` and never counted as if it were observed.

LEG 1 -- from a criticism dispatch to the trial door
  U0  a batch criticism dispatch happens          LLMCall(role=argumentative_critic)
  U1  the case names a target in this batch       (no marker; skipped silently)
  U2  case.attack and case.case.strip()           (no marker; registers nothing)
  U3  try_counterexample grounds it               a DEMONSTRATIVE warrant appears
  U4  execution supremacy takes it                Measure["arg-crit-overridden-by-execution", target]
  U5  THE AUTHORITY GATE                          observe_only -> Measure["scrutiny", target, critic]
                                                  trial_required -> leg 2
  U6  no adapter (crash recovery)                 Measure["defended-trial-deferred", target, "recovery-no-provider"]

LEG 2 -- inside `_argument_trial_steps`, in source order
  T1  defender/judge role present                 Measure["trial-declined", target, "no-defender-role"|"no-judge-role"]
  T2  target resolvable                           ... "unknown-target"
  T3  ensemble adequacy                           ... "single-judge-seat"|"no-critic-school"|"same-school-critic"
                                                  (multi-model runs instead RAISE from require_cross_family_judges)
  T4  formal supremacy                            ... "execution-backed"
  T5  non-empty case                              ... "empty-case"
  --  defender call                               LLMCall(role=defender)
  T6  judge ensemble unanimous                    ... "ensemble-split"        <- judge calls precede
  T7  the unanimous verdict is `fail`             ... "defence-sustained"
  T8  every decisive_point quotes the exchange    ... "referential-integrity"
  T9  paraphrase invariance                       ... "ensemble-split" (re-ruling) | "paraphrase-flip"
  T10 WARRANT MINTED                              a warrant with type ARGUMENTATIVE

`ensemble-split` is the one AMBIGUOUS marker: T6 and T9 spell it
identically, deliberately ("renaming it would change what those roots'
diagnostics mean" -- trial.py). This instrument disambiguates them
structurally, never by prose: a T9 split is preceded by an
LLMCall(role="variator") since the trial's own start, a T6 split is not.
Any split it cannot place that way is reported as `ensemble-split:
unplaced` rather than assigned.

Writes road_census.json. Roots are read as text; no Harness is opened and
nothing is written inside a root.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / "road_census.json"

ROOTS = {
    "P-R1": "experiments/2026-08-25-poietics-program/run",
    "GEX": "experiments/2026-08-12-live-grounded-extension-expansion/run",
}

# Marker -> (leg, gate id, human name). Order is the road's order.
LEG1 = {
    "arg-crit-overridden-by-execution": ("U4", "execution supremacy (upstream)"),
    "scrutiny": ("U5", "AUTHORITY GATE: observe_only"),
    "defended-trial-deferred": ("U6", "no adapter (crash recovery)"),
}
DECLINE_GATE = {
    "no-defender-role": "T1",
    "no-judge-role": "T1",
    "unknown-target": "T2",
    "single-judge-seat": "T3",
    "no-critic-school": "T3",
    "same-school-critic": "T3",
    "execution-backed": "T4",
    "empty-case": "T5",
    "ensemble-split": "T6/T9",
    "defence-sustained": "T7",
    "referential-integrity": "T8",
    "paraphrase-flip": "T9",
}
# Gates reached only AFTER the defender and judge seats have spent. A decline
# at one of these proves the trial CONVENED; a decline before them proves it
# was refused at the door.
CONVENED_GATES = {"T6", "T6/T9", "T7", "T8", "T9"}


def read_log(root: Path) -> list[dict]:
    events = []
    with (root / "log.jsonl").open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def warrant_census(root: Path) -> dict:
    """Every warrant in the root, split by MINT SITE.

    A trial-minted warrant is `w:argtrial:<case_hash>:<target>`
    (`trial.py::_argument_trial_steps`); a commitment verdict mints
    `w:<commitment>:<target>` (`rules/warrants.py::register_fail_warrant`).
    The id prefix is therefore the MINT SITE, and the mint site is the
    question -- `WarrantType.ARGUMENTATIVE` alone would not separate a
    trial's warrant from any other argumentative mint, and
    `DR-CON-warrants-and-attacks` is explicit that the edge builder is
    BLIND to `WarrantType`.

    Two stores exist across the roots and both are read: a dedicated
    `objects/warrant/` directory (the grounded-extension root) and
    warrants carried inline on the artifact record (P-R1). Reading only
    one silently returns zero on the other, which is how a census reports
    "no trial warrants" for a run that minted eight.
    """
    counts: dict[str, int] = {}
    ids: list[str] = []
    wdir = root / "objects" / "warrant"
    if wdir.exists():
        for path in sorted(wdir.glob("*.json")):
            record = json.loads(path.read_text())
            warrant = record.get("data", record)
            wid = str(warrant.get("id", ""))
            site = "argtrial" if wid.startswith("w:argtrial:") else "commitment"
            key = f"{site}/{warrant.get('type', '?')}"
            counts[key] = counts.get(key, 0) + 1
            if site == "argtrial":
                ids.append(wid)
    adir = root / "objects" / "artifact"
    if adir.exists():
        for path in sorted(adir.glob("*.json")):
            record = json.loads(path.read_text())
            for warrant in (record.get("data", record).get("warrants") or ()):
                wid = warrant if isinstance(warrant, str) else str(warrant.get("id", ""))
                wtype = "?" if isinstance(warrant, str) else str(warrant.get("type", "?"))
                site = "argtrial" if wid.startswith("w:argtrial:") else "commitment"
                key = f"inline:{site}/{wtype}"
                counts[key] = counts.get(key, 0) + 1
                if site == "argtrial" and wid not in ids:
                    ids.append(wid)
    return {"by_mint_site": dict(sorted(counts.items())), "argtrial_warrant_ids": sorted(ids)}


def _parse_completion(text: str):
    """Parse a raw provider completion, undoing ONE normalization: a
    markdown code fence around the JSON body.

    The harness's own repair path accepts a fenced body (`llm/repair.py`),
    so a census that refused it would report 100 of 123 grounded-extension
    dispatches as unreadable and shrink the funnel's denominator to the
    subset of seats that happened not to fence. Nothing else is repaired --
    a body that is still not JSON after de-fencing is counted unreadable.
    """
    body = text.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
        if body.rstrip().endswith("```"):
            body = body.rstrip()[: -3]
    try:
        return json.loads(body)
    except ValueError:
        return None


def funnel_head(root: Path, events: list[dict]) -> dict:
    """Stage U0-U2: dispatches, cases returned, cases that claimed an attack.

    Read from each critic call's own raw completion blob, not from prose and
    not from the registered artifacts: the raw blob is what the wire contract
    actually returned, so `attack: false` is counted where the model said it
    rather than where the harness happened to register nothing.

    A blob that cannot be read is counted in `unreadable`, never skipped --
    a silently dropped dispatch would shrink the funnel's own denominator.
    """
    blobs = root / "blobs"
    dispatches = cases = attacking = non_empty_case = unreadable = 0
    for event in events:
        llm = event.get("llm") or {}
        if str(llm.get("role")) != "argumentative_critic":
            continue
        dispatches += 1
        raw = str(llm.get("raw_ref") or "")
        path = blobs / raw[:2] / raw if len(raw) > 2 else None
        if path is None or not path.exists():
            unreadable += 1
            continue
        payload = _parse_completion(path.read_text())
        if payload is None:
            unreadable += 1
            continue
        rows = payload.get("cases")
        if rows is None:  # the atomic (single-target) critic contract
            rows = [payload]
        for row in rows:
            cases += 1
            if row.get("attack"):
                attacking += 1
                if str(row.get("case") or "").strip():
                    non_empty_case += 1
    return {
        "U0_dispatches": dispatches,
        "U1_cases_returned": cases,
        "U2_cases_claiming_attack": attacking,
        "U2_cases_attack_with_non_empty_text": non_empty_case,
        "dispatch_blobs_unreadable": unreadable,
    }


def walk(name: str, rel: str) -> dict:
    root = REPO / rel
    events = read_log(root)
    dispatches = {"argumentative_critic": 0, "defender": 0, "judge": 0, "variator": 0}
    leg1: dict[str, int] = {}
    declines: list[dict] = []
    blocked: dict[str, int] = {}
    # Structural disambiguation state: a variator call since the last event
    # that could only belong to a trial's start (the defender call).
    variator_since_defender = 0
    judges_since_defender = 0
    for event in events:
        llm = event.get("llm") or {}
        role = str(llm.get("role") or "")
        if role in dispatches:
            dispatches[role] += 1
        if role == "defender":
            variator_since_defender = 0
            judges_since_defender = 0
        elif role == "variator":
            variator_since_defender += 1
        elif role == "judge":
            judges_since_defender += 1
        inputs = [str(v) for v in (event.get("inputs") or ())]
        if not inputs:
            continue
        signal = inputs[0]
        if signal in LEG1:
            gate = LEG1[signal][0]
            leg1[gate] = leg1.get(gate, 0) + 1
        elif signal == "trial-declined":
            reason = inputs[2] if len(inputs) > 2 else "unrecorded"
            gate = DECLINE_GATE.get(reason, "T?")
            placed = reason
            agree = None
            if reason == "ensemble-split":
                # Two INDEPENDENT structural discriminators, agreement required.
                # (a) a variator call has landed since this trial's defender
                #     call -- only `_paraphrase_screen` calls the variator
                #     inside a trial;
                # (b) more than one ensemble ruling has been spent since the
                #     defender call -- the first ruling costs exactly
                #     len(judge_seats) calls, a re-ruling costs that again.
                by_variator = "T9" if variator_since_defender > 0 else "T6"
                by_judges = "T9" if judges_since_defender > 2 else "T6"
                agree = by_variator == by_judges
                if agree:
                    gate = by_variator
                    placed = (
                        "ensemble-split (paraphrase re-ruling)"
                        if gate == "T9"
                        else "ensemble-split (first ruling)"
                    )
                else:
                    gate, placed = "T6/T9", "ensemble-split: unplaced"
            declines.append(
                {
                    "seq": event.get("seq"),
                    "target": inputs[1] if len(inputs) > 1 else None,
                    "reason": reason,
                    "gate": gate,
                    "placed": placed,
                    "judges_since_defender": judges_since_defender,
                    "variator_since_defender": variator_since_defender,
                    "discriminators_agree": agree,
                }
            )
        elif signal.startswith("trial-blocked:"):
            reason = signal.split(":", 1)[1] or "unrecorded"
            blocked[reason] = blocked.get(reason, 0) + 1
    by_gate: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    for row in declines:
        by_gate[row["gate"]] = by_gate.get(row["gate"], 0) + 1
        by_reason[row["placed"]] = by_reason.get(row["placed"], 0) + 1
    convened = sum(
        n for gate, n in by_gate.items() if gate in CONVENED_GATES
    )
    refused_at_door = len(declines) - convened
    warrants = warrant_census(root)
    minted = len(warrants["argtrial_warrant_ids"])
    unplaced = sum(1 for row in declines if row["placed"] == "ensemble-split: unplaced")
    return {
        "root": rel,
        "n_events": len(events),
        "dispatches_by_role": dispatches,
        "funnel_head": funnel_head(root, events),
        "leg1_terminators": dict(sorted(leg1.items())),
        # Every trial that enters `_argument_trial_steps` leaves it by exactly
        # one door: a `trial-declined` Measure, or a minted argtrial warrant.
        "trials_entered": len(declines) + minted,
        "trials_declined": len(declines),
        "trials_sustained_warrant_minted": minted,
        "declines_by_gate": dict(sorted(by_gate.items())),
        "declines_by_reason": dict(sorted(by_reason.items())),
        "ensemble_split_unplaced": unplaced,
        "trial_blocked": dict(sorted(blocked.items())),
        "trials_convened_judge_spent": convened + minted,
        "trials_refused_at_the_door": refused_at_door,
        "warrants": warrants,
        "declines": declines,
    }


def main() -> int:
    payload = {
        "schema": "w4.road-census.v1",
        "roots": {name: walk(name, rel) for name, rel in ROOTS.items()},
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    for name, row in payload["roots"].items():
        print(f"== {name} {row['root']}")
        for key in (
            "dispatches_by_role",
            "funnel_head",
            "leg1_terminators",
            "trials_entered",
            "trials_declined",
            "trials_sustained_warrant_minted",
            "declines_by_gate",
            "declines_by_reason",
            "ensemble_split_unplaced",
            "trials_convened_judge_spent",
            "trials_refused_at_the_door",
            "warrants",
        ):
            print(f"   {key}: {row[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
