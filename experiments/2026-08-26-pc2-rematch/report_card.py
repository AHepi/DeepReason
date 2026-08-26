#!/usr/bin/env python3
"""PREREG.md §7's report card, computed by the COMMITTED instruments.

NOTHING HERE RE-DERIVES A METRIC.  Every number comes from an instrument the
run-anatomy program already wrote, invoked exactly as its own tranche
invoked it -- as a subprocess where it is a CLI, by function where it is a
library:

    C1  construction validity      W1  `pc1_headline.constructions_from_root`
    C2  invented-handle rate       W1  `census.census_root`, against the
                                       COMMITTED `MESSAGE_CODE_TABLE.json`
                                       (the same classification the baselines
                                       were computed with; relearning it
                                       would let the two censuses disagree)
    C3  placebo-corrected coupling W2  `census.py` then `q5.py`, the pair,
                                       in that order, as CLIs
    C4  operator-question share    W6  `flow.scan_root` + `flow.rollup`
    C5  tokens per valid candidate derived from C4's token total and C1's
                                       valid count -- the ONE derived number,
                                       and it is a division of two measured
                                       ones

Re-deriving any of these would produce a second definition of a number whose
whole value is that it is comparable to P-C1's, and two definitions of one
metric is how a report card stops being a report card.

SELF-CHECK.  Run with `--verify-against-pc1` and it drives every instrument
on P-C1's OWN root and compares the result to PREREG.md §7's frozen
baselines.  A mismatch means this driver is wired to something other than
what produced the baselines, and it exits non-zero.  That check exists
because the failure mode of a report card is not a wrong number, it is a
number computed a different way from the one it is placed beside.

Usage:
    python report_card.py <root> [--out FILE]
    python report_card.py --verify-against-pc1
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
PROGRAM = REPO / "experiments" / "2026-08-26-run-anatomy-program"
W1 = PROGRAM / "W1-form-census"
W2 = REPO / "experiments" / "2026-08-26-run-anatomy-w2-criticism"
W6 = PROGRAM / "W6-token-flow"
FRONTIER = REPO / "experiments" / "2026-08-25-change-constructive-frontier"
PC1_ROOT = "experiments/2026-08-25-change-constructive-frontier/run"

NOT_MEASURED = "NOT MEASURED"

# PREREG.md §7, restated as data so a reader can diff code against the frozen
# document.  Each entry names the POPULATION it was measured on, because two
# different "validity rates" live in the committed record and substituting one
# for the other would manufacture a result.
BASELINES = {
    "C1_construction_validity": {
        "arm_h_mechanism_census": round(15 / 133, 4),
        "arm_h_valid": 15,
        "arm_h_constructions": 133,
        "arm_h_artifact_level": 0.1136,
        "arm_s_artifact_level": 0.434,
        "population": (
            "P-C1's ARM H root, MECHANISM census (blob-level: 15 VALID of 133 "
            "constructions the model wrote). The 11.36% / 43.4% figures are the "
            "ARTIFACT-level rates from arm_h_scores.json and arm_s_merged.jsonl "
            "and are quoted separately -- the two are not interchangeable"
        ),
        "source": "W1-form-census/PC1_HEADLINE.json (`mechanism.arm_h`)",
    },
    "C2_invented_handle": {
        "pc1_root_invented": 2,
        "pc1_root_wire_failures": 77,
        "pc1_root_wire_validity": 0.8767,
        "population_54_root_share": 0.626,
        "population": (
            "TWO POPULATIONS, never substituted: P-C1's own root (2 of 77 wire "
            "failures = 2.6%; wire validity 87.67% over 292 attempts), and the "
            "54-root population F2 cites (737 of 1178, 62.6%)"
        ),
        "source": "W1-form-census/CENSUS_PER_ROOT.json; F2 DELIVERY.md",
    },
    "C3_coupling": {
        "R1_mechanical_coupling_minus_placebo": 0.05865102639296187,
        "R1_mechanical_neglect": 0.906158357771261,
        "R2_prose_quote": "INADMISSIBLE as a rate (W2's own residue)",
        "llm_attacks_reaching_a_later_conjecture_dispatch": "0 of 196",
        "population": "P-C1's own root",
        "source": "run-anatomy-w2-criticism/pc1_q5.json",
    },
    "C4_operator_question_share": {
        "share": 0.532,
        "calls": 61,
        "tokens": 373903,
        "competing": {"audit:ritual": 0.412, "repair_reasks": 0.056},
        "population": "P-C1's ARM H root",
        "source": "W6-token-flow/PC1_POSTMORTEM.json",
    },
    "C5_tokens_per_valid_candidate": {
        "value": round(702789 / 15, 1),
        "population": "P-C1's ARM H run (702 789 log tokens / 15 valid)",
        "source": "P-C1 RESULTS.md",
    },
}


def _fail(card: dict, key: str, error: Exception) -> None:
    """A metric whose instrument cannot run is NOT MEASURED, never estimated."""
    card[key] = {
        "value": NOT_MEASURED,
        "reason": f"{type(error).__name__}: {error}",
        "baseline": BASELINES.get(key),
    }


def c1(root_rel: str, card: dict) -> None:
    """W1's mechanism census: the committed checker over every construction.

    `constructions_from_root` finds the POINT-bearing strings; `mechanism`
    runs `checker.check` over each and counts the verdicts.  Both are W1's,
    and `mechanism` is the function that produced PC1_HEADLINE.json's
    `mechanism.arm_h` block -- which is the baseline this row is compared to.
    """
    sys.path.insert(0, str(W1))
    sys.path.insert(0, str(FRONTIER))  # `mechanism` imports the committed checker
    try:
        import pc1_headline

        found = pc1_headline.constructions_from_root(root_rel)
        mech = pc1_headline.mechanism(found, "ARM H2")
        verdicts = dict(mech.get("checker_verdicts") or {})
        n = int(mech.get("constructions_found") or 0)
        valid = int(verdicts.get("VALID", 0))
        card["C1_construction_validity"] = {
            "value": round(valid / n, 4) if n else NOT_MEASURED,
            "valid": valid,
            "constructions_found": n,
            "verdicts": verdicts,
            "min_area_zero_rate": mech.get("min_area_zero_rate"),
            "zero_cause_signature": mech.get("zero_cause_signature"),
            "baseline": BASELINES["C1_construction_validity"],
        }
    except Exception as error:
        _fail(card, "C1_construction_validity", error)


def c2(root_rel: str, card: dict) -> None:
    sys.path.insert(0, str(W1))
    try:
        import census as w1_census

        table = json.loads((W1 / "MESSAGE_CODE_TABLE.json").read_text())["table"]
        doc = w1_census.census_root(root_rel, table)
        classes = dict(doc.get("failure_classes") or {})
        invented_keys = (
            "V6_WIRE_REFERENCE_INVALID",
            "SCRATCH_ALIAS_UNKNOWN",
            "BRIDGE_WIRE_REFERENCE_INVALID",
        )
        invented = sum(v for k, v in classes.items() if k in invented_keys)
        failures = sum(classes.values())
        card["C2_invented_handle"] = {
            "value": round(invented / failures, 4) if failures else NOT_MEASURED,
            "invented_handle_failures": invented,
            "wire_failures_total": failures,
            "wire_validity_rate": doc.get("validity_rate"),
            "attempts": doc.get("attempts"),
            "failure_classes": classes,
            "baseline": BASELINES["C2_invented_handle"],
        }
    except Exception as error:
        _fail(card, "C2_invented_handle", error)


def c3(root_rel: str, card: dict, workdir: Path) -> None:
    """W2's pair, as CLIs, in W2's own order."""
    try:
        census_out = workdir / "w2_census.json"
        q5_out = workdir / "w2_q5.json"
        for argv in (
            [sys.executable, str(W2 / "census.py"), root_rel, str(census_out)],
            [
                sys.executable, str(W2 / "q5.py"), root_rel, str(census_out),
                str(q5_out), "--checker", str(FRONTIER),
            ],
        ):
            done = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
            if done.returncode != 0:
                raise RuntimeError(
                    f"{Path(argv[1]).name} rc={done.returncode}: "
                    f"{(done.stderr or done.stdout)[-500:]}"
                )
        data = json.loads(q5_out.read_text())
        card["C3_coupling"] = {
            "value": {
                key: data.get(key)
                for key in ("R1_mechanical", "R2_prose_quote",
                            "n_criticism_events_total", "exposure")
            },
            "baseline": BASELINES["C3_coupling"],
        }
    except Exception as error:
        _fail(card, "C3_coupling", error)


def c4_and_c5(root_rel: str, card: dict) -> None:
    """W6's scan, attributed by W6's own committed problem-line rule.

    `flow.scan_root` produces the rows; `pc1_postmortem.PROBLEM_LINE` is the
    committed regex that says WHICH problem a call's prompt was about, and
    the seed question is the problem id beginning `question-` -- W6's own
    selector, not a new one.  The join between the two is bookkeeping, not a
    metric definition: no threshold, no taxonomy and no classification is
    introduced here.
    """
    sys.path.insert(0, str(W6))
    try:
        import flow
        import pc1_postmortem

        scanned = flow.scan_root(root_rel)
        rows = scanned.get("rows") or []
        for row in rows:
            row["fate_class"] = flow.fate_class(row)
        total = sum(r["total_tokens"] for r in rows)

        abs_root = REPO / root_rel
        prompt_ref = {}
        for line in (abs_root / "log.jsonl").open():
            event = json.loads(line)
            if event.get("llm"):
                prompt_ref[event["seq"]] = event["llm"]["prompt_ref"]
        problems = {}
        for path in sorted((abs_root / "objects" / "problem").iterdir()):
            data = json.loads(path.read_text())["data"]
            problems[data["id"]] = data.get("description")
        seed = next((p for p in problems if p.startswith("question-")), None)

        for row in rows:
            ref = prompt_ref.get(row["seq"])
            text = ""
            if ref:
                blob = abs_root / "blobs" / ref[:2] / ref
                if blob.exists():
                    text = blob.read_text(encoding="utf-8", errors="replace")
            match = pc1_postmortem.PROBLEM_LINE.search(text)
            row["problem"] = match.group(1).strip() if match else "no-problem-line-in-prompt"
            row["on_seed_question"] = row["problem"] == seed

        seed_rows = [r for r in rows if r["on_seed_question"]]
        spawned = [
            r for r in rows
            if not r["on_seed_question"] and r["problem"] != "no-problem-line-in-prompt"
        ]
        no_line = [r for r in rows if r["problem"] == "no-problem-line-in-prompt"]
        seed_tokens = sum(r["total_tokens"] for r in seed_rows)

        card["C4_operator_question_share"] = {
            "value": round(seed_tokens / total, 4) if total else NOT_MEASURED,
            "seed_question_id": seed,
            "log_total_tokens": total,
            "calls": len(rows),
            "on_the_seed_question": {"calls": len(seed_rows), "tokens": seed_tokens},
            "on_problems_the_run_spawned_for_itself": {
                "calls": len(spawned),
                "tokens": sum(r["total_tokens"] for r in spawned),
                "problem_ids": sorted({r["problem"] for r in spawned}),
            },
            "no_problem_line_in_prompt": {
                "calls": len(no_line),
                "tokens": sum(r["total_tokens"] for r in no_line),
            },
            "by_purpose": flow.rollup(rows, ("purpose",)),
            "by_call_kind": flow.rollup(rows, ("call_kind",)),
            "baseline": BASELINES["C4_operator_question_share"],
        }
        valid = (card.get("C1_construction_validity") or {}).get("valid")
        card["C5_tokens_per_valid_candidate"] = {
            "value": round(total / valid, 1) if valid else NOT_MEASURED,
            "log_total_tokens": total,
            "valid_constructions": valid,
            "baseline": BASELINES["C5_tokens_per_valid_candidate"],
        }
    except Exception as error:
        _fail(card, "C4_operator_question_share", error)
        _fail(card, "C5_tokens_per_valid_candidate", error)


def build(root_rel: str) -> dict:
    card: dict = {"schema": "pc2.report-card.v1", "root": root_rel}
    with tempfile.TemporaryDirectory() as tmp:
        c1(root_rel, card)
        c2(root_rel, card)
        c3(root_rel, card, Path(tmp))
        c4_and_c5(root_rel, card)
    return card


def verify_against_pc1() -> int:
    """Drive every instrument on P-C1's root and match PREREG §7's baselines."""
    card = build(PC1_ROOT)
    problems: list[str] = []

    got = card.get("C1_construction_validity") or {}
    if got.get("valid") != BASELINES["C1_construction_validity"]["arm_h_valid"]:
        problems.append(
            f"C1 valid={got.get('valid')} != {BASELINES['C1_construction_validity']['arm_h_valid']}"
        )

    got = card.get("C2_invented_handle") or {}
    if got.get("invented_handle_failures") != BASELINES["C2_invented_handle"]["pc1_root_invented"]:
        problems.append(
            f"C2 invented={got.get('invented_handle_failures')} != "
            f"{BASELINES['C2_invented_handle']['pc1_root_invented']}"
        )
    if got.get("wire_failures_total") != BASELINES["C2_invented_handle"]["pc1_root_wire_failures"]:
        problems.append(
            f"C2 wire_failures={got.get('wire_failures_total')} != "
            f"{BASELINES['C2_invented_handle']['pc1_root_wire_failures']}"
        )

    got = ((card.get("C3_coupling") or {}).get("value") or {}).get("R1_mechanical") or {}
    want = BASELINES["C3_coupling"]["R1_mechanical_coupling_minus_placebo"]
    if got.get("CouplingRate_minus_Placebo") != want:
        problems.append(
            f"C3 coupling-placebo={got.get('CouplingRate_minus_Placebo')} != {want}"
        )

    got = card.get("C4_operator_question_share") or {}
    if got.get("calls") not in (292,):
        problems.append(f"C4 calls={got.get('calls')} != 292 (P-C1's provider calls)")

    print(json.dumps(card, indent=1, sort_keys=True, default=str))
    if problems:
        print("\nSELF-CHECK FAILED:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("\nSELF-CHECK OK: every instrument reproduces PREREG §7's baseline on P-C1's root")
    return 0


def main() -> int:
    os.chdir(REPO)  # every instrument addresses roots repo-relative
    if "--verify-against-pc1" in sys.argv:
        return verify_against_pc1()
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    try:
        root_rel = str(root.relative_to(REPO))
    except ValueError:
        root_rel = str(root)
    card = build(root_rel)
    text = json.dumps(card, indent=1, sort_keys=True, default=str)
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
