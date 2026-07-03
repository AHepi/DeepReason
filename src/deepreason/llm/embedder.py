"""Embedder role (spec §9, §11): content -> vector, non-generator model.

HashingEmbedder is the default: a deterministic local embedding (hashed
bag of word uni+bigrams, signed, L2-normalized). Being a pure function of
content, every §11.3 diagnostic computed from it is replay-deterministic
without raw logging. An API embedder is a drop-in swap but MUST log its
raws (§1) — and negative-atlas entries / school geometry are
model-version-specific: revalidate on upgrade (§11.5, §17).
"""

import hashlib
import math
import re


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


class HashingEmbedder:
    def __init__(self, dim: int = 128) -> None:
        self.dim = dim
        self.name = "hashing"
        self.model = f"hashing-{dim}"
        self.version = "1"

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _tokens(text):
            digest = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
            sign = 1.0 if (digest >> 32) % 2 else -1.0
            vec[digest % self.dim] += sign
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm else vec


def cosine(u: list[float], v: list[float]) -> float:
    return sum(a * b for a, b in zip(u, v))


def distance(u: list[float], v: list[float]) -> float:
    return 1.0 - cosine(u, v)
