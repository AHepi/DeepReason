"""Embedder role (spec §9, §11): content -> vector, non-generator model.

HashingEmbedder is the default: a deterministic local embedding (hashed
bag of word uni+bigrams, signed, L2-normalized). Being a pure function of
content, every §11.3 diagnostic computed from it is replay-deterministic
without raw logging — but its geometry is LEXICAL: measured on this repo's
artifacts it reads a renamed copy of the same algorithm as FAR (0.62) and
a genuinely different algorithm as CLOSE (0.29), and it lumped distinct
design documents sharing jargon inside the near-dup radius (the recorded
refuted-attractor orbit in runs/embedder_design).

NeuralEmbedder (optional, fastembed/ONNX, CPU) fixes the fine-grained
ordering. Its determinism posture follows the adjudicated record of
runs/embedder_design — the original "pinned ONNX is bitwise deterministic
on CPU" claim was REFUTED (kernel selection varies across CPU features and
runtime versions), so no cross-environment determinism is claimed anywhere.
Instead the boundary is made explicit and checkable:

  - Replay never re-embeds: embeddings feed attention machinery and logged
    measures only; replay reads the log (§0). Nothing here weakens that.
  - Within one process, embeddings are cached per (model, artifact) — one
    embedding per artifact per run, so a run is self-consistent.
  - Across environments, drift is DETECTED, not denied: fingerprint()
    hashes the model identity, library versions, and the actual vector of
    a sentinel text. The scheduler stamps it on the log at run start, so
    two runs' geometries are comparable iff their stamps match. School
    geometry and negative-atlas comparisons are valid only within a
    matching fingerprint (§11.5, §17) — revalidate on any change.

Thresholds are scale-specific: every distance knob shipped in config was
tuned on the hashing scale. Switching embedders REQUIRES recalibration via
views/basin.threshold_calibration (labeled planted-duplicate pairs +
corpus sibling/unrelated distributions — never a blind distribution map;
the quantile/isotonic shortcuts were each refuted on the same record).
"""

import hashlib
import math
import re

_SENTINEL = (
    "deepreason embedder sentinel: the quick brown fox refutes the lazy "
    "conjecture; def solve(nodes, edges): return sorted(nodes)"
)


class EmbedderUnavailable(RuntimeError):
    """The configured embedding backend cannot run here (missing optional
    dependency, model fetch failure). Callers fall back to HashingEmbedder
    and record the degradation on the log — never silently."""


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

    def fingerprint(self) -> dict:
        return {"model": self.model, "version": self.version,
                "sentinel": _sentinel_hash(self)}


class NeuralEmbedder:
    """fastembed (ONNX, CPU, no torch) behind the same duck-typed surface.
    Verified models on this repo's artifacts: BAAI/bge-small-en-v1.5
    (best prose margins) and jinaai/jina-embeddings-v2-base-code (best
    code margins). Raises EmbedderUnavailable if fastembed is absent or
    the model cannot initialize — the playwright/browser-oracle precedent:
    the harness runs unchanged without the optional dependency."""

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5") -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as e:
            raise EmbedderUnavailable(
                f"fastembed not installed (pip install 'deepreason[embed]'): {e}"
            ) from e
        try:
            self._backend = TextEmbedding(model_name=model)
        except Exception as e:  # model list/fetch errors are library-specific
            raise EmbedderUnavailable(f"embedding model {model!r} unavailable: {e}") from e
        self.name = "neural"
        self.model = model
        self.version = _library_versions()

    def embed(self, text: str) -> list[float]:
        # fastembed truncates to the model's context window itself; normalize
        # defensively so distance() stays cosine even if a model config drifts.
        vec = [float(x) for x in next(iter(self._backend.embed([text])))]
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm else vec

    def fingerprint(self) -> dict:
        """Environment-scoped identity: model + library versions + the hash
        of an actual sentinel embedding. Two environments agree on geometry
        iff these match — the drift the record proved undetectable by a
        model-version stamp alone (ONNX kernels vary per CPU) lands in the
        sentinel term."""
        return {"model": self.model, "version": self.version,
                "sentinel": _sentinel_hash(self)}


def _library_versions() -> str:
    import importlib.metadata as md

    parts = []
    for pkg in ("fastembed", "onnxruntime"):
        try:
            parts.append(f"{pkg}-{md.version(pkg)}")
        except md.PackageNotFoundError:
            parts.append(f"{pkg}-?")
    return "+".join(parts)


def _sentinel_hash(embedder) -> str:
    """Hash of the sentinel text's rounded embedding — geometry identity,
    cheap to compare on the log. Rounding to 1e-6 absorbs sub-noise float
    formatting while still catching any kernel/version drift that moves a
    coordinate."""
    vec = embedder.embed(_SENTINEL)
    payload = ",".join(f"{x:.6f}" for x in vec)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def build_embedder(model: str | None):
    """Config seam: None => the zero-dependency default. Raises
    EmbedderUnavailable (does not fall back) — the CALLER owns the fallback
    so the degradation is recorded on the log, never swallowed here."""
    if not model:
        return HashingEmbedder()
    return NeuralEmbedder(model)


def cosine(u: list[float], v: list[float]) -> float:
    return sum(a * b for a, b in zip(u, v))


def distance(u: list[float], v: list[float]) -> float:
    return 1.0 - cosine(u, v)
