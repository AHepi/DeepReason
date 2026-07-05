#!/usr/bin/env python
"""Cache benchmark (docs/CACHE_DESIGN.md step (a)): measure the REAL
workload from logged run directories — every prompt a provider actually
saw, replayed byte-for-byte from the blob store. No API calls, no tokens.

Measures, per run and cross-run:
  - exact-match hit rate: fraction of prompts identical to an earlier one
    (the ce1b3cfc fingerprint design's own falsifier: <20% => net negative)
  - prefix-reuse fraction: mean fraction of each prompt's bytes shared
    with the best-matching earlier prompt (what a component-DAG or
    provider prefix cache could bill at the cached rate; the c9931dd1
    design's falsifier uses the same-run figure: <90% => refuted)

With --ground <cache_design_run>, registers the measurement into that
harness as import-role evidence with a source-reliability node, plus a
demonstrative verdict against any surviving design whose forbidden case
OBTAINED — real-world data entering as warrants, never as a score (§0).
"""

import argparse
import json
import sys
from os.path import commonprefix
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.harness import Harness  # noqa: E402

EXACT_FLOOR = 0.20   # ce1b3cfc's self-imposed falsifier
PREFIX_FLOOR = 0.90  # c9931dd1's self-imposed falsifier (same-run prefix reuse)


def collect_prompts(root: Path) -> list[tuple[str, str]]:
    """(role, prompt_text) per LLM call, in event order."""
    harness = Harness(root)
    out = []
    for event in harness.log.read():
        if event.llm is None or not event.llm.prompt_ref:
            continue
        try:
            text = harness.blobs.get(event.llm.prompt_ref).decode()
        except KeyError:
            continue  # sealed or missing blob: skip, honestly
        out.append((event.llm.role, text))
    return out


def best_prefix_fraction(text: str, pool: list[str]) -> float:
    """Longest shared prefix with any pool member, as a fraction of text.
    Pool is bounded by the caller; comparison is deterministic."""
    best = 0
    for other in pool:
        n = len(commonprefix([text, other]))
        if n > best:
            best = n
    return best / len(text) if text else 0.0


def measure(run_roots: list[Path]) -> dict:
    report: dict = {"runs": {}, "cross_run": {}}
    global_pool: list[str] = []
    global_seen: set[str] = set()
    cross_exact = cross_total = 0
    cross_prefix_sum = 0.0
    for root in run_roots:
        prompts = collect_prompts(root)
        seen: set[str] = set()
        pool: list[str] = []
        exact = 0
        prefix_sum = 0.0
        per_role: dict[str, list[float]] = {}
        for role, text in prompts:
            if text in seen:
                exact += 1
            frac = best_prefix_fraction(text, pool)
            prefix_sum += frac
            per_role.setdefault(role, []).append(frac)
            # cross-run: pool of ALL earlier prompts (this run + prior runs)
            if text in global_seen or text in seen:
                cross_exact += 1
            cross_prefix_sum += max(frac, best_prefix_fraction(text, global_pool))
            cross_total += 1
            seen.add(text)
            pool.append(text)
        n = len(prompts)
        report["runs"][str(root)] = {
            "prompts": n,
            "exact_hit_rate": round(exact / n, 4) if n else None,
            "prefix_reuse_fraction": round(prefix_sum / n, 4) if n else None,
            "per_role_prefix_reuse": {
                r: round(sum(v) / len(v), 4) for r, v in sorted(per_role.items())
            },
        }
        global_seen |= seen
        global_pool.extend(pool)
    report["cross_run"] = {
        "prompts": cross_total,
        "exact_hit_rate": round(cross_exact / cross_total, 4) if cross_total else None,
        "prefix_reuse_fraction": round(cross_prefix_sum / cross_total, 4) if cross_total else None,
    }
    runs = [r for r in report["runs"].values() if r["prompts"]]
    same_run_prefix = (
        sum(r["prefix_reuse_fraction"] * r["prompts"] for r in runs)
        / sum(r["prompts"] for r in runs)
    ) if runs else None
    exact_measured = report["cross_run"]["exact_hit_rate"]
    prefix_measured = round(same_run_prefix, 4) if same_run_prefix is not None else None
    report["verdicts"] = {
        "exact_floor": {
            "design": "ce1b3cfc (content-addressable pack dedup)",
            "forbidden_case": f"cross-run exact hit ratio < {EXACT_FLOOR}",
            "measured": exact_measured,
            # None => no data; the forbidden case is UNMEASURED, not obtained.
            "obtained": None if exact_measured is None else exact_measured < EXACT_FLOOR,
        },
        "prefix_floor": {
            "design": "c9931dd1 (prompt-component DAG)",
            "forbidden_case": f"same-run prefix reuse < {PREFIX_FLOOR}",
            "measured": prefix_measured,
            "obtained": None if prefix_measured is None else prefix_measured < PREFIX_FLOOR,
        },
    }
    return report


def ground(target_root: Path, report: dict) -> None:
    """Register the measurement as evidence + demonstrative verdicts in the
    cache-design harness. Follows §12: evidence (role=import) depends on an
    attackable source-reliability node; verdicts are warrants with traces,
    never scores."""
    from deepreason.canonical import sha256_hex
    from deepreason.ontology import Interface, Provenance, Ref, Status
    from deepreason.ontology.commitment import Commitment
    from deepreason.programs import content_text
    from deepreason.rules.warrants import register_fail_warrant

    harness = Harness(target_root)
    payload = json.dumps(report, indent=2, sort_keys=True)
    evidence_sha = sha256_hex(payload.encode())[:12]

    reliability = harness.create_artifact(
        "source-reliability: deterministic replay of this repository's own "
        "logged prompts (runs/*); representative of the harness workload, "
        "attackable if the workload mix is unrepresentative",
        provenance=Provenance(role="import"),
    )
    evidence = harness.create_artifact(
        payload,
        interface=Interface(refs=[Ref(target=reliability.id, role="dependence")]),
        provenance=Provenance(role="import"),
    )
    checks = [
        # (verdict key, commitment id, claim markers, measured, floor)
        ("exact_floor", f"cachebench-exact-floor@{evidence_sha}",
         ("content-addressable", "dedup"),
         report["cross_run"]["exact_hit_rate"], EXACT_FLOOR),
        ("prefix_floor", f"cachebench-prefix-floor@{evidence_sha}",
         ("dag", "component"),
         report["verdicts"]["prefix_floor"]["measured"], PREFIX_FLOOR),
    ]
    for key, kappa_id, markers, measured, floor in checks:
        if measured is None:
            # No prompts collected — the forbidden case is unmeasured. Grounding
            # a `predicate:None >= floor` verdict would refute designs from zero
            # data; skip instead.
            print(f"SKIP {key}: no measurement (no prompts collected)")
            continue
        harness.register_commitment(
            Commitment(id=kappa_id, eval=f"predicate:{measured} >= {floor}")
        )
        for aid, pid in list(harness.state.addr):
            if harness.state.status.get(aid) != Status.ACCEPTED:
                continue
            text = content_text(harness.state.artifacts[aid], harness.blobs)
            try:
                claim = json.loads(text).get("claim", "")
            except (ValueError, AttributeError):
                continue
            if not any(m in claim.lower() for m in markers):
                continue
            if not report["verdicts"][key]["obtained"]:
                harness.record_measure(inputs=[f"cachebench-supports:{aid}", evidence.id])
                print(f"measurement SUPPORTS {aid[:12]} (no warrant registered)")
                continue
            critic = register_fail_warrant(
                harness,
                commitment_id=kappa_id,
                target_id=aid,
                nu_content=(
                    f"nu: the cachebench verdict of {kappa_id} on {aid} is sound — "
                    "attack the measurement's representativeness, not this line"
                ),
                critic_content=(
                    f"critic: measured {key} {measured} is below the design's own "
                    f"floor {floor} — its forbidden case obtained "
                    f"(evidence {evidence.id[:12]})"
                ),
                trace_ref=harness.blobs.put(payload.encode()),
            )
            print(f"REFUTED by measurement: {aid[:12]} (critic {critic.id[:12]}, "
                  f"status now {harness.state.status.get(aid).value})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_roots", nargs="*", help="run directories with log.jsonl")
    parser.add_argument("--out", default="experiments/results/cachebench_report.json")
    parser.add_argument("--ground", default=None,
                        help="cache-design run root to register evidence + verdicts into")
    args = parser.parse_args()
    roots = [Path(r) for r in args.run_roots]
    if not roots:
        roots = sorted(p.parent for p in Path("runs").glob("*/log.jsonl"))
    report = measure(roots)
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report["verdicts"], indent=2, sort_keys=True))
    print(f"\nfull report: {args.out}")
    if args.ground:
        ground(Path(args.ground), report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
