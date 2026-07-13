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

# Metadata only: package source is resolved into a run, never vendored here.
# Exact versions deliberately do not appear in this catalog; a catalog entry
# states an admissible surface, while the import record freezes actual bytes.
_RUNTIME = {
    "motion": {
        "source": "runtime", "package": "motion", "slots": ["core-animation"],
        "license_class": "MIT", "qualification": "qualified",
        "conflicts": ["animejs", "gsap"],
        "exports": {
            "animate": "animate(target, keyframes, options?)",
            "scroll": "scroll(callbackOrAnimation, options?)",
            "inView": "inView(target, callback, options?)",
            "stagger": "stagger(duration?, options?)",
        },
        "patterns": ["animate an owned element", "bind an owned transform to scroll"],
        "restrictions": ["clean up inView and scroll subscriptions"],
    },
    "animejs": {
        "source": "runtime", "package": "animejs", "slots": ["core-animation"],
        "license_class": "MIT", "qualification": "qualified",
        "conflicts": ["motion", "gsap"],
        "exports": {
            "animate": "animate(targets, parameters)",
            "createTimeline": "createTimeline(parameters?)",
            "stagger": "stagger(value, parameters?)",
            "svg": "svg",
            "createDraggable": "createDraggable(target, parameters?)",
        },
        "patterns": ["create a bounded timeline", "animate an owned SVG"],
        "restrictions": ["pause and revert instances during cleanup"],
    },
    "gsap": {
        "source": "runtime", "package": "gsap", "slots": ["core-animation"],
        "license_class": "GSAP-standard", "qualification": "conditional",
        "conflicts": ["motion", "animejs"],
        "exports": {"gsap": "gsap", "ScrollTrigger": "ScrollTrigger"},
        "patterns": ["build a scoped gsap context", "pin one declared scene"],
        "restrictions": ["requires explicit GSAP licence permission", "revert context"],
    },
    "lenis": {
        "source": "runtime", "package": "lenis", "slots": ["scroll-coordination"],
        "license_class": "MIT", "qualification": "qualified", "conflicts": [],
        "exports": {"default": "new Lenis(options?)"},
        "patterns": ["create one page scroll coordinator"],
        "restrictions": ["destroy on cleanup", "disable for reduced motion"],
    },
    "paper-shaders": {
        "source": "runtime", "package": "@paper-design/shaders",
        "slots": ["visual-rendering"], "license_class": "Apache-2.0",
        "qualification": "qualified", "conflicts": ["ogl"],
        "exports": {
            "MeshGradient": "new MeshGradient(canvas, options?)",
            "PaperTexture": "new PaperTexture(canvas, options?)",
            "LiquidMetal": "new LiquidMetal(canvas, options?)",
        },
        "patterns": ["mount one prepared shader on an owned canvas"],
        "restrictions": ["destroy renderer", "static canvas fallback required"],
    },
    "ogl": {
        "source": "runtime", "package": "ogl", "slots": ["visual-rendering"],
        "license_class": "Unlicense", "qualification": "qualified",
        "conflicts": ["paper-shaders"],
        "exports": {
            "Renderer": "new Renderer(options?)", "Camera": "new Camera(gl, options?)",
            "Program": "new Program(gl, options)", "Mesh": "new Mesh(gl, options)",
            "Geometry": "new Geometry(gl, attributes?)", "Texture": "new Texture(gl, options?)",
        },
        "patterns": ["create one renderer for an owned canvas"],
        "restrictions": ["bounded RAF", "context-loss and static fallback required"],
    },
    "swup": {
        "source": "runtime", "package": "swup", "slots": ["navigation-transition"],
        "license_class": "MIT", "qualification": "qualified", "conflicts": [],
        "exports": {"default": "new Swup(options?)"},
        "patterns": ["manage transitions between server-rendered pages"],
        "restrictions": ["multi-page architecture only", "destroy on cleanup"],
    },
}


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


def runtime_catalog() -> dict[str, dict]:
    """Open runtime-provider metadata. Callers receive copies."""
    return {name: {**entry, "exports": dict(entry["exports"]),
                   "slots": list(entry["slots"]),
                   "conflicts": list(entry["conflicts"]),
                   "patterns": list(entry["patterns"]),
                   "restrictions": list(entry["restrictions"])}
            for name, entry in _RUNTIME.items()}


def capability_catalog() -> dict[str, dict]:
    """The one catalog, with built-in and runtime-resolved provider sources."""
    builtins = {
        name: {"source": "built-in", "package": None, "slots": ["styling-layout"],
               "qualification": "vendored", "conflicts": []}
        for name in _OPTIONS
    }
    return {**builtins, **runtime_catalog()}
