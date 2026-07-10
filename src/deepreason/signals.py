"""Signal registry: every measure tag the harness emits, documented once.

Measure events (Rule.MEASURE) carry a SIGNAL as ``inputs[0]`` — the machine-
readable answer to "what happened here?". This module is the single source of
truth for what each signal means, so a human following the log (or the
``signals``/``trace``/``narrate``/``report`` views) never meets an
undocumented tag. tests/test_signals.py AST-scans the source tree and fails
when a new record_measure/record_llm_calls literal is not registered here —
enforcement without call-site churn.

Two measure families carry NO signal string by design: HV estimates
(``hv_set`` payload, inputs = the measured artifact id) and reach sweeps
(``reach_set`` payload, inputs = the reached artifact ids). Recognize them by
their payload, not their inputs.
"""

SIGNALS: dict[str, str] = {
    # Scheduler heartbeat
    "cycle": "cycle heartbeat: [cycle, number, selected problem id or '-'] — "
             "every event that follows (by seq) until the next heartbeat "
             "belongs to this cycle",
    # Argumentative criticism accounting (rules/crit.py)
    "arg-crit": "argumentative critic ran and registered nothing new "
                "(no fault found, or the critic artifact deduplicated)",
    "arg-crit-cx-rejected": "the critic's counterexample failed to ground "
                            "(gate-rejected / property held) — the rejection "
                            "reason was echoed back for a retry",
    "arg-crit-overridden-by-execution": "execution supremacy: the target "
                                        "passes its execution oracle, so a "
                                        "purely argumentative case registered "
                                        "nothing",
    "batch-crit": "batched critic call over the listed targets registered "
                  "nothing that committed an event",
    "batch-crit-cx-retry": "shared counterexample-retry call for the listed "
                           "overridden targets",
    "property-wipeout-quarantine": "a proposed property's violation was "
                                   "quarantined: no sibling candidate "
                                   "satisfies the property, so it indicts the "
                                   "population, not the target",
    # Vision criticism (rules/vision.py)
    "vision-crit": "vision critic looked at the target's recorded screenshots "
                   "and registered nothing (no visible fault, or dedupe)",
    "vision-crit-overridden-by-execution": "execution supremacy blocked a "
                                           "visual argument against an "
                                           "in-process-oracle-backed target",
    # Browser oracle evidence (rules/act.py)
    "browser-pass": "the candidate was rendered and driven by the frozen "
                    "interaction script and PASSED every step — evidence "
                    "artifacts recorded",
    "browser-spec-overrun": "the browser interaction spec was unusable — a "
                            "spec defect, not the candidate's fault",
    # Experiment / property design (rules/experiment.py)
    "experiment-design": "experimenter call proposed input generators but "
                         "nothing committed an event (dedupe/empty)",
    "property-design": "property-designer call proposed checkers but nothing "
                       "committed an event (dedupe/empty)",
    # Scheduler rotation
    "disc-attempts-exhausted": "a discrimination problem hit its attempt cap "
                               "and is paused permanently — recorded as "
                               "unresolved, not retried into starvation",
    "spec-generation": "diversity-specification call for the cycle's problem",
    # record_llm_calls tags (spent calls that registered nothing themselves)
    "synth-noregister": "synthesizer call that registered no relation",
    "property-relevance-trial": "judge-ensemble call ruling whether a proposed "
                                "property follows from the problem statement",
    "hv-nomeasure": "variator call for an HV estimate that produced no measure",
    "conj-noregister": "conjecturer call whose candidates all failed admission",
    "trial-llm": "a trial-protocol call (critic/defender/judge/paraphrase)",
    "audit-llm": "an audit-protocol call",
    "dropped-call": "an LLM call was dropped (schema/endpoint failure); extra "
                    "inputs carry the reason — its spend is still on the record",
}

PREFIXES: dict[str, str] = {
    "gate:": "conjecture admission gate rejected a candidate (suffix = reason)",
    "spec-transmission:": "measured fraction of diversity specs realized "
                          "(suffix = score)",
    "trial-blocked:": "a trial ruling was screened out by a guard (suffix = "
                      "ensemble-split | referential-integrity | "
                      "paraphrase-flip | order-swap | unresolved-standard)",
    "audit-hit:": "a planted-flaw audit caught the judge (suffix = nu target)",
    "judge-error-rate:": "measured judge error rate on planted flaws "
                         "(suffix = rate)",
    "judge-self-preference:": "measured judge self-preference bias (suffix = rate)",
    "judge-verbosity-bias:": "measured judge verbosity bias (suffix = rate)",
    "hv-floor-nomeasure:": "hv-floor could not be measured for the target "
                           "(suffix = target id)",
    "controller-hold:": "self-calibration controller held its policy "
                        "(suffix = reason)",
    "intervention:": "capture-control response-ladder intervention fired "
                     "(suffix = stagnation-recruit | debt-sweep | "
                     "orbit-rotate | exogenous-brake | reseed)",
}

_UNREGISTERED = "(unregistered signal)"


def describe(signal: str) -> str:
    """One-line meaning: exact match first, then longest matching prefix."""
    if signal in SIGNALS:
        return SIGNALS[signal]
    best = ""
    for prefix in PREFIXES:
        if signal.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    return PREFIXES[best] if best else _UNREGISTERED


def is_known(signal: str) -> bool:
    return describe(signal) != _UNREGISTERED


def family(signal: str) -> str:
    """Normalize a signal to its registry key ('trial-blocked:*' for prefix
    families) — the grouping the report's signal counters use."""
    if signal in SIGNALS:
        return signal
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        if signal.startswith(prefix):
            return prefix + "*"
    return signal
