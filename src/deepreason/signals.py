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

from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# The contract (operator design law, 2026-08-14; v2 program Rung 1b).
#
# A signal is anything DECLARING a name, a unit, producer-agnostic semantics,
# and a staleness bound. New setups add signals by declaration through this
# typed channel -- never by teaching a consumer about a subsystem. The
# declaration is the contract; SIGNALS and PREFIXES below are DERIVED views of
# it, so the registry has one source of truth rather than two copies.
#
# `unspecified` is an honest debt marker, not a default. Every entry migrated
# from the pre-contract registry carries it, because inventing a unit for a
# signal whose author never stated one would be fabrication dressed as rigour.
# A NEW signal may not use it: tests/test_signal_contract.py pins the census so
# the debt can only shrink.
# ---------------------------------------------------------------------------

Unit = Literal[
    "unspecified",   # migrated before the contract; the author stated none
    "event",         # one occurrence of a discrete happening
    "count",         # a cardinal quantity carried in the payload
    "ratio",         # a dimensionless fraction
    "tokens",        # provider token spend
    "digest",        # a content address, carrying identity rather than size
]

Staleness = Literal[
    "unspecified",   # migrated before the contract
    "immediate",     # meaningful only in the cycle that emitted it
    "cycle",         # usable until the next cycle boundary
    "run",           # usable for the life of the run
    "permanent",     # a fact about the record, never stale
]


@dataclass(frozen=True)
class SignalDeclaration:
    """One signal's contract. Producer-agnostic by construction: `semantics`
    says what the signal MEANS, never which subsystem emits it -- a consumer
    that needs to know the producer is reaching around the contract."""

    name: str
    unit: Unit
    semantics: str
    staleness: Staleness

    def __post_init__(self) -> None:
        if not self.name or not self.semantics:
            raise ValueError(f"signal declaration incomplete: {self.name!r}")


# Entries migrated before the contract whose unit and staleness this tranche
# has the evidence to state (Rung 1b-ii). Their SEMANTICS PROSE IS UNTOUCHED --
# the paydown replaces `unspecified` in place and nothing else, so no signal
# name and no recorded meaning changes spelling. `REC-add-signal.md`'s paydown
# rule: lower MIGRATION_DEBT by exactly the number fixed, and say in the commit
# what evidence fixed it. Here the evidence is this rung's own consumption
# side, which defines when each is emitted and how long a consumer may believe
# it.
_PAID_DOWN: dict[str, tuple[Unit, Staleness]] = {
    # One bounded update; the next cycle's policy supersedes it.
    "controller-update": ("event", "cycle"),
    # Episode-deduplicated: the last statement stands for the run.
    "controller-authority": ("event", "run"),
    # A resume-time restatement of the limits already in force.
    "controller-rehydration": ("event", "run"),
    # One cycle's hold decision.
    "controller-hold:": ("event", "cycle"),
    # `Controller._new_transport_drops` counts these cumulatively across the
    # whole log, so an occurrence stays usable for the life of the run.
    "dropped-call": ("event", "run"),
}


def _migrated(entries: dict) -> dict:
    """Wrap a pre-contract registry literal as declarations.

    Their semantics are the prose their authors wrote, carried verbatim. Their
    unit and staleness are `unspecified` because nobody ever stated one, and
    that is the truthful record of the situation.
    """

    return {
        name: SignalDeclaration(
            name=name,
            unit=_PAID_DOWN.get(name, ("unspecified", "unspecified"))[0],
            semantics=meaning,
            staleness=_PAID_DOWN.get(name, ("unspecified", "unspecified"))[1],
        )
        for name, meaning in entries.items()
    }


_SIGNAL_MEANINGS: dict[str, str] = {
    "experimental-v5-override.v1": "explicit diagnostic-only override of "
                                    "the v5 active-inquiry containment gate "
                                    "(inputs: [signal, manifest digest]); "
                                    "authority/process only and prohibited "
                                    "in qualification campaigns",
    "dossier-pack-receipt.v1": "deterministic bounded selection receipt for "
                                 "one immutable run-input evidence dossier "
                                 "(inputs: [signal, receipt digest, selected "
                                 "source ids...]); attention and provenance "
                                 "only, never evidence admission or truth",
    "proposal-envelope-invalid": "a wire-valid conjecture proposal failed "
                                 "envelope compilation and was skipped "
                                 "(inputs: [signal, exception type]); the "
                                 "containment backstop from live_smoke_v1 "
                                 "finding F1 - model output never crashes "
                                 "the loop",
    # Scheduler heartbeat
    "cycle": "cycle heartbeat: [cycle, number, selected problem id or '-'] — "
             "every event that follows (by seq) until the next heartbeat "
             "belongs to this cycle",
    "run-resume": "same-root continuation began under the unchanged bound "
                  "manifest (inputs: [signal, prior stop digest, manifest "
                  "digest]); process-only and never an epistemic signal",
    "run-stop": "operational run stop at a safe boundary (inputs: [signal, "
                "stop-policy digest, canonical metrics, reason, event "
                "sequence]); never truth, completeness, or ontology status",
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
    "controller-authority": "the self-calibration controller stated which "
                            "roles it may steer and why not for the rest "
                            "(inputs: [signal, full|partial|none, canonical "
                            "JSON of steerable roles and blocked roles with "
                            "typed reasons]); re-emitted only when that set "
                            "changes, so an inert controller is never silent",
    "controller-rehydration": "resume restored the latest accepted bounded "
                              "controller limits onto freshly constructed "
                              "endpoints (inputs: [signal, policy artifact "
                              "id, canonical knob JSON]); process-only",
    # Pre-registered jolt-trigger pilot (views/jolt_signals.py, jolts.py).
    "jolt-functional-observation": "deterministic domain evaluator receipt "
                                   "for one candidate (inputs: [signal, "
                                   "canonical typed JSON]); Measure only and "
                                   "never status, a warrant, or a graph edge",
    "jolt-trigger": "replay-derived hard-orbit/soft-exhaustion diagnosis "
                    "receipt (inputs: [signal, canonical typed JSON]); an "
                    "attention decision only",
    "jolt-action": "one pre-registered prompt, representation, exemplar, or "
                   "fixed problem-focus action (inputs: [signal, canonical "
                   "typed JSON]); no status or adjudication mutation",
    "jolt-false-trigger": "seeded healthy-state sample for estimating jolt "
                          "harm (inputs: [signal, canonical JSON]); process "
                          "metadata only",
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
    "foreign-criticism-coverage.v1": "durable v4 process receipt that one "
                                      "school-owned target was exposed to an "
                                      "exact routed argumentative-critic call "
                                      "from a distinct foreign school (inputs: "
                                      "[signal, target id, owner:<school>, "
                                      "critic:<school>, source:<event seq>, "
                                      "route:<sha256>]); coverage only, never "
                                      "a verdict, warrant, attack, or status",
    "scrutiny": "observe-only criticism authority (RC1): the critic's case "
                "registered as scrutiny evidence with NO warrant (inputs: "
                "[signal, target id, critic artifact id]); status unchanged",
    "trial-declined": "trial_required criticism authority: the defended "
                      "trial over a precomputed case did not sustain "
                      "(inputs: [signal, target id, reason]); no warrant",
    "trial-observation": "advisory rubric trial completed without a warrant "
                         "or attack edge (inputs: [signal, target id, "
                         "observation artifact id, outcome]); the artifact "
                         "retains the case, defence, rulings, and guard result",
    "pairwise-observation": "advisory pairwise comparison completed without "
                            "a warrant or status change (inputs: [signal, "
                            "problem id, observation artifact id, outcome]); "
                            "the artifact retains both preferences and the "
                            "order-swap result",
    "infra-review-no-case": "explicit infrastructure review ran and the "
                            "critic mounted no case (inputs: [signal, "
                            "artifact id]); the call is on the record",
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
    "property-relevance-declined": "ADJUDICATION_STATUS_AUTHORITY_ENABLED is "
                                   "False: no judge was dispatched for the "
                                   "property's relevance trial, so it neither "
                                   "activates this round nor is refuted "
                                   "(inputs: [signal, property artifact id]); "
                                   "status untouched, mirrors observe_only",
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
    "stop-escape": "convergence policy selected one bounded escape-ladder "
                   "action at a completed cycle boundary (inputs: [signal, "
                   "action, cycle]); attention only",
    "scheduler-stop": "the deterministic stop policy ended scheduling at a "
                      "completed cycle boundary (inputs: [signal, reason, "
                      "policy digest]); no epistemic status is changed",
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
    # Cross-run skills (skills/): pinned attention and explicit current reruns
    "skills-retrieval": "an immutable skill snapshot was ranked and sliced "
                        "for schools (inputs: [signal, receipt digest, receipt "
                        "blob]). Attention only; it supplies no support, "
                        "evidence, warrant, grounding, or status credit",
    "skills-adoption": "a current candidate explicitly adopted exact test "
                       "definitions and reran them now (inputs: [signal, "
                       "capsule id, source candidate id, adopted candidate "
                       "id, commitment:verdict...]). Old source verdicts do "
                       "not transfer",
    # Advisory scratch authoring (scratch/authoring.py)
    "scratch-call-failed": "a bounded scratch authoring or guide call exhausted "
                           "schema/endpoint repair and registered no authored "
                           "content (inputs: [signal, contract id]); process-only",
    "scratch-guide-stale": "a model-authored cluster guide completed after its "
                           "bound snapshot stopped being current, so the guide "
                           "was discarded (inputs: [signal, cluster id, snapshot "
                           "hash]); attention-only and never authority",
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
    "relatedness-trial": "judge-ensemble call ruling whether a candidate_checker "
                         "commitment is directly related to its conjecture's "
                         "own explanation (D2 rev 2, R35); registers nothing "
                         "itself, but is spent even on a losing ruling",
    "encoder-delegation": "coder-seat call authoring commitment code for an "
                          "already-admitted conjecture's own prose (D2 rev 2, "
                          "R38); registers nothing itself — the caller attaches "
                          "the returned spec via the ordinary draft/register path",
    "hv-nomeasure": "variator call for an HV estimate that produced no measure",
    "conj-noregister": "conjecturer call whose candidates all failed admission",
    "conjecture-turn-call": "one active v4 conjecturer turn completed; the exact "
                            "prompt, raw output, route, contract, spend, and "
                            "optional advisory context are bound to this "
                            "process-only event",
    "trial-llm": "a trial-protocol call (critic/defender/judge/paraphrase)",
    "audit-llm": "an audit-protocol call",
    "dropped-call": "an LLM call was dropped (schema/endpoint failure); extra "
                    "inputs carry the reason — its spend is still on the record",
}

_PREFIX_MEANINGS: dict[str, str] = {
    "evidence-citation:": "one deterministic check of a candidate's claimed "
                          "grounding in an admitted dossier block (suffix = "
                          "typed outcome code, verified or failed; inputs: "
                          "[signal, block id or claimed ref, candidate "
                          "artifact id, problem id]); attention and "
                          "diagnostics for criticism, never a status",
    "gate:": "conjecture admission gate rejected a candidate (suffix = reason)",
    "research-fetch:": "one contained web-fetch attempt for a research "
                       "problem (suffix = FETCHED or a typed refusal/"
                       "failure code; inputs: [signal, host, "
                       "requests:used/limit, problem id]); every attempt "
                       "reaches the log — successes, refusals, and the "
                       "typed budget-exhaustion record alike",
    "research-allowance:": "replay-derived working allowance for contained "
                           "research grants inside the frozen envelope "
                           "(suffix = allowance/cap; inputs: [signal, "
                           "waste:uncited/consumed, refusal-streak:n, "
                           "stagnation:0|1, problem id]); recorded before "
                           "every grant decision so each tightening or "
                           "widening of where tokens flow is attackable in "
                           "the log — the frozen cap itself never moves",
    "config-critique:": "one config-referee review outcome over standard "
                        "views (suffix = config_effective | config_mistuned "
                        "| REJECTED_UNFOUNDED; grounded verdicts carry "
                        "inputs: [signal, recommendation:menu-entry, "
                        "cited:seq list, view ref, verdict ref]); advice "
                        "and attention on the record only — no budget, "
                        "status, or policy byte moves because the referee "
                        "spoke, and an uncited verdict is recorded as its "
                        "own rejection",
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

# ---------------------------------------------------------------------------
# Signals declared UNDER the contract. Not `_migrated`: their authors stated a
# unit and a staleness bound, which is what the contract asks for and what
# `unspecified` records the absence of.
# ---------------------------------------------------------------------------

_DECLARED: tuple[SignalDeclaration, ...] = (
    # The v2 calculus program's three detection signals (Rung 2 / Amendment 3),
    # declared so Rung 1b-ii's allocation policy has something to consume.
    # Every one prices ATTENTION and none may reach a label.
    SignalDeclaration(
        name="problem.thrash.v1",
        unit="ratio",
        semantics="fraction of recent consecutive work units that changed "
                  "subject: 0.0 means work stayed on one problem (depth), 1.0 "
                  "means every unit moved to a different one (scatter). "
                  "Read over a bounded recent window, so it answers 'lately'. "
                  "It is evidence about where effort went and about nothing "
                  "else — never about whether any problem is solved, solvable, "
                  "or worth working",
        staleness="cycle",
    ),
    SignalDeclaration(
        name="criticism.attack-target-entropy.v1",
        unit="ratio",
        semantics="normalised Shannon entropy (0..1) of how the standing "
                  "attack edges are distributed over the targets they attack: "
                  "1.0 means criticism is spread evenly over everything it has "
                  "touched, near 0 means it is concentrated on a single "
                  "target, and 0.0 also covers 'fewer than two targets have "
                  "been attacked at all'. Dispersion only — it says nothing "
                  "about whether any attack is sound or any target is wrong",
        staleness="cycle",
    ),
    SignalDeclaration(
        name="problem.independence-resolution-rate.v1",
        unit="ratio",
        semantics="fraction of consulted premise-orphan resolutions settled as "
                  "INDEPENDENCE rather than retirement or translation — the "
                  "calculus's over-binding diagnostic (§9.8): a high rate says "
                  "questions are being marked as resting on premises they turn "
                  "out not to need. 0.0 when nothing has been resolved. "
                  "Diagnostic only; it neither validates nor impugns any "
                  "resolution, each of which is an attackable artifact",
        staleness="run",
    ),
    # The premise channel's two process receipts. They exist because a
    # mechanism nobody triggers is a mechanism that never runs (ERRATA E28),
    # and a receipt is the only way that is visible from the record alone.
    SignalDeclaration(
        name="premise.work-invited.v1",
        unit="event",
        semantics="an invitation to name what the problem itself presupposes "
                  "was standing when a unit of work began (inputs: [signal, "
                  "problem id]). Attention only: it offers a question, mints "
                  "no problem, and carries no reward for accepting and no "
                  "penalty for declining",
        staleness="cycle",
    ),
    SignalDeclaration(
        name="premise.rent-undecided.v1",
        unit="event",
        semantics="a premise was NOT refuted by demarcation, and why (inputs: "
                  "[signal, premise artifact id, reason]): either the "
                  "load-bearingness reading was unavailable, or a sampled role "
                  "variant drew a different verdict from the battery, so the "
                  "claim does work. The distinction this records is the one "
                  "silence destroys — 'we could not check' is not 'we checked "
                  "and it was fine', and neither is a verdict about the "
                  "premise",
        staleness="run",
    ),
    SignalDeclaration(
        name="demarcation-variation",
        unit="tokens",
        semantics="one variator sample taken to decide whether a claim's "
                  "mechanism is load-bearing (§12.2). The call registers "
                  "nothing itself; its spend and THE SAMPLED VARIANTS "
                  "THEMSELVES are on this event, which is how a non-seeded "
                  "kernel meets the replay-determinism requirement (§12.1 "
                  "permits either a seeded total function or explicitly "
                  "logged variants). A sample, never a proof: whatever "
                  "consumes it owes its own validity node the declaration "
                  "that it rested on one",
        staleness="permanent",
    ),
    SignalDeclaration(
        name="premise.attribution-filed.v1",
        unit="event",
        semantics="a premise artifact and its attribution reached the record "
                  "for one problem (inputs: [signal, problem id, the target "
                  "whose criticism carried it]). Registration is not a "
                  "verdict: both artifacts are ordinary and attackable, the "
                  "problem is marked only if the attribution stands AND the "
                  "premise falls, and a mark is an open question rather than a "
                  "status",
        staleness="permanent",
    ),
    SignalDeclaration(
        name="allocation.seat-truncation.v1",
        unit="ratio",
        semantics="the share of one SEAT INSTANCE's recent provider calls that "
                  "hit the completion length limit. Keyed by seat instance, "
                  "not role: two structurally asymmetric seats filled by one "
                  "conjecturer are two signals, because they may need "
                  "throttling independently. A process fact about transport, "
                  "never about the content that was truncated -- it may price "
                  "a completion cap and may never reach a label",
        staleness="cycle",
    ),
    SignalDeclaration(
        name="allocation.seat-repair.v1",
        unit="ratio",
        semantics="the share of one SEAT INSTANCE's recent provider calls that "
                  "consumed more than one completion attempt (schema or "
                  "transport repair). Keyed by seat instance for the same "
                  "reason as the truncation share. Says the wire was expensive, "
                  "never that the output was wrong: a repaired call and a "
                  "first-pass call are equally admissible evidence",
        staleness="cycle",
    ),
    SignalDeclaration(
        name="allocation.policy-authorized.v1",
        unit="event",
        semantics="a controller policy's limits are the ones currently in "
                  "force. Read on resume to restore the limits a run was "
                  "already operating under, and after a hold to revert to "
                  "them. It is an adjudication outcome about the ALLOCATION "
                  "layer's own artifact and confers nothing on any other "
                  "artifact's status",
        staleness="run",
    ),
    SignalDeclaration(
        name="allocation.policy-contested.v1",
        unit="event",
        semantics="a controller policy is under an unresolved attack, so "
                  "allocation must hold its current limits (fail-static). A "
                  "topology binding no seat that can attack an artifact cannot "
                  "produce this signal at all, which is a disclosed open loop "
                  "rather than a fault. Reading it changes only how much a "
                  "seat may spend, never what any artifact is",
        staleness="run",
    ),
)


# Prefix families declared under the Rung 1b-i contract. Separate from
# _PREFIX_MEANINGS for the same reason _DECLARED is separate from
# _SIGNAL_MEANINGS: that dict is the pre-contract migration pool and every
# entry in it carries `unspecified`, which a new signal may not.
_DECLARED_PREFIXES: tuple[SignalDeclaration, ...] = (
    SignalDeclaration(
        name="premise-citation:",
        unit="event",
        semantics="one deterministic check of a citation a PREMISE "
                  "attribution claimed (suffix = typed outcome code; inputs: "
                  "[signal, block id or claimed ref, problem id]). Distinct "
                  "from evidence-citation in its SUBJECT and in its BINDING: "
                  "the subject is the problem's presupposition rather than a "
                  "candidate, and the check resolves against the blocks that "
                  "call's own exposure receipt records, so a real admitted "
                  "block the call was never shown records NOT_EXPOSED rather "
                  "than verifying. A verified check is not support for the "
                  "premise — it says the quoted bytes are the admitted bytes, "
                  "and nothing about whether the premise is true",
        staleness="permanent",
    ),
)


# The declarations are the contract; these two are derived views of it.
SIGNAL_DECLARATIONS: dict[str, SignalDeclaration] = _migrated(_SIGNAL_MEANINGS)
SIGNAL_DECLARATIONS.update({d.name: d for d in _DECLARED})
PREFIX_DECLARATIONS: dict[str, SignalDeclaration] = _migrated(_PREFIX_MEANINGS)
PREFIX_DECLARATIONS.update({d.name: d for d in _DECLARED_PREFIXES})

SIGNALS: dict[str, str] = {n: d.semantics for n, d in SIGNAL_DECLARATIONS.items()}
PREFIXES: dict[str, str] = {n: d.semantics for n, d in PREFIX_DECLARATIONS.items()}


def declaration(signal: str) -> SignalDeclaration | None:
    """The contract for one signal: exact match first, then longest prefix."""
    exact = SIGNAL_DECLARATIONS.get(signal)
    if exact is not None:
        return exact
    matches = [p for p in PREFIX_DECLARATIONS if signal.startswith(p)]
    if not matches:
        return None
    return PREFIX_DECLARATIONS[max(matches, key=len)]


def unspecified_declarations() -> list[str]:
    """Names whose unit or staleness predates the contract. This list is the
    migration debt: pinned by a test, allowed to shrink, never to grow."""
    return sorted(
        name
        for name, d in {**SIGNAL_DECLARATIONS, **PREFIX_DECLARATIONS}.items()
        if d.unit == "unspecified" or d.staleness == "unspecified"
    )


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
