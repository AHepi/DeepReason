#!/usr/bin/env python
"""Critic specificity — verifier-anchored sound corpus builder
(pre-registered: experiments/critic_specificity_prereg.yaml).

Builds the 40-item specificity set: for each item a mechanically checkable
claim template on the neutral topic pools (tides, bridge engineering, chess
openings, plate tectonics, bronze-age trade, clock mechanisms,
postal-network economics) is instantiated with seeded random parameters,
verified TRUE by a trusted local checker function (authored here, never by
any model), and only then handed to deepseek-v4-pro to write a short sound
supporting argument (strict JSON {"argument": str}). Arguments must contain
the claim's key numbers verbatim (mechanical acceptance gate); items whose
claim ever fails its checker are rejected and re-drawn.

Console output is ids/counts/error names only — never item bodies.

Outputs (experiments/critic_spec_items/):
  sound_items.json   the 40 verified items (hidden_annotation.verified_true)
  gen.jsonl          append-only generation checkpoint (resume-safe)
Ledger: experiments/critic_spec_run/token_usage.json (shared with the
critic run; whole-experiment ceiling 250,000 tokens; max 3 in flight).

Usage: python scripts/critic_spec_corpus.py
"""

import concurrent.futures
import hashlib
import heapq
import json
import os
import random
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from e02_adversary import UsageLedger  # noqa: E402

from deepreason.easy import load_credentials  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason.llm.repair import parse_one_json_value  # noqa: E402

BASE_URL = "https://ollama.com/v1"
GEN_MODEL = "deepseek-v4-pro"
MAX_IN_FLIGHT = 3
TOKEN_CEILING = 250_000  # whole-experiment cap (corpus + critic runs)

ITEMS_DIR = REPO / "experiments/critic_spec_items"
RUN_DIR = REPO / "experiments/critic_spec_run"
LEDGER_PATH = RUN_DIR / "token_usage.json"

GEN_PROMPT = """You are writing a certification artifact: a short, \
rigorous supporting argument for a factual claim that is known to be true.

CLAIM: {claim}

Write a 4-7 sentence argument that establishes this claim. State the claim \
explicitly with its exact numbers, show the calculation or reasoning that \
proves it, and conclude. Every statement must be correct; do not hedge, do \
not add unrelated facts, and do not change or round any number.

Reply with EXACTLY one strict JSON object and nothing else:
{{"argument": "<the argument text>"}}"""


# ---------------------------------------------------------------------- #
# Trusted local checkers (runner-authored; no model output ever enters).
# ---------------------------------------------------------------------- #

def check_tides_cycles(p) -> bool:
    total_min = p["days"] * 1440
    return (p["cycle_minutes"] == 745
            and p["claimed_cycles"] == total_min // 745
            and p["claimed_cycles"] * 745 <= total_min
            and (p["claimed_cycles"] + 1) * 745 > total_min)


def check_bridge_truss(p) -> bool:
    return (p["reactions"] == 3
            and p["members"] + p["reactions"] == 2 * p["joints"])


def check_chess_knight(p) -> bool:
    f = "abcdefgh".index(p["square"][0])
    r = int(p["square"][1]) - 1
    moves = [(1, 2), (2, 1), (2, -1), (1, -2),
             (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
    n = sum(1 for df, dr in moves
            if 0 <= f + df < 8 and 0 <= r + dr < 8)
    return p["claimed_attacked"] == n


def check_plate_distance(p) -> bool:
    # R mm/yr over T Myr: R*T*1e6 mm = R*T km exactly.
    return p["claimed_km"] == p["rate_mm_yr"] * p["myr"]


def check_trade_shortest_path(p) -> bool:
    nodes = p["cities"]
    graph: dict[str, list[tuple[str, int]]] = {c: [] for c in nodes}
    for a, b, w in p["edges"]:
        graph[a].append((b, w))
        graph[b].append((a, w))
    src, dst = p["origin"], p["destination"]
    dist = {c: float("inf") for c in nodes}
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return dist[dst] == p["claimed_days"]


def check_clock_gear(p) -> bool:
    return (p["wheel1"] * p["wheel2"]
            == p["claimed_ratio"] * p["pinion1"] * p["pinion2"]
            and p["wheel1"] % p["pinion1"] == 0
            and p["wheel2"] % p["pinion2"] == 0)


def check_postal_routes(p) -> bool:
    n = p["offices"]
    return p["claimed_routes"] == n * (n - 1) // 2


def check_postal_weekday(p) -> bool:
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]
    return p["claimed_weekday"] == weekdays[(p["towns"] - 1) % 7]


# ---------------------------------------------------------------------- #
# Claim templates (params -> params, claim text, key numbers, checker).
# ---------------------------------------------------------------------- #

CITY_POOL = ["Uruk", "Byblos", "Troy", "Knossos", "Ugarit",
             "Hattusa", "Memphis", "Ashur"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]


def t_tides(rng: random.Random) -> dict:
    days = rng.randint(14, 90)
    cycles = days * 1440 // 745
    p = {"days": days, "cycle_minutes": 745, "claimed_cycles": cycles}
    claim = (f"Assuming each lunar semidiurnal (M2) tidal cycle lasts "
             f"exactly 745 minutes, exactly {cycles} complete tidal cycles "
             f"fit within {days} days (that is, within {days * 1440} "
             f"minutes).")
    return {"topic": "tides", "template": "tides_cycles", "params": p,
            "claim": claim, "key_numbers": [str(cycles), str(days)],
            "checker": "check_tides_cycles"}


def t_truss(rng: random.Random) -> dict:
    joints = rng.randint(6, 24)
    members = 2 * joints - 3
    p = {"joints": joints, "members": members, "reactions": 3}
    claim = (f"A planar pin-jointed bridge truss with {joints} joints, "
             f"{members} members, and 3 support reaction components "
             f"satisfies the count condition for static determinacy, "
             f"m + r = 2j, since {members} + 3 = {2 * joints}.")
    return {"topic": "bridge engineering", "template": "bridge_truss",
            "params": p, "claim": claim,
            "key_numbers": [str(members), str(joints), str(2 * joints)],
            "checker": "check_bridge_truss"}


def t_knight(rng: random.Random) -> dict:
    f = rng.randint(0, 7)
    r = rng.randint(0, 7)
    square = "abcdefgh"[f] + str(r + 1)
    moves = [(1, 2), (2, 1), (2, -1), (1, -2),
             (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
    n = sum(1 for df, dr in moves
            if 0 <= f + df < 8 and 0 <= r + dr < 8)
    p = {"square": square, "claimed_attacked": n}
    claim = (f"In the opening position analysis of chess, a knight standing "
             f"on {square} of an otherwise empty chessboard attacks exactly "
             f"{n} squares.")
    return {"topic": "chess openings", "template": "chess_knight",
            "params": p, "claim": claim,
            "key_numbers": [square, str(n)],
            "checker": "check_chess_knight"}


def t_plate(rng: random.Random) -> dict:
    rate = rng.randint(8, 95)
    myr = rng.randint(2, 12)
    km = rate * myr
    p = {"rate_mm_yr": rate, "myr": myr, "claimed_km": km}
    claim = (f"A tectonic plate moving at a constant {rate} millimetres per "
             f"year travels exactly {km} kilometres in {myr} million years.")
    return {"topic": "plate tectonics", "template": "plate_distance",
            "params": p, "claim": claim,
            "key_numbers": [str(km), str(rate), str(myr)],
            "checker": "check_plate_distance"}


def t_trade(rng: random.Random) -> dict:
    cities = rng.sample(CITY_POOL, 5)
    a, b, c, d, e = cities
    topology = [(a, b), (b, c), (a, c), (c, d), (b, d), (d, e), (c, e)]
    edges = [(x, y, rng.randint(2, 9)) for x, y in topology]
    graph: dict[str, list[tuple[str, int]]] = {x: [] for x in cities}
    for x, y, w in edges:
        graph[x].append((y, w))
        graph[y].append((x, w))
    dist = {x: float("inf") for x in cities}
    dist[a] = 0
    heap = [(0, a)]
    while heap:
        dd, u = heapq.heappop(heap)
        if dd > dist[u]:
            continue
        for v, w in graph[u]:
            if dd + w < dist[v]:
                dist[v] = dd + w
                heapq.heappush(heap, (dist[v], v))
    best = dist[e]
    p = {"cities": cities, "edges": edges, "origin": a,
         "destination": e, "claimed_days": best}
    routes = "; ".join(f"{x} to {y} takes {w} days" for x, y, w in edges)
    claim = (f"In a bronze-age trade network whose only caravan routes are: "
             f"{routes} — the shortest possible travel time from {a} to {e} "
             f"is exactly {best} days.")
    return {"topic": "bronze-age trade", "template": "trade_shortest_path",
            "params": p, "claim": claim,
            "key_numbers": [str(best), a, e],
            "checker": "check_trade_shortest_path"}


def t_gear(rng: random.Random) -> dict:
    p1 = rng.choice([8, 10, 12, 16])
    r1 = rng.choice([3, 4, 5, 6])
    p2 = rng.choice([8, 10, 12, 16])
    r2 = rng.choice([3, 4, 5, 6, 8])
    w1, w2 = p1 * r1, p2 * r2
    ratio = r1 * r2
    p = {"pinion1": p1, "wheel1": w1, "pinion2": p2, "wheel2": w2,
         "claimed_ratio": ratio}
    claim = (f"In a clock gear train where a {p1}-tooth pinion drives a "
             f"{w1}-tooth wheel, and a {p2}-tooth pinion mounted on that "
             f"wheel's arbor drives a {w2}-tooth wheel, the overall "
             f"velocity reduction from the first pinion to the final wheel "
             f"is exactly {ratio}:1, because ({w1} x {w2}) / ({p1} x {p2}) "
             f"= {ratio}.")
    return {"topic": "clock mechanisms", "template": "clock_gear",
            "params": p, "claim": claim,
            "key_numbers": [str(ratio), str(w1), str(w2), str(p1), str(p2)],
            "checker": "check_clock_gear"}


def t_postal_routes(rng: random.Random) -> dict:
    n = rng.randint(8, 40)
    k = n * (n - 1) // 2
    p = {"offices": n, "claimed_routes": k}
    claim = (f"A postal network in which every pair of its {n} sorting "
             f"offices is joined by one dedicated direct route requires "
             f"exactly {k} routes, since {n} x {n - 1} / 2 = {k}.")
    return {"topic": "postal-network economics", "template": "postal_routes",
            "params": p, "claim": claim,
            "key_numbers": [str(k), str(n)],
            "checker": "check_postal_routes"}


def t_postal_weekday(rng: random.Random) -> dict:
    n = rng.randint(9, 40)
    day = WEEKDAYS[(n - 1) % 7]
    p = {"towns": n, "claimed_weekday": day}
    claim = (f"A mail coach that serves {n} towns on consecutive days, one "
             f"town per day with no rest days, starting on a Monday, "
             f"delivers to the final town on a {day}.")
    return {"topic": "postal-network economics",
            "template": "postal_weekday", "params": p, "claim": claim,
            "key_numbers": [str(n), day],
            "checker": "check_postal_weekday"}


CHECKERS = {
    "check_tides_cycles": check_tides_cycles,
    "check_bridge_truss": check_bridge_truss,
    "check_chess_knight": check_chess_knight,
    "check_plate_distance": check_plate_distance,
    "check_trade_shortest_path": check_trade_shortest_path,
    "check_clock_gear": check_clock_gear,
    "check_postal_routes": check_postal_routes,
    "check_postal_weekday": check_postal_weekday,
}

# 40 items: template plan (index -> template fn).
PLAN = ([t_tides] * 6 + [t_truss] * 5 + [t_knight] * 6 + [t_plate] * 6
        + [t_trade] * 6 + [t_gear] * 6 + [t_postal_routes] * 3
        + [t_postal_weekday] * 2)
assert len(PLAN) == 40


def seed_for(item_id: str) -> int:
    return int(hashlib.sha256(item_id.encode()).hexdigest()[:12], 16)


def draw_item(idx: int) -> dict:
    """Instantiate template idx; redraw until the trusted checker passes
    (a failure indicates a construction bug — recorded, never shipped)."""
    item_id = f"csp-{idx:02d}"
    seed = seed_for(item_id)
    rejects = 0
    for bump in range(50):
        rng = random.Random(seed + bump)
        spec = PLAN[idx](rng)
        ok = CHECKERS[spec["checker"]](spec["params"])
        if ok:
            return {"id": item_id, "seed": seed + bump,
                    "checker_rejects": rejects, **spec}
        rejects += 1
    raise RuntimeError(f"{item_id}: checker never passed (template bug)")


# ---------------------------------------------------------------------- #
# Live generation (deepseek-v4-pro, strict JSON, mechanical acceptance).
# ---------------------------------------------------------------------- #

def gen_endpoint() -> OpenAICompatEndpoint:
    return OpenAICompatEndpoint(
        BASE_URL, GEN_MODEL,
        api_key=os.environ["OLLAMA_API_KEY"],
        temperature=1.0, max_tokens=1200, json_mode=True,
        reasoning="none", provider="ollama", timeout_s=600,
    )


def generate_argument(spec: dict, ledger: UsageLedger) -> dict:
    """Ask the adversary for a supporting argument; accept only if it
    contains every key number of the verified claim. Bounded retries."""
    prompt = GEN_PROMPT.format(claim=spec["claim"])
    ask = prompt
    attempts = {"transport_retries": 0, "json_retries": 0,
                "acceptance_rejects": 0}
    last_err = "none"
    for attempt in range(8):
        ledger.check()
        endpoint = gen_endpoint()
        try:
            raw = endpoint.complete(ask)
        except EndpointError as e:
            attempts["transport_retries"] += 1
            last_err = type(e).__name__
            delay = min(15 * (2 ** attempt), 240)
            print(f"  [{spec['id']}] endpoint error ({last_err}); "
                  f"backoff {delay}s", flush=True)
            time.sleep(delay)
            continue
        ledger.add("generate", endpoint.last_usage, ask, raw)
        try:
            parsed = json.loads(parse_one_json_value(raw).text)
            if not isinstance(parsed, dict):
                raise ValueError("not an object")
        except ValueError:
            attempts["json_retries"] += 1
            last_err = "json_parse"
            ask = (prompt + "\n\nYour previous reply was not a single valid "
                   "JSON object. Reply with EXACTLY one JSON object and "
                   "nothing else.")
            continue
        arg = parsed.get("argument")
        if (isinstance(arg, str) and 150 <= len(arg.strip()) <= 3000
                and all(k in arg for k in spec["key_numbers"])):
            return {"argument": arg.strip(), **attempts}
        attempts["acceptance_rejects"] += 1
        last_err = "acceptance_gate"
        ask = (prompt + "\n\nYour previous argument was rejected by a "
               "mechanical gate: it must be 150-3000 characters and must "
               "contain each of the claim's exact numbers verbatim. Try "
               "again. Reply with EXACTLY one JSON object.")
    raise RuntimeError(f"{spec['id']}: generation failed ({last_err})")


def main() -> int:
    load_credentials()
    ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    ledger = UsageLedger(LEDGER_PATH, ceiling=TOKEN_CEILING)

    specs = [draw_item(i) for i in range(40)]
    n_redraws = sum(s["checker_rejects"] for s in specs)
    # Every shipped claim re-verified by its trusted checker, right now.
    for s in specs:
        assert CHECKERS[s["checker"]](s["params"]), s["id"]
    print(f"claims drawn and verified TRUE: {len(specs)} "
          f"(checker redraws: {n_redraws})", flush=True)
    from collections import Counter
    print("templates:", dict(Counter(s["template"] for s in specs)),
          flush=True)

    checkpoint = ITEMS_DIR / "gen.jsonl"
    done: dict[str, dict] = {}
    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            rec = json.loads(line)
            done[rec["id"]] = rec
    todo = [s for s in specs if s["id"] not in done]
    print(f"generating arguments: {len(todo)} to run "
          f"({len(done)} checkpointed; tokens so far {ledger.total})",
          flush=True)
    write_lock = threading.Lock()

    def worker(spec):
        gen = generate_argument(spec, ledger)
        rec = {**spec, **gen}
        with write_lock:
            with checkpoint.open("a") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
            done[rec["id"]] = rec
        print(f"  {rec['id']}: ok "
              f"(json_retries={gen['json_retries']} "
              f"accept_rejects={gen['acceptance_rejects']} "
              f"tokens {ledger.total})", flush=True)

    with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
        futures = [pool.submit(worker, s) for s in todo]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    items = []
    for spec in specs:
        rec = done[spec["id"]]
        items.append({
            "id": rec["id"],
            "sub_battery": "verified_sound",
            "topic": rec["topic"],
            "template": rec["template"],
            "seed": rec["seed"],
            "params": rec["params"],
            "claim": rec["claim"],
            "checker": rec["checker"],
            "source": "scripts/critic_spec_corpus.py trusted checker + "
                      "deepseek-v4-pro argument",
            "judged_text": rec["argument"],
            "hidden_annotation": {
                "verified_true": True,
                "checker": rec["checker"],
                "checker_rejects": rec["checker_rejects"],
                "key_numbers": rec["key_numbers"],
            },
        })
    out = ITEMS_DIR / "sound_items.json"
    out.write_text(json.dumps(items, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(items)} items -> {out} (tokens {ledger.total})",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
