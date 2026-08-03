# Goal: decide and correct the `attached-evidence` verdict on run-0a3e93d6 without moving any other recorded root

Class: defect

Observed: the triage run of the 2026-08-02 stress triplet reached
`state=completed` and then failed its own integrity check. Two independent
instruments agree, which is why this is a defect and not an instrument
artefact:

- `experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc/REPLAY_VALIDATION.json`
  → `valid: false`, exactly one violation:
  `attached-evidence` / "bound source
  `src-56d86e9b3a1d59413e02c76cdf675f84f6288fa7` lacks one
  reliability-dependent candidate evidence artifact".
- the ladder's own exit contract: `reason_rc=5` (`triage.log:13`), produced by
  `run_result_exit_code` (`src/deepreason/application/models.py:1258`, the
  `return 5` branch at :1269) on `verification.integrity_valid is False`.
- the ladder audit `triage-audit.json` reproduces the same single violation
  under `replay_violations`.

A run that completes must not write a record that its own replay validation
calls invalid. Exactly one of two things is therefore untrue, and the record
alone does not yet say which:

- **W** — the write path bound a source without attaching the
  reliability-dependent candidate evidence artifact the binding requires. The
  finding is correct; the committed root is a true record of a real breach and
  must stay invalid forever.
- **R** — the reader over-demands: `verify_root`'s `attached-evidence` check
  requires an artifact that this shape of binding is not obliged to carry. The
  finding is spurious and the reader is what gets fixed, so that this root and
  every root like it verify as they should.

Naming which of W or R holds is `dr-diagnose`'s job. This goal is written so it
is decidable under either.

Success criterion (machine-decidable):

    # 1. the disposition is pinned by a regression test naming this run
    python -m pytest tests/ -k attached_evidence -q
    → passes, and the test asserts the outcome DIAGNOSIS.md selected:
       under W: verify_root on the committed root still reports exactly the
                one `attached-evidence` violation (the evidence is preserved),
                AND a new test proves the write path can no longer emit a
                bound source without its required artifact;
       under R: verify_root(<committed root>)["violations"] == []

    # 2. the full gate
    python -m pytest tests/ -q -n 4
    → 0 failed

    # 3. no other recorded root moved (DR-INV-frozen-surfaces, instrument 2)
    python tools/root_sweep.py <after.txt>
    → diffed against the 45-root baseline in
      experiments/2026-08-02-stress-triplet/RESULTS.md (sweep appendix):
      no root's `valid`, `att` or `epistemic_checks_passed` changes, except
      run-0a3e93d6, whose movement is permitted ONLY under R and ONLY if
      FIX.md predicted it in advance.

In scope (max 3):

1. `src/deepreason/invariants.py` — the `attached-evidence` finding
   (DR-SUB-verification, DR-SEAM-harness-x-verification). A frozen surface:
   READERS may be fixed, FORMATS may not. The check NAME may not be renamed —
   it is compared against recorded roots.
2. the writer that emits the source binding and its candidate evidence
   artifacts. `dr-diagnose` names the module from the record; the candidates
   the map offers are DR-SUB-capabilities (research controller, which is what
   `RESEARCH_SOURCE_AUDIT.md` projects) and DR-SUB-application.
3. `tests/` — the regression, whose docstring names this run per CLAUDE.md.

Documentation (operator-granted scope addition, 2026-08-03, verbatim: "take
this opportunity to fix documentation as you go"): map documents this tranche
actually touches move in the SAME commit as the code, per `SCHEMA.md` and
`REC-change-a-seam.md`. Concretely that is `DR-SUB-verification` and
`DR-SEAM-harness-x-verification`, plus a Traps entry for whichever of W or R
turns out to hold. Documentation defects found OUTSIDE those documents go to
PARKED.md — the grant widens what this tranche may repair, not what it must
survey.

NOT in scope:

- The `replay_valid: null` probe-rule bug in the ladder audits
  (`ladder_common.sh`), even though it is visible in the very same
  `triage-audit.json` this goal quotes. Handover item 4, one commit of its own.
- The 11-vs-14 census delta in `INV-frozen-surfaces.md` (handover item 2).
  Tempting, because it is a documentation defect in a document this tranche
  reads — but it belongs to a different instrument question and has its own
  entry. PARKED.
- Re-running the live triage ladder. The committed root is the repro; the
  `env` credential files did not survive the container rollback.

Budget: <=150 changed lines, 1 commit, ~3 hours.

Stop conditions inherited from orchestrator: yes. Note that scope item 1 is a
frozen surface, so the orchestrator's "fix requires touching frozen-record
semantics" stop applies the moment the fix would change a finding NAME, a
finding SHAPE, or any recorded root's `valid` other than run-0a3e93d6.
