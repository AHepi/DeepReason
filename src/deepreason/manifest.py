"""Component manifests: chunked website builds for small-context models.

A live run forced the model to emit ONE complete HTML document per
candidate (35k-token generations against a small context window —
truncations and transport timeouts were the observable symptoms). The
chunked pipeline replaces that shape:

    plan -> design (carries a COMPONENT MANIFEST) -> one component problem
    per manifest entry -> deterministic assembly -> integration criticism

The manifest is part of an ordinary, criticizable design artifact — never
a schema outside the graph. Its declared contracts (mount ids, CSS
namespaces, JS exports/uses, custom events, vendored libs, order, size
bounds) become machine-checkable commitments on the component problems, so
cross-component assumptions are explicit and testable, and the assembled
page can be composed by repository code instead of one giant LLM call.

Nothing here is final or beyond criticism: program verdicts reliably
establish that a declared test failed, while the test's own soundness and
relevance remain attackable through the commitment's validity node, like
every other machine check in the harness.

Everything in this module is a deterministic pure function of artifact
bytes and frozen commitment specs (§0): no wall clock, no randomness, no
LLM — verdicts and assembled pages replay byte-for-byte.
"""

import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.commitment import Budget, Commitment

PASS, FAIL = "pass", "fail"

# DOM events a fragment may listen for without declaring them — declaring
# `click` would be ceremony; CUSTOM events are the cross-component wiring
# and must be declared in the manifest.
_DOM_EVENTS = frozenset({
    "click", "dblclick", "input", "change", "submit", "reset", "keydown",
    "keyup", "keypress", "focus", "blur", "focusin", "focusout", "load",
    "DOMContentLoaded", "scroll", "resize", "mouseover", "mouseout",
    "mouseenter", "mouseleave", "mousedown", "mouseup", "mousemove",
    "touchstart", "touchend", "touchmove", "pointerdown", "pointerup",
    "pointermove", "dragstart", "dragend", "dragover", "drop", "wheel",
    "animationend", "transitionend", "visibilitychange", "hashchange",
    "popstate", "storage", "toggle", "close", "error",
})

# window.* members a fragment may CALL without declaring a dependency —
# the browser's own surface, not another component's export.
_WINDOW_BUILTINS = frozenset({
    "addEventListener", "removeEventListener", "dispatchEvent",
    "requestAnimationFrame", "cancelAnimationFrame", "setTimeout",
    "setInterval", "clearTimeout", "clearInterval", "matchMedia",
    "getComputedStyle", "scrollTo", "scrollBy", "alert", "confirm",
    "prompt", "open", "fetch", "atob", "btoa", "structuredClone",
})

CapabilitySlot = Literal[
    "core-animation", "scroll-coordination", "visual-rendering",
    "navigation-transition",
]


class ArtDirection(BaseModel):
    """The design language comes first; packages are only its substrate."""

    model_config = ConfigDict(extra="forbid")

    motion_language: str = Field(min_length=1)
    scroll_narrative: str = Field(min_length=1)
    depth_structure: str = Field(min_length=1)
    transition_grammar: str = Field(min_length=1)
    texture_language: str = Field(min_length=1)
    reduced_motion_version: str = Field(min_length=1)
    static_fallback: str = Field(min_length=1)


class ImportBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    javascript_bytes: int = Field(default=0, ge=0)
    css_bytes: int = Field(default=0, ge=0)


class DependencyRequest(BaseModel):
    """What an accepted design wants, never an unresolved install record."""

    model_config = ConfigDict(extra="forbid")

    capability_slot: CapabilitySlot
    artistic_requirement: str = Field(min_length=1)
    technical_capability: str = Field(min_length=1)
    preferred_provider: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    package: str | None = None
    alias: str = Field(pattern=r"^[A-Za-z_$][\w$]*$")
    required_features: list[str] = Field(min_length=1)
    intended_components: list[str] = Field(min_length=1)
    reduced_motion: str = Field(min_length=1)
    fallback: str = Field(min_length=1)
    lifecycle: str = Field(min_length=1)
    budget: ImportBudget
    ownership: str | None = None
    compatibility_commitment: str | None = None
    canvas_id: str | None = None
    pixel_ratio_cap: float | None = Field(default=None, gt=0)
    context_loss: str | None = None

    @field_validator("package")
    @classmethod
    def _request_never_resolves_versions(cls, value):
        if value is None:
            return value
        # Scoped package names contain one leading @; a second @ is a version.
        tail = value[1:] if value.startswith("@") else value
        if "@" in tail or any(c in value for c in "*^~<>= "):
            raise ValueError("dependency requests name packages but never versions or ranges")
        return value

    @model_validator(mode="after")
    def _runtime_request_has_a_budget(self):
        if (self.preferred_provider != "native"
                and self.budget.javascript_bytes == 0
                and self.budget.css_bytes == 0):
            raise ValueError("runtime dependency requests require a non-zero bundle budget")
        return self


class AnimationLifecycle(BaseModel):
    """Bounded component ownership for listeners, observers and animation."""

    model_config = ConfigDict(extra="forbid")

    animated: bool = False
    initializer: str | None = None
    cleanup: str | None = None
    frame_loop_owner: Literal["none", "shared", "component"] = "none"
    webgl_canvas_id: str | None = None
    pixel_ratio_cap: float | None = Field(default=None, gt=0)
    context_loss: str | None = None
    static_fallback: str | None = None

    @model_validator(mode="after")
    def _animated_contract_is_bounded(self):
        if self.animated and (not self.initializer or not self.cleanup):
            raise ValueError("animated components require initializer and cleanup exports")
        if self.webgl_canvas_id and (
            self.pixel_ratio_cap is None or not self.context_loss or not self.static_fallback
        ):
            raise ValueError(
                "WebGL ownership requires pixel_ratio_cap, context_loss and static_fallback"
            )
        return self


class ComponentSpec(BaseModel):
    """One manifest entry: a component's identity and integration contract."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    purpose: str = ""
    element_id: str = Field(pattern=r"^[A-Za-z][\w-]*$")  # root mount id
    css_prefix: str = Field(pattern=r"^[a-z][\w-]*-$")    # class namespace it owns
    js_exports: list[str] = Field(default_factory=list)   # window.<name> it defines
    js_uses: list[str] = Field(default_factory=list)      # upstream exports it calls
    events_emitted: list[str] = Field(default_factory=list)
    events_listened: list[str] = Field(default_factory=list)
    libs: list[str] = Field(default_factory=list)         # vendored catalog picks
    runtime_imports: list[str] = Field(default_factory=list)  # design aliases only
    lifecycle: AnimationLifecycle = Field(default_factory=AnimationLifecycle)
    order: int = 0                                        # assembly position
    max_chars: int | None = Field(default=None, gt=0)     # per-chunk size bound

    @field_validator("js_exports", "js_uses")
    @classmethod
    def _identifiers(cls, value):
        for name in value:
            if not re.fullmatch(r"[A-Za-z_$][\w$]*", name):
                raise ValueError(f"not a JS identifier: {name!r}")
        return value

    @model_validator(mode="after")
    def _lifecycle_exports_exist(self):
        required = {x for x in (self.lifecycle.initializer, self.lifecycle.cleanup) if x}
        missing = sorted(required - set(self.js_exports))
        if missing:
            raise ValueError(f"lifecycle export(s) missing from js_exports: {missing}")
        return self


class Manifest(BaseModel):
    """The parseable contract block inside a design artifact."""

    model_config = ConfigDict(extra="forbid")

    title: str = ""
    architecture: Literal["single-document", "multi-page"] = "single-document"
    libs: list[str] = Field(default_factory=list)  # page-level catalog picks
    art_direction: ArtDirection | None = None
    dependencies: list[DependencyRequest] = Field(default_factory=list)
    components: list[ComponentSpec] = Field(min_length=1, max_length=12)

    @field_validator("components")
    @classmethod
    def _contracts_are_unambiguous(cls, comps):
        for field in ("name", "element_id", "css_prefix", "order"):
            values = [getattr(c, field) for c in comps]
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate component {field} in manifest")
        exports: dict[str, str] = {}
        for c in comps:
            for name in c.js_exports:
                if name in exports:
                    raise ValueError(
                        f"export {name!r} claimed by both {exports[name]!r} "
                        f"and {c.name!r}"
                    )
                exports[name] = c.name
        return comps

    @model_validator(mode="after")
    def _dependency_plan_is_coherent(self):
        if self.dependencies and self.art_direction is None:
            raise ValueError("runtime dependencies require art_direction before package choices")
        component_names = {c.name for c in self.components}
        aliases: set[str] = set()
        by_slot: dict[str, list[DependencyRequest]] = {}
        by_provider: dict[str, DependencyRequest] = {}
        for request in self.dependencies:
            if request.alias in aliases:
                raise ValueError(f"duplicate dependency alias {request.alias!r}")
            aliases.add(request.alias)
            unknown = sorted(set(request.intended_components) - component_names)
            if unknown:
                raise ValueError(
                    f"dependency {request.alias!r} names unknown components {unknown}"
                )
            by_slot.setdefault(request.capability_slot, []).append(request)
            by_provider[request.preferred_provider] = request
            if request.preferred_provider == "swup" and self.architecture != "multi-page":
                raise ValueError("Swup requires an accepted multi-page architecture")
            if request.capability_slot == "visual-rendering" and request.preferred_provider in {
                "paper-shaders", "ogl",
            } and (not request.canvas_id or request.pixel_ratio_cap is None
                   or not request.context_loss):
                raise ValueError(
                    f"{request.preferred_provider} requires canvas_id, pixel_ratio_cap "
                    "and context_loss"
                )
        if len(by_slot.get("scroll-coordination", [])) > 1:
            raise ValueError("multiple smooth-scroll coordinators are forbidden")
        core = by_slot.get("core-animation", [])
        if len(core) > 1 and any(
            not r.ownership or not r.compatibility_commitment for r in core
        ):
            raise ValueError(
                "overlapping core animation engines require non-overlapping ownership "
                "and an explicit compatibility commitment"
            )
        if len(core) > 1 and len({r.ownership for r in core}) != len(core):
            raise ValueError("core animation engine ownership must be non-overlapping")
        if {"paper-shaders", "ogl"} <= set(by_provider):
            paper, ogl = by_provider["paper-shaders"], by_provider["ogl"]
            if (paper.canvas_id == ogl.canvas_id or not paper.ownership or not ogl.ownership
                    or not paper.compatibility_commitment or not ogl.compatibility_commitment):
                raise ValueError(
                    "Paper Shaders and OGL require separate canvases, ownership and "
                    "compatibility commitments"
                )
        for component in self.components:
            undeclared = sorted(set(component.runtime_imports) - aliases)
            if undeclared:
                raise ValueError(
                    f"component {component.name!r} uses undeclared import aliases {undeclared}"
                )
            for alias in component.runtime_imports:
                request = next(r for r in self.dependencies if r.alias == alias)
                if request.preferred_provider == "native":
                    raise ValueError(
                        f"native capability {alias!r} uses browser APIs, not an import alias"
                    )
                if component.name not in request.intended_components:
                    raise ValueError(
                        f"component {component.name!r} is outside alias {alias!r} ownership"
                    )
        components = {c.name: c for c in self.components}
        for request in self.dependencies:
            if request.capability_slot in {
                "core-animation", "scroll-coordination", "visual-rendering",
            }:
                unbounded = sorted(
                    name for name in request.intended_components
                    if not components[name].lifecycle.animated
                )
                if unbounded:
                    raise ValueError(
                        f"animated import {request.alias!r} requires bounded lifecycle "
                        f"contracts on {unbounded}"
                    )
            if request.canvas_id and not any(
                components[name].lifecycle.webgl_canvas_id == request.canvas_id
                for name in request.intended_components
            ):
                raise ValueError(
                    f"canvas {request.canvas_id!r} has no owning component lifecycle"
                )
        return self

    def ordered(self) -> list[ComponentSpec]:
        return sorted(self.components, key=lambda c: (c.order, c.name))

    def exports(self) -> set[str]:
        return {name for c in self.components for name in c.js_exports}

    def emitted_events(self) -> set[str]:
        return {e for c in self.components for e in c.events_emitted}


_MANIFEST_BLOCK = re.compile(r"```manifest\s*\n(.*?)```", re.S)


def parse_manifest(text: str, known_libs: set[str] | None = None
                   ) -> tuple[Manifest | None, str]:
    """Extract and validate the ```manifest fenced block. Returns
    (manifest, "") or (None, reason). Pure function of the text."""
    match = _MANIFEST_BLOCK.search(text or "")
    if not match:
        return None, "no ```manifest fenced block found"
    try:
        manifest = Manifest.model_validate(json.loads(match.group(1)))
    except ValueError as e:
        return None, f"manifest invalid: {e}"[:400]
    if known_libs is not None:
        unknown = sorted(
            {lib for c in manifest.components for lib in c.libs}
            .union(manifest.libs) - known_libs
        )
        if unknown:
            return None, (
                f"unknown libs {unknown}: the vendored catalog offers "
                f"{sorted(known_libs)}"
            )
    for c in manifest.components:
        undeclared = sorted(set(c.js_uses) - (manifest.exports() - set(c.js_exports)))
        if undeclared:
            return None, (
                f"component {c.name!r} uses {undeclared} which no other "
                "component exports"
            )
    return manifest, ""


# --------------------------------------------------------------------- #
# Programs (deterministic verdicts; wired into programs.PROGRAMS)


def manifest_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    """A design candidate must carry a valid COMPONENT MANIFEST. The known
    lib names are frozen into budget.extra so the verdict is replay-stable
    even if the shipped catalog later grows."""
    known = {x for x in str((budget.extra or {}).get("libs", "")).split(",") if x}
    manifest, error = parse_manifest(text, known_libs=known or None)
    if manifest is None:
        return FAIL, {"reason": error}
    return PASS, {"components": len(manifest.components)}


def _ids_in(content: str) -> list[str]:
    return re.findall(r"""\bid\s*=\s*["']([^"']+)["']""", content)


def _style_blocks(content: str) -> list[str]:
    return re.findall(r"<style[^>]*>(.*?)</style>", content, re.S | re.I)


def _script_blocks(content: str) -> list[str]:
    return re.findall(r"<script[^>]*>(.*?)</script>", content, re.S | re.I)


def _css_violations(css: str, element_id: str, css_prefix: str) -> list[str]:
    """Every top-level rule must be scoped to the component's mount id or
    its owned class namespace; keyframe names live in the namespace too."""
    out = []
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for name in re.findall(r"@keyframes\s+([\w-]+)", css):
        if not name.startswith(css_prefix):
            out.append(f"keyframes {name!r} outside namespace {css_prefix!r}")
    body = re.sub(r"@keyframes\s+[\w-]+\s*{", "{", css)
    for selector in re.findall(r"(?:^|[}{;])\s*([^{}@;]+?)\s*\{", body):
        selector = selector.strip()
        if not selector:
            continue
        if f"#{element_id}" in selector or f".{css_prefix}" in selector:
            continue
        out.append(f"selector {selector[:60]!r} not scoped to "
                   f"#{element_id} or .{css_prefix}*")
    return out


def _js_violations(js: str, spec: ComponentSpec, allowed_uses: set[str]) -> list[str]:
    out = []
    js = re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", js, flags=re.S))
    if re.search(r"\bimport\s*(?:\(|[\s{*])|\brequire\s*\(", js):
        out.append(
            "direct or dynamic package imports are forbidden; use DeepReasonImports aliases"
        )
    if re.search(r"(?:https?:)?//|\b(?:fetch|XMLHttpRequest)\s*\(", js):
        out.append("remote dependencies or network imports are forbidden")
    aliases = set(re.findall(
        r"\bDeepReasonImports\.([A-Za-z_$][\w$]*)", js
    ))
    undeclared_aliases = sorted(aliases - set(spec.runtime_imports))
    if undeclared_aliases:
        out.append(f"undeclared runtime import alias(es): {', '.join(undeclared_aliases)}")
    assigned = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=(?!=)", js))
    undeclared = sorted(assigned - set(spec.js_exports))
    if undeclared:
        out.append(f"undeclared global assignment(s): window.{', window.'.join(undeclared)}")
    missing = sorted(set(spec.js_exports) - assigned)
    if missing:
        out.append(f"declared export(s) never defined: {', '.join(missing)}")
    called = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*\(", js))
    foreign = sorted(
        called - set(spec.js_exports) - allowed_uses - _WINDOW_BUILTINS
    )
    if foreign:
        out.append(f"undeclared dependency call(s): window.{', window.'.join(foreign)}")
    emitted = set(re.findall(r"""CustomEvent\(\s*["']([\w:.-]+)["']""", js))
    rogue = sorted(emitted - set(spec.events_emitted))
    if rogue:
        out.append(f"undeclared custom event(s) emitted: {', '.join(rogue)}")
    listened = set(re.findall(r"""addEventListener\(\s*["']([\w:.-]+)["']""", js))
    rogue_listen = sorted(
        listened - set(spec.events_listened) - _DOM_EVENTS
    )
    if rogue_listen:
        out.append(f"undeclared custom event(s) listened for: {', '.join(rogue_listen)}")
    if spec.lifecycle.animated:
        if "prefers-reduced-motion" not in js:
            out.append("animated component does not implement prefers-reduced-motion")
        cleanup = spec.lifecycle.cleanup or ""
        if cleanup and not re.search(rf"window\.{re.escape(cleanup)}\s*=(?!=)", js):
            out.append(f"cleanup export {cleanup!r} is not defined")
        if "requestAnimationFrame" in js and "cancelAnimationFrame" not in js:
            out.append("animation frame loop has no cancellation path")
    return out


def component_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    """The chunk contract: bounded, a fragment (not a document), mounted at
    the declared id, namespaced CSS, declared JS surface. The full spec is
    frozen into budget.extra, so the verdict replays byte-for-byte."""
    try:
        spec_blob = json.loads((budget.extra or {}).get("spec", "{}"))
        spec = ComponentSpec.model_validate(spec_blob["component"])
        max_chars = int(spec_blob.get("max_chars") or 4000)
        allowed_uses = set(spec_blob.get("allowed_uses") or [])
        import_ids = set(spec_blob.get("import_ids") or [])
    except (ValueError, KeyError, TypeError) as e:
        return FAIL, {"reason": f"unreadable component spec: {e}"}

    violations: list[str] = []
    limit = spec.max_chars or max_chars
    if len(text) > limit:
        violations.append(f"oversized: {len(text)} chars > {limit}")
    if re.search(r"<!doctype|<html\b|<head\b|<body\b", text, re.I):
        violations.append("full HTML document where a fragment is required")
    ids = _ids_in(text)
    if spec.element_id not in ids:
        violations.append(f"missing declared mount id #{spec.element_id}")
    foreign_ids = sorted(
        {i for i in ids
         if i != spec.element_id and not i.startswith(spec.element_id + "-")}
    )
    if foreign_ids:
        violations.append(
            f"id(s) outside the component's namespace: {', '.join(foreign_ids)} "
            f"(use #{spec.element_id} or #{spec.element_id}-*)"
        )
    for css in _style_blocks(text):
        violations.extend(_css_violations(css, spec.element_id, spec.css_prefix))
    for js in _script_blocks(text):
        violations.extend(_js_violations(js, spec, allowed_uses))
    if import_ids and artifact is not None:
        declared = {
            ref.target for ref in artifact.interface.refs
            if str(ref.role.value if hasattr(ref.role, "value") else ref.role) == "dependence"
        }
        missing_import_refs = sorted(import_ids - declared)
        if missing_import_refs:
            violations.append(
                "missing dependence ref(s) to resolved import record: "
                + ", ".join(x[:12] for x in missing_import_refs)
            )
    if violations:
        return FAIL, {"component": spec.name, "violations": violations}
    return PASS, {"component": spec.name, "chars": len(text)}


def integration_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    """Global coherence of the ASSEMBLED page: locally valid components can
    still compose into a broken application. Static half of integration
    criticism (the browser commitment is the executable half). Violations
    name the implicated component so failures spawn TARGETED repair."""
    try:
        manifest = Manifest.model_validate(
            json.loads((budget.extra or {}).get("spec", "{}"))["manifest"]
        )
    except (ValueError, KeyError, TypeError) as e:
        return FAIL, {"reason": f"unreadable manifest spec: {e}"}

    violations: list[str] = []
    implicated: set[str] = set()
    if len(re.findall(r"<!doctype", text, re.I)) != 1:
        violations.append("assembled page must contain exactly one doctype")
    if re.search(
        r"<(?:script|link|img|source)\b[^>]+(?:src|href)\s*=\s*[\"'](?:https?:)?//"
        r"|\bimport\s*\(\s*[\"']https?://"
        r"|url\(\s*[\"']?https?://",
        text,
        re.I,
    ):
        violations.append("assembled page retains a remote dependency")
    ids = _ids_in(text)
    counts: dict[str, int] = {}
    for i in ids:
        counts[i] = counts.get(i, 0) + 1
    for c in manifest.components:
        if counts.get(c.element_id, 0) == 0:
            violations.append(f"component {c.name!r} mount #{c.element_id} missing")
            implicated.add(c.name)
        elif counts[c.element_id] > 1:
            violations.append(f"mount #{c.element_id} duplicated")
            implicated.add(c.name)
    dupes = sorted(i for i, n in counts.items() if n > 1)
    if dupes:
        violations.append(f"duplicate id(s): {', '.join(dupes)}")
        for c in manifest.components:
            if any(d == c.element_id or d.startswith(c.element_id + "-") for d in dupes):
                implicated.add(c.name)
    js = "\n".join(_script_blocks(text))
    assigned = set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=(?!=)", js))
    for c in manifest.components:
        undefined = sorted(set(c.js_exports) - assigned)
        if undefined:
            violations.append(
                f"component {c.name!r} never defines declared export(s): "
                f"{', '.join(undefined)}"
            )
            implicated.add(c.name)
    for c in manifest.components:
        unmet = sorted(set(c.js_uses) - assigned)
        if unmet:
            violations.append(
                f"component {c.name!r} depends on unavailable export(s): "
                f"{', '.join(unmet)}"
            )
            implicated.add(c.name)
            implicated.update(
                other.name for other in manifest.components
                if set(other.js_exports) & set(unmet)
            )
    emitted = set(re.findall(r"""CustomEvent\(\s*["']([\w:.-]+)["']""", js))
    for c in manifest.components:
        silent = sorted(
            e for e in c.events_listened
            if e not in _DOM_EVENTS and e not in emitted
        )
        if silent:
            violations.append(
                f"component {c.name!r} listens for event(s) nothing emits: "
                f"{', '.join(silent)}"
            )
            implicated.add(c.name)
    if violations:
        return FAIL, {"violations": violations, "implicated": sorted(implicated)}
    return PASS, {"components": len(manifest.components)}


# --------------------------------------------------------------------- #
# Commitment builders (content-addressed; replay-stable)


def manifest_commitment(known_libs: set[str]) -> Commitment:
    libs = ",".join(sorted(known_libs))
    digest = sha256_hex(canonical_json(libs))[:12]
    return Commitment(
        id=f"manifest-wf@{digest}",
        eval="program:manifest_wf",
        budget=Budget(extra={"libs": libs}),
    )


def component_commitment(spec: ComponentSpec, max_chars: int,
                         allowed_uses: list[str],
                         import_ids: list[str] | None = None) -> Commitment:
    blob = {
        "component": spec.model_dump(),
        "max_chars": max_chars,
        "allowed_uses": sorted(allowed_uses),
        "import_ids": sorted(import_ids or []),
    }
    digest = sha256_hex(canonical_json(blob))[:12]
    return Commitment(
        id=f"component-wf@{digest}",
        eval="program:component_wf",
        budget=Budget(extra={"spec": json.dumps(blob, sort_keys=True)}),
    )


def integration_commitment(manifest: Manifest) -> Commitment:
    blob = {"manifest": manifest.model_dump()}
    digest = sha256_hex(canonical_json(blob))[:12]
    return Commitment(
        id=f"integration-wf@{digest}",
        eval="program:integration_wf",
        budget=Budget(extra={"spec": json.dumps(blob, sort_keys=True)}),
    )


# --------------------------------------------------------------------- #
# Deterministic assembly (pure string composition; no LLM)


def assemble_html(manifest: Manifest, fragments: dict[str, str],
                  lib_css: dict[str, str], baseline_css: str = "",
                  runtime_css: str = "", runtime_js: str = "") -> str:
    """Compose accepted component fragments into one self-contained page:
    shell + baseline + selected vendored libs + fragments in declared
    order. Pure function — the same inputs assemble the same bytes."""
    missing = [c.name for c in manifest.components if c.name not in fragments]
    if missing:
        raise ValueError(f"missing fragments for component(s): {missing}")
    styles = []
    if baseline_css:
        styles.append(f"<style>\n/* vendored: baseline */\n{baseline_css}\n</style>")
    for name in sorted(lib_css):
        styles.append(f"<style>\n/* vendored: {name} */\n{lib_css[name]}\n</style>")
    if runtime_css:
        styles.append(f"<style>\n/* runtime bundle */\n{runtime_css}\n</style>")
    body = []
    for spec in manifest.ordered():
        body.append(f"<!-- component: {spec.name} -->")
        body.append(fragments[spec.name].strip())
    title = manifest.title or "Assembled site"
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        + "\n".join(styles)
        + "\n</head>\n<body>\n"
        + "\n".join(body)
        + (f"\n<script>\n/* runtime bundle */\n{runtime_js}\n</script>" if runtime_js else "")
        + "\n</body>\n</html>\n"
    )
