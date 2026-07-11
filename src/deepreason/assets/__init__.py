"""Vendored front-end capability catalog.

Browser verification runs with networking disabled (browser.py renders via
set_content, no fetches), so reusable infrastructure must live IN the
repository — a CDN link would silently load nothing. This package holds a
small catalog, not one compulsory framework: a single universal visual
system would act as a shared stylistic attractor across schools and runs
(the same failure surface capture control exists to police).

Two tiers, deliberately different in governance:

- ``baseline()`` — a TECHNICAL floor (box-model sanity, media bounds,
  focus visibility, reduced-motion respect). Injected universally by the
  assembler and documented as such; it makes no aesthetic decision.
- ``catalog()`` — named OPTIONS ("classless" semantic base styles,
  "layout" primitives, ...). A design artifact must explicitly select
  them in its manifest; selections land in component contracts, the
  assembled artifact's dependence refs, and the replay log — visible,
  criticizable, replaceable.

Contents are original to this repository (repo license applies); catalog
text is read once per process and content-addressed downstream, so
assembly stays byte-for-byte replayable.
"""

from functools import lru_cache
from importlib import resources

_OPTIONS = ("classless", "layout")


@lru_cache(maxsize=None)
def _read(name: str) -> str:
    return (resources.files(__package__) / f"{name}.css").read_text()


def baseline() -> str:
    """The universal technical floor (see module docstring)."""
    return _read("baseline")


def catalog() -> dict[str, str]:
    """Selectable options: name -> CSS text."""
    return {name: _read(name) for name in _OPTIONS}


def catalog_names() -> set[str]:
    return set(_OPTIONS)
