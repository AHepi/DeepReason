"""Pinned code-workload inputs and localized patch compilation.

The model-facing contract contains only file/anchor aliases and replacement
text.  This module compiles those aliases into a content-addressed patch against
a trusted workspace snapshot.  It never accepts an argv, cwd, environment,
route, budget, or status field from model output.

Patch application is deliberately separate from adjudication.  Every error in
this module is an operational ``PatchApplicationError``; callers must not turn
one into an epistemic refutation of the proposed idea.
"""

from __future__ import annotations

import ast
import fnmatch
import os
import stat
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex

_DIGEST_PATTERN = r"^[0-9a-f]{64}$"
_LANGUAGES = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".lean": "lean4",
}
_DEFAULT_PATCH_BYTES = 256 * 1024
_DEFAULT_CARD_LINES = 80


class _FrozenModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    def model_dump(self, *args, **kwargs):
        # Pydantic 2.11 gained ``serialize_by_alias``.  Keep the wire contract
        # stable on every supported >=2.7 release as well.
        kwargs.setdefault("by_alias", True)
        return super().model_dump(*args, **kwargs)

    def model_dump_json(self, *args, **kwargs):
        kwargs.setdefault("by_alias", True)
        return super().model_dump_json(*args, **kwargs)


class CodeProblem(_FrozenModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class WorkspaceSpec(_FrozenModel):
    root: str = Field(min_length=1)
    root_digest: str = Field(pattern=_DIGEST_PATTERN)
    allowed_paths: tuple[str, ...] = Field(min_length=1)
    read_only_source: Literal[True] = True

    @field_validator("root")
    @classmethod
    def _explicit_root(cls, value: str) -> str:
        path = Path(value)
        if not path.is_absolute():
            raise ValueError("workspace.root must be an explicit absolute path")
        return str(path)

    @field_validator("allowed_paths")
    @classmethod
    def _safe_globs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            if not value or "\x00" in value:
                raise ValueError("allowed path patterns must be nonempty")
            path = PurePosixPath(value.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("allowed path patterns must stay below the workspace root")
        return values


class CheckSpec(_FrozenModel):
    """A trusted command declared by the workload, never by a candidate."""

    id: str = Field(min_length=1)
    runner: Literal["pytest", "command", "property", "lint", "compile"]
    argv: tuple[str, ...] = Field(min_length=1)
    cwd: str = "."
    env: dict[str, str] = Field(default_factory=dict)
    step_or_item_limit: int = Field(default=0, ge=0)
    expected_exit: int = 0

    @field_validator("argv")
    @classmethod
    def _valid_argv(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value or "\x00" in value for value in values):
            raise ValueError("argv entries must be nonempty and contain no NUL")
        return values

    @field_validator("cwd")
    @classmethod
    def _relative_cwd(cls, value: str) -> str:
        return _normal_relative(value, field="check cwd", allow_dot=True)

    @field_validator("env")
    @classmethod
    def _plain_environment(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not key or "=" in key or "\x00" in key for key in value):
            raise ValueError("environment keys must be plain variable names")
        if any("\x00" in item for item in value.values()):
            raise ValueError("environment values must contain no NUL")
        return value


class CodeExport(_FrozenModel):
    enabled: bool = False
    directory: str | None = None

    @model_validator(mode="after")
    def _explicit_directory_when_enabled(self):
        if self.enabled and not self.directory:
            raise ValueError("enabled code export requires an explicit directory")
        if self.directory and not Path(self.directory).is_absolute():
            raise ValueError("export.directory must be an explicit absolute path")
        return self


class SimulationSpec(_FrozenModel):
    schema_: Literal["deepreason-simulation-v1"] = Field(
        default="deepreason-simulation-v1", alias="schema"
    )
    language: Literal["python"] = "python"
    entry: str = Field(min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    seed_set: tuple[int, ...] = Field(min_length=1)
    inputs_ref: str = Field(pattern=_DIGEST_PATTERN)
    observables: tuple[str, ...] = Field(min_length=1)
    checker_ref: str = Field(pattern=_DIGEST_PATTERN)
    deterministic_step_limit: int = Field(default=100_000, ge=1)
    sample_limit: int = Field(default=100, ge=1)
    toolchain_id: str = Field(default="python@3.11", min_length=1)

    @property
    def schema(self) -> str:
        return self.schema_

    @field_validator("seed_set")
    @classmethod
    def _unique_seeds(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if len(value) != len(set(value)):
            raise ValueError("simulation seeds must be unique")
        return value

    @field_validator("observables")
    @classmethod
    def _unique_observables(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)) or any(not item for item in value):
            raise ValueError("simulation observables must be nonempty and unique")
        return value


class CodeWorkloadSpec(_FrozenModel):
    schema_: Literal["deepreason-code-workload-v1"] = Field(
        default="deepreason-code-workload-v1", alias="schema"
    )
    problem: CodeProblem
    workspace: WorkspaceSpec
    languages: tuple[str, ...] = Field(default=("python",), min_length=1)
    entrypoints: tuple[str, ...] = ()
    checks: tuple[CheckSpec, ...] = ()
    simulations: tuple[SimulationSpec, ...] = ()
    export: CodeExport = Field(default_factory=CodeExport)

    @property
    def schema(self) -> str:
        return self.schema_

    @model_validator(mode="after")
    def _unique_ids_and_pinned_operations(self):
        check_ids = [check.id for check in self.checks]
        if len(check_ids) != len(set(check_ids)):
            raise ValueError("check ids must be unique")
        # Aggregate operation count may be unlimited elsewhere, but every
        # simulation in this frozen workload remains finitely bounded.
        if any(sim.sample_limit <= 0 or sim.deterministic_step_limit <= 0 for sim in self.simulations):
            raise ValueError("each simulation operation must have finite positive bounds")
        return self


class SymbolRecord(_FrozenModel):
    name: str
    kind: Literal["function", "async_function", "class"]
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)


class DependencyEdge(_FrozenModel):
    source: str
    target: str
    relation: Literal["imports"] = "imports"


class WorkspaceFile(_FrozenModel):
    path: str
    mode: int = Field(ge=0)
    size: int = Field(ge=0)
    sha256: str = Field(pattern=_DIGEST_PATTERN)
    language: str
    symbol_index: tuple[SymbolRecord, ...] = ()


class WorkspaceSnapshot(_FrozenModel):
    schema_: Literal["deepreason-code-workspace-v1"] = Field(
        default="deepreason-code-workspace-v1", alias="schema"
    )
    root_digest: str = Field(pattern=_DIGEST_PATTERN)
    files: tuple[WorkspaceFile, ...]
    dependency_edges: tuple[DependencyEdge, ...] = ()
    test_mapping: dict[str, tuple[str, ...]] = Field(default_factory=dict)

    @property
    def schema(self) -> str:
        return self.schema_

    def file(self, path: str) -> WorkspaceFile:
        normalized = _normal_relative(path, field="snapshot path")
        try:
            return next(item for item in self.files if item.path == normalized)
        except StopIteration as error:
            raise KeyError(normalized) from error


class CodePatchProposal(_FrozenModel):
    """Shallow model output.  No operational field is accepted here."""

    file: str = Field(min_length=1)
    anchor: str = Field(min_length=1)
    replacement: str


class CodePatchCandidate(_FrozenModel):
    patches: tuple[CodePatchProposal, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    typicality: float = Field(ge=0.0, le=1.0)


class PatchEdit(_FrozenModel):
    path: str
    base_blob: str = Field(pattern=_DIGEST_PATTERN)
    anchor_before: str = Field(min_length=1)
    replacement: str
    occurrence: int = Field(default=1, ge=1)

    @field_validator("path")
    @classmethod
    def _safe_path(cls, value: str) -> str:
        return _normal_relative(value, field="patch path")


class CodePatch(_FrozenModel):
    schema_: Literal["deepreason-code-patch-v1"] = Field(
        default="deepreason-code-patch-v1", alias="schema"
    )
    base_root_digest: str = Field(pattern=_DIGEST_PATTERN)
    edits: tuple[PatchEdit, ...] = Field(min_length=1)

    @property
    def schema(self) -> str:
        return self.schema_

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json")))


class AppliedCodeArtifact(_FrozenModel):
    """Content-addressed description of an applied tree, not an ontology type."""

    schema_: Literal["deepreason-applied-code-v1"] = Field(
        default="deepreason-applied-code-v1", alias="schema"
    )
    base_root_digest: str = Field(pattern=_DIGEST_PATTERN)
    root_digest: str = Field(pattern=_DIGEST_PATTERN)
    patch_digest: str = Field(pattern=_DIGEST_PATTERN)
    files: tuple[WorkspaceFile, ...]

    @property
    def schema(self) -> str:
        return self.schema_


class CodeCard(_FrozenModel):
    alias: str
    file: str
    symbol: str | None = None
    line_span: tuple[int, int]
    digest: str = Field(pattern=_DIGEST_PATTERN)
    anchor: str
    excerpt: str
    diagnostics: tuple[str, ...] = ()


class PatchApplicationError(ValueError):
    """Stable operational failure; it carries no candidate verdict."""

    def __init__(self, code: str, message: str, *, path: str | None = None) -> None:
        self.code = code
        self.path = path
        location = f" [{path}]" if path else ""
        super().__init__(f"{code}{location}: {message}")


def _normal_relative(value: str, *, field: str, allow_dot: bool = False) -> str:
    raw = value.replace("\\", "/")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "\x00" in raw:
        raise ValueError(f"{field} must stay below the workspace root")
    normalized = path.as_posix()
    if normalized in {"", "."} and not allow_dot:
        raise ValueError(f"{field} must name a file")
    return normalized


def _allowed(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern.replace("\\", "/")) for pattern in patterns)


def _python_metadata(relative: str, data: bytes) -> tuple[tuple[SymbolRecord, ...], tuple[DependencyEdge, ...]]:
    if Path(relative).suffix not in {".py", ".pyi"}:
        return (), ()
    try:
        tree = ast.parse(data.decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return (), ()
    symbols: list[SymbolRecord] = []
    edges: list[DependencyEdge] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = (
                "class"
                if isinstance(node, ast.ClassDef)
                else "async_function"
                if isinstance(node, ast.AsyncFunctionDef)
                else "function"
            )
            symbols.append(
                SymbolRecord(
                    name=node.name,
                    kind=kind,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                )
            )
        elif isinstance(node, ast.Import):
            edges.extend(
                DependencyEdge(source=relative, target=alias.name) for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            dots = "." * node.level
            edges.append(
                DependencyEdge(source=relative, target=f"{dots}{node.module or ''}")
            )
    symbols.sort(key=lambda item: (item.line_start, item.name, item.kind))
    edges.sort(key=lambda item: (item.source, item.target))
    return tuple(symbols), tuple(edges)


def _tree_digest(files: Iterable[WorkspaceFile]) -> str:
    payload = [
        {
            "path": item.path,
            "mode": item.mode,
            "size": item.size,
            "sha256": item.sha256,
            "language": item.language,
            "symbol_index": [symbol.model_dump(mode="json") for symbol in item.symbol_index],
        }
        for item in sorted(files, key=lambda file: file.path)
    ]
    return sha256_hex(canonical_json(payload))


def _module_name(path: str) -> str | None:
    pure = PurePosixPath(path)
    if pure.suffix not in {".py", ".pyi"}:
        return None
    parts = list(pure.with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) or None


def snapshot_workspace(
    spec: WorkspaceSpec,
    *,
    verify_declared_digest: bool = True,
    blobs=None,
) -> WorkspaceSnapshot:
    """Hash the allowed regular files and build deterministic Python indexes.

    The source remains untouched.  Symlinks are excluded from the snapshot so
    a later patch cannot silently redirect a write outside the pinned tree.
    """

    root = Path(spec.root)
    if not root.is_dir():
        raise PatchApplicationError("workspace-missing", "workspace root is not a directory")
    files: list[WorkspaceFile] = []
    edges: list[DependencyEdge] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if not _allowed(relative, spec.allowed_paths):
            continue
        data = path.read_bytes()
        if blobs is not None:
            stored_ref = blobs.put(data)
            if stored_ref != sha256_hex(data):
                raise PatchApplicationError(
                    "blob-store-mismatch", "blob store returned a non-content digest", path=relative
                )
        symbols, imports = _python_metadata(relative, data)
        edges.extend(imports)
        files.append(
            WorkspaceFile(
                path=relative,
                mode=stat.S_IMODE(path.stat().st_mode),
                size=len(data),
                sha256=sha256_hex(data),
                language=_LANGUAGES.get(path.suffix.lower(), "text"),
                symbol_index=symbols,
            )
        )
    digest = _tree_digest(files)
    if verify_declared_digest and digest != spec.root_digest:
        raise PatchApplicationError(
            "root-mismatch",
            f"declared {spec.root_digest}, observed {digest}",
        )

    tests = [item for item in files if item.path.startswith("tests/")]
    test_imports = {
        item.path: {edge.target.lstrip(".") for edge in edges if edge.source == item.path}
        for item in tests
    }
    mapping: dict[str, tuple[str, ...]] = {}
    for item in files:
        module = _module_name(item.path)
        if not module or item.path.startswith("tests/"):
            continue
        matched = sorted(
            test.path
            for test in tests
            if any(
                imported == module
                or imported.startswith(module + ".")
                or module.startswith(imported + ".")
                for imported in test_imports[test.path]
            )
        )
        if matched:
            mapping[item.path] = tuple(matched)
    return WorkspaceSnapshot(
        root_digest=digest,
        files=tuple(files),
        dependency_edges=tuple(sorted(edges, key=lambda edge: (edge.source, edge.target))),
        test_mapping=mapping,
    )


def compile_patch_candidate(
    candidate: CodePatchCandidate,
    snapshot: WorkspaceSnapshot,
    *,
    file_aliases: Mapping[str, str],
    anchor_aliases: Mapping[str, str],
) -> CodePatch:
    """Compile semantic model output into a pinned patch artifact.

    Mandatory paths, anchors, and base digests come from harness-owned alias
    tables.  Because ``CodePatchCandidate`` forbids extra fields, a model-authored
    command cannot cross this boundary.
    """

    edits: list[PatchEdit] = []
    for proposal in candidate.patches:
        try:
            path = file_aliases[proposal.file]
        except KeyError as error:
            raise PatchApplicationError("unknown-file-alias", proposal.file) from error
        try:
            anchor = anchor_aliases[proposal.anchor]
        except KeyError as error:
            raise PatchApplicationError("unknown-anchor-alias", proposal.anchor) from error
        try:
            base = snapshot.file(path)
        except KeyError as error:
            raise PatchApplicationError("unknown-file", "file is absent from snapshot", path=path) from error
        edits.append(
            PatchEdit(
                path=base.path,
                base_blob=base.sha256,
                anchor_before=anchor,
                replacement=proposal.replacement,
                occurrence=1,
            )
        )
    return CodePatch(base_root_digest=snapshot.root_digest, edits=tuple(edits))


def _safe_target(root: Path, relative: str) -> Path:
    try:
        normalized = _normal_relative(relative, field="patch path")
    except ValueError as error:
        raise PatchApplicationError("path-escape", str(error), path=relative) from error
    target = root / normalized
    current = root
    for part in PurePosixPath(normalized).parts:
        current = current / part
        if current.is_symlink():
            raise PatchApplicationError(
                "symlink-escape", "patch targets may not traverse symlinks", path=normalized
            )
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise PatchApplicationError("path-escape", "resolved path leaves workspace", path=normalized) from error
    return target


def _replace_occurrence(text: str, edit: PatchEdit) -> str:
    count = text.count(edit.anchor_before)
    if count == 0:
        raise PatchApplicationError("anchor-missing", "exact anchor not found", path=edit.path)
    if edit.occurrence > count:
        raise PatchApplicationError(
            "anchor-occurrence", f"requested occurrence {edit.occurrence}, found {count}", path=edit.path
        )
    start = -1
    cursor = 0
    for _ in range(edit.occurrence):
        start = text.find(edit.anchor_before, cursor)
        cursor = start + len(edit.anchor_before)
    return text[:start] + edit.replacement + text[start + len(edit.anchor_before) :]


def apply_code_patch(
    spec: WorkspaceSpec,
    snapshot: WorkspaceSnapshot,
    patch: CodePatch,
    destination: str | Path,
    *,
    max_patch_bytes: int = _DEFAULT_PATCH_BYTES,
    source_blobs=None,
    output_blobs=None,
) -> AppliedCodeArtifact:
    """Materialize and patch a private workspace at ``destination``.

    Only pinned allowed regular files are copied; the source tree is always
    read-only.  The caller owns the destination and may run trusted checks
    there before discarding it.
    """

    if patch.base_root_digest != snapshot.root_digest:
        raise PatchApplicationError("base-root-mismatch", "patch targets a different snapshot")
    patch_bytes = sum(
        len(edit.anchor_before.encode()) + len(edit.replacement.encode()) for edit in patch.edits
    )
    if patch_bytes > max_patch_bytes:
        raise PatchApplicationError(
            "patch-too-large", f"patch is {patch_bytes} bytes; limit is {max_patch_bytes}"
        )
    root = Path(spec.root)
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise PatchApplicationError("destination-not-empty", "ephemeral destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)

    copied: dict[str, Path] = {}
    for item in snapshot.files:
        if not _allowed(item.path, spec.allowed_paths):
            raise PatchApplicationError("forbidden-file", "snapshot file is not allowed", path=item.path)
        if source_blobs is not None:
            try:
                data = source_blobs.get(item.sha256)
            except KeyError as error:
                raise PatchApplicationError(
                    "snapshot-blob-missing", "pinned source bytes are unavailable", path=item.path
                ) from error
        else:
            source = _safe_target(root, item.path)
            if not source.is_file() or source.is_symlink():
                raise PatchApplicationError(
                    "source-changed", "snapshot source is no longer regular", path=item.path
                )
            data = source.read_bytes()
        if sha256_hex(data) != item.sha256:
            raise PatchApplicationError("base-mismatch", "source bytes changed after snapshot", path=item.path)
        target = destination / item.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        os.chmod(target, item.mode)
        copied[item.path] = target

    original_blobs = {item.path: item.sha256 for item in snapshot.files}
    for edit in patch.edits:
        if not _allowed(edit.path, spec.allowed_paths):
            raise PatchApplicationError("forbidden-file", "path is outside allowed paths", path=edit.path)
        target = _safe_target(destination, edit.path)
        if edit.path not in copied:
            raise PatchApplicationError("forbidden-file", "path is absent from snapshot", path=edit.path)
        if original_blobs[edit.path] != edit.base_blob:
            raise PatchApplicationError("base-mismatch", "edit base blob differs from snapshot", path=edit.path)
        raw = target.read_bytes()
        if b"\x00" in raw:
            raise PatchApplicationError("binary-mutation", "NUL byte in target", path=edit.path)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise PatchApplicationError("binary-mutation", "target is not UTF-8 text", path=edit.path) from error
        target.write_text(_replace_occurrence(text, edit), encoding="utf-8", newline="")

    output_files: list[WorkspaceFile] = []
    for item in snapshot.files:
        target = copied[item.path]
        data = target.read_bytes()
        if output_blobs is not None:
            output_ref = output_blobs.put(data)
            if output_ref != sha256_hex(data):
                raise PatchApplicationError(
                    "blob-store-mismatch", "blob store returned a non-content digest", path=item.path
                )
        symbols, _edges = _python_metadata(item.path, data)
        output_files.append(
            WorkspaceFile(
                path=item.path,
                mode=stat.S_IMODE(target.stat().st_mode),
                size=len(data),
                sha256=sha256_hex(data),
                language=item.language,
                symbol_index=symbols,
            )
        )
    return AppliedCodeArtifact(
        base_root_digest=snapshot.root_digest,
        root_digest=_tree_digest(output_files),
        patch_digest=patch.digest,
        files=tuple(output_files),
    )


def build_code_cards(
    spec: WorkspaceSpec,
    snapshot: WorkspaceSnapshot,
    *,
    implicated_paths: Iterable[str],
    diagnostics: Mapping[str, Iterable[str]] | None = None,
    max_cards: int = 12,
    max_lines: int = _DEFAULT_CARD_LINES,
    blobs=None,
) -> tuple[CodeCard, ...]:
    """Create bounded, focused cards instead of rendering a repository dump."""

    diagnostics = diagnostics or {}
    cards: list[CodeCard] = []
    root = Path(spec.root)
    for relative in dict.fromkeys(implicated_paths):
        if len(cards) >= max_cards:
            break
        try:
            item = snapshot.file(relative)
        except KeyError:
            continue
        if blobs is not None:
            try:
                data = blobs.get(item.sha256)
            except KeyError:
                continue
        else:
            target = _safe_target(root, item.path)
            data = target.read_bytes()
        if sha256_hex(data) != item.sha256 or b"\x00" in data:
            continue
        try:
            lines = data.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            continue
        symbols = item.symbol_index or (None,)
        for symbol in symbols:
            if len(cards) >= max_cards:
                break
            start = symbol.line_start if symbol else 1
            end = symbol.line_end if symbol else min(len(lines), max_lines)
            end = min(end, start + max_lines - 1)
            excerpt = "".join(lines[start - 1 : end])
            if not excerpt:
                continue
            cards.append(
                CodeCard(
                    alias=f"F{len(cards) + 1}",
                    file=item.path,
                    symbol=symbol.name if symbol else None,
                    line_span=(start, end),
                    digest=sha256_hex(excerpt.encode()),
                    anchor=excerpt,
                    excerpt=excerpt,
                    diagnostics=tuple(str(value) for value in diagnostics.get(item.path, ())),
                )
            )
    return tuple(cards)


def declared_root_digest(root: str | Path, allowed_paths: Iterable[str]) -> str:
    """Convenience for setup-time manifest compilation.

    Runtime still verifies the resulting declaration before the first model
    call; this helper does not weaken that preflight.
    """

    root = Path(root).resolve()
    provisional = WorkspaceSpec(
        root=str(root),
        root_digest="0" * 64,
        allowed_paths=tuple(allowed_paths),
    )
    return snapshot_workspace(provisional, verify_declared_digest=False).root_digest
