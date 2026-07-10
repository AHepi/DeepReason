"""Vision criticism (§3 extension): an LLM that LOOKS at the rendered app.

The browser oracle (rules/act.py) records what the candidate DOES (DOM
assertions under a virtual clock); the vision critic judges what it LOOKS
like — the dimension no DOM assertion covers, which is exactly why
program:browser_oracle grants no execution supremacy. The critic receives the
recorded screenshot bytes (content-addressed evidence artifacts) through the
multimodal adapter and registers an ordinary ARGUMENTATIVE warrant whose ν
MENTIONs the screenshots it judged: attack the ν (or refute the screenshots'
reliability upstream) and the target reinstates — a visual judgment is a
case, never a verdict from reality (D2/N1).

Supremacy is consulted uniformly: a target backed by a PASSING in-process
oracle (exec/property) still cannot be refuted by visual argument — that
boundary is deliberate and documented; app candidates carry browser
commitments, not in-process oracles, so vision criticism has full force on
them.
"""

from deepreason.canonical import sha256_hex
from deepreason.llm.contracts import VisionCriticOutput
from deepreason.ontology import Artifact, Interface, Provenance, Ref, Rule, Status, Warrant, WarrantType
from deepreason.ontology.artifact import RefRole
from deepreason.rules.act import browser_evidence
from deepreason.rules.warrants import execution_backed

_MAX_SCREENSHOTS = 4


def _screenshots(harness, target_id: str) -> tuple[list[str], list[bytes], list[dict]]:
    """Non-refuted screenshot evidence for the target, oldest-first, capped."""
    ids: list[str] = []
    payloads = browser_evidence(harness, target_id)
    for payload in payloads:
        for sid in payload.get("screenshots", []):
            if sid in ids or len(ids) >= _MAX_SCREENSHOTS:
                continue
            if harness.state.status.get(sid) == Status.REFUTED:
                continue
            ids.append(sid)
    images: list[bytes] = []
    for sid in ids:
        artifact = harness.state.artifacts[sid]
        try:
            images.append(harness.blobs.get(artifact.content_ref))  # raw: PNGs
        except KeyError:
            ids = [i for i in ids if i != sid]
    return ids, images, payloads


def crit_vision(harness, target_id: str, adapter, config) -> Artifact | None:
    """One vision-critic call over the target's recorded screenshots;
    registers an argumentative critic iff it attacks. Returns None (with the
    call logged as a Measure) when there are no screenshots, no fault is
    found, or execution supremacy blocks the argument."""
    problem_ids = [pid for aid, pid in harness.state.addr if aid == target_id]
    problem = next(
        (harness.state.problems[p] for p in problem_ids if p in harness.state.problems),
        None,
    )
    shot_ids, images, payloads = _screenshots(harness, target_id)
    if not images:
        return None  # nothing rendered on the record: nothing to look at
    lines = [
        "THE APP UNDER JUDGMENT (you are seeing its RENDERED screenshots):",
        problem.description if problem else "(no problem description on record)",
        "",
        f"SCREENSHOTS ({len(shot_ids)}) — attached in order; evidence artifact ids:",
    ]
    steps_by_shot: dict[str, str] = {}
    for payload in payloads:
        for step in payload.get("trace", {}).get("steps", []):
            if "screenshot_index" in step:
                idx = step["screenshot_index"]
                shots = payload.get("screenshots", [])
                if idx < len(shots):
                    steps_by_shot[shots[idx]] = f"captured after script step {step['i']}"
    for i, sid in enumerate(shot_ids):
        lines.append(f"- image {i}: {sid[:12]} ({steps_by_shot.get(sid, 'state capture')})")
    lines += [
        "",
        "DIRECTIVE: judge only what is visible; attack=true needs a concrete "
        "visual fault a user would hit, tied to the app's stated purpose.",
    ]
    output, llm_call = adapter.call(
        "vision_critic", "\n".join(lines), VisionCriticOutput, images=images
    )
    if not output.attack or not output.case.strip():
        harness.record_measure(inputs=["vision-crit", target_id], llm=llm_call)
        return None
    if execution_backed(harness, target_id):
        # Uniform supremacy: a passing in-process oracle beats visual argument.
        harness.record_measure(
            inputs=["vision-crit-overridden-by-execution", target_id], llm=llm_call
        )
        return None
    case_hash = sha256_hex(output.case.encode())[:16]
    nu = harness.create_artifact(
        f"nu: vision case {case_hash} against {target_id} is sound (judged from "
        f"recorded screenshots {', '.join(s[:12] for s in shot_ids)})",
        interface=Interface(refs=[Ref(target=s, role=RefRole.MENTION) for s in shot_ids]),
        provenance=Provenance(role="critic"),
    )
    warrant = Warrant(
        id=f"w:vision:{case_hash}:{target_id}",
        target=target_id,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu.id,
    )
    before = set(harness.state.artifacts)
    critic = harness.create_artifact(
        output.case,
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm_call,
    )
    if critic.id in before:
        harness.record_measure(inputs=["vision-crit", target_id], llm=llm_call)
    return critic
