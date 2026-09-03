"""The typed receipt of what a brief actually showed (SPEC S1.4, S7, A4).

"Not typed" (R7) constrains a plugin's OUTPUT, not its RECEIPT. A plugin that
emitted nothing typed at all would make the run unauditable, which contradicts
this repo's own epistemology: the record is the only admissible evidence.

The distinction this file exists to protect is `rendered` against `dropped`
against `absent`. The walk can only say a section rendered; whether it
survived the budget is the ALLOCATOR's answer, and a receipt that reported
`rendered` for a section the seat never saw would be the silent cap the whole
layer abolishes, telling the record a more comfortable story than the pack.

NOT IN THIS TRANCHE: writing these to the run's record. That needs a new
object kind, which is a frozen-surface-2 contact and is awaiting an operator
grant (CHECKLIST step 24). The receipts themselves need no grant, so they are
built and proven here.
"""

import pytest

from deepreason.llm.packs import render_conj_pack, render_crit_pack
from deepreason.llm.seat_plugins import ensure_seeded
from deepreason.llm.seat_sections import DISPOSITIONS, SectionReceiptV1
from tests.conj_pack_golden_cases import _rich_kwargs, _seed, _seed_bare
from tests.crit_pack_golden_cases import _rich_kwargs as _crit_rich
from tests.crit_pack_golden_cases import _seed as _crit_seed


@pytest.fixture(autouse=True)
def seeded():
    ensure_seeded()


def _conj(tmp_path, **overrides):
    problem, harness, ids = _seed(tmp_path)
    kwargs = _rich_kwargs(problem, harness, ids)
    kwargs.update(overrides)
    receipts: list[SectionReceiptV1] = []
    pack = render_conj_pack(token_budget=6000, section_receipts=receipts, **kwargs)
    return pack, receipts


def test_every_visited_entry_leaves_a_receipt(tmp_path):
    from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_LAYOUT

    _pack, receipts = _conj(tmp_path)
    assert len(receipts) == len(CONJECTURER_LEGACY_LAYOUT.entries)
    assert all(isinstance(r, SectionReceiptV1) for r in receipts)
    assert all(r.disposition in DISPOSITIONS for r in receipts)


def test_a_receipt_names_the_plugin_and_the_version_that_ran(tmp_path):
    """"Which bytes did this run show, from which plugin, at which version,
    under which parameters" must be answerable from the receipt alone."""
    _pack, receipts = _conj(tmp_path)
    by_section = {r.section_id: r for r in receipts}
    problem = by_section["problem"]
    assert problem.plugin_id == "dr.problem"
    assert problem.plugin_version == "1.0.0"
    assert problem.parameters_digest.startswith("sha256:")
    assert problem.disposition == "rendered"
    assert problem.source_bytes > 0


def test_a_plugin_that_declined_is_absent_not_dropped(tmp_path):
    """`absent` is the plugin having nothing this cycle; `dropped` is the
    allocator cutting content that existed. Collapsing them would lose the
    distinction the record is for."""
    problem, harness = _seed_bare(tmp_path)
    receipts: list[SectionReceiptV1] = []
    render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=2,
        token_budget=4000,
        neighbourhood_n=0,
        section_receipts=receipts,
    )
    by_section = {r.section_id: r for r in receipts}
    # A bare first cycle has no evidence, no neighbourhood and no school.
    assert by_section["citable-evidence-blocks"].disposition == "absent"
    assert by_section["neighbourhood"].disposition == "absent"
    assert by_section["problem"].disposition == "rendered"
    for receipt in receipts:
        if receipt.disposition == "absent":
            assert receipt.source_bytes == 0 and receipt.rendered_bytes == 0


def test_a_section_the_allocator_cut_is_recorded_as_dropped(tmp_path):
    """The case the whole file turns on: the walk said `rendered`, the budget
    disagreed, and the RECORD follows the budget."""
    _pack, wide = _conj(tmp_path)
    problem, harness, ids = _seed(tmp_path / "tight")
    kwargs = _rich_kwargs(problem, harness, ids)
    receipts: list[SectionReceiptV1] = []
    pack = render_conj_pack(token_budget=900, section_receipts=receipts, **kwargs)

    assert "CONTEXT WITHHELD FOR BUDGET" in pack
    dropped = {r.section_id for r in receipts if r.disposition == "dropped"}
    assert dropped, [(r.section_id, r.disposition) for r in receipts]
    # Every dropped section really is missing from the pack, and every one of
    # them rendered something at the wide budget -- so this is the allocator
    # cutting content, not a plugin declining.
    rendered_wide = {r.section_id for r in wide if r.disposition == "rendered"}
    for section_id in dropped:
        assert f"## {section_id}\n" not in pack, section_id
        assert section_id in rendered_wide, section_id
    assert all(r.rendered_bytes == 0 for r in receipts if r.disposition == "dropped")


def test_a_compressed_section_is_recorded_as_compressed(tmp_path):
    """Between rendered and dropped: the seat saw part of it, and the record
    says so rather than reporting a whole section."""
    problem, harness, ids = _seed(tmp_path)
    kwargs = _rich_kwargs(problem, harness, ids)
    for budget in (900, 1200, 1500, 1800, 2100, 2400):
        receipts: list[SectionReceiptV1] = []
        render_conj_pack(token_budget=budget, section_receipts=receipts, **kwargs)
        compressed = [r for r in receipts if r.disposition == "compressed"]
        if compressed:
            assert all(0 < r.rendered_bytes < r.source_bytes for r in compressed)
            return
    pytest.skip("no budget in the swept range compressed a section")


def test_the_critic_seat_produces_receipts_the_same_way(tmp_path):
    """A seat is a shell: the receipt machinery does not know which seat ran."""
    from deepreason.llm.seat_layouts import CRITIC_LEGACY_LAYOUT

    harness, problem, target_id, _bare = _crit_seed(tmp_path)
    kwargs = _crit_rich(harness, problem, target_id)
    receipts: list[SectionReceiptV1] = []
    render_crit_pack(token_budget=6000, section_receipts=receipts, **kwargs)

    assert len(receipts) == len(CRITIC_LEGACY_LAYOUT.entries)
    by_section = {r.section_id: r for r in receipts}
    assert by_section["target"].plugin_id == "dr.target"
    assert by_section["target"].disposition == "rendered"
    # The shared plugin appears in BOTH seats' receipts under one id.
    assert by_section["frame-slice"].plugin_id == "dr.frame.slice"


def test_no_receipt_field_names_a_seat():
    """The seat-is-a-shell law's scope boundary, on the record side: a receipt
    that named its seat would hand the evidence side a generation-side fact."""
    assert not [f for f in SectionReceiptV1.model_fields if "seat" in f.lower()]
