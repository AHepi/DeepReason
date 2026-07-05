"""Trial protocol (spec §3 rubric-verdict guard; §10.2 comparative modes).

The rubric judge is never asked "is this good?" — only the narrow question
the pack poses. Flow: critic drafts the case for fail citing specific
clauses; defender answers; judge rules with a decisive_point. Program
checks then screen the ruling: referential integrity (decisive_point must
resolve to an element of the exchange), order-swap consistency (anchored/
pairwise), paraphrase spot-check, ensemble agreement across families.
Only surviving rulings package warrants; trace_ref = full transcript + all
check results (a warrant-validity condition, §2 — it suppresses noise,
never criticism). Blocked rulings are logged as Measure events; a streak
of blocks is a critic-gaming signal.
"""

import json

from deepreason.informal.standards import precedent_slice, resolve_standard, standard_body
from deepreason.llm.contracts import (
    ArgumentativeCriticOutput,
    DefenderOutput,
    JudgeRuling,
    PairwiseRuling,
    VariatorOutput,
)
from deepreason.canonical import canonical_json
from deepreason.ontology import Interface, Provenance, Ref, Rule, Warrant, WarrantType
from deepreason.programs import content_text


def conforming_transcript(blobs, trace_ref: str) -> bool:
    """Well-formedness (§2): a rubric-derived warrant's trace_ref must hold
    a conforming trial transcript — re-checkable by program."""
    try:
        data = json.loads(blobs.get(trace_ref))
    except (KeyError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    ruling = data.get("ruling") or {}
    decisive = ruling.get("decisive_point", "")
    exchange = f"{data.get('case', '')}\n{data.get('answer', '')}"
    return bool(
        data.get("case")
        and data.get("answer")
        and decisive
        and decisive in exchange
        and isinstance(data.get("checks"), dict)
    )


def transcript_blob(harness, *, case: str, answer: str, decisive_point: str,
                    checks: dict | None = None, **meta) -> str:
    """Store a transcript; returns the trace_ref blob hash."""
    data = {"case": case, "answer": answer,
            "ruling": {"verdict": "fail", "decisive_point": decisive_point},
            "checks": checks or {}, **meta}
    return harness.blobs.put(canonical_json(data))


def _block(harness, reason: str, target_id: str, diagnostics) -> None:
    harness.record_measure(inputs=[f"trial-blocked:{reason}", target_id])
    if diagnostics is not None:
        diagnostics.append({"trial": target_id[:12], "blocked": reason})
    return None


def _judge_pack(harness, config, body, target_text, case, answer,
                standard_id, anchor_text=None, swapped=False) -> str:
    lines = [f"STANDARD {body['spec']} (mode: {body['mode']}):", body["rubric"], ""]
    precedents = precedent_slice(harness, standard_id, config.PRECEDENT_K)
    if precedents:
        lines.append("PRECEDENTS (user rulings first):")
        lines += [f"- {p['holding']}" for p in precedents]
        lines.append("")
    if body["mode"] == "anchored" and anchor_text is not None:
        first = ("KNOWN-BAD ANCHOR", anchor_text) if swapped else ("CANDIDATE", target_text)
        second = ("CANDIDATE", target_text) if swapped else ("KNOWN-BAD ANCHOR", anchor_text)
        lines += [f"{first[0]}:\n{first[1]}", "", f"{second[0]}:\n{second[1]}", "",
                  "QUESTION: does the CANDIDATE beat the anchor on the standard's "
                  "criteria? verdict=pass iff it does."]
    else:
        lines += [f"TARGET:\n{target_text}", "",
                  "QUESTION: does the case establish that the target violates the "
                  "cited clause? verdict=fail iff it does."]
    lines += ["", "THE CASE FOR FAIL:", case, "", "THE DEFENCE:", answer, "",
              "Rule on the exchange; decisive_point MUST quote a span of it."]
    return "\n".join(lines)


def _judge_all(harness, adapter, pack: str, diagnostics, target_id):
    """Rule with the full ensemble; disagreement blocks (never averaged)."""
    ruling, llm_call = adapter.call("judge", pack, JudgeRuling)
    for index in range(1, adapter.ensemble_size("judge")):
        other, _ = adapter.call("judge", pack, JudgeRuling, endpoint_index=index)
        if other.verdict != ruling.verdict:
            return None, llm_call  # ensemble split: critic-gaming signal
    return ruling, llm_call


def run_trial(harness, target_id: str, commitment, adapter, config,
              diagnostics: list | None = None, embedder=None):
    """Full §3 guard. Returns the registered critic artifact, or None (the
    ruling was pass / blocked — nothing registers, correctly)."""
    # The trial needs critic + defender + judge (variator is optional, §3);
    # a config missing any is a logged no-op, not a mid-run KeyError crash.
    for role in ("argumentative_critic", "defender", "judge"):
        if not adapter.has_role(role):
            return _block(harness, f"no-{role}-role", target_id, diagnostics)
    spec_id = commitment.eval.split(":", 1)[1]
    standard = resolve_standard(harness, spec_id)
    if standard is None:
        return _block(harness, "unresolved-standard", target_id, diagnostics)
    body = standard_body(harness, standard)
    target_text = content_text(harness.state.artifacts[target_id], harness.blobs)
    case_hint = commitment.budget.extra.get("case", "")

    # 1. The critic drafts the case for fail, citing specific clauses.
    critic_pack = "\n".join([
        f"STANDARD {body['spec']}:", body["rubric"], "",
        f"FORBIDDEN CASE UNDER TRIAL: {case_hint}" if case_hint else "",
        f"TARGET:\n{target_text}", "",
        "Draft the strongest case that the target violates the standard, citing "
        "specific clauses/cases — or attack=false if none exists.",
    ])
    case_out, _ = adapter.call("argumentative_critic", critic_pack, ArgumentativeCriticOutput)
    if not case_out.attack or not case_out.case.strip():
        return None  # no case, no trial

    # 2. The defender answers.
    defence_pack = f"THE CASE AGAINST THE TARGET:\n{case_out.case}\n\nTARGET:\n{target_text}"
    defence, _ = adapter.call("defender", defence_pack, DefenderOutput)

    # 3. The judge rules on the exchange (precedent slice in the pack).
    anchor_text = None
    if body["mode"] == "anchored":
        anchors = body.get("anchors", [])
        if anchors and anchors[0] in harness.state.artifacts:
            anchor_text = content_text(harness.state.artifacts[anchors[0]], harness.blobs)
    pack = _judge_pack(harness, config, body, target_text, case_out.case,
                       defence.answer, standard.id, anchor_text)
    ruling, judge_llm = _judge_all(harness, adapter, pack, diagnostics, target_id)
    if ruling is None:
        return _block(harness, "ensemble-split", target_id, diagnostics)
    if ruling.verdict != "fail":
        return None  # the work survives; nothing registers

    exchange = f"{case_out.case}\n{defence.answer}"
    checks: dict = {"ensemble": adapter.ensemble_size("judge")}

    # 4. Referential integrity (program check).
    if ruling.decisive_point not in exchange:
        return _block(harness, "referential-integrity", target_id, diagnostics)
    checks["referential_integrity"] = True

    # 5. Order-swap consistency (anchored/pairwise modes).
    if body["mode"] in ("anchored", "pairwise") and anchor_text is not None:
        swapped_pack = _judge_pack(harness, config, body, target_text, case_out.case,
                                   defence.answer, standard.id, anchor_text, swapped=True)
        swapped, _ = _judge_all(harness, adapter, swapped_pack, diagnostics, target_id)
        if swapped is None or swapped.verdict != ruling.verdict:
            return _block(harness, "order-swap", target_id, diagnostics)
        checks["order_swap"] = "pass"
    else:
        checks["order_swap"] = "skipped"

    # 6. Paraphrase spot-check: any flip => no warrant.
    if adapter.has_role("variator"):
        n = config.TRIAL_PARAPHRASE_N
        para_out, _ = adapter.call(
            "variator",
            f"TARGET CONTENT:\n{exchange}\n\nDIRECTIVE: produce exactly {n} "
            "meaning-preserving paraphrases of this exchange.",
            VariatorOutput,
        )
        flips = 0
        for paraphrase in [e.content for e in para_out.edits[:n]]:
            repack = pack.replace(exchange, paraphrase) if exchange in pack else (
                pack + "\n\nPARAPHRASED EXCHANGE:\n" + paraphrase)
            reruling, _ = adapter.call("judge", repack, JudgeRuling)
            if reruling.verdict != "fail":
                flips += 1
        if flips:
            return _block(harness, "paraphrase-flip", target_id, diagnostics)
        checks["paraphrase"] = {"n": n, "flips": 0}
    else:
        checks["paraphrase"] = "skipped"

    # Package: transcript blob, nu MENTIONING the standard (case-law closure
    # extension, §1), ordinary demonstrative warrant, critic artifact.
    trace_ref = transcript_blob(
        harness, case=case_out.case, answer=defence.answer,
        decisive_point=ruling.decisive_point, checks=checks,
        target=target_id, commitment=commitment.id, standard=standard.id,
        mode=body["mode"],
    )
    nu = harness.create_artifact(
        f"nu: the trial ruling under {body['spec']} on {target_id} is sound",
        interface=Interface(refs=[Ref(target=standard.id, role="mention")]),
        provenance=Provenance(role="critic"),
    )
    warrant = Warrant(
        id=f"w:{commitment.id}:{target_id}",
        target=target_id,
        type=WarrantType.DEMONSTRATIVE,
        commitment=commitment.id,
        verdict="fail",
        trace_ref=trace_ref,
        validity_node=nu.id,
    )
    return harness.create_artifact(
        f"critic: trial fail under {body['spec']} on {target_id[:12]} — "
        f"{ruling.decisive_point[:100]}",
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=judge_llm,
    )


def pairwise_discriminate(harness, problem, a_id: str, b_id: str, adapter, config,
                          diagnostics: list | None = None):
    """§10.2: (A, B, pi, criteria) -> winner + decisive_point, mandatory
    order-swap. Registers an argumentative warrant against the loser,
    indexed to pi — never a global ranking. 'neither' registers nothing:
    the rivalry stands, correctly unresolved."""
    a_text = content_text(harness.state.artifacts[a_id], harness.blobs)
    b_text = content_text(harness.state.artifacts[b_id], harness.blobs)
    criteria = "\n".join(f"- {c}" for c in problem.criteria)

    def pack(first, second, first_label, second_label):
        return "\n".join([
            f"PROBLEM {problem.id}: {problem.description}", "CRITERIA:", criteria, "",
            f"{first_label}:\n{first}", "", f"{second_label}:\n{second}", "",
            "QUESTION: which candidate better addresses the problem, for this "
            "problem only? winner=neither if you cannot discriminate. "
            "decisive_point MUST quote a span of a candidate.",
        ])

    ruling1, llm_call = adapter.call("judge", pack(a_text, b_text, "A", "B"), PairwiseRuling)
    if ruling1.winner == "neither":
        return None
    ruling2, _ = adapter.call("judge", pack(b_text, a_text, "A", "B"), PairwiseRuling)
    # Under the swap, candidate a is labelled B: the same real winner is
    # required (order-swap consistency, §3).
    consistent = (
        (ruling1.winner == "A" and ruling2.winner == "B")
        or (ruling1.winner == "B" and ruling2.winner == "A")
    )
    if not consistent:
        return _block(harness, "order-swap", f"{a_id[:12]}v{b_id[:12]}", diagnostics)
    # Referential integrity (§3): a named winner MUST quote a span of a
    # candidate. An empty decisive_point is unscreened LLM adjudication —
    # block it rather than skipping the check (the empty string is a substring
    # of everything, so it would otherwise pass vacuously). PairwiseRuling
    # allows "" only for 'neither', handled above.
    if not ruling1.decisive_point or ruling1.decisive_point not in f"{a_text}\n{b_text}":
        return _block(harness, "referential-integrity", f"{a_id[:12]}v{b_id[:12]}", diagnostics)

    loser = b_id if ruling1.winner == "A" else a_id
    winner = a_id if ruling1.winner == "A" else b_id
    trace_ref = harness.blobs.put(canonical_json({
        "pairwise": {"problem": problem.id, "winner": winner, "loser": loser,
                     "decisive_point": ruling1.decisive_point},
        "order_swap": "pass",
    }))
    nu = harness.create_artifact(
        f"nu: the pairwise ruling {winner[:12]} > {loser[:12]} for {problem.id} is sound",
        provenance=Provenance(role="critic"),
    )
    warrant = Warrant(
        id=f"w:pairwise:{problem.id}:{loser}",
        target=loser,
        type=WarrantType.ARGUMENTATIVE,
        trace_ref=trace_ref,
        validity_node=nu.id,
    )
    return harness.create_artifact(
        json.dumps({"pairwise": {"problem": problem.id, "winner": winner,
                                 "loser": loser,
                                 "decisive_point": ruling1.decisive_point}},
                   sort_keys=True),
        codec="json",
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm_call,
        problem_id=problem.id,
    )
