"""Compact website contracts -> the canonical :mod:`deepreason.manifest`.

The compact wire objects deliberately contain only local aliases and one
component's integration surface.  This module owns every global decision:
canonical ids, ordering, namespacing, lifecycle boilerplate, dependency
wiring, budgets and validation.  It is a deterministic compiler -- no model,
clock, filesystem or event-log access occurs here.

Compilation is not acceptance.  A successfully compiled ``Manifest`` still
goes through ``manifest_wf`` and the ordinary website workflow before any
component is built.  Conversely, an invalid contract produces stable,
component-local diagnostics; it never changes routing or policy.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from deepreason.manifest import (
    AnimationLifecycle,
    ArtDirection,
    ComponentSpec,
    DependencyRequest,
    Manifest,
    manifest_wf,
)
from deepreason.ontology.commitment import Budget


_ALIAS = re.compile(r"^C[1-9][0-9]*$")
_IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")
_DOM_ID = re.compile(r"^[A-Za-z][\w-]*$")


class CompactOutlineComponent(BaseModel):
    """One deliberately small design-outline item."""

    model_config = ConfigDict(extra="forbid")

    alias: str = Field(pattern=r"^C[1-9][0-9]*$")
    purpose: str = Field(min_length=1, max_length=500)


class CompactDesignOutline(BaseModel):
    """The complete model-visible output for ``DESIGN_OUTLINE``."""

    model_config = ConfigDict(extra="forbid")

    components: list[CompactOutlineComponent] = Field(min_length=1, max_length=12)

    @field_validator("components")
    @classmethod
    def _aliases_are_unique(cls, value):
        aliases = [component.alias for component in value]
        if len(aliases) != len(set(aliases)):
            raise ValueError("duplicate component alias")
        return value


class CompactComponentContract(BaseModel):
    """One component-local wire value; it cannot select workflow policy."""

    model_config = ConfigDict(extra="forbid")

    alias: str = Field(pattern=r"^C[1-9][0-9]*$")
    slots: list[str] = Field(default_factory=lambda: ["root"], min_length=1, max_length=8)
    exports: list[str] = Field(default_factory=list, max_length=16)
    owned_dom_ids: list[str] = Field(min_length=1, max_length=32)
    depends_on: list[str] = Field(default_factory=list, max_length=12)
    content_requirements: list[str] = Field(default_factory=list, max_length=32)
    motion_requirement: Literal["full", "limited", "static"] = "static"

    @field_validator("slots", "exports")
    @classmethod
    def _local_identifiers(cls, value):
        for item in value:
            if not _IDENT.fullmatch(item):
                raise ValueError(f"not a local identifier: {item!r}")
        if len(value) != len(set(value)):
            raise ValueError("duplicate local identifier")
        return value

    @field_validator("owned_dom_ids")
    @classmethod
    def _dom_ids(cls, value):
        for item in value:
            if not _DOM_ID.fullmatch(item):
                raise ValueError(f"not a DOM identifier: {item!r}")
        if len(value) != len(set(value)):
            raise ValueError("duplicate owned DOM identifier")
        return value

    @field_validator("depends_on")
    @classmethod
    def _dependency_aliases(cls, value):
        for item in value:
            if not _ALIAS.fullmatch(item):
                raise ValueError(f"not a component alias: {item!r}")
        if len(value) != len(set(value)):
            raise ValueError("duplicate dependency alias")
        return value


class CompactArtDirection(BaseModel):
    """Flat, bounded transport for the canonical global art direction."""

    model_config = ConfigDict(extra="forbid")

    palette: str = Field(min_length=1, max_length=400)
    typography: str = Field(min_length=1, max_length=400)
    spacing_strategy: str = Field(min_length=1, max_length=400)
    responsive_strategy: str = Field(min_length=1, max_length=600)
    interaction_state_model: str = Field(min_length=1, max_length=600)
    motion_language: str = Field(min_length=1, max_length=600)
    scroll_narrative: str = Field(min_length=1, max_length=600)
    depth_structure: str = Field(min_length=1, max_length=600)
    transition_grammar: str = Field(min_length=1, max_length=600)
    texture_language: str = Field(min_length=1, max_length=600)
    reduced_motion_version: str = Field(min_length=1, max_length=600)
    static_fallback: str = Field(min_length=1, max_length=600)


class ManifestDiagnostic(BaseModel):
    """A stable operational error, never an epistemic verdict."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: Literal[
        "INVALID_OUTLINE",
        "INVALID_COMPONENT_CONTRACT",
        "MISSING_COMPONENT_CONTRACT",
        "DUPLICATE_COMPONENT_ID",
        "UNKNOWN_COMPONENT_ALIAS",
        "UNKNOWN_DEPENDENCY_ALIAS",
        "DEPENDENCY_CYCLE",
        "EXPORT_NOT_DECLARED",
        "SLOT_OWNER_CONFLICT",
        "ANIMATION_LIFECYCLE_INCOMPLETE",
        "REDUCED_MOTION_FALLBACK_MISSING",
        "IMPORT_LIMIT_EXCEEDED",
        "REMOTE_ASSET_FORBIDDEN",
        "UNKNOWN_LIBRARY",
        "MANIFEST_SCHEMA_INVALID",
        "MANIFEST_WF_FAILED",
    ]
    path: str
    message: str
    component_alias: str | None = None
    repair_scope: str
    received: Any | None = None


class ManifestCompileResult(BaseModel):
    """Result of one complete deterministic compile/validate pass."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest: Manifest | None = None
    diagnostics: list[ManifestDiagnostic] = Field(default_factory=list)
    alias_to_component: dict[str, str] = Field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.manifest is not None and not self.diagnostics

    @property
    def repair_aliases(self) -> list[str]:
        return sorted({
            diagnostic.component_alias
            for diagnostic in self.diagnostics
            if diagnostic.component_alias is not None
        })


def _pointer(parts: Sequence[Any]) -> str:
    if not parts:
        return ""
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped)


def _slug_identifier(value: str, fallback: str) -> str:
    value = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    value = re.sub(r"-+", "-", value)
    if not value or not value[0].isalpha():
        value = fallback
    return value[:32].rstrip("-") or fallback


def _js_identifier(component_id: str, local: str) -> str:
    local = re.sub(r"\W", "_", local)
    return f"{component_id.replace('-', '_')}_{local}"


def _component_alias_for_index(
    index: int | None,
    aliases: Sequence[str],
) -> str | None:
    if index is None or index < 0 or index >= len(aliases):
        return None
    return aliases[index]


def _error_code(message: str) -> str:
    lower = message.lower()
    if "duplicate component" in lower or "claimed by both" in lower:
        return "DUPLICATE_COMPONENT_ID"
    if "unknown components" in lower or "unknown component" in lower:
        return "UNKNOWN_DEPENDENCY_ALIAS"
    if "no other component exports" in lower or "unavailable export" in lower:
        return "EXPORT_NOT_DECLARED"
    if "lifecycle" in lower or "initializer" in lower or "cleanup" in lower:
        return "ANIMATION_LIFECYCLE_INCOMPLETE"
    if "static_fallback" in lower or "reduced_motion" in lower:
        return "REDUCED_MOTION_FALLBACK_MISSING"
    if "import" in lower and ("limit" in lower or "budget" in lower):
        return "IMPORT_LIMIT_EXCEEDED"
    if "remote" in lower or "http" in lower or "cdn" in lower:
        return "REMOTE_ASSET_FORBIDDEN"
    return "MANIFEST_SCHEMA_INVALID"


def _validation_diagnostics(
    error: ValidationError,
    aliases: Sequence[str],
) -> list[ManifestDiagnostic]:
    diagnostics: list[ManifestDiagnostic] = []
    for item in error.errors(include_url=False):
        loc = tuple(item.get("loc") or ())
        component_index = None
        if len(loc) >= 2 and loc[0] == "components" and isinstance(loc[1], int):
            component_index = loc[1]
        alias = _component_alias_for_index(component_index, aliases)
        code = _error_code(str(item.get("msg") or "invalid manifest"))
        diagnostics.append(ManifestDiagnostic(
            code=code,
            path=_pointer(loc),
            message=str(item.get("msg") or "invalid manifest"),
            component_alias=alias,
            repair_scope=(f"/component_contracts/{alias}" if alias else "/manifest"),
            received=item.get("input"),
        ))
    return diagnostics


def _cycle_aliases(contracts: Mapping[str, CompactComponentContract]) -> set[str]:
    """Return every node in a dependency cycle, deterministically."""
    graph = {alias: tuple(contract.depends_on) for alias, contract in contracts.items()}
    visiting: set[str] = set()
    visited: set[str] = set()
    cyclic: set[str] = set()

    def visit(node: str, trail: tuple[str, ...]) -> None:
        if node in visiting:
            start = trail.index(node) if node in trail else 0
            cyclic.update(trail[start:])
            cyclic.add(node)
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, ()):
            if dependency in graph:
                visit(dependency, (*trail, dependency))
        visiting.remove(node)
        visited.add(node)

    for alias in sorted(graph):
        visit(alias, (alias,))
    return cyclic


class ManifestCompiler:
    """Compile compact local contracts into one canonical ``Manifest``.

    ``known_libs`` and ``import_policy`` are frozen constructor inputs.  A
    local repair replaces one contract, then :meth:`compile` revalidates the
    complete object; untouched contracts are never regenerated.
    """

    def __init__(self, *, known_libs: Iterable[str] | None = None,
                 import_policy: Any | None = None):
        self.known_libs = None if known_libs is None else frozenset(known_libs)
        self.import_policy = import_policy

    def compile(
        self,
        outline: CompactDesignOutline | Mapping[str, Any],
        component_contracts: Sequence[CompactComponentContract | Mapping[str, Any]],
        *,
        art_direction: CompactArtDirection | Mapping[str, Any] | None = None,
        title: str = "",
        libs: Sequence[str] = (),
        dependencies: Sequence[DependencyRequest | Mapping[str, Any]] = (),
    ) -> ManifestCompileResult:
        diagnostics: list[ManifestDiagnostic] = []
        try:
            outline_value = (
                outline if isinstance(outline, CompactDesignOutline)
                else CompactDesignOutline.model_validate(outline)
            )
        except ValidationError as error:
            for item in error.errors(include_url=False):
                message = str(item.get("msg") or "invalid outline")
                diagnostics.append(ManifestDiagnostic(
                    code=(
                        "DUPLICATE_COMPONENT_ID"
                        if "duplicate component alias" in message.lower()
                        else "INVALID_OUTLINE"
                    ),
                    path=_pointer(item.get("loc") or ()),
                    message=message,
                    repair_scope="/design_outline",
                    received=item.get("input"),
                ))
            return ManifestCompileResult(diagnostics=diagnostics)

        aliases = [component.alias for component in outline_value.components]
        outline_aliases = set(aliases)
        parsed: dict[str, CompactComponentContract] = {}
        for index, raw in enumerate(component_contracts):
            raw_alias = raw.alias if isinstance(raw, CompactComponentContract) else raw.get("alias")
            try:
                contract = (
                    raw if isinstance(raw, CompactComponentContract)
                    else CompactComponentContract.model_validate(raw)
                )
            except (ValidationError, AttributeError) as error:
                errors = error.errors(include_url=False) if isinstance(error, ValidationError) else [{
                    "loc": (), "msg": str(error), "input": raw,
                }]
                for item in errors:
                    alias = raw_alias if isinstance(raw_alias, str) and _ALIAS.fullmatch(raw_alias) else None
                    diagnostics.append(ManifestDiagnostic(
                        code="INVALID_COMPONENT_CONTRACT",
                        path=f"/component_contracts/{index}{_pointer(item.get('loc') or ())}",
                        message=str(item.get("msg") or "invalid component contract"),
                        component_alias=alias,
                        repair_scope=(f"/component_contracts/{alias}" if alias else f"/component_contracts/{index}"),
                        received=item.get("input"),
                    ))
                continue
            if contract.alias in parsed:
                diagnostics.append(ManifestDiagnostic(
                    code="DUPLICATE_COMPONENT_ID",
                    path=f"/component_contracts/{index}/alias",
                    message=f"duplicate component contract for {contract.alias}",
                    component_alias=contract.alias,
                    repair_scope=f"/component_contracts/{contract.alias}",
                    received=contract.alias,
                ))
                continue
            if contract.alias not in outline_aliases:
                diagnostics.append(ManifestDiagnostic(
                    code="UNKNOWN_COMPONENT_ALIAS",
                    path=f"/component_contracts/{index}/alias",
                    message=f"component alias {contract.alias!r} is absent from the outline",
                    component_alias=contract.alias,
                    repair_scope=f"/component_contracts/{contract.alias}",
                    received=contract.alias,
                ))
                continue
            parsed[contract.alias] = contract

        for alias in aliases:
            if alias not in parsed:
                diagnostics.append(ManifestDiagnostic(
                    code="MISSING_COMPONENT_CONTRACT",
                    path=f"/component_contracts/{alias}",
                    message=f"no component contract supplied for {alias}",
                    component_alias=alias,
                    repair_scope=f"/component_contracts/{alias}",
                ))

        for alias in aliases:
            contract = parsed.get(alias)
            if contract is None:
                continue
            if "root" not in contract.slots:
                diagnostics.append(ManifestDiagnostic(
                    code="SLOT_OWNER_CONFLICT",
                    path=f"/component_contracts/{alias}/slots",
                    message="every component must own its root slot",
                    component_alias=alias,
                    repair_scope=f"/component_contracts/{alias}",
                    received=contract.slots,
                ))
            for dependency in contract.depends_on:
                if dependency not in outline_aliases:
                    diagnostics.append(ManifestDiagnostic(
                        code="UNKNOWN_DEPENDENCY_ALIAS",
                        path=f"/component_contracts/{alias}/depends_on",
                        message=f"unknown dependency alias {dependency!r}",
                        component_alias=alias,
                        repair_scope=f"/component_contracts/{alias}",
                        received=dependency,
                    ))
                elif dependency == alias:
                    diagnostics.append(ManifestDiagnostic(
                        code="DEPENDENCY_CYCLE",
                        path=f"/component_contracts/{alias}/depends_on",
                        message="a component cannot depend on itself",
                        component_alias=alias,
                        repair_scope=f"/component_contracts/{alias}",
                        received=dependency,
                    ))

        # Localize ownership collisions before canonical Manifest validation,
        # whose model-level duplicate error cannot identify the second alias.
        dom_owners: dict[str, str] = {}
        for alias in aliases:
            contract = parsed.get(alias)
            if contract is None:
                continue
            for raw_id in contract.owned_dom_ids:
                normalized = _slug_identifier(
                    raw_id.replace("_", "-"), f"{alias.lower()}-root"
                )
                owner = dom_owners.get(normalized)
                if owner is not None and owner != alias:
                    diagnostics.append(ManifestDiagnostic(
                        code="SLOT_OWNER_CONFLICT",
                        path=f"/component_contracts/{alias}/owned_dom_ids",
                        message=(
                            f"DOM id {normalized!r} is already owned by component {owner}"
                        ),
                        component_alias=alias,
                        repair_scope=f"/component_contracts/{alias}",
                        received=raw_id,
                    ))
                else:
                    dom_owners[normalized] = alias

        for alias in sorted(_cycle_aliases(parsed)):
            diagnostics.append(ManifestDiagnostic(
                code="DEPENDENCY_CYCLE",
                path=f"/component_contracts/{alias}/depends_on",
                message="component dependency graph contains a cycle",
                component_alias=alias,
                repair_scope=f"/component_contracts/{alias}",
            ))

        animated_aliases = [
            alias for alias in aliases
            if alias in parsed and parsed[alias].motion_requirement != "static"
        ]
        art_value: CompactArtDirection | None = None
        if art_direction is not None:
            try:
                art_value = (
                    art_direction if isinstance(art_direction, CompactArtDirection)
                    else CompactArtDirection.model_validate(art_direction)
                )
            except ValidationError as error:
                for item in error.errors(include_url=False):
                    diagnostics.append(ManifestDiagnostic(
                        code="REDUCED_MOTION_FALLBACK_MISSING",
                        path="/art_direction" + _pointer(item.get("loc") or ()),
                        message=str(item.get("msg") or "invalid art direction"),
                        repair_scope="/art_direction",
                        received=item.get("input"),
                    ))
        if animated_aliases and art_value is None:
            for alias in animated_aliases:
                diagnostics.append(ManifestDiagnostic(
                    code="REDUCED_MOTION_FALLBACK_MISSING",
                    path="/art_direction",
                    message="animated components require reduced-motion and static fallbacks",
                    component_alias=alias,
                    repair_scope="/art_direction",
                ))

        unknown_libs = sorted(set(libs) - self.known_libs) if self.known_libs is not None else []
        for lib in unknown_libs:
            code = "REMOTE_ASSET_FORBIDDEN" if "://" in lib else "UNKNOWN_LIBRARY"
            diagnostics.append(ManifestDiagnostic(
                code=code,
                path="/libs",
                message=f"library {lib!r} is not in the frozen vendored catalog",
                repair_scope="/libs",
                received=lib,
            ))

        max_imports = getattr(self.import_policy, "max_direct_dependencies", None)
        if max_imports is not None and len(dependencies) > max_imports:
            diagnostics.append(ManifestDiagnostic(
                code="IMPORT_LIMIT_EXCEEDED",
                path="/dependencies",
                message=f"{len(dependencies)} dependencies exceed the limit {max_imports}",
                repair_scope="/dependencies",
                received=len(dependencies),
            ))

        if diagnostics:
            mapping = {alias: alias.lower() for alias in aliases}
            return ManifestCompileResult(
                diagnostics=sorted(diagnostics, key=lambda item: (item.path, item.code, item.message)),
                alias_to_component=mapping,
            )

        mapping = {alias: alias.lower() for alias in aliases}
        components: list[ComponentSpec] = []
        outline_by_alias = {component.alias: component for component in outline_value.components}
        for order, alias in enumerate(aliases):
            contract = parsed[alias]
            component_id = mapping[alias]
            root_id = contract.owned_dom_ids[0]
            root_id = _slug_identifier(root_id.replace("_", "-"), f"{component_id}-root")

            local_exports = list(contract.exports)
            if contract.motion_requirement != "static":
                for required in ("mount", "destroy"):
                    if required not in local_exports:
                        local_exports.append(required)
            exports = [_js_identifier(component_id, local) for local in local_exports]
            exported_by_local = dict(zip(local_exports, exports, strict=True))
            initializer = exported_by_local.get("mount") if contract.motion_requirement != "static" else None
            cleanup = exported_by_local.get("destroy") if contract.motion_requirement != "static" else None

            uses: list[str] = []
            for dependency_alias in contract.depends_on:
                dependency = parsed[dependency_alias]
                dependency_locals = list(dependency.exports)
                if dependency.motion_requirement != "static":
                    for required in ("mount", "destroy"):
                        if required not in dependency_locals:
                            dependency_locals.append(required)
                preferred = "mount" if "mount" in dependency_locals else (
                    dependency_locals[0] if dependency_locals else None
                )
                if preferred is None:
                    diagnostics.append(ManifestDiagnostic(
                        code="EXPORT_NOT_DECLARED",
                        path=f"/component_contracts/{alias}/depends_on",
                        message=f"dependency {dependency_alias} declares no callable export",
                        component_alias=alias,
                        repair_scope=f"/component_contracts/{dependency_alias}",
                        received=dependency_alias,
                    ))
                else:
                    uses.append(_js_identifier(mapping[dependency_alias], preferred))

            components.append(ComponentSpec(
                name=component_id,
                purpose=outline_by_alias[alias].purpose + (
                    " Requirements: " + "; ".join(contract.content_requirements)
                    if contract.content_requirements else ""
                ),
                element_id=root_id,
                css_prefix=f"{component_id}-",
                js_exports=exports,
                js_uses=uses,
                lifecycle=AnimationLifecycle(
                    animated=contract.motion_requirement != "static",
                    initializer=initializer,
                    cleanup=cleanup,
                    frame_loop_owner=(
                        "component" if contract.motion_requirement == "full" else
                        "shared" if contract.motion_requirement == "limited" else "none"
                    ),
                    static_fallback=(art_value.static_fallback if art_value and contract.motion_requirement != "static" else None),
                ),
                order=order,
            ))

        if diagnostics:
            return ManifestCompileResult(
                diagnostics=sorted(diagnostics, key=lambda item: (item.path, item.code, item.message)),
                alias_to_component=mapping,
            )

        dependency_values: list[DependencyRequest] = []
        try:
            dependency_values = [
                item if isinstance(item, DependencyRequest) else DependencyRequest.model_validate(item)
                for item in dependencies
            ]
            manifest = Manifest(
                title=title,
                libs=list(libs),
                art_direction=(
                    ArtDirection.model_validate(
                        art_value.model_dump(
                            include=set(ArtDirection.model_fields)
                        )
                    )
                    if art_value
                    else None
                ),
                dependencies=dependency_values,
                components=components,
            )
        except ValidationError as error:
            return ManifestCompileResult(
                diagnostics=_validation_diagnostics(error, aliases),
                alias_to_component=mapping,
            )

        # Exercise the same program used by the ordinary manifest commitment.
        # This is still only operational validation; the workflow registers
        # the compiled result and subjects it to normal criticism afterwards.
        fenced = "```manifest\n" + json.dumps(manifest.model_dump(), sort_keys=True) + "\n```"
        budget = Budget(extra={
            "libs": ",".join(sorted(self.known_libs or set())),
        })
        verdict, trace = manifest_wf(fenced, budget)
        if verdict != "pass":
            message = str(trace.get("reason") or "manifest_wf failed")
            return ManifestCompileResult(
                diagnostics=[ManifestDiagnostic(
                    code=_error_code(message) if _error_code(message) != "MANIFEST_SCHEMA_INVALID" else "MANIFEST_WF_FAILED",
                    path="/manifest",
                    message=message,
                    repair_scope="/manifest",
                )],
                alias_to_component=mapping,
            )
        return ManifestCompileResult(manifest=manifest, alias_to_component=mapping)

    def repair_component(
        self,
        outline: CompactDesignOutline | Mapping[str, Any],
        component_contracts: Sequence[CompactComponentContract | Mapping[str, Any]],
        replacement: CompactComponentContract | Mapping[str, Any],
        **compile_kwargs: Any,
    ) -> ManifestCompileResult:
        """Replace exactly one alias and recompile/revalidate the whole manifest."""
        replacement_value = (
            replacement if isinstance(replacement, CompactComponentContract)
            else CompactComponentContract.model_validate(replacement)
        )
        values: list[CompactComponentContract | Mapping[str, Any]] = []
        replaced = False
        for contract in component_contracts:
            alias = contract.alias if isinstance(contract, CompactComponentContract) else contract.get("alias")
            if alias == replacement_value.alias:
                if not replaced:
                    values.append(replacement_value)
                    replaced = True
                continue
            values.append(contract)
        if not replaced:
            values.append(replacement_value)
        return self.compile(outline, values, **compile_kwargs)

    # Explicit name used by workflow callers and diagnostics.
    repair_component_contract = repair_component

    def validate_manifest(
        self,
        manifest: Manifest | Mapping[str, Any],
        *,
        aliases: Sequence[str] = (),
    ) -> ManifestCompileResult:
        """Validate a direct canonical manifest with the same stable errors.

        This is the frontier/direct companion to :meth:`compile`: both paths
        converge on the same Pydantic model and ``manifest_wf`` program.
        """
        try:
            value = (
                manifest if isinstance(manifest, Manifest)
                else Manifest.model_validate(manifest)
            )
        except ValidationError as error:
            return ManifestCompileResult(
                diagnostics=_validation_diagnostics(error, aliases),
                alias_to_component={
                    alias: alias.lower() for alias in aliases
                },
            )
        unknown = sorted(
            set(value.libs).union(
                lib for component in value.components for lib in component.libs
            ) - self.known_libs
        ) if self.known_libs is not None else []
        if unknown:
            diagnostics = [ManifestDiagnostic(
                code=("REMOTE_ASSET_FORBIDDEN" if "://" in lib else "UNKNOWN_LIBRARY"),
                path="/libs",
                message=f"library {lib!r} is not in the frozen vendored catalog",
                repair_scope="/libs",
                received=lib,
            ) for lib in unknown]
            return ManifestCompileResult(diagnostics=diagnostics)
        fenced = "```manifest\n" + json.dumps(value.model_dump(), sort_keys=True) + "\n```"
        verdict, trace = manifest_wf(
            fenced,
            Budget(extra={"libs": ",".join(sorted(self.known_libs or set()))}),
        )
        if verdict != "pass":
            reason = str(trace.get("reason") or "manifest_wf failed")
            return ManifestCompileResult(diagnostics=[ManifestDiagnostic(
                code="MANIFEST_WF_FAILED",
                path="/manifest",
                message=reason,
                repair_scope="/manifest",
            )])
        return ManifestCompileResult(
            manifest=value,
            alias_to_component={alias: alias.lower() for alias in aliases},
        )


def compile_compact_manifest(
    outline: CompactDesignOutline | Mapping[str, Any],
    component_contracts: Sequence[CompactComponentContract | Mapping[str, Any]],
    **kwargs: Any,
) -> ManifestCompileResult:
    """Convenience pure function for callers without a persistent compiler."""
    known_libs = kwargs.pop("known_libs", None)
    import_policy = kwargs.pop("import_policy", None)
    return ManifestCompiler(
        known_libs=known_libs,
        import_policy=import_policy,
    ).compile(outline, component_contracts, **kwargs)
