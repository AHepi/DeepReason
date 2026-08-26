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
