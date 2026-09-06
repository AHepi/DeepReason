"""A writer's-room root -> an attachment directory the full harness can admit.

SPEC S3 (R3). One block per room record, body VERBATIM, each record headed by
one line naming its kind, id, cycle and (for objections and proposals) the
conjecture it is about. Three plain-text files rather than one file per
record, because `reason --attach` admits at most 64 files and the managed
attached-evidence policy binds at most 16 sources and shows at most 8 per
call (SPEC "The three ceilings"); three sources are shown whole on every call.

Why the layout is what it is:
  * a blank-line-separated paragraph is ONE admission block (`parse.py`), so
    a record is a paragraph and the header is its first line;
  * no `#` line and no pipe-table line anywhere, so the file sniffs as
    text/plain and no heading or table block is minted;
  * the header line has no comma, so the file can never sniff as CSV;
  * the conjectures file sorts first and the proposals file lists every
    conjecture's refuted-if proposal before any other kind, because the
    citable legend shows the first 32 blocks in admission order and those are
    the ids a candidate can cite (SPEC A3; PARKED P2).

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


def header(record: dict) -> str:
    parts = [record["kind"].upper(), f"id={record['id'][:16]}", f"cycle={record['cycle']}"]
    if record["about"]:
        parts.append(f"about={record['about'][:16]}")
    if record["kind"] == "conjecture" and record["label"]:
        # A comma in the header is the one character that could change how
        # the file is admitted (the CSV sniff); the body below keeps the
        # label verbatim, so nothing is lost by folding it here.
        parts.append(f"angle={record['label'].replace(',', ';')}")
    if record["kind"] == "proposal" and record["label"]:
        parts.append(f"kind={record['label']}")
    line = " ".join(parts)
    if "," in line or "\n" in line or line.startswith("#") or line.startswith("|"):
        raise ValueError(f"header would change how the file is admitted: {line!r}")
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
    manifest = {"schema": "room-attachment-conversion.v1", "files": {}, "records": []}
    for name, rows in grouped.items():
        chunks = []
        for record in rows:
            _check_body(record["body"])
            chunks.append(header(record) + "\n" + record["body"])
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
    """Re-read the files and prove every paragraph body is the record's body."""
    bodies = {(r["kind"], r["id"]): r["body"] for r in records}
    ok = 0
    for name in FILES:
        text = (out / name).read_text(encoding="utf-8")
        for paragraph in text.rstrip("\n").split("\n\n"):
            head, _, body = paragraph.partition("\n")
            kind = head.split(" ", 1)[0].lower()
            short = head.split(" id=", 1)[1].split(" ", 1)[0]
            full = next(k for k in bodies if k[0] == kind and k[1].startswith(short))
            ok += bodies[full] == body
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
    print(f"chars {manifest['chars_total']}")
    for name, info in manifest["files"].items():
        print(f"{name}: {info['records']} records, {info['bytes']} bytes")
    return 0 if verbatim == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
