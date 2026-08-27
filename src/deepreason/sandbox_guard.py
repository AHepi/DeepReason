"""The ONE definition of the untrusted-code attribute boundary.

Four call sites execute model-authored Python behind an AST guard —
``oracle.py`` (the code-testing channel), ``programs.py`` (predicate eval),
``verification/simulation.py`` (the declarative worker) and the frozen worker
inside ``verification/contained.py`` (``sandboxed_python_v1``).  Before this
module each carried its own copy of the rule, and each copy had the same hole.

The hole, recorded so it is never reintroduced: every copy rejected attributes
whose name begins with an underscore, on the reasoning that the escape family
runs through ``().__class__.__base__.__subclasses__()``.  It does not have to.
``gi_frame``, ``f_back`` and ``f_globals`` carry no underscore, so

    def simulate(inputs, rng):
        box = []
        def g():
            box.append(gg.gi_frame.f_back.f_back.f_globals)
            yield 1
        gg = g()
        for v in gg:
            break
        w = box[0]              # the WORKER's own module globals

walked straight out of every sandbox in the repository and returned the real
``builtins`` module.  Demonstrated 2026-08-27 against two of the four:
``experiments/2026-08-27-change-execution-safety/`` SAFETY.md, findings E1-E3
(a file written outside the scratch directory, an arbitrary shell command, and
a TCP connection to the open internet — each while the verdict stayed ``pass``).

## Why a prefix rule and not a name allowlist

A name allowlist over attributes is the shape that first suggests itself, and
it is wrong here: model code legitimately reaches ``math.sqrt``,
``rng.randint``, ``items``/``append``/``join``, and the attributes of classes
the model itself defines.  An allowlist would have to enumerate a set that has
no boundary, and every omission is a false rejection the operator would feel
(REQUEST.md C8: "it doesn't break other modules").

What DOES have a boundary is the other side.  CPython namespaces its entire
frame/code/generator introspection surface under a small set of fixed
prefixes, plus dunders.  That set is CLOSED, enumerable, and — crucially —
checkable: ``tests/test_sandbox_guard.py`` walks the real attribute lists of
every object type reachable inside a sandbox (generator, coroutine, async
generator, traceback, frame, code, function, method, module, type) and asserts
this module rejects every public one.  That test goes red if a future CPython
adds an introspection attribute under a new prefix, which is the property a
hand-maintained denylist cannot have.

So the rule is a denylist over a closed set, with a re-derivable proof that the
set is closed — not a denylist over an open one, which is what failed.
"""

from __future__ import annotations

import ast

# Every prefix under which CPython exposes a frame, code object, function,
# traceback or generator/coroutine internal.  Order is irrelevant; the set is
# what matters, and `tests/test_sandbox_guard.py::test_the_prefix_set_covers_
# every_public_introspection_attribute` is what proves it complete.
#
#   _      dunders and private attributes (the historical rule, kept)
#   f_     frame: f_back, f_globals, f_locals, f_builtins, f_code, f_trace...
#   gi_    generator: gi_frame, gi_code, gi_yieldfrom, gi_running...
#   cr_    coroutine: cr_frame, cr_code, cr_await, cr_origin...
#   ag_    async generator: ag_frame, ag_code, ag_await, ag_running...
#   tb_    traceback: tb_frame, tb_next, tb_lasti, tb_lineno
#   co_    code object: co_consts, co_names, co_code, co_filename...
#   func_  Python-2 function aliases; free to forbid, nothing legitimate reads them
#   im_    Python-2 bound-method aliases; likewise
FORBIDDEN_ATTRIBUTE_PREFIXES: tuple[str, ...] = (
    "_",
    "f_",
    "gi_",
    "cr_",
    "ag_",
    "tb_",
    "co_",
    "func_",
    "im_",
)

# Attributes that leak a type or the type graph without a prefix to catch them.
# `mro` is a method on every class: `SomeClass.mro()` hands back `object`, from
# which `__subclasses__` is one dunder away.  The dunder is already blocked, so
# this is depth rather than the load-bearing rule — but a boundary that depends
# on the NEXT rule holding is not a boundary.
FORBIDDEN_ATTRIBUTE_NAMES: frozenset[str] = frozenset({"mro"})


def forbidden_attribute(name: str) -> bool:
    """Is ``obj.<name>`` outside the boundary for untrusted code?"""

    return name in FORBIDDEN_ATTRIBUTE_NAMES or name.startswith(
        FORBIDDEN_ATTRIBUTE_PREFIXES
    )


def forbidden_name(name: str) -> bool:
    """Is the bare identifier ``name`` outside the boundary?

    Underscore names only.  This is deliberately NOT the attribute rule: a
    local variable called ``f_total`` reaches nothing, while ``obj.f_total``
    is indistinguishable at parse time from a frame walk.
    """

    return name.startswith("_")


def attribute_violation(tree: ast.AST) -> str | None:
    """Return a diagnostic for the first out-of-boundary access, else ``None``.

    Attribute and Name rules only.  Each call site keeps its own additional
    rules (imports, ``**``, integer-literal caps, ``global``/``nonlocal``)
    because those differ by site and are not part of this boundary.
    """

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and forbidden_attribute(node.attr):
            return f"forbidden attribute .{node.attr}"
        if isinstance(node, ast.Name) and forbidden_name(node.id):
            return f"forbidden name {node.id}"
    return None


# The same rule as source text, for the ONE consumer that cannot import it: the
# frozen worker inside `verification/contained.py` runs in a scrubbed
# environment with no PYTHONPATH, so nothing in this repository is importable
# from inside the containment boundary.  Interpolating this string into the
# worker keeps ONE definition of the boundary instead of a copy that drifts —
# the modularity law (operator 2026-08-26) applied to a component that cannot
# import its own interface.  `tests/test_sandbox_guard.py` asserts the two
# agree on every input, so "generated from" is checked and not merely intended.
WORKER_GUARD_SOURCE: str = (
    "FORBIDDEN_ATTRIBUTE_PREFIXES = "
    + repr(FORBIDDEN_ATTRIBUTE_PREFIXES)
    + "\nFORBIDDEN_ATTRIBUTE_NAMES = "
    + repr(sorted(FORBIDDEN_ATTRIBUTE_NAMES))
    + """


def forbidden_attribute(name):
    return name in FORBIDDEN_ATTRIBUTE_NAMES or name.startswith(
        FORBIDDEN_ATTRIBUTE_PREFIXES
    )
"""
)


__all__ = [
    "FORBIDDEN_ATTRIBUTE_NAMES",
    "FORBIDDEN_ATTRIBUTE_PREFIXES",
    "WORKER_GUARD_SOURCE",
    "attribute_violation",
    "forbidden_attribute",
    "forbidden_name",
]
