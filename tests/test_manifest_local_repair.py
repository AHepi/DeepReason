"""Compact manifest errors repair one local contract and revalidate globally."""

from deepreason.canonical import canonical_json
from deepreason.workflows.manifest_compiler import ManifestCompiler


OUTLINE = {
    "components": [
        {"alias": "C1", "purpose": "hero and primary DNA visualization"},
        {"alias": "C2", "purpose": "replication explanation"},
        {"alias": "C3", "purpose": "closing navigation"},
    ]
}

ART_DIRECTION = {
    "palette": "deep navy with cyan and magenta molecular highlights",
    "typography": "geometric display type with readable humanist body text",
    "spacing_strategy": "fluid section spacing on a consistent grid",
    "responsive_strategy": "single column on small screens with scalable diagrams",
    "interaction_state_model": "section-local controls with one global motion preference",
    "motion_language": "slow orbital motion with brief state transitions",
    "scroll_narrative": "sections reveal in document order",
    "depth_structure": "foreground helix over quiet cellular layers",
    "transition_grammar": "opacity and transform only",
    "texture_language": "fine grain and luminous strands",
    "reduced_motion_version": "all sections visible without scroll animation",
    "static_fallback": "a complete readable still composition",
}


def contract(alias, root, *, depends_on=(), exports=(), motion="static"):
    return {
        "alias": alias,
        "slots": ["root"],
        "exports": list(exports),
        "owned_dom_ids": [root],
        "depends_on": list(depends_on),
        "content_requirements": [f"content for {alias}"],
        "motion_requirement": motion,
    }


def test_unknown_dependency_is_localized_then_one_contract_is_repaired():
    compiler = ManifestCompiler(known_libs={"classless", "layout"})
    bad = [
        contract("C1", "dna-hero", exports=("mount", "destroy"), motion="full"),
        contract("C2", "dna-copy", depends_on=("C9",)),
        contract("C3", "dna-close"),
    ]
    failed = compiler.compile(
        OUTLINE, bad, art_direction=ART_DIRECTION, libs=["classless"]
    )
    assert failed.manifest is None
    diagnostic = next(
        item for item in failed.diagnostics
        if item.code == "UNKNOWN_DEPENDENCY_ALIAS"
    )
    assert diagnostic.component_alias == "C2"
    assert diagnostic.path == "/component_contracts/C2/depends_on"
    assert diagnostic.repair_scope == "/component_contracts/C2"
    assert failed.repair_aliases == ["C2"]

    repaired = compiler.repair_component_contract(
        OUTLINE,
        bad,
        contract("C2", "dna-copy", depends_on=("C1",)),
        art_direction=ART_DIRECTION,
        libs=["classless"],
    )
    assert repaired.ok
    assert [item.name for item in repaired.manifest.ordered()] == ["c1", "c2", "c3"]
    assert repaired.manifest.components[1].js_uses == ["c1_mount"]


def test_compile_is_byte_deterministic_and_supplies_lifecycle_boilerplate():
    compiler = ManifestCompiler(known_libs={"classless"})
    contracts = [
        contract("C1", "dna_hero", exports=(), motion="limited"),
        contract("C2", "dna-copy", depends_on=("C1",)),
        contract("C3", "dna-close"),
    ]
    first = compiler.compile(OUTLINE, contracts, art_direction=ART_DIRECTION)
    second = compiler.compile(OUTLINE, contracts, art_direction=ART_DIRECTION)
    assert first.ok and second.ok
    assert canonical_json(first.manifest.model_dump()) == canonical_json(
        second.manifest.model_dump()
    )
    animated = first.manifest.ordered()[0]
    assert animated.lifecycle.initializer == "c1_mount"
    assert animated.lifecycle.cleanup == "c1_destroy"
    assert {"c1_mount", "c1_destroy"} <= set(animated.js_exports)
    assert animated.lifecycle.static_fallback == ART_DIRECTION["static_fallback"]


def test_owned_dom_collision_names_only_the_affected_contract():
    compiler = ManifestCompiler()
    result = compiler.compile(OUTLINE, [
        contract("C1", "shared-root"),
        contract("C2", "shared_root"),
        contract("C3", "unique-root"),
    ])
    collision = next(
        item for item in result.diagnostics
        if item.code == "SLOT_OWNER_CONFLICT"
    )
    assert collision.component_alias == "C2"
    assert collision.repair_scope == "/component_contracts/C2"


def test_complete_manifest_is_revalidated_after_local_repair():
    compiler = ManifestCompiler()
    contracts = [
        contract("C1", "one", exports=("mount",)),
        contract("C2", "two", depends_on=("C1",)),
        contract("C3", "three"),
    ]
    initial = compiler.compile(OUTLINE, contracts)
    assert initial.ok
    # Repairing C1 to remove its only export makes C2's unchanged dependency
    # invalid.  The compiler must catch that global consequence.
    repaired = compiler.repair_component_contract(
        OUTLINE, contracts, contract("C1", "one")
    )
    assert not repaired.ok
    error = next(item for item in repaired.diagnostics if item.code == "EXPORT_NOT_DECLARED")
    assert error.component_alias == "C2"
    assert error.repair_scope == "/component_contracts/C1"
