"""Phase H counterfactual forensics for bronze flat v1 (zero LLM tokens).

Two replays over the retained roots and the census:

1. Gate replay: every emitted proposal is evaluated against the run's final
   refuted record under three policies - exact-hash-only, the repaired
   semantic gate, and the legacy (pre-repair) gate. Co-evolution is NOT
   simulated: refutations that would themselves have changed under a
   different gate are held fixed at the actual record, and proposals
   emitted before a stream's first refutation are counted admitted under
   every policy. The numbers bound what each policy would have let through.

2. Authority replay: the status graph with every direct argumentative
   warrant treated as observe-only (no attack edge). An artifact stays
   refuted only if a non-argumentative warrant (program, execution)
   attacks it. No LLM is consulted.

Output: experiments/results/bronze_flat_v1_counterfactual_forensics.json
"""
from __future__ import annotations

import json
from pathlib import Path

from deepreason.harness import Harness
from deepreason import programs
from deepreason.ontology import Artifact, Interface, Provenance

ROOTS = {
    "deepseek-v4-pro": Path("experiments/bronze_flat_2026-07-13/deepseek-v4-pro"),
    "qwen3.5:397b": Path("experiments/bronze_flat_2026-07-13/qwen3_5_397b"),
    "kimi-k2.6": Path("experiments/bronze_flat_2026-07-13/kimi-k2_6"),
}
CENSUS = Path("experiments/results/bronze_flat_v1_census.json")
OUT = Path("experiments/results/bronze_flat_v1_counterfactual_forensics.json")

STREAM_KEYS = {
    "deepseek-v4-pro": "deepseek-v4-pro",
    "qwen3_5_397b": "qwen3.5:397b",
    "kimi-k2_6": "kimi-k2.6",
    "deepseek-v4-pro/": "deepseek-v4-pro",
}


def _refuted_conjecture_interface(harness):
    """The shared bronze interface: every registered conjecture carries the
    same criteria set, so the emitted candidates are evaluated under it."""
    for artifact in harness.state.artifacts.values():
        if artifact.provenance.role.value == "conjecturer":
            return artifact.interface
    return Interface(commitments=[])


def _prospective(content: str, interface) -> Artifact:
    content_ref = f"inline:{content}"
    return Artifact(
        id=Artifact.compute_id(content_ref, "utf8", interface),
        content_ref=content_ref,
        codec="utf8",
        interface=interface,
        provenance=Provenance(role="conjecturer"),
    )


def _first_refutation_seq(root: Path) -> int | None:
    for line in open(root / "log.jsonl"):
        event = json.loads(line)
        if event["rule"] == "Crit":
            return event["seq"]
    return None


def _content_by_sha(root: Path, harness) -> dict[str, str]:
    """Rebuild emitted candidate contents from the conjecturer raw blobs,
    keyed by the census's content sha256."""
    import hashlib

    contents: dict[str, str] = {}
    for line in open(root / "log.jsonl"):
        event = json.loads(line)
        llm = event.get("llm")
        if not llm or llm.get("role") != "conjecturer":
            continue
        refs = [llm.get("raw_ref")] + [
            attempt.get("raw_ref") for attempt in llm.get("attempt_trace") or []
        ]
        for ref in dict.fromkeys(r for r in refs if r):
            try:
                raw = harness.blobs.get(ref)
                raw = raw.decode() if isinstance(raw, bytes) else raw
                data = json.loads(raw)
                # Some raws are double-encoded JSON strings.
                if isinstance(data, str):
                    data = json.loads(data)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            for candidate in data.get("candidates") or []:
                content = candidate.get("content")
                if not isinstance(content, str):
                    continue
                sha = hashlib.sha256(content.encode()).hexdigest()
                contents.setdefault(sha, content)
    return contents


def gate_replay(stream: str, root: Path, rows: list[dict]) -> dict:
    harness = Harness(root)
    interface = _refuted_conjecture_interface(harness)
    refuted = {
        aid for aid, status in harness.state.status.items()
        if status.value == "refuted"
    }
    first_kill = _first_refutation_seq(root)

    # Legacy battery: shared evaluable commitments between the prospective
    # candidate and each refuted prior, equivalence blocks regardless of
    # program class, domain, or embedder (the pre-repair semantics).
    def legacy_blocks(candidate: Artifact) -> bool:
        for prior_id in refuted:
            prior = harness.state.artifacts.get(prior_id)
            if prior is None:
                continue
            ids = dict.fromkeys(
                candidate.interface.commitments + prior.interface.commitments
            )
            battery = sorted(
                cid for cid in ids
                if cid in harness.commitments
                and programs.evaluable(harness.commitments[cid])
            )
            if not battery:
                continue
            cv = tuple(
                programs.evaluate(harness.commitments[cid], candidate, harness.blobs)[0]
                for cid in battery
            )
            pv = tuple(
                programs.evaluate(harness.commitments[cid], prior, harness.blobs)[0]
                for cid in battery
            )
            if cv == pv:
                return True
        return False

    # Repaired battery rule: a battery whose evaluable members are all
    # structural cannot establish equivalence, so for this corpus the
    # repaired gate reduces to exact hash plus receipts. Verified per
    # candidate rather than assumed.
    def repaired_blocks(candidate: Artifact) -> bool:
        if candidate.id in refuted:
            return True
        for prior_id in refuted:
            prior = harness.state.artifacts.get(prior_id)
            if prior is None:
                continue
            ids = dict.fromkeys(
                candidate.interface.commitments + prior.interface.commitments
            )
            battery = [
                cid for cid in ids
                if cid in harness.commitments
                and programs.evaluable(harness.commitments[cid])
            ]
            if not battery:
                continue
            if all(
                programs.program_class(harness.commitments[cid]) == "structural"
                for cid in battery
            ):
                continue
            cv = tuple(
                programs.evaluate(harness.commitments[cid], candidate, harness.blobs)[0]
                for cid in battery
            )
            pv = tuple(
                programs.evaluate(harness.commitments[cid], prior, harness.blobs)[0]
                for cid in battery
            )
            if cv == pv:
                return True
        return False

    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from bronze_census import stream_candidate_contents

    contents = stream_candidate_contents(stream)
    contents.update(_content_by_sha(root, harness))
    counts = {
        "emitted": 0,
        "admitted_exact_hash_only": 0,
        "admitted_repaired_gate": 0,
        "admitted_legacy_gate": 0,
        "pre_first_kill": 0,
        "content_unrecovered": 0,
    }
    for row in rows:
        if not row.get("schema_valid", True):
            continue
        content = contents.get(row.get("content_sha256") or "")
        if content is None:
            counts["content_unrecovered"] += 1
            continue
        counts["emitted"] += 1
        candidate = _prospective(content, interface)
        if first_kill is not None and row.get("seq", 0) < first_kill:
            counts["pre_first_kill"] += 1
            counts["admitted_exact_hash_only"] += 1
            counts["admitted_repaired_gate"] += 1
            counts["admitted_legacy_gate"] += 1
            continue
        if candidate.id not in refuted:
            counts["admitted_exact_hash_only"] += 1
        if not repaired_blocks(candidate):
            counts["admitted_repaired_gate"] += 1
        if not legacy_blocks(candidate):
            counts["admitted_legacy_gate"] += 1
    return counts


def authority_replay(root: Path) -> dict:
    harness = Harness(root)
    remains_refuted, would_stand = [], []
    for aid, status in harness.state.status.items():
        if status.value != "refuted":
            continue
        artifact = harness.state.artifacts.get(aid)
        if artifact is None:
            continue
        attacking = [
            w for w in harness.warrants.values() if w.target == aid
        ]
        non_argumentative = [
            w for w in attacking if w.type.value != "argumentative"
        ]
        role = artifact.provenance.role.value
        entry = {"id": aid[:12], "role": role}
        if non_argumentative:
            entry["kept_refuted_by"] = sorted(
                w.type.value for w in non_argumentative
            )
            remains_refuted.append(entry)
        else:
            would_stand.append(entry)
    return {
        "would_return_to_accepted": would_stand,
        "remains_refuted": remains_refuted,
    }


def main() -> None:
    census = json.loads(CENSUS.read_text())
    by_stream: dict[str, list[dict]] = {
        name: stream.get("rows", [])
        for name, stream in census["streams"].items()
    }

    report = {
        "schema": "deepreason-bronze-flat-v1-counterfactuals",
        "inputs": {
            "census": str(CENSUS),
            "roots": {k: str(v) for k, v in ROOTS.items()},
        },
        "caveats": [
            "co-evolution not simulated: the refuted record is held fixed at "
            "the actual run's final state; a different gate or authority "
            "would have changed which refutations existed at each step",
            "proposals emitted before a stream's first refutation are "
            "counted admitted under every policy",
            "authority replay changes no stored root; it recomputes which "
            "refuted artifacts are attacked only by argumentative warrants",
        ],
        "gate_replay": {},
        "authority_replay": {},
    }
    for dirname in ("deepseek-v4-pro", "qwen3_5_397b", "kimi-k2_6"):
        root = Path("experiments/bronze_flat_2026-07-13") / dirname
        rows = by_stream.get(dirname, [])
        if rows:
            report["gate_replay"][dirname] = gate_replay(dirname, root, rows)
        report["authority_replay"][dirname] = authority_replay(root)

    totals = {}
    for key in ("emitted", "admitted_exact_hash_only", "admitted_repaired_gate",
                "admitted_legacy_gate", "pre_first_kill"):
        totals[key] = sum(v.get(key, 0) for v in report["gate_replay"].values())
    report["gate_replay"]["totals"] = totals
    report["authority_replay"]["summary"] = {
        stream: {
            "would_return_to_accepted": len(v["would_return_to_accepted"]),
            "remains_refuted": len(v["remains_refuted"]),
        }
        for stream, v in report["authority_replay"].items()
        if stream != "summary"
    }
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps({"gate_totals": totals,
                      "authority": report["authority_replay"]["summary"]}, indent=1))


if __name__ == "__main__":
    main()
