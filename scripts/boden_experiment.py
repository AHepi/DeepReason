#!/usr/bin/env python
"""The Boden experiments (experiments/boden_prereg.yaml): is an LLM
question-evolution loop exploratory (touring a fixed repertoire) or
transformational (extending it)? Four matched arms on laguna-m.1; the
only difference between arms is where the question stream comes from.

  --arm F-fixed|L-loop|X-exogenous|R-noise   run one arm (resumable)
  --report                                    compute metrics + verdict

Instruments are embedder-free (the hashing embedder is certified blind):
incremental LZMA compression novelty + Heaps type-growth curves.
"""

import argparse
import json
import lzma
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pydantic import BaseModel, Field, ValidationError  # noqa: E402

from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "runs" / "boden"
REPORT = ROOT / "experiments" / "results" / "boden_report.json"

N_DRAWS = 300
PER_CONDITION = 10          # draws per question/lens
N_CONDITIONS = 30           # questions (X, R) or chain-generations total (L)
CHAINS = 2                  # independent L chains (15 generations each)
TEMP = 0.9
# laguna-m.1 is a REASONING model and poolside is the "generic" provider,
# which has NO API knob to disable reasoning (llm/providers.py). The first
# run set 600 and reasoning burned ~470-560 of it, truncating the JSON on
# ~55% of draws — and, worse, the truncation rate rose with question length
# (the long seed question failed far more than short exogenous ones), which
# would bias the very loop-vs-fixed comparison this experiment makes. The
# fix is headroom above the reasoning budget; the 2-field contract needs
# only ~200 output tokens, so 2500 never truncates. (docs/AGENT.md
# reasoning-burn trap.) Contaminated first run archived under
# runs/boden_contaminated_600tok/.
MAX_TOKENS = 2500

SEED_QUESTION = (
    "Why did the interconnected palace civilizations of the Eastern "
    "Mediterranean — Mycenaean Greece, Hittite Anatolia, Ugarit and the "
    "Levantine city-states — collapse nearly simultaneously around "
    "1200-1150 BC after centuries of stability, while Egypt survived "
    "diminished?"
)

# X-exogenous: 30 committed history-mechanism questions (eras/regions/
# systems deliberately spread; written once, never edited after prereg).
EXOGENOUS = [
    "Why did the Western Roman Empire fall in the 5th century while the Eastern half survived another millennium?",
    "Why did the Maya lowland cities depopulate in the 9th century AD?",
    "Why did the Indus Valley civilization's urban centers decline around 1900 BC?",
    "Why did the Mongol Empire fragment within a century of Genghis Khan's death?",
    "Why did the Ming dynasty ban long-distance treasure voyages after 1433?",
    "Why did the Black Death accelerate the end of serfdom in Western Europe but entrench it in the East?",
    "Why did the Spanish Empire's silver windfall coincide with its long-run economic decline?",
    "Why did the Dutch Republic, tiny and resource-poor, dominate 17th-century world trade?",
    "Why did the Industrial Revolution begin in Britain rather than France or China?",
    "Why did the Ottoman Empire's technological edge over Europe reverse between 1500 and 1800?",
    "Why did Japan industrialize rapidly after 1868 while Qing China did not?",
    "Why did the Soviet Union collapse in 1991 without a major war?",
    "Why did Easter Island's society collapse before European contact?",
    "Why did the Anasazi abandon Chaco Canyon in the 12th century?",
    "Why did Carthage lose the Punic Wars despite naval and commercial superiority?",
    "Why did the Abbasid Caliphate's scientific golden age wane after the 11th century?",
    "Why did feudal Japan avoid the gunpowder-driven centralization that transformed Europe?",
    "Why did the Inca Empire fall to a few hundred Spaniards within two years?",
    "Why did the Hanseatic League decline after dominating Baltic trade for three centuries?",
    "Why did the American South industrialize so much later than the North?",
    "Why did Venice's naval supremacy in the Mediterranean end in the 16th century?",
    "Why did the Khmer Empire abandon Angkor in the 15th century?",
    "Why did Norse Greenland's settlements die out while Inuit communities thrived there?",
    "Why did the French Revolution radicalize into the Terror within four years?",
    "Why did Prohibition fail in the United States while similar bans succeeded elsewhere?",
    "Why did the Byzantine Empire survive the 7th-century Arab conquests that destroyed Sasanian Persia?",
    "Why did the printing press destabilize religious authority in Europe but not in the Ottoman lands?",
    "Why did the Great Divergence between European and Asian living standards open when it did?",
    "Why did Argentina, among the world's richest countries in 1900, fall behind over the 20th century?",
    "Why did the Bronze Age Uluburun-style long-distance trade never re-emerge in the Iron Age Mediterranean at the same intensity?",
]

# R-noise: deterministic 2-word lenses from a fixed wordlist (seeded
# LCG shuffle — no runtime randomness, replayable).
WORDS = [
    "salt", "ledger", "harbor", "kiln", "oath", "plague", "bronze", "loom",
    "canal", "cavalry", "monsoon", "scribe", "vineyard", "anvil", "caravan",
    "temple", "granary", "dye", "mercenary", "amber", "chariot", "census",
    "famine", "guild", "papyrus", "quarry", "raid", "sail", "tin", "tribute",
]


def _lenses() -> list[tuple[str, str]]:
    xs = list(range(len(WORDS)))
    state = 20260706
    for i in range(len(xs) - 1, 0, -1):
        state = (state * 48271) % 2147483647
        j = state % (i + 1)
        xs[i], xs[j] = xs[j], xs[i]
    pairs = []
    for k in range(N_CONDITIONS):
        a, b = xs[(2 * k) % len(xs)], xs[(2 * k + 1) % len(xs)]
        pairs.append((WORDS[a], WORDS[b]))
    return pairs


class Answer(BaseModel):
    claim: str = Field(min_length=20)
    mechanism: str = Field(min_length=40)


class NextQuestion(BaseModel):
    question: str = Field(min_length=20)


def _endpoint() -> OpenAICompatEndpoint:
    # AMENDMENT 2 (prereg): poolside/laguna-m.1 was hard-429 for 2.5+ hours
    # (unusable). Switched to deepseek-v4-flash with reasoning="none" — a
    # provider whose reasoning knob is controllable, so the reasoning-burn
    # truncation that contaminated run 1 cannot recur. The verdict now
    # scopes to deepseek-v4-flash. The laguna config is preserved below for
    # the record / a future poolside-recovered rerun.
    if os.environ.get("BODEN_PROVIDER") == "poolside":
        return OpenAICompatEndpoint(
            "https://inference.poolside.ai/v1", "poolside/laguna-m.1",
            api_key=os.environ["POOLSIDE_API_KEY"], temperature=TEMP,
            max_tokens=MAX_TOKENS, json_mode=True)
    return OpenAICompatEndpoint(
        "https://api.deepseek.com", "deepseek-v4-flash",
        api_key=os.environ["DEEPSEEK_API_KEY"], temperature=TEMP,
        max_tokens=MAX_TOKENS, json_mode=True, reasoning="none")


def _extract(raw: str) -> str:
    s = raw.strip()
    i, j = s.find("{"), s.rfind("}")
    return s[i:j + 1] if 0 <= i < j else s


def _call(ep, prompt: str, model: type[BaseModel], log, kind: str, meta: dict):
    err = ""
    # A transport error (rate limit / 5xx) is NOT a draw outcome: back off
    # and retry the SAME draw so a 429 storm can never consume draw slots as
    # failures. Only schema-invalid output counts against the 3 real
    # attempts. transport_wait caps total patience per draw (~10 min).
    transport_wait = 0.0
    attempt = 0
    while attempt < 3:
        req = prompt if not err else (
            prompt + f"\nYour previous output was invalid: {err[:300]}\n"
            "Return ONLY a valid JSON object.")
        try:
            raw = ep.complete(req)
        except EndpointError as e:
            err = str(e)[:200]
            log.write(json.dumps({"kind": kind, "meta": meta, "attempt": attempt,
                                  "endpoint_error": err}) + "\n")
            log.flush()
            if transport_wait < 600:
                back = min(60.0, 5.0 * (2 ** min(6, int(transport_wait // 30))))
                time.sleep(back)
                transport_wait += back
                continue  # SAME draw, no attempt consumed
            return None  # give up this draw after ~10 min of rate limiting
        usage = getattr(ep, "last_usage", None) or {}
        try:
            obj = model.model_validate_json(_extract(raw))
        except (ValidationError, ValueError) as e:
            err = str(e)[:200]
            log.write(json.dumps({"kind": kind, "meta": meta, "attempt": attempt,
                                  "invalid": err, "raw": raw[:400],
                                  "usage": usage}) + "\n")
            attempt += 1  # a schema failure IS a real attempt
            continue
        log.write(json.dumps({"kind": kind, "meta": meta, "attempt": attempt,
                              "prompt": prompt, "raw": raw,
                              "usage": usage}) + "\n")
        log.flush()
        return obj
    log.write(json.dumps({"kind": kind, "meta": meta, "failed": True}) + "\n")
    log.flush()
    return None


def _answer_prompt(question: str, lens: tuple[str, str] | None = None) -> str:
    lens_line = (
        f"\nLENS (approach the question through these two concepts): "
        f"{lens[0]}, {lens[1]}\n" if lens else "")
    return (
        f"QUESTION: {question}\n{lens_line}\n"
        "Propose ONE explanatory account. Return JSON: "
        '{"claim": "<one-sentence thesis>", "mechanism": "<the specific '
        'causal mechanism, 2-4 sentences, concrete>"}. '
        "Name a specific causal mechanism — an institution, incentive, "
        "process, or material constraint — not a mood or inevitability."
    )


def _question_prompt(question: str, answers: list[Answer]) -> str:
    shown = "\n".join(
        f"- {a.claim} || {a.mechanism[:200]}" for a in answers[-3:])
    return (
        f"CURRENT QUESTION: {question}\n\nRECENT ANSWERS:\n{shown}\n\n"
        "Pose the SUCCESSOR question these answers make most urgent — the "
        "question that, if answered, would most change our understanding. "
        "It may shift domain, scale, or era; it must be answerable by a "
        "causal-mechanism account and must NOT be a restatement. "
        'Return JSON: {"question": "<the question>"}'
    )


def run_arm(arm: str) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{arm}.jsonl"
    # Resume = number of COMPLETED draw() calls already logged: a draw
    # terminates as a success (carries "prompt") or a hard-fail (carries
    # "failed"). Invalid mid-call retry attempts also carry "raw", so the
    # naive `"raw" in line` count over-counted them as done (fixed here).
    # NOTE (L-loop): resume restores the draw COUNT but not the chain/gen/
    # question walk — a mid-run death resets L-loop to the seed question.
    # Acceptable now that the truncation fix makes single-shot completion
    # the norm; reconstruct-from-log if that stops holding.
    done = 0
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") == "answer" and ("prompt" in r or r.get("failed")):
                done += 1
    if done >= N_DRAWS:
        print(f"[{arm}] already complete ({done} draws)")
        return 0
    ep = _endpoint()
    log = path.open("a")
    n = done
    print(f"[{arm}] starting at {n}/{N_DRAWS}", flush=True)

    def draw(question, cond_idx, lens=None):
        nonlocal n
        obj = _call(ep, _answer_prompt(question, lens), Answer, log,
                    "answer", {"arm": arm, "cond": cond_idx, "i": n})
        n += 1
        if n % 25 == 0:
            print(f"[{arm}] {n}/{N_DRAWS}", flush=True)
        return obj

    if arm == "F-fixed":
        while n < N_DRAWS:
            draw(SEED_QUESTION, 0)
    elif arm == "X-exogenous":
        while n < N_DRAWS:
            cond = n // PER_CONDITION
            draw(EXOGENOUS[cond % len(EXOGENOUS)], cond)
    elif arm == "R-noise":
        lenses = _lenses()
        while n < N_DRAWS:
            cond = n // PER_CONDITION
            draw(SEED_QUESTION, cond, lens=lenses[cond % len(lenses)])
    elif arm == "L-loop":
        per_chain = N_DRAWS // CHAINS
        for chain in range(CHAINS):
            question = SEED_QUESTION
            answers: list[Answer] = []
            target = (chain + 1) * per_chain
            gen = 0
            while n < target:
                if answers and len(answers) % PER_CONDITION == 0:
                    nq = _call(ep, _question_prompt(question, answers),
                               NextQuestion, log, "question",
                               {"arm": arm, "chain": chain, "gen": gen})
                    if nq is not None:
                        question = nq.question
                        gen += 1
                    answers = []
                a = draw(question, f"c{chain}g{gen}")
                if a is not None:
                    answers.append(a)
    else:
        print(f"unknown arm {arm}", file=sys.stderr)
        return 1
    log.close()
    print(f"[{arm}] done: {n} draws")
    return 0


# ------------------------------------------------------------------ #
# Instruments (embedder-free, deterministic)

def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


def _csize(data: bytes) -> int:
    return len(lzma.compress(data, preset=6))


def _answers(arm: str) -> list[dict]:
    path = OUT_DIR / f"{arm}.jsonl"
    out = []
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("kind") == "answer" and "raw" in r:
                try:
                    a = Answer.model_validate_json(_extract(r["raw"]))
                except (ValidationError, ValueError):
                    continue
                out.append({"i": r["meta"]["i"], "cond": r["meta"]["cond"],
                            "text": f"{a.claim} {a.mechanism}"})
    out.sort(key=lambda r: r["i"])
    return out


def _questions(arm: str = "L-loop") -> list[dict]:
    path = OUT_DIR / f"{arm}.jsonl"
    out = []
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("kind") == "question" and "raw" in r:
                try:
                    q = NextQuestion.model_validate_json(_extract(r["raw"]))
                except (ValidationError, ValueError):
                    continue
                out.append({"chain": r["meta"]["chain"], "gen": r["meta"]["gen"],
                            "text": q.question})
    return out


def compression_curve(texts: list[str]) -> list[float]:
    """Marginal novelty per draw: compressed bytes added to the corpus,
    normalized by the draw's standalone compressed size."""
    curve = []
    corpus = b""
    prev = _csize(corpus)
    for t in texts:
        blob = (_norm(t) + "\n").encode()
        cur = _csize(corpus + blob)
        alone = _csize(blob)
        curve.append(max(0.0, (cur - prev) / alone) if alone else 0.0)
        corpus += blob
        prev = cur
    return curve


def type_curves(texts: list[str]) -> dict:
    words_seen, bigrams_seen = set(), set()
    new_bigrams = []
    for t in texts:
        ws = _norm(t).split()
        bs = {f"{a}_{b}" for a, b in zip(ws, ws[1:])}
        new_bigrams.append(len(bs - bigrams_seen))
        words_seen |= set(ws)
        bigrams_seen |= bs
    return {"total_words": len(words_seen), "total_bigrams": len(bigrams_seen),
            "new_bigrams_per_draw": new_bigrams}


def _bigrams(texts: list[str]) -> set:
    out = set()
    for t in texts:
        ws = _norm(t).split()
        out |= {f"{a}_{b}" for a, b in zip(ws, ws[1:])}
    return out


def _qmean(xs: list[float], q: int) -> float | None:
    """Mean of quartile q (0-3) in draw order."""
    if not xs:
        return None
    n = len(xs)
    lo, hi = (q * n) // 4, ((q + 1) * n) // 4
    chunk = xs[lo:hi]
    return sum(chunk) / len(chunk) if chunk else None


def report() -> int:
    arms = {}
    for arm in ("F-fixed", "L-loop", "X-exogenous", "R-noise"):
        rows = _answers(arm)
        texts = [r["text"] for r in rows]
        comp = compression_curve(texts)
        types = type_curves(texts)
        arms[arm] = {
            "n": len(texts),
            "comp_q": [round(_qmean(comp, q), 4) for q in range(4)],
            "newbig_q": [round(_qmean([float(x) for x in types["new_bigrams_per_draw"]], q), 2)
                         for q in range(4)],
            "total_bigrams": types["total_bigrams"],
            "curve": [round(c, 4) for c in comp],
        }

    def fq(arm):  # final-quartile compression novelty
        return arms[arm]["comp_q"][3]

    def ratio(arm):  # final/first quartile within arm
        f, l = arms[arm]["comp_q"][0], arms[arm]["comp_q"][3]
        return (l / f) if f else None

    # P1 instrument validation: fixed arm decays.
    p1 = {"F_final_over_first": round(ratio("F-fixed"), 3),
          "decays": ratio("F-fixed") < 0.6}
    # P2 loop vs fixed (needs BOTH instruments to agree, prereg).
    comp_says_sustained = (fq("L-loop") >= 1.5 * fq("F-fixed")
                           and ratio("L-loop") >= 0.6)
    lb, fb = arms["L-loop"]["newbig_q"][3], arms["F-fixed"]["newbig_q"][3]
    types_says_sustained = lb >= 1.5 * fb
    p2 = {"L_final": fq("L-loop"), "F_final": fq("F-fixed"),
          "L_final_over_first": round(ratio("L-loop"), 3),
          "L_newbig_final": lb, "F_newbig_final": fb,
          "generative": bool(comp_says_sustained and types_says_sustained),
          "instruments_agree": comp_says_sustained == types_says_sustained}
    # P3 loop vs noise.
    p3_comp = fq("L-loop") > 1.2 * fq("R-noise")
    p3_types = arms["L-loop"]["newbig_q"][3] > 1.2 * arms["R-noise"]["newbig_q"][3]
    p3 = {"L_final": fq("L-loop"), "R_final": fq("R-noise"),
          "generative": bool(p3_comp and p3_types),
          "instruments_agree": p3_comp == p3_types}
    # P4 question-corpus saturation.
    qs = _questions()
    qtexts = [q["text"] for q in qs]
    qtypes = type_curves(qtexts)["new_bigrams_per_draw"]
    third = max(1, len(qtypes) // 3)
    first_t = sum(qtypes[:third]) / third
    last_t = sum(qtypes[-third:]) / third
    chain_big = [_bigrams([q["text"] for q in qs if q["chain"] == c])
                 for c in range(CHAINS)]
    overlap = (len(chain_big[0] & chain_big[1])
               / max(1, len(chain_big[0] | chain_big[1]))) if len(chain_big) == 2 else None
    p4 = {"n_questions": len(qs),
          "first_third_new_bigrams": round(first_t, 2),
          "last_third_new_bigrams": round(last_t, 2),
          "sustained": bool(first_t and last_t / first_t >= 0.5),
          "chain_bigram_overlap": round(overlap, 3) if overlap is not None else None}
    # P5 reach: L's exclusive territory, by quartile.
    fx = _bigrams([r["text"] for r in _answers("F-fixed")]) | \
         _bigrams([r["text"] for r in _answers("X-exogenous")])
    lrows = _answers("L-loop")
    n = len(lrows)
    excl = []
    for q in range(4):
        chunk = [r["text"] for r in lrows[(q * n) // 4:((q + 1) * n) // 4]]
        big = _bigrams(chunk)
        excl.append(round(len(big - fx) / max(1, len(big)), 4))
    p5 = {"exclusive_fraction_by_quartile": excl,
          "growing": excl[3] > excl[0]}

    score = sum([p2["generative"], p3["generative"], p4["sustained"], p5["growing"]])
    verdict = ("transformational-for-this-model" if score == 4
               else "closed-repertoire-confirmed-for-this-model" if score == 0
               else f"mixed ({score}/4 generative)")
    out = {"arms": {k: {kk: vv for kk, vv in v.items() if kk != "curve"}
                    for k, v in arms.items()},
           "curves": {k: v["curve"] for k, v in arms.items()},
           "P1_depth": p1, "P2_loop_vs_fixed": p2, "P3_loop_vs_noise": p3,
           "P4_question_saturation": p4, "P5_reach": p5,
           "score_generative": score, "verdict": verdict}
    REPORT.write_text(json.dumps(out, indent=2))
    for k in ("P1_depth", "P2_loop_vs_fixed", "P3_loop_vs_noise",
              "P4_question_saturation", "P5_reach"):
        print(k, json.dumps(out[k]))
    print("\nVERDICT:", verdict)
    print("report:", REPORT)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.report:
        return report()
    if args.arm:
        return run_arm(args.arm)
    print("pass --arm or --report", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
