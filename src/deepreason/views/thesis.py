"""thesis(pi) view (spec §8) — the run's record argued as ONE position.

The harness ends a run as survivors + refutations + open rivalries; this
view has an LLM compose the COMMITTED conclusion a reader actually wants:
pick the best-supported surviving position, argue it from the record,
rebut the refuted alternatives with the record's own arguments, state the
live rivals and what would discriminate them, and name what would
overturn the thesis. The pack is the LLM's entire world; every citation
is program-checked against the pack's artifact ids (one violation-repair
re-call, then annotate — never raise, never silently accept).

READ-ONLY by construction: the view never registers anything, and it
refuses an adapter that shares the run root's blob store (LLMAdapter.call
writes prompt/raw blobs via adapter.blobs). Spend is returned in the
result — prose.py precedent: view calls stay off the run's log.
"""

import json

from deepreason.informal.skeleton import parse_skeleton
from deepreason.llm.contracts import ThesisOutput
from deepreason.ontology.problem import SpawnTrigger
from deepreason.ontology.state import Status
from deepreason.programs import content_text

_ITEM_ACCEPTED_CAP = 900
_ITEM_CLAIM_CAP = 240
_ITEM_CASE_CAP = 420
_ITEM_QUOTE_CAP = 200

_FOOTER = (
    "\nDIRECTIVE: from this record ONLY, produce the committed thesis "
    "(rules in your role brief). Cite bracketed ids exactly."
)


def problem_family(state, problem_id: str) -> list[str]:
    """The problem plus every problem spawned (transitively) from it or
    from artifacts addressing it — BFS fixpoint over provenance.from_."""
    if problem_id not in state.problems:
        return []
    addressed_by = {}
    for aid, pid in state.addr:
        addressed_by.setdefault(aid, set()).add(pid)
    family = {problem_id}
    changed = True
    while changed:
        changed = False
        for pid, problem in state.problems.items():
            if pid in family:
                continue
            for fid in problem.provenance.from_:
                parents = {fid} if fid in family else addressed_by.get(fid, set())
                if fid in family or parents & family:
                    family.add(pid)
                    changed = True
                    break
    return [pid for pid in state.problems if pid in family]  # registration order


def _claim_line(text: str) -> str:
    skeleton = parse_skeleton(text)
    if skeleton is not None:
        return skeleton.claim
    return text


def _decisive_from_warrants(harness, attacker) -> str:
    """The trial decisive_point (or program-check error) behind an attack,
    duck-typed over the trace shapes the harness actually writes."""
    for wid in attacker.warrants:
        warrant = harness.warrants.get(wid)
        if warrant is None or not warrant.trace_ref:
            continue
        try:
            trace = json.loads(harness.blobs.get(warrant.trace_ref))
        except (KeyError, ValueError):
            continue
        if not isinstance(trace, dict):
            continue
        ruling = trace.get("ruling") or {}
        if ruling.get("decisive_point"):
            return str(ruling["decisive_point"])
        if trace.get("error"):
            return str(trace["error"])
    return ""


def _pack(harness, problem_id: str, budget_chars: int) -> tuple[str, set[str]]:
    state = harness.state
    problem = state.problems[problem_id]
    family = set(problem_family(state, problem_id))
    rank = {aid: i for i, aid in enumerate(state.artifacts)}  # registration order
    addressed = [aid for aid, pid in state.addr if pid in family]
    attackers_of = {}
    for x, t in state.att:
        attackers_of.setdefault(t, []).append(x)

    accepted, refuted = [], []
    for aid in dict.fromkeys(addressed):
        artifact = state.artifacts[aid]
        if artifact.provenance.role.value not in ("conjecturer", "synthesizer"):
            continue
        status = state.status.get(aid)
        if status == Status.ACCEPTED:
            accepted.append(aid)
        elif status == Status.REFUTED:
            refuted.append(aid)
    accepted.sort(key=lambda a: (-(state.hv.get(a, -1.0)), rank[a]))
    refuted.sort(key=lambda a: -rank[a])  # most recent first

    pack_ids: set[str] = set()
    lines = [
        f"PROBLEM {problem_id}: {problem.description}",
        f"(family: {len(family)} problems including spawned successors)",
        "",
    ]
    used = sum(len(line) + 1 for line in lines) + len(_FOOTER)

    def emit(section: str, items: list[tuple[str, set[str]]]) -> None:
        nonlocal used
        header = f"== {section} =="
        lines.append(header)
        used += len(header) + 1
        shown = 0
        for text, ids in items:
            if used + len(text) + 1 > budget_chars:
                marker = f"(+{len(items) - shown} more omitted for budget)"
                lines.append(marker)
                used += len(marker) + 1
                break
            lines.append(text)
            used += len(text) + 1
            pack_ids.update(ids)  # only INCLUDED items become citable
            shown += 1
        lines.append("")
        used += 1

    # Each item carries the ids it makes citable, so an OMITTED item never
    # becomes citable (a thesis cannot cite evidence trimmed out of its pack).
    def _item(text: str, ids: set[str]) -> tuple[str, set[str]]:
        return text, ids

    accepted_items = []
    for aid in accepted:
        artifact = state.artifacts[aid]
        text = content_text(artifact, harness.blobs)
        skeleton = parse_skeleton(text)
        hv = state.hv.get(aid)
        head = f"[{aid[:12]}] (school: {artifact.provenance.school or '-'}" + (
            f", hv {hv:.2f})" if hv is not None else ")")
        if skeleton is not None:
            body = f"CLAIM: {skeleton.claim}\nMECHANISM: {skeleton.mechanism}"
            for case in skeleton.forbidden[:2]:
                body += f"\nFORBIDS: {case.case}"
        else:
            body = text
        accepted_items.append(_item(f"{head}\n{body}"[:_ITEM_ACCEPTED_CAP], {aid[:12]}))

    pairwise_items = []
    for aid, artifact in state.artifacts.items():
        text = content_text(artifact, harness.blobs)
        if not text.startswith('{"pairwise"'):
            continue
        try:
            body = json.loads(text)["pairwise"]
        except (ValueError, KeyError, TypeError):
            continue
        if body.get("problem") not in family:
            continue
        pairwise_items.append(_item(
            f"[{body['winner'][:12]}] beat [{body['loser'][:12]}]: "
            f"{str(body.get('decisive_point', ''))[:_ITEM_QUOTE_CAP]}",
            {body["winner"][:12], body["loser"][:12]}))

    rivalry_items = []
    accepted_set = set(accepted)
    for pid in problem_family(state, problem_id):
        rivals = [a for a, p in state.addr if p == pid and a in accepted_set]
        if len(rivals) >= 2:
            rivalry_items.append(_item(
                f"{pid}: " + ", ".join(f"[{a[:12]}]" for a in rivals), set()))

    refuted_items = []
    for aid in refuted:
        artifact = state.artifacts[aid]
        claim = _claim_line(content_text(artifact, harness.blobs))[:_ITEM_CLAIM_CAP]
        entry = f"[{aid[:12]}] REFUTED: {claim}"
        ids = {aid[:12]}
        for attacker_id in sorted(attackers_of.get(aid, []), key=lambda a: rank[a]):
            attacker = state.artifacts[attacker_id]
            case = content_text(attacker, harness.blobs)[:_ITEM_CASE_CAP]
            entry += f"\n  FELLED BY [{attacker_id[:12]}]: {case}"
            decisive = _decisive_from_warrants(harness, attacker)
            if decisive:
                entry += f"\n  DECISIVE: {decisive[:_ITEM_QUOTE_CAP]}"
            ids.add(attacker_id[:12])
            break  # one argued case per refutation keeps the pack broad
        refuted_items.append(_item(entry, ids))

    # Order matters under trimming: survivors are the pool the thesis picks
    # from; pairwise + rivalries are cheap and feed the rivals section; the
    # big refuted section takes the remainder (recency-first) so those small,
    # load-bearing sections are never starved by it.
    for section, items in (
        ("SURVIVING POSITIONS (accepted after criticism)", accepted_items),
        ("PAIRWISE RULINGS", pairwise_items),
        ("UNRESOLVED RIVALRIES (multiple survivors, undecided)", rivalry_items),
        ("REFUTED POSITIONS (with the arguments that felled them)", refuted_items),
    ):
        emit(section, items)

    lines.append(_FOOTER)
    return "\n".join(lines), pack_ids


def evidence_pack(harness, problem_id: str | None = None,
                  budget_chars: int = 24_000) -> str:
    text, _ = _pack(harness, _resolve_problem(harness, problem_id), budget_chars)
    return text


def _resolve_problem(harness, problem_id: str | None) -> str:
    if problem_id is not None:
        if problem_id not in harness.state.problems:
            raise KeyError(f"problem not registered: {problem_id}")
        return problem_id
    for pid, problem in harness.state.problems.items():
        if problem.provenance.trigger == SpawnTrigger.SEED:
            return pid
    raise KeyError("no seed problem in this root; pass problem_id")


def check_citations(output: ThesisOutput, pack_ids: set[str]) -> list[str]:
    """Unresolved citations: not an exact pack id and not a unique >=8-char
    prefix of exactly one pack id."""
    cited: list[str] = []
    for section in list(output.argument) + list(output.rebuttals):
        cited += section.citations
    cited += [r.artifact for r in output.rivals if r.artifact]
    unresolved = []
    for raw in cited:
        cid = raw.strip().strip("[]")
        if cid in pack_ids:
            continue
        if len(cid) >= 8 and sum(1 for p in pack_ids if p.startswith(cid)) == 1:
            continue
        unresolved.append(raw)
    return sorted(set(unresolved))


def thesis(harness, adapter, problem_id: str | None = None,
           budget_chars: int = 24_000, role: str = "thesis") -> dict:
    """Compose the committed thesis for a problem's record. Read-only over
    the root; the adapter must NOT share the run's blob store."""
    if adapter.blobs is harness.blobs:
        raise ValueError(
            "thesis() is read-only: give the adapter a scratch BlobStore, "
            "not the run root's (adapter.call writes prompt/raw blobs)")
    pid = _resolve_problem(harness, problem_id)
    pack, pack_ids = _pack(harness, pid, budget_chars)
    call_role = role if adapter.has_role(role) else "summarizer"
    calls = []

    output, llm_call = adapter.call(call_role, pack, ThesisOutput,
                                    template_role="thesis")
    calls.append(llm_call)
    unresolved = check_citations(output, pack_ids)
    retried = False
    if unresolved:
        retried = True
        repair_pack = pack + (
            "\n\nCITATION VIOLATION: your previous output cited ids not in "
            f"the pack: {unresolved}. Every citation must copy a bracketed "
            "id from the pack exactly. Rewrite the SAME thesis with valid "
            "citations only.")
        retry_out, retry_call = adapter.call(call_role, repair_pack,
                                             ThesisOutput, template_role="thesis")
        calls.append(retry_call)
        retry_unresolved = check_citations(retry_out, pack_ids)
        if len(retry_unresolved) < len(unresolved):
            output, unresolved = retry_out, retry_unresolved

    bad = {c.strip().strip("[]") for c in check_citations(output, pack_ids)}
    citations = sorted({
        c.strip().strip("[]")
        for section in list(output.argument) + list(output.rebuttals)
        for c in section.citations
    } - bad)
    return {
        "problem": pid,
        "thesis": output.thesis,
        "output": output,
        "citations": citations,
        "citation_check": {"ok": not unresolved, "unresolved": unresolved,
                           "retried": retried},
        "pack_chars": len(pack),
        "spend": {
            "tokens": sum(c.tokens for c in calls),
            "calls": len(calls),
            "meter": adapter.meter.snapshot() if adapter.meter else None,
        },
    }


def render_thesis(result: dict) -> str:
    """Markdown view of a thesis result, spend header first (read-only
    runs report their cost here, never on the run's log)."""
    output: ThesisOutput = result["output"]
    check = result["citation_check"]
    lines = [
        f"# Thesis: {result['problem']}",
        "",
        f"*spend: {result['spend']['tokens']} tokens in "
        f"{result['spend']['calls']} call(s); pack {result['pack_chars']} chars; "
        f"citations {'OK' if check['ok'] else 'UNRESOLVED: ' + ', '.join(check['unresolved'])}"
        + (" (after retry)" if check["retried"] else "") + "*",
        "",
        "## Thesis",
        "",
        output.thesis,
    ]
    for title, sections in (("Argument", output.argument),
                            ("Rebuttals", output.rebuttals)):
        if not sections:
            continue
        lines += ["", f"## {title}"]
        for section in sections:
            lines += ["", f"### {section.heading}", "", section.body]
            if section.citations:
                lines.append("- cites: " + ", ".join(section.citations))
    if output.rivals:
        lines += ["", "## Live rivals"]
        for rival in output.rivals:
            tag = f"[{rival.artifact}] " if rival.artifact else ""
            lines += ["", f"- {tag}{rival.position}",
                      f"  - would discriminate: {rival.discriminator}"]
    lines += ["", "## What would overturn this"]
    lines += [f"- {item}" for item in output.overturn]
    return "\n".join(lines)
