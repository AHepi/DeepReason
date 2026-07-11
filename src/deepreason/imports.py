"""Run-local front-end imports for accepted chunked website manifests.

The LLM emits :class:`DependencyRequest` values, never shell commands or
versions. This trusted service resolves exact npm bytes in an isolated run
directory, refuses lifecycle scripts, stores every archive plus the lockfile,
generates a bounded alias/API capsule, and bundles with the archived esbuild
toolchain. Package availability failures are operational; policy, licence,
surface and byte failures are epistemic and may enter the ordinary warrant
path. Nothing in this module installs into DeepReason or a global Node tree.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from deepreason import assets
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.config import ImportPolicy
from deepreason.manifest import DependencyRequest, Manifest
from deepreason.ontology import Provenance
from deepreason.ontology.artifact import Interface, Ref, RefRole


class OperationalImportError(RuntimeError):
    """Infrastructure did not yield a verdict; callers defer without warrant."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class ImportPlanError(ValueError):
    """A resolved design demonstrably violates an accepted import commitment."""

    def __init__(self, code: str, detail: str, evidence_ids: list[str] | None = None):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.evidence_ids = list(evidence_ids or [])


@dataclass(frozen=True)
class BundleResult:
    fragments: dict[str, str]
    javascript: str
    css: str
    metadata: dict[str, Any]
    lifecycle_source: str = ""


@dataclass(frozen=True)
class ResolvedImportSet:
    record_id: str
    catalog_id: str
    lockfile_id: str
    toolchain_id: str
    capsule_ids: tuple[str, ...]
    alias_ids: tuple[str, ...]
    archive_ids: tuple[str, ...]
    requests: tuple[DependencyRequest, ...]
    packages: tuple[dict[str, Any], ...]
    toolchain_ref: str
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def dependence_ids(self) -> list[str]:
        return [
            self.record_id, self.catalog_id, self.lockfile_id, self.toolchain_id,
            *self.capsule_ids, *self.alias_ids, *self.archive_ids,
        ]


def _exact_ref(value: str) -> tuple[str, str]:
    name, marker, version = value.rpartition("@")
    if not marker or not name or not version or any(c in version for c in "*^~<>= "):
        raise ImportPlanError("unresolved-version", f"not an exact package ref: {value!r}")
    return name, version


def _artifact_bytes(harness, artifact_id: str) -> bytes:
    artifact = harness.state.artifacts[artifact_id]
    if artifact.content_ref.startswith("inline:"):
        return artifact.content_ref[len("inline:"):].encode()
    return harness.blobs.get(artifact.content_ref)


def _integrity_matches(data: bytes, expected: str) -> bool:
    algorithm, marker, encoded = expected.partition("-")
    if not marker or algorithm not in hashlib.algorithms_available:
        return False
    actual = base64.b64encode(hashlib.new(algorithm, data).digest()).decode()
    return actual == encoded


def shared_lifecycle_source(manifest: Manifest) -> str:
    """One page coordinator invokes every declared initializer and cleanup."""
    initializers = [
        component.lifecycle.initializer for component in manifest.ordered()
        if component.lifecycle.animated and component.lifecycle.initializer
    ]
    cleanups = [
        component.lifecycle.cleanup for component in reversed(manifest.ordered())
        if component.lifecycle.animated and component.lifecycle.cleanup
    ]
    if not initializers:
        return ""
    return "\n".join([
        "(() => {",
        "  let started = false;",
        "  const start = () => {",
        "    if (started) return; started = true;",
        *[f"    if (typeof window.{name} === 'function') window.{name}();"
          for name in initializers],
        "  };",
        "  const stop = () => {",
        "    if (!started) return; started = false;",
        *[f"    if (typeof window.{name} === 'function') window.{name}();"
          for name in cleanups],
        "  };",
        "  globalThis.DeepReasonLifecycle = Object.freeze({ start, stop });",
        "  if (document.readyState === 'loading')",
        "    document.addEventListener('DOMContentLoaded', start, { once: true });",
        "  else queueMicrotask(start);",
        "  window.addEventListener('pagehide', stop);",
        "})();",
        "",
    ])


def _archive_manifest(data: bytes) -> tuple[dict[str, Any], str, bool]:
    """Return package.json and the actual licence-file text, if supplied."""
    import io

    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            package_json = archive.extractfile("package/package.json")
            if package_json is None:
                raise KeyError("package/package.json")
            manifest = json.loads(package_json.read())
            unsupported_binary = bool(manifest.get("gypfile") or manifest.get("binary"))
            licence = ""
            for member in archive.getmembers():
                if member.name.endswith((".node", "/binding.gyp")):
                    unsupported_binary = True
                name = PurePosixPath(member.name).name.lower()
                if name in {"license", "license.md", "license.txt", "licence", "copying"}:
                    stream = archive.extractfile(member)
                    if stream is not None:
                        licence = stream.read(32_000).decode(errors="replace")
                        break
            return manifest, licence, unsupported_binary
    except (tarfile.TarError, KeyError, json.JSONDecodeError) as error:
        raise OperationalImportError("malformed-archive", str(error)) from error


def _safe_extract(data: bytes, destination: Path) -> None:
    """Extract an npm package tarball without trusting archive paths/links."""
    import io

    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for member in archive.getmembers():
                path = PurePosixPath(member.name)
                if not path.parts or path.parts[0] != "package":
                    continue
                relative = Path(*path.parts[1:])
                target = (destination / relative).resolve()
                if root != target and root not in target.parents:
                    raise OperationalImportError("malformed-archive", "archive path escape")
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise OperationalImportError("malformed-archive", member.name)
                    target.write_bytes(stream.read())
                    target.chmod(member.mode & 0o755 or 0o644)
                # Symlinks and devices are deliberately not materialized.
    except tarfile.TarError as error:
        raise OperationalImportError("malformed-archive", str(error)) from error


class ImportService:
    """The one trusted resolver/bundler used by the website workflow."""

    def __init__(self, harness, policy: ImportPolicy):
        self.harness = harness
        self.policy = policy
        self.root = Path(harness.root) / "imports"
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalog = assets.runtime_catalog()

    def validate_request(self, manifest: Manifest) -> list[DependencyRequest]:
        requests = [r for r in manifest.dependencies if r.preferred_provider != "native"]
        if requests and not self.policy.enabled:
            raise ImportPlanError("imports-disabled", "runtime imports are disabled")
        if len(requests) > self.policy.max_direct_dependencies:
            raise ImportPlanError(
                "direct-limit",
                f"{len(requests)} runtime imports exceed {self.policy.max_direct_dependencies}",
            )
        core = sum(r.capability_slot == "core-animation" for r in requests)
        scroll = sum(r.capability_slot == "scroll-coordination" for r in requests)
        canvases = {r.canvas_id for r in requests if r.canvas_id}
        if core > self.policy.max_core_animation_engines:
            raise ImportPlanError("core-engine-limit", "too many core animation engines")
        if scroll > self.policy.max_scroll_coordinators:
            raise ImportPlanError("scroll-limit", "too many scroll coordinators")
        if len(canvases) > self.policy.max_webgl_canvases:
            raise ImportPlanError("webgl-limit", "too many WebGL canvases")
        if any((r.pixel_ratio_cap or 0) > self.policy.max_pixel_ratio for r in requests):
            raise ImportPlanError("pixel-ratio", "declared pixel ratio exceeds import policy")
        if sum(r.budget.javascript_bytes for r in requests) > self.policy.max_javascript_bytes:
            raise ImportPlanError("javascript-budget", "declared JavaScript budget exceeds policy")
        if sum(r.budget.css_bytes for r in requests) > self.policy.max_css_bytes:
            raise ImportPlanError("css-budget", "declared CSS budget exceeds policy")
        for request in requests:
            entry = self.catalog.get(request.preferred_provider)
            if entry is None:
                if not self.policy.discovery_beyond_catalog or not request.package:
                    raise ImportPlanError(
                        "unqualified-provider",
                        f"{request.preferred_provider!r} requires the slower discovery path",
                    )
                continue
            if request.capability_slot not in entry["slots"]:
                raise ImportPlanError(
                    "slot-mismatch",
                    f"{request.preferred_provider} does not provide {request.capability_slot}",
                )
            unknown = sorted(set(request.required_features) - set(entry["exports"]))
            if unknown:
                raise ImportPlanError(
                    "undeclared-export",
                    f"{request.preferred_provider} surface does not approve {unknown}",
                )
            if request.preferred_provider == "gsap" and not self.policy.allow_gsap_license:
                raise ImportPlanError("gsap-license", "GSAP licence permission is not enabled")
        return requests

    def _run(self, argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "HOME": str(cwd),
            "npm_config_cache": str(cwd / ".npm-cache"),
            "npm_config_ignore_scripts": "true",
            "npm_config_audit": "false",
            "npm_config_fund": "false",
        }
        try:
            return subprocess.run(
                argv, cwd=cwd, env=env, text=True, capture_output=True,
                timeout=180, check=True,
            )
        except subprocess.TimeoutExpired as error:
            raise OperationalImportError("registry-timeout", str(error)) from error
        except (OSError, subprocess.CalledProcessError) as error:
            detail = getattr(error, "stderr", None) or str(error)
            raise OperationalImportError("tool-failure", str(detail)[-1200:]) from error

    def _npm_json(self, args: list[str], cwd: Path) -> Any:
        result = self._run(["npm", *args, "--json"], cwd)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise OperationalImportError("registry-response", str(error)) from error

    def _metadata(self, package: str, version: str | None, cwd: Path) -> dict[str, Any]:
        spec = f"{package}@{version}" if version else package
        data = self._npm_json(
            ["view", spec, "name", "version", "license", "repository", "homepage",
             "dist", "scripts", "exports", "engines", "browserslist", "browser",
             "module", "main", "type", "time", "deprecated", "readme",
             "--registry", self.policy.permitted_registries[0]],
            cwd,
        )
        if not isinstance(data, dict) or not data.get("version"):
            raise OperationalImportError("registry-response", f"no exact version for {package}")
        return data

    def _download(self, url: str) -> bytes:
        if not any(url.startswith(registry.rstrip("/") + "/")
                   for registry in self.policy.permitted_registries):
            raise ImportPlanError("registry-policy", f"archive outside permitted registries: {url}")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "DeepReason/0.1"})
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise OperationalImportError("download-failure", str(error)) from error

    def _evidence_artifact(
        self, payload: Any, *, codec: str = "json", source: str = "npm registry",
        design_id: str | None = None, package: str | None = None,
    ) -> str:
        content = canonical_json(payload) if codec == "json" else str(payload).encode()
        if design_id and package:
            # Use the canonical research channel: a scoped research problem,
            # accepted source-reliability support, relevance commitment, and
            # ordinary program criticism. Registration is not suitability;
            # policy/export/bundle commitments below still decide that.
            from deepreason.ontology import Budget, Commitment, Problem, ProblemProvenance
            from deepreason.ops import submit_evidence

            marker = json.dumps(f'"name":"{package}"')
            scope = Commitment(
                id=f"import-evidence-scope@{sha256_hex(canonical_json(package))[:16]}",
                eval=f"predicate:{marker} in content",
                budget=Budget(),
            )
            json_wf = Commitment(id="import-evidence-json@v1", eval="program:json-wf")
            for commitment in (json_wf, scope):
                if commitment.id not in self.harness.commitments:
                    self.harness.register_commitment(commitment)
            problem_id = f"pi-import-research-{sha256_hex(canonical_json([design_id, package]))[:20]}"
            if problem_id not in self.harness.state.problems:
                self.harness.register_problem(Problem(
                    id=problem_id,
                    description=(
                        f"verify current registry/package facts for {package}: exact version, "
                        "integrity, licence, public exports, browser surface and maintenance state"
                    ),
                    criteria=[json_wf.id, scope.id],
                    provenance=ProblemProvenance.model_validate({
                        "trigger": "research", "from": [design_id],
                    }),
                ))
            return submit_evidence(
                self.harness, problem_id, source, content, codec=codec,
                metadata={"package": package, "channel": "runtime-import"},
            ).id
        return self.harness.create_artifact(
            content, codec=codec, provenance=Provenance(role="import")
        ).id

    def _create_lock(self, exact: list[str], work: Path) -> dict[str, Any]:
        dependencies = {name: version for name, version in map(_exact_ref, exact)}
        (work / "package.json").write_bytes(canonical_json({
            "name": "deepreason-run-imports", "private": True, "version": "0.0.0",
            "dependencies": dependencies,
        }))
        self._run([
            "npm", "install", "--package-lock-only", "--ignore-scripts", "--save-exact",
            "--omit=dev", "--registry", self.policy.permitted_registries[0],
        ], work)
        try:
            return json.loads((work / "package-lock.json").read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise OperationalImportError("lockfile-failure", str(error)) from error

    def _alias_source(self, requests: list[DependencyRequest]) -> str:
        lines = [
            "globalThis.DeepReasonImports = globalThis.DeepReasonImports || Object.create(null);"
        ]
        for index, request in enumerate(requests):
            entry = self.catalog.get(request.preferred_provider, {})
            package = entry.get("package") or request.package
            imports = []
            members = []
            for feature in request.required_features:
                local = f"_dr_{index}_{re.sub(r'[^A-Za-z0-9_$]', '_', feature)}"
                if feature == "default":
                    imports.append(f"import {local} from {json.dumps(package)};")
                    members.append(f"default: {local}")
                else:
                    imports.append(
                        f"import {{ {feature} as {local} }} from {json.dumps(package)};"
                    )
                    members.append(f"{json.dumps(feature)}: {local}")
            lines[0:0] = imports
            lines.append(
                f"globalThis.DeepReasonImports.{request.alias} = Object.freeze({{{', '.join(members)}}});"
            )
        return "\n".join(lines) + "\n"

    def _capsule(self, request: DependencyRequest, package: str, version: str) -> dict[str, Any]:
        entry = self.catalog.get(request.preferred_provider, {})
        signatures = entry.get("exports", {})
        return {
            "alias": request.alias,
            "package": package,
            "version": version,
            "exports": [
                {"name": name, "signature": signatures.get(name, f"{name}: exported value")}
                for name in request.required_features
            ],
            "lifecycle": request.lifecycle,
            "cleanup": "component cleanup export must release every owned resource",
            "verified_patterns": list(entry.get("patterns", []))[:2],
            "restrictions": list(entry.get("restrictions", [])),
            "reduced_motion": request.reduced_motion,
            "fallback": request.fallback,
        }

    def resolve(
        self, manifest: Manifest, *, design_id: str | None = None
    ) -> ResolvedImportSet | None:
        requests = self.validate_request(manifest)
        if not requests:
            return None
        work = Path(tempfile.mkdtemp(prefix="resolve-", dir=self.root))
        evidence_ids: list[str] = []
        try:
            catalog_artifact = self.harness.create_artifact(
                canonical_json({
                    "catalog_ref": self.policy.catalog_ref,
                    "providers": assets.capability_catalog(),
                }),
                codec="json", provenance=Provenance(role="import"),
            )
            metadata: dict[str, dict[str, Any]] = {}
            exact: list[str] = []
            for request in requests:
                entry = self.catalog.get(request.preferred_provider, {})
                package = entry.get("package") or request.package
                if not package:
                    raise ImportPlanError("package-name", f"no package for {request.alias}")
                info = self._metadata(package, None, work)
                version = str(info["version"])
                exact.append(f"{package}@{version}")
                metadata[request.alias] = {**info, "package": package, "version": version}
                evidence_ids.append(self._evidence_artifact(
                    info, source=str(info.get("dist", {}).get("tarball") or
                                     self.policy.permitted_registries[0]),
                    design_id=design_id, package=package,
                ))
            builder_name, builder_version = _exact_ref(self.policy.builder_toolchain_ref)
            builder_info = self._metadata(builder_name, builder_version, work)
            evidence_ids.append(self._evidence_artifact(
                builder_info,
                source=str(builder_info.get("dist", {}).get("tarball") or
                           self.policy.permitted_registries[0]),
                design_id=design_id, package=builder_name,
            ))
            lock = self._create_lock([*exact, self.policy.builder_toolchain_ref], work)
            package_entries = [
                (path, item) for path, item in lock.get("packages", {}).items()
                if path and isinstance(item, dict) and item.get("resolved")
            ]
            runtime_paths = [p for p, _ in package_entries if not p.endswith("node_modules/esbuild")
                             and "/node_modules/@esbuild/" not in p
                             and not p.startswith("node_modules/@esbuild/")]
            transitive = max(0, len(runtime_paths) - len(requests))
            if transitive > self.policy.max_transitive_dependencies:
                raise ImportPlanError(
                    "transitive-limit",
                    f"{transitive} transitives exceed {self.policy.max_transitive_dependencies}",
                    evidence_ids,
                )
            archives: list[dict[str, Any]] = []
            archive_ids: list[str] = []
            licence_evidence: list[str] = []
            for install_path, item in package_entries:
                url, integrity = str(item["resolved"]), str(item.get("integrity", ""))
                data = self._download(url)
                if not integrity or not _integrity_matches(data, integrity):
                    raise OperationalImportError("integrity-mismatch", install_path)
                package_manifest, licence_text, unsupported_binary = _archive_manifest(data)
                is_builder = (
                    package_manifest.get("name") == builder_name
                    or str(package_manifest.get("name", "")).startswith("@esbuild/")
                )
                scripts = package_manifest.get("scripts") or {}
                lifecycle = sorted(set(scripts) & {"preinstall", "install", "postinstall"})
                if unsupported_binary and not is_builder:
                    raise OperationalImportError(
                        "unsupported-binary",
                        f"{package_manifest.get('name')} requires native compilation/binaries",
                    )
                if lifecycle and self.policy.lifecycle_scripts_forbidden and not is_builder:
                    raise OperationalImportError(
                        "forbidden-lifecycle-script",
                        f"{package_manifest.get('name')} declares {lifecycle}",
                    )
                licence = str(package_manifest.get("license") or item.get("license") or "")
                if not is_builder and licence not in self.policy.permitted_licenses:
                    if not (package_manifest.get("name") == "gsap"
                            and self.policy.allow_gsap_license):
                        ev = self._evidence_artifact({
                            "manifest": package_manifest, "license_file": licence_text,
                        }, source=url, design_id=design_id,
                            package=str(package_manifest.get("name") or "unknown"))
                        raise ImportPlanError(
                            "licence-policy",
                            f"{package_manifest.get('name')} has non-permitted licence {licence!r}",
                            [*evidence_ids, ev],
                        )
                evidence = self._evidence_artifact({
                    "manifest": package_manifest, "license_file": licence_text,
                }, source=url, design_id=design_id,
                    package=str(package_manifest.get("name") or "unknown"))
                licence_evidence.append(evidence)
                archive = self.harness.create_artifact(
                    data, codec="application/gzip", provenance=Provenance(role="import")
                )
                archive_ids.append(archive.id)
                archives.append({
                    "name": package_manifest.get("name"),
                    "version": package_manifest.get("version"),
                    "install_path": install_path,
                    "integrity": integrity,
                    "registry_source": url,
                    "archive_id": archive.id,
                    "license": licence,
                    "lifecycle_scripts": lifecycle,
                    "dependencies": sorted((package_manifest.get("dependencies") or {}).keys()),
                })
            evidence_ids.extend(licence_evidence)
            lock_artifact = self.harness.create_artifact(
                canonical_json(lock), codec="json", provenance=Provenance(role="import")
            )
            tool_archives = [a["archive_id"] for a in archives
                             if a["name"] == builder_name or str(a["name"]).startswith("@esbuild/")]
            toolchain = self.harness.create_artifact(
                canonical_json({
                    "toolchain": self.policy.builder_toolchain_ref,
                    "lockfile": lock_artifact.id,
                    "archives": tool_archives,
                }),
                codec="json",
                interface=Interface(refs=[
                    Ref(target=lock_artifact.id, role=RefRole.DEPENDENCE),
                    *(Ref(target=aid, role=RefRole.DEPENDENCE) for aid in tool_archives),
                ]),
                provenance=Provenance(role="import"),
            )
            capsule_ids: list[str] = []
            alias_ids: list[str] = []
            alias_source = self._alias_source(requests)
            for request in requests:
                info = metadata[request.alias]
                capsule = self.harness.create_artifact(
                    canonical_json(self._capsule(request, info["package"], info["version"])),
                    codec="json",
                    provenance=Provenance(role="import"),
                )
                capsule_ids.append(capsule.id)
            alias_artifact = self.harness.create_artifact(
                alias_source,
                codec="code:javascript",
                interface=Interface(refs=[
                    *(Ref(target=aid, role=RefRole.DEPENDENCE) for aid in capsule_ids),
                    Ref(target=toolchain.id, role=RefRole.DEPENDENCE),
                ]),
                provenance=Provenance(role="import"),
            )
            alias_ids.append(alias_artifact.id)
            resolved_stub = ResolvedImportSet(
                record_id="", catalog_id=catalog_artifact.id,
                lockfile_id=lock_artifact.id, toolchain_id=toolchain.id,
                capsule_ids=tuple(capsule_ids), alias_ids=tuple(alias_ids),
                archive_ids=tuple(archive_ids), requests=tuple(requests),
                packages=tuple(archives), toolchain_ref=self.policy.builder_toolchain_ref,
                evidence_ids=tuple(evidence_ids),
            )
            # This esbuild pass programmatically proves every selected export
            # exists before component problems are spawned.
            self._bundle_javascript(resolved_stub, alias_source, work / "verify")
            record_payload = {
                "schema": "resolved-import-v1",
                "catalog_label": self.policy.catalog_ref,
                "catalog_ref": catalog_artifact.id,
                "toolchain_ref": self.policy.builder_toolchain_ref,
                "policy": self.policy.model_dump(mode="json"),
                "requests": [r.model_dump(mode="json") for r in requests],
                "resolved": [
                    {
                        "alias": r.alias, "package": metadata[r.alias]["package"],
                        "version": metadata[r.alias]["version"],
                        "integrity": metadata[r.alias].get("dist", {}).get("integrity"),
                        "selected_exports": list(r.required_features),
                    } for r in requests
                ],
                "packages": archives,
                "lockfile": lock_artifact.id,
                "toolchain": toolchain.id,
                "api_capsules": capsule_ids,
                "aliases": alias_ids,
                "evidence": evidence_ids,
            }
            refs = [
                Ref(target=catalog_artifact.id, role=RefRole.DEPENDENCE),
                Ref(target=lock_artifact.id, role=RefRole.DEPENDENCE),
                Ref(target=toolchain.id, role=RefRole.DEPENDENCE),
                *(Ref(target=aid, role=RefRole.DEPENDENCE)
                  for aid in [*archive_ids, *capsule_ids, *alias_ids, *evidence_ids]),
            ]
            record = self.harness.create_artifact(
                canonical_json(record_payload), codec="json", interface=Interface(refs=refs),
                provenance=Provenance(role="import"),
            )
            return ResolvedImportSet(
                **{**resolved_stub.__dict__, "record_id": record.id}
            )
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def materialize(self, resolved: ResolvedImportSet, destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        node_modules = destination / "node_modules"
        try:
            lock = json.loads(_artifact_bytes(self.harness, resolved.lockfile_id))
        except (KeyError, json.JSONDecodeError) as error:
            raise ImportPlanError("lockfile-mismatch", str(error)) from error
        locked = {
            path: item for path, item in lock.get("packages", {}).items()
            if path and isinstance(item, dict) and item.get("resolved")
        }
        recorded = {package["install_path"]: package for package in resolved.packages}
        if set(locked) != set(recorded) or any(
            locked[path].get("version") != recorded[path].get("version")
            or locked[path].get("integrity") != recorded[path].get("integrity")
            for path in set(locked) & set(recorded)
        ):
            raise ImportPlanError(
                "lockfile-mismatch", "stored archives do not exactly match stored lockfile"
            )
        for package in resolved.packages:
            data = _artifact_bytes(self.harness, package["archive_id"])
            if not _integrity_matches(data, package["integrity"]):
                raise OperationalImportError("integrity-mismatch", package["install_path"])
            _safe_extract(data, destination / package["install_path"])
        (destination / "package-lock.json").write_bytes(
            _artifact_bytes(self.harness, resolved.lockfile_id)
        )
        return node_modules

    def _esbuild_path(self, resolved: ResolvedImportSet, work: Path) -> Path:
        name, _ = _exact_ref(resolved.toolchain_ref)
        path = work / "node_modules" / name / "bin" / "esbuild"
        if not path.exists():
            raise OperationalImportError("toolchain-unavailable", str(path))
        return path

    def _bundle_javascript(
        self, resolved: ResolvedImportSet, source: str, work: Path
    ) -> tuple[str, dict[str, Any], str]:
        work.mkdir(parents=True, exist_ok=True)
        self.materialize(resolved, work)
        (work / "entry.js").write_text(source)
        esbuild = self._esbuild_path(resolved, work)
        try:
            self._run([
                "node", str(esbuild), "entry.js", "--bundle", "--format=iife",
                "--platform=browser", "--target=es2020", "--minify",
                "--outfile=bundle.js", "--metafile=meta.json", "--log-level=error",
            ], work)
        except OperationalImportError as error:
            if "No matching export" in error.detail or "not exported" in error.detail:
                raise ImportPlanError("missing-export", error.detail, list(resolved.evidence_ids))
            if "[ERROR]" in error.detail:
                raise ImportPlanError(
                    "bundle-source", error.detail, list(resolved.evidence_ids)
                ) from error
            raise
        javascript = (work / "bundle.js").read_text()
        css = (work / "bundle.css").read_text() if (work / "bundle.css").exists() else ""
        metadata = json.loads((work / "meta.json").read_text())
        return javascript, metadata, css

    @staticmethod
    def _input_package(path: str) -> str | None:
        marker = "node_modules/"
        if marker not in path:
            return None
        tail = path.rsplit(marker, 1)[1]
        parts = tail.split("/")
        if not parts:
            return None
        return "/".join(parts[:2]) if parts[0].startswith("@") and len(parts) > 1 else parts[0]

    def _attribution(
        self, resolved: ResolvedImportSet, metadata: dict[str, Any]
    ) -> dict[str, dict[str, int]]:
        dependencies = {
            str(package["name"]): set(package.get("dependencies") or [])
            for package in resolved.packages
        }
        direct = {
            request.alias: str(
                self.catalog.get(request.preferred_provider, {}).get("package")
                or request.package
            )
            for request in resolved.requests
        }
        closure: dict[str, set[str]] = {}
        for alias, root in direct.items():
            seen, pending = set(), [root]
            while pending:
                name = pending.pop()
                if name in seen:
                    continue
                seen.add(name)
                pending.extend(sorted(dependencies.get(name, set()) - seen))
            closure[alias] = seen
        output: dict[str, dict[str, int]] = {
            alias: {"javascript_bytes": 0, "css_bytes": 0} for alias in direct
        }
        for output_path, detail in metadata.get("outputs", {}).items():
            byte_kind = "css_bytes" if output_path.endswith(".css") else "javascript_bytes"
            for input_path, contribution in detail.get("inputs", {}).items():
                package = self._input_package(input_path)
                if package is None:
                    continue
                for alias, owned in closure.items():
                    if package in owned:
                        output[alias][byte_kind] += int(contribution.get("bytesInOutput", 0))
        return output

    def bundle_components(
        self, manifest: Manifest, fragments: dict[str, str], resolved: ResolvedImportSet
    ) -> BundleResult:
        """Bundle approved aliases + component JS/CSS; leave only component HTML."""
        scripts: list[str] = [_artifact_bytes(self.harness, resolved.alias_ids[0]).decode()]
        styles: list[str] = []
        clean: dict[str, str] = {}
        for spec in manifest.ordered():
            fragment = fragments[spec.name]
            scripts.extend(re.findall(r"<script[^>]*>(.*?)</script>", fragment, re.S | re.I))
            styles.extend(re.findall(r"<style[^>]*>(.*?)</style>", fragment, re.S | re.I))
            fragment = re.sub(r"<script[^>]*>.*?</script>", "", fragment, flags=re.S | re.I)
            fragment = re.sub(r"<style[^>]*>.*?</style>", "", fragment, flags=re.S | re.I)
            clean[spec.name] = fragment
        lifecycle = shared_lifecycle_source(manifest)
        if lifecycle:
            scripts.append(lifecycle)
        build = Path(tempfile.mkdtemp(prefix="bundle-", dir=self.root))
        try:
            javascript, js_meta, runtime_css = self._bundle_javascript(
                resolved, "\n".join(scripts), build
            )
            (build / "entry.css").write_text("\n".join(styles))
            esbuild = self._esbuild_path(resolved, build)
            try:
                self._run([
                    "node", str(esbuild), "entry.css", "--bundle", "--minify",
                    "--outfile=component.css", "--metafile=css-meta.json", "--log-level=error",
                ], build)
            except OperationalImportError as error:
                if "[ERROR]" in error.detail:
                    raise ImportPlanError(
                        "bundle-source", error.detail, list(resolved.evidence_ids)
                    ) from error
                raise
            component_css = ((build / "component.css").read_text()
                             if (build / "component.css").exists() else "")
            css = runtime_css + component_css
            css_meta = json.loads((build / "css-meta.json").read_text())
            js_bytes, css_bytes = len(javascript.encode()), len(css.encode())
            if js_bytes > self.policy.max_javascript_bytes:
                raise ImportPlanError("javascript-budget", f"bundle is {js_bytes} bytes")
            if css_bytes > self.policy.max_css_bytes:
                raise ImportPlanError("css-budget", f"bundle is {css_bytes} bytes")
            attribution = self._attribution(resolved, js_meta)
            for request in resolved.requests:
                actual = attribution.get(request.alias, {})
                if actual.get("javascript_bytes", 0) > request.budget.javascript_bytes:
                    raise ImportPlanError(
                        "dependency-javascript-budget",
                        f"{request.alias} contributes {actual['javascript_bytes']} bytes",
                    )
                if actual.get("css_bytes", 0) > request.budget.css_bytes:
                    raise ImportPlanError(
                        "dependency-css-budget",
                        f"{request.alias} contributes {actual['css_bytes']} bytes",
                    )
            return BundleResult(
                fragments=clean, javascript=javascript, css=css,
                metadata={
                    "toolchain": resolved.toolchain_ref,
                    "javascript_bytes": js_bytes, "css_bytes": css_bytes,
                    "lifecycle_sha256": sha256_hex(lifecycle.encode()) if lifecycle else None,
                    "dependency_attribution": attribution,
                    "javascript": js_meta, "css": css_meta,
                },
                lifecycle_source=lifecycle,
            )
        finally:
            shutil.rmtree(build, ignore_errors=True)


def register_epistemic_import_failure(harness, design_id: str, error: ImportPlanError) -> None:
    """Put a demonstrated import-plan failure through the ordinary graph path."""
    from deepreason.ontology import Rule, Warrant, WarrantType

    refs = [Ref(target=aid, role=RefRole.EVIDENCE) for aid in error.evidence_ids]
    nu = harness.create_artifact(
        f"nu: import commitment {error.code} is sound and relevant — {error.detail}",
        interface=Interface(refs=refs), provenance=Provenance(role="critic"),
    )
    digest = sha256_hex(canonical_json({
        "target": design_id, "code": error.code, "detail": error.detail,
        "evidence": error.evidence_ids,
    }))[:20]
    harness.create_artifact(
        f"critic: accepted dependency request violates {error.code}: {error.detail}",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(
            id=f"w:import:{digest}", target=design_id, type=WarrantType.ARGUMENTATIVE,
            validity_node=nu.id,
        )],
        rule=Rule.CRIT,
    )


def resolve_for_design(harness, design_id: str, manifest: Manifest, config) -> ResolvedImportSet | None:
    """Workflow adapter: resolve, defer operational failures, criticize facts."""
    service = ImportService(harness, config.IMPORT_POLICY)
    try:
        return service.resolve(manifest, design_id=design_id)
    except OperationalImportError as error:
        harness.record_measure(inputs=["import-deferred", design_id, error.code])
        return None
    except ImportPlanError as error:
        register_epistemic_import_failure(harness, design_id, error)
        return None
