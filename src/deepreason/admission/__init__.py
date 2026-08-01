"""Evidence admission: documents become durable, citable dossier material.

Admission is the only path from user-supplied bytes to a dossier whose
digest joins frozen run identity.  Everything here is deterministic: the
same input bytes and the same ``PARSER_VERSION`` mint the same dossier
digest on every machine, forever.  Nothing enters silently; refusals are
typed records inside the dossier itself.
"""

from deepreason.admission.parse import (
    PARSER_VERSION,
    AdmissionError,
    AdmissionInput,
    AdmissionReport,
    admit_sources,
    sniff_media_type,
)
from deepreason.admission.store import (
    AdmissionStore,
    admission_store,
)

__all__ = [
    "PARSER_VERSION",
    "AdmissionError",
    "AdmissionInput",
    "AdmissionReport",
    "AdmissionStore",
    "admission_store",
    "admit_sources",
    "sniff_media_type",
]
