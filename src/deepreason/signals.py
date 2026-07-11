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
    # Embedder geometry identity (llm/embedder.py; adjudicated in
    # runs/embedder_design — cross-environment drift is detected, never denied)
    "embedder": "geometry identity stamp, once per run before the first "
                "heartbeat: [signal, model, library versions, sentinel-"
                "embedding hash] — school geometry and atlas distances are "
                "comparable across runs iff these match",
    "embedder-fallback": "EMBEDDER_MODEL was set but the backend is "
                         "unavailable; the run degraded to the hashing "
                         "embedder (inputs: [signal, model, reason])",
    # Staged pipeline (easy.py make: plan -> design -> build)
    "assembled": "chunked build: repository code composed the accepted "
                 "component fragments into a page artifact (inputs: [signal, "
                 "assembled artifact id, component names...])",
    "integration-repair": "static integration criticism failed on an "
                          "assembled page; the implicated components get "
                          "TARGETED successor repair problems (inputs: "
                          "[signal, assembled id, implicated-names JSON])",
    "import-deferred": "runtime package resolution or bundling hit an "
                       "operational failure (registry, archive, integrity, "
                       "sandbox or toolchain): no verdict or warrant is "
                       "created and the accepted design stays schedulable "
                       "(inputs: [signal, design id, failure category])",
    "stage-pick": "staged pipeline chose a stage's surviving artifact as the "
                  "next stage's frozen foundation (inputs: [signal, stage, "
                  "artifact id]) — attention only; the lineage commitment "
                  "carries the authority",
    "website-stage": "deterministic website workflow transition result "
                     "(inputs: [signal, stage, outcome, next action, attempt]); "
                     "process-only and never an acceptance or status signal",
    "website-terminal": "website workflow stopped with a typed terminal "
                        "summary (inputs: [signal, stage, outcome, resume "
                        "command]); no invalid page is exported",
    "website-design-mode": "website design transport changed only by the "
                           "deterministic profile policy (inputs: [signal, "
                           "source profile, selected recovery mode]); never "
                           "a model-authored route or status change",
    "website-compact-call": "one bounded compact website micro-call completed "
                            "(outline, art direction, or one component "
                            "contract); its prompt/raw refs and spend are on "
                            "this process-only event",
    "website-compact-dropped": "a compact website micro-call exhausted "
                               "schema or transport repair; its spend remains "
                               "logged and no partial value is compiled",
    "website-compact-critic-dropped": "ordinary argumentative criticism of "
                                      "a compiled compact design hit an "
                                      "operational/schema failure; no verdict "
                                      "was inferred from the dropped call",
    "controller-update": "bounded self-calibration update derived only from "
                         "process-health signals (inputs: [signal, canonical "
                         "JSON with knob deltas and evidence]); a Measure "
                         "only, never an artifact, warrant, or status",
    "controller-rehydration": "resume restored the latest accepted bounded "
                              "controller limits onto freshly constructed "
                              "endpoints (inputs: [signal, policy artifact "
                              "id, canonical knob JSON]); process-only",
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
    "property-checker-crash": "a conjectured checker THREW on a real domain "
                              "input — the crash refutes the CHECKER (its "
                              "well-formedness claim), never the candidate "
                              "(inputs: [signal, property id, error])",
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
    "disc-transport-deferred": "a discrimination ruling was dropped by a "
                               "TRANSPORT failure: not an epistemic verdict, "
                               "so it does not count toward the permanent "
                               "attempt cap — the rivalry stays schedulable "
                               "(inputs: [signal, problem id])",
    "hv-skip-oversize": "lazy HV spot-check skipped: the artifact's content "
                        "exceeds HV_CONTENT_MAX_CHARS, so K whole-content "
                        "variator edits cannot fit a completion window "
                        "(inputs: [signal, artifact id, char count])",
    "spec-generation": "diversity-specification call for the cycle's problem",
    # Research service (§12; research/backends.py, ops.py)
    "research-off": "research is deliberately DISABLED (RESEARCH_BACKEND: "
                    "null) while uncovered research problems exist — logged "
                    "once per continuous unavailable-state episode",
    "research-awaiting-agent": "agent mode: uncovered research problems are "
                               "waiting in ops.research_docket for the "
                               "operating agent — the ordinary waiting state "
                               "(once per episode; inputs carry problem ids). "
                               "Never emitted as research being off",
    "research-agent-requested": "grounding-decay escalation (§11.4) of "
                                "agent-serviced research problems to top "
                                "priority — a capture-response intervention "
                                "(inputs: [signal, triggering flag, problem "
                                "ids...])",
    "research-fetch-failed": "one retrieval attempt failed (inputs: [signal, "
                             "problem id, cycle or '-', strategy, category, "
                             "reason]). Operational only — never evidence, "
                             "never a verdict; internal attempts feed the "
                             "cooldown/cap reconstruction, 'agent' reports "
                             "do not",
    "research-fetch-exhausted": "a research problem hit RESEARCH_ATTEMPTS_MAX "
                                "internal failures: that internal strategy "
                                "pauses (attention only) — the problem stays "
                                "open and the agent channel can still cover it",
    "research-evidence-registered": "ops.submit_evidence registered candidate "
                                    "evidence (inputs: [signal, problem id, "
                                    "evidence id, source]). Registration is "
                                    "not coverage: that is derived from the "
                                    "graph after relevance and reliability "
                                    "hold",
    # Payload-recognized pseudo-signals (bare-id measures; see event_signal)
    "hv": "hard-to-vary estimate recorded (hv_set payload; inputs = artifact id)",
    "reach-provisional": "cross-problem survival on a battery below "
                         "REACH_COVERAGE_MIN coverage - logged for attention, "
                         "grounds no reach, no addressing, no debt (inputs: "
                         "[signal, artifact id, foreign problem id])",
    "reach": "reach sweep recorded (reach_set payload; inputs = reached ids)",
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
    "audit-blocked:": "a judge audit was screened out before graph mutation "
                      "(suffix = ensemble-split)",
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


def event_signal(event) -> str | None:
    """The signal of a Measure event; None for non-measures. The two bare-id
    measure families are recognized by PAYLOAD: 'hv' (hv_set) and 'reach'
    (reach_set) — their inputs are artifact ids, not tags."""
    if event.rule.value != "Measure":
        return None
    if event.state_diff.hv_set:
        return "hv"
    if event.state_diff.reach_set or getattr(event.state_diff, "addr_add", None):
        return "reach"
    return str(event.inputs[0]) if event.inputs else ""
