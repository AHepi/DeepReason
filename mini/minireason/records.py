"""What a mini seat writes when it is not proposing a conjecture: a RECORD,
never an artifact.

Implements S4 (R4, R13, R14, C9) of the mini isolation programme. R4 is the
operator's "a new kind of artifact that generates commitments on conjectures,
but does not force a strict format"; R13 is "within mini, criticism can't
overturn anything"; R14 is "the point is content generation for now".

WHY A RECORD AND NOT AN ARTIFACT. Everything in the authority layer -- rank,
admission, immunity, attack edges, refutation, status -- reads
`state.artifacts`. A commitment proposal (and, from T5, a criticism) written
as an artifact would sit in that map with a status the adjudicator assigns
it, and the road from there to "shape buys standing" is one careless read
long. Written as a Measure event carrying a marker, the kind, the artifact it
is about and a content-addressed blob, it is in the record -- typed,
append-only, replayable, spend attached -- and NOWHERE the authority layer
looks. "A proposal is RECORDED, not registered" (SPEC S4) is then a property
of the record's shape, not of anyone's restraint.

The other road, an artifact with a new provenance role, was measured and
closed: `tools/blast_radius.py` reads widening `Provenance` as CONTACT on the
harness surface, and no grant exists (T4 step 32).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from deepreason.canonical import canonical_json

#: Every mini record's first input. A reader can find them in any root
#: without knowing this module's vocabulary.
MINI_RECORD_MARKER = "mini:record"
#: A record dropped at the point of use, and why -- disclose, never die.
MINI_RECORD_DROPPED_MARKER = "mini:record-dropped"


class MiniRecordError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class MiniRecordV1:
    """One thing a mini seat wrote, read back from the record.

    `ref` is the blob's content address for a record and the artifact id for
    an artifact, so the pool a seat is shown can carry both in one order.
    NO score, rank, weight, confidence, priority, authority or severity: the
    shape may never buy standing (the formalism-optional law), and there is
    nothing here for an authority path to read even by mistake.
    """

    seq: int
    kind: str
    ref: str
    about: tuple[str, ...]
    content: str


def _payload(kind: str, about: str | None, body: str, named: str | None) -> bytes:
    payload = {"kind": kind, "about": about, "body": body}
    if named is not None and named != about:
        # What the seat WROTE as its target, when the stage bound it to the
        # one it was shown: kept, so the record never loses the seat's words.
        payload["named"] = named
    return canonical_json(payload)


def record_mini_output(session, kind: str, *, body: str, about: str | None = None,
                       named: str | None = None, spend=None):
    """Write one record: a Measure event naming the kind, what it is about and
    the blob holding its body. Returns the event.

    `about`, when given, MUST name an artifact present in this run; a record
    about nothing in the run is not a record about a conjecture, and it is
    DROPPED with a typed event saying so rather than written with a dangling
    reference the next reader would trip on. `spend` lands on whichever event
    is written, exactly once, so the meter and the log still agree (G1).
    """

    if about is not None and about not in session.harness.state.artifacts:
        session.measure(
            [MINI_RECORD_DROPPED_MARKER, "MINI_RECORD_ABOUT_UNKNOWN", f"kind:{kind}",
             f"about:{about}"],
            spend,
        )
        return None
    ref = session.blobs.put(_payload(kind, about, body, named))
    inputs = [MINI_RECORD_MARKER, f"kind:{kind}"]
    if about is not None:
        inputs.append(f"about:{about}")
    inputs.append(f"blob:{ref}")
    return session.measure(inputs, spend)


def _field(inputs, prefix: str) -> str | None:
    for item in inputs:
        if item.startswith(prefix):
            return item[len(prefix):]
    return None


def mini_records(session) -> tuple[MiniRecordV1, ...]:
    """Every record in this run, in record order, bodies read back from their
    blobs. Reads the log and the blob store; writes nothing."""

    out = []
    for event in session.state.events:
        if not event.inputs or event.inputs[0] != MINI_RECORD_MARKER:
            continue
        kind = _field(event.inputs, "kind:")
        ref = _field(event.inputs, "blob:")
        if kind is None or ref is None:
            continue
        payload = json.loads(session.blobs.get(ref).decode("utf-8"))
        about = payload.get("about")
        out.append(
            MiniRecordV1(
                seq=event.seq,
                kind=kind,
                ref=ref,
                about=(about,) if about else (),
                content=str(payload.get("body", "")),
            )
        )
    return tuple(out)


__all__ = [
    "MINI_RECORD_DROPPED_MARKER",
    "MINI_RECORD_MARKER",
    "MiniRecordError",
    "MiniRecordV1",
    "mini_records",
    "record_mini_output",
]
