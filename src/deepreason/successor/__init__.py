"""Successor questions: the declared interface, and nothing else.

A criticism may propose the question it thinks should be asked NEXT. The
proposal is OPTIONAL, it is never required and never penalized, and what
happens to it is configuration:

- `resolve` names the destination a run selects; `route` sends a filled
  question there. The shipped default is the scratchpad, linked to the problem
  the question was proposed under.
- `mint` is the second road -- the proposal becomes a problem -- and it is off
  unless a run switches it on.
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
from deepreason.successor.route import route

# The DECLARED interface. `minting_notices` and the registration helpers are
# reachable beside it as ordinary module attributes; this tuple is the surface a
# consumer may rely on, pinned by tests/test_successor_registry.py.
__all__ = [
    "DESTINATIONS",
    "SUCCESSOR_DESTINATION_REGISTRY_VERSION",
    "mint",
    "resolve",
    "route",
    "unknown_destination_notices",
]
