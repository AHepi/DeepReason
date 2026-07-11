"""Hard-to-vary (spec §6 Def 3.6; §7 hv-floor).

Lazy spot-check on accepted artifacts: the variator emits k bounded edits
via mu(.|a); HV_B(a) = 1 - Pr[edit passes B(a) and is inequivalent]. Only
inequivalent survivors count (a rename is the same explanation) — the
equivalence surrogate here is normalized-text identity plus optional
embedding proximity, declared in the validity node and therefore attackable
(§17: LLM-dependent assumptions are parked in nu, visible, not eliminated).

hv-floor (§7 Brake 1): a commitment schema pinned into connection-problem
criteria. Instantiation freezes k and HV_MIN into the commitment
(content-addressed via the id hash), so verdicts are replay-stable. B0 =
the target's evaluable commitments — HV-type commitments are excluded by
construction (stratification: HV over a battery containing itself does not
terminate). fail packages an ordinary demonstrative warrant; Adj does the
rest: fresh unattacked critic in G => relation REFUTED, reinstatement =
attack nu.
"""

import json
import re

from deepreason import programs
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm.contracts import VariatorOutput
from deepreason.llm.embedder import distance
from deepreason.rules.warrants import register_fail_warrant, verdict_on_record
from deepreason.ontology import (
    Artifact,
    Commitment,
    Interface,
    Provenance,
)
from deepreason.ontology.commitment import Budget

HV_FLOOR_PROGRAM = "hv_floor"
_EQUIV_EMBED_EPS = 0.02


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


_EQUIV_BATTERY_CAP = 12


def _equivalence_battery(harness, artifact) -> list[str]:
    """The frozen battery that DECIDES equivalence (~=_B, Def 3.5): the
    artifact's own evaluable commitments first, then other registered
    evaluable commitments (cross-problem criteria give edits room to differ
    from an all-passing original), deterministic order, capped."""
    own = [c for c in sorted(set(artifact.interface.commitments))
           if c in harness.commitments and programs.evaluable(harness.commitments[c])]
    foreign = [c for c in sorted(harness.commitments)
               if c not in set(own) and programs.evaluable(harness.commitments[c])]
    return (own + foreign)[:_EQUIV_BATTERY_CAP]


def _text_vector(harness, battery: list[str], text: str) -> tuple:
    fake = Artifact(
        id="", content_ref=f"inline:{text}", codec="utf8",
        interface=Interface(commitments=list(battery)),
        provenance=Provenance(role="variator"),
    )
    return tuple(
        programs.evaluate(harness.commitments[c], fake, harness.blobs)[0]
        for c in battery
    )


def _equivalent(a: str, b: str, embedder=None, harness=None,
                equiv_battery: list[str] | None = None,
                pass_battery: list[str] | None = None) -> bool:
    """Substantive equivalence is decided by the FROZEN VERDICT VECTOR over
    the equivalence battery (~=_B) — never by embedding proximity, which
    remains a cheap pre-filter only (approved correction: replacing one
    opaque shortcut with another is not a fix). Vectors that DIFFER are
    authoritative in every case. Vectors that AGREE are authoritative only
    when the equivalence battery has discriminating MARGIN beyond the pass
    battery (survivors already pass B0, so agreement over B0 alone is
    vacuous — it would collapse HV to 1.0). Where the vector structurally
    cannot decide, the legacy text+embedding surrogate applies — the
    declared, attackable assumption the module docstring parks in nu."""
    if _normalize(a) == _normalize(b):
        return True
    if harness is not None and equiv_battery:
        if _text_vector(harness, equiv_battery, a) != _text_vector(
            harness, equiv_battery, b
        ):
            return False  # substantively different: authoritative
        margin = [c for c in equiv_battery if c not in set(pass_battery or [])]
        if margin:
            return True  # agreement over criteria that COULD have differed
    if embedder is not None:
        return distance(embedder.embed(a), embedder.embed(b)) <= _EQUIV_EMBED_EPS
    return False


def _evaluable_battery(artifact: Artifact, commitments: dict) -> list[str]:
    """B0: evaluable commitments only — hv-floor itself is not registry-
    evaluable, so stratification (B0 excludes HV-type) holds by construction."""
    return sorted(
        cid
        for cid in artifact.interface.commitments
        if cid in commitments and programs.evaluable(commitments[cid])
    )


def _variator_pack(text: str, battery_desc: list[str], k: int, struct: bool) -> str:
    lines = [f"TARGET CONTENT:\n{text}", ""]
    if battery_desc:
        lines += ["BATTERY THE EDITS WILL FACE:"] + [f"- {b}" for b in battery_desc] + [""]
    if struct:
        lines += [
            "KERNEL mu_struct (§10.7): the target is a skeleton — substitute at "
            "role level. Swap the mechanism, the causal link, the scope. Each "
            "edit must be a complete valid skeleton JSON. Do NOT merely reword.",
            "",
        ]
    lines.append(f"DIRECTIVE: produce exactly {k} bounded edits.")
    return "\n".join(lines)


def _sample_edits(harness, adapter, artifact: Artifact, k: int):
    """Returns (text, battery, edits, kernel, llm_call). Kernel selection
    (§6/§10.7): mu_struct whenever the content parses as a skeleton —
    rewording-only variation is banned as the sole kernel for skeletons."""
    from deepreason.informal.skeleton import parse_skeleton

    text = programs.content_text(artifact, harness.blobs)
    kernel = "mu_struct" if parse_skeleton(text) is not None else "mu"
    battery = _evaluable_battery(artifact, harness.commitments)
    pack = _variator_pack(
        text, [harness.commitments[c].eval for c in battery], k, kernel == "mu_struct"
    )
    output, llm_call = adapter.call("variator", pack, VariatorOutput)
    return text, battery, [e.content for e in output.edits[:k]], kernel, llm_call


def _survival(harness, artifact, text, battery, edits, embedder) -> tuple[float, list[dict]]:
    """s_hat = fraction of edits that pass the battery AND are inequivalent."""
    per_edit = []
    survivors = 0
    equiv_battery = _equivalence_battery(harness, artifact)
    for edit in edits:
        fake = Artifact(
            id="",
            content_ref=f"inline:{edit}",
            codec="utf8",
            interface=Interface(commitments=list(battery)),
            provenance=Provenance(role="variator"),
        )
        verdicts = {
            cid: programs.evaluate(harness.commitments[cid], fake, harness.blobs)[0]
            for cid in battery
        }
        passes = all(v == programs.PASS for v in verdicts.values())
        inequivalent = not _equivalent(
            text, edit, embedder, harness=harness, equiv_battery=equiv_battery,
            pass_battery=battery,
        )
        if passes and inequivalent:
            survivors += 1
        per_edit.append(
            {"edit": edit[:120], "verdicts": verdicts, "inequivalent": inequivalent}
        )
    return (survivors / len(edits) if edits else 0.0), per_edit


def hv_spot_check(harness, adapter, artifact_id: str, k: int, embedder=None) -> float | None:
    """Lazy HV estimate (§6), logged as a Measure event; a spot-check,
    re-estimable later. Returns None when unmeasurable (no variator/edits)."""
    if not adapter.has_role("variator"):
        return None
    artifact = harness.state.artifacts[artifact_id]
    text, battery, edits, _kernel, llm_call = _sample_edits(harness, adapter, artifact, k)
    if not edits:
        harness.record_llm_calls([llm_call], "hv-nomeasure")
        return None
    s_hat, _ = _survival(harness, artifact, text, battery, edits, embedder)
    hv = 1.0 - s_hat
    harness.record_measure(hv={artifact_id: hv}, inputs=[artifact_id], llm=llm_call)
    return hv


def hv_floor_commitment(config) -> Commitment:
    """Instantiate hv-floor@<params-hash> with k and HV_MIN frozen in."""
    k = int(config.HV_K)
    hv_min = float(config.HV_MIN if config.HV_MIN is not None else 0.5)
    params_hash = sha256_hex(canonical_json({"k": k, "hv_min": hv_min}))[:12]
    return Commitment(
        id=f"hv-floor@{params_hash}",
        eval=f"program:{HV_FLOOR_PROGRAM}",
        budget=Budget(extra={"k": k, "hv_min": str(hv_min)}),
    )


def is_hv_floor(commitment: Commitment) -> bool:
    return commitment.eval == f"program:{HV_FLOOR_PROGRAM}"


def run_hv_floor(harness, adapter, target_id: str, commitment: Commitment, embedder=None) -> str:
    """Evaluate the hv-floor criterion; fail => ordinary demonstrative
    warrant with the four-clause validity node (§7). Only fail packages a
    warrant; overrun/pass do not."""
    if not adapter.has_role("variator"):
        return programs.OVERRUN  # no kernel available within budget
    target = harness.state.artifacts[target_id]
    if verdict_on_record(harness, commitment.id, target_id):
        return programs.FAIL  # verdict already on the record
    k = int(commitment.budget.extra.get("k", 5))
    hv_min = float(commitment.budget.extra.get("hv_min", "0.5"))
    text, battery, edits, kernel, llm_call = _sample_edits(harness, adapter, target, k)
    if not edits:
        # No bounded edits sampled => hv is UNMEASURED. Falling through would
        # record s_hat=0 -> hv=1.0, vacuously PASSing the floor from zero
        # samples (hv_spot_check guards this the same way).
        if llm_call is not None:
            harness.record_measure(inputs=[f"hv-floor-nomeasure:{target_id}"], llm=llm_call)
        return programs.OVERRUN
    s_hat, per_edit = _survival(harness, target, text, battery, edits, embedder)
    hv = 1.0 - s_hat
    if hv >= hv_min:
        harness.record_measure(hv={target_id: hv}, inputs=[target_id], llm=llm_call)
        return programs.PASS
    register_fail_warrant(
        harness,
        commitment_id=commitment.id,
        target_id=target_id,
        nu_content=(
            f"nu: hv-floor verdict on {target_id} is sound — (i) mu emitted genuine "
            "bounded edits; (ii) k suffices at the decision margin; (iii) the "
            "equivalence surrogate is adequate (misclassifying rephrasings as "
            "inequivalent inflates s_hat); (iv) B0 is an adequate surrogate for B."
        ),
        critic_content=f"critic: hv-floor fail on {target_id[:12]} (hv={hv:.2f} < {hv_min})",
        trace_ref=harness.blobs.put(
            json.dumps(
                {"k": k, "hv_min": hv_min, "s_hat": s_hat, "kernel": kernel,
                 "per_edit": per_edit},
                sort_keys=True,
            ).encode()
        ),
        llm=llm_call,
    )
    return programs.FAIL
