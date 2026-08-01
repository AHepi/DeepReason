"""evidence(id) — the full dossier for one artifact: what it claims, who
attacked it with what recorded evidence, what rendered/ran, and which LLM
calls produced or judged it. Deterministic read-only join over log + state +
objects — the view that replaces every ad-hoc forensic script. Every ref it
prints is followable: `deepreason blob <ref>` dumps content, `deepreason
trace <id>` lists the touching events.
"""

import json

from deepreason.programs import content_text


def _status(harness, some_id: str) -> str:
    status = harness.state.status.get(some_id)
    return status.value if status is not None else "unregistered"


def _head(harness, artifact_id: str, limit: int = 72) -> str:
    artifact = harness.state.artifacts.get(artifact_id)
    if artifact is None:
        return ""
    if str(artifact.codec) == "image/png":
        return "(png bytes)"
    text = " ".join(content_text(artifact, harness.blobs).split())
    return text[:limit]


def _spec_summary(kappa) -> str:
    try:
        spec = json.loads(kappa.budget.extra.get("spec", "{}"))
    except (ValueError, AttributeError):
        spec = {}
    if not spec:
        return ""
    if "script" in spec:
        steps = spec["script"] if isinstance(spec["script"], list) else []
        asserts = sum(1 for s in steps if str(s.get("op", "")).startswith("assert"))
        return f"{len(steps)} interaction steps, {asserts} assertions"
    if "checker" in spec:
        first = next((ln for ln in str(spec["checker"]).splitlines()
                      if ln.strip() and not ln.strip().startswith('"')), "")
        n = len(spec.get("inputs", []))
        return f"checker `{first.strip()[:60]}`, {n} frozen input(s)"
    if "tests" in spec:
        return f"{len(spec['tests'])} frozen test(s), entry {spec.get('entry')!r}"
    return ""


def evidence(harness, artifact_id: str) -> str:
    state = harness.state
    if artifact_id not in state.artifacts:
        return f"{artifact_id}: not registered"
    artifact = state.artifacts[artifact_id]
    lines: list[str] = []

    role = artifact.provenance.role.value if artifact.provenance else "?"
    problems = [pid for aid, pid in state.addr if aid == artifact_id]
    lines.append(f"ARTIFACT {artifact_id}")
    lines.append(f"  status {_status(harness, artifact_id)} · codec {artifact.codec} "
                 f"· role {role}"
                 + (f" · problems {', '.join(problems)}" if problems else ""))
    head = _head(harness, artifact_id)
    if head:
        lines.append(f'  content "{head}"')

    if artifact.interface.commitments:
        lines.append("COMMITMENTS CARRIED (its declared attack surface)")
        for cid in artifact.interface.commitments:
            kappa = harness.commitments.get(cid)
            if kappa is None:
                lines.append(f"  {cid}: (unregistered)")
                continue
            extra = _spec_summary(kappa)
            obs = " · observation-valued" if kappa.observation_valued else ""
            lines.append(f"  {cid}: {kappa.eval}{obs}" + (f" · {extra}" if extra else ""))

    against = [w for w in harness.warrants.values() if w.target == artifact_id]
    if against:
        lines.append("WARRANTS AGAINST IT")
        for w in against:
            carrier = next(
                (
                    state.artifacts[aid]
                    for aid in harness.carrier_ids(w.id)
                    if aid in state.artifacts
                ),
                None,
            )
            lines.append(
                f"  {w.type.value} · commitment {w.commitment or '(none: argued case)'}"
                + (f" · verdict {w.verdict}" if w.verdict else "")
            )
            if carrier is not None:
                lines.append(f'    by critic {carrier.id[:12]} '
                             f'[{_status(harness, carrier.id)}] "{_head(harness, carrier.id, 60)}"')
            lines.append(
                f"    nu {w.validity_node[:12]} [{_status(harness, w.validity_node)}]"
                + (f" · trace {w.trace_ref[:12]}" if w.trace_ref else "")
            )
            kappa = harness.commitments.get(w.commitment) if w.commitment else None
            source = kappa.budget.extra.get("source_artifact") if kappa else None
            if source:
                lines.append(
                    f"    sourced from proposed property {source[:12]} "
                    f"[{_status(harness, source)}] — this verdict stands as long "
                    f"as its source does"
                )

    carried = [
        harness.warrants[wid]
        for wid in harness.carried_warrant_ids(artifact.id)
        if wid in harness.warrants
    ]
    if carried:
        lines.append("WARRANTS IT CARRIES (it is a critic)")
        for w in carried:
            lines.append(f"  {w.type.value} -> {w.target[:12]} "
                         f"[{_status(harness, w.target)}]")

    from deepreason.rules.act import browser_evidence

    payloads = browser_evidence(harness, artifact_id)
    if payloads:
        lines.append("BROWSER EVIDENCE (rendered and driven, recorded once)")
        for p in payloads:
            failed = p.get("trace", {}).get("failed_step")
            lines.append(
                f"  verdict {p['verdict']}"
                + (f" · failed step {failed}" if failed is not None else "")
                + f" · via {p.get('browser', '?')} · evidence {p['evidence_id'][:12]}"
            )
            for sid in p.get("screenshots", []):
                shot = state.artifacts.get(sid)
                ref = shot.content_ref if shot is not None else "?"
                lines.append(f"    screenshot {sid[:12]} · blob {ref[:16]}")

    vision_events = [
        e for e in harness.log.read()
        if e.inputs and str(e.inputs[0]).startswith("vision-crit")
        and len(e.inputs) > 1 and e.inputs[1] == artifact_id
    ]
    vision_warrants = [w for w in against if w.id.startswith("w:vision:")]
    if vision_events or vision_warrants:
        lines.append("VISION")
        for e in vision_events:
            verdict = ("no fault found" if e.inputs[0] == "vision-crit"
                       else "attack blocked by execution supremacy")
            lines.append(f"  looked at seq #{e.seq}: {verdict}")
        for w in vision_warrants:
            lines.append(f"  visual fault on record (nu {w.validity_node[:12]} "
                         f"[{_status(harness, w.validity_node)}])")

    calls = [e for e in harness.log.read()
             if e.llm is not None and artifact_id in e.outputs]
    if calls:
        lines.append("LLM CALLS THAT PRODUCED IT")
        for e in calls:
            lines.append(
                f"  seq #{e.seq} {e.llm.role} · {e.llm.model} · "
                f"{e.llm.tokens} tokens · {e.llm.attempts} attempt(s) · "
                f"prompt {e.llm.prompt_ref[:12]} · raw {e.llm.raw_ref[:12]}"
            )

    deps = [b for a, b in state.dep if a == artifact_id]
    if deps:
        lines.append("DEPENDS ON")
        for d in deps:
            lines.append(f'  {d[:12]} [{_status(harness, d)}] "{_head(harness, d, 60)}"')

    lines.append("")
    lines.append("follow refs: deepreason blob <ref> · deepreason trace <id> · "
                 "deepreason why <id>")
    return "\n".join(lines)
