"""The successor-question registry: where a proposed question GOES, and what
switching the minting road on discloses.

The operator's law of 2026-08-29 (CLAUDE.md, "Successor questions: optional to
propose, routed by pluggable destination, minting gated off-by-default")::

    "This should be an optional field the LLM can fill in. Not enforceable. If
     it is filled in, it goes to scratchpad by default, linked to the problem
     it was proposed under and visible by conjecturers. But build the wiring to
     mint, with the option to switch it on with a flag saying something like
     'may cause critics to fully consume conjecturer role'. Switch off by
     default. Again, maximum configurable surface. The scratch pad option must
     function like a plugin that allows for movement elsewhere as well. Again,
     the modularity thing and Max config thing."

Two mappings, both DECLARATIONS rather than wiring, in the shape
`DR-INV-signal-contract` establishes for signals and `channels.py` and
`discharge/policy.py` already ship:

- ``DESTINATIONS`` says where a filled question goes. "Like a plugin that
  allows for movement elsewhere" is the whole requirement: a new destination
  enters by registering a row, and every consumer reaches it through
  ``resolve`` without being edited.
- ``GATES`` says what a per-run switch permits and what its enablement
  discloses. The minting gate's ``warning`` carries the operator's own words
  verbatim, because the law names the text rather than the idea.

What this module is NOT. It decides ROUTING and DISCLOSURE and nothing else.
There is no numeric field on a declaration, so there is no rank, weight or
admission score for any configuration to set: a critic that fills the field
earns nothing and a critic that leaves it empty pays nothing
(`DR-CON-conjecture-kinds` R-g, the formalism-optional law, applied to this
channel; pinned by tests/test_successor_law_line.py).
"""

from __future__ import annotations

from dataclasses import dataclass, fields as _dataclass_fields
from typing import get_type_hints


@dataclass(frozen=True)
class SuccessorDeclaration:
    """One registered row: a destination a question may go to, or a gate a run
    may switch on.

    ``default`` answers exactly one question for both kinds of row -- what a
    configuration that names nothing gets. For a destination that is "this is
    the shipped fallback"; for a gate it is "this gate is on when nothing says
    otherwise". ``enforcement`` names where the row is actually READ, and where
    a switch cannot yet be SET it must say so rather than name one that does not
    exist -- the failure mode this repo has already paid for once, in an
    allocation controller whose 47 decisions reached no dispatch. That is a
    convention a row's author keeps, NOT an enforced property: no test and no
    map check reads a `SuccessorDeclaration`'s ``enforcement``, so a false string
    here goes unnoticed until a reader follows it. `DR-INV-evidence-channels`
    carries the check this registry still lacks -- it asserts every channel row's
    toggle is a real `Config` field, which is the assertion no gate row here
    could satisfy while Q1 is unanswered.

    ``routes`` is producer-agnostic on purpose: it says what the row DOES, never
    which subsystem proposed the question, because a consumer that has to know
    the producer has left the contract (`DR-INV-signal-contract`).
    """

    id: str
    routes: str
    default: bool
    enforcement: str
    authority: str
    warning: str = ""


# The registry. Versioned as a whole under the signal contract's VERSIONED
# layer: a change to what these rows MEAN is a versioned change; which row a
# given run selects is FREE configuration.
SUCCESSOR_DESTINATION_REGISTRY_VERSION = "successor-destinations.v1"

# The Config field a destination row is selected by, and the one a gate is
# switched with. ONE field each for every row present and future: a new
# destination gets its selector by registering, never by adding a knob, which
# is what makes "customisation is easy" a property of the design rather than a
# promise about future authors.
SUCCESSOR_DESTINATION_FIELD = "SUCCESSOR_QUESTION_DESTINATION"
SUCCESSOR_MINTING_FIELD = "SUCCESSOR_MINTING_ENABLED"

DEFAULT_DESTINATION_ID = "scratchpad.v1"
MINTING_GATE_ID = "minting.v1"

DESTINATIONS: dict[str, SuccessorDeclaration] = {
    DEFAULT_DESTINATION_ID: SuccessorDeclaration(
        id=DEFAULT_DESTINATION_ID,
        routes=(
            "one advisory scratch block carrying the question, linked to the "
            "problem it was proposed under and readable by conjecturer seats "
            "through the ordinary attention pack"
        ),
        default=True,
        enforcement="deepreason.successor.route.route -> ScratchService.create_block",
        authority='operator 2026-08-29: "it goes to scratchpad by default"',
    ),
}

GATES: dict[str, SuccessorDeclaration] = {
    MINTING_GATE_ID: SuccessorDeclaration(
        id=MINTING_GATE_ID,
        routes=(
            "a filled question may additionally MINT a problem carrying the "
            "SUCCESSOR trigger and naming both its parents"
        ),
        default=False,
        enforcement=(
            "deepreason.successor.mint.mint -> registry.minting_enabled -> "
            f"getattr(config, {SUCCESSOR_MINTING_FIELD!r}, this row's default). "
            f"deepreason.config.Config declares no {SUCCESSOR_MINTING_FIELD} "
            "field and forbids extras, so no run configured through it can "
            "switch this gate on until the Q1 frozen-surface-4 grant lands "
            "(PARKED.md Q1); today only a duck-typed configuration object can"
        ),
        authority='operator 2026-08-29: "Switch off by default"',
        # The operator named the TEXT, not the idea, so it is carried verbatim
        # and never paraphrased: a reader checking this row against CLAUDE.md
        # must find the same words.
        warning="may cause critics to fully consume conjecturer role",
    ),
}


# Declaration and WRITER are registered together, so "add a destination" is one
# call and never an edit to whatever routes. The two maps stay separate because
# the declaration is the VERSIONED contract while the writer is ordinary code
# implementing it: a row may be declared before anything can serve it, and that
# state is disclosed at the point of use rather than hidden.
_WRITERS: dict[str, object] = {}


def register_destination(declaration: SuccessorDeclaration, writer=None) -> None:
    """Register one destination row, optionally with the writer serving it."""
    DESTINATIONS[declaration.id] = declaration
    if writer is not None:
        _WRITERS[declaration.id] = writer


def unregister_destination(destination_id: str) -> None:
    """Remove a registered row and its writer.

    The shipped default cannot be removed: a registry with no fallback would
    turn an unknown selector from a disclosure into a failure.
    """
    if destination_id == DEFAULT_DESTINATION_ID:
        raise ValueError("the shipped default destination cannot be unregistered")
    DESTINATIONS.pop(destination_id, None)
    _WRITERS.pop(destination_id, None)


def writer_for(destination_id: str):
    """The writer registered for this row, or None if the row has no server."""
    return _WRITERS.get(destination_id)


def declaration_field_types() -> dict[str, object]:
    """The declaration's own field annotations, resolved.

    Exposed so the law-line test can assert the ABSENCE of a numeric field over
    the MODEL rather than over today's rows -- a row added tomorrow cannot
    introduce a weight the model does not allow.
    """
    hints = get_type_hints(SuccessorDeclaration)
    return {f.name: hints[f.name] for f in _dataclass_fields(SuccessorDeclaration)}


def _selected_destination_id(config) -> str:
    raw = getattr(config, SUCCESSOR_DESTINATION_FIELD, None)
    if raw is None:
        return DEFAULT_DESTINATION_ID
    text = str(raw).strip()
    return text or DEFAULT_DESTINATION_ID


def resolve(config) -> SuccessorDeclaration:
    """The destination row this configuration selects.

    An id naming no registered row FALLS BACK to the shipped default and is
    disclosed by `unknown_destination_notices`, never refused: the
    all-configurations law (operator, 2026-08-12) applied to a selector, and
    the same rule `DR-INV-signal-contract` states for an unknown policy id.
    """
    return DESTINATIONS.get(_selected_destination_id(config), DESTINATIONS[DEFAULT_DESTINATION_ID])


def unknown_destination_notices(config):
    """A selector naming no registered destination, as a typed notice.

    ``CompileNoticeV1`` is imported HERE, at call time, rather than at module
    scope: the registry must stay importable without the manifest module, or a
    consumer that only wants to know where a question goes acquires a
    dependency on the thing that compiles manifests. The type is reused
    verbatim and never modified, exactly as `channels.py` reuses it.
    """
    from deepreason.run_manifest import CompileNoticeV1

    selected = _selected_destination_id(config)
    if selected in DESTINATIONS:
        return ()
    known = ", ".join(sorted(DESTINATIONS))
    return (
        CompileNoticeV1(
            code="SUCCESSOR_DESTINATION_UNKNOWN",
            message=(
                f"{SUCCESSOR_DESTINATION_FIELD} names no registered successor "
                f"destination {selected!r}; questions route to "
                f"{DEFAULT_DESTINATION_ID!r}"
            ),
            pointer=f"/{SUCCESSOR_DESTINATION_FIELD}",
            resolution=f"remove it, or name one of: {known}",
        ),
    )


def minting_enabled(config) -> bool:
    """Is the minting road switched on for this run? Off unless named."""
    return bool(getattr(config, SUCCESSOR_MINTING_FIELD, GATES[MINTING_GATE_ID].default))


def minting_notices(config):
    """The operator's own warning, typed, when the minting gate is on.

    Never a refusal and never silence (the ungated-seats law, 2026-08-28):
    switching a gate on is always permitted and always discloses. An off gate
    returns no notice, because a run that changed nothing has nothing to
    disclose.
    """
    from deepreason.run_manifest import CompileNoticeV1

    if not minting_enabled(config):
        return ()
    gate = GATES[MINTING_GATE_ID]
    return (
        CompileNoticeV1(
            code="SUCCESSOR_MINTING_ENABLED",
            message=(
                f"{SUCCESSOR_MINTING_FIELD} is on: a criticism may mint a new "
                f"problem -- {gate.warning}"
            ),
            pointer=f"/{SUCCESSOR_MINTING_FIELD}",
            resolution=f"set {SUCCESSOR_MINTING_FIELD}=false to route questions only",
        ),
    )
