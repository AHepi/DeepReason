"""Root-bound disk hybrid index for bounded brain navigation."""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import unicodedata
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path

from deepreason.brain.cards import build_cards, load_card
from deepreason.brain.store import BrainStore
from deepreason.canonical import canonical_json, sha256_hex

_TOKEN = re.compile(r"[a-z0-9_]+")
_VECTOR_DIMS = 64


def normalize_query(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(_TOKEN.findall(normalized))


def tokens(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(normalize_query(text).split()))


def card_text(card: object) -> str:
    values: list[str] = []
    for name in (
        "title",
        "summary",
        "facets",
        "entities",
        "conditions",
        "overturn_conditions",
    ):
        value = getattr(card, name)
        values.extend(value if isinstance(value, tuple) else (value,))
    return " ".join(values)


def hashed_vector(text: str) -> tuple[float, ...]:
    vector = [0.0] * _VECTOR_DIMS
    terms = tokens(text)
    for term in terms:
        digest = bytes.fromhex(sha256_hex(term.encode()))
        dimension = int.from_bytes(digest[:2], "big") % _VECTOR_DIMS
        sign = 1.0 if digest[2] & 1 else -1.0
        vector[dimension] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return tuple(vector)


def vector_buckets(vector: tuple[float, ...]) -> tuple[str, ...]:
    bits = 0
    for index, value in enumerate(vector):
        if value >= 0:
            bits |= 1 << index
    return tuple(f"{band}:{(bits >> (band * 16)) & 0xFFFF:04x}" for band in range(4))


def cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return max(0.0, sum(a * b for a, b in zip(left, right, strict=True)))


def _projection_manifest(path: Path) -> dict | None:
    try:
        return json.loads((path / "manifest.json").read_text())
    except (OSError, ValueError):
        return None


def _compatible_projection(version_root: Path, digest: str) -> tuple[str, str] | None:
    if not version_root.is_dir():
        return None
    matches: list[tuple[int, str, str]] = []
    for child in sorted(version_root.iterdir()):
        data = _projection_manifest(child)
        if data and data.get("records_digest") == digest:
            event = data.get("activation_event") or {}
            matches.append(
                (
                    int(event.get("seq", -1)),
                    child.name,
                    str(data.get("base_root") or data.get("root_digest")),
                )
            )
    if not matches:
        return None
    _, projection_root, base_root = max(matches)
    return projection_root, base_root


def _index_source_digest(store: BrainStore, record_ids: tuple[str, ...]) -> str:
    links = [
        {"seq": event.seq, "digest": event.digest}
        for event in store.iter_events()
        if event.type == "Link"
    ]
    return sha256_hex(canonical_json({"records": sorted(record_ids), "links": links}))


def _connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    else:
        connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def build_index(store: BrainStore, *, force: bool = False) -> Path:
    root = store.manifest.root_digest
    version_root = store.indexes_path / store.manifest.index_version
    target = version_root / root
    if not force and _projection_manifest(target):
        return target
    build_cards(store, force=force)
    # Card generation logs a derived event only; the authoritative root is unchanged.
    root = store.manifest.root_digest
    ids = store.record_ids()
    digest = _index_source_digest(store, ids)

    compatible = None if force else _compatible_projection(version_root, digest)
    activation_parent: str | None = None
    if compatible is None:
        base = root
        actual = version_root / base
        actual.mkdir(parents=True, exist_ok=True)
        database = actual / "index.sqlite"
        tmp = actual / f"index.tmp.{os.getpid()}.sqlite"
        if tmp.exists():
            tmp.unlink()
        # sqlite3.Connection's context manager commits/rolls back but does not
        # close the handle. Windows therefore refuses the atomic replace below
        # unless ownership of the connection is closed explicitly.
        with closing(_connect(tmp)) as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=OFF;
                PRAGMA synchronous=FULL;
                CREATE TABLE lexical(token TEXT NOT NULL, id TEXT NOT NULL,
                                     PRIMARY KEY(token, id)) WITHOUT ROWID;
                CREATE TABLE vector_bucket(bucket TEXT NOT NULL, id TEXT NOT NULL,
                                           PRIMARY KEY(bucket, id)) WITHOUT ROWID;
                CREATE TABLE graph(source TEXT NOT NULL, target TEXT NOT NULL,
                                   PRIMARY KEY(source, target)) WITHOUT ROWID;
                CREATE TABLE collection(id TEXT PRIMARY KEY, name TEXT NOT NULL) WITHOUT ROWID;
                CREATE TABLE activation(record_id TEXT NOT NULL, seq INTEGER NOT NULL,
                                        type TEXT NOT NULL, day TEXT NOT NULL,
                                        logical_seq INTEGER, payload TEXT NOT NULL,
                                        PRIMARY KEY(record_id, seq)) WITHOUT ROWID;
                CREATE TABLE record_event(record_id TEXT NOT NULL, seq INTEGER NOT NULL,
                                          digest TEXT NOT NULL,
                                          PRIMARY KEY(record_id, seq)) WITHOUT ROWID;
                """
            )
            for record_id in ids:
                card = load_card(store, root, record_id)
                text = card_text(card)
                connection.executemany(
                    "INSERT OR IGNORE INTO lexical(token,id) VALUES (?,?)",
                    ((token, record_id) for token in tokens(text)),
                )
                connection.executemany(
                    "INSERT OR IGNORE INTO vector_bucket(bucket,id) VALUES (?,?)",
                    ((bucket, record_id) for bucket in vector_buckets(hashed_vector(text))),
                )
                connection.executemany(
                    "INSERT OR IGNORE INTO graph(source,target) VALUES (?,?)",
                    ((record_id, related) for related in card.related),
                )
                collection = card.facets[0] if card.facets else "unfiled"
                connection.execute(
                    "INSERT INTO collection(id,name) VALUES (?,?)", (record_id, collection)
                )
            for event in store.events:
                authoritative_record = event.payload.get("record_id")
                if event.type in {"Ingest", "Distill"} and isinstance(
                    authoritative_record, str
                ):
                    connection.execute(
                        "INSERT OR IGNORE INTO record_event(record_id,seq,digest) VALUES (?,?,?)",
                        (authoritative_record, event.seq, event.digest),
                    )
                if event.type == "Link":
                    source = event.payload.get("source")
                    target_id = event.payload.get("target")
                    if isinstance(source, str) and isinstance(target_id, str):
                        connection.execute(
                            "INSERT OR IGNORE INTO graph(source,target) VALUES (?,?)",
                            (source, target_id),
                        )
                if event.type in {"Reinforce", "Pin", "Unpin"}:
                    activation_ids = (event.payload.get("record_id"),)
                elif event.type == "Access":
                    activation_ids = event.payload.get("record_ids", ())
                else:
                    activation_ids = ()
                for activation_id in activation_ids:
                    if not isinstance(activation_id, str):
                        continue
                    connection.execute(
                        """INSERT OR IGNORE INTO activation
                           (record_id,seq,type,day,logical_seq,payload)
                           VALUES (?,?,?,?,?,?)""",
                        (
                            activation_id,
                            event.seq,
                            event.type,
                            event.day.isoformat(),
                            event.logical_seq,
                            canonical_json(event.payload).decode(),
                        ),
                    )
            connection.commit()
        os.replace(tmp, database)
    else:
        activation_parent, base = compatible

    projection = {
        "schema": "deepreason-hybrid-index-v1",
        "root_digest": root,
        "records_digest": digest,
        "base_root": base,
        "record_count": len(ids),
        "index_version": store.manifest.index_version,
        "activation_parent_root": activation_parent,
        "activation_event": None,
    }
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.json"
    tmp_manifest = target / f"manifest.tmp.{os.getpid()}.json"
    tmp_manifest.write_bytes(canonical_json(projection))
    os.replace(tmp_manifest, manifest_path)
    store.append_event(
        "Index", {"root_digest": root, "records_digest": digest, "base_root": base}
    )
    return target


def index_database(store: BrainStore, root_digest: str) -> Path:
    projection_root = store.indexes_path / store.manifest.index_version / root_digest
    projection = _projection_manifest(projection_root)
    if not projection:
        raise KeyError(f"index not built for brain root {root_digest}")
    return (
        store.indexes_path
        / store.manifest.index_version
        / projection["base_root"]
        / "index.sqlite"
    )


def candidate_ids(
    store: BrainStore,
    root_digest: str,
    query: str,
    *,
    limit: int,
    posting_limit: int,
) -> tuple[dict[str, int], dict[str, int]]:
    """Return bounded lexical and LSH hit counts without scanning all cards."""

    query_terms = tokens(query)
    if not query_terms:
        return {}, {}
    placeholders = ",".join("?" for _ in query_terms)
    database = index_database(store, root_digest)
    query_vector = hashed_vector(query)
    buckets = vector_buckets(query_vector)
    bucket_placeholders = ",".join("?" for _ in buckets)
    with closing(_connect(database, read_only=True)) as connection:
        lexical_rows = connection.execute(
            f"""SELECT id, COUNT(*) AS hits FROM lexical
                WHERE token IN ({placeholders})
                GROUP BY id ORDER BY hits DESC, id ASC LIMIT ?""",
            (*query_terms, min(limit, posting_limit)),
        ).fetchall()
        vector_rows = connection.execute(
            f"""SELECT id, COUNT(*) AS hits FROM vector_bucket
                WHERE bucket IN ({bucket_placeholders})
                GROUP BY id ORDER BY hits DESC, id ASC LIMIT ?""",
            (*buckets, min(limit, posting_limit)),
        ).fetchall()
    return (
        {str(row["id"]): int(row["hits"]) for row in lexical_rows},
        {str(row["id"]): int(row["hits"]) for row in vector_rows},
    )


def graph_neighbors(
    store: BrainStore, root_digest: str, seeds: Iterable[str], *, limit: int
) -> tuple[str, ...]:
    seeds = tuple(dict.fromkeys(seeds))
    if not seeds or limit <= 0:
        return ()
    placeholders = ",".join("?" for _ in seeds)
    database = index_database(store, root_digest)
    with closing(_connect(database, read_only=True)) as connection:
        rows = connection.execute(
            f"""SELECT target FROM graph WHERE source IN ({placeholders})
                UNION SELECT source AS target FROM graph WHERE target IN ({placeholders})
                ORDER BY target LIMIT ?""",
            (*seeds, *seeds, limit),
        ).fetchall()
    return tuple(str(row["target"]) for row in rows)


def collections(store: BrainStore, root_digest: str, ids: Iterable[str]) -> dict[str, str]:
    ids = tuple(dict.fromkeys(ids))
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    database = index_database(store, root_digest)
    with closing(_connect(database, read_only=True)) as connection:
        rows = connection.execute(
            f"SELECT id,name FROM collection WHERE id IN ({placeholders})", ids
        ).fetchall()
    return {str(row["id"]): str(row["name"]) for row in rows}


def indexed_activation_events(
    store: BrainStore, root_digest: str, record_ids: Iterable[str]
) -> tuple[dict, ...] | None:
    """Read only relevant activation rows from the root-bound derived index."""

    ids = tuple(dict.fromkeys(record_ids))
    if not ids:
        return ()
    projection_root = store.indexes_path / store.manifest.index_version / root_digest
    projection = _projection_manifest(projection_root)
    if not projection:
        return None
    placeholders = ",".join("?" for _ in ids)
    database = index_database(store, root_digest)
    event_by_seq: dict[int, dict] = {}
    with closing(_connect(database, read_only=True)) as connection:
        for row in connection.execute(
            f"""SELECT seq,type,day,logical_seq,payload FROM activation
                WHERE record_id IN ({placeholders}) ORDER BY seq""",
            ids,
        ).fetchall():
            seq = int(row["seq"])
            event_by_seq[seq] = {
                "seq": seq,
                "type": str(row["type"]),
                "day": str(row["day"]),
                "logical_seq": row["logical_seq"],
                "payload": json.loads(row["payload"]),
            }
    wanted = set(ids)
    seen_roots: set[str] = set()
    cursor: str | None = root_digest
    while cursor is not None:
        if cursor in seen_roots:
            raise ValueError("activation projection cycle")
        seen_roots.add(cursor)
        cursor_projection = _projection_manifest(
            store.indexes_path / store.manifest.index_version / cursor
        )
        if not cursor_projection:
            raise ValueError(f"missing activation projection for root {cursor}")
        event = cursor_projection.get("activation_event")
        if event:
            payload = event.get("payload", {})
            direct = payload.get("record_id")
            accessed = payload.get("record_ids", ())
            if direct in wanted or any(record_id in wanted for record_id in accessed):
                event_by_seq[int(event["seq"])] = event
        cursor = cursor_projection.get("activation_parent_root")
    return tuple(event_by_seq[seq] for seq in sorted(event_by_seq))


def indexed_record_events(
    store: BrainStore, root_digest: str, record_ids: Iterable[str]
) -> dict[str, tuple[dict[str, object], ...]] | None:
    ids = tuple(dict.fromkeys(record_ids))
    if not ids:
        return {}
    projection = _projection_manifest(
        store.indexes_path / store.manifest.index_version / root_digest
    )
    if not projection:
        return None
    placeholders = ",".join("?" for _ in ids)
    result: dict[str, list[dict[str, object]]] = {record_id: [] for record_id in ids}
    with closing(
        _connect(index_database(store, root_digest), read_only=True)
    ) as connection:
        rows = connection.execute(
            f"""SELECT record_id,seq,digest FROM record_event
                WHERE record_id IN ({placeholders}) ORDER BY seq""",
            ids,
        ).fetchall()
    for row in rows:
        result[str(row["record_id"])].append(
            {"seq": int(row["seq"]), "digest": str(row["digest"])}
        )
    return {record_id: tuple(events) for record_id, events in result.items()}
