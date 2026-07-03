"""Canonical serialization (spec §1).

Artifact ids are sha256 over canonical JSON of (content_ref, codec,
interface); blobs are sha256 over raw bytes. Canonical = sorted keys,
compact separators, UTF-8.
"""

import hashlib
import json


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
