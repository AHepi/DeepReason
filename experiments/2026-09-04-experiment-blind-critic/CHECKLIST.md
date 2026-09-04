# Checklist for: does a blind critic perform better?
State: next=12 blockers=none
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map ids this plan was scoped from (seam read before the subsystems):
`DR-INV-frozen-surfaces`, `DR-SEAM-packs-and-token-economy-x-rules`,
`DR-INV-seat-section-plugins`, `DR-REC-add-a-section-plugin`,
`DR-CON-criticism-source`, `DR-CON-warrants-and-attacks`,
`DR-CON-discharge-channel`, `DR-CON-packs-and-token-economy`,
`DR-INV-render-layout`.

No map document changes in this tranche: nothing under `src/` moves, so
no `Verified-at:` stamp may advance and no `Traps` entry is earned. That
is a decision, recorded here so a later reader does not read the absence
as an omission.

**Standing done-criterion on EVERY step (S0):**
`git status --porcelain src/ | wc -l` -> `0`

---

- [x] 1. (S5, A9, A11) Write `select_targets.py`: the deterministic target selector over
      the roots M1 names, and run it to produce `SELECTION.json`.
      done-when: `python select_targets.py --write` prints `120 selected`
      and re-running prints an identical `SELECTION.sha256`.
      DONE:
          120 selected
          eligible seen: 137
          with recorded history: 120
          SELECTION.sha256: b07661e35069277c476a994420af14a5eec629e29e9be9f2a0978a7e60ce4e53
          --- rerun ---
          120 selected
          eligible seen: 137
          with recorded history: 120
          SELECTION.sha256: b07661e35069277c476a994420af14a5eec629e29e9be9f2a0978a7e60ce4e53
          all have history: True
          planted/clean with history: 60 60
          schools: school-0 33, school-1 28, school-2 27, school-3 32
      Three findings during this step, all in SPEC Amendment 1: A9 (the
      eligibility rule gained a history clause, or F2 would have run at
      70 observations per level against the 99 it needs), A10 (no
      rebuttal exists in any source root, so F2 is prior-objection
      exposure), A11 (the file was renamed off the stdlib's `select`).

- [x] 2. (S5, S6) [COMMIT] Write `plant.py`: the six mutators, the
      single-difference assertion, and `DEFECT_KEY.json`.
      done-when: `python plant.py --write` prints `60 pairs, 10 per
      class` and `assert_single_difference` passes on all 60; a second
      run reproduces `DEFECT_KEY.json` byte-for-byte.
      DONE:
          60 pairs, 10 per class
            unsupported-comparison: 10
            causal-non-sequitur: 10
            evidence-misquotation: 10
            circular-mechanism: 10
            scope-contradiction: 10
            vacuous-forbidden-case: 10
          DEFECT_KEY.sha256: b1813c10848092fe849a53a611146bf86a6c609e1eccbdbd6671af82d95b4b74
          --- rerun --- identical digest
          sha256sum DEFECT_KEY.json ->
            b1813c10848092fe849a53a611146bf86a6c609e1eccbdbd6671af82d95b4b74

- [x] 3. (S1, S2, S3, S4) Write `cells.py`: the two operator plugins and
      the four layout registrations, plus the census renderer.
      done-when: `python cells.py --census` prints a 13-row table for
      `seat-pack.critic.legacy-v0`, `default == C00: True`, `all four
      distinct: True`, `src/ bytes unchanged: True`.
      DONE:
          entries: 13   (the full census table is in PREREG.md, step 4)
          default == C00: True
            C00  bytes=1338  provenance=False  history=False
            C10  bytes=1533  provenance=True   history=False
            C01  bytes=1600  provenance=False  history=True
            C11  bytes=1795  provenance=True   history=True
          all four distinct: True
          src/ bytes unchanged: True
      One correction inside the step: the shipped plugins seed lazily, so
      `ensure_seeded()` must run before a cell layout can copy the
      shipped entries. Fixed in `cells.py`; nothing under `src/` moved.

- [x] 4. (S1, S9, S13, S14, S15, S19) [COMMIT] Write `PREREG.md`: the
      census, the four cells, the six defect classes, M1-M5 with their
      exact definitions and detectors, the five re-fixed sharpness
      criteria, the sample-size arithmetic, the verdict rule, the
      saturation rules, and "What this tranche is allowed to conclude".
      done-when: `PREREG.md` exists and contains the strings
      `M1 sensitivity`, `M5 sharpness`, `BLIND BETTER`,
      `INFORMED BETTER`, `INCONCLUSIVE`, `98.11`.
      DONE (occurrences):
          M1 sensitivity     1
          M5 sharpness       1
          BLIND BETTER       1
          INFORMED BETTER    1
          INCONCLUSIVE       3
          98.11              1

- [x] 5. (S7) [COMMIT] SEAL. Write `PREREG.sha256` and
      `DEFECT_KEY.sha256`; commit and push BOTH before any experimental
      provider call.
      done-when: `sha256sum -c PREREG.sha256 DEFECT_KEY.sha256` prints
      two `OK` lines, and `git log --oneline -1` shows this commit
      pushed. THIS COMMIT IS THE FREEZE LINE.
      DONE:
          PREREG.md: OK
          DEFECT_KEY.json: OK
          3fbf7731ff93fa491fe9f6176a8a2b0cfe2349eeba0dd31df18a8a3399a2a7df  PREREG.md
          b1813c10848092fe849a53a611146bf86a6c609e1eccbdbd6671af82d95b4b74  DEFECT_KEY.json
          b07661e35069277c476a994420af14a5eec629e29e9be9f2a0978a7e60ce4e53  SELECTION.json
          ls raw -> No such file or directory   (nothing measured yet)

- [x] 6. (S16, R19) Green soak on the launch config.
      done-when: `python -u scripts/cycle_soak.py --case <case>` exits 0
      and its tail is pasted into `SOAK.txt`.
      DONE:
          --case epoch3      rc=0  [soak] exit 0 (clean)
          --case reach-rich  rc=0  [soak] exit 0 (clean)
          --case pc1         rc=1  V6_SIMULATION_TOOLCHAIN_REQUIRED  -> PARKED
          --case pc2         rc=1  same                              -> PARKED
      epoch3 is solo glm-5.2 across all eleven roles, which is this
      tranche's critic seat model. The two red cases are a pre-existing
      manifest-compile failure this tranche did not cause and does not
      fix; they go to PARKED.md at step 13.

- [x] 7. (S16, A6) Write `bench.py` and prove it end-to-end on FOUR
      calls (one target, four cells) before the full launch.
      done-when: `python bench.py --smoke` writes four run roots, each
      with a parsed `ArgumentativeCriticOutput`, and prints
      `smoke: 4/4 parsed`.
      DONE:
          [bench] complete: 4 calls, 0 failed
          smoke: 4/4 parsed
          C00 attempts 1 attack True caselen  856 tok 2628 att 0
          C10 attempts 1 attack True caselen  856 tok 2024 att 0
          C01 attempts 1 attack True caselen 1705 tok 2763 att 0
          C11 attempts 1 attack True caselen 1225 tok 2425 att 0
          distinct packs: 4   distinct cases: 4
          root footprint 52K -> ~25MB for the full 480
      Two corrections inside the step, both in how the reply is READ, not
      in what the harness does: the filled form lives in the `raw_ref`
      blob each `attempt_trace` entry names, not inline in the event; and
      the reply arrives fenced in a markdown code block often enough that
      the measurement now parses it with the adapter's OWN normaliser
      rather than a hand-rolled one, so it cannot read a different object
      than the run acted on.

- [x] 8. (S8, S16) [COMMIT] Launch the full bench detached, snapshot
      loop armed: 120 targets x 4 cells = 480 calls, <=3 concurrent.
      done-when: `raw/driver.log` shows `launched`, the monitor shows
      progress, and on completion `raw/calls.jsonl` holds 480 rows.
      DONE:
          [bench] complete: 480 calls, 0 failed
          rows 480  failed 0  unparseable forms 0
          per cell  C00 120  C10 120  C01 120  C11 120
          attack=true  C00 120  C10 120  C01 120  C11 120
          att edges    (none in any cell)
          raw/ 29M
      TWO PRE-REGISTERED RULES FIRE ON THESE COUNTS, before any measure
      is computed:
        * M2 is SATURATED. The critic attacked 120 of 120 targets in
          every cell, sound and planted alike, so the false-attack rate
          is 1.000 everywhere. PREREG section 6's saturation rule fires:
          M2 is NON-DISCRIMINATING, and the verdict's M2 clause is
          carried explicitly rather than dropped.
        * M3 is on its FLOOR. Zero attack edges in any cell, exactly as
          PREREG section 6 predicted under observe_only authority. M3 is
          reported and decides nothing.
      Both were written down before the first call. Neither is a
      surprise, and neither is read as a result.

- [x] 9. (S8, S10, S11, S12) [COMMIT] Write `measure.py` and compute
      M1-secondary, M2, M3, M4 from the record alone.
      done-when: `M2.json`, `M3.json`, `M4.json` exist; `M3.json`
      satisfies `attack_true >= att_edges` in every cell; `measure.py`
      contains no read of a self-reported score field.
      DONE:
          no self-reported field is read: OK
          (the criterion is checked on FIELD READS, by AST, not on the
           word anywhere in the file -- the rule stated in the docstring
           was breaking its own grep. Corrected inside the step.)

          M2 false attack (clean targets)
            C00  60/60 = 1.000   C10  60/60 = 1.000
            C01  60/60 = 1.000   C11  60/60 = 1.000   SATURATED: True

          M3 warrant rate (denominator = every criticism attempt)
            every cell: 120 calls, attack=true 120, att edges 0, rate 0.000
            attack_true >= att_edges holds in all four cells

          M4 spend per criticism (mean tokens)
            C00 prompt 1187.5 completion 1504.7 total 2692.1
            C10 prompt 1230.5 completion 1397.8 total 2628.3
            C01 prompt 1478.3 completion 1588.0 total 3066.3
            C11 prompt 1526.7 completion 1620.1 total 3146.7

          M1 SECONDARY (lexical) sensitivity, 60 planted per cell
            C00 39/60 = 0.650   C10 43/60 = 0.717
            C01 35/60 = 0.583   C11 31/60 = 0.517
            F1 provenance: omitted 0.617 present 0.617 d1 +0.0000
                           p 1.0      McNemar b/c 13/13 p 0.845
            F2 history:    omitted 0.683 present 0.550 d1 +0.1333
                           p 0.03365  McNemar b/c 25/9  p 0.0101

- [x] 10. (S9) [COMMIT] Run the blind three-grader naming panel for
      M1-primary. Grader rows carry no cell field.
      done-when: `M1.json` exists with per-cell numerator/denominator
      for both detectors and their agreement; the assertion on grader
      row key sets passes.
      DONE:
          blind rows: 240  keys: ['bid','clean','criticism','note','planted']
            (the blinding assertion is on the KEY SET; cell, school, arm
             and layout are ABSENT from the row, not blanked)
          720 grader calls; graded bids 240 of 240; unanimous 239

          M1 PRIMARY (blind three-grader panel), 60 planted per cell
            C00 33/60 = 0.550   C10 32/60 = 0.533
            C01 28/60 = 0.467   C11 28/60 = 0.467
            F1 provenance: omitted 0.508 present 0.500 d1 +0.0083
                           p 0.897   McNemar b/c 9/8  p 1.0
            F2 history:    omitted 0.542 present 0.467 d1 +0.0750
                           p 0.245   McNemar b/c 14/5 p 0.0665

          detector agreement 213/240 = 0.887 (disagreement 0.113;
            PREREG's falsifier fires above 0.25 -- it does not fire)

- [x] 11. (S13) [COMMIT] Run the blind three-judge sharpness panel.
      `blind/keymap.json` lands in the SAME commit as
      `blind/scores.json`, never before.
      done-when: `M5.json` exists with median-of-three totals per bid
      and the contested flag; `blind/criticisms.jsonl` rows carry
      exactly `{bid, target, criticism}`.
      DONE:
          blind rows: 479  keys: ['bid','criticism','target']
          1437 judge calls; scored bids 479 of 479
          contested 0; self-identifying rows 0

          M5 median-of-three totals, out of 15
            C00 n=120 median 14.0 mean 14.400
            C10 n=120 median 14.0 mean 14.358
            C01 n=119 median 14.0 mean 14.370
            C11 n=120 median 14.0 mean 14.350

          M5 IS A FAILED INSTRUMENT, not a null result. The totals span
          10 to 15 with 1404 of 1436 at 14 or 15, and the reason is a
          hard ceiling in the rubric itself:
            c1 specific       3/3 on ALL 1436 judgements
            c5 non-evasion    3/3 on ALL 1436 judgements
            c2 fault is real  3/3 on 1427 of 1436
            c3 case is made   3/3 on 1430 of 1436
            c4 answerable     the ONLY criterion that moves (2 or 3)
          Four of five criteria cannot fail against this model's
          criticism, so M5 cannot separate the cells and reports its own
          definition back. Recorded as an instrument failure by the same
          standard PARKED P7 CORRECTED set. M5 does not enter either
          verdict, which PREREG section 8 already fixed in advance.

- [ ] 12. (S14, S17, S21) [COMMIT] Write `RESULTS.md`: one verdict per
      factor, the numbers beside it, and the residue.
      done-when: `RESULTS.md` contains exactly two verdict lines, each
      one of BLIND BETTER / INFORMED BETTER / INCONCLUSIVE, and a
      `## Residue` section.

- [ ] 13. (all) Write `PARKED.md` for everything noticed and not fixed
      (at minimum: the provider's rejection of `"reasoning":"none"`,
      M5's finding; and the missing no-harness baseline arm).
      done-when: `PARKED.md` exists and every entry carries a
      ready-to-send prompt.

- [ ] 14. (S18) Targeted gate ring: the tests that pin the shipped
      critic brief and the seat-section interface.
      done-when: `python -m pytest tests/test_crit_pack_legacy_golden.py
      tests/test_seat_section_architecture.py tests/test_seat_pack_layout.py
      tests/test_seat_section_registry.py -q` -> `0 failed` (paste it).

- [ ] 15. (all) Map check: `python tools/docs_verify.py`
      done-when: 0 failed, and `--audit` reports 0 new findings.

- [ ] 16. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends `N passed, 0 failed` (paste it).

- [ ] 17. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND the branch head
      is on origin AND `git diff --stat 0f6bf2c854 -- src/ | wc -l` is
      `0`.
