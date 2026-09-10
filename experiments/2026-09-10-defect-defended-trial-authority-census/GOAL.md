# Goal: a completed run that carried defended trials reports `valid: true` from `deepreason results --verify`

Class: defect

Observed: On the committed live root
`experiments/2026-09-09-fix-solo-criticism-authority/runs/home-solo/runs/run-02818acc38961781e2e820d0d6b591fb`
(22 trials) `verify_root` reports ZERO integrity/replay violations while the
verification report reports 76 security findings — 75 of them
`transaction-authority :: unknown v6 task kind: defended_trial_step` — so
`VerificationReportV2.valid` (integrity AND security) is `false` on a
replay-clean, completed run. The identical finding appears at 3 on a stub root
built on the PRE-EXISTING `ENGAGED_CRITICISM_AUTHORITY=defended_trial` road,
which proves the gap predates the 2026-09-09 solo tranche. Evidence:
`experiments/2026-09-09-fix-solo-criticism-authority/proof/LIVE_VERIFICATION_CHANNELS.txt`
and that tranche's `PARKED.md` P4.

Success criterion (machine-decidable):

    # 1. the stub root flips
    python experiments/2026-09-10-defect-defended-trial-authority-census/proof/stub_defended_trial_root.py
      -> before fix: valid False, transaction-authority findings > 0,
                     unknown kinds {'defended_trial_step': N}
      -> after  fix: valid True,  transaction-authority findings == 0

    # 2. a FORGED trial step is still reported (mutation proof)
    python -m pytest tests/test_defended_trial_transaction_authority.py -q
      -> passed; the forged-step test FAILS if the new branch is replaced by
         an unconditional accept

    # 3. the two committed roots carrying defended trials re-verify unedited
    python experiments/2026-09-10-defect-defended-trial-authority-census/proof/recheck_committed_roots.py
      -> each root's stored verdict printed beside its recomputed one;
         no root moves from clean to dirty

    # 4. the gate
    python -m pytest tests/ -q -n 4
      -> 0 failed

In scope (max 3):
  - `src/deepreason/verification/report.py` (`_transaction_findings`) — FROZEN
    SURFACE 3; no code until the operator grants contact
  - `src/deepreason/workflow/models.py` (read only — `DEFENDED_TRIAL_STEP`)
  - `src/deepreason/informal/trial.py` (read only — what actually prepares the
    transaction, and therefore what "authorised" must mean)

NOT in scope: the continuation gate itself. Today
`terminal.continuation_authority` is `true` and `record_security_violations` is
`[]` on a root the report calls invalid. This tranche STATES that disagreement
in VERIFY.md and does not change the gate; the open-work-order policy question
is parked elsewhere and stays parked. Also not in scope: any record format
change, any check-name change, `invariants.py`.

Budget: <=150 changed lines, 1 commit for the fix (plus phase-boundary artifact
commits), ~4 hours.

Stop conditions inherited from orchestrator: yes. Additional hard stop declared
by the executor brief: STOP AT FIX.md with a frozen-surface grant request in the
standard stop format; do not implement until the operator's words arrive.

## Map preflight (DR- ids resolved before any design)

Read in this order, per `docs/map/INDEX.md`'s one ordering rule:

  - `DR-INV-frozen-surfaces` — surface 3 is `invariants.py` AND
    `verification/`. Target file is inside it. Read in full BEFORE designing.
  - `DR-SEAM-harness-x-verification` — the written seam nearest the target.
  - `DR-SEAM-periphery-x-verification`, `DR-SEAM-llm-x-verification` — the two
    other verification seams.
  - `DR-SUB-verification` — the owning subsystem (`verify_root`, the epistemic
    check report).
  - `DR-SUB-workflow` — the v6 transactional work lifecycle that writes the
    transactions being censused.
  - `DR-CON-authority` — who may change a Status, and the two authority
    vocabularies; "authorised" for a trial step has to be said in its terms.

  **workflow x verification has NO seam document and is absent from
  `INDEX.md`'s matrix entirely** — i.e. no measured `deepreason.*` import
  traffic between the two sides' declared `Owns:` files. The agreement this
  defect breaks is exactly that unwritten one: `verification/report.py`
  censuses task kinds that `workflow/models.py` declares. Per `INDEX.md`, an
  absent pair is not a pair that does not interact.

## Amendment, 2026-09-10 (same day, before any code) — criterion 1 sharpened

Found during dr-propose-fix and recorded rather than absorbed. The defect also
reaches the run's TERMINAL: `terminalize_text_run` asks the same reader for a
verification summary and freezes it into `run-result.json`, so a completed
defended-trial run stores `security_valid: false` about itself, which the
report then re-reports as a second security finding. Editing that stored
summary is forbidden — the record is law — so an already-committed completed
run cannot and must not flip to `valid: true`.

Criterion 1 therefore becomes:

    # 1a. a run COMPLETED on the fixed code -- the goal's headline
    python .../proof/stub_terminalized_root.py <tmpdir>
      -> before: valid false, security 4 (3 trial + 1 stored echo),
                 stored security_valid false, verify_root violations 0
      -> after:  valid true,  security 0, stored security_valid true,
                 verify_root violations 0

    # 1b. the cycle-only stub, unchanged as its own row
    python .../proof/stub_defended_trial_root.py <tmpdir>
      -> after: valid true, security 0

Criterion 3 (the committed roots) becomes: each root's
`transaction-authority` findings go to zero and exactly ONE security finding
remains — its own stored record of what the reader said at the time — so
`valid` stays `false` on all five, honestly. No root is edited.
