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

from deepreason.bridge.evidence_pack import legacy_pack as _pack
from deepreason.bridge.evidence_pack import problem_family as problem_family
from deepreason.llm.contracts import ThesisOutput
from deepreason.ontology.problem import SpawnTrigger


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
