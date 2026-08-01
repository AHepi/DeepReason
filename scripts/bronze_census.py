"""Bronze Flat v1 proposal census (repair plan phase F / phase H rebuild_v1_census).

Deterministic, zero-token forensic program. Walks every conjecturer LLM call
in the three retained Bronze Flat v1 roots, enumerates every emitted
candidate (final raw response plus attempt-trace raws when they differ),
and joins each candidate to its recorded disposition:

  registered          exact content match to an artifact this call registered
  gate-blocked        an anti-relapse gate Measure names the candidate
  deduped             exact twin of an artifact registered by an earlier call
                      (or a within-call twin); the rule skips these silently
  vs-k-truncated      the model emitted more candidates than VS_K; the rule
                      never processed this one (proved by its forbidden-case
                      commitment ids never being registered by this call)
  attempt-superseded  candidate came from a non-final attempt raw; the call
                      retried and this raw never reached the gate
  dropped-call        the call was dropped (schema/endpoint error) before any
                      gate or registration
  parse-failed        the raw (or candidate) does not decode into the
                      candidates schema
  unresolved          the retained record does not support any of the above

Join methods are recorded per row and kept honest:

  exact-content   content hash or recomputed artifact id matches the record
  fc-register     paired through the deterministic forbidden-case commitment
                  Register events interleaved with the gate Measures
  event-window    inferred from the gate/register accounting of this call's
                  event window (counts must reconcile exactly)
  attempt-trace   row comes from a non-final attempt raw
  none            unresolved

Every number in the output is computed from the retained roots; nothing is
hard coded. Output is deterministic: sorted keys, no timestamps, and a
single generated_from_commit field.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.informal.skeleton import (  # noqa: E402
    forbidden_commitment,
    parse_skeleton,
)
from deepreason.ontology import Artifact, Interface, Ref  # noqa: E402

STREAMS = ("deepseek-v4-pro", "qwen3_5_397b", "kimi-k2_6")
RUNS_DIR = REPO / "experiments" / "bronze_flat_2026-07-13"
OUT_PATH = REPO / "experiments" / "results" / "bronze_flat_v1_census.json"

INLINE = "inline:"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lenient_json(raw: str):
    """Decode a raw model response the way the wire layer effectively did:
    strict JSON first, then a fenced ```json block, then the first JSON
    value found in the text."""
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        pass
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.S)
    if match:
        try:
            return json.loads(match.group(1))
        except ValueError:
            pass
    brace = raw.find("{")
    if brace >= 0:
        try:
            obj, _ = json.JSONDecoder().raw_decode(raw[brace:])
            return obj
        except ValueError:
            pass
    return None


def coerce_content(value):
    """Mirror ConjectureCandidate's content coercion: an object skeleton is
    canonicalized to a sorted-keys JSON string."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return value


def extract_candidates(parsed):
    """Return (candidates, note). A top-level skeleton object (claim +
    mechanism, no candidates wrapper) is surfaced as one schema-invalid
    candidate so the emitted population stays complete."""
    if not isinstance(parsed, dict):
        return None, "response-not-an-object"
    if isinstance(parsed.get("candidates"), list):
        return parsed["candidates"], None
    if "claim" in parsed and "mechanism" in parsed:
        return [{"content": json.dumps(parsed, sort_keys=True), "typicality": None}], (
            "bare-skeleton-response"
        )
    return None, "no-candidates-field"


def candidate_schema_valid(content, typicality) -> bool:
    return (
        isinstance(content, str)
        and len(content) > 0
        and isinstance(typicality, (int, float))
        and not isinstance(typicality, bool)
        and 0.0 <= float(typicality) <= 1.0
    )


def resolve_ref_target(target, artifacts):
    """models.compile_interface resolution: exact id, else unique prefix."""
    if not target or not isinstance(target, str):
        return None
    if target in artifacts:
        return target
    matches = [aid for aid in artifacts if aid.startswith(target)]
    return matches[0] if len(matches) == 1 else None


def candidate_fc_ids(content) -> list[str]:
    """Deterministic forbidden-case commitment ids for a skeleton content
    string (empty when the content is not a parseable skeleton)."""
    skeleton = parse_skeleton(content)
    if skeleton is None:
        return []
    out = []
    for case in skeleton.forbidden:
        cid = forbidden_commitment(case).id
        if cid not in out:
            out.append(cid)
    return out


def recompute_candidate_ids(content, cand_refs, problem_criteria, artifact_pools):
    """Recompute the prospective artifact id under the interface variants
    the run could have produced. Commitments are the problem criteria plus
    the deterministic forbidden-case commitment ids; refs come from the
    candidate's own refs resolved against each artifact pool (and the
    empty-refs variant covers unresolvable alias references)."""
    commitments = list(problem_criteria)
    skeleton = parse_skeleton(content)
    if skeleton is not None:
        for case in skeleton.forbidden:
            cid = forbidden_commitment(case).id
            if cid not in commitments:
                commitments.append(cid)
    commitments = list(dict.fromkeys(commitments))
    ids = set()
    ref_variants = [[]]
    for pool in artifact_pools:
        refs, seen = [], set()
        for ref in cand_refs:
            if not isinstance(ref, dict):
                continue
            role = ref.get("role", "dependence")
            if role not in ("dependence", "mention"):
                continue
            resolved = resolve_ref_target(ref.get("target"), pool)
            if resolved is None:
                continue
            key = (resolved, role)
            if key in seen:
                continue
            seen.add(key)
            refs.append(Ref(target=resolved, role=role))
        if refs:
            ref_variants.append(refs)
    for refs in ref_variants:
        iface = Interface(commitments=commitments, refs=refs)
        ids.add(Artifact.compute_id(f"{INLINE}{content}", "utf8", iface))
    return ids


def stream_candidate_contents(stream: str) -> dict[str, str]:
    """content sha256 -> content text for every emitted candidate in the
    stream (final raws plus differing attempt raws), for offline rescoring.
    Unparseable raws contribute nothing: there is no candidate text."""
    root = RUNS_DIR / stream
    harness = Harness(str(root))
    events = [json.loads(line) for line in (root / "log.jsonl").open()]
    out: dict[str, str] = {}
    for event in events:
        llm = event.get("llm")
        if not llm or llm.get("role") != "conjecturer":
            continue
        if call_kind(event) not in ("Conj", "conj-noregister", "dropped-call"):
            continue
        raw_refs = [llm.get("raw_ref")]
        for attempt in llm.get("attempt_trace") or []:
            if attempt.get("raw_ref") not in raw_refs:
                raw_refs.append(attempt["raw_ref"])
        for ref in raw_refs:
            raw = harness.blobs.get(ref).decode("utf-8", "replace")
            parsed = lenient_json(raw)
            cands, _note = (
                extract_candidates(parsed) if parsed is not None else (None, None)
            )
            if cands is None:
                continue
            for cand in cands:
                if not isinstance(cand, dict):
                    continue
                content = coerce_content(cand.get("content"))
                if isinstance(content, str) and content:
                    out[sha256_text(content)] = content
    return out


def call_kind(event) -> str:
    if event["rule"] == "Conj":
        return "Conj"
    if event["rule"] == "Measure" and event["inputs"]:
        return event["inputs"][0].split(":")[0]
    return event["rule"]


def classify_warrant(warrant: dict) -> str:
    wid = warrant.get("id", "")
    wtype = warrant.get("type", "")
    if wid.startswith("w:arg:") or wtype == "argumentative":
        return "direct-argumentative"
    if wid.startswith("w:skeleton-wf:") or warrant.get("commitment"):
        return "program"
    return wtype or "unknown"


def load_warrants(root: Path) -> list[dict]:
    wdir = root / "objects" / "warrant"
    out = []
    if wdir.is_dir():
        for path in sorted(wdir.iterdir()):
            record = json.loads(path.read_text())
            out.append(record.get("data", record))
    return out


def adjudication_paths(harness, root: Path) -> dict:
    """For every REFUTED registered artifact, classify how it was refuted
    from the warrants that target it."""
    warrants = load_warrants(root)
    by_target: dict[str, list[dict]] = {}
    for warrant in warrants:
        by_target.setdefault(warrant.get("target", ""), []).append(warrant)
    out = {}
    for aid, artifact in harness.state.artifacts.items():
        status = harness.state.status.get(aid)
        if getattr(status, "name", str(status)) != "REFUTED":
            continue
        targeting = sorted(by_target.get(aid, []), key=lambda w: w.get("id", ""))
        paths = sorted({classify_warrant(w) for w in targeting})
        if not paths:
            path = "no-warrant-found"
        elif len(paths) == 1:
            path = paths[0]
        else:
            path = "mixed:" + "+".join(paths)
        out[aid] = {
            "adjudication_path": path,
            "role": artifact.provenance.role if artifact.provenance else None,
            "warrant_ids": [w.get("id") for w in targeting],
            "warrant_paths": paths,
        }
    return out


def build_stream_census(stream: str) -> dict:
    root = RUNS_DIR / stream
    harness = Harness(str(root))
    events = [json.loads(line) for line in (root / "log.jsonl").open()]

    artifacts = harness.state.artifacts
    registered_conj = {
        aid: art
        for aid, art in artifacts.items()
        if art.provenance and art.provenance.role == "conjecturer"
    }
    content_of = {
        aid: art.content_ref[len(INLINE):]
        for aid, art in registered_conj.items()
        if art.content_ref.startswith(INLINE)
    }
    reg_seq = {
        aid: (art.provenance.event_seq if art.provenance else 0)
        for aid, art in registered_conj.items()
    }
    problems = harness.state.problems

    call_events = [
        e
        for e in events
        if e.get("llm")
        and e["llm"].get("role") == "conjecturer"
        and call_kind(e) in ("Conj", "conj-noregister", "dropped-call")
    ]
    gate_events = [
        e
        for e in events
        if e["rule"] == "Measure" and e["inputs"] and e["inputs"][0].startswith("gate:")
    ]
    cycle_marks = [
        (e["seq"], int(e["inputs"][1]))
        for e in events
        if e["rule"] == "Measure" and e["inputs"] and e["inputs"][0] == "cycle"
    ]
    fc_first_seq: dict[str, int] = {}
    for e in events:
        if e["rule"] == "Register" and e["outputs"] and e["outputs"][0].startswith("fc:"):
            fc_first_seq.setdefault(e["outputs"][0], e["seq"])

    rows: list[dict] = []
    anomalies: list[dict] = []
    prev_call_seq = -1

    for event in sorted(call_events, key=lambda e: e["seq"]):
        seq = event["seq"]
        llm = event["llm"]
        kind = call_kind(event)
        window_start = prev_call_seq
        window_gates = [g for g in gate_events if window_start < g["seq"] < seq]
        prev_call_seq = seq
        cycle = max((c for s, c in cycle_marks if s < seq), default=None)

        # Problem context: one conj() call serves exactly one problem, so
        # every gate Measure in the window must agree; a Conj event carries
        # the problem directly. Anything else stays unresolved.
        gate_problems = sorted({g["inputs"][2] for g in window_gates})
        if kind == "Conj" and event["inputs"]:
            call_problem = event["inputs"][0]
        elif len(gate_problems) == 1:
            call_problem = gate_problems[0]
        else:
            call_problem = "unresolved"
        if kind == "Conj" and gate_problems and gate_problems != [call_problem]:
            anomalies.append({"seq": seq, "note": "gate-problem-mismatch"})

        criteria = []
        if call_problem in problems:
            criteria = [
                c for c in problems[call_problem].criteria if c in harness.commitments
            ]
        if not criteria:
            # All Bronze Flat problems carry the same two criteria; fall
            # back to any problem's criteria list (they are identical).
            any_problem = next(iter(problems.values()), None)
            criteria = (
                [c for c in any_problem.criteria if c in harness.commitments]
                if any_problem
                else []
            )

        registered_here = list(event.get("outputs") or []) if kind == "Conj" else []
        artifacts_before = {
            aid: art
            for aid, art in artifacts.items()
            if not (art.provenance and art.provenance.event_seq >= seq)
        }
        artifact_pools = (artifacts_before, artifacts)

        # Attempt-trace raws that differ from the final raw are part of the
        # emitted population but never reached the gate.
        final_raw_ref = llm.get("raw_ref")
        for attempt in llm.get("attempt_trace") or []:
            if attempt.get("raw_ref") == final_raw_ref:
                continue
            araw = harness.blobs.get(attempt["raw_ref"]).decode("utf-8", "replace")
            parsed = lenient_json(araw)
            cands, note = extract_candidates(parsed) if parsed is not None else (None, "undecodable")
            if cands is None:
                rows.append(
                    {
                        "stream": stream,
                        "seq": seq,
                        "call_kind": kind,
                        "attempt": attempt.get("attempt"),
                        "candidate_index": None,
                        "problem": call_problem,
                        "cycle": cycle,
                        "content_sha256": sha256_text(araw),
                        "typicality": None,
                        "schema_valid": False,
                        "disposition": "parse-failed",
                        "join_method": "attempt-trace",
                        "note": note,
                    }
                )
                continue
            for index, cand in enumerate(cands):
                content = coerce_content(cand.get("content")) if isinstance(cand, dict) else None
                typicality = cand.get("typicality") if isinstance(cand, dict) else None
                valid = candidate_schema_valid(content, typicality)
                rows.append(
                    {
                        "stream": stream,
                        "seq": seq,
                        "call_kind": kind,
                        "attempt": attempt.get("attempt"),
                        "candidate_index": index,
                        "problem": call_problem,
                        "cycle": cycle,
                        "content_sha256": sha256_text(content) if isinstance(content, str) else None,
                        "typicality": typicality if valid else typicality,
                        "schema_valid": valid,
                        "disposition": "attempt-superseded",
                        "join_method": "attempt-trace",
                        "note": note,
                    }
                )

        raw = harness.blobs.get(final_raw_ref).decode("utf-8", "replace")
        parsed = lenient_json(raw)
        cands, note = extract_candidates(parsed) if parsed is not None else (None, "undecodable")
        if cands is None:
            rows.append(
                {
                    "stream": stream,
                    "seq": seq,
                    "call_kind": kind,
                    "attempt": None,
                    "candidate_index": None,
                    "problem": call_problem,
                    "cycle": cycle,
                    "content_sha256": sha256_text(raw),
                    "typicality": None,
                    "schema_valid": False,
                    "disposition": "parse-failed",
                    "join_method": "none",
                    "note": note,
                }
            )
            continue

        gate_ids = {g["inputs"][1]: g for g in window_gates}
        matched_gate_ids: set[str] = set()
        matched_registered: set[str] = set()
        call_rows: list[dict] = []
        seen_shas: set[str] = set()

        for index, cand in enumerate(cands):
            content = coerce_content(cand.get("content")) if isinstance(cand, dict) else None
            typicality = cand.get("typicality") if isinstance(cand, dict) else None
            valid = candidate_schema_valid(content, typicality)
            row = {
                "stream": stream,
                "seq": seq,
                "call_kind": kind,
                "attempt": None,
                "candidate_index": index,
                "problem": call_problem,
                "cycle": cycle,
                "content_sha256": sha256_text(content) if isinstance(content, str) else None,
                "typicality": typicality,
                "schema_valid": valid,
                "disposition": None,
                "join_method": None,
                "note": note,
            }
            if not isinstance(content, str) or not content:
                row.update(disposition="parse-failed", join_method="none")
                call_rows.append(row)
                continue
            if kind == "dropped-call":
                row.update(disposition="dropped-call", join_method="event-window")
                call_rows.append(row)
                continue

            cand_refs = cand.get("refs") if isinstance(cand.get("refs"), list) else []
            recomputed = recompute_candidate_ids(content, cand_refs, criteria, artifact_pools)
            row["_fc"] = candidate_fc_ids(content)

            registered_match = next(
                (
                    aid
                    for aid in registered_here
                    if content_of.get(aid) == content and aid not in matched_registered
                ),
                None,
            )
            if registered_match is not None:
                matched_registered.add(registered_match)
                row.update(
                    disposition="registered",
                    join_method="exact-content",
                    artifact_id=registered_match,
                    final_status=str(
                        getattr(harness.state.status.get(registered_match), "name", None)
                    ),
                )
                call_rows.append(row)
                continue

            gate_hit = next((g for g in recomputed if g in gate_ids), None)
            if gate_hit is not None and gate_hit not in matched_gate_ids:
                matched_gate_ids.add(gate_hit)
                gate = gate_ids[gate_hit]
                row.update(
                    disposition="gate-blocked",
                    join_method="exact-content",
                    artifact_id=gate_hit,
                    gate_reason=gate["inputs"][0][len("gate:"):],
                    problem=gate["inputs"][2],
                )
                call_rows.append(row)
                continue

            dedupe_prior = next(
                (
                    aid
                    for aid, prior_content in content_of.items()
                    if prior_content == content and reg_seq.get(aid, 0) < seq
                ),
                None,
            )
            if dedupe_prior is None:
                dedupe_prior = next(
                    (aid for aid in recomputed if aid in artifacts_before), None
                )
            if dedupe_prior is not None:
                row.update(
                    disposition="deduped",
                    join_method="exact-content",
                    artifact_id=dedupe_prior,
                )
                call_rows.append(row)
                continue
            if row["content_sha256"] in seen_shas:
                row.update(disposition="deduped", join_method="exact-content")
                call_rows.append(row)
                continue
            call_rows.append(row)
            seen_shas.add(row["content_sha256"])

        # Event-window reconciliation for candidates the exact join missed.
        unmatched_rows = [r for r in call_rows if r["disposition"] is None]
        unmatched_gates = [g for g in window_gates if g["inputs"][1] not in matched_gate_ids]
        unmatched_registered = [a for a in registered_here if a not in matched_registered]
        if unmatched_rows:
            if len(unmatched_rows) == len(unmatched_gates) and not unmatched_registered:
                for row in unmatched_rows:
                    row.update(disposition="gate-blocked", join_method="event-window")
                    if len(gate_problems) == 1:
                        row["problem"] = gate_problems[0]
            elif (
                kind == "conj-noregister"
                and not unmatched_gates
                and not unmatched_registered
            ):
                # A noregister call admits nothing: every processed candidate
                # was either gate-measured or silently skipped as an exact
                # twin of a registered artifact.
                for row in unmatched_rows:
                    row.update(disposition="deduped", join_method="event-window")
            elif (
                kind == "Conj"
                and not unmatched_gates
                and len(unmatched_rows) == len(unmatched_registered)
            ):
                for row, aid in zip(unmatched_rows, unmatched_registered):
                    row.update(
                        disposition="registered",
                        join_method="event-window",
                        artifact_id=aid,
                        final_status=str(
                            getattr(harness.state.status.get(aid), "name", None)
                        ),
                    )
            elif (
                kind == "conj-noregister"
                and len(unmatched_gates) < len(unmatched_rows)
                and not unmatched_registered
            ):
                # The model emitted more candidates than the rule processed
                # (VS_K truncation). The processed ones are provable: each
                # registers its fresh forbidden-case commitments immediately
                # before its gate Measure, so the fc Register events in the
                # window pair candidates to gates deterministically.
                fc_regs = [
                    (e["seq"], e["outputs"][0])
                    for e in events
                    if e["rule"] == "Register"
                    and window_start < e["seq"] < seq
                    and e["outputs"]
                    and e["outputs"][0].startswith("fc:")
                    and fc_first_seq.get(e["outputs"][0]) == e["seq"]
                ]
                assigned: dict[int, int] = {}
                for reg_seq_num, fcid in fc_regs:
                    for row_index, row in enumerate(unmatched_rows):
                        if row_index in assigned:
                            continue
                        if fcid in row.get("_fc", []):
                            assigned[row_index] = reg_seq_num
                            break
                processed = [unmatched_rows[i] for i in sorted(assigned)]
                truncated = [
                    row
                    for i, row in enumerate(unmatched_rows)
                    if i not in assigned
                    and row.get("_fc")
                    and all(fc_first_seq.get(f, 10**9) > seq for f in row["_fc"])
                ]
                if len(processed) == len(unmatched_gates) and len(processed) + len(
                    truncated
                ) == len(unmatched_rows):
                    gates_left = sorted(unmatched_gates, key=lambda g: g["seq"])
                    for row_index in sorted(assigned):
                        row = unmatched_rows[row_index]
                        fc_seq = assigned[row_index]
                        gate = next(
                            (g for g in gates_left if g["seq"] > fc_seq), None
                        )
                        if gate is not None:
                            gates_left.remove(gate)
                            row.update(
                                disposition="gate-blocked",
                                join_method="fc-register",
                                artifact_id=gate["inputs"][1],
                                gate_reason=gate["inputs"][0][len("gate:"):],
                                problem=gate["inputs"][2],
                            )
                        else:
                            row.update(
                                disposition="gate-blocked", join_method="fc-register"
                            )
                    for row in truncated:
                        row.update(
                            disposition="vs-k-truncated", join_method="fc-register"
                        )
                else:
                    for row in unmatched_rows:
                        row.update(disposition="unresolved", join_method="none")
                    anomalies.append(
                        {
                            "seq": seq,
                            "note": "fc-register-evidence-does-not-reconcile",
                            "unmatched_candidates": len(unmatched_rows),
                            "unmatched_gates": len(unmatched_gates),
                            "fc_processed": len(processed),
                            "fc_truncated": len(truncated),
                        }
                    )
            else:
                for row in unmatched_rows:
                    row.update(disposition="unresolved", join_method="none")
                anomalies.append(
                    {
                        "seq": seq,
                        "note": "window-counts-do-not-reconcile",
                        "unmatched_candidates": len(unmatched_rows),
                        "unmatched_gates": len(unmatched_gates),
                        "unmatched_registered": len(unmatched_registered),
                    }
                )
        elif unmatched_gates:
            anomalies.append(
                {
                    "seq": seq,
                    "note": "gate-measures-without-candidate",
                    "unmatched_gates": len(unmatched_gates),
                }
            )
        for row in call_rows:
            row.pop("_fc", None)
        rows.extend(call_rows)

    counts = {
        "emitted": len(rows),
        "registered": sum(1 for r in rows if r["disposition"] == "registered"),
        "gate_blocked": sum(1 for r in rows if r["disposition"] == "gate-blocked"),
        "deduped": sum(1 for r in rows if r["disposition"] == "deduped"),
        "vs_k_truncated": sum(
            1 for r in rows if r["disposition"] == "vs-k-truncated"
        ),
        "attempt_superseded": sum(
            1 for r in rows if r["disposition"] == "attempt-superseded"
        ),
        "dropped_call": sum(1 for r in rows if r["disposition"] == "dropped-call"),
        "parse_failed": sum(1 for r in rows if r["disposition"] == "parse-failed"),
        "unresolved": sum(1 for r in rows if r["disposition"] == "unresolved"),
    }
    join_methods = {}
    for row in rows:
        join_methods[row["join_method"]] = join_methods.get(row["join_method"], 0) + 1
    coverage = (
        (counts["emitted"] - counts["unresolved"]) / counts["emitted"]
        if counts["emitted"]
        else None
    )

    return {
        "anomalies": anomalies,
        "conjecturer_calls": len(call_events),
        "counts": counts,
        "coverage": coverage,
        "gate_measures": len(gate_events),
        "join_methods": join_methods,
        "refuted_adjudication": adjudication_paths(harness, root),
        "registered_conjecturer_artifacts": sorted(registered_conj),
        "rows": rows,
    }


def build_census() -> dict:
    streams = {stream: build_stream_census(stream) for stream in STREAMS}
    totals = {}
    for stream_data in streams.values():
        for key, value in stream_data["counts"].items():
            totals[key] = totals.get(key, 0) + value
    coverage = (
        (totals["emitted"] - totals["unresolved"]) / totals["emitted"]
        if totals.get("emitted")
        else None
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()
    return {
        "coverage": coverage,
        "generated_from_commit": commit,
        "roots": {s: str((RUNS_DIR / s).relative_to(REPO)) for s in STREAMS},
        "schema": "deepreason-bronze-flat-v1-census-v1",
        "streams": streams,
        "totals": totals,
    }


def main() -> None:
    census = build_census()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(census, indent=2, sort_keys=True) + "\n")
    summary = {
        "coverage": census["coverage"],
        "totals": census["totals"],
        "streams": {
            s: {"counts": d["counts"], "coverage": d["coverage"]}
            for s, d in census["streams"].items()
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
