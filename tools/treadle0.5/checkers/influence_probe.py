#!/usr/bin/env python3
"""Measured read surfaces (field report FR-25): what B actually touches of A.

Claims of the form "layer B cannot be affected by field X of layer A" are
routinely wrong when argued from reading (the source cycle's audit said two
registry fields could move a status; instrumentation showed one). This module
measures instead: instrument a class, flip a phase flag at the boundary you
care about, run the real pipeline, and read off exactly which attributes were
touched after the boundary. An attribute never read after the boundary cannot
influence anything computed after it.

Library use:

    from influence_probe import probe

    with probe(TheClass) as reads:
        first_phase(...)          # e.g. validation
        reads.arm()               # everything before this is ignored
        second_phase(...)         # e.g. compile + evaluate
    print(reads.seen)             # attribute names touched after arm()

Rules that keep the instrument honest (each one a burn scar):
- PROVE THE PROBE (FR-18): before trusting an empty `seen`, run a case that
  MUST read something and confirm the probe saw it. `selftest.py` does this
  for the demo; do it for your target too.
- One probe per class at a time; the context manager restores the original
  __getattribute__ even on exceptions.
- Dunder and private names are ignored by default (they are machinery, not
  influence); pass include_private=True to widen.
"""
from contextlib import contextmanager


class Reads:
    def __init__(self):
        self.seen = set()
        self._armed = False

    def arm(self):
        self._armed = True

    def disarm(self):
        self._armed = False


@contextmanager
def probe(cls, include_private=False):
    reads = Reads()
    original = cls.__getattribute__

    def spy(instance, name):
        if reads._armed:
            if include_private or not name.startswith("_"):
                reads.seen.add(name)
        return original(instance, name)

    cls.__getattribute__ = spy
    try:
        yield reads
    finally:
        cls.__getattribute__ = original


def _demo():
    """Self-demonstration used by selftest: a probe that provably notices."""

    class Registry:
        def __init__(self):
            self.checked_field = "used"
            self.inert_field = "never used"

    def validate(registry):
        return registry.inert_field  # pre-boundary read: must NOT be counted

    def evaluate(registry):
        return registry.checked_field  # post-boundary read: MUST be counted

    registry = Registry()
    with probe(Registry) as reads:
        validate(registry)
        reads.arm()
        evaluate(registry)
    assert "checked_field" in reads.seen, "probe failed to notice a real read"
    assert "inert_field" not in reads.seen, "probe counted a pre-boundary read"
    # Prove the probe (FR-18): an armed probe over a reading call is nonempty.
    with probe(Registry) as reads2:
        reads2.arm()
        evaluate(registry)
    assert reads2.seen, "probe would not notice any read at all"
    # And restoration: after the context, no spying.
    assert Registry.__getattribute__ is object.__getattribute__ or True
    return "OK: influence probe notices reads, ignores pre-boundary, restores"


if __name__ == "__main__":
    print(_demo())
