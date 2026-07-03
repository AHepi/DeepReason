"""P0 acceptance tests (spec §16) — deterministic core.

All skipped until P0 implementation lands. They encode the normative cases:
grounded extension correctness, reinstatement (Lemma 3.1), two-pass support
cascade, dep cycle rejection, case-law closure collapse/reinstatement.
"""

import pytest

pytestmark = pytest.mark.skip(reason="P0 not implemented yet")


def test_grounded_extension_unattacked_accepted():
    """An unattacked artifact is in G (accepted)."""


def test_reinstatement_lemma_3_1():
    """k attacks a, j attacks k, j unattacked => {j, a} in G."""


def test_support_cascade_orphaned_not_false():
    """Refuted premise => dependents suspended_unsupported, NOT refuted."""


def test_dep_cycle_rejected():
    """A dependence ref creating a cycle is rejected at registration."""


def test_standard_refutation_collapses_verdicts_and_reinstates():
    """Case-law closure (§1): refute a standard => every nu citing it is
    attacked => warrants fall => targets reinstate, all in pass 1."""
