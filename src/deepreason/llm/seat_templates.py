"""Formatting without code — a deliberately tiny template language.

The operator asked to "test freely how conjecturers respond to various input
format" (R9) and said "formatting can be done with the plugin" (R8). A Python
plugin can already do that, but changing a FORMAT should cost a text file
rather than a Python file, so an operator can vary one and re-run without
writing code.

**The power here is small on purpose, and the reason is the trust boundary
rather than taste.** An operator's plugin directory is TRUSTED — the operator
authors treadle tasks on the same basis — and a `.py` plugin in it executes.
That trust is a reason to keep the TEMPLATE kind unable to execute at all, not
a reason to widen it: an operator who wants code writes a plugin, and one who
wants a format writes a template that provably cannot run anything.

TWO CONSTRUCTS, AND NO OTHERS:

    {{ name }}            substitution, and one dot of traversal: {{ item.id }}
    {% for x in list %}…{% endfor %}

No expression evaluation, no calls, no filters, no imports, no indexing, no
comparison, no arithmetic, no traversal past one dot. The grammar is a
WHITELIST: a delimiter whose body does not match one of the forms above is a
typed refusal, never a best-effort render. A blacklist would have to
anticipate every escape; this has to anticipate none.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from deepreason.llm.seat_sections import SeatSectionError

TEMPLATE_SUFFIX = ".tmpl"

# One identifier, or one identifier and ONE attribute. Nothing else is a name.
_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DOTTED = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")
# The iterable may be a name or a ONE-DOT attribute, exactly as a
# substitution may. Anything else -- a call, an index, a filter -- is refused
# by falling off this pattern, which is the whitelist doing its work.
_FOR = re.compile(
    r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+"
    r"([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)$"
)
_ENDFOR = re.compile(r"^endfor$")

# Every delimiter in the source, in order. Matching the OPENERS too (rather
# than only well-formed pairs) is what makes an unclosed `{{` a refusal
# instead of literal text that silently ships to a model.
_TOKEN = re.compile(r"(\{\{.*?\}\}|\{%.*?%\}|\{\{|\{%)", re.S)


def _refuse(code: str, message: str) -> None:
    raise SeatSectionError(code, message)


def _lookup(name: str, context: Mapping[str, Any]) -> Any:
    if _NAME.match(name):
        if name not in context:
            _refuse(
                "SEAT_TEMPLATE_UNKNOWN_NAME",
                f"{name!r} is not in this template's declared context; "
                "available: " + ", ".join(sorted(context)),
            )
        return context[name]
    if _DOTTED.match(name):
        head, attribute = name.split(".")
        if head not in context:
            _refuse(
                "SEAT_TEMPLATE_UNKNOWN_NAME",
                f"{head!r} is not in this template's declared context",
            )
        base = context[head]
        if isinstance(base, Mapping):
            if attribute not in base:
                _refuse(
                    "SEAT_TEMPLATE_UNKNOWN_NAME",
                    f"{name!r} does not resolve",
                )
            return base[attribute]
        # A leading underscore would reach a private attribute, and
        # `__class__` from there reaches the whole interpreter.
        if attribute.startswith("_") or not hasattr(base, attribute):
            _refuse("SEAT_TEMPLATE_UNKNOWN_NAME", f"{name!r} does not resolve")
        value = getattr(base, attribute)
        if callable(value):
            _refuse(
                "SEAT_TEMPLATE_NOT_EXPRESSIBLE",
                f"{name!r} is callable; a template may not call anything",
            )
        return value
    _refuse(
        "SEAT_TEMPLATE_NOT_EXPRESSIBLE",
        f"{name!r} is not a name or a one-dot attribute. A template has "
        "substitution and iteration and nothing else: no calls, no filters, "
        "no operators, no indexing, no imports, no deeper traversal.",
    )


def _tokens(source: str) -> list:
    out = []
    position = 0
    for match in _TOKEN.finditer(source):
        if match.start() > position:
            out.append(("text", source[position : match.start()]))
        body = match.group(0)
        if body in ("{{", "{%"):
            _refuse(
                "SEAT_TEMPLATE_UNCLOSED",
                f"unclosed {body!r} at offset {match.start()}",
            )
        if body.startswith("{{"):
            out.append(("name", body[2:-2].strip()))
        else:
            out.append(("tag", body[2:-2].strip()))
        position = match.end()
    if position < len(source):
        out.append(("text", source[position:]))
    return out


def _render(tokens: list, index: int, context: Mapping[str, Any], out: list) -> int:
    while index < len(tokens):
        kind, body = tokens[index]
        if kind == "text":
            out.append(body)
            index += 1
        elif kind == "name":
            out.append(str(_lookup(body, context)))
            index += 1
        elif _ENDFOR.match(body):
            return index
        else:
            match = _FOR.match(body)
            if match is None:
                _refuse(
                    "SEAT_TEMPLATE_NOT_EXPRESSIBLE",
                    f"{{% {body} %}} is not a construct this template "
                    "language has; only `for x in list` and `endfor` are.",
                )
            variable, iterable_name = match.groups()
            iterable = _lookup(iterable_name, context)
            if isinstance(iterable, (str, bytes)) or not hasattr(
                iterable, "__iter__"
            ):
                _refuse(
                    "SEAT_TEMPLATE_NOT_ITERABLE",
                    f"{iterable_name!r} is not a sequence to iterate",
                )
            body_start = index + 1
            end = _skip(tokens, body_start)
            for item in iterable:
                scoped = dict(context)
                scoped[variable] = item
                _render(tokens, body_start, scoped, out)
            index = end + 1
    return index


def _skip(tokens: list, index: int) -> int:
    """The index of the `endfor` closing the loop that opened before `index`."""

    depth = 0
    while index < len(tokens):
        kind, body = tokens[index]
        if kind == "tag":
            if _FOR.match(body):
                depth += 1
            elif _ENDFOR.match(body):
                if depth == 0:
                    return index
                depth -= 1
        index += 1
    _refuse("SEAT_TEMPLATE_UNCLOSED", "a `for` has no matching `endfor`")
    return index  # pragma: no cover - _refuse always raises


def render_template(source: str, context: Mapping[str, Any]) -> str:
    """Expand one template against a bounded, caller-declared context."""

    out: list[str] = []
    tokens = _tokens(source)
    _render(tokens, 0, context, out)
    return "".join(out)
