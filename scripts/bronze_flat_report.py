"""Bronze flat v1 report generator (prereg: experiments/bronze_flat_v1_prereg.yaml).

Mechanical stats are computed from the retained roots; the narrative reading
is committed prose, clearly marked interpretive. Zero LLM tokens.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from deepreason.harness import Harness
from deepreason.invariants import verify_root

ROOTS = Path("experiments/bronze_flat_2026-07-13")
STREAMS = {
    "deepseek-v4-pro": "deepseek-v4-pro",
    "qwen3_5_397b": "qwen3.5:397b",
    "kimi-k2_6": "kimi-k2.6",
}
OUT = Path("experiments/results/bronze_flat_v1_report.json")


def _content(ref: str, blobs) -> dict:
    if ref.startswith("inline:"):
        try:
            return json.loads(ref[len("inline:"):])
        except Exception:
            return {"raw": ref[7:400]}
    try:
        return json.loads(blobs.get(ref))
    except Exception:
        return {"raw": str(ref)[:400]}


def stream_stats(dirname: str, model: str) -> dict:
    root = ROOTS / dirname
    ver = verify_root(root)
    h = Harness(root)
    st = h.state
    events = [json.loads(l) for l in open(root / "log.jsonl")]

    measures = collections.Counter(
        e["inputs"][0] if e["inputs"] else "?" for e in events if e["rule"] == "Measure"
    )
    gate_blocks = sum(v for k, v in measures.items() if k.startswith("gate:battery-equivalent"))
    noop_registers = sum(
        1 for e in events if e["rule"] == "Register" and not e["state_diff"].get("A+")
    )
    llm_roles = collections.Counter(e["llm"]["role"] for e in events if e.get("llm"))

    conjectures = []
    for aid, a in st.artifacts.items():
        if a.provenance.role.value != "conjecturer":
            continue
        c = _content(a.content_ref, h.blobs)
        conjectures.append(
            {
                "id": aid[:12],
                "status": st.status[aid].value,
                "claim": str(c.get("claim", ""))[:400],
                "mechanism": str(c.get("mechanism", ""))[:400],
                "malformed_skeleton": not c.get("claim"),
            }
        )

    refuted_kinds = collections.Counter()
    for aid, s in st.status.items():
        if s.value != "refuted" or aid not in st.artifacts:
            continue
        a = st.artifacts[aid]
        role = a.provenance.role.value
        c = _content(a.content_ref, h.blobs)
        if role == "conjecturer":
            refuted_kinds["conjecture"] += 1
        elif "stance" in json.dumps(c)[:250]:
            refuted_kinds["school-stance-seed"] += 1
        elif role == "seed":
            refuted_kinds["standard-or-seed"] += 1
        else:
            refuted_kinds[role] += 1

    return {
        "model": model,
        "verify_root_violations": ver["violations"],
        "events": ver["stats"]["events"],
        "cycles_completed": measures.get("cycle", 0),
        "tokens": ver["stats"]["logged_tokens"],
        "artifacts": ver["stats"]["artifacts"],
        "accepted": ver["stats"]["accepted"],
        "refuted": ver["stats"]["refuted"],
        "refuted_by_kind": dict(refuted_kinds),
        "conjectures": conjectures,
        "llm_calls_by_role": dict(llm_roles),
        "anti_relapse_gate_blocks": gate_blocks,
        "conj_noregister": measures.get("conj-noregister", 0),
        "noop_registers_content_dedup": noop_registers,
        "trials_llm": measures.get("trial-llm", 0),
        "trials_blocked_ensemble_split": measures.get("trial-blocked:ensemble-split", 0),
        "interventions": {
            k.split(":", 1)[1]: v
            for k, v in measures.items()
            if k.startswith("intervention:")
        },
        "dropped_cycles": measures.get("dropped-call", 0),
    }


def main() -> None:
    streams = {name: stream_stats(d, name) for d, name in
               ((d, m) for d, m in STREAMS.items())}

    report = {
        "schema": "deepreason-bronze-flat-v1",
        "prereg": "experiments/bronze_flat_v1_prereg.yaml",
        "question": "pi-bronze (Late Bronze Age collapse with differential survival)",
        "streams": streams,
        "totals": {
            "tokens": sum(s["tokens"] for s in streams.values()),
            "budget": 1_500_000,
        },
        "cross_stream_mechanism_inventory": {
            "note": "committed reading of every substantive conjecture; "
                    "interpretive but exhaustive over the 10 non-malformed conjectures",
            "mechanism_classes": {
                "systems-network-collapse": ["deepseek-v4-pro", "qwen3.5:397b", "kimi-k2.6"],
                "military-technology-shift": ["deepseek-v4-pro", "qwen3.5:397b", "kimi-k2.6"],
                "climate-drought-famine": ["qwen3.5:397b", "kimi-k2.6"],
                "pandemic": ["deepseek-v4-pro"],
                "earthquake-storm": ["qwen3.5:397b"],
            },
            "opening_conjecture_all_streams": "systems-network-collapse",
            "novel_mechanisms_beyond_published_scholarship": 0,
            "reading": "every proposed mechanism maps onto a published scholarly "
                        "position (systems collapse, military revolution, drought "
                        "migration, earthquake storm, plague, iron diffusion); the "
                        "streams reproduced the historiography menu with high "
                        "cross-family convergence and zero novel mechanisms",
        },
        "criticism_dynamics": {
            "substantive_conjectures_proposed": 10,
            "substantive_conjectures_refuted": 10,
            "frontier_survivors": 0,
            "reinstatements": 0,
            "objection_pattern_reading": "dominant conviction ground is a "
                "scope-formalism charge: the skeleton's covers/excludes fields "
                "must exclude Egypt (it did not collapse), but any use of Egypt's "
                "survival inside the mechanism is then charged as a "
                "scope-vs-mechanism contradiction. The question's own "
                "differential-survival clause is thereby converted into an "
                "automatic conviction device. A minority of objections are "
                "genuinely substantive (Kassite Babylonia comparison, iron "
                "diffusion chronology).",
        },
        "findings": {
            "F3": "the argumentative critic refuted the run's own normative "
                  "infrastructure: in the deepseek and qwen streams it attacked "
                  "and killed 4 school-stance seeds each and the std-hist "
                  "standard itself (objection-equals-warrant shields nothing; "
                  "there is no protected class of artifacts)",
            "F4": "proposal mass is dominated by repeats: 273/183/927 no-op "
                  "content-address re-registrations and 165/183/269 anti-relapse "
                  "gate blocks against the first refuted conjecture's battery "
                  "equivalence class - after the first kill, no stream escaped "
                  "its opening idea's equivalence class for the rest of the run",
        },
        "registered_observables_readings": {
            "novelty_trajectory": "admitted conjectures are genuinely diverse "
                "under nomic (mean pairwise distance 0.57/0.53/0.58 vs paraphrase "
                "margin 0.19) - unlike the gemma corpora. But admission is the "
                "survivor filter: the blocked/deduped mass shows default gravity "
                "toward the refuted basin.",
            "differential_survival_contact": "spontaneous in all three streams, "
                "in two forms: inside conjecture prose (Nile resilience, Nubian "
                "gold, metallurgical conservatism) and, perversely, as the "
                "critics' favourite conviction weapon (scope-formalism).",
            "forbidden_case_quality": "sampled cases are concrete and "
                "discriminating (e.g. 'evidence of a single simultaneous "
                "military conquest by a unified enemy'); the qwen critic attacked "
                "the standard itself over counterfactual-observation coherence.",
            "detector_signals": "generator dist_slope +0.29/n-a/-0.05; "
                "trial-blocked:ensemble-split 1/1/6 (cross-family abstention "
                "working as designed); criticism_debt 0 everywhere.",
            "wire_discipline": "dropped conjecturer cycles 1/1/2 (schema-invalid "
                "after bounded repair), runs continued; kimi spent 2x tokens of "
                "the other streams for fewer artifacts.",
        },
        "narrative_reading_interpretive": (
            "Three strong models each opened with the strongest available theory "
            "(systems collapse), stated real mechanisms with real falsifiers, and "
            "spontaneously engaged the differential-survival clause. The court "
            "then convicted everything: 10 of 10 substantive conjectures refuted, "
            "zero survivors, zero reinstatements, and in two streams the critic "
            "also struck down the run's own standard and stance seeds. After each "
            "opening kill, every stream circled its first idea's equivalence "
            "class for dozens of cycles (F4) while the anti-relapse gate - "
            "correctly - refused re-entry. The run is a live, unscripted "
            "confirmation of the courtroom diagnosis: the archive held (all "
            "roots verify clean, replay intact), the repertoire was scholarly "
            "but not novel, and the criticism climate, not the problem, "
            "dominated the dynamics. As hypothesis generators: (1) observe-only "
            "or witness-routed criticism is a precondition for seeing what the "
            "generative layer can actually build over long horizons; (2) "
            "infrastructure artifacts need either protected status or "
            "trial-gated attack admission (F3); (3) the covers/excludes skeleton "
            "needs an explicit differential-outcome field so explaining a "
            "survivor is not chargeable as a contradiction."
        ),
        "caveats": [
            "observational case study, n=3 streams, one question; no verdicts",
            "legacy live_run.py path: no RunManifest, no preflight "
            "(manifest_present false in verify_root stats); the manifest path "
            "(ops.run_scheduler + preflight_harness) is the evidence-grade "
            "route for future preregs",
            "judge seat 2 (gpt-oss:120b) shared across streams per amendment 1",
            "refuted/accepted statuses reflect the known-indiscriminate critic, "
            "not ground truth (recorded up front in the prereg)",
        ],
    }
    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT}")
    print(json.dumps({k: {"tokens": v["tokens"], "conjectures": len(v["conjectures"]),
                          "refuted": v["refuted"], "gate_blocks": v["anti_relapse_gate_blocks"]}
                      for k, v in report["streams"].items()}, indent=1))


if __name__ == "__main__":
    main()
