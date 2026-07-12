"""Lean 4 kernel verification with pinned source, toolchain, imports, and axioms."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.verification._sandbox import seccomp_available
from deepreason.verification.models import VerificationRequest, VerificationResult

_VERSION_RE = re.compile(r"\bversion\s+([0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)\b", re.I)
_IMPORT_RE = re.compile(r"(?m)^\s*import\s+([^\n]+)$")
_AXIOMS_RE_TEMPLATE = r"['\"]?{name}['\"]?\s+depends on axioms:\s*\[(.*?)\]"
_NO_AXIOMS_TEMPLATE = r"['\"]?{name}['\"]?\s+does not depend on any axioms"
_SANDBOX_ABORT = "DEEPREASON_SANDBOX_ABORT:"
_DIAGNOSTIC_CAP = 1_000_000
_SOURCE_CAP = 8_000_000


class LeanBackend:
    """Finite Lean 4 verifier.

    The backend records kernel acceptance and assumption dependencies only.
    It does not certify an informal formalization, empirical premise, or the
    consistency of Lean itself.
    """

    backend_id = "lean4"

    def __init__(
        self,
        blobs,
        *,
        executable: str | Path = "lean",
        toolchain_id: str,
        timeout_s: int = 30,
        cpu_seconds: int = 30,
        memory_limit_mb: int = 2_048,
    ) -> None:
        if timeout_s <= 0 or cpu_seconds <= 0 or memory_limit_mb <= 0:
            raise ValueError("Lean containment limits must be positive and finite")
        if not re.fullmatch(
            r"lean4@[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", toolchain_id
        ):
            raise ValueError("toolchain_id must pin an exact Lean 4 version")
        self.blobs = blobs
        self.executable = str(executable)
        self.toolchain_id = toolchain_id
        self.timeout_s = timeout_s
        self.cpu_seconds = cpu_seconds
        self.memory_bytes = memory_limit_mb * 1024 * 1024

    def _resolved_executable(self) -> str | None:
        candidate = Path(self.executable)
        if candidate.is_absolute() or candidate.parent != Path("."):
            return str(candidate.resolve()) if candidate.is_file() else None
        resolved = shutil.which(self.executable)
        return str(Path(resolved).resolve()) if resolved else None

    @staticmethod
    def _file_sha256(path: str) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _environment(work: Path) -> dict[str, str]:
        package_root = str(Path(__file__).resolve().parents[2])
        return {
            "HOME": str(work),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": package_root,
            "TMPDIR": str(work),
        }

    def _sandbox_command(self, command: list[str]) -> list[str]:
        return [
            sys.executable,
            "-m",
            "deepreason.verification._sandbox",
            "--cpu-seconds",
            str(self.cpu_seconds),
            "--memory-bytes",
            str(self.memory_bytes),
            "--",
            *command,
        ]

    def _run(self, command: list[str], work: Path) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(  # noqa: S603 - trusted executable and fixed Lean flags
            self._sandbox_command(command),
            cwd=work,
            env=self._environment(work),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.timeout_s,
            check=False,
        )

    def fingerprint(self) -> dict[str, Any]:
        executable = self._resolved_executable()
        base: dict[str, Any] = {
            "backend": self.backend_id,
            "toolchain_id": self.toolchain_id,
            "runner": "local",
            "executable": executable or self.executable,
            "network": False,
            "sandbox": "seccomp",
            "available": False,
        }
        if executable is None:
            return {**base, "reason": "toolchain_missing"}
        if not seccomp_available():
            return {**base, "reason": "containment_unavailable"}
        executable_sha256 = self._file_sha256(executable)
        try:
            with tempfile.TemporaryDirectory(prefix="deepreason-lean-fingerprint-") as raw:
                completed = self._run([executable, "--version"], Path(raw))
        except (OSError, subprocess.TimeoutExpired):
            return {
                **base,
                "executable_sha256": executable_sha256,
                "reason": "version_unavailable",
            }
        version_bytes = completed.stdout + completed.stderr
        version_text = version_bytes.decode("utf-8", errors="replace")
        match = _VERSION_RE.search(version_text)
        version = match.group(1) if match else None
        expected = self.toolchain_id.partition("@")[2]
        available = completed.returncode == 0 and version == expected
        return {
            **base,
            "available": available,
            "version": version,
            "executable_sha256": executable_sha256,
            "version_output_sha256": sha256_hex(version_bytes),
            **({} if available else {"reason": "toolchain_version_mismatch"}),
        }

    @staticmethod
    def _without_comments_and_strings(source: str) -> str:
        output: list[str] = []
        index = 0
        block_depth = 0
        in_string = False
        while index < len(source):
            pair = source[index:index + 2]
            char = source[index]
            if block_depth:
                if pair == "/-":
                    block_depth += 1
                    index += 2
                elif pair == "-/":
                    block_depth -= 1
                    index += 2
                else:
                    index += 1
                output.append(" ")
                continue
            if in_string:
                if char == "\\":
                    index += 2
                else:
                    in_string = char != '"'
                    index += 1
                output.append(" ")
                continue
            if pair == "/-":
                block_depth = 1
                output.append(" ")
                index += 2
            elif pair == "--":
                end = source.find("\n", index)
                index = len(source) if end < 0 else end
                output.append("\n")
            elif char == '"':
                in_string = True
                output.append(" ")
                index += 1
            else:
                output.append(char)
                index += 1
        return "".join(output)

    @classmethod
    def _forbidden_placeholders(cls, source: str) -> list[str]:
        clean = cls._without_comments_and_strings(source)
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_']*", clean))
        return sorted(tokens.intersection({"admit", "sorry"}))

    @classmethod
    def _source_imports(cls, source: str) -> list[str]:
        clean = cls._without_comments_and_strings(source)
        imports: list[str] = []
        for match in _IMPORT_RE.finditer(clean):
            imports.extend(part for part in match.group(1).split() if part)
        return imports

    @staticmethod
    def _lock_imports(data: bytes) -> list[str]:
        try:
            payload = json.loads(data)
            entries = payload["imports"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError("imports lock must be JSON with an imports array") from error
        if not isinstance(entries, list):
            raise ValueError("imports lock imports must be an array")
        names: list[str] = []
        for entry in entries:
            if isinstance(entry, str):
                name = entry
            elif isinstance(entry, dict) and isinstance(entry.get("module"), str):
                name = entry["module"]
            else:
                raise ValueError("imports lock entries must be module names or records")
            if not name or name in names:
                raise ValueError("imports lock modules must be non-empty and unique")
            names.append(name)
        return names

    @staticmethod
    def _axioms(output: str, targets: list[str]) -> tuple[dict[str, list[str]], list[str]]:
        reports: dict[str, list[str]] = {}
        missing: list[str] = []
        for target in targets:
            escaped = re.escape(target)
            match = re.search(
                _AXIOMS_RE_TEMPLATE.format(name=escaped), output, re.DOTALL
            )
            if match:
                reports[target] = sorted(
                    {item.strip() for item in match.group(1).split(",") if item.strip()}
                )
            elif re.search(_NO_AXIOMS_TEMPLATE.format(name=escaped), output):
                reports[target] = []
            else:
                missing.append(target)
        return reports, missing

    def _store_result(
        self,
        *,
        request: VerificationRequest,
        fingerprint: dict[str, Any],
        source_sha256: str,
        verdict: str,
        diagnostics: dict[str, Any],
        axioms: dict[str, list[str]] | None = None,
        theorems: list[str] | None = None,
    ) -> VerificationResult:
        diagnostics_ref = self.blobs.put(canonical_json(diagnostics))
        axioms_ref = self.blobs.put(
            canonical_json(
                {
                    "schema": "deepreason-lean-axioms-v1",
                    "theorems": axioms or {},
                }
            )
        )
        return VerificationResult(
            backend=self.backend_id,
            fingerprint=fingerprint,
            verdict=verdict,
            diagnostics_ref=diagnostics_ref,
            axioms_ref=axioms_ref,
            theorems=theorems or [],
            source_sha256=source_sha256,
            toolchain_sha256=sha256_hex(canonical_json(fingerprint)),
        )

    def verify(self, request: VerificationRequest) -> VerificationResult:
        fingerprint = self.fingerprint()
        source_sha256 = request.source_ref
        diagnostic_base: dict[str, Any] = {
            "schema": "deepreason-lean-diagnostics-v1",
            "toolchain_id": request.toolchain_id,
            "source_ref": request.source_ref,
            "imports_lock_ref": request.imports_lock_ref,
            "max_heartbeats": request.max_heartbeats,
            "max_rec_depth": request.max_rec_depth,
            "allow_sorry": request.allow_sorry,
            "allowed_axioms": list(request.allowed_axioms),
            "target_theorems": list(request.target_theorems),
        }
        if request.backend != self.backend_id or request.toolchain_id != self.toolchain_id:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostic_base, "reason": "toolchain_not_registered"},
            )
        if not fingerprint.get("available"):
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={
                    **diagnostic_base,
                    "reason": fingerprint.get("reason", "toolchain_unavailable"),
                },
            )
        try:
            source_bytes = self.blobs.get(request.source_ref)
        except KeyError:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostic_base, "reason": "source_unavailable"},
            )
        source_sha256 = sha256_hex(source_bytes)
        if source_sha256 != request.source_ref:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostic_base, "reason": "source_digest_mismatch"},
            )
        if len(source_bytes) > _SOURCE_CAP:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostic_base, "reason": "source_size_limit"},
            )
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="fail",
                diagnostics={**diagnostic_base, "reason": "source_not_utf8"},
            )
        placeholders = self._forbidden_placeholders(source)
        if placeholders and not request.allow_sorry:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="fail",
                diagnostics={
                    **diagnostic_base,
                    "reason": "forbidden_placeholder",
                    "tokens": placeholders,
                },
            )

        imports = self._source_imports(source)
        lock_sha256: str | None = None
        try:
            if request.imports_lock_ref is None:
                declared_imports: list[str] = []
            else:
                lock_bytes = self.blobs.get(request.imports_lock_ref)
                lock_sha256 = sha256_hex(lock_bytes)
                if lock_sha256 != request.imports_lock_ref:
                    return self._store_result(
                        request=request,
                        fingerprint=fingerprint,
                        source_sha256=source_sha256,
                        verdict="overrun",
                        diagnostics={
                            **diagnostic_base,
                            "reason": "imports_lock_digest_mismatch",
                        },
                    )
                declared_imports = self._lock_imports(lock_bytes)
        except KeyError:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostic_base, "reason": "imports_lock_unavailable"},
            )
        except ValueError as error:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={
                    **diagnostic_base,
                    "reason": "invalid_imports_lock",
                    "detail": str(error),
                },
            )
        undeclared = sorted(set(imports).difference(declared_imports))
        if undeclared:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="fail",
                diagnostics={
                    **diagnostic_base,
                    "reason": "undeclared_import",
                    "imports": undeclared,
                    "imports_lock_sha256": lock_sha256,
                },
            )

        executable = str(fingerprint["executable"])
        if self._file_sha256(executable) != fingerprint.get("executable_sha256"):
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostic_base, "reason": "toolchain_fingerprint_changed"},
            )
        axiom_commands = "\n".join(
            f"#print axioms {theorem}" for theorem in request.target_theorems
        )
        checked_source = source + ("\n" + axiom_commands + "\n" if axiom_commands else "")
        try:
            with tempfile.TemporaryDirectory(prefix="deepreason-lean-") as raw_work:
                work = Path(raw_work)
                source_path = work / "Main.lean"
                source_path.write_text(checked_source, encoding="utf-8")
                completed = self._run(
                    [
                        executable,
                        f"-DmaxHeartbeats={request.max_heartbeats}",
                        f"-DmaxRecDepth={request.max_rec_depth}",
                        str(source_path),
                    ],
                    work,
                )
                stdout = completed.stdout[:_DIAGNOSTIC_CAP].decode(
                    "utf-8", errors="replace"
                ).replace(raw_work, "<workdir>")
                stderr = completed.stderr[:_DIAGNOSTIC_CAP].decode(
                    "utf-8", errors="replace"
                ).replace(raw_work, "<workdir>")
        except subprocess.TimeoutExpired:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostic_base, "reason": "sandbox_timeout"},
            )
        except OSError as error:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={
                    **diagnostic_base,
                    "reason": "sandbox_abort",
                    "detail": type(error).__name__,
                },
            )

        combined = stdout + "\n" + stderr
        resource_abort = (
            completed.returncode < 0
            and -completed.returncode
            in {signal.SIGKILL, signal.SIGXCPU, signal.SIGABRT, signal.SIGSEGV}
        ) or _SANDBOX_ABORT in stderr or "bad_alloc" in combined
        diagnostics = {
            **diagnostic_base,
            "imports": imports,
            "imports_lock_sha256": lock_sha256,
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
        if resource_abort:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="overrun",
                diagnostics={**diagnostics, "reason": "sandbox_abort"},
            )
        if completed.returncode != 0:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="fail",
                diagnostics={**diagnostics, "reason": "kernel_rejected"},
            )

        reports, missing = self._axioms(combined, request.target_theorems)
        if missing:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="fail",
                diagnostics={
                    **diagnostics,
                    "reason": "axiom_report_missing",
                    "theorems": missing,
                },
                axioms=reports,
            )
        present_axioms = {axiom for values in reports.values() for axiom in values}
        disallowed = sorted(present_axioms.difference(request.allowed_axioms))
        if not request.allow_sorry and "sorryAx" in present_axioms:
            disallowed = sorted(set(disallowed).union({"sorryAx"}))
        if disallowed:
            return self._store_result(
                request=request,
                fingerprint=fingerprint,
                source_sha256=source_sha256,
                verdict="fail",
                diagnostics={
                    **diagnostics,
                    "reason": "disallowed_axiom",
                    "axioms": disallowed,
                },
                axioms=reports,
            )
        return self._store_result(
            request=request,
            fingerprint=fingerprint,
            source_sha256=source_sha256,
            verdict="pass",
            diagnostics={**diagnostics, "reason": "kernel_accepted"},
            axioms=reports,
            theorems=list(request.target_theorems),
        )


Lean4Backend = LeanBackend
