# Checklist — re-plan after VALIDATION.md FAIL

Scope: only the three items VALIDATION.md failed, under the operator's
ruling (REQUEST.md R12a/R12b, R15a, R1a). Nothing else in the tranche is
reopened.

- [x] **C1 — Park the successor-manifest digest materialization (R12b).**
  Done-criterion: `PARKED.md` exists with the parked item, its structural
  reason, and what would justify unparking it.
  Output: `experiments/2026-07-30-change-amendment-epochs/PARKED.md`,
  section "P1".

- [x] **C2 — Amend the spec's R12 mechanism clause (R12a).**
  Edit `docs/proposals/AMENDMENT_EPOCHS.md` so the "Manifest epoch
  record" bullet states the record-carried design and keeps the outcome
  clause (no requalify) as the requirement; rewrite "As implemented" so
  it no longer frames this as a departure while keeping the structural
  reasoning.
  Done-criterion: the design section says the manifest is copied verbatim
  and the successor run-input is named by the record; the words
  "departure"/"departs" no longer appear; `git diff` pasted.

- [x] **C3 — Correct the spec's `--root` usage line (R1a).**
  Done-criterion: the usage block in `docs/proposals/AMENDMENT_EPOCHS.md`
  shows `deepreason --root ROOT amend ...` and the `continue` line shows
  the real flags; `deepreason --root <root> amend --help` still works.

- [x] **C4 — Implement bounded supersession of a staged epoch (R15a).**
  In `src/deepreason/amendment/apply.py`: when a staged-but-uncommitted
  epoch has applied no ledger events (`fence_seq == harness._next_seq`),
  a different amendment supersedes it — discard the staged epoch
  directory and stage fresh. When events exist, keep the fail-closed
  refusal and make the refusal name the operator's real route (complete
  this epoch identically, then amend again for the next one).
  Done-criterion: two new regression tests pass — supersession when
  nothing was applied, typed refusal naming the route when something
  was; existing crash-recovery test still passes.

- [x] **C5 — Full gate.**
  Done-criterion: `pytest tests/ -q -n 4` ends `0 failed`, pasted.

- [x] **C6 — Re-validate.**
  Done-criterion: `VALIDATION.md` rewritten with every acceptance check
  re-run, verdict PASS.

## Executed outputs

- **C1** — `PARKED.md` written, section "P1 — Materialize a distinct
  successor manifest digest per amendment epoch".
- **C2** — `docs/proposals/AMENDMENT_EPOCHS.md`: the "Manifest epoch
  record" bullet now states the manifest is copied verbatim and the
  successor run-input is named by the record; "As implemented" rewritten
  without the departure framing.

        $ grep -ni "departure\|departs" docs/proposals/AMENDMENT_EPOCHS.md
        rc=1  (no matches)

- **C3** — usage block corrected:

        deepreason --root ROOT amend [--attach FILE ...] \
            [--reshape-question "TEXT"] [--allow-partial]
        deepreason --root ROOT continue --budget cycles=N \
            [--token-budget N|unlimited]

- **C4** — `_discard_staged_epoch` plus the two-shape recovery branch in
  `_amend_locked`; refusal message now names the route.

        tests/test_amendment_epochs.py .............     [100%]
        15 passed in 60.66s (0:01:00)

  including the two new cases
  `test_staged_epoch_that_never_reached_the_ledger_is_superseded` and
  `test_staged_epoch_that_applied_events_refuses_and_names_the_route`,
  with `test_partial_amendment_refuses_continuation_and_completes_on_rerun`
  still passing.
- **C5** — full gate:

        3128 passed, 7 skipped in 488.53s (0:08:08)

- **C6** — `VALIDATION.md` rewritten as a second pass; all 16 acceptance
  checks re-run against the amended spec and amended code; verdict PASS.
  The first pass's FAIL is preserved in "First-pass verdict (superseded)".

## Re-plan 2 — post-delivery coverage gaps (R26, R27)

- [x] **C7 — Make the chain/epoch detectors fire (gap 1).**
  Done-criterion: a test per `verify_root` amendment failure branch and
  per record-model rejection rule, each asserting the specific finding.
  Output: `tests/test_amendment_chain_integrity.py`, 28 cases; amendment
  models coverage 84% -> 100%.

- [x] **C8 — Amendment beside a bridge episode (gap 2).**
  Done-criterion: one root carrying both a commitment-bound bridge
  episode and an amendment past the same horizon, with terminal authority
  and `verify_root` still valid; plus a negative case proving the
  amendment authorization did not become a general licence.

- [x] **C9 — Three or more chained epochs (gap 3).**
  Done-criterion: three epochs chained, four dossiers bound, four
  questions on the frontier, `verify_root` clean, and a corrupted MIDDLE
  epoch still detected.

- [x] **C10 — Delete the dead exports.**
  Done-criterion: `epoch_fences`, `epoch_for_event_seq`,
  `current_manifest`, `current_run_input`, `current_dossier` removed;
  `epoch_manifest_path` made private. Public surface 23 -> 18 names, all
  with a caller or a test.

- [x] **C11 — Live run (R27): attempted, blocked on the credential.**
  Done-criterion: a typed determination either way, with evidence.
  Outcome: BLOCKED. See VALIDATION.md "Live run attempt".
