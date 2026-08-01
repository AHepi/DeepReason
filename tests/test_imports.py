"""Controlled project-local package imports extend the existing website path."""

import base64
import hashlib
import io
import json
import tarfile

import pytest
from pydantic import ValidationError

from deepreason.config import Config, ImportPolicy, apply_overrides
from deepreason.harness import Harness
from deepreason.imports import (
    ImportPlanError,
    ImportService,
    OperationalImportError,
    register_epistemic_import_failure,
    resolve_for_design,
    shared_lifecycle_source,
)
from deepreason.manifest import (
    ComponentSpec,
    Manifest,
    component_commitment,
    component_wf,
)
from deepreason.ontology import Interface, Provenance, Ref, Status


ART = {
    "motion_language": "brief elastic reveals that settle into stillness",
    "scroll_narrative": "sections reveal at their semantic boundary",
    "depth_structure": "foreground type over a quiet shallow field",
    "transition_grammar": "fast entrance, slow settle, direct exit",
    "texture_language": "subtle grain, no decorative shader by default",
    "reduced_motion_version": "all content present with opacity-only state changes",
    "static_fallback": "the complete typeset page without movement",
}


def request(provider="motion", alias="motion", slot="core-animation", **extra):
    value = {
        "capability_slot": slot,
        "artistic_requirement": "connect the chapter reveals",
        "technical_capability": "viewport and scroll-linked animation",
        "preferred_provider": provider,
        "alias": alias,
        "required_features": ["animate"],
        "intended_components": ["hero"],
        "reduced_motion": "render final states with no parallax",
        "fallback": "semantic static section",
        "lifecycle": "initialize once and cancel every subscription on cleanup",
        "budget": {"javascript_bytes": 50_000, "css_bytes": 2_000},
    }
    value.update(extra)
    return value


def manifest(*dependencies, component=None):
    default_component = {
        "name": "hero", "element_id": "hero-root", "css_prefix": "hero-",
        "runtime_imports": [d["alias"] for d in dependencies], "order": 0,
    }
    if dependencies:
        default_component.update({
            "js_exports": ["initHero", "destroyHero"],
            "lifecycle": {"animated": True, "initializer": "initHero",
                          "cleanup": "destroyHero", "frame_loop_owner": "shared"},
        })
    if any(d.get("canvas_id") for d in dependencies):
        canvas = next(d["canvas_id"] for d in dependencies if d.get("canvas_id"))
        default_component["lifecycle"].update({
            "webgl_canvas_id": canvas, "pixel_ratio_cap": 1.5,
            "context_loss": "replace with gradient", "static_fallback": "static gradient",
        })
    return Manifest.model_validate({
        "title": "Runtime site",
        "art_direction": ART if dependencies else None,
        "dependencies": list(dependencies),
        "components": [component or default_component],
    })


def _tgz(name, version, *, license="MIT", scripts=None, exports="export const animate=()=>{}"):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as archive:
        files = {
            "package/package.json": json.dumps({
                "name": name, "version": version, "license": license,
                "module": "index.js", "main": "index.js", "scripts": scripts or {},
            }).encode(),
            "package/index.js": exports.encode(),
            "package/LICENSE": f"{license} fixture".encode(),
        }
        for path, content in files.items():
            info = tarfile.TarInfo(path)
            info.size = len(content)
            info.mtime = 0
            archive.addfile(info, io.BytesIO(content))
    return data.getvalue()


def _integrity(data):
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()


def test_import_policy_is_nested_typed_and_unknown_fields_fail():
    configured = apply_overrides(
        Config(), {"IMPORT_POLICY.max_javascript_bytes": 123_456}
    )
    assert configured.IMPORT_POLICY.max_javascript_bytes == 123_456
    with pytest.raises(ValidationError, match="mystery"):
        Config.model_validate({"IMPORT_POLICY": {"mystery": True}})
    with pytest.raises(ValidationError, match="exact package@version"):
        ImportPolicy(builder_toolchain_ref="esbuild@latest")


def test_native_only_design_resolves_nothing_and_registers_no_packages(tmp_path):
    harness = Harness(tmp_path / "run")
    native = request(provider="native", alias="nativeMotion", package=None)
    component = {
        "name": "hero", "element_id": "hero-root", "css_prefix": "hero-",
        "runtime_imports": [], "js_exports": ["initHero", "destroyHero"],
        "lifecycle": {"animated": True, "initializer": "initHero",
                      "cleanup": "destroyHero", "frame_loop_owner": "shared"},
    }
    result = ImportService(harness, ImportPolicy()).resolve(manifest(native, component=component))
    assert result is None
    assert not [a for a in harness.state.artifacts.values()
                if a.provenance.role.value == "import"]


def test_core_engines_need_explicit_non_overlapping_ownership():
    anime = request(provider="animejs", alias="anime", required_features=["animate"])
    with pytest.raises(ValidationError, match="overlapping core animation"):
        manifest(request(), anime)
    accepted = manifest(
        request(ownership="DOM reveals", compatibility_commitment="distinct targets"),
        request(provider="animejs", alias="anime", ownership="SVG illustration",
                compatibility_commitment="distinct targets"),
    )
    assert len(accepted.dependencies) == 2


def test_multiple_scroll_coordinators_and_paper_ogl_default_pair_fail():
    one = request(provider="lenis", alias="scrollA", slot="scroll-coordination",
                  required_features=["default"])
    two = request(provider="lenis", alias="scrollB", slot="scroll-coordination",
                  required_features=["default"])
    with pytest.raises(ValidationError, match="multiple smooth-scroll"):
        manifest(one, two)
    paper = request(provider="paper-shaders", alias="paper", slot="visual-rendering",
                    required_features=["MeshGradient"], canvas_id="fx", pixel_ratio_cap=1.5,
                    context_loss="replace with gradient")
    ogl = request(provider="ogl", alias="ogl", slot="visual-rendering",
                  required_features=["Renderer"], canvas_id="fx", pixel_ratio_cap=1.5,
                  context_loss="replace with gradient")
    with pytest.raises(ValidationError, match="separate canvases"):
        manifest(paper, ogl)


def test_component_cannot_import_packages_or_undeclared_aliases():
    spec = ComponentSpec.model_validate({
        "name": "hero", "element_id": "hero-root", "css_prefix": "hero-",
        "runtime_imports": ["motion"],
    })
    commitment = component_commitment(spec, 4000, [])
    direct = '<div id="hero-root"></div><script>import {animate} from "motion";</script>'
    verdict, trace = component_wf(direct, commitment.budget)
    assert verdict == "fail"
    assert any("direct or dynamic" in item for item in trace["violations"])
    rogue = ('<div id="hero-root"></div><script>'
             'DeepReasonImports.anime.animate("x",{});</script>')
    verdict, trace = component_wf(rogue, commitment.budget)
    assert verdict == "fail"
    assert any("undeclared runtime import alias" in item for item in trace["violations"])


def test_animated_component_requires_cleanup_reduced_motion_and_raf_cancel():
    component = {
        "name": "hero", "element_id": "hero-root", "css_prefix": "hero-",
        "js_exports": ["initHero", "destroyHero"],
        "lifecycle": {"animated": True, "initializer": "initHero", "cleanup": "destroyHero",
                      "frame_loop_owner": "component"},
    }
    spec = ComponentSpec.model_validate(component)
    commitment = component_commitment(spec, 4000, [])
    bad = '''<div id="hero-root"></div><script>
window.initHero = function(){ requestAnimationFrame(window.initHero); };
window.destroyHero = function(){};
</script>'''
    verdict, trace = component_wf(bad, commitment.budget)
    assert verdict == "fail"
    assert any("prefers-reduced-motion" in v for v in trace["violations"])
    assert any("cancellation path" in v for v in trace["violations"])


def test_shared_lifecycle_initializes_and_cleans_components_in_reverse_order():
    first = request(alias="first", ownership="one", compatibility_commitment="split")
    second = request(provider="animejs", alias="second", ownership="two",
                     compatibility_commitment="split")
    value = Manifest.model_validate({
        "title": "x", "art_direction": ART, "dependencies": [first, second],
        "components": [
            {"name": "hero", "element_id": "hero-root", "css_prefix": "hero-",
             "runtime_imports": ["first", "second"], "js_exports": ["initHero", "stopHero"],
             "lifecycle": {"animated": True, "initializer": "initHero",
                           "cleanup": "stopHero", "frame_loop_owner": "shared"}},
        ],
    })
    source = shared_lifecycle_source(value)
    assert "DeepReasonLifecycle" in source
    assert "DOMContentLoaded" in source and "pagehide" in source
    assert source.index("initHero") < source.index("stopHero")


def test_resolution_records_exact_archives_lock_capsule_alias_evidence_and_toolchain(
        tmp_path, monkeypatch):
    harness = Harness(tmp_path / "run")
    service = ImportService(harness, ImportPolicy())
    design = harness.create_artifact("accepted design", provenance=Provenance(role="conjecturer"))
    motion = _tgz("motion", "1.2.3")
    builder = _tgz("esbuild", "0.28.1", scripts={"postinstall": "node install.js"})
    urls = {"https://registry.npmjs.org/motion/-/motion-1.2.3.tgz": motion,
            "https://registry.npmjs.org/esbuild/-/esbuild-0.28.1.tgz": builder}

    def metadata(package, version, work):
        resolved_version = version or "1.2.3"
        data = builder if package == "esbuild" else motion
        return {"name": package, "version": resolved_version, "license": "MIT",
                "dist": {"integrity": _integrity(data),
                         "tarball": next(u for u in urls if f"/{package}/-" in u)}}

    lock = {"lockfileVersion": 3, "packages": {
        "": {"dependencies": {"motion": "1.2.3", "esbuild": "0.28.1"}},
        "node_modules/motion": {"version": "1.2.3", "resolved": list(urls)[0],
                                "integrity": _integrity(motion), "license": "MIT"},
        "node_modules/esbuild": {"version": "0.28.1", "resolved": list(urls)[1],
                                 "integrity": _integrity(builder), "license": "MIT"},
    }}
    monkeypatch.setattr(service, "_metadata", metadata)
    monkeypatch.setattr(service, "_create_lock", lambda exact, work: lock)
    monkeypatch.setattr(service, "_download", lambda url: urls[url])
    monkeypatch.setattr(service, "_bundle_javascript",
                        lambda resolved, source, work: ("verified", {"inputs": {}}))

    resolved = service.resolve(manifest(request()), design_id=design.id)
    assert resolved is not None
    record = json.loads(harness.blobs.get(
        harness.state.artifacts[resolved.record_id].content_ref
    ))
    assert record["resolved"][0]["version"] == "1.2.3"
    assert record["resolved"][0]["selected_exports"] == ["animate"]
    assert record["lockfile"] == resolved.lockfile_id
    assert record["toolchain"] == resolved.toolchain_id
    assert record["catalog_ref"] == resolved.catalog_id
    assert record["api_capsules"] and record["aliases"] and record["evidence"]
    assert len(record["packages"]) == 2
    assert all(package["archive_id"] in resolved.archive_ids
               for package in record["packages"])
    assert any(problem.id.startswith("pi-import-research-")
               for problem in harness.state.problems.values())
    assert any(event.inputs and event.inputs[0] == "research-evidence-registered"
               for event in harness.log.read())
    attribution = service._attribution(resolved, {"outputs": {"bundle.js": {"inputs": {
        "node_modules/motion/index.js": {"bytesInOutput": 321},
        "entry.js": {"bytesInOutput": 9},
    }}}})
    assert attribution["motion"]["javascript_bytes"] == 321
    offline = tmp_path / "offline-materialization"
    monkeypatch.setattr(service, "_download", lambda url: (_ for _ in ()).throw(
        AssertionError("replay/materialization must not contact the registry")
    ))
    service.materialize(resolved, offline)
    assert (offline / "node_modules" / "motion" / "package.json").exists()
    # The permanent repository dependency tree was not mutated.
    assert not (tmp_path.parent / "node_modules").exists()
    replay = Harness(tmp_path / "run")
    assert replay.state.status == harness.state.status
    assert resolved.record_id in replay.state.artifacts


def test_resolution_operational_failure_defers_without_warrant(tmp_path, monkeypatch):
    harness = Harness(tmp_path / "run")
    design = harness.create_artifact("design", provenance=Provenance(role="conjecturer"))
    monkeypatch.setattr(
        ImportService, "_metadata",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            OperationalImportError("registry-timeout", "offline")
        ),
    )
    result = resolve_for_design(harness, design.id, manifest(request()), Config())
    assert result is None
    assert harness.state.status[design.id] == Status.ACCEPTED
    assert not harness.warrants
    assert any(e.inputs[:3] == ["import-deferred", design.id, "registry-timeout"]
               for e in harness.log.read())


def test_epistemic_import_failure_uses_evidence_on_validity_node(tmp_path):
    harness = Harness(tmp_path / "run")
    design = harness.create_artifact("design", provenance=Provenance(role="conjecturer"))
    evidence = harness.create_artifact(b"registry metadata", provenance=Provenance(role="import"))
    register_epistemic_import_failure(
        harness, design.id, ImportPlanError("licence-policy", "forbidden", [evidence.id])
    )
    assert harness.state.status[design.id] == Status.REFUTED
    warrant = next(iter(harness.warrants.values()))
    nu = harness.state.artifacts[warrant.validity_node]
    assert any(ref.target == evidence.id and ref.role.value == "evidence"
               for ref in nu.interface.refs)


def test_component_import_lineage_is_machine_checked(tmp_path):
    harness = Harness(tmp_path / "run")
    resolved = harness.create_artifact("resolved", provenance=Provenance(role="import"))
    spec = ComponentSpec.model_validate({
        "name": "hero", "element_id": "hero-root", "css_prefix": "hero-",
        "runtime_imports": ["motion"],
    })
    commitment = component_commitment(spec, 4000, [], [resolved.id])
    content = '<div id="hero-root"></div>'
    artifact = harness.create_artifact(content, provenance=Provenance(role="conjecturer"))
    verdict, trace = component_wf(content, commitment.budget, artifact)
    assert verdict == "fail" and "missing dependence ref" in trace["violations"][0]
    carried = harness.create_artifact(
        content, interface=Interface(refs=[Ref(target=resolved.id, role="dependence")]),
        provenance=Provenance(role="conjecturer"),
    )
    assert component_wf(content, commitment.budget, carried)[0] == "pass"
