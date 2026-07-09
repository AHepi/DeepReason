"""Artifact schema (spec §1).

Untyped by construction (Def 3.2): there is NO ``kind`` field. Content is
opaque bytes + codec (Sigma*, Def 3.1); meaning is imposed by conjecture and
checked by program.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RefRole(str, Enum):
    DEPENDENCE = "dependence"  # contributes a support edge (this -> target) to dep
    MENTION = "mention"


class Ref(BaseModel):
    target: str  # artifact id
    role: RefRole


class Interface(BaseModel):
    """Attack surface + support declarations."""

    commitments: list[str] = Field(default_factory=list)  # commitment ids
    refs: list[Ref] = Field(default_factory=list)


class ProvenanceRole(str, Enum):
    CONJECTURER = "conjecturer"
    CRITIC = "critic"
    VARIATOR = "variator"
    SYNTHESIZER = "synthesizer"
    SEED = "seed"
    IMPORT = "import"
    USER = "user"
    # Self-calibration controller (controller.py): emits calibration_policy
    # artifacts. Provenance-only like every role — epistemically inert (D2);
    # a policy steers generation, never adjudication.
    CONTROLLER = "controller"
    # Experiment design (rules/experiment.py): emits input GENERATORS for
    # property oracles — def gen(k) sources the fuzz pass enumerates. Inert
    # like every role: a generator never decides anything (the frozen gate
    # admits every input, the frozen checker decides every violation); it
    # only chooses where the harness looks.
    EXPERIMENTER = "experimenter"


class Provenance(BaseModel):
    """Provenance is never a warrant (D2): epistemically inert by construction.

    ``school`` records the conditioning regime (§11.1) that generated the
    artifact; it may shape packs and scheduling, never adjudication.
    """

    role: ProvenanceRole
    school: str | None = None
    event_seq: int = 0


Codec = Literal["utf8", "json", "csv", "f64le", "i64le", "raw"] | str  # + "code:<lang>"


class Artifact(BaseModel):
    """id = sha256(canonical(content_ref, codec, interface)) — content-addressed."""

    id: str
    content_ref: str  # blob hash or inline string
    codec: str = "utf8"
    interface: Interface = Field(default_factory=Interface)
    warrants: list[str] = Field(default_factory=list)  # warrant ids carried
    provenance: Provenance

    @staticmethod
    def compute_id(content_ref: str, codec: str, interface: Interface) -> str:
        """sha256 over canonical JSON of (content_ref, codec, interface)."""
        from deepreason.canonical import canonical_json, sha256_hex

        payload = {
            "content_ref": content_ref,
            "codec": codec,
            "interface": interface.model_dump(mode="json"),
        }
        return sha256_hex(canonical_json(payload))
