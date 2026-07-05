"""Judge audits (spec §10.4) — program-checked attacks on rubric
infrastructure. Informal TRUTH cannot be program-checked; judge BEHAVIOR
can. Audit outputs enter as ordinary demonstrative warrants (eval:program,
reliable) against the relevant nu nodes: "this judge flips under
paraphrase" is a direct warranted attack on the judge-reliability assertion
the nu carries — formal machinery criticizing informal machinery, with the
full force of the graph. The planted-flaw battery measures the judge only
on flaws we know how to construct; unknown flaw classes are unmeasured by
construction (§17).
"""

import json

from deepreason.canonical import canonical_json
from deepreason.informal.appellate import spawn_audit_problem
from deepreason.llm.contracts import JudgeRuling, PairwiseRuling, VariatorOutput
from deepreason.ontology import Commitment, Provenance, Rule, Warrant, WarrantType

PARAPHRASE_AUDIT = Commitment(id="audit:paraphrase-invariance", eval="program:paraphrase_audit")
PREMISE_AUDIT = Commitment(id="audit:premise-deletion", eval="program:premise_deletion_audit")


def _rubric_warrants(harness):
    for warrant in harness.warrants.values():
        kappa = harness.commitments.get(warrant.commitment) if warrant.commitment else None
        if kappa is None or not kappa.eval.startswith("rubric:"):
            continue
        try:
            transcript = json.loads(harness.blobs.get(warrant.trace_ref))
        except (KeyError, ValueError, TypeError):
            continue
        yield warrant, transcript


def _audit_warrant(harness, audit_commitment, nu_target: str, finding: dict, llm=None):
    """Register an audit critic carrying a program warrant against a nu.

    ``llm`` is the decisive judge re-ruling that produced the finding — it is
    logged on the critic event so replay, eval_report, and the controller's
    process signals see each audit LLM call (§0), not just the live meter."""
    harness.register_commitment(audit_commitment)
    if any(
        w.commitment == audit_commitment.id and w.target == nu_target
        for w in harness.warrants.values()
    ):
        return None
    trace_ref = harness.blobs.put(canonical_json(finding))
    audit_nu = harness.create_artifact(
        f"nu: the {audit_commitment.id} finding against {nu_target} is sound",
        provenance=Provenance(role="critic"),
    )
    warrant = Warrant(
        id=f"w:{audit_commitment.id}:{nu_target}",
        target=nu_target,
        type=WarrantType.DEMONSTRATIVE,
        commitment=audit_commitment.id,
        verdict="fail",
        trace_ref=trace_ref,
        validity_node=audit_nu.id,
    )
    critic = harness.create_artifact(
        f"audit-critic: {audit_commitment.id} hit on {nu_target[:12]}",
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm,
    )
    harness.record_measure(inputs=[f"audit-hit:{nu_target}", audit_commitment.id])
    return critic


def _judge_exchange(adapter, transcript: dict, exchange: str):
    pack = "\n".join([
        "Re-rule on this exchange (audit replay).",
        "THE CASE FOR FAIL:", exchange, "",
        "verdict=fail iff the case establishes the violation.",
    ])
    ruling, llm_call = adapter.call("judge", pack, JudgeRuling)
    return ruling.verdict, llm_call


def _log_calls(harness, calls) -> None:
    """Persist LLM calls that did not land on a critic event (variator
    paraphrases, non-decisive re-rulings) as Measure events, so no audit
    call is missing from the event log's per-event llm records."""
    for call in calls:
        if call is not None:
            harness.record_measure(inputs=["audit-llm"], llm=call)


def paraphrase_invariance_audit(harness, adapter, config) -> list:
    """Re-run logged rulings on variator paraphrases; flips are hits."""
    hits = []
    for warrant, transcript in list(_rubric_warrants(harness)):
        exchange = f"{transcript['case']}\n{transcript['answer']}"
        para, para_call = adapter.call(
            "variator",
            f"TARGET CONTENT:\n{exchange}\n\nDIRECTIVE: produce exactly "
            f"{config.TRIAL_PARAPHRASE_N} meaning-preserving paraphrases.",
            VariatorOutput,
        )
        calls = [para_call]
        flips = []
        decisive = None
        for p in para.edits[: config.TRIAL_PARAPHRASE_N]:
            verdict, call = _judge_exchange(adapter, transcript, p.content)
            calls.append(call)
            if verdict != "fail":
                flips.append(p.content[:80])
                decisive = call
        if flips:
            critic = _audit_warrant(
                harness, PARAPHRASE_AUDIT, warrant.validity_node,
                {"warrant": warrant.id, "flips": flips}, llm=decisive,
            )
            if decisive is not None:
                calls.remove(decisive)
            if critic is not None:
                hits.append(critic)
        _log_calls(harness, calls)
    return hits


def premise_deletion_audit(harness, adapter, config) -> list:
    """Delete the cited decisive_point; the verdict SHOULD flip. A verdict
    that survives the removal of its own stated grounds is easy to vary."""
    hits = []
    for warrant, transcript in list(_rubric_warrants(harness)):
        decisive = transcript["ruling"]["decisive_point"]
        exchange = f"{transcript['case']}\n{transcript['answer']}".replace(decisive, "")
        verdict, call = _judge_exchange(adapter, transcript, exchange)
        if verdict == "fail":
            critic = _audit_warrant(
                harness, PREMISE_AUDIT, warrant.validity_node,
                {"warrant": warrant.id, "deleted": decisive[:120]}, llm=call,
            )
            if critic is not None:
                hits.append(critic)
        else:
            _log_calls(harness, [call])
    return hits


def planted_flaw_calibration(
    harness, adapter, config, calibration: list[tuple[str, bool]], rubric: str
) -> float:
    """Constructed flaws (circularity, equivocation, Persephone-vacuity) +
    clean controls: ground truth by construction makes this a PROGRAM check
    on an informal judge. Error rate is logged; > JUDGE_ERR_MAX spawns
    audit-the-critic."""
    errors = 0
    for content, has_flaw in calibration:
        pack = "\n".join([
            "STANDARD (calibration):", rubric, "",
            f"TARGET:\n{content}", "",
            "QUESTION: does the target violate the standard? verdict=fail iff yes.",
        ])
        ruling, _ = adapter.call("judge", pack, JudgeRuling)
        if (ruling.verdict == "fail") != has_flaw:
            errors += 1
    rate = errors / len(calibration) if calibration else 0.0
    harness.record_measure(inputs=[f"judge-error-rate:{rate:.4f}"])
    if config.JUDGE_ERR_MAX is not None and rate > config.JUDGE_ERR_MAX:
        spawn_audit_problem(harness, "planted-flaw-error-rate")
    return rate


def bias_probes(
    harness, adapter, config,
    self_preference_pairs: list[tuple[str, str]] = (),
    verbosity_pairs: list[tuple[str, str]] = (),
) -> dict:
    """Planted probes (§10.4): (own_family, foreign) authorship-masked
    pairs, and (terse, padded) same-content pairs. Preference measured over
    BOTH presentation orders; systematic preference is a measured bias
    logged against the judge's reliability record."""

    def preference_rate(pairs, first_is_probe: bool) -> float | None:
        if not pairs:
            return None
        preferred = 0
        total = 0
        for probe, other in pairs:
            for a_text, b_text, probe_label in (
                (probe, other, "A"), (other, probe, "B")
            ):
                pack = "\n".join([
                    "Which candidate is better? Judge content only.",
                    f"A:\n{a_text}", "", f"B:\n{b_text}", "",
                    "winner=neither if equal.",
                ])
                ruling, _ = adapter.call("judge", pack, PairwiseRuling)
                total += 1
                if ruling.winner == probe_label:
                    preferred += 1
        return preferred / total

    self_rate = preference_rate(self_preference_pairs, True)
    verbosity_rate = preference_rate(
        [(padded, terse) for terse, padded in verbosity_pairs], True
    )
    inputs = []
    if self_rate is not None:
        inputs.append(f"judge-self-preference:{self_rate:.4f}")
    if verbosity_rate is not None:
        inputs.append(f"judge-verbosity-bias:{verbosity_rate:.4f}")
    if inputs:
        harness.record_measure(inputs=inputs)
    return {"self_preference": self_rate, "verbosity": verbosity_rate}
