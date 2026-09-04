"""`wire_contract_for`'s answers are frozen by two callers (SPEC §17.9).

This tranche's frozen-surface forecast was NO CONTACT, and
`tools/blast_radius.py` disagreed the moment `wire_contract_for` was declared
a touched symbol:

    frozen_surface_verdict CONTACT
      - replay-validation record formats (invariants.py) | SYMBOL_INDIRECT
      - manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT

Both rows were opened rather than dismissed as grep artefacts, and both are
REAL call sites:

* `invariants.py:1233` calls it for the conjecturer and takes `.contract_id`
  to build the AUTHORIZED CONTRACT ID SET a replay validates a conjecturer
  call against. A different id for an unchanged input would change committed
  roots' replay verdicts. That is frozen surface 3.
* `run_manifest.py:2074` calls it for the defender, judge and variator seats
  and folds each `.contract_id` into the manifest's behavioral assignments,
  which `production_contract_pairs` projects into the qualification subject.
  That is frozen surfaces 4 and 5.

So the constraint this file pins: **for every input those callers make,
`wire_contract_for` keeps returning the same `contract_id`.** Form selection in
this tranche therefore happens at the DISPATCH SITE — a seat asks for the
contract it wants — and never by changing this function's answer.

The table below is deliberately NOT a sweep over every model class in the
tree: a sweep would go red when someone adds an unrelated contract, which
would make it noise rather than a check. It is exactly the inputs that reach a
frozen surface, plus the seat forms this tranche can select among.
"""

import pytest

from deepreason.llm.contracts import (
    ArgumentativeCriticOutput,
    ConjecturerOutput,
    DefenderOutput,
    JudgeRuling,
    PairwiseRuling,
    SynthesizerOutput,
    VariatorOutput,
)
from deepreason.llm.wire import AliasTable, wire_contract_for
from deepreason.workloads.text import ReasoningConjecturerOutput

_PROFILES = ("compact", "standard", "frontier")

# (role, output model, profile) -> contract_id, captured from base e91f4fcc3.
# Every row is reachable from `invariants.py:1233` or `run_manifest.py:2074`,
# or is a form this tranche's seats may select.
FROZEN_MAP = {
    ("conjecturer", "ConjecturerOutput", "compact"): "conjecturer.compact.v1",
    ("conjecturer", "ConjecturerOutput", "standard"): "conjecturer.direct.v1",
    ("conjecturer", "ConjecturerOutput", "frontier"): "conjecturer.direct.v1",
    ("conjecturer", "ReasoningConjecturerOutput", "compact"): "reasoning.conjecturer.compact.v2",
    ("conjecturer", "ReasoningConjecturerOutput", "standard"): "reasoningconjecturer.direct.v1",
    ("conjecturer", "ReasoningConjecturerOutput", "frontier"): "reasoningconjecturer.direct.v1",
    ("defender", "DefenderOutput", "compact"): "defender.compact.v1",
    ("defender", "DefenderOutput", "standard"): "defender.direct.v1",
    ("defender", "DefenderOutput", "frontier"): "defender.direct.v1",
    ("judge", "JudgeRuling", "compact"): "judge.compact.v1",
    ("judge", "JudgeRuling", "standard"): "judgeruling.direct.v1",
    ("judge", "JudgeRuling", "frontier"): "judgeruling.direct.v1",
    ("judge", "PairwiseRuling", "compact"): "judge_pairwise.compact.v1",
    ("judge", "PairwiseRuling", "standard"): "pairwiseruling.direct.v1",
    ("judge", "PairwiseRuling", "frontier"): "pairwiseruling.direct.v1",
    ("variator", "VariatorOutput", "compact"): "variator.compact.v1",
    ("variator", "VariatorOutput", "standard"): "variator.direct.v1",
    ("variator", "VariatorOutput", "frontier"): "variator.direct.v1",
    ("argumentative_critic", "ArgumentativeCriticOutput", "compact"): "argumentative_critic.compact.v1",
    ("argumentative_critic", "ArgumentativeCriticOutput", "standard"): "argumentativecritic.direct.v1",
    ("argumentative_critic", "ArgumentativeCriticOutput", "frontier"): "argumentativecritic.direct.v1",
    ("synthesizer", "SynthesizerOutput", "compact"): "synthesizer.compact.v1",
    ("synthesizer", "SynthesizerOutput", "standard"): "synthesizer.direct.v1",
    ("synthesizer", "SynthesizerOutput", "frontier"): "synthesizer.direct.v1",
}

_MODELS = {
    "ConjecturerOutput": ConjecturerOutput,
    "ReasoningConjecturerOutput": ReasoningConjecturerOutput,
    "DefenderOutput": DefenderOutput,
    "JudgeRuling": JudgeRuling,
    "PairwiseRuling": PairwiseRuling,
    "VariatorOutput": VariatorOutput,
    "ArgumentativeCriticOutput": ArgumentativeCriticOutput,
    "SynthesizerOutput": SynthesizerOutput,
}


def _resolve(role, model_name, profile):
    return wire_contract_for(
        role,
        _MODELS[model_name],
        profile,
        AliasTable({"A_001": "artifact-1"}),
        expected_target="artifact-1",
    ).contract_id


@pytest.mark.parametrize("key,expected", sorted(FROZEN_MAP.items()))
def test_the_contract_id_for_a_frozen_input_has_not_moved(key, expected):
    assert _resolve(*key) == expected


def test_every_profile_of_every_pinned_pair_is_covered():
    """A table with a hole is a check with a hole: the pairs below are the ones
    whose answers reach a frozen surface, so all three profiles of each must be
    pinned."""
    pairs = {(role, model) for role, model, _profile in FROZEN_MAP}
    for role, model in pairs:
        for profile in _PROFILES:
            assert (role, model, profile) in FROZEN_MAP, (role, model, profile)


def test_the_two_frozen_callers_still_call_this_function():
    """The pin is only worth having while those callers exist. If either stops
    calling `wire_contract_for`, this file's premise has changed and someone
    should read it again rather than trusting a table that guards nothing."""
    import pathlib

    invariants = pathlib.Path("src/deepreason/invariants.py").read_text()
    manifest = pathlib.Path("src/deepreason/run_manifest.py").read_text()
    assert "wire_contract_for(" in invariants
    assert "wire_contract_for(" in manifest
    assert ".contract_id" in invariants and ".contract_id" in manifest


def test_this_tranche_opens_neither_frozen_caller():
    """§17.9's disposal, as a check rather than a promise: form selection goes
    through the dispatch site, so neither file is edited.

    Both ends are pinned. Against the WORKING TREE this asserted its claim only
    until the seat-shell tranche merged, after which it read every later
    tranche's diff as that tranche's and turned red on the first granted
    contact anywhere in the five files -- which is a claim it has no way to
    evaluate. `643dd8ea1` is that tranche's last commit, so the range is the
    diff the docstring is actually about, and the check now re-derives it
    forever instead of decaying into a permanent bar on five files that grants
    exist to open (re-aimed 2026-09-04,
    experiments/2026-09-04-defect-dead-seat-retirement/)."""
    import subprocess

    changed = subprocess.run(
        ["git", "diff", "--name-only", "e91f4fcc3", "643dd8ea1", "--", "src/"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    forbidden = {
        "src/deepreason/invariants.py",
        "src/deepreason/run_manifest.py",
        "src/deepreason/qualification.py",
        "src/deepreason/cli/doctor.py",
        "src/deepreason/verification/report.py",
    }
    assert not (set(changed) & forbidden), sorted(set(changed) & forbidden)
