"""Build and smoke-test the distributable wheel in a fresh virtualenv.

This is intentionally a standalone, standard-library driver so the same gate
runs on Linux, macOS, and Windows.  It never constructs a provider endpoint or
makes a model call.  Invoke it from the repository root with Python 3.11+::

    python scripts/wheel_smoke.py
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv


CORE_MCP_TOOLS = {
    "start_run",
    "run_status",
    "run_result",
    "continue_run",
    "cancel_run",
    "scratch_map",
    "scratch_search",
    "scratch_open",
    "scratch_related",
    "scratch_attention",
    "start_bridge",
    "bridge_status",
    "bridge_result",
    "bridge_claims",
    "get_capabilities",
    "get_help_topic",
    "get_request_requirements",
}


def _run(command: list[str], *, cwd: Path, input_text: str | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=300,
        env={
            **os.environ,
            # The production surface is the thing this gate certifies even if
            # a developer's shell explicitly enabled the quarantined surface.
            "DEEPREASON_ENABLE_LEGACY_MCP": "0",
            # Prevent checkout modules from masking missing wheel contents.
            "PYTHONPATH": "",
        },
    )
    if completed.returncode:
        rendered = " ".join(command)
        raise RuntimeError(
            f"command failed ({completed.returncode}): {rendered}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout


def _venv_executable(root: Path, name: str) -> Path:
    directory = root / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    return directory / f"{name}{suffix}"


def _assert_help(executable: Path, arguments: list[str], expected: str, repo: Path) -> None:
    output = _run([str(executable), *arguments], cwd=repo)
    if expected not in output:
        raise AssertionError(
            f"{executable.name} {' '.join(arguments)} did not advertise {expected!r}"
        )


def _check_mcp(executable: Path, repo: Path) -> None:
    requests = "\n".join(
        json.dumps(message, separators=(",", ":"))
        for message in (
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {},
            },
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
    ) + "\n"
    output = _run([str(executable)], cwd=repo, input_text=requests)
    responses = [json.loads(line) for line in output.splitlines() if line.strip()]
    by_id = {response.get("id"): response for response in responses}
    if by_id[1]["result"]["serverInfo"]["name"] != "deepreason":
        raise AssertionError("deepreason-mcp did not initialize as deepreason")
    tools = by_id[2]["result"]["tools"]
    names = {tool["name"] for tool in tools}
    missing = CORE_MCP_TOOLS - names
    if missing:
        raise AssertionError(
            "installed default MCP surface omits supported core operations: "
            f"{sorted(missing)}"
        )



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep",
        action="store_true",
        help="retain the temporary directory for local diagnosis",
    )
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    temp_root = Path(tempfile.mkdtemp(prefix="deepreason-wheel-smoke-"))
    try:
        wheelhouse = temp_root / "wheelhouse"
        wheelhouse.mkdir()
        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--wheel-dir",
                str(wheelhouse),
            ],
            cwd=repo,
        )
        wheels = sorted(wheelhouse.glob("deepreason-*.whl"))
        if len(wheels) != 1:
            raise AssertionError(f"expected one DeepReason wheel, found {len(wheels)}")

        environment = temp_root / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = _venv_executable(environment, "python")
        deepreason = _venv_executable(environment, "deepreason")
        mcp = _venv_executable(environment, "deepreason-mcp")
        _run([str(python), "-m", "pip", "install", str(wheels[0])], cwd=repo)

        if _venv_executable(environment, "deepreason-campaign").exists():
            raise AssertionError("core wheel unexpectedly installed deepreason-campaign")

        _assert_help(deepreason, ["--help"], "scratch", repo)
        _assert_help(deepreason, ["scratch", "--help"], "coverage", repo)
        _assert_help(deepreason, ["bridge", "--help"], "claims", repo)
        _check_mcp(mcp, repo)

        import_check = """
import importlib.util
from deepreason.bridge import ClaimLedgerV1
from deepreason.llm.embedder import HashingEmbedder, build_embedder
from deepreason.locking import ProcessLock
from deepreason.scratch.service import ScratchService
from minireason.advisory import MiniAdvisorySession

assert ClaimLedgerV1 is not None
assert ProcessLock is not None
assert ScratchService is not None
assert MiniAdvisorySession is not None
assert isinstance(build_embedder(None), HashingEmbedder)
assert build_embedder(None).name == "hashing"
assert importlib.util.find_spec("fastembed") is None
"""
        _run([str(python), "-c", import_check], cwd=temp_root)
        print(
            "wheel smoke passed: supported entry points, required core MCP operations, "
            "canonical scratch/bridge/locking, MiniReason advisory facade, and "
            "deterministic embedder fallback"
        )
        return 0
    finally:
        if args.keep:
            print(f"retained: {temp_root}")
        else:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
