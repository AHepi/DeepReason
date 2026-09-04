"""The reference menu: one authority for every legal handle set.

Implements F2 of the REBUILD program
(`experiments/2026-08-26-change-f2-reference-menu/`). The motivating
measurement is W1's form census over 54 committed roots
(`experiments/2026-08-26-run-anatomy-program/W1-form-census/RESULTS.md`):
62.6% of every field-attributed diagnostic in the record is a reference
handle the model made up, and where the record explicitly told a seat that
omission was legal, the seat invented a value anyway 255 times out of 257.
"""

import re

import pytest

from deepreason.llm import reference_menu as rm

# The five fields W1 section 2 names as the commonest field-attributed
# failures in the whole corpus, with the diagnostic count each produced.
# Named here rather than in a comment so a registry that stops covering one
# fails loudly (docs/map/INV-reference-menu.md).
CENSUS_ATTESTED = {
    "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block": 244,
    "conjecturer.turn.v6:/scratch_proposal/unresolved_questions/*/related_refs": 230,
    "batch-critic.v2:/cases/*/premise_evidence/*/block": 129,
    "conjecturer.turn.v6:/scratch_proposal/links/*/to_ref": 70,
    "conjecturer.turn.v6:/candidates/*/optional_refs/*": 64,
}


def _binding(**overrides):
    """A binding carrying one plausible handle of every registered kind."""

    values = {
        "citable_block_ids": ("a3f19c2b8e04", "7d0c1149ab52", "ff0011223344"),
        "scratch_handles": ("SCR_001", "SCR_002"),
        "new_block_keys": ("NEW_001",),
        "aliases": ("A1", "A2", "A3"),
    }
    values.update(overrides)
    return rm.MenuBinding(**values)


# --- the registry is a contract ------------------------------------------- #


def test_the_registry_declares_every_census_attested_field():
    """Every field W1 measured as a top-five failure has a declaration."""

    missing = sorted(
        field_id
        for field_id in CENSUS_ATTESTED
        if field_id not in rm.REFERENCE_FIELD_DECLARATIONS
    )
    assert not missing, f"census-attested fields with no declaration: {missing}"


def test_the_registry_is_keyed_by_its_own_declarations():
    """Two copies of one fact is how a registry stops being a contract."""

    for key, declaration in rm.REFERENCE_FIELD_DECLARATIONS.items():
        assert declaration.field_id == key
        assert declaration.field_id == f"{declaration.contract}:{declaration.pointer}"


def test_a_declaration_refuses_to_be_incomplete():
    """Mirrors SignalDeclaration.__post_init__: an incomplete declaration is
    a registry entry that lies about what it covers."""

    with pytest.raises(ValueError):
        rm.ReferenceFieldDeclaration(
            contract="",
            pointer="/candidates/0",
            handle_kind="artifact_alias",
            omission_legal=False,
            omission_first_ask="",
            omission_repair="",
        )
    with pytest.raises(ValueError):
        rm.ReferenceFieldDeclaration(
            contract="c",
            pointer="/candidates/0",
            handle_kind="no_such_kind_is_registered",
            omission_legal=False,
            omission_first_ask="",
            omission_repair="",
        )


def test_a_declaration_that_permits_omission_must_spell_both_forms():
    """R6 wants the escape road spelled concretely. A first ask has no patch
    to remove from, so the two spellings are different sentences and the
    declaration owns both -- otherwise two authors spell one escape."""

    for declaration in rm.REFERENCE_FIELD_DECLARATIONS.values():
        if not declaration.omission_legal:
            continue
        assert declaration.omission_first_ask.strip()
        assert declaration.omission_repair.strip()
        assert declaration.omission_first_ask != declaration.omission_repair


# --- the omission entry is a selectable item, not prose ------------------- #


def test_omission_is_entry_zero_where_legal():
    """W1 section 3: told in prose that omission was legal, seats invented a
    handle 255 of 257 times (CFR 99.2%), while an escape that lives IN the
    vocabulary gets taken. So the escape is index 0 of the menu."""

    legal = [
        d for d in rm.REFERENCE_FIELD_DECLARATIONS.values() if d.omission_legal
    ]
    assert legal, "no omission-legal field declared; the CFR finding has no target"
    for declaration in legal:
        render = rm.render_reference_menu(declaration.field_id, _binding())
        assert render is not None
        entries = rm.menu_entries(declaration.field_id, _binding())
        assert entries[0].index == 0
        assert entries[0].is_omission
        assert entries[0].text == declaration.omission_first_ask
        assert declaration.omission_first_ask in render.text


def test_a_field_without_legal_omission_offers_no_omission_entry():
    """The menu may not invent an escape the validators do not accept: that
    would be a menu deciding validity (INV-reference-menu, FROZEN (b))."""

    closed = [
        d for d in rm.REFERENCE_FIELD_DECLARATIONS.values() if not d.omission_legal
    ]
    assert closed, "no omission-illegal field declared; the guard is untested"
    for declaration in closed:
        entries = rm.menu_entries(declaration.field_id, _binding())
        assert entries
        assert not any(entry.is_omission for entry in entries)
        assert entries[0].index == 1


# --- the index grammar ---------------------------------------------------- #


def test_index_grammar_is_offered_on_every_menu():
    """R2: a long list is 'an indexed table the field selects from by
    index'. A seat cannot select by index unless the menu says it may."""

    for declaration in rm.REFERENCE_FIELD_DECLARATIONS.values():
        render = rm.render_reference_menu(declaration.field_id, _binding())
        if render is None:
            continue
        for entry in rm.menu_entries(declaration.field_id, _binding()):
            assert f"[{entry.index}]" in render.text


def test_long_list_is_the_same_grammar_as_a_short_one():
    """The short/long fork changes layout density only. A seat that learned
    to answer [2] on a short menu must answer [2] on a long one, so the
    index grammar may not differ between the two renderings."""

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    policy = rm.MenuRenderPolicy(inline_threshold=3, maximum_entries=64)
    short = rm.render_reference_menu(
        field_id, _binding(citable_block_ids=("a" * 12, "b" * 12)), policy=policy
    )
    long = rm.render_reference_menu(
        field_id,
        _binding(citable_block_ids=tuple(f"{i:012x}" for i in range(20))),
        policy=policy,
    )
    assert short is not None and long is not None
    assert short.inline is True
    assert long.inline is False
    # Same selection grammar in both: entry [1] is addressable either way.
    assert "[1]" in short.text and "[1]" in long.text
    grammar = rm.INDEX_REPLY_GUIDANCE
    assert grammar in short.text and grammar in long.text


def test_menu_order_is_index_order_not_key_order():
    """CLAUDE.md's ledgered invariant: handle maps reload key-sorted
    (B1, B10, B2, ...), so comparison goes by handle INDEX, never by key
    order. A key-sorted menu renders 1, 10, 11, 2 and fails here."""

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    blocks = tuple(f"{i:012x}" for i in range(1, 12))  # eleven, so 10 and 11 exist
    entries = [
        e
        for e in rm.menu_entries(field_id, _binding(citable_block_ids=blocks))
        if not e.is_omission
    ]
    assert [e.index for e in entries] == list(range(1, 12))
    assert [e.text for e in entries] == list(blocks)


def test_index_grammar_never_shadows_a_legal_handle():
    """An index reply may only be resolved because no field's own grammar
    admits one. A future field whose handles are bare integers turns this
    red -- correctly: such a field must not use index replies."""

    for declaration in rm.REFERENCE_FIELD_DECLARATIONS.values():
        grammar = re.compile(rm.handle_source(declaration.handle_kind).grammar)
        for candidate in ("0", "1", "2", "11", "[2]", "#2", " 2 "):
            assert grammar.fullmatch(candidate.strip()) is None, (
                f"{declaration.field_id}: index token {candidate!r} is a legal "
                f"handle under this field's own grammar"
            )


# --- customisation is a check, not a claim -------------------------------- #


def test_a_new_field_gets_a_menu_by_registering():
    """Operator design law, 2026-08-26: 'Customisation needs to be easy.'
    A renderer that hard-codes field names or handle kinds fails here."""

    class _SyntheticSource:
        grammar = r"^ZZQ_[0-9]{2}$"

        def handles(self, binding):
            return ("ZZQ_01", "ZZQ_02")

    kind = "synthetic_kind_for_this_test"
    field_id = "synthetic.contract.v9:/nowhere/*/handle_that_is_not_in_src"
    rm.register_handle_source(kind, _SyntheticSource())
    declaration = rm.ReferenceFieldDeclaration(
        contract="synthetic.contract.v9",
        pointer="/nowhere/*/handle_that_is_not_in_src",
        handle_kind=kind,
        omission_legal=True,
        omission_first_ask='leave "handle_that_is_not_in_src" out entirely.',
        omission_repair="write a remove operation at /nowhere/0.",
    )
    rm.register_reference_field(declaration)
    try:
        render = rm.render_reference_menu(field_id, _binding())
        assert render is not None
        assert "ZZQ_01" in render.text and "ZZQ_02" in render.text
        assert declaration.omission_first_ask in render.text
        assert "[0]" in render.text and "[2]" in render.text
    finally:
        rm.unregister_reference_field(field_id)
        rm.unregister_handle_source(kind)
    assert field_id not in rm.REFERENCE_FIELD_DECLARATIONS


def test_a_registered_field_name_appears_nowhere_in_the_renderer():
    """The other half of register-don't-edit: the renderer must not know any
    field by name. A grep, because it is the cheapest thing that would fail
    if someone special-cased a field inside the render path."""

    import pathlib

    source = pathlib.Path(rm.__file__).read_text()
    body = source.split("REFERENCE_FIELD_DECLARATIONS", 1)[-1]
    render_body = body.split("def render_reference_menu", 1)[-1]
    for pointer in ("evidence_refs", "related_refs", "premise_evidence"):
        assert pointer not in render_body, (
            f"render_reference_menu special-cases {pointer!r}; a new field "
            f"must get a menu by registering, not by editing the renderer"
        )


# --- the token economy: bounded, and never silently capped ---------------- #


def test_truncation_is_disclosed_inside_the_menu_text():
    """No silent caps. The disclosure lives INSIDE the rendered text so no
    consumer can carry the menu without the fact that it is partial --
    DR-CON-packs-and-token-economy's rule applied to a new section family.
    """

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    policy = rm.MenuRenderPolicy(inline_threshold=4, maximum_entries=5)
    blocks = tuple(f"{i:012x}" for i in range(1, 41))
    render = rm.render_reference_menu(
        field_id, _binding(citable_block_ids=blocks), policy=policy
    )
    assert render is not None
    assert render.truncated is True
    assert render.shown == 5
    assert render.total == 40
    assert "+35 further legal handles not shown" in render.text
    assert "truncated" in render.text
    # The handle at index 6 was cut, so the menu must not appear to offer it.
    assert f"[6]" not in render.text


def test_an_untruncated_menu_says_nothing_about_truncation():
    """An always-present 'truncated: none' line is the empty slot that
    RESEARCH_JUDGE_BLINDING_2026-08-22 measured as worse than a populated
    one; `_allocate_sections` already omits its notice for the same reason.
    """

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    render = rm.render_reference_menu(field_id, _binding())
    assert render is not None
    assert render.truncated is False
    assert "not shown" not in render.text
    assert "truncated" not in render.text


def test_menu_tokens_are_counted_in_the_token_economys_own_unit():
    """R11: the menu's token cost is logged by the token economy. Counting
    it with a private estimator would give the pack budget two different
    answers about what one section costs."""

    from deepreason.packs.allocate import approximate_tokens

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    render = rm.render_reference_menu(field_id, _binding())
    assert render is not None
    assert render.tokens == approximate_tokens(render.text)
    assert render.tokens > 0


def test_the_menu_is_bounded_by_its_policy_not_by_its_input():
    """The bound is a FREE parameter with an envelope, not a constant a
    caller can grow past by handing over a longer list."""

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    blocks = tuple(f"{i:012x}" for i in range(1, 500))
    for maximum in (1, 7, 32):
        policy = rm.MenuRenderPolicy(inline_threshold=1, maximum_entries=maximum)
        legal = rm.legal_handles_for(
            field_id, _binding(citable_block_ids=blocks), policy=policy
        )
        assert legal.shown == maximum
        assert legal.total == 499
        assert legal.truncated is True


def test_a_policy_that_contradicts_itself_is_refused():
    """An inline threshold above the maximum would render a menu inline and
    then cut it, which is a silent cap wearing a layout's clothes."""

    with pytest.raises(ValueError):
        rm.MenuRenderPolicy(inline_threshold=40, maximum_entries=8)
    with pytest.raises(ValueError):
        rm.MenuRenderPolicy(inline_threshold=0, maximum_entries=8)


# --- reuse, not modification ---------------------------------------------- #


def test_the_reused_modules_are_not_modified_by_the_menu_machinery():
    """SPEC section 1's disposition, made failable.

    `tools/blast_radius.py` reports CONTACT with the replay-validation
    surface for any change declaring `ordered_refs`, because
    `invariants.py` references that symbol. This tranche only CALLS it.
    The durable form of that claim is not a byte pin on those files -- a
    later tranche may legitimately edit `invariants.py` -- but that the
    menu machinery reaches them read-only, through their own accessors,
    and imports none of them. The tranche-scoped byte proof lives at
    `experiments/2026-08-26-change-f2-reference-menu/proof/`.
    """

    import ast
    import pathlib

    source = pathlib.Path(rm.__file__).read_text()
    tree = ast.parse(source)

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    forbidden = {
        module
        for module in imported
        if module.startswith(
            (
                "deepreason.invariants",
                "deepreason.verification",
                "deepreason.scratch",
                "deepreason.evidence",
                "deepreason.harness",
                "deepreason.run_manifest",
                "deepreason.capabilities",
            )
        )
    }
    assert not forbidden, (
        f"reference_menu.py imports {sorted(forbidden)}; the menu consumes a "
        f"render receipt duck-typed and must not reach a frozen surface"
    )

    # The render receipt is touched only through its read-only accessors.
    receipt_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "receipt"
    }
    assert receipt_calls <= {"ordered_refs", "alias_map"}, (
        f"reference_menu.py calls {sorted(receipt_calls - {'ordered_refs', 'alias_map'})} "
        f"on a render receipt; only the read accessors are reuse"
    )
    assert "ordered_refs" in receipt_calls, (
        "the scratch menu no longer goes through ordered_refs; CLAUDE.md's "
        "ledgered invariant says a handle map is compared by handle INDEX, "
        "never through .values()"
    )


# --- the menu reaches the FIRST ask --------------------------------------- #


def _conj_problem(harness):
    from deepreason.ontology import Commitment, Problem, ProblemProvenance

    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    problem = Problem(
        id="pi-tides",
        description="explain the tides",
        criteria=["k-moon"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )
    harness.register_problem(problem)
    return problem


def test_conj_pack_carries_the_menu_on_the_first_ask(harness):
    """R4: the legal set arrives BEFORE the first attempt, not after it.

    W1 section 5 is the cost of the current ordering: the first ask is
    91.7% valid across 2 699 attempts, and every repair attempt afterwards
    is ~58% and does not improve with repetition -- so a legal-handle list
    that only appears in a repair diagnostic is a list delivered into the
    worst-converting turn the harness has.
    """

    from deepreason.llm.packs import render_conj_pack

    problem = _conj_problem(harness)
    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    binding = _binding()
    menus = (rm.render_reference_menu(field_id, binding),)
    pack = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=2,
        token_budget=4000,
        citable_evidence_context="CITABLE EVIDENCE BLOCKS\n[a3f19c2b8e04] a claim",
        reference_menus=menus,
    )
    assert "/candidates/*/evidence_refs/*/block" in pack
    assert "a3f19c2b8e04" in pack
    assert rm.INDEX_REPLY_GUIDANCE in pack
    # The escape road is a selectable item in the pack, not advice beside it.
    assert "[0]" in pack


def test_a_pack_without_menus_is_byte_identical_to_the_pack_before_this_change(
    harness,
):
    """The census (SPEC section 7) classifies every existing render_conj_pack
    caller as MUST NOT MOVE. `reference_menus` defaults to (), so a caller
    that passes nothing renders exactly what it rendered before."""

    from deepreason.llm.packs import render_conj_pack

    problem = _conj_problem(harness)
    without = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs, 2, 4000
    )
    explicitly_empty = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        2,
        4000,
        reference_menus=(),
    )
    assert without == explicitly_empty
    assert "REFERENCE MENU" not in without


def test_menu_sections_are_exact_and_mandatory():
    """A menu may be neither compressed nor dropped, and both halves are
    forced rather than preferred.

    Compression cuts a section's tail, and a menu's tail is its truncation
    notice -- so a compressed menu loses handles AND the statement that
    handles were lost. Dropping is worse still in this codebase: a droppable
    section that is also exact is admitted on its `min_tokens` and then
    rendered at full source size, overshooting the budget with no accounting
    signal (DR-CON-packs-and-token-economy's NEGATIVE rule and its own
    exhibiting check). Exact-and-mandatory is the only pairing that is
    neither, and it is affordable for the same reason it is affordable for
    `frame-crisis`: the content is bounded by construction, here at
    `MenuRenderPolicy.maximum_entries`.
    """

    from deepreason.llm import packs

    menus = (
        rm.render_reference_menu(
            "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block", _binding()
        ),
    )
    sections = packs._menu_sections(menus, 4)
    assert sections
    for section in sections:
        assert section.droppable is False, "a dropped menu leaves no header"
        assert section.compressible is False, "a compressed menu loses handles"


def test_batch_crit_pack_carries_the_menu(harness):
    """The critic's premise_evidence block field is W1's third-commonest
    failure (129 diagnostics), and it fails the same way the conjecturer's
    does: a free pattern with no legal-set owner anywhere."""

    from deepreason.llm.packs import render_batch_crit_pack
    from deepreason.ontology import Commitment, Interface, Provenance

    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    target = harness.create_artifact(
        "the moon pulls the sea",
        interface=Interface(commitments=["k-moon"]),
        provenance=Provenance(role="conjecturer"),
    )
    field_id = "batch-critic.v2:/cases/*/premise_evidence/*/block"
    menus = (rm.render_reference_menu(field_id, _binding()),)
    pack = render_batch_crit_pack(
        [target.id],
        harness.state,
        harness.commitments,
        harness.blobs,
        4000,
        reference_menus=menus,
    )
    assert "/cases/*/premise_evidence/*/block" in pack
    assert "a3f19c2b8e04" in pack
    assert rm.INDEX_REPLY_GUIDANCE in pack


def test_crit_packs_without_menus_do_not_move(harness):
    """Every existing critic-pack caller is MUST NOT MOVE in the census."""

    from deepreason.llm.packs import render_batch_crit_pack, render_crit_pack
    from deepreason.ontology import Commitment, Interface, Provenance

    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    target = harness.create_artifact(
        "the moon pulls the sea",
        interface=Interface(commitments=["k-moon"]),
        provenance=Provenance(role="conjecturer"),
    )
    for render in (render_crit_pack, render_batch_crit_pack):
        first = render(
            [target.id] if render is render_batch_crit_pack else target.id,
            harness.state,
            harness.commitments,
            harness.blobs,
            4000,
        )
        second = render(
            [target.id] if render is render_batch_crit_pack else target.id,
            harness.state,
            harness.commitments,
            harness.blobs,
            4000,
            reference_menus=(),
        )
        assert first == second
        assert "REFERENCE MENU" not in first


# --- the wire schema does not move ---------------------------------------- #


def _v6_contract(**overrides):
    from deepreason.llm.wire import AliasTable, ConjecturerTurnWireContractV6

    values = {"reasoning": True, "aliases": AliasTable({"SRC_001": "c1"})}
    values.update(overrides)
    return ConjecturerTurnWireContractV6(**values)


def _batch_critic_contract(**overrides):
    from deepreason.llm.wire import AliasTable, BatchCriticWireContractV2

    values = {"aliases": AliasTable({"SRC_001": "artifact-one", "SRC_002": "artifact-two"})}
    values.update(overrides)
    return BatchCriticWireContractV2(**values)


def _schema_sha(contract) -> str:
    import hashlib
    import json

    payload = json.dumps(
        contract.model_json_schema(), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_wire_schema_sha_does_not_move(monkeypatch):
    """R8: this layer is prompt rendering and validation-message sourcing.
    No property is added, removed or re-typed on any contract.

    Written to be meaningful BEFORE the citable-block state lands and after
    it: the schema a model reads must not depend on whether the contract was
    told which blocks are citable, because that fact is diagnostic sourcing
    and not part of the form.
    """

    blocks = ("a3f19c2b8e04", "7d0c1149ab52")
    for build in (_v6_contract, _batch_critic_contract):
        bare = _schema_sha(build())
        try:
            informed = _schema_sha(build(citable_block_ids=blocks))
        except TypeError:
            # The parameter has not landed yet; the pin is still meaningful
            # as a same-shape check and becomes the real one once it does.
            informed = _schema_sha(build())
        assert bare == informed, (
            f"{build.__name__}: model_json_schema moved when the contract was "
            f"given its citable-block set; that set is diagnostic sourcing, "
            f"not part of the form the model reads"
        )


# --- one authority: the menu and the diagnostic are the same set ---------- #


def _scratch_error(scratch_handles, new_keys, bad="SCR_999"):
    """A validation error carrying the durable scratch state, exactly as
    `ConjecturerTurnWireContractV6._attach_scratch_reference_context`
    attaches it."""

    error = ValueError("unknown scratch handle")
    error.scratch_reference_context = {
        "scratch_handles": tuple(scratch_handles),
        "new_block_keys": tuple(new_keys),
    }
    return error


def test_menu_and_diagnostic_are_one_set():
    """R5: the diagnostic's legal list is guaranteed identical to the menu
    shown, because both are renderings of ONE `legal_handles_for` result.

    Two lists kept in agreement is what E26's law forbids, and it is what
    the tree did before this module existed: `wire.py` attached the scratch
    namespace to the error and `repair.py` independently re-derived a list
    from it, while the pack showed a third thing.
    """

    from deepreason.llm.repair import _scratch_reference_guidance

    scratch = tuple(f"SCR_{i:03d}" for i in range(1, 15))
    new_keys = ("NEW_001", "NEW_002")
    binding = rm.MenuBinding(scratch_handles=scratch, new_block_keys=new_keys)

    cases = [
        (
            "/scratch_proposal/unresolved_questions/0/related_refs",
            "conjecturer.turn.v6:/scratch_proposal/unresolved_questions/*/related_refs",
        ),
        (
            "/scratch_proposal/links/0/to_ref",
            "conjecturer.turn.v6:/scratch_proposal/links/*/to_ref",
        ),
        (
            "/scratch_proposal/revisions/0/target_alias",
            "conjecturer.turn.v6:/scratch_proposal/revisions/*/target_alias",
        ),
    ]
    for pointer, field_id in cases:
        guidance = _scratch_reference_guidance(
            _scratch_error(scratch, new_keys), pointer, "SCR_999"
        )
        assert guidance is not None, pointer
        menu = rm.legal_handles_for(field_id, binding)
        assert menu is not None, field_id
        assert tuple(guidance["legal_handles"]) == menu.handles, (
            f"{pointer}: the diagnostic's legal list and the menu's differ; "
            f"there must be exactly one resolver for a field's legal set"
        )
        assert bool(guidance["omission_or_unknown_legal"]) == menu.omission_legal


def test_the_diagnostic_consumes_the_resolver_rather_than_agreeing_with_it(
    monkeypatch,
):
    """Set equality alone cannot distinguish ONE authority from two that
    happen to agree -- and on the obvious fixture they do agree, which is
    how "two lists kept in agreement" survives a test suite. So this asserts
    CONSUMPTION: divert the resolver and the diagnostic must follow it.
    """

    from deepreason.llm import repair

    sentinel = rm.LegalHandleSet(
        field_id="sentinel",
        handles=("SCR_777", "NEW_777"),
        total=2,
        truncated=False,
        omission_legal=True,
    )
    monkeypatch.setattr(
        repair, "legal_handles_for", lambda *a, **k: sentinel, raising=True
    )
    guidance = repair._scratch_reference_guidance(
        _scratch_error(("SCR_001",), ()),
        "/scratch_proposal/unresolved_questions/0/related_refs",
        "SCR_999",
    )
    assert tuple(guidance["legal_handles"]) == ("SCR_777", "NEW_777"), (
        "the diagnostic did not follow the resolver; it is re-deriving the "
        "legal set locally, which is the second list E26's law forbids"
    )


def test_the_diagnostic_omission_wording_comes_from_the_declaration():
    """One escape road, one owner. The repair-mode spelling is the
    declaration's `omission_repair`, so the diagnostic cannot describe an
    escape differently from the menu that offered it."""

    from deepreason.llm.repair import _scratch_reference_guidance

    scratch = ("SCR_001",)
    guidance = _scratch_reference_guidance(
        _scratch_error(scratch, ()),
        "/scratch_proposal/unresolved_questions/0/related_refs",
        "SCR_999",
    )
    declaration = rm.REFERENCE_FIELD_DECLARATIONS[
        "conjecturer.turn.v6:/scratch_proposal/unresolved_questions/*/related_refs"
    ]
    assert declaration.omission_repair in guidance["instruction"]


# --- the two block fields gain a legal-set owner --------------------------- #


def test_block_field_diagnostic_lists_legal_blocks():
    """W1's largest single class: 244 + 129 diagnostics on `.../block`, and
    every one of them a bare `string_pattern_mismatch` with no list, because
    nothing in the tree owned the legal block set. The contract now carries
    it, so the diagnostic can say what the menu said.
    """

    from deepreason.llm.repair import diagnostic_from_error

    blocks = ("a3f19c2b8e04", "7d0c1149ab52")
    contract = _v6_contract(citable_block_ids=blocks)
    # A handle that is not even well-formed hex, which is what the 244
    # recorded `string_pattern_mismatch` diagnostics on this field are. Note
    # that a well-formed but INVENTED hex handle passes this pattern and is
    # caught later by the citation checker -- the menu's job is to stop both,
    # and only the first is visible to the wire.
    value = {
        "candidates": [
            {
                "claim": "the moon pulls the sea",
                "mechanism": "tidal bulge",
                "counterconditions": ["none"],
                "checker_specs": [],
                "typicality": 0.5,
                "optional_refs": [],
                "evidence_refs": [{"block": "the-tides-paper", "quote": "q"}],
            }
        ]
    }
    try:
        contract.validate_value(value)
    except Exception as error:  # noqa: BLE001 - the diagnostic is the subject
        diagnostics = diagnostic_from_error(
            contract.contract_id, error, contract.model_json_schema()
        )
    else:  # pragma: no cover - the fixture is invalid by construction
        raise AssertionError("the invented block handle was accepted")

    items = diagnostics if isinstance(diagnostics, list) else [diagnostics]
    listed = [
        item
        for item in items
        if getattr(item, "legal_handles", None)
        and set(blocks) <= set(item.legal_handles)
    ]
    assert listed, (
        f"no diagnostic listed the legal block set; got "
        f"{[(getattr(i, 'path', None), getattr(i, 'legal_handles', None)) for i in items]}"
    )


def test_a_contract_told_no_blocks_offers_no_block_list():
    """Absence is not an empty menu. A run with no citable evidence must not
    receive a menu implying one exists -- that is the empty slot the judge
    blinding research measured as worse than a populated one."""

    contract = _v6_contract()
    assert contract.citable_block_ids == ()
    assert (
        rm.render_reference_menu(
            "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block",
            rm.MenuBinding(),
        )
        is None
    )


def test_batch_critic_block_diagnostic_lists_legal_blocks():
    """The critic's half of the same class: 129 diagnostics on
    /cases/*/premise_evidence/*/block, likewise with no list until now."""

    from deepreason.llm.repair import diagnostic_from_error

    blocks = ("a3f19c2b8e04", "7d0c1149ab52")
    contract = _batch_critic_contract(citable_block_ids=blocks)
    value = {
        "cases": [
            {
                "target_alias": "SRC_001",
                "attack": True,
                "case": "the mechanism is unstated",
                "premise_evidence": [
                    {"block": "the-tides-paper", "quote": "q"}
                ],
            }
        ]
    }
    try:
        contract.validate_value(value)
    except Exception as error:  # noqa: BLE001 - the diagnostic is the subject
        diagnostics = diagnostic_from_error(
            contract.contract_id, error, contract.model_json_schema()
        )
    else:  # pragma: no cover - invalid by construction
        raise AssertionError("the malformed block handle was accepted")

    items = diagnostics if isinstance(diagnostics, list) else [diagnostics]
    listed = [
        item
        for item in items
        if getattr(item, "legal_handles", None)
        and set(blocks) <= set(item.legal_handles)
    ]
    assert listed, (
        f"no diagnostic listed the legal block set; got "
        f"{[(getattr(i, 'path', None), getattr(i, 'legal_handles', None)) for i in items]}"
    )


# --- a seat replying by index resolves to the right handle ----------------- #


def test_index_reply_resolves_to_the_menu_entry():
    """R9. The menu says 'you may answer with the handle itself or with its
    [index]', so an index reply must land on the handle the menu showed at
    that index -- the same `legal_handles_for` ordering, not a re-derivation.
    """

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    blocks = tuple(f"{i:012x}" for i in range(1, 12))
    binding = _binding(citable_block_ids=blocks)
    for index, expected in enumerate(blocks, start=1):
        for spelling in (f"[{index}]", str(index), f"#{index}", f" {index} "):
            assert (
                rm.resolve_index_reply(field_id, spelling, binding) == expected
            ), f"{spelling!r} did not resolve to entry {index}"


def test_index_zero_takes_the_omission_where_it_is_legal():
    """The escape road as a structural act rather than prose advice: the
    seat selects [0] and the field is dropped. W1 measured what advice
    achieves -- 7 of 120 ladders took an escape the diagnostic spelled out.
    """

    legal_field = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    assert (
        rm.resolve_index_reply(legal_field, "[0]", _binding()) is rm.OMISSION
    )
    closed_field = "conjecturer.turn.v6:/scratch_proposal/links/*/to_ref"
    assert rm.resolve_index_reply(closed_field, "[0]", _binding()) == "[0]", (
        "an omission was resolved for a field whose validators do not accept "
        "one; a menu may never decide validity"
    )


def test_an_out_of_range_or_unknown_index_is_left_untouched():
    """Resolution never guesses. A reply this menu cannot address stays
    exactly as the model wrote it, so the validators see the real value and
    the diagnostic reports the real mistake."""

    field_id = "conjecturer.turn.v6:/candidates/*/evidence_refs/*/block"
    binding = _binding()  # three blocks
    assert rm.resolve_index_reply(field_id, "[99]", binding) == "[99]"
    assert rm.resolve_index_reply(field_id, "a3f19c2b8e04", binding) == "a3f19c2b8e04"
    assert rm.resolve_index_reply("no.such.field:/x", "[1]", binding) == "[1]"
    assert rm.resolve_index_reply(field_id, "[1]", rm.MenuBinding()) == "[1]"
    assert rm.resolve_index_reply(field_id, 7, binding) == 7


def test_a_seat_replying_by_index_validates_end_to_end():
    """R9, through the real contract rather than the resolver alone: the
    value the validators see is a handle, so the schema the model read is
    unchanged and nothing about validity moved."""

    contract = _v6_contract(citable_block_ids=("a3f19c2b8e04", "7d0c1149ab52"))

    def candidate(block):
        return {
            "claim": "the moon pulls the sea",
            "mechanism": "tidal bulge",
            "counterconditions": ["none"],
            "checker_specs": [],
            "typicality": 0.5,
            "optional_refs": [],
            "evidence_refs": [{"block": block, "quote": "q"}],
        }

    turn = contract.validate_value({"candidates": [candidate("[2]")]})
    assert turn.candidates[0].evidence_refs[0].block == "7d0c1149ab52"

    # [0] is the escape, and it removes the whole reference rather than
    # leaving a {quote} with no block -- which would turn a legal omission
    # into a fresh validation failure.
    omitted = contract.validate_value({"candidates": [candidate("[0]")]})
    assert omitted.candidates[0].evidence_refs == ()

    # A handle written out in full still works, unchanged.
    direct = contract.validate_value({"candidates": [candidate("a3f19c2b8e04")]})
    assert direct.candidates[0].evidence_refs[0].block == "a3f19c2b8e04"


def test_index_resolution_is_a_no_op_for_a_contract_that_declares_no_menu():
    """A contract cannot acquire this behaviour by accident: the base hook
    returns no binding, so resolution never runs where it was not declared."""

    from deepreason.llm.wire import AliasTable, CriticWireContract
    from deepreason.llm.contracts import ArgumentativeCriticOutput

    contract = CriticWireContract(
        aliases=AliasTable({"A1": "artifact-one"}),
        expected_target="artifact-one",
    )
    assert contract._menu_binding({}) is None
    assert contract._resolve_menu_indices({"x": "[2]"}) == {"x": "[2]"}


# --- architecture: the interface is enforced, not merely offered ---------- #


def test_a_menu_never_changes_what_is_valid():
    """FROZEN clause (b), and F2's instance of the harness's oldest
    invariant: measures never adjudicate.

    A menu changes what the model is SHOWN. It may never change what the
    validators ACCEPT. Emptying the registry removes every menu and every
    index resolution; the verdicts must not move.
    """

    saved = dict(rm.REFERENCE_FIELD_DECLARATIONS)

    def candidate(block, refs=()):
        return {
            "claim": "the moon pulls the sea",
            "mechanism": "tidal bulge",
            "counterconditions": ["none"],
            "checker_specs": [],
            "typicality": 0.5,
            "optional_refs": list(refs),
            "evidence_refs": [{"block": block, "quote": "q"}],
        }

    corpus = [
        {"candidates": [candidate("a3f19c2b8e04")]},
        {"candidates": [candidate("the-tides-paper")]},
        {"candidates": [candidate("a3f19c2b8e04", refs=["SRC_001"])]},
        {"candidates": [candidate("a3f19c2b8e04", refs=["SRC_999"])]},
        {"candidates": []},
        {"candidates": [candidate("A3F19C2B8E04")]},
    ]

    def verdicts():
        out = []
        contract = _v6_contract(citable_block_ids=("a3f19c2b8e04", "7d0c1149ab52"))
        for value in corpus:
            try:
                contract.validate_value(value)
                out.append("VALID")
            except Exception as error:  # noqa: BLE001 - the verdict is the subject
                out.append(type(error).__name__)
        return out

    with_menus = verdicts()
    try:
        rm.REFERENCE_FIELD_DECLARATIONS.clear()
        without_menus = verdicts()
    finally:
        rm.REFERENCE_FIELD_DECLARATIONS.update(saved)

    assert with_menus == without_menus, (
        f"the menu machinery moved a verdict: {with_menus} vs {without_menus}; "
        f"a menu is presentation and may never decide validity"
    )
    assert verdicts() == with_menus, "the registry was not restored"


def test_consumers_reach_the_legal_set_only_through_the_interface():
    """The other half of enforced modularity, mirroring
    tests/test_signal_contract.py's controller check.

    This passes on the tree as it stands, so its value is not that it turns
    anything green today: it FAILS the day a consumer re-derives a legal
    handle set itself, which is exactly what `repair.py` did before this
    module existed -- and what made the prompt, the wire and the diagnostic
    three lists of one fact.
    """

    import ast
    import pathlib

    from deepreason.llm import packs, repair

    for module in (packs, repair):
        source = pathlib.Path(module.__file__).read_text()
        tree = ast.parse(source)
        reaches_interface = any(
            isinstance(node, ast.ImportFrom)
            and (node.module or "").endswith("reference_menu")
            for node in ast.walk(tree)
        ) or any(
            isinstance(node, ast.ImportFrom)
            and (node.module or "") == "deepreason.llm"
            and any(a.name == "reference_menu" for a in node.names)
            for node in ast.walk(tree)
        )
        assert reaches_interface, (
            f"{module.__name__} does not consume the reference-menu interface"
        )

    # `repair.py` must not rebuild a legal list from a subsystem's state: the
    # only local composition of scratch handles left is the fallback for a
    # pointer the registry does not cover, and it is guarded by the
    # declaration being None.
    source = pathlib.Path(repair.__file__).read_text()
    guidance = source.split("def _scratch_reference_guidance", 1)[1].split(
        "\ndef ", 1
    )[0]
    assert "legal_handles_for(" in guidance, (
        "the scratch diagnostic stopped consuming the resolver"
    )
    block_guidance = source.split("def _block_reference_guidance", 1)[1].split(
        "\ndef ", 1
    )[0]
    assert "legal_handles_for(" in block_guidance, (
        "the block diagnostic stopped consuming the resolver"
    )


def test_no_critic_menu_can_carry_scratch_content():
    """DR-SEAM-rules-x-scratch's structural refusal, extended to cover the
    new parameter.

    Criticism is given no scratch content, and that section warns in writing
    that the danger is "a scratch parameter arriving disguised as one more"
    optional argument. `reference_menus` is exactly such an argument, so the
    refusal is re-established for it here rather than left to the current
    caller's good behaviour: no scratch-kind field is declared on a critic
    contract, and `rules/crit.py` requests only citable-block menus.
    """

    import pathlib

    from deepreason.rules import crit

    for declaration in rm.declarations_for_contract("batch-critic.v2"):
        assert not declaration.handle_kind.startswith("scratch"), (
            f"{declaration.field_id} would put scratch content in a critic pack"
        )

    source = pathlib.Path(crit.__file__).read_text()
    body = source.split("def _premise_evidence_menus", 1)[1].split("\ndef ", 1)[0]
    assert 'handle_kinds=("citable_block",)' in body, (
        "the critic's menu builder no longer restricts itself to citable "
        "blocks; a scratch-kind menu would reach a criticism pack"
    )


def test_a_pre_v6_conjecture_pack_carries_no_v6_menu():
    """Regression (full gate, F2-d): the post-allocation menus were appended
    outside the v6 guard, so a pre-v6 run received a menu for
    `optional_refs` -- a field its own form does not have.

    Caught by `tests/test_semantic_freedom_constitution.py::
    test_offline_semantic_freedom_baseline_is_measurable`, whose pinned
    `tokens_per_admitted_useful_candidate` moved 784.5 -> 875.0 while every
    epistemic metric it records stayed identical. The token cost was the
    only visible symptom of a menu naming a field the seat cannot fill.
    The fixture was NOT updated: gating the menus restored it exactly.

    784.5 was that metric's pinned value at the time. It is now 825.0: the
    render-layout tranche (2026-08-28) re-pinned it as a disclosed cost, with
    every added prompt character accounted for. The lesson here is unchanged
    and is the reason that re-pin had to be argued from the prompt bytes — a
    token rise with the epistemic metrics identical is exactly what a defect
    of this class looks like.
    """

    import ast
    import pathlib

    from deepreason.llm import seat_source_plugins

    # The two menu builds moved out of `rules/conj.py` into the seat's
    # registered section sources (2026-09-04) and the guard moved with them.
    # The claim is unchanged and so is its bite: every menu build in the tree
    # is reached only on the v6 path, whichever module holds it.
    source = pathlib.Path(seat_source_plugins.__file__).read_text()
    tree = ast.parse(source)
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "menu_renders_for"
            for call in ast.walk(node)
        )
    ]
    assert functions, "no section source builds reference menus at all"
    for function in functions:
        guards = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and getattr(node.func, "attr", "") == "lookup"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "active_v6"
        ]
        assert guards, (
            f"{function.name} builds a menu without consulting active_v6; the "
            "v6 turn contract's fields must not be offered to a pre-v6 form"
        )
