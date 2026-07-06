"""M0 — append-only events + content-addressed storage (MINI_PLAN §3.1).

The on-disk layout is a strict subset of the parent's (G6): root/log.jsonl
holds parent-schema events, root/blobs is the sha256 blob store, and
root/objects holds the parent's four record schemas so parent replay can
rehydrate outputs by id. State is a pure function of the log: two replays
are byte-equal (G2). Kept because the accounting layer caught three real
spend bugs in the parent (invisible trial spend, retry-exhausted spend,
mid-retry budget death).
"""

import hashlib
import json
import os
import warnings
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

RULES = ("Conj", "Crit", "Adj", "Spawn", "Refl", "Register", "Merge", "Measure", "Reseed")


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact_id(content_ref: str, codec: str, interface: dict) -> str:
    """The parent's canonical id: sha256 over (content_ref, codec, interface)."""
    return sha256_hex(canonical_json(
        {"content_ref": content_ref, "codec": codec, "interface": interface}
    ))


class Call(BaseModel):
    """LLM spend record — a subset of the parent's LLMCall (all its required
    fields present, so parent replay validates mini events unchanged)."""

    role: str
    model: str = ""
    endpoint: str = ""
    prompt_ref: str
    raw_ref: str = ""
    tokens: int = 0
    ms: int = 0
    attempts: int = 1
    truncated: bool = False


class Event(BaseModel):
    seq: int
    ts: str  # iso8601
    rule: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    llm: Call | None = None


class BlobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref: str) -> Path:
        return self.root / ref[:2] / ref

    def put(self, data: bytes) -> str:
        ref = sha256_hex(data)
        path = self._path(ref)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.parent / f"{ref}.tmp.{os.getpid()}"
            tmp.write_bytes(data)
            os.replace(tmp, path)
        return ref

    def get(self, ref: str) -> bytes:
        path = self._path(ref)
        if not path.exists():
            raise KeyError(f"blob not found: {ref}")
        return path.read_bytes()


class ObjectStore:
    """Parent record files: objects/<sha256(id)>.json = {schema, id, data}."""

    SCHEMAS = ("artifact", "commitment", "warrant", "problem")

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, oid: str) -> Path:
        return self.root / f"{sha256_hex(oid.encode())}.json"

    def put(self, schema: str, oid: str, data: dict) -> None:
        assert schema in self.SCHEMAS
        path = self._path(oid)
        if path.exists():
            return  # immutable; same id => same record
        tmp = path.with_suffix(f".tmp.{os.getpid()}")
        tmp.write_bytes(canonical_json({"schema": schema, "id": oid, "data": data}))
        os.replace(tmp, path)

    def get(self, oid: str) -> tuple[str, dict]:
        path = self._path(oid)
        if not path.exists():
            raise KeyError(f"object not found: {oid}")
        record = json.loads(path.read_text())
        return record["schema"], record["data"]


class SeqError(ValueError):
    """An append would break the strictly-consecutive seq stream."""


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._repair_torn_tail()
        self.next_seq = sum(1 for _ in self.read())
        self._size = self.path.stat().st_size if self.path.exists() else 0

    def _repair_torn_tail(self) -> None:
        """Truncate a torn FINAL line at open (crash mid-append). Without
        this, the next append writes onto the unterminated fragment and the
        merged line swallows a real, fsynced event — found by the chaos
        battery: acknowledged data lost AFTER a clean recovery. Only bytes
        that were never acknowledged durable are removed (append returns
        only after the full line + newline hit the disk); a bad line with
        valid lines after it is real corruption and is left to raise."""
        if not self.path.exists():
            return
        data = self.path.read_bytes()
        if not data:
            return
        offset, valid_end = 0, 0
        torn_at: int | None = None
        while offset < len(data):
            nl = data.find(b"\n", offset)
            end = (nl + 1) if nl != -1 else len(data)
            line = data[offset:end].strip()
            ok = not line
            if line:
                try:
                    Event.model_validate_json(line)
                    ok = nl != -1  # even a parseable line is torn without its newline
                except ValidationError:
                    ok = False
            if ok:
                valid_end = end
                torn_at = None
            elif torn_at is None:
                torn_at = offset
            else:
                return  # bad line followed by more lines: corruption, read() raises
            offset = end
        if torn_at is not None:
            warnings.warn(
                f"{self.path}: truncating torn final line (crash mid-append), "
                f"{len(data) - valid_end} bytes discarded",
                stacklevel=3,
            )
            with open(self.path, "r+b") as f:
                f.truncate(valid_end)
                f.flush()
                os.fsync(f.fileno())

    def append(self, event: Event) -> None:
        if event.seq != self.next_seq:
            raise SeqError(f"seq {event.seq} != expected {self.next_seq}")
        if event.rule not in RULES:
            raise SeqError(f"rule {event.rule!r} outside the parent enum")
        # Single-writer fence: if the file grew under us, another writer is
        # live and appending would duplicate a seq — silent corruption the
        # chaos battery caught. Fail HERE, not at the next replay.
        actual = self.path.stat().st_size if self.path.exists() else 0
        if actual != self._size:
            raise SeqError(
                f"log advanced under us ({actual} != {self._size} bytes): "
                "concurrent writer on this root")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")
            f.flush()
            os.fsync(f.fileno())
            self._size = f.tell()
        self.next_seq += 1

    def read(self):
        """Yield events in order; a torn FINAL line (crash mid-append) is
        dropped with a warning, a bad line anywhere else raises."""
        if not self.path.exists():
            return
        pending: tuple[int, str] | None = None
        with open(self.path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                if pending is not None:
                    yield Event.model_validate_json(pending[1])
                pending = (lineno, line)
        if pending is not None:
            try:
                yield Event.model_validate_json(pending[1])
            except ValidationError as e:
                warnings.warn(f"{self.path}: dropping torn final line: {e}", stacklevel=2)


class State:
    """Materialized view — never ground truth; recompute from the log."""

    def __init__(self) -> None:
        self.artifacts: dict[str, dict] = {}
        self.problems: dict[str, dict] = {}
        self.commitments: dict[str, dict] = {}
        self.warrants: dict[str, dict] = {}
        self.addr: list[tuple[str, str]] = []  # (artifact, problem)
        self.events: list[Event] = []

    @property
    def refuted(self) -> set[str]:
        """v0 status is {live, refuted-by-check}: an artifact is refuted iff
        a registered artifact carries a warrant targeting it (refuters are
        never attacked in v0 — reinstatement graduates to the parent)."""
        return {
            self.warrants[wid]["target"]
            for a in self.artifacts.values()
            for wid in a.get("warrants", ())
            if wid in self.warrants and self.warrants[wid]["target"] in self.artifacts
        }

    def status(self, aid: str) -> str:
        return "refuted-by-check" if aid in self.refuted else "live"

    def logged_tokens(self) -> int:
        return sum(e.llm.tokens for e in self.events if e.llm is not None)

    def digest(self) -> str:
        """Canonical fingerprint for the byte-replay invariant (G2)."""
        return sha256_hex(canonical_json({
            "artifacts": sorted(self.artifacts),
            "problems": sorted(self.problems),
            "commitments": sorted(self.commitments),
            "warrants": sorted(self.warrants),
            "addr": sorted(self.addr),
            "refuted": sorted(self.refuted),
            "events": len(self.events),
            "logged_tokens": self.logged_tokens(),
        }))


def apply_event(state: State, event: Event, objects: ObjectStore) -> None:
    """The ONE event-application path (parent's _apply_event, subsetted):
    live commits and replay both go through here, so reopening a root
    reproduces state byte-for-byte. Each output id rehydrates from objects."""
    if event.seq != len(state.events):
        raise SeqError(f"seq {event.seq} at position {len(state.events)}")
    for oid in event.outputs:
        schema, data = objects.get(oid)
        if schema == "artifact":
            state.artifacts[oid] = data
            for pid in event.inputs:
                if pid in state.problems and (oid, pid) not in state.addr:
                    state.addr.append((oid, pid))
        elif schema == "problem":
            state.problems[oid] = data
        elif schema == "commitment":
            state.commitments[oid] = data
        elif schema == "warrant":
            state.warrants[oid] = data
    state.events.append(event)


def replay(root: Path) -> State:
    """State as a pure function of the log (G2)."""
    root = Path(root)
    objects = ObjectStore(root / "objects")
    state = State()
    for event in EventLog(root / "log.jsonl").read():
        apply_event(state, event, objects)
    return state
