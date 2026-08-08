"""Relatedness-claim minting (D2 rev 2, R43/M27).

A dual-mode conjecture's code-commitment (item 2) must be "directly
related to the explanation" (Amendment 1) without a faithfulness
referee. This module mints the small, auxiliary tracking artifact that
carries ONE judgment — is this commitment related — the same shape
`register_fail_warrant`'s own `nu` validity-node artifact already is
for a DIFFERENT judgment (was this test sound, `rules/warrants.py`).
Deliberately NOT a warrant/critic triple: there is no warrant here,
only an ordinary artifact whose own `Status` — computed by the
EXISTING, unmodified grounded-extension machinery, exactly like any
other artifact's — records whether the relatedness claim currently
stands. `formally_backed`'s new per-commitment check (step 12) reads
that `Status`; nothing here adjudicates it.
"""

import json

from deepreason.ontology import Interface, Provenance, Ref, Status
from deepreason.ontology.artifact import RefRole

RELATEDNESS_CLAIM_CODEC = "prose:relatedness-claim"


def mint_relatedness_claim(
    harness,
    conjecture_id: str,
    commitment_id: str,
    claim_text: str,
    *,
    provenance_role: str = "conjecturer",
) -> str:
    """Mint a relatedness-claim artifact for one (conjecture, commitment)
    pair (R43, M27). Linked to the conjecture via
    ``Ref(target=conjecture_id, role=RefRole.MENTION)`` — the SAME role
    ``active_properties`` already reads for a different kind of claim
    (M17: MENTION is inert to the support cascade). Content carries
    ``commitment_id`` so a later reader can find the claim for one
    SPECIFIC commitment rather than any claim on the conjecture."""
    content = json.dumps(
        {"commitment": commitment_id, "claim": claim_text}, sort_keys=True
    )
    artifact = harness.create_artifact(
        content,
        codec=RELATEDNESS_CLAIM_CODEC,
        interface=Interface(refs=[Ref(target=conjecture_id, role=RefRole.MENTION)]),
        provenance=Provenance(role=provenance_role),
    )
    return artifact.id


def relatedness_claim_holds(harness, conjecture_id: str, commitment_id: str) -> bool:
    """True unless a relatedness claim minted for THIS (conjecture,
    commitment) pair exists and a sustained challenge (Item 5) has
    flipped its own ``Status`` away from ``ACCEPTED`` (R43). No linked
    claim at all is the F6 opt-out default — protection stays intact,
    exactly as for a commitment that never had its relatedness
    questioned. `formally_backed`'s only caller reads this per
    commitment of the new kind; it never touches the CONJECTURE's own
    `Status` (R43: "the shield falls, the artifact doesn't")."""
    from deepreason import programs

    for artifact in harness.state.artifacts.values():
        if artifact.codec != RELATEDNESS_CLAIM_CODEC:
            continue
        if not any(
            r.role == RefRole.MENTION and r.target == conjecture_id
            for r in artifact.interface.refs
        ):
            continue
        text = programs.content_text(artifact, harness.blobs)
        try:
            data = json.loads(text)
        except ValueError:
            continue
        if data.get("commitment") != commitment_id:
            continue
        return harness.state.status.get(artifact.id) == Status.ACCEPTED
    return True


def relatedness_trial(harness, claim_artifact, conjecture_text: str, adapter, config) -> bool:
    """The referee-free relatedness check (Amendment 1, R24/R35, M21): does
    the challenged commitment "directly relate to the explanation,
    functioning solely as a criticizable surface" for it — judged by BOTH
    cross-family ensemble seats on the narrow question only, reusing
    `relevance_trial`'s own SHAPE (`rules/experiment.py`: referential-
    integrity + unanimity guards) rather than inventing a new referee
    (Amendment 1: "the referee should be irrelevant... if a referee is
    needed, the artifact surface needs a redesign"). On anything short of
    unanimous located passes, registers an ARGUMENTATIVE fail warrant
    against the RELATEDNESS-CLAIM artifact itself — never the conjecture or
    the commitment — mirroring `relevance_trial`'s own
    `target=prop_artifact.id` pattern exactly, so a sustained challenge can
    defeat ONE claim without touching anything else's `Status`. Reactive
    only (R42/F6): nothing calls this as a precondition to admission; it
    runs only when a critic raises a relatedness challenge."""
    from deepreason.canonical import sha256_hex
    from deepreason.llm.contracts import JudgeRuling
    from deepreason.llm.packs import aliases_for_values
    from deepreason.ontology import Provenance, Rule, Warrant, WarrantType
    from deepreason.programs import content_text

    judge_seats = adapter.require_cross_family_judges()
    claim_text = content_text(claim_artifact, harness.blobs)
    pack = "\n".join([
        "NARROW QUESTION: is the attached commitment directly related to "
        "the conjecture's own explanation, functioning solely as a "
        "criticizable surface for it (rule pass), or is it unrelated "
        "filler code (rule fail)?",
        "",
        f"CONJECTURE'S OWN EXPLANATION:\n{conjecture_text}",
        "",
        f"RELATEDNESS CLAIM:\n{claim_text}",
        "",
        "decisive_point MUST quote a span of the explanation or the claim.",
    ])
    calls: list = []
    rulings: list = []
    try:
        for seat in range(len(judge_seats)):
            ruling, llm_call = adapter.call(
                "judge",
                pack,
                JudgeRuling,
                endpoint_index=seat,
                aliases=aliases_for_values([conjecture_text, claim_text], prefix="K"),
            )
            calls.append(llm_call)
            if ruling.decisive_point and ruling.decisive_point not in pack:
                # Unlocatable grounds: invalid ruling, blocked (relevance_trial's
                # own guard against unanchored judge assertions).
                rulings.append(None)
                continue
            rulings.append(ruling)
    finally:
        harness.record_llm_calls(calls, "relatedness-trial")

    if all(r is not None and r.verdict == "pass" for r in rulings):
        return True
    failed = [r for r in rulings if r is not None and r.verdict == "fail"]
    if failed:
        case = failed[0].decisive_point
        case_hash = sha256_hex(case.encode())[:16]
        nu = harness.create_artifact(
            f"nu: relatedness ruling {case_hash} against {claim_artifact.id} is sound",
            provenance=Provenance(role="critic"),
        )
        harness.create_artifact(
            f"critic: commitment does not directly relate to the conjecture's "
            f"own explanation — {case}",
            provenance=Provenance(role="critic"),
            warrants=[Warrant(
                id=f"w:relatedness-trial:{case_hash}:{claim_artifact.id}",
                type=WarrantType.ARGUMENTATIVE,
                target=claim_artifact.id,
                validity_node=nu.id,
            )],
            rule=Rule.CRIT,
        )
    return False
