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
