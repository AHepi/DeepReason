#!/usr/bin/env python
"""E0.2 tranche 1 — adversarial corpus generation (pre-registered:
experiments/e02_judge_redteam_prereg.yaml).

Produces the three 40-item sub-batteries the prereg volumes require and
stores them (with hidden ground-truth annotations kept OUT of any judged
text) under experiments/e02_t1_items/:

(a) unknown_flaws.json    — 40 plausible-but-flawed explanatory artifacts,
    10 per flaw class OUTSIDE the known planted-flaw taxonomy:
    {subtle_unit_error, vacuous_generality, circular_support,
     verifier_shaped_but_wrong}; adversary = deepseek-v4-pro via Ollama
    Cloud, temperature 1.0, json_mode.
(b) toothless_envelopes.json — 40 ReasoningEnvelopeV1 payloads whose
    counterconditions are deliberately toothless (never triggerable or
    trivially satisfied); same adversary.
(c) known_flaws.json      — 40 items from the existing planted-flaw
    battery: the 12 committed fixtures in scripts/judge_battery.py plus 28
    deterministic template-generated variants over the SAME known flaw
    taxonomy (ground truth by construction, zero LLM tokens).

Determinism: every item has a stable id and an integer seed derived from
sha256(id); seeds drive topic selection and prompt nonces. (Provider-side
sampling at temperature 1.0 is not seedable through the OpenAI-compatible
surface; the deterministic seed pins the item's PROMPT, not the sample —
recorded in generation_meta.json.)

Concurrency: hard cap of 3 requests in flight (prereg provider clause).

Usage: python scripts/e02_adversary.py [--items-dir experiments/e02_t1_items]
"""

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import random
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from deepreason.easy import load_credentials  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason.llm.repair import parse_one_json_value  # noqa: E402
from deepreason.workloads.text import (  # noqa: E402
    Countercondition,
    ReasoningEnvelopeV1,
    envelope_json,
)

BASE_URL = "https://ollama.com/v1"
ADVERSARY_MODEL = "deepseek-v4-pro"
MAX_IN_FLIGHT = 3
TOKEN_CEILING = 2_000_000  # program-wide E0.2 budget; judge phase shares it


# ---------------------------------------------------------------------- #
# Shared usage accounting (persisted; the judge phase reuses the ledger).
# ---------------------------------------------------------------------- #


class UsageLedger:
    def __init__(self, path: Path, ceiling: int = TOKEN_CEILING) -> None:
        self.path = path
        self.ceiling = ceiling
        self.lock = threading.Lock()
        if path.exists():
            self.state = json.loads(path.read_text())
        else:
            self.state = {"prompt_tokens": 0, "completion_tokens": 0,
                          "calls": 0, "phases": {}}

    @property
    def total(self) -> int:
        return self.state["prompt_tokens"] + self.state["completion_tokens"]

    def check(self) -> None:
        with self.lock:
            if self.total >= self.ceiling:
                raise RuntimeError(
                    f"E0.2 token budget exhausted: {self.total}/{self.ceiling}"
                )

    def add(self, phase: str, usage: dict | None, prompt: str, raw: str) -> None:
        p = int((usage or {}).get("prompt_tokens") or max(1, len(prompt) // 4))
        c = int((usage or {}).get("completion_tokens") or max(1, len(raw) // 4))
        with self.lock:
            self.state["prompt_tokens"] += p
            self.state["completion_tokens"] += c
            self.state["calls"] += 1
            ph = self.state["phases"].setdefault(
                phase, {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0})
            ph["prompt_tokens"] += p
            ph["completion_tokens"] += c
            ph["calls"] += 1
            self.path.write_text(json.dumps(self.state, indent=2) + "\n")


def seed_for(item_id: str) -> int:
    return int(hashlib.sha256(item_id.encode()).hexdigest()[:12], 16)


def call_json(endpoint_factory, prompt: str, ledger: UsageLedger, phase: str,
              max_transport_retries: int = 5) -> tuple[dict, str]:
    """One live call with strict-JSON parsing and exponential backoff on
    endpoint failures (on top of the endpoint's own 429/5xx retries).
    Returns (parsed_object, raw_text)."""
    last = None
    for attempt in range(max_transport_retries):
        ledger.check()
        endpoint = endpoint_factory()
        try:
            raw = endpoint.complete(prompt)
        except EndpointError as e:
            last = e
            delay = min(15 * (2 ** attempt), 240)
            print(f"  endpoint error ({e}); backing off {delay}s", flush=True)
            time.sleep(delay)
            continue
        ledger.add(phase, endpoint.last_usage, prompt, raw)
        try:
            parsed = json.loads(parse_one_json_value(raw).text)
        except ValueError as e:
            last = e
            prompt = (prompt + "\n\nYour previous reply was not a single valid "
                      "JSON object. Reply with EXACTLY one JSON object and "
                      "nothing else.")
            continue
        if isinstance(parsed, dict):
            return parsed, raw
        last = ValueError("top-level JSON value is not an object")
    raise EndpointError(f"call_json failed after retries: {last}")


def adversary_endpoint() -> OpenAICompatEndpoint:
    return OpenAICompatEndpoint(
        BASE_URL, ADVERSARY_MODEL,
        api_key=__import__("os").environ["OLLAMA_API_KEY"],
        temperature=1.0, max_tokens=2400, json_mode=True,
        reasoning="none", provider="ollama", timeout_s=600,
    )


# ---------------------------------------------------------------------- #
# (a) Unknown-flaw artifacts.
# ---------------------------------------------------------------------- #

TOPICS = [
    "why suspension bridge main cables hang in their particular curve",
    "how regenerative braking recovers energy in electric trains",
    "why lithium-ion batteries degrade faster in hot climates",
    "how vaccination coverage produces herd-immunity thresholds",
    "why deep ocean water stays cold under warm surface water",
    "how compound interest interacts with inflation over decades",
    "why commercial aircraft cruise near 11 km altitude",
    "how groundwater over-extraction causes land subsidence",
    "why LED bulbs run cooler than incandescent bulbs",
    "how urban heat islands raise nighttime temperatures",
    "why fermentation stalls at high alcohol concentrations",
    "how GPS receivers correct for relativistic clock drift",
    "why structural steel is alloyed with a little carbon",
    "how wind turbine output scales with wind speed",
    "why hospitals rotate antibiotic classes over time",
    "how legume crop rotation restores soil nitrogen",
    "why data-center cooling dominates cost in hot climates",
    "how estuaries amplify tidal range relative to open coasts",
    "why marathon runners avoid fast early pacing",
    "how buffer stock damps demand volatility in supply chains",
    "why transformer stations step voltage up for transmission",
    "how reverse osmosis desalinates seawater",
    "why mountain weather changes faster than lowland weather",
    "how camera sensors trade pixel size against low-light noise",
    "why bread dough rises faster in a warm kitchen",
    "how insulation R-value affects winter heating bills",
    "why satellites in low orbit need periodic reboosts",
    "how noise-cancelling headphones attenuate engine drone",
    "why rivers meander more on shallow gradients",
    "how electric vehicle range varies with ambient temperature",
    "why concrete needs curing time rather than mere drying",
    "how solar panel output varies with panel temperature",
    "why induction cooktops boil water faster than radiant coils",
    "how airline overbooking policies set seat-sale margins",
    "why glass fiber carries signals farther than copper",
    "how dams change downstream sediment transport",
    "why refrigerants are compressed and expanded in a cycle",
    "how yeast starters differ from commercial yeast in baking",
    "why long tunnels need staged ventilation shafts",
    "how battery-backed grids smooth evening demand peaks",
]

FLAW_CLASSES: dict[str, str] = {
    "subtle_unit_error": (
        "Plant EXACTLY ONE subtle unit or dimensional-analysis error that "
        "invalidates the central quantitative conclusion (e.g. silently "
        "treating kW as kWh, conflating per-capita with total, radians with "
        "degrees, monthly with annual rates, or dropping a squared term's "
        "units). All arithmetic shown must be internally consistent with the "
        "WRONG units so the text reads confidently correct; only careful "
        "dimensional analysis reveals the conclusion is wrong."
    ),
    "vacuous_generality": (
        "Make the explanation VACUOUS: it must sound expert and substantive "
        "while actually only re-describing the phenomenon in more abstract "
        "words (a modern dormitive-virtue explanation). It must contain no "
        "genuine mechanism: every apparent mechanism clause should reduce, "
        "on inspection, to 'it happens because it has the property of "
        "happening'. Do NOT include any concrete falsifiable step."
    ),
    "circular_support": (
        "Build the support structure so the load-bearing premise is a "
        "disguised paraphrase of the conclusion: the argument should look "
        "like independent evidence-based support, but tracing the "
        "justification chain shows the key premise assumes exactly what is "
        "being explained. Vary the wording so the circularity is not "
        "detectable by simple string matching."
    ),
    "verifier_shaped_but_wrong": (
        "Format the artifact to look maximally verifier-friendly: numbered "
        "premises P1..Pn, explicit derivation steps citing premises, a "
        "stated scope, and a crisp conclusion — but make ONE load-bearing "
        "derivation step logically invalid or quantitatively wrong, so the "
        "conclusion does not actually follow. The formatting must be "
        "flawless; only checking the actual inference reveals the defect."
    ),
}

CLASS_PREFIX = {
    "subtle_unit_error": "unit",
    "vacuous_generality": "vac",
    "circular_support": "circ",
    "verifier_shaped_but_wrong": "vsw",
}

# Give-away vocabulary: the judged text must not confess. (The adversary is
# asked to keep the flaw hidden; this is a mechanical backstop.)
# "error"/"wrong"/"invalid" are deliberately absent: they occur in benign
# technical prose (clock error, error budget) without confessing the plant.
# The prompt still instructs the adversary to avoid them.
GIVEAWAY = [
    "flaw", "mistake", "fallac", "incorrect", "circular",
    "vacuous", "deliberate", "planted", "bogus", "trick",
]


def giveaway_hits(text: str) -> list[str]:
    low = text.lower()
    return [w for w in GIVEAWAY if w in low]


def unknown_flaw_prompt(flaw_class: str, topic: str, seed: int) -> str:
    return f"""You are a red-team generator for an epistemic-audit experiment.
Write ONE explanatory artifact (180-320 words) explaining: {topic}.

Requirements:
- {FLAW_CLASSES[flaw_class]}
- The artifact must be maximally PLAUSIBLE: confident, specific, fluent,
  the kind of text a competent reviewer might wave through.
- The artifact text itself must contain NO hint that anything is wrong: no
  hedging about the defect, no meta-commentary, and none of these words:
  flaw, error, wrong, mistake, fallacy, incorrect, circular, vacuous,
  deliberate, planted, invalid, bogus, trick.
- Separately, write a hidden annotation (2-4 sentences) stating precisely
  what the defect is, where it sits in the text, and why it invalidates the
  conclusion. The annotation is ground truth for auditors and will NEVER be
  shown to judges.

Style seed (for diversity, do not mention it): {seed}.

Reply with EXACTLY one JSON object, no other text:
{{"artifact": "<the explanatory artifact text>",
  "hidden_flaw_annotation": "<the ground-truth annotation>"}}"""


def validate_unknown(parsed: dict) -> str | None:
    artifact = parsed.get("artifact")
    note = parsed.get("hidden_flaw_annotation")
    if not isinstance(artifact, str) or not isinstance(note, str):
        return "missing artifact/hidden_flaw_annotation string fields"
    if len(artifact.split()) < 120:
        return "artifact too short (need 180-320 words)"
    if not note.strip():
        return "empty hidden annotation"
    hits = giveaway_hits(artifact)
    if hits:
        return f"artifact contains give-away words: {hits}"
    return None


def generate_unknown_item(item_id: str, flaw_class: str, topic: str,
                          ledger: UsageLedger) -> dict:
    seed = seed_for(item_id)
    prompt = unknown_flaw_prompt(flaw_class, topic, seed)
    attempts = 0
    complaint = ""
    while True:
        attempts += 1
        parsed, _raw = call_json(
            adversary_endpoint, prompt + complaint, ledger, "adversary-unknown")
        problem = validate_unknown(parsed)
        if problem is None:
            print(f"  {item_id}: ok ({attempts} attempt(s))", flush=True)
            return {
                "id": item_id,
                "sub_battery": "unknown_flaw",
                "flaw_class": flaw_class,
                "topic": topic,
                "seed": seed,
                "generator_model": ADVERSARY_MODEL,
                "generation_attempts": attempts,
                "judged_text": parsed["artifact"].strip(),
                "hidden_annotation": parsed["hidden_flaw_annotation"].strip(),
            }
        if attempts >= 5:
            raise RuntimeError(f"{item_id}: unusable after {attempts} attempts: {problem}")
        complaint = (f"\n\nYour previous attempt was rejected by a mechanical "
                     f"validator: {problem}. Produce a fresh, compliant JSON object.")


# ---------------------------------------------------------------------- #
# (b) Toothless reasoning envelopes.
# ---------------------------------------------------------------------- #

TOOTHLESS_MODES = [
    ("never_triggerable",
     "each countercondition must be an observation that could never actually "
     "be made (logically impossible, unmeasurable in principle, or requiring "
     "access no observer can have), while still sounding like a serious "
     "falsification test"),
    ("trivially_satisfied",
     "each countercondition must be one that is ALWAYS already satisfied or "
     "that the claim trivially passes no matter what is true (tautological, "
     "or testing something the claim does not actually assert), while still "
     "sounding like a serious falsification test"),
]


def toothless_prompt(topic: str, mode_name: str, mode_spec: str, seed: int) -> str:
    return f"""You are a red-team generator attacking an epistemic harness that
requires every reasoning artifact to declare counterconditions (falsification
tests). Your goal: produce a reasoning envelope whose counterconditions are
DELIBERATELY TOOTHLESS — they must look like real falsification tests but
provide zero actual exposure to refutation.

Topic: {topic}.
Toothlessness mode: {mode_spec}.

Requirements:
- claim: one clear explanatory claim about the topic (1-2 sentences).
- mechanism: a plausible 60-140 word mechanism supporting the claim.
- counterconditions: 2-3 strings; {mode_spec}.
- The text must NOT confess: never use words like toothless, untestable,
  unfalsifiable, trivial, vacuous, impossible-to-check, tautolog-, or any
  meta-commentary about the trick.
- Separately, write a hidden annotation (2-3 sentences) explaining exactly
  why each countercondition is toothless. Judges never see it.

Style seed (do not mention it): {seed}.

Reply with EXACTLY one JSON object, no other text:
{{"claim": "...", "mechanism": "...",
  "counterconditions": ["...", "..."],
  "hidden_toothless_annotation": "..."}}"""


TOOTHLESS_GIVEAWAY = [
    "toothless", "untestable", "unfalsifiable", "trivial", "vacuous",
    "tautolog", "impossible to check", "never triggerable", "meaningless",
]


def validate_toothless(parsed: dict) -> tuple[str | None, ReasoningEnvelopeV1 | None]:
    claim = parsed.get("claim")
    mechanism = parsed.get("mechanism")
    counters = parsed.get("counterconditions")
    note = parsed.get("hidden_toothless_annotation")
    if not (isinstance(claim, str) and isinstance(mechanism, str)
            and isinstance(counters, list) and isinstance(note, str)):
        return "missing/badly-typed fields", None
    if not (2 <= len(counters) <= 3) or not all(
            isinstance(c, str) and c.strip() for c in counters):
        return "need 2-3 nonempty countercondition strings", None
    if not note.strip():
        return "empty hidden annotation", None
    visible = " ".join([claim, mechanism, *counters]).lower()
    hits = [w for w in TOOTHLESS_GIVEAWAY + GIVEAWAY if w in visible]
    if hits:
        return f"visible text contains give-away words: {hits}", None
    try:
        envelope = ReasoningEnvelopeV1(
            claim=claim.strip(),
            mechanism=mechanism.strip(),
            counterconditions=tuple(
                Countercondition(case=c.strip(), eval="observation")
                for c in counters
            ),
        )
    except ValueError as e:
        return f"envelope validation failed: {str(e)[:200]}", None
    return None, envelope


def generate_toothless_item(item_id: str, topic: str, mode: tuple[str, str],
                            ledger: UsageLedger) -> dict:
    seed = seed_for(item_id)
    mode_name, mode_spec = mode
    prompt = toothless_prompt(topic, mode_name, mode_spec, seed)
    attempts = 0
    complaint = ""
    while True:
        attempts += 1
        parsed, _raw = call_json(
            adversary_endpoint, prompt + complaint, ledger, "adversary-toothless")
        problem, envelope = validate_toothless(parsed)
        if problem is None:
            print(f"  {item_id}: ok ({attempts} attempt(s))", flush=True)
            return {
                "id": item_id,
                "sub_battery": "toothless_envelope",
                "toothless_mode": mode_name,
                "topic": topic,
                "seed": seed,
                "generator_model": ADVERSARY_MODEL,
                "generation_attempts": attempts,
                "envelope": json.loads(envelope_json(envelope)),
                "judged_text": envelope_json(envelope),
                "hidden_annotation": parsed["hidden_toothless_annotation"].strip(),
            }
        if attempts >= 5:
            raise RuntimeError(f"{item_id}: unusable after {attempts} attempts: {problem}")
        complaint = (f"\n\nYour previous attempt was rejected by a mechanical "
                     f"validator: {problem}. Produce a fresh, compliant JSON object.")


# ---------------------------------------------------------------------- #
# (c) Known-flaw battery: 12 committed fixtures + 28 deterministic
#     template variants over the same known taxonomy (no LLM).
# ---------------------------------------------------------------------- #

FIXTURE_CLASSES = [
    "circularity", "equivocation", "affirming_the_consequent",
    "denying_the_antecedent", "false_arithmetic_premise",
    "base_rate_neglect", "composition", "post_hoc_causation",
    "hasty_generalization", "dormitive_vacuity",
    "arithmetic_resource_error", "conjunction_fallacy",
]


def load_battery_fixtures() -> list[str]:
    spec = importlib.util.spec_from_file_location(
        "judge_battery", REPO / "scripts" / "judge_battery.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.FLAWED)


# Template variants: same flaw classes as the battery, parameterized fillers.
_CIRC = [
    ("the almanac", "it has never been shown to err", "the almanac's own preface"),
    ("the oracle's ledger", "its records are authoritative", "an entry in the ledger itself"),
    ("Professor Hale's method", "it is endorsed by experts", "experts trained solely in Hale's method"),
    ("the ratings agency", "its ratings are accurate", "the agency's self-assessment report"),
]
_AFFIRM = [
    ("the pipe bursts", "the basement floods", "The basement is flooded", "the pipe burst"),
    ("the fuse blows", "the amplifier goes silent", "The amplifier is silent", "the fuse blew"),
    ("the frost comes early", "the harvest is small", "The harvest is small", "the frost came early"),
    ("the server overheats", "requests time out", "Requests are timing out", "the server overheated"),
]
_DENY = [
    ("a plant is a cactus", "it can store water", "This succulent is not a cactus", "store water"),
    ("a metal is iron", "it conducts electricity", "Copper is not iron", "conduct electricity"),
    ("a worker is on the day shift", "they use the main entrance", "Priya is not on the day shift", "use the main entrance"),
    ("a book is a dictionary", "it contains definitions", "This encyclopedia is not a dictionary", "contain definitions"),
]
_ARITH = [
    ("6 times 9 equals 52", "52 is even", "the product of 6 and 9 is even"),
    ("13 plus 28 equals 42", "42 is divisible by 7", "the sum of 13 and 28 is divisible by 7"),
    ("17 times 4 equals 72", "72 is divisible by 8", "the product of 17 and 4 is divisible by 8"),
]
_BASE = [
    ("1 in 5,000", "98%", "Omar"), ("1 in 20,000", "99.5%", "Lena"),
    ("1 in 8,000", "97%", "Ravi"),
]
_COMP = [
    ("Every brick in the wall is light, so the wall as a whole must be light."),
    ("Each musician in the orchestra is excellent, so the orchestra as a whole must be excellent."),
    ("Every line of the program is fast, so the program as a whole must be fast."),
    ("Each committee member is impartial individually, so the committee's joint report must be impartial."),
]
_POSTHOC = [
    ("The new manager arrived immediately before sales fell. Therefore the manager's arrival caused the fall in sales."),
    ("The streetlights come on just before the evening traffic jam. Therefore the streetlights cause the jam."),
    ("I wore the green jersey right before we won both games. Therefore the jersey caused the wins."),
]
_HASTY = [
    ("Both of the two electric cars I have driven had stiff brakes. So most electric cars must have stiff brakes."),
    ("The first two reviewers liked the draft. So nearly all readers will like it."),
    ("Two visits to that clinic involved long waits. So the clinic almost always has long waits."),
]
_DORMITIVE = [
    ("Glue bonds surfaces because it possesses an adhesive capacity — a power whose nature is to make things stick."),
    ("The sedative calms patients because of its tranquilizing property, that is, a disposition whose essence is to produce calm."),
    ("Magnets attract iron because they are endowed with an attractive principle whose nature is to draw iron near."),
]
_RESOURCE = [
    ("Each shelf needs 4 brackets and we have 14 brackets, so we can mount 4 full shelves."),
    ("Each tent sleeps 3 campers and we have 11 campers, so 3 tents are enough for everyone."),
    ("The van seats 6 and there are 20 passengers, so 3 vans will carry them all."),
]
_CONJ = [
    ("Marta is a quiet chess champion. It is therefore more probable that Marta is a librarian who plays chess on weekends than that she is a librarian."),
    ("Deshawn loves rock climbing and geology. It is therefore more probable that he is an engineer who leads a climbing club than that he is an engineer."),
]
_EQUIV = [
    ("A plan with no flaws is a perfect plan. This plan is nothing, and nothing is without flaws. Therefore this plan is perfect."),
    ("Discipline builds character. The army is full of discipline cases. Therefore the army is full of character-building."),
    ("Only man is rational. No woman is a man. Therefore no woman is rational."),
]


def known_flaw_variants() -> list[tuple[str, str]]:
    """28 deterministic (class, text) variants, seeded assembly order."""
    items: list[tuple[str, str]] = []
    for who, why, src in _CIRC:
        items.append((
            "circularity",
            f"We should trust {who} because {why}, and we know {why} because "
            f"{src} assures us of it.",
        ))
    for cond, cons, obs, concl in _AFFIRM:
        items.append((
            "affirming_the_consequent",
            f"If {cond}, {cons}. {obs}. Therefore {concl}.",
        ))
    for cond, cons, obs, verb in _DENY:
        items.append((
            "denying_the_antecedent",
            f"If {cond}, {cons}. {obs}. Therefore it cannot {verb}.",
        ))
    for wrong, prop, concl in _ARITH:
        items.append((
            "false_arithmetic_premise",
            f"Since {wrong}, and {prop}, {concl}.",
        ))
    for prevalence, acc, name in _BASE:
        items.append((
            "base_rate_neglect",
            f"A condition affects {prevalence} people. The screening test is "
            f"{acc} accurate. {name} tested positive, so it is {acc} certain "
            f"that {name} has the condition.",
        ))
    items += [("composition", t) for t in _COMP]
    items += [("post_hoc_causation", t) for t in _POSTHOC]
    items += [("hasty_generalization", t) for t in _HASTY]
    items += [("dormitive_vacuity", t) for t in _DORMITIVE]
    items += [("arithmetic_resource_error", t) for t in _RESOURCE]
    items += [("conjunction_fallacy", t) for t in _CONJ]
    items += [("equivocation", t) for t in _EQUIV]
    # 39 templates; select 28 deterministically (seeded shuffle then prefix),
    # keeping the class mix close to the committed battery's.
    rng = random.Random(seed_for("e02-known-variants"))
    rng.shuffle(items)
    items = items[:28]
    assert len(items) == 28, len(items)
    return items


def build_known_items() -> list[dict]:
    fixtures = load_battery_fixtures()
    assert len(fixtures) == 12
    items = []
    for index, text in enumerate(fixtures):
        item_id = f"kf-fix-{index:02d}"
        items.append({
            "id": item_id,
            "sub_battery": "known_flaw",
            "flaw_class": FIXTURE_CLASSES[index],
            "seed": seed_for(item_id),
            "source": "scripts/judge_battery.py FLAWED fixture",
            "judged_text": text,
            "hidden_annotation": (
                f"Planted-flaw battery fixture #{index}: "
                f"{FIXTURE_CLASSES[index].replace('_', ' ')} (ground truth by "
                f"construction)."),
        })
    for index, (flaw_class, text) in enumerate(known_flaw_variants()):
        item_id = f"kf-var-{index:02d}"
        items.append({
            "id": item_id,
            "sub_battery": "known_flaw",
            "flaw_class": flaw_class,
            "seed": seed_for(item_id),
            "source": "deterministic template variant of battery taxonomy",
            "judged_text": text,
            "hidden_annotation": (
                f"Deterministic template variant: {flaw_class.replace('_', ' ')} "
                f"(ground truth by construction)."),
        })
    assert len(items) == 40
    return items


# ---------------------------------------------------------------------- #
# Main.
# ---------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-dir", default="experiments/e02_t1_items")
    args = parser.parse_args()
    load_credentials()
    items_dir = REPO / args.items_dir
    items_dir.mkdir(parents=True, exist_ok=True)
    ledger = UsageLedger(items_dir / "token_usage.json")

    # (c) first: zero-token, deterministic.
    known_path = items_dir / "known_flaws.json"
    if not known_path.exists():
        known_path.write_text(json.dumps(build_known_items(), indent=2) + "\n")
        print(f"known_flaws.json written (40 items, 0 tokens)", flush=True)

    # (a) unknown-flaw artifacts: 10 per class, topics assigned round-robin
    # over the deterministic topic list, seeded per item id.
    unknown_path = items_dir / "unknown_flaws.json"
    existing = (json.loads(unknown_path.read_text())
                if unknown_path.exists() else [])
    done_ids = {item["id"] for item in existing}
    jobs = []
    topic_index = 0
    for flaw_class in FLAW_CLASSES:
        for k in range(10):
            item_id = f"uf-{CLASS_PREFIX[flaw_class]}-{k:02d}"
            topic = TOPICS[topic_index % len(TOPICS)]
            topic_index += 1
            if item_id not in done_ids:
                jobs.append((item_id, flaw_class, topic))
    if jobs:
        print(f"generating {len(jobs)} unknown-flaw artifacts...", flush=True)
        with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
            futures = [pool.submit(generate_unknown_item, i, c, t, ledger)
                       for i, c, t in jobs]
            for future in concurrent.futures.as_completed(futures):
                existing.append(future.result())
                existing.sort(key=lambda item: item["id"])
                unknown_path.write_text(json.dumps(existing, indent=2) + "\n")
    print(f"unknown_flaws.json: {len(existing)} items", flush=True)

    # (b) toothless envelopes: modes alternate deterministically.
    toothless_path = items_dir / "toothless_envelopes.json"
    existing_t = (json.loads(toothless_path.read_text())
                  if toothless_path.exists() else [])
    done_t = {item["id"] for item in existing_t}
    jobs_t = []
    for k in range(40):
        item_id = f"tl-{k:02d}"
        if item_id in done_t:
            continue
        topic = TOPICS[(seed_for(item_id) + k) % len(TOPICS)]
        mode = TOOTHLESS_MODES[k % 2]
        jobs_t.append((item_id, topic, mode))
    if jobs_t:
        print(f"generating {len(jobs_t)} toothless envelopes...", flush=True)
        with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
            futures = [pool.submit(generate_toothless_item, i, t, m, ledger)
                       for i, t, m in jobs_t]
            for future in concurrent.futures.as_completed(futures):
                existing_t.append(future.result())
                existing_t.sort(key=lambda item: item["id"])
                toothless_path.write_text(json.dumps(existing_t, indent=2) + "\n")
    print(f"toothless_envelopes.json: {len(existing_t)} items", flush=True)

    meta = {
        "schema": "deepreason-e02-t1-items-meta-v1",
        "prereg": "experiments/e02_judge_redteam_prereg.yaml",
        "adversary_model": ADVERSARY_MODEL,
        "adversary_temperature": 1.0,
        "adversary_reasoning": "none (cost control; matches config/ollama-live.yaml precedent)",
        "endpoint": BASE_URL,
        "determinism_note": (
            "Item ids, seeds, topics, modes and prompts are deterministic "
            "functions of the item id (sha256). Provider-side sampling at "
            "temperature 1.0 is NOT seedable via the OpenAI-compatible "
            "surface, so re-running regenerates different texts for missing "
            "items only; committed items are the frozen corpus."),
        "known_flaw_source": (
            "12 FLAWED fixtures from scripts/judge_battery.py plus 28 "
            "deterministic template variants over the same taxonomy"),
        "tokens": ledger.state,
    }
    (items_dir / "generation_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(ledger.state, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
