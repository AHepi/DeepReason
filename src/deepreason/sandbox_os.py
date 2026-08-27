"""The OS-level containment probe, shared by every backend that runs untrusted code.

The language boundary (:mod:`deepreason.sandbox_guard`) decides what
model-authored source may REFER to.  This module decides what the process
running it may REACH, and it exists because the language boundary failed once:
on 2026-08-27 a frame walk carried model code straight through every AST guard
in this repository to the real ``builtins``
(``experiments/2026-08-27-change-execution-safety/SAFETY.md``).

The lesson recorded there is not "the guard was wrong" — it is that a
containment property resting on ONE layer is one bug away from absent.  The
network namespace is what makes that concrete: in the same reproduction, with a
full language escape in hand and ``os.system`` available, the network was still
gone, because that property never depended on the language boundary at all.

So the probe lives here, once, and both backends that execute untrusted Python
use it: ``verification/contained.py`` (``sandboxed_python_v1``, opt-in) and
``oracle_sandbox.py`` (the code-testing channel, on by default and — until this
module — carrying no OS boundary whatsoever).

**Availability is not assumed.** The probe runs the real interpreter inside the
candidate namespace, so "available" means the exact execution shape works, not
that an ``unshare`` binary exists.  The two backends then differ, deliberately:
the opt-in simulation runner FAILS CLOSED (no namespace, no execution), while
the always-on code-testing channel degrades — a host without user namespaces
must still be able to test code, which is the operator's standing ruling
("Otherwise how is an LLM supposed to test code").  Degrading is safe to do
only because it is VISIBLE: :func:`network_denial_available` is what the tests
assert, so the difference between the two states is a fact a reader can check
rather than an assumption they must make.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

# Cached probe outcome: None = not yet probed, () = unavailable, otherwise the
# exact command prefix that denies network access.
_NETWORK_DENIAL_PREFIX: tuple[str, ...] | None = None

# Tried in order. The first form works unprivileged by creating a user
# namespace alongside the network namespace; the second needs CAP_SYS_ADMIN and
# is the fallback for hosts that grant it but forbid user namespaces.
_CANDIDATE_FLAGS: tuple[tuple[str, ...], ...] = (
    ("--map-root-user", "--net"),
    ("--net",),
)

_PROBE_TIMEOUT_SECONDS = 20


def network_denial_prefix() -> tuple[str, ...]:
    """Return the probed command prefix that denies network access, or ``()``.

    Cached per process: the probe costs a subprocess launch, and the answer
    cannot change within one run.
    """

    global _NETWORK_DENIAL_PREFIX
    if _NETWORK_DENIAL_PREFIX is not None:
        return _NETWORK_DENIAL_PREFIX
    prefix: tuple[str, ...] = ()
    unshare = shutil.which("unshare")
    if unshare is not None:
        for flags in _CANDIDATE_FLAGS:
            candidate = (unshare, *flags, "--")
            try:
                probe = subprocess.run(  # noqa: S603 - fixed probe command
                    [*candidate, sys.executable, "-c", "raise SystemExit(0)"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=_PROBE_TIMEOUT_SECONDS,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if probe.returncode == 0:
                prefix = candidate
                break
    _NETWORK_DENIAL_PREFIX = prefix
    return prefix


def network_denial_available() -> bool:
    return bool(network_denial_prefix())


def reset_probe_cache() -> None:
    """Forget the cached probe. For tests that simulate an unequipped host."""

    global _NETWORK_DENIAL_PREFIX
    _NETWORK_DENIAL_PREFIX = None


__all__ = [
    "network_denial_available",
    "network_denial_prefix",
    "reset_probe_cache",
]
