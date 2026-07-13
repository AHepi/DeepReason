from deepreason.packs import PackIR, PackSection, allocate_pack


def _section(identifier, text, priority, *, droppable, compressible, minimum=1):
    return PackSection(
        id=identifier,
        text_ref="inline:" + text,
        priority=priority,
        min_tokens=minimum,
        max_tokens=max(minimum, 10_000),
        droppable=droppable,
        compressible=compressible,
        cache_group=identifier,
        provenance_refs=(),
    )


def test_mandatory_criteria_and_output_contract_are_never_clipped():
    criteria = "CRITERION " * 200
    contract = "OUTPUT_SCHEMA " * 200
    optional = "memory " * 5000
    ir = PackIR(
        profile="reasoning.text.v1",
        template_role="conjecturer",
        target_tokens=50,
        sections=(
            _section("criteria", criteria, 2, droppable=False, compressible=False),
            _section("output-contract", contract, 5, droppable=False, compressible=False),
            _section("memory", optional, 11, droppable=True, compressible=True),
        ),
    )
    result = allocate_pack(ir)
    assert criteria in result.text
    assert contract in result.text
    assert next(s for s in result.sections if s.id == "memory").dropped
    assert result.mandatory_overflow > 0


def test_large_explicit_target_is_not_compact_clamped():
    body = "x" * 20_000
    ir = PackIR(
        profile="compact",
        template_role="critic",
        target_tokens=5000,
        sections=(
            _section("problem", body, 1, droppable=False, compressible=True, minimum=10),
        ),
    )
    result = allocate_pack(ir)
    assert result.allocated_tokens == 5000
    assert len(result.text) > 1200 * 4
