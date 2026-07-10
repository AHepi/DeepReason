"""Act (browser evidence): run an app candidate in its real medium, ONCE,
and materialize the outcome as evidence.

A browser run is exogenous — not replay-deterministic — so this rule follows
research/backends.run_research exactly: the single non-deterministic call
(``browser.run``) happens once per (candidate, commitment), its outcome is
registered as import-role artifacts (screenshots as image/png + a JSON trace,
both DEPENDING on an attackable source-reliability node), and replay reads
the log. Idempotence is the existing research guard: evidence is addressed to
the auto-spawned ``research:{cid}:{aid[:12]}`` problem, so ``pending()`` is
the run-once check AND detection.evidence_lambda counts the coverage — zero
new plumbing (the browser commitment is observation_valued).

Verdicts: FAIL -> ordinary demonstrative warrant (the cachebench precedent —
real-world measurement entering as a warrant, never a score); PASS -> a
browser-pass Measure. OVERRUN (malformed spec) is a spec defect, not the
candidate's fault: measure only. The browser backend is duck-typed
(PlaywrightBrowser live, FakeBrowser in tests — the suite never needs
Chromium).
"""

import json

from deepreason.browser import BROWSER_PROGRAM, FAIL, PASS, load_spec
from deepreason.canonical import canonical_json
from deepreason.ontology import (
    Artifact,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
)
from deepreason.ontology.artifact import RefRole
from deepreason.programs import content_text
from deepreason.research.backends import pending
from deepreason.rules.warrants import register_fail_warrant, verdict_on_record


def browser_rid(commitment_id: str, target_id: str) -> str:
    """The research problem id browser evidence is addressed to (must match
    rules/spawn.py's observation-valued spawn scheme)."""
    return f"research:{commitment_id}:{target_id[:12]}"


def browser_evidence(harness, target_id: str) -> list[dict]:
    """Recorded browser outcomes for a target: parsed trace payloads
    ({commitment, verdict, screenshots: [ids], trace, ...}) from non-refuted
    import evidence. Read by the vision critic and the export view."""
    out: list[dict] = []
    for cid in harness.state.artifacts[target_id].interface.commitments:
        rid = browser_rid(cid, target_id)
        for aid, pid in harness.state.addr:
            if pid != rid:
                continue
            artifact = harness.state.artifacts[aid]
            if artifact.codec != "json" or artifact.provenance.role.value != "import":
                continue
            try:
                payload = json.loads(content_text(artifact, harness.blobs))
            except ValueError:
                continue
            if payload.get("target") == target_id and "verdict" in payload:
                out.append({"evidence_id": aid, **payload})
    return out


def needs_browser_run(harness, target_id: str) -> bool:
    """True iff the target carries a browser commitment whose evidence is not
    yet on the record — the scheduler's per-cycle budget counts real runs."""
    target = harness.state.artifacts.get(target_id)
    if target is None:
        return False
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or kappa.eval != f"program:{BROWSER_PROGRAM}":
            continue
        rid = browser_rid(cid, target_id)
        if not pending(harness, rid) and not verdict_on_record(harness, cid, target_id):
            return True
    return False


def run_browser_evidence(harness, target_id: str, browser, config) -> Artifact | None:
    """One browser run per (candidate, browser commitment); returns the
    demonstrative critic on FAIL, None otherwise. Everything downstream of
    the single ``browser.run`` call is a pure function of the recorded
    bytes (§0)."""
    target = harness.state.artifacts.get(target_id)
    if target is None:
        return None
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or kappa.eval != f"program:{BROWSER_PROGRAM}":
            continue
        rid = browser_rid(cid, target_id)
        if pending(harness, rid) or verdict_on_record(harness, cid, target_id):
            continue  # ran before: evidence (or its warrant) is on the record
        # Evidence addressing requires the research problem to EXIST (addr
        # pairs only record against registered problems); normally spawn.py
        # creates it on the next scan, but act runs evidence-first — register
        # it here (idempotent; spawn's `rid in problems` guard then skips).
        harness.register_problem(
            Problem(
                id=rid,
                description=f"obtain evidence for observation-valued {cid} on {target_id[:12]}",
                criteria=[],
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "research", "from": [target_id, cid]}
                ),
            )
        )

        result = browser.run(content_text(target, harness.blobs), load_spec(kappa.budget))

        reliability = harness.create_artifact(
            f"source-reliability: {browser.name} render of {target_id[:12]} "
            f"under {cid} is a faithful execution of the candidate",
            provenance=Provenance(role="import"),
        )
        dep_reliability = Ref(target=reliability.id, role=RefRole.DEPENDENCE)
        shot_ids: list[str] = []
        for png in result.screenshots:
            shot = harness.create_artifact(
                png,
                codec="image/png",
                interface=Interface(refs=[dep_reliability]),
                provenance=Provenance(role="import"),
                problem_id=rid,
            )
            shot_ids.append(shot.id)
        payload = {
            "commitment": cid,
            "target": target_id,
            "verdict": result.verdict,
            "trace": result.trace,
            "screenshots": shot_ids,
            "browser": browser.name,
        }
        evidence = harness.create_artifact(
            json.dumps(payload, sort_keys=True),
            codec="json",
            interface=Interface(
                refs=[
                    dep_reliability,
                    *(Ref(target=s, role=RefRole.MENTION) for s in shot_ids),
                ]
            ),
            provenance=Provenance(role="import"),
            problem_id=rid,
        )
        if result.verdict == PASS:
            harness.record_measure(inputs=["browser-pass", cid, target_id])
            continue
        if result.verdict != FAIL:
            # overrun: the SPEC is unusable — not the candidate's fault (§1).
            harness.record_measure(inputs=["browser-spec-overrun", cid, target_id])
            continue
        return register_fail_warrant(
            harness,
            commitment_id=cid,
            target_id=target_id,
            nu_content=(
                f"nu: browser verdict of {cid} on {target_id} is sound — the "
                f"candidate was RENDERED and DRIVEN by the frozen interaction "
                f"script and failed step {result.trace.get('failed_step')}; "
                f"evidence {evidence.id[:12]} depends on the attackable "
                f"reliability of {browser.name}"
            ),
            critic_content=(
                f"critic: browser run failed {cid} on {target_id[:12]} at step "
                f"{result.trace.get('failed_step')} "
                f"({json.dumps(result.trace.get('steps', [])[-1:])[:200]})"
            ),
            nu_interface=Interface(refs=[Ref(target=evidence.id, role=RefRole.MENTION)]),
            trace_ref=harness.blobs.put(canonical_json(payload)),
        )
    return None
