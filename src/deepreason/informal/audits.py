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
from deepreason.llm.packs import aliases_for_values
from deepreason.ontology import Commitment
from deepreason.rules.warrants import register_fail_warrant, verdict_on_record

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

    ``llm`` is one representative record from the unanimous ensemble that
    produced the finding; the other seats are logged on audit Measure events.
    The representative occupies the event schema's singular LLM slot but has
    no independent authority over registration.
    """
    harness.register_commitment(audit_commitment)
    if verdict_on_record(harness, audit_commitment.id, nu_target):
        return None
    critic = register_fail_warrant(
        harness,
        commitment_id=audit_commitment.id,
        target_id=nu_target,
        nu_content=f"nu: the {audit_commitment.id} finding against {nu_target} is sound",
        critic_content=f"audit-critic: {audit_commitment.id} hit on {nu_target[:12]}",
        trace_ref=harness.blobs.put(canonical_json(finding)),
        llm=llm,
    )
    harness.record_measure(inputs=[f"audit-hit:{nu_target}", audit_commitment.id])
    return critic


def _ensemble_call(
    adapter,
    seats,
    pack: str,
    output_model,
    aliases,
    calls: list,
    decision_field: str,
):
    """Call every frozen judge seat and return only a unanimous ruling.

    ``calls`` belongs to the outer audit and is appended as each seat lands,
    so a later seat failure cannot erase earlier spend.  Distinct grounds are
    allowed; disagreement means different normative decisions (verdict or
    winner) and returns ``None`` rather than selecting seat zero.
    """
    rulings = []
    for index in range(len(seats)):
        ruling, llm_call = adapter.call(
            "judge",
            pack,
            output_model,
            endpoint_index=index,
            aliases=aliases,
        )
        calls.append(llm_call)
        rulings.append(ruling)
    decisions = {getattr(ruling, decision_field) for ruling in rulings}
    return (rulings[0] if len(decisions) == 1 else None), rulings


def _judge_exchange(adapter, seats, exchange: str, calls: list):
    pack = "\n".join([
        "Re-rule on this exchange (audit replay).",
        "THE CASE FOR FAIL:", exchange, "",
        "verdict=fail iff the case establishes the violation.",
    ])
    ruling, rulings = _ensemble_call(
        adapter,
        seats,
        pack,
        JudgeRuling,
        aliases_for_values([exchange], prefix="K"),
        calls,
        "verdict",
    )
    return (ruling.verdict if ruling is not None else None), rulings


def _log_calls(harness, calls) -> None:
    """Persist audit LLM calls that did not land on a critic event (variator
    paraphrases, non-decisive re-rulings) — see Harness.record_llm_calls."""
    harness.record_llm_calls(calls, "audit-llm")


def paraphrase_invariance_audit(harness, adapter, config) -> list:
    """Re-run logged rulings on variator paraphrases; flips are hits."""
    warrants = list(_rubric_warrants(harness))
    if not warrants:
        return []
    # Preflight the whole frozen ensemble before the variator (or any other
    # endpoint) can spend.  Audits are normative criticism, not a convenience
    # path around the rubric ensemble requirement.
    seats = adapter.require_cross_family_judges()
    hits = []
    for warrant, transcript in warrants:
        calls = []
        try:
            exchange = f"{transcript['case']}\n{transcript['answer']}"
            para, para_call = adapter.call(
                "variator",
                f"TARGET CONTENT:\n{exchange}\n\nDIRECTIVE: produce exactly "
                f"{config.TRIAL_PARAPHRASE_N} meaning-preserving paraphrases.",
                VariatorOutput,
            )
            calls.append(para_call)
            flips = []
            registration_call = None
            split = False
            for p in para.edits[: config.TRIAL_PARAPHRASE_N]:
                verdict, _ = _judge_exchange(adapter, seats, p.content, calls)
                if verdict is None:
                    split = True
                    break
                if verdict != "fail":
                    flips.append(p.content[:80])
                    # The graph decision is unanimous; one representative
                    # call may ride its event while every other seat is logged
                    # separately below.
                    registration_call = calls[-len(seats)]
            if split:
                harness.record_measure(
                    inputs=["audit-blocked:ensemble-split", warrant.id]
                )
                continue
            if flips:
                before = set(harness.state.artifacts)
                critic = _audit_warrant(
                    harness,
                    PARAPHRASE_AUDIT,
                    warrant.validity_node,
                    {
                        "warrant": warrant.id,
                        "flips": flips,
                        "ensemble": len(seats),
                    },
                    llm=registration_call,
                )
                # The representative re-ruling rides the critic event only if
                # one committed; an on-record/deduped audit commits nothing.
                if (
                    critic is not None
                    and critic.id not in before
                    and registration_call is not None
                ):
                    calls.remove(registration_call)
                if critic is not None:
                    hits.append(critic)
        finally:
            _log_calls(harness, calls)
    return hits


def premise_deletion_audit(harness, adapter, config) -> list:
    """Delete the cited decisive_point; the verdict SHOULD flip. A verdict
    that survives the removal of its own stated grounds is easy to vary."""
    warrants = list(_rubric_warrants(harness))
    if not warrants:
        return []
    seats = adapter.require_cross_family_judges()
    hits = []
    for warrant, transcript in warrants:
        calls = []
        try:
            decisive = transcript["ruling"]["decisive_point"]
            exchange = f"{transcript['case']}\n{transcript['answer']}".replace(
                decisive, ""
            )
            verdict, _ = _judge_exchange(adapter, seats, exchange, calls)
            if verdict is None:
                harness.record_measure(
                    inputs=["audit-blocked:ensemble-split", warrant.id]
                )
                continue
            if verdict == "fail":
                registration_call = calls[-len(seats)]
                before = set(harness.state.artifacts)
                critic = _audit_warrant(
                    harness,
                    PREMISE_AUDIT,
                    warrant.validity_node,
                    {
                        "warrant": warrant.id,
                        "deleted": decisive[:120],
                        "ensemble": len(seats),
                    },
                    llm=registration_call,
                )
                if critic is not None and critic.id not in before:
                    calls.remove(registration_call)
                if critic is not None:
                    hits.append(critic)
        finally:
            _log_calls(harness, calls)
    return hits


def planted_flaw_calibration(
    harness, adapter, config, calibration: list[tuple[str, bool]], rubric: str
) -> float | None:
    """Constructed flaws (circularity, equivocation, Persephone-vacuity) +
    clean controls: ground truth by construction makes this a PROGRAM check
    on an informal judge. Error rate is logged; > JUDGE_ERR_MAX spawns
    audit-the-critic."""
    seats = adapter.require_cross_family_judges()
    errors = 0
    calls = []
    split = False
    try:
        for content, has_flaw in calibration:
            pack = "\n".join([
                "STANDARD (calibration):", rubric, "",
                f"TARGET:\n{content}", "",
                "QUESTION: does the target violate the standard? "
                "verdict=fail iff yes.",
            ])
            ruling, _ = _ensemble_call(
                adapter,
                seats,
                pack,
                JudgeRuling,
                aliases_for_values([content], prefix="K"),
                calls,
                "verdict",
            )
            if ruling is None:
                split = True
                break
            if (ruling.verdict == "fail") != has_flaw:
                errors += 1
    finally:
        _log_calls(harness, calls)
    if split:
        harness.record_measure(inputs=["audit-blocked:ensemble-split", "calibration"])
        return None
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

    if self_preference_pairs or verbosity_pairs:
        seats = adapter.require_cross_family_judges()
    else:
        seats = ()

    calls = []

    def preference_rate(pairs) -> float | None:
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
                ruling, _ = _ensemble_call(
                    adapter,
                    seats,
                    pack,
                    PairwiseRuling,
                    aliases_for_values([a_text, b_text], prefix="K"),
                    calls,
                    "winner",
                )
                if ruling is None:
                    harness.record_measure(
                        inputs=["audit-blocked:ensemble-split", "bias-probe"]
                    )
                    return None
                total += 1
                if ruling.winner == probe_label:
                    preferred += 1
        return preferred / total

    try:
        self_rate = preference_rate(self_preference_pairs)
        verbosity_rate = preference_rate(
            [(padded, terse) for terse, padded in verbosity_pairs]
        )
    finally:
        _log_calls(harness, calls)
    inputs = []
    if self_rate is not None:
        inputs.append(f"judge-self-preference:{self_rate:.4f}")
    if verbosity_rate is not None:
        inputs.append(f"judge-verbosity-bias:{verbosity_rate:.4f}")
    if inputs:
        harness.record_measure(inputs=inputs)
    return {"self_preference": self_rate, "verbosity": verbosity_rate}
