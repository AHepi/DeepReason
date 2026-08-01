"""Amendment epochs: reshape the question and inject evidence after a stop.

See ``docs/proposals/AMENDMENT_EPOCHS.md``.  Everything an amendment adds is
appended and chained; nothing existing is edited, re-statused, or replaced.
"""

from deepreason.amendment.apply import amend_run
from deepreason.amendment.models import RunAmendmentV1
from deepreason.amendment.state import (
    AMENDMENT_CHAIN_NAME,
    AMENDMENT_EPOCH_DIR,
    AMENDMENT_RECORD_NAME,
    AmendmentError,
    current_epoch,
    dossier_union,
    epoch_directory,
    epoch_problem_ids,
    load_amendments,
    load_epoch_dossier,
    load_epoch_manifest,
    load_epoch_run_input,
    require_no_partial_amendment,
    staged_amendment,
    union_citable_blocks,
    verify_epoch_run_input,
)

__all__ = [
    "AMENDMENT_CHAIN_NAME",
    "AMENDMENT_EPOCH_DIR",
    "AMENDMENT_RECORD_NAME",
    "AmendmentError",
    "RunAmendmentV1",
    "amend_run",
    "current_epoch",
    "dossier_union",
    "epoch_directory",
    "epoch_problem_ids",
    "load_amendments",
    "load_epoch_dossier",
    "load_epoch_manifest",
    "load_epoch_run_input",
    "require_no_partial_amendment",
    "staged_amendment",
    "union_citable_blocks",
    "verify_epoch_run_input",
]
