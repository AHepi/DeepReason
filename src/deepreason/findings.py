"""Reader-facing findings report, rendered deterministically from the record.

Everything an end user needs to know — what was established, what remains
contested, what is hedged or unverified, and what evidence was fetched,
refused, cited, or wasted — already exists in the append-only log as typed
records. This module translates that record into plain language with no
model in the loop, so the report can never claim more than the record
holds. Hashes are demoted to bracketed footnote handles.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


_CLAIM_CHARS = 600


def _clip(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= _CLAIM_CHARS:
        return text
    return text[:_CLAIM_CHARS] + "…"


def _claim_text(artifact) -> str:
    content = artifact.content_ref.removeprefix("inline:")
    try:
        value = json.loads(content)
    except (TypeError, ValueError):
        return _clip(str(content))
    if isinstance(value, dict):
        # Process bookkeeping is not a position a reader should weigh.
        if "school_policy" in value or value.get("schema") in {
            "attached-source-record.v1",
        }:
            return ""
        for key in ("claim", "content", "statement"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return _clip(text)
    return _clip(str(content))


def _atomic_write(path: Path, body: str) -> None:
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(body, encoding="utf-8")
    os.replace(temporary, path)


def write_findings_report(root: Path | str) -> Path | None:
    """Write FINDINGS.md beside the run's other reader files.

    Purely replay-derived; returns None (writing nothing) when the root is
    not a bound v5/v6 run. Never raises into its caller — a reporting
    failure must not fail a run's publication.
    """

    from deepreason.capabilities.models import (
        ResearchConsumptionV1,
        ResearchExecutionReceiptV1,
    )
    from deepreason.harness import Harness
    from deepreason.ontology import Status
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    root = Path(root)
    try:
        manifest = load_run_manifest(root / MANIFEST_NAME)
        if manifest.schema_version not in {5, 6}:
            return None
        harness = Harness(root, read_only=True)
    except Exception:  # noqa: BLE001 - reporting never fails publication
        return None

    lines: list[str] = ["# Findings", ""]
    try:
        from deepreason.evidence.state import load_run_input

        question = load_run_input(root).problem.description
        lines += ["## Question", "", question, ""]
    except Exception:  # noqa: BLE001
        pass

    # Evidence bookkeeping (candidate evidence carrying fetched text and
    # its reliability nodes) is provenance, not a position to weigh.
    evidence_bookkeeping: set[str] = set()
    for consumption in harness.capability_state.consumptions.values():
        if not isinstance(consumption, ResearchConsumptionV1):
            continue
        for evidence_ref in consumption.evidence_refs:
            evidence_bookkeeping.add(evidence_ref)
            evidence = harness.state.artifacts.get(evidence_ref)
            if evidence is not None:
                evidence_bookkeeping.update(
                    ref.target for ref in evidence.interface.refs
                )

    accepted: list[tuple[str, str]] = []
    refuted: list[tuple[str, str]] = []
    for artifact_id, artifact in harness.state.artifacts.items():
        if artifact_id in evidence_bookkeeping:
            continue
        text = _claim_text(artifact)
        if not text:
            continue
        status = harness.state.status.get(artifact_id)
        if status == Status.ACCEPTED:
            accepted.append((artifact_id, text))
        elif status == Status.REFUTED:
            refuted.append((artifact_id, text))

    lines += ["## Positions the record accepts", ""]
    if not accepted:
        lines += ["No formally accepted position survived criticism.", ""]
    else:
        if len(accepted) > 1:
            lines += [
                f"{len(accepted)} positions stand formally accepted. Where "
                "they answer the same question differently they are "
                "unresolved rivals: the record deliberately preserves the "
                "disagreement rather than merging it.",
                "",
            ]
        for artifact_id, text in accepted:
            lines.append(f"- {text} `[{artifact_id[:12]}]`")
        lines.append("")
    if refuted:
        lines += ["## Positions the record refuted", ""]
        for artifact_id, text in refuted:
            lines.append(f"- {text} `[{artifact_id[:12]}]`")
        lines.append("")

    # The latest composed view, when one exists, in its own words.
    try:
        from deepreason.application.bridge import load_snapshot

        snapshot = load_snapshot(root)
        output = snapshot.output
        if output is not None:
            lines += [
                "## Latest composed view",
                "",
                f"Resolution: **{output.resolution.value}** "
                f"(composed at formal sequence {snapshot.terminal.formal_seq}; "
                "supersedable — no answer is final).",
                "",
            ]
            for section in output.sections:
                lines.append(f"> {' '.join(section.text.split())}")
            if output.resolution_reason:
                lines += ["", f"Why not fully answered: {output.resolution_reason}"]
            unresolved = getattr(output, "unresolved_items", ()) or ()
            if unresolved:
                lines += ["", "Open items the composer refused to smooth over:", ""]
                for item in unresolved:
                    lines.append(f"- {getattr(item, 'description', item)}")
            lines.append("")
    except Exception:  # noqa: BLE001 - a bridge-free run still reports
        pass

    events = list(harness.log.read())
    citation_counts: dict[str, int] = {}
    for event in events:
        signal = str(event.inputs[0]) if event.inputs else ""
        if signal.startswith("evidence-citation:"):
            code = signal.split(":", 1)[1]
            citation_counts[code] = citation_counts.get(code, 0) + 1
    receipts = [
        receipt
        for receipt in harness.capability_state.receipts.values()
        if isinstance(receipt, ResearchExecutionReceiptV1)
    ]
    consumptions = [
        consumption
        for consumption in harness.capability_state.consumptions.values()
        if isinstance(consumption, ResearchConsumptionV1)
    ]

    hedges: list[str] = []
    for receipt in receipts:
        for attempt in receipt.attempts:
            if attempt.outcome != "FETCHED":
                hedges.append(
                    f"- Fetch refused (`{attempt.outcome}`): {attempt.url} — "
                    "any claim needing this source stayed unverified."
                )
    verified = citation_counts.get("EVIDENCE_CITATION_VERIFIED", 0)
    failed_citations = sum(
        count
        for code, count in citation_counts.items()
        if code != "EVIDENCE_CITATION_VERIFIED"
    )
    if failed_citations:
        detail = ", ".join(
            f"{count}× {code}"
            for code, count in sorted(citation_counts.items())
            if code != "EVIDENCE_CITATION_VERIFIED"
        )
        hedges.append(
            f"- {failed_citations} claimed citation(s) failed their "
            f"deterministic check ({detail}); those groundings are NOT "
            "established."
        )
    if hedges:
        lines += ["## Hedged and unverified", "", *hedges, ""]

    if receipts or consumptions or verified:
        lines += ["## Evidence trail", ""]
        for receipt in receipts:
            for attempt in receipt.attempts:
                if attempt.outcome == "FETCHED":
                    lines.append(
                        f"- Fetched: {attempt.url} "
                        f"({attempt.byte_count} bytes, content "
                        f"`{(attempt.content_sha256 or '')[:12]}`)"
                    )
        for consumption in consumptions:
            lines.append(
                f"- Consumed into {len(consumption.evidence_refs)} candidate "
                "evidence record(s) with byte-checkable citable blocks."
            )
        lines.append(
            f"- Byte-verified citations of admitted evidence: {verified}."
        )
        lines.append("")

    lines += [
        "---",
        "Every statement above is derived from the append-only run record; "
        "nothing was generated by a model for this report. Accepted does "
        "not mean true — it means the position survived recorded criticism "
        "so far, and the run remains continuable.",
        "",
    ]
    target = root / "FINDINGS.md"
    try:
        _atomic_write(target, "\n".join(lines))
    except OSError:
        return None
    return target


def findings_summary(root: Path | str) -> dict:
    """Reader-facing findings for a run root, replay-derived, JSON-able.

    Everything FINDINGS.md carries, plus the structure it flattens away:
    rivalry groups (competitors per problem), refutations with their
    recorded attackers, suspended positions, every spawned side branch
    with its worked/starved status, and the criticism and capability
    ledgers. Raises ValueError on an unreadable root — callers surface
    that; only the passive FINDINGS.md writer swallows errors.
    """

    import json as _json

    from deepreason.capabilities.models import (
        ResearchConsumptionV1,
        ResearchExecutionReceiptV1,
        ResearchFetchProposalV1,
        SimulationProposalV1,
    )
    from deepreason.harness import Harness
    from deepreason.ontology import Status

    root = Path(root)
    if not (root / "log.jsonl").exists():
        raise ValueError(f"not a run root (no log.jsonl): {root}")
    harness = Harness(root, read_only=True)
    state = harness.state

    summary: dict = {"schema": "deepreason-findings.v1", "root": str(root)}

    try:
        from deepreason.evidence.state import load_run_input

        summary["question"] = load_run_input(root).problem.description
    except Exception:  # noqa: BLE001 - legacy roots carry no run input
        summary["question"] = None

    status_path = root / "run-status.json"
    if status_path.exists():
        raw = _json.loads(status_path.read_text())
        summary["run"] = {
            key: raw.get(key)
            for key in ("state", "stop_reason", "message", "cycle",
                        "token_spend", "token_limit")
        }
    else:
        summary["run"] = None

    # Positions by status, with problem addressing for rivalry grouping.
    addressed: dict[str, list[str]] = {}
    for artifact_id, problem_id in state.addr:
        addressed.setdefault(artifact_id, []).append(problem_id)
    by_status: dict[str, list[dict]] = {
        "accepted": [], "refuted": [], "suspended": [],
    }
    for artifact_id, artifact in state.artifacts.items():
        text = _claim_text(artifact)
        if not text:
            continue
        status = state.status.get(artifact_id)
        row = {
            "id": artifact_id[:12],
            "claim": text,
            "role": artifact.provenance.role.value,
            "problems": sorted(addressed.get(artifact_id, [])),
        }
        if status == Status.ACCEPTED:
            by_status["accepted"].append(row)
        elif status == Status.REFUTED:
            by_status["refuted"].append(row)
        elif status in (Status.SUSPENDED, Status.SUSPENDED_UNSUPPORTED):
            row["status"] = status.value
            by_status["suspended"].append(row)
    summary["positions"] = by_status

    # Competitors: problems where several accepted positions stand as
    # unresolved rivals.
    rivals_by_problem: dict[str, list[str]] = {}
    for row in by_status["accepted"]:
        for problem_id in row["problems"]:
            rivals_by_problem.setdefault(problem_id, []).append(row["id"])
    summary["rivalries"] = [
        {"problem": problem_id, "rival_count": len(ids), "rivals": ids}
        for problem_id, ids in sorted(rivals_by_problem.items())
        if len(ids) >= 2
    ]

    # Refutation attribution: who attacked what, from the state's attack
    # relation (all roots) and typed criticism attempts (v6 roots).
    attacks: list[dict] = []
    for attacker, target in state.att:
        attacks.append({
            "attacker": attacker[:12],
            "target": target[:12],
            "kind": "attack",
        })
    attempts_dir = root / "objects" / "criticism-attempt-v1"
    criticism_attempts = 0
    if attempts_dir.is_dir():
        for record_path in attempts_dir.iterdir():
            record = _json.loads(record_path.read_bytes())
            data = record.get("data", record)
            criticism_attempts += 1
            attacks.append({
                "attacker": f"critic:{data.get('critic_school_id')}",
                "target": str(data.get("target_id", ""))[:12],
                "kind": "argumentative",
                "outcome": data.get("outcome"),
            })
    refuted_ids = {row["id"] for row in by_status["refuted"]}
    for row in by_status["refuted"]:
        row["attacked_by"] = [
            attack["attacker"] for attack in attacks
            if attack["target"] == row["id"]
        ]
    debt_dir = root / "objects" / "criticism-coverage-debt-v1"
    summary["criticism"] = {
        "attacks_recorded": len(attacks),
        "criticism_attempts": criticism_attempts,
        "coverage_debt_records": (
            len(list(debt_dir.iterdir())) if debt_dir.is_dir() else 0
        ),
        "attacks_on_refuted": sum(
            1 for attack in attacks if attack["target"] in refuted_ids
        ),
    }

    # Side branches: every spawned problem, what worked it, what starved.
    branches: list[dict] = []
    worked_by_problem: dict[str, int] = {}
    for problem_ids in addressed.values():
        for problem_id in problem_ids:
            worked_by_problem[problem_id] = worked_by_problem.get(problem_id, 0) + 1
    for problem_id, problem in state.problems.items():
        branches.append({
            "problem": problem_id,
            "trigger": problem.provenance.trigger.value,
            "description": _clip(problem.description),
            "positions_addressing": worked_by_problem.get(problem_id, 0),
        })
    branches.sort(key=lambda row: (row["trigger"], row["problem"]))
    summary["branches"] = branches
    summary["starved_branches"] = [
        row["problem"] for row in branches if row["positions_addressing"] == 0
    ]

    # Capability ledger: typed proposals with their terminal lifecycle,
    # plus the byte-checked citation counts.
    capability_rows: list[dict] = []
    capability_state = harness.capability_state
    for proposal_id, proposal in capability_state.proposals.items():
        ref = capability_state.current_transition_by_request.get(proposal_id)
        transition = capability_state.transitions.get(ref) if ref else None
        kind = (
            "simulation" if isinstance(proposal, SimulationProposalV1)
            else "research" if isinstance(proposal, ResearchFetchProposalV1)
            else type(proposal).__name__
        )
        capability_rows.append({
            "kind": kind,
            "lifecycle": transition.lifecycle.value if transition else None,
            "reason": transition.reason_code if transition else None,
            "purpose": _clip(str(
                getattr(proposal, "discriminating_purpose", None)
                or getattr(proposal, "purpose", "")
            )),
        })
    fetched = [
        {"url": attempt.url, "bytes": attempt.byte_count}
        for receipt in capability_state.receipts.values()
        if isinstance(receipt, ResearchExecutionReceiptV1)
        for attempt in receipt.attempts
        if attempt.outcome == "FETCHED"
    ]
    citation_counts: dict[str, int] = {}
    for event in harness.log.read():
        signal = str(event.inputs[0]) if event.inputs else ""
        if signal.startswith("evidence-citation:"):
            code = signal.split(":", 1)[1]
            citation_counts[code] = citation_counts.get(code, 0) + 1
    summary["capabilities"] = {
        "proposals": capability_rows,
        "fetched": fetched,
        "consumed_packages": sum(
            1 for consumption in capability_state.consumptions.values()
            if isinstance(consumption, ResearchConsumptionV1)
        ),
        "citations": citation_counts,
    }
    return summary


def render_findings(summary: dict) -> str:
    """The findings summary as reader-facing markdown."""

    lines = ["# Findings summary", ""]
    if summary.get("question"):
        lines += ["## Question", "", summary["question"], ""]
    run = summary.get("run")
    if run:
        lines += [
            f"Run: **{run.get('state')}** (stop: {run.get('stop_reason')}, "
            f"cycle {run.get('cycle')}, tokens "
            f"{run.get('token_spend')}/{run.get('token_limit')})",
            "",
        ]

    positions = summary["positions"]
    rivalries = summary["rivalries"]
    contested = {
        rival for rivalry in rivalries for rival in rivalry["rivals"]
    }
    lines += [
        f"## Established and contested ({len(positions['accepted'])} accepted)",
        "",
    ]
    for rivalry in rivalries:
        lines.append(
            f"### Rivalry on `{rivalry['problem']}` "
            f"({rivalry['rival_count']} competitors, unresolved)"
        )
        rows = {row["id"]: row for row in positions["accepted"]}
        for rival_id in rivalry["rivals"]:
            lines.append(f"- {rows[rival_id]['claim']} `[{rival_id}]`")
        lines.append("")
    uncontested = [
        row for row in positions["accepted"] if row["id"] not in contested
    ]
    if uncontested:
        lines.append("### Standing without recorded rivals")
        for row in uncontested:
            lines.append(f"- {row['claim']} `[{row['id']}]`")
        lines.append("")

    if positions["refuted"]:
        lines += ["## Refutations", ""]
        for row in positions["refuted"]:
            attackers = ", ".join(row.get("attacked_by") or []) or "unattributed"
            lines.append(f"- {row['claim']} `[{row['id']}]` — refuted by {attackers}")
        lines.append("")
    if positions["suspended"]:
        lines += ["## Suspended (neither accepted nor refuted)", ""]
        for row in positions["suspended"]:
            lines.append(f"- ({row['status']}) {row['claim']} `[{row['id']}]`")
        lines.append("")

    criticism = summary["criticism"]
    lines += [
        "## Criticism ledger",
        "",
        f"- Attacks recorded: {criticism['attacks_recorded']} "
        f"({criticism['criticism_attempts']} typed criticism attempts)",
        f"- Attacks landing on refuted positions: {criticism['attacks_on_refuted']}",
        f"- Coverage-debt records outstanding: {criticism['coverage_debt_records']}",
        "",
    ]

    branch_counts: dict[str, int] = {}
    for row in summary["branches"]:
        branch_counts[row["trigger"]] = branch_counts.get(row["trigger"], 0) + 1
    lines += ["## Side branches", ""]
    lines.append(
        "- Spawned: " + ", ".join(
            f"{count} {trigger}" for trigger, count in sorted(branch_counts.items())
        )
    )
    starved = summary["starved_branches"]
    lines.append(
        f"- Starved (no position ever addressed them): {len(starved)}"
        + (f" — e.g. {', '.join(starved[:6])}" if starved else "")
    )
    lines.append("")

    capabilities = summary["capabilities"]
    lines += ["## Capability trail", ""]
    if capabilities["proposals"]:
        for row in capabilities["proposals"]:
            lines.append(
                f"- {row['kind']}: {row['lifecycle']} ({row['reason']}) — "
                f"{row['purpose']}"
            )
    else:
        lines.append("- No typed capability proposals were filed.")
    for fetch in capabilities["fetched"]:
        lines.append(f"- Fetched: {fetch['url']} ({fetch['bytes']} bytes)")
    citations = capabilities["citations"]
    verified = citations.get("EVIDENCE_CITATION_VERIFIED", 0)
    failed = sum(
        count for code, count in citations.items()
        if code != "EVIDENCE_CITATION_VERIFIED"
    )
    lines.append(
        f"- Citations: {verified} byte-verified, {failed} failed their "
        "deterministic check (failed groundings are NOT established)."
    )
    lines += [
        "",
        "---",
        "Derived entirely from the append-only run record. Accepted does "
        "not mean true — it means the position survived recorded criticism "
        "so far, and the run remains continuable.",
        "",
    ]
    return "\n".join(lines)


__all__ = ["write_findings_report", "findings_summary", "render_findings"]
