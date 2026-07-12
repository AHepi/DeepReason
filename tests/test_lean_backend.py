from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from deepreason.storage.blobs import BlobStore
from deepreason.verification._sandbox import seccomp_available
from deepreason.verification.lean import LeanBackend
from deepreason.verification.models import VerificationRequest

pytestmark = pytest.mark.skipif(not seccomp_available(), reason="libseccomp unavailable")


@pytest.fixture
def fake_lean(tmp_path: Path) -> Path:
    executable = tmp_path / "lean"
    executable.write_text(
        """#!/usr/bin/env python3
import pathlib
import re
import os
import signal
import sys

if sys.argv[1:] == ["--version"]:
    print("Lean (version 4.19.0, fake pinned test kernel)")
    raise SystemExit(0)

source = pathlib.Path(sys.argv[-1]).read_text()
if "SANDBOX_ABORT" in source:
    os.kill(os.getpid(), signal.SIGKILL)
if "BROKEN_PROOF" in source:
    print("error: kernel rejected proof", file=sys.stderr)
    raise SystemExit(1)
for theorem in re.findall(r"#print axioms ([A-Za-z0-9_.']+)", source):
    if "USES_CHOICE" in source:
        print(f"'{theorem}' depends on axioms: [Classical.choice]")
    else:
        print(f"'{theorem}' does not depend on any axioms")
""",
        encoding="utf-8",
    )
    os.chmod(executable, 0o755)
    return executable


def _backend(tmp_path: Path, fake_lean: Path) -> tuple[LeanBackend, BlobStore]:
    blobs = BlobStore(tmp_path / "blobs")
    backend = LeanBackend(
        blobs,
        executable=fake_lean,
        toolchain_id="lean4@4.19.0",
        timeout_s=5,
        cpu_seconds=5,
        memory_limit_mb=512,
    )
    return backend, blobs


def _request(blobs: BlobStore, source: str, **changes) -> VerificationRequest:
    values = {
        "backend": "lean4",
        "toolchain_id": "lean4@4.19.0",
        "source_ref": blobs.put(source.encode()),
        "target_theorems": ["sample"],
    }
    values.update(changes)
    return VerificationRequest(**values)


def _diagnostics(blobs: BlobStore, ref: str) -> dict:
    return json.loads(blobs.get(ref))


def test_pinned_kernel_pass_records_fingerprint_and_axioms(tmp_path: Path, fake_lean: Path):
    backend, blobs = _backend(tmp_path, fake_lean)
    result = backend.verify(_request(blobs, "theorem sample : True := by trivial"))
    assert result.verdict == "pass"
    assert result.theorems == ["sample"]
    assert result.fingerprint["version"] == "4.19.0"
    assert result.fingerprint["network"] is False
    assert len(result.toolchain_sha256) == 64
    assert json.loads(blobs.get(result.axioms_ref))["theorems"] == {"sample": []}


def test_kernel_rejection_is_fail(tmp_path: Path, fake_lean: Path):
    backend, blobs = _backend(tmp_path, fake_lean)
    result = backend.verify(_request(blobs, "BROKEN_PROOF"))
    assert result.verdict == "fail"
    assert _diagnostics(blobs, result.diagnostics_ref)["reason"] == "kernel_rejected"


def test_sorry_is_rejected_before_kernel_check(tmp_path: Path, fake_lean: Path):
    backend, blobs = _backend(tmp_path, fake_lean)
    result = backend.verify(_request(blobs, "theorem sample : True := by sorry"))
    assert result.verdict == "fail"
    assert _diagnostics(blobs, result.diagnostics_ref)["reason"] == "forbidden_placeholder"


def test_axiom_policy_rejects_unlisted_axiom(tmp_path: Path, fake_lean: Path):
    backend, blobs = _backend(tmp_path, fake_lean)
    result = backend.verify(
        _request(blobs, "theorem sample : True := by trivial\n-- USES_CHOICE")
    )
    assert result.verdict == "fail"
    assert _diagnostics(blobs, result.diagnostics_ref)["reason"] == "disallowed_axiom"

    allowed = backend.verify(
        _request(
            blobs,
            "theorem sample : True := by trivial\n-- USES_CHOICE",
            allowed_axioms=["Classical.choice"],
        )
    )
    assert allowed.verdict == "pass"


def test_exact_import_lock_is_required_for_imports(tmp_path: Path, fake_lean: Path):
    backend, blobs = _backend(tmp_path, fake_lean)
    source = "import Std\ntheorem sample : True := by trivial"
    undeclared = backend.verify(_request(blobs, source))
    assert undeclared.verdict == "fail"
    assert _diagnostics(blobs, undeclared.diagnostics_ref)["reason"] == "undeclared_import"

    lock_ref = blobs.put(json.dumps({"imports": ["Std"]}).encode())
    declared = backend.verify(_request(blobs, source, imports_lock_ref=lock_ref))
    assert declared.verdict == "pass"


def test_malformed_import_lock_is_operational_overrun(tmp_path: Path, fake_lean: Path):
    backend, blobs = _backend(tmp_path, fake_lean)
    lock_ref = blobs.put(b"not-json")
    result = backend.verify(
        _request(
            blobs,
            "import Std\ntheorem sample : True := by trivial",
            imports_lock_ref=lock_ref,
        )
    )

    assert result.verdict == "overrun"
    assert not result.fail_warrant_eligible
    assert _diagnostics(blobs, result.diagnostics_ref)["reason"] == "invalid_imports_lock"


def test_missing_toolchain_is_operational_overrun_without_fail_warrant(tmp_path: Path):
    blobs = BlobStore(tmp_path / "blobs")
    backend = LeanBackend(
        blobs,
        executable=tmp_path / "missing-lean",
        toolchain_id="lean4@4.19.0",
    )
    result = backend.verify(_request(blobs, "theorem sample : True := by trivial"))
    assert result.verdict == "overrun"
    assert not result.fail_warrant_eligible
    assert _diagnostics(blobs, result.diagnostics_ref)["reason"] == "toolchain_missing"


def test_containment_abort_is_overrun_without_fail_warrant(tmp_path: Path, fake_lean: Path):
    backend, blobs = _backend(tmp_path, fake_lean)
    result = backend.verify(_request(blobs, "SANDBOX_ABORT"))
    assert result.verdict == "overrun"
    assert not result.fail_warrant_eligible
    assert _diagnostics(blobs, result.diagnostics_ref)["reason"] == "sandbox_abort"
