#!/usr/bin/env python
"""Chaos battery for MiniReason — the parent's measuring philosophy, ported:
every promise the mini makes must hold no matter how badly the engine LLM
behaves. A seeded adversarial endpoint emits garbage, half-valid JSON,
duplicates, paraphrases, unicode junk, partial/zero usage blocks, length
truncations, and endpoint faults; after EVERY run four invariants are
checked mechanically:

  I1 meter == log       (every token on the log exactly once, G1)
  I2 byte-replay        (two replays byte-equal; reopen == live state, G2)
  I3 parent ingest      (deepreason.invariants.verify_root == [], G6)
  I4 status agreement   (mini refuted-by-check == parent grounded refuted)

Any failure is recorded with its seed for exact reproduction.

Usage: python mini/scripts/chaos.py [--runs 150] [--scale 2000]
"""

import argparse
import json
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))
sys.path.insert(0, str(MINI.parent / "src"))

from minireason.call import EndpointError  # noqa: E402
from minireason.log import replay  # noqa: E402
from minireason.loop import Session, run  # noqa: E402

UNICODE_JUNK = "\u00e9\u4e2d\u6587 \U0001f9ea \\ \" ' \x00ish \r\n\t za\u0301lgo"


def _skeleton(rng: random.Random, i: int, flavor: str) -> str:
    body = {
        "claim": f"claim {i}: {rng.choice(['trade', 'climate', 'plague', 'elites'])}",
        "mechanism": f"mechanism {i} " + "x" * rng.randint(0, 200),
        "scope": {"covers": [f"c{i}"], "excludes": []},
        "forbidden": [{"case": f"case {i}",
                       "eval": "predicate:len(content) > 10"}],
        "prose_notes": None,
    }
    if flavor == "failing":
        body["forbidden"] = [{"case": "impossible",
                              "eval": "predicate:len(content) > 10**6"}]
    elif flavor == "no_forbidden":
        body["forbidden"] = []
    elif flavor == "rubric_only":
        body["forbidden"] = [{"case": "judged offline", "eval": "rubric:std"}]
    elif flavor == "unicode":
        body["claim"] = f"claim {i} {UNICODE_JUNK}"
        body["prose_notes"] = UNICODE_JUNK * rng.randint(1, 20)
    elif flavor == "huge":
        body["prose_notes"] = "pad " * rng.randint(2000, 8000)
    elif flavor == "bad_eval":
        body["forbidden"] = [{"case": "syntax error eval",
                              "eval": "predicate:len(content >"}]
    return json.dumps(body, sort_keys=(rng.random() < 0.5))


class ChaosEndpoint:
    """Seeded misbehavior; reports usage in every shape seen live."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.name, self.model = f"chaos-{seed}", "chaos"
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None
        self.calls = 0
        self.emitted: list[str] = []

    def _candidates(self) -> str:
        rng = self.rng
        k = rng.randint(1, 6)
        cands = []
        for _ in range(k):
            roll = rng.random()
            if roll < 0.15 and self.emitted:  # exact duplicate (relapse bait)
                content = rng.choice(self.emitted)
            elif roll < 0.25 and self.emitted:  # paraphrase: reshuffled keys
                try:
                    content = json.dumps(json.loads(rng.choice(self.emitted)),
                                         sort_keys=True, indent=rng.choice([None, 1]))
                except ValueError:
                    content = "not even json"
            else:
                flavor = rng.choice(["good", "good", "good", "failing", "failing",
                                     "no_forbidden", "rubric_only", "unicode",
                                     "huge", "bad_eval", "prose"])
                if flavor == "prose":
                    content = "plain prose candidate " + UNICODE_JUNK
                else:
                    content = _skeleton(rng, self.calls * 10 + len(cands), flavor)
            self.emitted.append(content)
            entry: dict = {"content": content}
            r = rng.random()
            if r < 0.1:
                entry["typicality"] = 7.3  # out of range: schema repair path
            elif r < 0.2:
                entry["content"] = json.loads(content) if content.startswith("{") \
                    else content  # skeleton-as-object coercion path
                entry["typicality"] = 0.5
            else:
                entry["typicality"] = round(rng.random(), 2)
            cands.append(entry)
        return json.dumps({"candidates": cands})

    def complete(self, prompt: str) -> str:
        self.calls += 1
        rng = self.rng
        roll = rng.random()
        if roll < 0.03:
            raise EndpointError("chaos: provider fell over")
        if roll < 0.18:
            response = rng.choice([
                "", "not json", '{"candidates": []}', '{"wrong": "shape"}',
                '{"candidates": [{"typicality": 0.5}]}',
                '{"candidates": [{"content": "x", "typicality": 0.5}',  # cut off
                "prose preamble {\"candidates\": oops",
            ])
        else:
            response = self._candidates()
            if rng.random() < 0.08:
                response = response[: max(10, len(response) // 3)]  # truncation
                self.last_finish_reason = "length"
        # Usage shapes seen live: full, partial, zero, absent.
        u = rng.random()
        if u < 0.55:
            self.last_usage = {"prompt_tokens": max(1, len(prompt) // 4),
                               "completion_tokens": max(1, len(response) // 4)}
        elif u < 0.75:
            self.last_usage = {"total_tokens": max(1, (len(prompt) + len(response)) // 4)}
        elif u < 0.85:
            self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        else:
            self.last_usage = None
        if self.last_finish_reason != "length" or rng.random() < 0.5:
            self.last_finish_reason = rng.choice(["stop", "stop", "stop", None])
        return response


def verify(root: Path, summary: dict) -> list[str]:
    failures: list[str] = []
    if not summary["meter_equals_log"]:
        failures.append("I1 meter!=log")
    d1, d2 = replay(root).digest(), replay(root).digest()
    live = Session(root).state.digest()
    if not (d1 == d2 == live):
        failures.append("I2 replay divergence")
    try:
        from deepreason.harness import Harness
        from deepreason.invariants import verify_root
        from deepreason.ontology import Status

        report = verify_root(root, meter_total=summary["logged_tokens"])
        if report["violations"]:
            failures.append(f"I3 parent violations: {report['violations'][:2]}")
        mini = Session(root).state
        parent = Harness(root)
        parent_refuted = {a for a, s in parent.state.status.items()
                          if s == Status.REFUTED}
        if parent_refuted != mini.refuted:
            failures.append(
                f"I4 status disagreement: parent-only="
                f"{len(parent_refuted - mini.refuted)} "
                f"mini-only={len(mini.refuted - parent_refuted)}")
    except ImportError:
        failures.append("parent not importable")
    return failures


def chaos_run(seed: int, workdir: Path) -> dict:
    rng = random.Random(seed ^ 0xC0FFEE)
    root = workdir / f"chaos-{seed}"
    problems = [(f"pi-{i}", f"problem {i}: why {rng.choice(['x', 'y', 'z'])}?")
                for i in range(rng.randint(1, 4))]
    started = time.monotonic()
    summary = run(problems, ChaosEndpoint(seed),
                  budget=rng.choice([500, 3_000, 20_000, 200_000]),
                  root=root,
                  vs_k=rng.randint(1, 8),
                  neighbourhood=rng.randint(0, 10),
                  stance_decay=rng.randint(1, 8),
                  turnover_k=rng.randint(1, 5),
                  window=rng.choice([5, 20]),
                  orbit_floor=rng.choice([3, 5]),
                  retry_max=rng.randint(0, 3),
                  max_cycles=rng.choice([5, 25, 60]))
    failures = verify(root, summary)
    return {"seed": seed, "stop": summary["stop"], "cycles": summary["cycles"],
            "events": len(Session(root).state.events),
            "refuted": summary["refuted"], "gate_blocks": summary["gate_blocks"],
            "rotations": summary["rotations"], "tokens": summary["tokens"]["total"],
            "wall_s": round(time.monotonic() - started, 2), "failures": failures}


def scale_probe(cycles: int, workdir: Path) -> dict:
    """One long healthy run: replay/graduation cost at thousands of events."""
    class Fresh:
        name, model = "fresh", "fresh"
        last_usage = last_finish_reason = None
        n = 0

        def complete(self, prompt: str) -> str:
            self.n += 1
            self.last_usage = {"prompt_tokens": len(prompt) // 4,
                               "completion_tokens": 200}
            return json.dumps({"candidates": [
                {"content": _skeleton(random.Random(self.n), self.n, "good"),
                 "typicality": 0.5}]})

    root = workdir / "scale"
    t0 = time.monotonic()
    summary = run([("pi-scale", "generate forever")], Fresh(), budget=10**9,
                  root=root, vs_k=1, turnover_k=10**6, max_cycles=cycles)
    t_run = time.monotonic() - t0
    t0 = time.monotonic()
    state = replay(root)
    t_replay = time.monotonic() - t0
    t0 = time.monotonic()
    failures = verify(root, summary)
    t_verify = time.monotonic() - t0
    return {"cycles": cycles, "events": len(state.events),
            "artifacts": len(state.artifacts),
            "log_mb": round((root / "log.jsonl").stat().st_size / 1e6, 2),
            "run_s": round(t_run, 2), "mini_replay_s": round(t_replay, 2),
            "parent_verify_s": round(t_verify, 2), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=150)
    parser.add_argument("--scale", type=int, default=2000)
    parser.add_argument("--seed0", type=int, default=1)
    args = parser.parse_args()

    workdir = Path(tempfile.mkdtemp(prefix="mini-chaos-"))
    results, failed = [], []
    t0 = time.monotonic()
    for seed in range(args.seed0, args.seed0 + args.runs):
        r = chaos_run(seed, workdir)
        results.append(r)
        if r["failures"]:
            failed.append(r)
            print(f"seed {seed}: FAIL {r['failures']}", flush=True)
        if seed % 25 == 0:
            print(f"... {seed - args.seed0 + 1}/{args.runs} runs, "
                  f"{len(failed)} failures", flush=True)
    campaign_s = time.monotonic() - t0

    scale = scale_probe(args.scale, workdir) if args.scale else None
    shutil.rmtree(workdir, ignore_errors=True)

    stops: dict = {}
    for r in results:
        stops[r["stop"]] = stops.get(r["stop"], 0) + 1
    report = {
        "experiment": "mini chaos battery (adversarial endpoint, seeded)",
        "runs": len(results), "failed_runs": len(failed),
        "failures": failed,
        "stop_distribution": stops,
        "totals": {"events": sum(r["events"] for r in results),
                   "refuted": sum(r["refuted"] for r in results),
                   "gate_blocks": sum(r["gate_blocks"] for r in results),
                   "rotations": sum(r["rotations"] for r in results),
                   "tokens_simulated": sum(r["tokens"] for r in results)},
        "campaign_s": round(campaign_s, 1),
        "scale_probe": scale,
    }
    out = MINI.parent / "experiments" / "results" / "mini_chaos_report.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))
    print(f"\nCHAOS: {'FAIL (' + str(len(failed)) + ' runs)' if failed else 'PASS'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
