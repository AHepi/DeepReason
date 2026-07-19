"""Immutable, run-bound evidence inputs for autonomous inquiry."""

from deepreason.evidence.models import (
    AttachedSourceProvenanceV1,
    AttachedSourceV1,
    DossierExcerptV1,
    DossierPackReceiptV1,
    EvidenceDossierV1,
    RunInputBudgetV1,
    RunInputCommitmentV1,
    RunInputManifest,
    RunInputManifestV1,
    RunInputManifestV2,
    RunInputProblemV1,
    RunInputProblemV2,
)
from deepreason.evidence.state import (
    bind_run_input,
    load_evidence_dossier,
    load_run_input,
    stage_attached_source,
    verify_run_input,
)
from deepreason.evidence.dossier import (
    commit_dossier_pack_receipt,
    dossier_exposure_counts,
    pack_dossier,
)
from deepreason.evidence.render import attach_bound_evidence, render_dossier_pack

__all__ = [
    "AttachedSourceProvenanceV1",
    "AttachedSourceV1",
    "DossierExcerptV1",
    "DossierPackReceiptV1",
    "EvidenceDossierV1",
    "RunInputBudgetV1",
    "RunInputCommitmentV1",
    "RunInputManifest",
    "RunInputManifestV1",
    "RunInputManifestV2",
    "RunInputProblemV1",
    "RunInputProblemV2",
    "bind_run_input",
    "commit_dossier_pack_receipt",
    "dossier_exposure_counts",
    "attach_bound_evidence",
    "load_evidence_dossier",
    "load_run_input",
    "pack_dossier",
    "render_dossier_pack",
    "stage_attached_source",
    "verify_run_input",
]
