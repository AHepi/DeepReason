"""One model's settings, as a document a human wrote.

The operator's words of 2026-09-01 (ledgered verbatim in
``experiments/2026-09-01-change-model-profile-registry/REQUEST.md``)::

    "Would this work for all unknown models as well? Surely creating agent.md
     would be better. Take this particular task out of the hands of the
     machine because we don't really know what future LLMs settings will be?"

    "model-profiles/glm-5.3/agent.md"

    "These questions miss the point. Harness is supposed to accommodate all
     possible future models and configurations"

So a document is ordinary Markdown -- a human writes whatever prose explains
their reasoning -- carrying EXACTLY ONE fenced block whose info string is
``deepreason-model-profile-v1``.  The prose is for the reader; only the block
is read.

Three properties this module exists to hold, each of which was a real failure
before it:

* **The declared ``model_id`` is the key, never the path.**  Provider ids carry
  colons (``deepseek-v4-pro:0813``, ``gpt-oss:120b``, ``qwen3.5:397b``).  An
  escaping scheme would be one more thing a human has to know, and the third
  operator quote above forbids designs that assume today's id shapes.
* **The block grammar is TOTAL.**  Zero blocks, two blocks and an unclosed
  block are each a typed error, never a guess.  `docs/map/SCHEMA.md` states the
  same rule for its own ``check:`` spans, and states the price of the
  alternative: 72 checks looked exactly like checks and never ran.
* **Absence stays absent.**  Every field but ``schema``, ``model_id`` and
  ``measured_on`` defaults to ``None`` or empty, and NOTHING here supplies a
  value the author did not write.  A default would be the machine deciding a
  model's settings, which is the whole thing being retired.

This module is pure: it parses text and validates it.  Where documents live and
how one is found is `DR-CON-model-profiles`'s registry half, not this file's.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal, Mapping

import yaml
from pydantic import ConfigDict, Field, ValidationError, field_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.frozen import FrozenDict, FrozenRecord

# The info string that marks the one block a loader reads.  Carries its own
# version so a future document shape can coexist with this one in the same
# directory rather than having to replace it in place.
FENCE_INFO = "deepreason-model-profile-v1"
SCHEMA_ID = "deepreason-model-profile.v1"

_FENCE_OPEN = f"```{FENCE_INFO}"
_FENCE_CLOSE = "```"


class ModelProfileError(ValueError):
    """A document that cannot be read, with a machine-readable reason.

    ``code`` is a string and deliberately never a number: ``cli/doctor.py``
    reads ``.code`` first and returns it as a ``failure_code`` constrained to
    ``^[A-Z][A-Z0-9_]*$``, and a numeric one normalises to a schema-invalid
    string that takes a whole battery down with the cause erased
    (`DR-SUB-llm` Traps, parked finding C5).
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class ReasoningFactsV1(FrozenRecord):
    """What is known about one model's reasoning knob.  DESCRIPTIVE ONLY.

    Nothing here may restrict, substitute for or veto a configured value --
    the operator's third quote above supersedes the earlier proposal that a
    profile should replace an undeclared value with its nearest declared one.
    ``documented_values`` is read by the PROBE, never by the dispatch path;
    the only field the harness acts on is ``extraction_value``, and it acts on
    it only where it would otherwise have supplied a constant of its own.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # The values this model's own provider documentation lists.
    documented_values: tuple[str, ...] = ()
    # What the split protocol's emission leg should send.  ``None`` means send
    # nothing, which is a DECLARATION ("omit the knob"), not an absence.
    extraction_value: str | None = None
    # Whether thinking can be switched off at all on this model.
    thinking_disablable: bool
    # The values measured to actually stop it thinking.  May be empty even
    # where the provider's vocabulary contains an off token: on glm-5.3
    # `none` does not stop the thinking, it stops the SEPARATION.
    disabling_values: tuple[str, ...] = ()
    # Per value: `side_channel`, `content`, or `absent`.  The field that would
    # have prevented this tranche's defect had it existed.
    trace_destination: Mapping[str, str] = Field(default_factory=FrozenDict)

    @field_validator("trace_destination", mode="after")
    @classmethod
    def _freeze_mapping(cls, value):
        return FrozenDict(value)


class ModelProfileV1(FrozenRecord):
    """One model's declared facts, as its ``agent.md`` states them."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        protected_namespaces=(),
    )

    schema_: Literal["deepreason-model-profile.v1"] = Field(
        SCHEMA_ID, alias="schema"
    )
    model_id: str = Field(min_length=1)
    # A profile with no date cannot go stale, and going stale visibly is the
    # point: a document that stops being true should fail a CHECK, not a RUN.
    measured_on: date

    reasoning: ReasoningFactsV1 | None = None
    context_window_tokens: int | None = Field(default=None, gt=0)
    max_output_tokens: int | None = Field(default=None, gt=0)
    tokens_per_second: float | None = Field(default=None, gt=0)
    # Can it obey "respond more compactly"?  A model that cannot meets the cap
    # ratchet's shrinking budget with the same output every time.
    can_compact: bool | None = None
    transport_notes: tuple[str, ...] = ()
    # How each claim above was measured.  Prose, but pointing at the record.
    evidence: tuple[str, ...] = ()
    # The command that re-verifies the claims above.
    probe: str | None = None

    @property
    def digest(self) -> str:
        """sha256 over the declared block, so rewording the prose is free.

        The record stamps this value (`DR-CON-model-profiles`), so it must
        move when a DECLARATION moves and stay still when a human improves a
        sentence.  Digesting the parsed record rather than the file bytes is
        what buys that.
        """

        return sha256_hex(canonical_json(self.model_dump(mode="json", by_alias=True)))


def extract_block(text: str) -> str:
    """The one declared block's body, or a typed error saying why not.

    Total by construction: every input yields a body or a code.  A fence of
    another kind (an ordinary ```yaml example in the prose) is invisible here,
    which is what lets a document show an example without declaring it.
    """

    lines = text.splitlines()
    openers = [i for i, line in enumerate(lines) if line.strip() == _FENCE_OPEN]
    if not openers:
        raise ModelProfileError(
            "MODEL_PROFILE_NO_BLOCK",
            f"no ```{FENCE_INFO} block; a model profile document declares "
            "exactly one",
        )
    if len(openers) > 1:
        raise ModelProfileError(
            "MODEL_PROFILE_MULTIPLE_BLOCKS",
            f"{len(openers)} ```{FENCE_INFO} blocks at lines "
            f"{[i + 1 for i in openers]}; exactly one is read and choosing "
            "between them is not the loader's to do",
        )
    start = openers[0]
    for end in range(start + 1, len(lines)):
        if lines[end].strip() == _FENCE_CLOSE:
            return "\n".join(lines[start + 1 : end]) + "\n"
    raise ModelProfileError(
        "MODEL_PROFILE_UNCLOSED_BLOCK",
        f"the ```{FENCE_INFO} block opened at line {start + 1} is never closed",
    )


def parse_document(text: str) -> ModelProfileV1:
    """Parse one ``agent.md`` into a validated profile."""

    body = extract_block(text)
    try:
        decoded: Any = yaml.safe_load(body)
    except yaml.YAMLError as error:
        raise ModelProfileError(
            "MODEL_PROFILE_MALFORMED", f"the declared block is not YAML: {error}"
        ) from error
    if not isinstance(decoded, Mapping):
        raise ModelProfileError(
            "MODEL_PROFILE_MALFORMED",
            f"the declared block must decode to a mapping, got "
            f"{type(decoded).__name__}",
        )
    try:
        return ModelProfileV1.model_validate(dict(decoded))
    except ValidationError as error:
        raise ModelProfileError(
            "MODEL_PROFILE_INVALID", f"the declared block is not a profile: {error}"
        ) from error
