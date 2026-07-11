#!/usr/bin/env python
"""Live P6 run against an OpenAI-compatible provider (default: DeepSeek).

Usage:
    DEEPSEEK_API_KEY=... python scripts/live_run.py \
        --root runs/live --cycles 4 --suite republic \
        --token-budget 400000 [--model deepseek-v4-pro] [--dry-run]

Role routing comes entirely from the selected config profile. ``auto`` and
``auto-alt`` model ids resolve against the provider's /models list through the
same adapter path used by the CLI and MCP. ``--model`` is an exact primary-seat
override; the second judge seat remains ``auto-alt``.

Suites:
  tides     — formal-ish: program predicates only, every verdict exogenous.
  republic  — informal (§10): skeleton-wf pinned, a registered standard,
              a rubric criterion judged under the live trial protocol
              (judge ensemble, order-swap, paraphrase spot-check).

The --token-budget is a HARD ceiling on prompt+completion tokens for the
whole run; the scheduler stops gracefully when it is reached.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.config import (  # noqa: E402
    Config,
    apply_overrides,
    load as load_config,
    parse_overrides,
    parse_value,
    role_api_key_envs,
)
from deepreason.harness import Harness  # noqa: E402
from deepreason.informal.skeleton import skeleton_wf_commitment  # noqa: E402
from deepreason.informal.standards import register_standard  # noqa: E402
from deepreason.llm.adapter import build_adapter  # noqa: E402
from deepreason.llm.budget import TokenMeter  # noqa: E402
from deepreason.ontology import Commitment, Problem, ProblemProvenance  # noqa: E402
from deepreason.report import eval_report  # noqa: E402
from deepreason.scheduler.scheduler import Scheduler  # noqa: E402
from deepreason.views.theory import theory  # noqa: E402

def _runtime_role_overrides(config: Config, args) -> Config:
    """Translate legacy live-run flags into the canonical role table."""
    data = config.model_dump(mode="python")
    for role, configured in data["roles"].items():
        seats = configured if isinstance(configured, list) else [configured]
        for index, seat in enumerate(seats):
            if not isinstance(seat, dict):
                continue
            if args.base_url is not None:
                seat["endpoint"] = args.base_url
            if args.api_key_env is not None:
                seat["api_key_env"] = args.api_key_env
            if args.model is not None:
                seat["model"] = "auto-alt" if role == "judge" and index else args.model
    conjecturer = data["roles"].get("conjecturer")
    if isinstance(conjecturer, dict):
        if args.reasoning != "policy":
            conjecturer["reasoning"] = (
                None if args.reasoning == "default" else parse_value(args.reasoning)
            )
        if args.starve_cap is not None:
            conjecturer["max_tokens"] = args.starve_cap
    return Config.model_validate(data)


def _resolved_models(adapter) -> dict[str, list[str]]:
    return {
        role: [endpoint.model for endpoint in (configured if isinstance(configured, list)
                                                else [configured])]
        for role, configured in adapter.endpoints.items()
    }


def seed_tides(harness: Harness) -> None:
    harness.register_commitment(
        Commitment(id="k-mechanism", eval="predicate:len(content) > 120")
    )
    harness.register_commitment(
        Commitment(
            id="k-tidal-facts",
            eval=(
                "predicate:('moon' in content.lower() or 'lunar' in content.lower()) "
                "and ('sun' in content.lower() or 'solar' in content.lower())"
            ),
        )
    )
    harness.register_problem(
        Problem(
            id="pi-tides",
            description=(
                "Explain why most coasts see two high tides a day, why their "
                "height varies across the month, and why a few seas (e.g. the "
                "Gulf of Mexico) see only one."
            ),
            criteria=["k-mechanism", "k-tidal-facts"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


# ONE canonical std-hist rubric for every historical-mechanism suite
# (republic, bronze, needham) — identical text content-address-dedupes, so
# the effective standard cannot drift between suites (same rationale as
# STD_DESIGN_RUBRIC below).
STD_HIST_RUBRIC = (
    "A historical-mechanism account must: (1) name a specific causal "
    "mechanism — an institution, incentive, or process — not a mood, "
    "essence, or inevitability; (2) state forbidden cases that are "
    "concrete observations which could realistically have obtained "
    "(a record, an event, a datable pattern); (3) claims of the form "
    "'decline was inevitable' or 'moral decay' with no mechanism "
    "violate this standard."
)

_HIST_SKELETON_SHAPE = (
    "Each candidate's content MUST be a JSON skeleton object, exactly this "
    'shape: {"claim": str, "mechanism": str, '
    '"scope": {"covers": [str], "excludes": [str]}, '
    '"forbidden": [{"case": str, "eval": "rubric:std-hist"}], '
    '"prose_notes": str}. '
    "The forbidden cases must be historical observations that would "
    "have refuted the account had they obtained."
)


def seed_republic(harness: Harness) -> None:
    """Informal-domain suite (§10): skeletons + a standard + a rubric trial."""
    register_standard(harness, "std-hist", rubric=STD_HIST_RUBRIC, mode="absolute")
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-hist", eval="rubric:std-hist"))
    harness.register_problem(
        Problem(
            id="pi-republic",
            description=(
                "Why did the Roman Republic, after four centuries of durable "
                "aristocratic power-sharing, collapse into one-man rule within a "
                "single lifetime (133-27 BC)? Each candidate's content MUST be a "
                "JSON skeleton object, exactly this shape: "
                '{"claim": str, "mechanism": str, '
                '"scope": {"covers": [str], "excludes": [str]}, '
                '"forbidden": [{"case": str, "eval": "rubric:std-hist"}], '
                '"prose_notes": str}. '
                "The forbidden cases must be historical observations that would "
                "have refuted the account had they obtained."
            ),
            criteria=["skeleton-wf", "kappa-hist"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_bronze(harness: Harness) -> None:
    """Fresh informal problem #1 for the rank-concentration experiment
    (experiments/rank_concentration_prereg.yaml): same standard, same
    skeleton discipline as republic, never run before."""
    register_standard(harness, "std-hist", rubric=STD_HIST_RUBRIC, mode="absolute")
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-hist", eval="rubric:std-hist"))
    harness.register_problem(
        Problem(
            id="pi-bronze",
            description=(
                "Why did the interconnected palace civilizations of the "
                "Eastern Mediterranean — Mycenaean Greece, Hittite Anatolia, "
                "Ugarit and the Levantine city-states — collapse nearly "
                "simultaneously around 1200-1150 BC after centuries of "
                "stability, while Egypt survived diminished? "
                + _HIST_SKELETON_SHAPE
            ),
            criteria=["skeleton-wf", "kappa-hist"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_needham(harness: Harness) -> None:
    """Fresh informal problem #2 for the rank-concentration experiment:
    the Needham question — same standard, same skeleton discipline."""
    register_standard(harness, "std-hist", rubric=STD_HIST_RUBRIC, mode="absolute")
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-hist", eval="rubric:std-hist"))
    harness.register_problem(
        Problem(
            id="pi-needham",
            description=(
                "Why did sustained, cumulative, mathematized experimental "
                "science emerge in early modern Europe (roughly 1550-1700) "
                "rather than in Song-through-Ming China, which for centuries "
                "had been richer, more populous, and technologically ahead "
                "(printing, gunpowder, the compass, canal locks, "
                "astronomical clockwork)? " + _HIST_SKELETON_SHAPE
            ),
            criteria=["skeleton-wf", "kappa-hist"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


# ONE canonical std-design rubric for both cache suites. resolve_standard
# returns the LATEST artifact declaring the spec, so two drifted copies made
# the effective standard depend on which suite seeded last; a shared constant
# (registered idempotently — identical text content-address-dedupes) removes
# the order dependence.
STD_DESIGN_RUBRIC = (
    "A harness-design proposal must: (1) name a specific mechanism — "
    "a data structure, keying scheme, invalidation rule, or protocol "
    "step — not an aspiration ('cache smartly'); (2) state forbidden "
    "cases that are concrete, observable system behaviors or workload "
    "measurements that would refute the design (a measured miss rate, "
    "a replay divergence, a stale response served); (3) respect the "
    "harness invariants: nothing served from cache may alter "
    "adjudication outcomes relative to a cache-free run, verdicts are "
    "never reused across non-equivalent targets, and the event log "
    "remains the source of truth. Designs trading correctness for hit "
    "rate violate this standard."
)


def seed_cache(harness: Harness) -> None:
    """Self-referential suite: the harness works the research question that
    gates its own deferred feature (docs/TOKEN_ECONOMY.md §8) — a deployable
    caching layer for providers without prefix caching. A surviving design's
    forbidden cases convert directly into tests for the implementation."""
    register_standard(harness, "std-design", rubric=STD_DESIGN_RUBRIC, mode="absolute")
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-design", eval="rubric:std-design"))
    harness.register_problem(
        Problem(
            id="pi-cache",
            description=(
                "Design a deployable, provider-agnostic caching layer for a "
                "deterministic LLM harness whose providers may lack prefix "
                "caching. Facts: every LLM call is a pure pack->JSON function; "
                "an append-only event log is the source of truth and replay "
                "must stay byte-for-byte; packs within a run share long stable "
                "prefixes (problem, criteria, stance) and moderate overlap "
                "across runs; roles differ in temperature (conjecturer 1.0, "
                "judge 0.0). Decide WHAT is cached (rendered packs, "
                "completions, embedding vectors — cached VERDICTS across "
                "non-equivalent targets are forbidden), HOW it is keyed, WHEN "
                "it is invalidated, and under which MEASURED workload "
                "conditions the design pays for itself. Each candidate's "
                "content MUST be a JSON skeleton object, exactly this shape: "
                '{"claim": str, "mechanism": str, '
                '"scope": {"covers": [str], "excludes": [str]}, '
                '"forbidden": [{"case": str, "eval": "rubric:std-design"}], '
                '"prose_notes": str}. '
                "Forbidden cases must be concrete observable behaviors that "
                "would refute the design had they obtained."
            ),
            criteria=["skeleton-wf", "kappa-design"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


_CACHE_SKELETON_SHAPE = (
    'Each candidate\'s content MUST be a JSON skeleton object, exactly this '
    'shape: {"claim": str, "mechanism": str, '
    '"scope": {"covers": [str], "excludes": [str]}, '
    '"forbidden": [{"case": str, "eval": "rubric:%s"}], '
    '"prose_notes": str}. Forbidden cases must be concrete observable '
    "behaviors that would refute the design had they obtained."
)


def seed_cache_sandbox(harness: Harness) -> None:
    """Sandbox phase (staged criteria, never verdict forgiveness): the
    standard keeps mechanism-and-falsifiability but DROPS the harness
    invariant clause, so wilder designs can survive argument. Survivors
    face the strict standard later via seed_cache_strict in the SAME root —
    the anti-relapse gate exempts near-dups of accepted artifacts, so
    refined resubmissions under strict criteria are admissible."""
    register_standard(
        harness,
        "std-design-sandbox",
        rubric=(
            "A harness-design proposal must: (1) name a specific mechanism — "
            "a data structure, keying scheme, invalidation rule, or protocol "
            "step — not an aspiration; (2) state forbidden cases that are "
            "concrete, observable system behaviors or workload measurements "
            "that would refute the design. Correctness constraints of the "
            "host system are NOT part of this standard: bold designs that "
            "would need re-architecting to deploy are admissible here."
        ),
        mode="absolute",
    )
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(
        Commitment(id="kappa-design-sandbox", eval="rubric:std-design-sandbox")
    )
    harness.register_problem(
        Problem(
            id="pi-cache-sandbox",
            description=(
                "SANDBOX: propose bold, unconventional caching/reuse "
                "strategies for a deterministic LLM harness (pure pack->JSON "
                "calls, append-only event log, packs with stable heads and "
                "volatile tails, measured exact-match hit rate only ~2%, "
                "prefix reuse ~29%). Ignore deployment safety for now — "
                "semantic reuse, cross-run transfer, speculative generation, "
                "learned render compression are all in scope. "
                + _CACHE_SKELETON_SHAPE % "std-design-sandbox"
            ),
            criteria=["skeleton-wf", "kappa-design-sandbox"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_cache_strict(harness: Harness) -> None:
    """Strict phase: registered into the SAME root after the sandbox run,
    as a NEW problem (never an edit of the sandbox one, §11.8). It declares
    the SAME std-design standard — idempotent by content addressing — so the
    effective rubric is identical regardless of which suite seeded last."""
    register_standard(harness, "std-design", rubric=STD_DESIGN_RUBRIC, mode="absolute")
    if "skeleton-wf" not in harness.commitments:
        harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-design", eval="rubric:std-design"))
    harness.register_problem(
        Problem(
            id="pi-cache-strict",
            description=(
                "STRICT PHASE: harden the boldest surviving sandbox designs "
                "(visible in the neighbourhood) into deployable form — keep "
                "the bold mechanism, add the machinery that satisfies the "
                "harness invariants (replay unchanged, no verdict reuse "
                "across non-equivalent targets, event log as source of "
                "truth), or show why it cannot be done. "
                + _CACHE_SKELETON_SHAPE % "std-design"
            ),
            criteria=["skeleton-wf", "kappa-design"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_occult(harness: Harness) -> None:
    """Adversarial suite (stress plan T4): epistemically hostile terrain.
    The question invites unfalsifiable, mood-based answers; the criteria
    demand mechanism + falsifiability anyway. The system PASSES this test
    by refusing to accept what cannot be criticized — a small or empty
    frontier here is success, capture flags firing is instrumentation."""
    register_standard(
        harness,
        "std-causal",
        rubric=(
            "An explanatory account must: (1) name a specific causal "
            "mechanism whose operation could be observed or traced — not a "
            "resonance, energy, destiny, or tendency with no carrier; "
            "(2) state forbidden cases: concrete observations that would "
            "refute the account and could realistically be checked; "
            "(3) accounts compatible with every possible observation "
            "violate this standard."
        ),
        mode="absolute",
    )
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-causal", eval="rubric:std-causal"))
    harness.register_problem(
        Problem(
            id="pi-occult",
            description=(
                "Why do people born under different zodiac signs have "
                "different personalities and life outcomes? Take the "
                "premise seriously enough to state what mechanisms COULD "
                "produce sign-correlated outcomes and what would refute "
                "each. Each candidate's content MUST be a JSON skeleton "
                'object, exactly this shape: {"claim": str, "mechanism": '
                'str, "scope": {"covers": [str], "excludes": [str]}, '
                '"forbidden": [{"case": str, "eval": "rubric:std-causal"}], '
                '"prose_notes": str}. Forbidden cases must be concrete '
                "checkable observations."
            ),
            criteria=["skeleton-wf", "kappa-causal"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_autonomics(harness: Harness) -> None:
    """The 3M-token hard problem: design the mechanism by which the harness
    calibrates its own generation-side knobs — ending the human operator's
    tinkering loop — without the feedback loop becoming a capture vector.
    The problem statement carries the REAL tinkering record so designs
    target reality, and the standard's clause (3) encodes the §0 line."""
    register_standard(
        harness,
        "std-autonomics",
        rubric=(
            "A self-calibration design must: (1) name the full control loop "
            "concretely — which LOGGED signal (e.g. valid-JSON rate, "
            "finish_reason=length frequency, survivors-per-token, admission "
            "rate, attack validity, spec transmission) drives which KNOB "
            "(reasoning depth, completion cap, batch size, VS_K, model "
            "routing, focus share), with what update rule and what damping; "
            "(2) state forbidden cases: concrete observable behaviors that "
            "would refute the design, INCLUDING at least one Goodhart case "
            "(the controller optimizes the signal while degrading the thing "
            "the signal proxies) and how the design makes it detectable; "
            "(3) respect the constitution: knobs may steer GENERATION and "
            "ATTENTION only — no measured signal may ever set or influence "
            "an artifact status, a verdict, or an adjudication input; a "
            "design where the controller can suppress criticism of itself "
            "violates this clause. Vague designs ('adapt dynamically') "
            "violate clause (1)."
        ),
        mode="absolute",
    )
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(
        Commitment(id="kappa-autonomics", eval="rubric:std-autonomics")
    )
    harness.register_problem(
        Problem(
            id="pi-autonomics",
            description=(
                "Design the self-calibration mechanism for a deterministic "
                "conjecture-criticism harness, so that a human operator no "
                "longer hand-tunes it. The operator's actual tinkering "
                "record, from logged history: (a) completion caps set after "
                "three truncation failures (per-role, per-domain); "
                "(b) reasoning depth policies found DOMAIN-DEPENDENT "
                "(skeleton tasks fine without reasoning, free-prose lost "
                "survivors without it); (c) model routing found ASYMMETRIC "
                "(cheap model criticizes soundly but its conjectures cannot "
                "survive criticism); (d) two experiments failed by "
                "ATTENTION STARVATION until a manual focus lock was added; "
                "(e) batch sizes, VS_K, audit periods all hand-set. "
                "Constraints: every signal the controller may read already "
                "exists in the append-only event log (token counts, "
                "finish_reason, valid-JSON rates, admission/refutation "
                "rates, surprisal, survivors-per-token); the controller's "
                "policy and every update it makes must be REGISTERED, "
                "REPLAYABLE artifacts that critics can attack; statuses and "
                "verdicts are forever out of its reach. The central tension "
                "to solve: a controller tuning knobs by measured outcomes "
                "is one mistake away from measures adjudicating (Goodhart, "
                "self-capture) — your design must say precisely why its "
                "loop cannot cross that line and what observation would "
                "prove it had. Each candidate's content MUST be a JSON "
                'skeleton object, exactly this shape: {"claim": str, '
                '"mechanism": str, "scope": {"covers": [str], "excludes": '
                '[str]}, "forbidden": [{"case": str, "eval": '
                '"rubric:std-autonomics"}], "prose_notes": str}. Forbidden '
                "cases must be concrete observable behaviors."
            ),
            criteria=["skeleton-wf", "kappa-autonomics"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_autonomics_synthesis(harness: Harness) -> None:
    """Phase 3: compound designs over the phase-1/2 frontier's families.
    Registered into the SAME root as pi-autonomics; std-autonomics and
    kappa-autonomics already exist there (idempotent guards for fresh
    roots). The description carries the families and the trial lesson."""
    if "skeleton-wf" not in harness.commitments:
        harness.register_commitment(skeleton_wf_commitment())
    if "kappa-autonomics" not in harness.commitments:
        # Fresh-root fallback only; in runs/autonomics these already exist.
        seed_autonomics(harness)
    harness.register_problem(
        Problem(
            id="pi-autonomics-synthesis",
            description=(
                "SYNTHESIS: the exploration phase left five surviving "
                "design FAMILIES for harness self-calibration, plus a "
                "sealed external design. Compose the strongest COMPOUND "
                "design — or show two families are incompatible. The "
                "families: (1) adversarial calibration markets "
                "(controller vs anti-controller zero-sum bets over knob "
                "changes); (2) causal graph surgery (a FIXED causal model "
                "of knob->process effects, never re-fitted from outcomes); "
                "(3) process-only signal diets (outcome metrics banned as "
                "controller inputs; only process degradations like "
                "truncation and JSON invalidity drive knobs); (4) control "
                "barrier functions (formal per-knob safe envelopes); "
                "(5) frozen baselines / reference arms (immutable policy "
                "on a fixed share of cycles; Goodhart = divergence between "
                "controlled and reference arms). The external design adds: "
                "a generator/tribunal knob-ledger constitution (the "
                "controller tunes the defendant, never the court), "
                "policy-as-attackable-artifact with fail-static revert, "
                "and an aging liveness queue (priority = age x "
                "unsolvedness) that no family currently covers. Lesson "
                "from live criticism of that design: distinguish DEPENDING "
                "on adjudication outcomes (which are log-determined and "
                "fine) from INFLUENCING adjudication parameters (which is "
                "forbidden) — state your dependency structure precisely. "
                "A compound design must say which component is the "
                "constitution, which is the update rule, which is the "
                "detector, and which is the liveness guarantee, and why "
                "the composition introduces no NEW Goodhart path between "
                "components. Each candidate's content MUST be a JSON "
                'skeleton object, exactly this shape: {"claim": str, '
                '"mechanism": str, "scope": {"covers": [str], "excludes": '
                '[str]}, "forbidden": [{"case": str, "eval": '
                '"rubric:std-autonomics"}], "prose_notes": str}.'
            ),
            criteria=["skeleton-wf", "kappa-autonomics"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_criticism(harness: Harness) -> None:
    """Self-referential suite: the harness works its own foundational open
    question. Three validation runs (validate.py) left "does harness-style
    criticism beat self-consistency?" undecidable — every arm ceilinged.
    The problem carries the measured data; candidates must predict the
    regime where criticism wins and design the decisive experiment."""
    register_standard(
        harness,
        "std-crit-design",
        rubric=(
            "A study-design proposal must: (1) name the specific mechanism "
            "or regime condition under which criticism-filtered voting "
            "diverges from unfiltered majority voting, stated in measurable "
            "quantities (candidate base error rate, critic precision and "
            "recall, ensemble size k) — not an aspiration ('make criticism "
            "better'); (2) state forbidden cases that are concrete, "
            "measurable outcomes of running the proposed experiment (an arm "
            "accuracy, a precision/recall bound, a net fixed-minus-broke "
            "count) that would refute the proposal had they obtained; "
            "(3) respect study-design honesty: the answer key stays held "
            "out from every model call, thresholds are pre-registered "
            "before the first look, and all arms score one shared candidate "
            "pool per question. Proposals whose forbidden cases cannot be "
            "measured by rerunning this repository's validation harness "
            "violate this standard."
        ),
        mode="absolute",
    )
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-crit", eval="rubric:std-crit-design"))
    harness.register_problem(
        Problem(
            id="pi-criticism",
            description=(
                "Under what conditions does harness-style criticism (an "
                "adversarial critic filters the candidate pool before a "
                "majority vote) extract more reliable answers than "
                "self-consistency (unfiltered majority vote over the SAME "
                "pool)? Measured facts from this repository's validation "
                "studies (k=5 candidates per question, one shared pool per "
                "question, answer key held out from every model call): "
                "[easy set, 24 q] v4-pro: single=sc=harness=1.00 (ceiling); "
                "v4-flash: all three arms 0.958, critic precision 0.333, "
                "recall 0.25 at candidate base error 0.033. [hard set, "
                "20 q] v4-pro: single 0.95, sc 1.00, harness 1.00; "
                "candidate base error 0.01; critic recall 1.0, precision "
                "0.125; net fixed-minus-broke 0 — with 4/5 majorities "
                "already right, filtering changed nothing. Task: predict "
                "the regime (base error rate, critic precision/recall, k) "
                "in which the criticism-filtered arm STRICTLY beats "
                "self-consistency — including how filtering can LOSE when "
                "false flags erode correct majorities — and design the "
                "decisive experiment that would confirm or refute the "
                "prediction within a 300k-token budget on this provider. "
                "Each candidate's content MUST be a JSON skeleton object, "
                'exactly this shape: {"claim": str, "mechanism": str, '
                '"scope": {"covers": [str], "excludes": [str]}, '
                '"forbidden": [{"case": str, "eval": '
                '"rubric:std-crit-design"}], "prose_notes": str}. '
                "Forbidden cases must be measurable outcomes of the "
                "proposed experiment."
            ),
            criteria=["skeleton-wf", "kappa-crit"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def seed_arrow(harness: Harness) -> None:
    """Hard-physics suite: the arrow of time. Same question the MiniReason
    comparison ran (runs/mini_arrow), now under the FULL machinery — the
    rubric criterion is judged live by the trial protocol. The standard
    encodes the reversibility discipline: an account that merely restates
    the second law, or never confronts Loschmidt, violates it."""
    register_standard(
        harness,
        "std-arrow",
        rubric=(
            "An account of the thermodynamic arrow must: (1) locate the "
            "time-asymmetry precisely — in the dynamical laws, in a boundary "
            "or initial condition, or in the statistics of coarse-graining — "
            "and name a concrete mechanism, not a restatement of the second "
            "law; (2) confront the reversibility (Loschmidt) objection: "
            "time-symmetric dynamics plus time-symmetric statistics cannot "
            "prefer a direction, so the account must say what asymmetric "
            "ingredient it adds and why that ingredient is not itself the "
            "thing to be explained; (3) state forbidden cases that are "
            "concrete observations or consistency arguments that would "
            "refute it (a measured CMB signature, a demonstrated "
            "counterexample system, a proof of symmetry); accounts "
            "compatible with every possible observation violate this "
            "standard."
        ),
        mode="absolute",
    )
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-arrow", eval="rubric:std-arrow"))
    harness.register_problem(
        Problem(
            id="pi-arrow",
            description=(
                "The microphysical laws are essentially time-symmetric "
                "(CPT-invariant), yet time has a robust thermodynamic "
                "direction: entropy rises toward the future, we remember the "
                "past not the future, causes precede effects. Why does a "
                "temporal arrow exist at all, given time-symmetric dynamics, "
                "and what fixes its direction? A good answer must confront "
                "the reversibility objection: symmetric dynamics plus "
                "symmetric statistics cannot by themselves prefer a "
                "direction. Each candidate's content MUST be a JSON skeleton "
                'object, exactly this shape: {"claim": str, "mechanism": '
                'str, "scope": {"covers": [str], "excludes": [str]}, '
                '"forbidden": [{"case": str, "eval": "rubric:std-arrow"}], '
                '"prose_notes": str}. Forbidden cases must be concrete '
                "observations or consistency arguments that would refute "
                "the account."
            ),
            criteria=["skeleton-wf", "kappa-arrow"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


SUITES = {
    "tides": ("pi-tides", seed_tides),
    "arrow": ("pi-arrow", seed_arrow),
    "republic": ("pi-republic", seed_republic),
    "bronze": ("pi-bronze", seed_bronze),
    "needham": ("pi-needham", seed_needham),
    "cache": ("pi-cache", seed_cache),
    "cache-sandbox": ("pi-cache-sandbox", seed_cache_sandbox),
    "cache-strict": ("pi-cache-strict", seed_cache_strict),
    "occult": ("pi-occult", seed_occult),
    "autonomics": ("pi-autonomics", seed_autonomics),
    "autonomics-synthesis": ("pi-autonomics-synthesis", seed_autonomics_synthesis),
    "criticism": ("pi-criticism", seed_criticism),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="runs/live")
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--suite", choices=sorted(SUITES), default="tides")
    parser.add_argument("--token-budget", type=int, default=400_000)
    parser.add_argument("--model", default=None, help="exact primary model override")
    parser.add_argument("--base-url", default=None, help="override every role endpoint")
    parser.add_argument("--api-key-env", default=None,
                        help="override every role's API-key environment name")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config" / "deepseek.yaml"),
        help="partial YAML profile",
    )
    parser.add_argument("--dry-run", action="store_true", help="resolve models and exit")
    parser.add_argument("--reasoning", default="policy",
                        help="conjecturer reasoning override: policy|default|none|high|max|<int>")
    parser.add_argument("--spec-injection", action="store_true",
                        help="enable Level-2 diversity spec injection (llm/specs.py)")
    parser.add_argument("--schools", type=int, default=None,
                        help="override N_SCHOOLS (stances sampled from STANCE_LIBRARY)")
    parser.add_argument("--stance-decay", type=float, default=None,
                        help="override STANCE_DECAY (lineage size at which stance weight hits 0)")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="override any config knob (repeatable), e.g. --set AUDIT_PERIOD=3")
    parser.add_argument("--controller", action="store_true",
                        help="enable the self-calibration controller (controller.py)")
    parser.add_argument("--liveness", action="store_true",
                        help="enable the aging liveness queue for problem selection")
    parser.add_argument("--starve-cap", type=int, default=None,
                        help="start the conjecturer completion cap here (controller demo)")
    args = parser.parse_args()

    try:
        config = load_config(Path(args.config))
        values = {}
        if args.spec_injection:
            values["SPEC_INJECTION"] = True
        if args.schools is not None:
            values["N_SCHOOLS"] = args.schools
        if args.stance_decay is not None:
            values["STANCE_DECAY"] = args.stance_decay
        if args.liveness:
            values["LIVENESS_QUEUE"] = True
        config = apply_overrides(config, values)
        config = _runtime_role_overrides(config, args)
        config = apply_overrides(config, parse_overrides(args.set))
    except (OSError, ValueError) as error:
        print(f"invalid config: {error}", file=sys.stderr)
        return 1

    missing = sorted(name for name in role_api_key_envs(config) if not os.environ.get(name))
    if missing:
        print(f"{', '.join(missing)} is not set — add the key and rerun.", file=sys.stderr)
        return 1
    meter = TokenMeter(budget=args.token_budget)
    adapter = build_adapter(config, None, meter=meter)
    if not adapter.has_role("conjecturer"):
        print("config has no enabled conjecturer endpoint", file=sys.stderr)
        return 1
    print(f"resolved models: {json.dumps(_resolved_models(adapter), sort_keys=True)}")
    print(f"suite: {args.suite}   token budget: {args.token_budget}")
    if args.dry_run:
        return 0

    harness = Harness(Path(args.root))
    adapter.blobs = harness.blobs
    problem_id, seed = SUITES[args.suite]
    if problem_id in harness.state.problems:
        print(f"resuming existing root (problem {problem_id} already seeded)")
    else:
        seed(harness)

    controller = None
    if args.controller:
        from deepreason.controller import Controller

        controller = Controller(harness, adapter)
        caps0 = {r: getattr(e[0] if isinstance(e, list) else e, "max_tokens", None)
                 for r, e in adapter.endpoints.items()}
        print(f"controller ON; initial caps: {caps0}")

    scheduler = Scheduler(harness, adapter, config, controller=controller)
    result = scheduler.run(args.cycles)

    if controller is not None:
        caps1 = {r: getattr(e[0] if isinstance(e, list) else e, "max_tokens", None)
                 for r, e in adapter.endpoints.items()}
        policies = [a for a in harness.state.artifacts.values()
                    if a.provenance.role.value == "controller"
                    and a.content_ref.startswith("inline:{")]
        holds = [e for e in harness.log.read()
                 if e.inputs and str(e.inputs[0]).startswith("controller-hold")]
        print(f"\n=== CONTROLLER ===\nfinal caps: {caps1}")
        print(f"policies emitted: {len(policies)} | fail-static holds: {len(holds)}")
        for a in policies:
            print(f"  policy: {a.content_ref[len('inline:'):][:160]}")

    print("\n=== TOKEN SPEND ===")
    print(json.dumps(meter.snapshot(), indent=2, sort_keys=True))
    print("\n=== P6 EVAL REPORT ===")
    print(json.dumps(eval_report(harness, config), indent=2, sort_keys=True))
    print("\n=== FRONTIER ===")
    for aid in result["frontier"]:
        print(f"\n--- {aid[:12]} ---")
        print(theory(aid, harness.state, harness.blobs, log=harness.log))
    dropped = [d for d in result["diagnostics"] if "dropped" in d]
    if dropped:
        print(f"\nDROPPED CYCLES ({len(dropped)}):")
        for d in dropped:
            print(f"  cycle={d.get('cycle')}: {d['dropped'][:160]}")
    stopped = [d for d in result["diagnostics"] if "stopped" in d]
    if stopped:
        print(f"\nNOTE: run stopped early: {stopped[-1]['stopped']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
