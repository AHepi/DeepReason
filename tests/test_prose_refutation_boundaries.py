"""Boundaries the prose-refutation work must not cross.

Implements R5/R6 of `experiments/2026-08-01-change-prose-can-refute/REQUEST.md`,
the operator's verbatim instruction:

    "The scratchpad authority chain needs to be completely separate from
     conjecture/criticism adjudication. They shouldn't exist together."

The scratchpad is an imaginative workshop declared `advisory_non_grounding`:
storage alone never makes a note a fact, evidence, or support for one.  These
tests pin the stronger property the operator asked for -- separation of the
AUTHORITY chain, not merely of grounding.  Nothing a criticism can act on, and
nothing that decides what stands, may carry a scratch object.

They pass today.  They exist so that the prose-refutation work, which widens
what a criticism is given and what it may do, cannot quietly couple the two.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from deepreason.llm import packs
from deepreason.rules import crit

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "deepreason"


def _imported_modules(path: Path) -> set[str]:
    """Every module named by an import anywhere in the file, nested included."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            seen.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            seen.add(node.module)
    return seen


def test_the_criticism_rule_imports_no_scratch_module():
    """R5/R6: the criticism side must not reach the scratchpad at all.

    A function-local import would satisfy a top-of-file grep and still couple
    the two, so the whole module is walked rather than its header.
    """

    imported = _imported_modules(_SOURCE_ROOT / "rules" / "crit.py")

    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )


def test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence():
    """R5/R6: `scratch_fence_seq` is transactional ordering, not content.

    The fence is the one legitimate appearance of the word on this side -- it
    sequences a transaction against the scratch log without reading it.  If any
    other scratch name appears here, the separation has been breached.
    """

    source = (_SOURCE_ROOT / "rules" / "crit.py").read_text(encoding="utf-8")
    mentions = [
        line.strip()
        for line in source.splitlines()
        if "scratch" in line.lower() and not line.strip().startswith("#")
    ]

    assert mentions, "expected the fence assignments; the test is stale otherwise"
    assert all("scratch_fence_seq" in line for line in mentions), mentions


def test_the_criticism_pack_cannot_be_given_scratch():
    """R5/R6: separation enforced by the signature, not by call-site habit.

    `render_conj_pack` accepts `scratch_context` because conjecture is where
    the workshop belongs.  The criticism pack must have no such parameter, so
    no future caller can pass one without changing this contract.
    """

    assert "scratch_context" in inspect.signature(packs.render_conj_pack).parameters

    for name in ("render_crit_pack", "render_batch_crit_pack"):
        parameters = inspect.signature(getattr(packs, name)).parameters
        assert "scratch_context" not in parameters, (name, sorted(parameters))


def test_the_defended_trial_imports_no_scratch_module():
    """R5/R6: the trial decides what stands, so it is authority chain proper.

    `crit_argumentative` routes a sustained case here, so this module is the
    last link before a prose case can change a status.  It must be as separate
    from the workshop as the criticism rule is.
    """

    imported = _imported_modules(_SOURCE_ROOT / "informal" / "trial.py")

    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )


def test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge():
    """R5/R6: what a warrant may name is the narrowest part of the chain.

    A warrant's referents are an artifact, a commitment, a validity node and a
    trace blob.  None of them is a scratch object, and nothing in the warrant
    module may import one.
    """

    imported = _imported_modules(_SOURCE_ROOT / "rules" / "warrants.py")
    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )

    imported = _imported_modules(_SOURCE_ROOT / "adjudication" / "edges.py")
    assert not [name for name in imported if name.startswith("deepreason.scratch")], (
        sorted(imported)
    )
