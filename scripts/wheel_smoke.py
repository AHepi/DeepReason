"""Build, inspect, and import the DeepReason wheel without source leakage.

This driver uses only the standard library.  It builds from the accepted
checkout, installs into a venv with no system site packages, then invokes the
installed console and module entry points from an unrelated empty directory.
It never constructs a provider endpoint or makes a model call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile


EXPECTED_MCP_SCHEMA_SHA256 = (
    "7520ea29fa8efba50c98a9ffa76adfbe0c59c66f51541dfe609dee7736bf82e1"
)
EXPECTED_MCP_TOOLS = {
    "get_readiness",
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
REQUIRED_MODULES = {
    "deepreason/__main__.py",
    "deepreason/provider_profile.py",
    "deepreason/qualification.py",
    "deepreason/preparation.py",
    "deepreason/readiness.py",
    "deepreason/mcp_registration.py",
}


def _environment(home: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["HOME"] = str(home)
    environment["USERPROFILE"] = str(home)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.pop("DEEPREASON_PROFILE", None)
    environment.pop("DEEPREASON_HOME", None)
    return environment


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=600,
    )
    if completed.returncode:
        rendered = " ".join(command)
        raise RuntimeError(
            f"command failed ({completed.returncode}): {rendered}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def _venv_executable(root: Path, name: str) -> Path:
    directory = root / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    return directory / f"{name}{suffix}"


def inspect_wheel(wheel: Path) -> None:
    """Fail closed on missing V6 modules or forbidden distributable content."""

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_MODULES - names
        if missing:
            raise AssertionError(f"wheel omits V6 facade modules: {sorted(missing)}")
        lowered = {name.casefold() for name in names}
        forbidden_fragments = (
            "minireason/",
            "/tests/",
            "deterministic_provider",
            "credentials",
            "run-manifest.json",
            "run-result.json",
            "events.jsonl",
        )
        for fragment in forbidden_fragments:
            if any(fragment in name for name in lowered):
                raise AssertionError(f"wheel contains forbidden content: {fragment}")
        if any(name.startswith(("tests/", "scripts/", "mini/")) for name in lowered):
            raise AssertionError("wheel contains repository-only tests, scripts, or Mini")

        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        entry_names = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
        if len(metadata_names) != 1 or len(entry_names) != 1:
            raise AssertionError("wheel metadata or entry points are ambiguous")
        metadata = archive.read(metadata_names[0]).decode("utf-8")
        if "Summary: DeepReason V6-only deterministic reasoning harness" not in metadata:
            raise AssertionError("wheel metadata does not truthfully identify V6-only mode")
        entry_points = archive.read(entry_names[0]).decode("utf-8")
        required_entries = {
            "deepreason = deepreason.cli.main:main",
            "deepreason-mcp = deepreason.mcp_server:main",
        }
        observed = {
            line.strip()
            for line in entry_points.splitlines()
            if line.strip() and not line.startswith("[")
        }
        if observed != required_entries:
            raise AssertionError(f"unexpected console entry points: {sorted(observed)}")


def _check_mcp(executable: Path, work: Path, env: dict[str, str]) -> None:
    requests = "\n".join(
        json.dumps(message, separators=(",", ":"))
        for message in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
    ) + "\n"
    output = _run(
        [str(executable)], cwd=work, env=env, input_text=requests
    ).stdout
    responses = [json.loads(line) for line in output.splitlines() if line.strip()]
    by_id = {response.get("id"): response for response in responses}
    if by_id[1]["result"]["serverInfo"]["name"] != "deepreason":
        raise AssertionError("installed deepreason-mcp did not initialize")
    tools = by_id[2]["result"]["tools"]
    names = {tool["name"] for tool in tools}
    if names != EXPECTED_MCP_TOOLS:
        raise AssertionError(f"installed MCP inventory drifted: {sorted(names)}")
    encoded = json.dumps(tools, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != EXPECTED_MCP_SCHEMA_SHA256:
        raise AssertionError("installed MCP tool schemas differ from the accepted facade")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    temp_root = Path(tempfile.mkdtemp(prefix="deepreason-wheel-smoke-"))
    try:
        wheelhouse = temp_root / "wheelhouse"
        wheelhouse.mkdir()
        build_home = temp_root / "build home"
        build_home.mkdir()
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
            env=_environment(build_home),
        )
        wheels = sorted(wheelhouse.glob("deepreason-*.whl"))
        if len(wheels) != 1:
            raise AssertionError(f"expected one DeepReason wheel, found {len(wheels)}")
        inspect_wheel(wheels[0])

        environment = temp_root / "installed environment with spaces"
        venv.EnvBuilder(
            with_pip=True,
            clear=True,
            system_site_packages=False,
        ).create(environment)
        configuration = (environment / "pyvenv.cfg").read_text(encoding="utf-8")
        if "include-system-site-packages = false" not in configuration.casefold():
            raise AssertionError("wheel smoke venv inherited system site packages")

        python = _venv_executable(environment, "python")
        deepreason = _venv_executable(environment, "deepreason")
        mcp = _venv_executable(environment, "deepreason-mcp")
        work = temp_root / "unrelated empty directory"
        home = temp_root / "blank home"
        work.mkdir()
        home.mkdir()
        clean_env = _environment(home)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                str(wheels[0]),
            ],
            cwd=work,
            env=clean_env,
        )
        _run([str(python), "-m", "pip", "check"], cwd=work, env=clean_env)

        import_check = """
import importlib.util, json, sys
import deepreason
import deepreason.mcp_registration
import deepreason.preparation
import deepreason.provider_profile
import deepreason.qualification
import deepreason.readiness
print(json.dumps({
    "module_file": deepreason.__file__,
    "sys_path": sys.path,
    "mini": importlib.util.find_spec("minireason"),
}, sort_keys=True))
"""
        imported = json.loads(
            _run([str(python), "-c", import_check], cwd=work, env=clean_env).stdout
        )
        module_file = Path(imported["module_file"]).resolve()
        if environment.resolve() not in module_file.parents or repo.resolve() in module_file.parents:
            raise AssertionError(f"deepreason imported outside the clean venv: {module_file}")
        if imported["mini"] is not None:
            raise AssertionError("MiniReason leaked into the installed wheel")
        repo_text = str(repo.resolve()).casefold()
        if any(repo_text in str(item).casefold() for item in imported["sys_path"]):
            raise AssertionError("repository path leaked into installed sys.path")

        console_help = _run([str(deepreason), "--help"], cwd=work, env=clean_env).stdout
        module_help = _run(
            [str(python), "-m", "deepreason", "--help"], cwd=work, env=clean_env
        ).stdout
        if console_help != module_help:
            raise AssertionError("console and python -m parsers differ")
        for removed in ("focus", "expand", "attack", "step"):
            if f"\n    {removed} " in console_help:
                raise AssertionError(f"removed public surface remains installed: {removed}")
        if "MiniReason" in console_help:
            raise AssertionError("MiniReason remains in installed console help")

        registration = json.loads(
            _run([str(deepreason), "mcp-registration"], cwd=work, env=clean_env).stdout
        )
        command = registration["mcpServers"]["deepreason"]["command"]
        if Path(command) != mcp.resolve() or " " not in command:
            raise AssertionError("MCP registration did not preserve the absolute spaced path")
        if registration["mcpServers"]["deepreason"] != {
            "command": str(mcp.resolve()),
            "args": [],
        }:
            raise AssertionError("MCP registration contains unexpected authority")
        _check_mcp(mcp, work, clean_env)
        print(
            "wheel smoke passed: isolated V6-only contents, clean imports, exact entry "
            "points, module parity, MCP registration, and exact MCP schemas"
        )
        return 0
    finally:
        if args.keep:
            print(f"retained: {temp_root}")
        else:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
