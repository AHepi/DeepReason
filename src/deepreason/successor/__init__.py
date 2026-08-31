"""Successor questions: the declared interface, and nothing else.

A criticism may propose the question it thinks should be asked NEXT. The
proposal is OPTIONAL, it is never required and never penalized, and what
happens to it is configuration:

- `resolve` names the destination a run selects; `route` sends a filled
  question there. The shipped default is the scratchpad, linked to the problem
  the question was proposed under.
- `mint` is the second road -- the proposal becomes a problem -- and it is off
  unless a run switches it on.
- `dispatch_recorded_proposals` is the PRODUCTION entry: a reader outside
  `rules/` that walks what criticism already recorded and routes what it
  finds. It is idempotent over an unchanged record, so a resumed run
  re-dispatches nothing.
- `unknown_destination_notices` discloses a selector naming no registered row,
  and `minting_notices` discloses the gate's own warning when it is on. Neither
  ever refuses.

Consumers import THIS module. A consumer reaching past it into a row's
internals, or branching on which row it got, has left the contract
(`DR-INV-signal-contract`) and `tests/test_successor_registry.py` is where that
shows up.
"""

from deepreason.successor.mint import mint
from deepreason.successor.registry import (
    DESTINATIONS,
    SUCCESSOR_DESTINATION_REGISTRY_VERSION,
    GATES,
    SuccessorDeclaration,
    minting_enabled,
    minting_notices,
    register_destination,
    resolve,
    unknown_destination_notices,
    unregister_destination,
    writer_for,
)
from deepreason.successor.reader import (
    dispatch_recorded_proposals,
    recorded_proposals,
)
from deepreason.successor.route import route

# The DECLARED interface. `minting_notices`, `recorded_proposals` and the
# registration helpers are reachable beside it as ordinary module attributes;
# this tuple is the surface a consumer may rely on. It is pinned by the
# `__all__` check in docs/map/CON-successor-questions.md, which
# tools/docs_verify.py runs, and by
# tests/test_successor_registry.py::test_the_declared_interface_is_exactly_seven_names,
# so dropping a name here goes red in both instruments.
#
# `dispatch_recorded_proposals` joined it on 2026-08-30 (Q3 road B): it is the
# name a production caller uses, so it is part of the contract rather than an
# implementation detail beside it.
__all__ = [
    "DESTINATIONS",
    "SUCCESSOR_DESTINATION_REGISTRY_VERSION",
    "dispatch_recorded_proposals",
    "mint",
    "resolve",
    "route",
    "unknown_destination_notices",
]
