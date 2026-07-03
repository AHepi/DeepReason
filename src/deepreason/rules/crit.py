"""Crit (spec §3): register critic artifacts carrying valid warrants.

- crit_program: run the target's evaluable commitments (tau_kappa); each
  ``fail`` packages an ordinary demonstrative warrant (commitment, verdict,
  trace_ref, attackable validity node nu). A bare verdict is never an edge.
- crit_argumentative: the argumentative_critic role mounts a case; it
  registers on its own merits as an argumentative warrant. Rubric verdicts
  exist only downstream of the trial guard (P5).
"""

import json

from deepreason import programs
from deepreason.canonical import sha256_hex
from deepreason.llm.contracts import ArgumentativeCriticOutput
from deepreason.llm.packs import render_crit_pack
from deepreason.ontology import Artifact, Provenance, Rule, Warrant, WarrantType


def _register_nu(harness, content: str) -> Artifact:
    return harness.create_artifact(content, provenance=Provenance(role="critic"))


def crit_program(harness, target_id: str) -> list[Artifact]:
    """Evaluate the target's commitments; register a critic per failure."""
    target = harness.state.artifacts[target_id]
    critics: list[Artifact] = []
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or not programs.evaluable(kappa):
            continue
        if any(
            w.commitment == cid and w.target == target_id for w in harness.warrants.values()
        ):
            continue  # this verdict is already on the record
        verdict, trace = programs.evaluate(kappa, target, harness.blobs)
        if verdict != programs.FAIL:
            continue
        trace_ref = harness.blobs.put(
            json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()
        )
        nu = _register_nu(
            harness, f"nu: verdict of {cid} on {target_id} is sound and relevant"
        )
        warrant = Warrant(
            id=f"w:{cid}:{target_id}",
            target=target_id,
            type=WarrantType.DEMONSTRATIVE,
            commitment=cid,
            verdict="fail",
            trace_ref=trace_ref,
            validity_node=nu.id,
        )
        critics.append(
            harness.create_artifact(
                f"critic: {cid} failed on {target_id[:12]}",
                provenance=Provenance(role="critic"),
                warrants=[warrant],
                rule=Rule.CRIT,
            )
        )
    return critics


def crit_argumentative(harness, target_id: str, adapter, config) -> Artifact | None:
    """One argumentative-critic call; registers a critic iff it attacks."""
    pack = render_crit_pack(
        target_id,
        harness.state,
        harness.commitments,
        harness.blobs,
        token_budget=config.PACK_TOKEN_BUDGET,
    )
    output, llm_call = adapter.call("argumentative_critic", pack, ArgumentativeCriticOutput)
    if not output.attack or not output.case.strip():
        return None  # no fault found: registers nothing, correctly
    case_hash = sha256_hex(output.case.encode())[:16]
    nu = _register_nu(
        harness, f"nu: argumentative case {case_hash} against {target_id} is sound"
    )
    warrant = Warrant(
        id=f"w:arg:{case_hash}:{target_id}",
        target=target_id,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu.id,
    )
    return harness.create_artifact(
        output.case,
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm_call,
    )
