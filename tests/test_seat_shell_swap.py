"""R20, demonstrated: the conjecturer's shell bound where the critic's is.

The operator's amendment, verbatim (2026-09-03): *"Is prefer if the
conjecturer seat could be used to replace the critic seat. That means an
artifact truely is determined by input and output, the artifact is just a
shell."* That is an obligation on the DELIVERABLE, so it gets a demonstration
rather than a shape argument.

**WHAT THIS FILE DOES NOT CLAIM.** It does not claim that a conjecturer shell
in a critic's seat produces useful criticism, or criticism at all. It proves
the SHELL IS SWAPPABLE — that the brief a seat is shown and the form it is
asked to fill are configuration, and that swapping them changes what is
rendered and nothing on the evidence side. Whether such a swap is a good idea
is an experiment (SPEC S12), and this tranche's answer to that is
"not measured".

Offline throughout: no provider call, no API key.
"""

import pytest

from deepreason.llm.packs import render_conj_pack, render_crit_pack
from deepreason.llm.seat_layouts import (
    CONJECTURER_LEGACY_SHELL,
    CRITIC_LEGACY_SHELL,
)
from deepreason.llm.seat_plugins import ensure_seeded
from deepreason.llm.seat_sections import (
    SEAT_SHELL_ENV,
    SectionReceiptV1,
    resolve_seat_pack_layout,
    resolve_seat_shell,
)
from deepreason.llm.wire import AliasTable, wire_contract_for
from deepreason.llm.contracts import ArgumentativeCriticOutput
from tests.crit_pack_golden_cases import _rich_kwargs, _seed

CRITIC_SEAT = "argumentative_critic"


@pytest.fixture(autouse=True)
def seeded():
    ensure_seeded()


def _render_critic(tmp_path, **overrides):
    harness, problem, target_id, _bare = _seed(tmp_path)
    kwargs = _rich_kwargs(harness, problem, target_id)
    kwargs.update(overrides)
    receipts: list[SectionReceiptV1] = []
    pack = render_crit_pack(token_budget=6000, section_receipts=receipts, **kwargs)
    return pack, receipts, target_id


def test_the_two_shipped_shells_describe_todays_two_seats():
    assert resolve_seat_shell("conjecturer") == CONJECTURER_LEGACY_SHELL
    assert resolve_seat_shell(CRITIC_SEAT) == CRITIC_LEGACY_SHELL
    assert CONJECTURER_LEGACY_SHELL.layout_id != CRITIC_LEGACY_SHELL.layout_id
    assert CONJECTURER_LEGACY_SHELL.form_id != CRITIC_LEGACY_SHELL.form_id


def test_1_the_critic_seat_renders_under_whichever_shell_is_bound(
    tmp_path, monkeypatch
):
    """Assertion 1: bind the CONJECTURER shell in the critic's place, and the
    critic's call renders that shell's brief instead of its own."""
    before, _receipts, _target = _render_critic(tmp_path)
    assert "## target-commitments" in before
    assert "## criteria" not in before

    monkeypatch.setenv(SEAT_SHELL_ENV, f"{CRITIC_SEAT}=seat.conjecturer.legacy-v0")
    assert (
        resolve_seat_pack_layout(CRITIC_SEAT).layout_id
        == CONJECTURER_LEGACY_SHELL.layout_id
    )
    after, _receipts, _target = _render_critic(tmp_path / "swapped")

    # The critic's own sections are gone, and the OUTPUT CONTRACT — the
    # clearest single signal of which shell ran — is the conjecturer's.
    assert "## target-commitments" not in after
    assert "## target\n" not in after
    assert "mount the strongest NEW specific case against the target" not in after
    assert "diverse candidates with typicality estimates" in after

    # And the honest limit, asserted rather than glossed: the conjecturer
    # sections that need a PROBLEM decline in a seat whose request has none.
    # A shell is portable; what it can render still depends on what the seat's
    # request carries. That is the protocol working, not failing — `None` means
    # "this section has nothing this cycle".
    assert "## criteria" not in after
    assert "## problem\n" not in after


def test_2_the_receipts_record_the_shell_that_actually_ran(tmp_path, monkeypatch):
    """Assertion 2: the record follows the swap. A receipt naming the seat's
    nominal plugins while a different shell ran would make the swap
    unauditable."""
    monkeypatch.setenv(SEAT_SHELL_ENV, f"{CRITIC_SEAT}=seat.conjecturer.legacy-v0")
    _pack, receipts, _target = _render_critic(tmp_path)
    rendered = {r.plugin_id for r in receipts}
    assert "dr.criteria" in rendered            # a conjecturer plugin ran
    assert "dr.target-commitments" not in rendered   # no critic plugin did
    # ...and the ones that could not render are recorded ABSENT, not omitted:
    # a swap whose declined sections left no trace would be unauditable.
    absent = {r.plugin_id for r in receipts if r.disposition == "absent"}
    assert "dr.criteria" in absent and "dr.problem" in absent
    assert resolve_seat_shell(CRITIC_SEAT).shell_id == "seat.conjecturer.legacy-v0"


def test_3_the_parse_half_does_not_vary_with_the_shell(tmp_path, monkeypatch):
    """Assertion 3, and the law's own scope boundary. The shell governs how
    content is GENERATED; what counts as EVIDENCE does not vary with it. So a
    swapped shell still compiles its reply through the FIXED parse half of
    whichever form is named — the canonical model is untouched."""
    contract = wire_contract_for(
        CRITIC_SEAT,
        ArgumentativeCriticOutput,
        "compact",
        AliasTable({"A_001": "artifact-1"}),
        expected_target="artifact-1",
    )
    monkeypatch.setenv(SEAT_SHELL_ENV, f"{CRITIC_SEAT}=seat.conjecturer.legacy-v0")
    swapped = wire_contract_for(
        CRITIC_SEAT,
        ArgumentativeCriticOutput,
        "compact",
        AliasTable({"A_001": "artifact-1"}),
        expected_target="artifact-1",
    )
    assert contract.contract_id == swapped.contract_id
    assert contract.canonical_model is swapped.canonical_model is ArgumentativeCriticOutput


def test_4_expected_target_and_alias_binding_are_unchanged(tmp_path, monkeypatch):
    """Assertion 4. The critic's target binding is AUTHORITY-side: which
    artifact may be attacked is not the shell's to move, and a swap that moved
    it would have crossed the law's scope boundary."""
    aliases = AliasTable({"A_001": "artifact-1"})
    monkeypatch.setenv(SEAT_SHELL_ENV, f"{CRITIC_SEAT}=seat.conjecturer.legacy-v0")
    contract = wire_contract_for(
        CRITIC_SEAT,
        ArgumentativeCriticOutput,
        "compact",
        aliases,
        expected_target="artifact-1",
    )
    assert contract.expected_target == "artifact-1"
    assert contract.expected_alias == aliases.alias_for("artifact-1")
    assert contract.aliases.aliases == aliases.aliases


def test_the_swap_is_reversible_and_leaves_no_residue(tmp_path, monkeypatch):
    """A configuration change, not a migration: unbinding restores the seat."""
    monkeypatch.setenv(SEAT_SHELL_ENV, f"{CRITIC_SEAT}=seat.conjecturer.legacy-v0")
    swapped, _r, _t = _render_critic(tmp_path)
    monkeypatch.delenv(SEAT_SHELL_ENV)
    restored, _r, _t = _render_critic(tmp_path / "restored")
    assert "## target-commitments" in restored
    assert "## criteria" not in restored
    assert swapped != restored
