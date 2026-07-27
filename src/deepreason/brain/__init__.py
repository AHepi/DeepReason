"""Optional explicit-path external memory.

The package affects attention only.  Importing it does not create a default
brain, inspect the filesystem, or attach memory to a harness run.
"""

from deepreason.brain.models import (
    ActivationSpec,
    BrainManifest,
    CandidateScore,
    LessonRecord,
    MemoryCard,
    MemoryPolicy,
    MemoryProvenance,
    MemoryRecord,
    MemoryRef,
    RetrievalReceipt,
    RetrievalResult,
    RunLocalBrainSnapshot,
)
from deepreason.brain.ingest import ingest_file, ingest_files
from deepreason.brain.retrieve import retrieve
from deepreason.brain.snapshot import replay_snapshot, snapshot_retrieval
from deepreason.brain.store import BrainStore

__all__ = [
    "ActivationSpec",
    "BrainManifest",
    "BrainStore",
    "CandidateScore",
    "LessonRecord",
    "MemoryCard",
    "MemoryPolicy",
    "MemoryProvenance",
    "MemoryRecord",
    "MemoryRef",
    "RetrievalReceipt",
    "RetrievalResult",
    "RunLocalBrainSnapshot",
    "ingest_file",
    "ingest_files",
    "replay_snapshot",
    "retrieve",
    "snapshot_retrieval",
]
