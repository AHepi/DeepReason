"""Work that runs AFTER a criticism pass and is not criticism.

A tiny registry, and it exists to keep two rules true at once that a direct
call cannot.

1. `DR-SEAM-rules-x-scratch` rule 6 forbids widening the CRITICISM side, so a
   channel that reacts to criticism must be a reader outside `rules/`
   (Q3 road B, operator 2026-08-30).
2. `tests/test_successor_law_line.py` forbids any DECIDING package —
   `scheduler`, `adjudication`, `informal`, `rules`, `workflow`, `workflows` —
   from naming the successor machinery at all, with an EMPTY permitted-exception
   list. That check is blunt on purpose: it is about coupling, not about
   spelling, and a rank read written without the forbidden words would slip
   past it, so nothing is allowed to argue its way onto the list.

A direct `scheduler -> deepreason.successor` call satisfies (1) and breaks (2).
So the scheduler names a HOOK POINT instead of a feature: it says "a criticism
pass just finished" and knows nothing about who listens. The coupling that rule
is protecting against genuinely is not created — the scheduler cannot read a
successor question, cannot reach the registry, and would behave identically if
the successor package were deleted from the build.

This is the modularity law's own shape (2026-08-26, "every behavior a run can
vary is reachable as CONFIGURATION or a REGISTERED, VERSIONED ARTIFACT — never
by editing code"): a second post-criticism reader is a registration, not an
edit to whatever runs cycles.

WHAT A HOOK MAY AND MAY NOT DO. It may WRITE — that is the difference between
this and `Scheduler.run`'s `on_cycle`, which is documented read-only and must
not register. It may NOT decide: nothing here may change a status, a rank, an
admission or a warrant, and the law-line tests are what hold that for the one
registered hook today. A hook that raises is REPORTED, never fatal: this runs
advisory channels, and an advisory channel must not be able to kill a cycle.
"""

from __future__ import annotations

from collections.abc import Callable

# VERSIONED as a whole, like the signal registry and the successor destinations:
# what a hook point MEANS moves under a version, while which hooks are
# registered is free configuration.
AFTER_CRITICISM_REGISTRY_VERSION = "aftercycle-hooks.v1"

# The hooks THIS BUILD ships, as import paths resolved at first use.
#
# Declared here rather than registered by the hook's own package on import,
# and that is not a style choice: it was MEASURED. With the successor package
# registering itself, the hook was armed only if something had already imported
# `deepreason.config` -- importing `deepreason.scheduler.scheduler` alone left
# `after_criticism_hooks()` EMPTY, so on some import orders the channel would
# have been silently dead. A channel that works by import accident is the exact
# defect this hook point exists to close.
#
# Resolved LAZILY, inside `run_after_criticism`, because the hook's package
# imports this module: a module-scope import here would be a cycle.
_DECLARED_HOOKS: tuple[tuple[str, str], ...] = (
    ("successor-questions", "deepreason.successor:dispatch_recorded_proposals"),
)

_AFTER_CRITICISM: dict[str, Callable] = {}
_RESOLVED = False


def register_after_criticism(name: str, hook: Callable) -> None:
    """Register one post-criticism reader under a stable name.

    Keyed by name so a re-import cannot register the same hook twice — modules
    are imported once, but a test that reloads one would otherwise double-run
    it, and a doubled advisory write is the kind of defect that looks like a
    provider fault.
    """
    if not name:
        raise ValueError("an after-criticism hook needs a name")
    _AFTER_CRITICISM[name] = hook


def unregister_after_criticism(name: str) -> None:
    _AFTER_CRITICISM.pop(name, None)


def _resolve_declared() -> None:
    """Import and register every declared hook, once per process.

    A declared hook that cannot be imported is SKIPPED rather than fatal: a
    build that ships without one of these packages must still run cycles.
    """
    global _RESOLVED
    if _RESOLVED:
        return
    _RESOLVED = True
    import importlib

    for name, path in _DECLARED_HOOKS:
        module_name, _, attribute = path.partition(":")
        try:
            module = importlib.import_module(module_name)
            hook = getattr(module, attribute)
        except (ImportError, AttributeError):
            continue
        _AFTER_CRITICISM.setdefault(name, hook)


def after_criticism_hooks() -> tuple[str, ...]:
    """The registered names, sorted. The order hooks run in."""
    _resolve_declared()
    return tuple(sorted(_AFTER_CRITICISM))


def run_after_criticism(harness, config, *, on_error=None) -> tuple[str, ...]:
    """Run every registered hook. Returns the names that raised.

    `on_error(name, exception)` is how a caller records a failure in whatever
    way it already records failures — the scheduler has `_drop`, the P1 loop has
    a diagnostics list, and this module should not learn about either.
    """
    _resolve_declared()
    failed: list[str] = []
    for name in after_criticism_hooks():
        try:
            _AFTER_CRITICISM[name](harness, config)
        except Exception as exc:  # advisory: report, never fatal to a cycle
            failed.append(name)
            if on_error is not None:
                on_error(name, exc)
    return tuple(failed)
