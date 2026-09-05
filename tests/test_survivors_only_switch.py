"""`--survivors-only` on the two root-consuming instruments (R7/R8, 2026-09-04).

The progress law makes "survivors harder to vary" the success criterion, and
neither instrument could express it: both measured every admitted conjecture,
survivor and untested alike. The switch restricts them to the artifacts
`DR-CON-evidence-states` calls SUPPORTED.

R8 is the harder half — "no default behaviour of either instrument changes" —
because both instruments carry committed numbers that other tranches cite. The
default path is therefore pinned against a capture taken BEFORE the switch
existed (`experiments/2026-09-04-change-evidence-states/proof/
instruments_before.txt`, committed), not against the instrument's current self.

A note on the instrument the request NAMED and this file does not touch.
`experiments/2026-08-28-diversity-generation/analyse.py` is the other candidate
for "the diversity instrument": `analyse_form_arms.py` delegates M1/M2/M3 to
it. It reads `raw/<arm>/<question>/r<rep>/*.json` — direct provider calls — and
never opens a run root, so it holds no artifact that could HAVE an evidence
state and the switch would be inert in it. The switch went to the instrument it
could actually reach; the reasoning is in SPEC.md A3.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
TRANCHE = REPO / "experiments/2026-09-04-change-evidence-states"
BEFORE = TRANCHE / "proof/instruments_before.txt"
FORM_ARMS = REPO / "experiments/2026-09-03-change-conjecturer-pluggable-interface/analyse_form_arms.py"
DIVERSITY = REPO / "experiments/2026-09-03-change-provenance-history-channel/measure_diversity_per_problem.py"
ROOT = "experiments/2026-09-02-live-p-a2-corrected/run"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args], cwd=REPO, capture_output=True, text=True, timeout=900
    )


def _captured_block(title: str) -> str:
    """One instrument's recorded default output, from the committed capture."""

    text = BEFORE.read_text()
    marker = f"--- {title} ---\n"
    assert marker in text, (title, "no such block in the before-capture")
    body = text.split(marker, 1)[1]
    for terminator in ("\n--- ", "\nrc="):
        if terminator in body:
            body = body.split(terminator, 1)[0]
    return body.strip("\n")


def test_the_before_capture_is_committed_evidence():
    """Durable-evidence rule 1: a capture that is not committed dies with the
    session and takes this file's whole meaning with it."""

    listed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(BEFORE.relative_to(REPO))],
        cwd=REPO, capture_output=True,
    )
    assert listed.returncode == 0, BEFORE


# --- R8: the default path did not move ------------------------------------ #


def test_form_arms_default_output_is_byte_identical_to_the_before_capture():
    result = _run(str(FORM_ARMS), "--roots", ROOT)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip("\n") == _captured_block("analyse_form_arms.py --roots <p-a2>")


def test_form_arms_self_test_and_no_roots_paths_did_not_move():
    assert _run(str(FORM_ARMS), "--self-test").stdout.strip() == "ok"
    empty = _run(str(FORM_ARMS))
    assert empty.returncode == 1
    assert "STEP 1 has not run" in empty.stderr


def test_diversity_default_output_is_byte_identical_to_the_before_capture():
    result = _run(str(DIVERSITY), ROOT)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip("\n") == _captured_block(
        "measure_diversity_per_problem.py <p-a2>"
    )


# --- R7: the switch restricts to SUPPORTED -------------------------------- #


def _supported_ids() -> set[str]:
    from deepreason.harness import Harness
    from deepreason.views.evidence_states import EvidenceState, evidence_states

    readings = evidence_states(Harness(REPO / ROOT, read_only=True))
    return {aid for aid, r in readings.items() if r is EvidenceState.SUPPORTED}


def test_form_arms_survivors_only_counts_exactly_the_supported_artifacts():
    expected = len(_supported_ids())
    assert expected > 0, "the fixture root must actually carry survivors"
    result = _run(str(FORM_ARMS), "--roots", ROOT, "--survivors-only")
    assert result.returncode == 0, result.stderr
    assert f"survivors-only: {expected} artifacts" in result.stdout
    assert f"{ROOT}: {expected}" in result.stdout


def test_diversity_survivors_only_measures_fewer_conjectures_than_the_default():
    """The switch must actually restrict. An implementation that accepted the
    flag and measured the whole pool would report the wrong number under the
    right name, which is worse than not having the flag."""

    default = _run(str(DIVERSITY), ROOT).stdout
    filtered = _run(str(DIVERSITY), ROOT, "--survivors-only").stdout
    assert "[--survivors-only]" in filtered
    assert "[--survivors-only]" not in default

    def seed_count(text: str) -> int:
        line = next(l for l in text.splitlines() if "SEED PROBLEM" in l)
        return int(line.rsplit("(n=", 1)[1].split(")", 1)[0])

    assert seed_count(filtered) < seed_count(default)


def test_diversity_survivors_only_keeps_only_supported_artifacts():
    """Behavioural, not textual: the rows the filter keeps ARE the reader's
    SUPPORTED set, so a filter that drifted to some other criterion reddens."""

    import importlib.util

    spec = importlib.util.spec_from_file_location("diversity_instrument", DIVERSITY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    root = REPO / ROOT
    rows = module.conjectures(root)
    kept = module.survivors_only(root, rows)
    supported = _supported_ids()

    assert kept, "the fixture root must carry at least one surviving conjecture"
    assert {row["id"] for row in kept} <= supported
    assert len(kept) < len(rows)


@pytest.mark.parametrize("script", [FORM_ARMS, DIVERSITY])
def test_the_switch_is_off_by_default(script):
    """R8 as a property of the parser, not of one run: the flag defaults to
    False, so no caller gets the filter without asking for it."""

    source = script.read_text()
    assert '"--survivors-only", action="store_true"' in source
    assert "default=True" not in source
