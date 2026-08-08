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

from deepreason.ontology import Interface, Provenance, Ref
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
