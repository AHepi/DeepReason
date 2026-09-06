"""A writer's-room root -> an attachment directory the full harness can admit.

SPEC S3 (R3), amended by SPEC Amendment 4 (R39, R40). One block per room
record, body VERBATIM, each record headed by one line naming its kind, its
cycle and -- for a proposal or an objection -- the CONJECTURE IT IS ABOUT, by
that conjecture's ordinal and angle. Three plain-text files rather than one
file per record, because `reason --attach` admits at most 64 files and the
managed attached-evidence policy binds at most 16 sources and shows at most 8
per call (SPEC "The three ceilings"); three sources are shown whole on every
call.

ONE ID SYSTEM (PARKED P7 road A, taken 2026-09-06). The header lines used to
carry `id=<room record id>` and `about=<room record id>`. The 2026-09-06
launch measured what that costs: the seat had TWO id systems in front of it --
the room's record ids inside the frozen text and the admission block ids in
the legend -- and cited the room's 58 times against the legend's 21, every one
recorded as `EVIDENCE_REF_UNKNOWN_BLOCK`; the critic died of the same
confusion. So NO ROOM RECORD ID IS WRITTEN INTO THE ATTACHED TEXT any more.
The record ids live in CONVERSION.json alone, which is not attached; the only
ids the seat can see are the legend's, which are the only ones that resolve.

A conjecture is named in a header by its ORDINAL (`n=`, its position in the
room) and its ANGLE; a proposal or objection names its target the same way
(`about-n=`, `about-angle=`). Neither is id-shaped, and neither is mirrored
anywhere the seat is asked to cite from.

THE PREAMBLE (R40). The organiser's directive in
`src/deepreason/llm/seat_plugins.py` describes the OLD header line, and this
window may not edit `src/`; R40 says so and says where the instruction goes
instead -- "the attachment's own preamble paragraph". Each file therefore
opens with one short paragraph that states the header shape actually used and
that the room's records carry no citable id. It is the only text in the
attachment that is not a room record, and it is disclosed as such.

Why the layout is what it is:
  * a blank-line-separated paragraph is ONE admission block (`parse.py`), so
    a record is a paragraph and the header is its first line;
  * no `#` line and no pipe-table line anywhere, so the file sniffs as
    text/plain and no heading or table block is minted;
  * the header line has no comma, so the file can never sniff as CSV;
  * the header line carries no room record id (see ONE ID SYSTEM above);
  * the conjectures file sorts first and the proposals file lists every
    conjecture's refuted-if proposal before any other kind. This was written
    to steer the citable legend, which shows the dossier's first 32 blocks;
    it does NOT, because admission sorts blocks by content id
    (`admission/parse.py`), so the legend's 32 are a hash-ordered sample of
    the 94 (measured: 7 conjectures, 13 proposals, 12 objections). The order
    is kept for the human reader of the frozen section and for the proof that
    the room reached the seat whole; the cap and the order are PARKED (P2),
    and SPEC Amendment 1 records the wrong assumption.

Reads `mini/minireason` (import only); writes nothing under it.

    python room_to_attachment.py <room-root> <out-dir> [--json CONVERSION.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "mini"))

FILES = ("01-conjectures.txt", "02-proposals.txt", "03-objections.txt")
PROPOSAL_KIND_ORDER = ("refuted-if", "forbids", "must-not", "predicts")
_LABEL = {
    "conjecture": re.compile(r"\n\[angle: (?P<v>.*)\]\Z", re.S),
    "proposal": re.compile(r"\n\[kind: (?P<v>.*)\]\Z", re.S),
    "objection": re.compile(r"\n\[would settle: (?P<v>.*)\]\Z", re.S),
}


def _label(kind: str, body: str) -> str | None:
    match = _LABEL[kind].search(body)
    if match is None:
        return None
    return " ".join(match.group("v").split())


def _cycle(seq: int, conj_seqs: list[int]) -> int:
    return sum(1 for boundary in conj_seqs if boundary <= seq)


def load_records(root: pathlib.Path) -> list[dict]:
    from minireason.loop import Session
    from minireason.records import mini_records

    session = Session(root)
    events = list(session.state.events)
    conj_events = [e for e in events if getattr(e.rule, "value", e.rule) == "Conj"]
    conj_seqs = [e.seq for e in conj_events]
    order: dict[str, int] = {}
    for event in conj_events:
        for artifact_id in event.outputs:
            order.setdefault(artifact_id, len(order))
    records: list[dict] = []
    artifacts = session.harness.state.artifacts
    for artifact_id in sorted(order, key=order.get):
        artifact = artifacts[artifact_id]
        role = getattr(artifact.provenance.role, "value", artifact.provenance.role)
        if role != "conjecturer":
            continue
        body = artifact.content_ref[len("inline:"):]
        records.append(
            {
                "kind": "conjecture",
                "id": artifact_id,
                "cycle": _cycle(artifact.provenance.event_seq, conj_seqs),
                "about": None,
                "label": _label("conjecture", body),
                "body": body,
            }
        )
    for record in mini_records(session):
        kind = {
            "mini.commitment-proposal.v1": "proposal",
            "mini.criticism.v1": "objection",
        }.get(record.kind)
        if kind is None:
            continue
        records.append(
            {
                "kind": kind,
                "id": record.ref,
                "cycle": _cycle(record.seq, conj_seqs),
                "about": record.about[0] if record.about else None,
                "label": _label(kind, record.content),
                "body": record.content,
            }
        )
    return records


def _flat(text: str) -> str:
    return " ".join(text.split()).replace(",", ";")


def conjecture_index(records: list[dict]) -> dict:
    """Ordinal and angle per conjecture, in the room's own order."""

    out: dict[str, dict] = {}
    for record in records:
        if record["kind"] == "conjecture":
            out[record["id"]] = {"n": len(out) + 1, "angle": record["label"]}
    return out


PREAMBLE = (
    "PREAMBLE -- how to read {name}. "
    "The paragraphs below are the records of a writer's room, one record per "
    "paragraph. Each opens with a header line: CONJECTURE n=<number> "
    "cycle=<number> angle=<the conjecture's angle>; PROPOSAL cycle=<number> "
    "kind=<one of refuted-if / forbids / must-not / predicts> "
    "about-n=<the conjecture's "
    "number> about-angle=<its angle>; OBJECTION cycle=<number> about-n=<the "
    "conjecture's number> about-angle=<its angle>. A proposal's or "
    "objection's about-n and about-angle name the conjecture it was written "
    "about. These numbers and angles are NOT citable ids and naming one "
    "grounds nothing: the only ids that resolve are the ids listed in "
    "CITABLE EVIDENCE BLOCKS, and an id from anywhere else is recorded as a "
    "failed citation. This paragraph is the only text here that is not a "
    "room record."
)


def header(record: dict, conjectures: dict) -> str:
    """One header line, carrying NO room record id (P7 road A).

    `conjectures` maps a conjecture's record id to `{"n": ordinal, "angle":
    label}`; a proposal or objection is headed by its target's ordinal and
    angle, never by an id.
    """

    parts = [record["kind"].upper()]
    if record["kind"] == "conjecture":
        parts.append(f"n={conjectures[record['id']]['n']}")
    parts.append(f"cycle={record['cycle']}")
    if record["kind"] == "proposal" and record["label"]:
        parts.append(f"kind={record['label']}")
    if record["kind"] == "conjecture" and record["label"]:
        # A comma in the header is the one character that could change how
        # the file is admitted (the CSV sniff); the body below keeps the
        # label verbatim, so nothing is lost by folding it here.
        parts.append(f"angle={_flat(record['label'])}")
    if record["kind"] != "conjecture" and record["about"]:
        target = conjectures.get(record["about"])
        if target is None:
            raise ValueError(f"a record about something that is not a conjecture: {record['about']!r}")
        parts.append(f"about-n={target['n']}")
        if target["angle"]:
            parts.append(f"about-angle={_flat(target['angle'])}")
    line = " ".join(parts)
    if "," in line or "\n" in line or line.startswith("#") or line.startswith("|"):
        raise ValueError(f"header would change how the file is admitted: {line!r}")
    if re.search(r"\b[0-9a-f]{12,}\b", line):
        raise ValueError(f"a header carrying an id-shaped token: {line!r}")
    return line


def _check_body(body: str) -> None:
    if "\n\n" in body or not body.strip():
        raise ValueError("a body with a blank line would become two blocks")
    for line in body.split("\n"):
        if line.startswith("#") or line.lstrip().startswith("|"):
            raise ValueError("a body line that reads as a heading or table row")
    if len(body.encode("utf-8")) > 3_800:
        raise ValueError("a body near the 4096-byte block ceiling would be split")


def paragraphs(records: list[dict]) -> dict[str, list[dict]]:
    conj_order = {r["id"]: i for i, r in enumerate(records) if r["kind"] == "conjecture"}
    proposals = [r for r in records if r["kind"] == "proposal"]

    def proposal_key(record):
        kind_rank = (
            PROPOSAL_KIND_ORDER.index(record["label"])
            if record["label"] in PROPOSAL_KIND_ORDER
            else len(PROPOSAL_KIND_ORDER)
        )
        return (kind_rank, conj_order.get(record["about"], 10**6))

    return {
        FILES[0]: [r for r in records if r["kind"] == "conjecture"],
        FILES[1]: sorted(proposals, key=proposal_key),
        FILES[2]: [r for r in records if r["kind"] == "objection"],
    }


def write(records: list[dict], out: pathlib.Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    grouped = paragraphs(records)
    conjectures = conjecture_index(records)
    manifest = {
        "schema": "room-attachment-conversion.v2",
        "files": {},
        "records": [],
        "preamble": {},
        "conjecture_ordinals": {
            cid: {"n": info["n"], "angle": info["angle"]} for cid, info in conjectures.items()
        },
        "header_carries_record_id": False,
    }
    for name, rows in grouped.items():
        preamble = PREAMBLE.format(name=name)
        chunks = [preamble]
        manifest["preamble"][name] = {
            "chars": len(preamble),
            "sha256": hashlib.sha256(preamble.encode("utf-8")).hexdigest(),
        }
        for record in rows:
            _check_body(record["body"])
            chunks.append(header(record, conjectures) + "\n" + record["body"])
            manifest["records"].append(
                {
                    "file": name,
                    "kind": record["kind"],
                    "id": record["id"],
                    "cycle": record["cycle"],
                    "about": record["about"],
                    "label": record["label"],
                    "chars": len(record["body"]),
                    "body_sha256": hashlib.sha256(record["body"].encode("utf-8")).hexdigest(),
                }
            )
        text = "\n\n".join(chunks) + "\n"
        (out / name).write_text(text, encoding="utf-8")
        manifest["files"][name] = {
            "records": len(rows),
            "bytes": len(text.encode("utf-8")),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
    return manifest


def verify_verbatim(records: list[dict], out: pathlib.Path) -> int:
    """Re-read the files and prove every paragraph body is the record's body.

    Matched BY POSITION, because no paragraph carries a record id any more
    (P7 road A): the k-th record written into a file must be the k-th
    paragraph after that file's preamble, and its body must be equal byte for
    byte. A header that has drifted out of step therefore fails here rather
    than passing on a lucky id match.
    """

    grouped = paragraphs(records)
    ok = 0
    for name in FILES:
        text = (out / name).read_text(encoding="utf-8")
        paras = text.rstrip("\n").split("\n\n")
        if not paras or not paras[0].startswith("PREAMBLE -- how to read "):
            raise ValueError(f"{name}: the preamble paragraph is missing")
        for record, paragraph in zip(grouped[name], paras[1:], strict=True):
            head, _, body = paragraph.partition("\n")
            if head != header(record, conjecture_index(records)):
                raise ValueError(f"{name}: a header that is not the one written")
            if "id=" in head or record["id"][:8] in head:
                raise ValueError(f"{name}: a room record id reached the attached text")
            ok += record["body"] == body
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("room_root")
    ap.add_argument("out_dir")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    records = load_records(pathlib.Path(args.room_root))
    out = pathlib.Path(args.out_dir)
    manifest = write(records, out)
    manifest["room_root"] = args.room_root
    counts = {k: sum(1 for r in records if r["kind"] == k) for k in ("conjecture", "proposal", "objection")}
    manifest["counts"] = counts
    manifest["chars_total"] = sum(len(r["body"]) for r in records)
    verbatim = verify_verbatim(records, out)
    manifest["verbatim"] = f"{verbatim}/{len(records)}"
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"records {len(records)} ({counts['conjecture']} conjectures, "
        f"{counts['proposal']} proposals, {counts['objection']} objections)"
    )
    print(f"verbatim {verbatim}/{len(records)}")
    print(f"chars {manifest['chars_total']} (room records only; the three preambles are extra)")
    print(f"header carries a room record id: {manifest['header_carries_record_id']}")
    for name, info in manifest["files"].items():
        print(f"{name}: {info['records']} records, {info['bytes']} bytes")
    return 0 if verbatim == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
