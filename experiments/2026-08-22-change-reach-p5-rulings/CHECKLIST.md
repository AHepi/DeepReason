# Checklist for: codify two operator rulings on reach semantics (P5-reach)
State: next=2 blockers=none
Map ids (from REQUEST.md's preflight, unchanged): DR-INV-frozen-surfaces,
DR-SEAM-evaluation-x-rules (read before the subsystems; its shared
`_substantive` surface is OUT of scope), DR-SUB-evaluation (the covering
document; takes the Traps entry and the exit-documentation check),
DR-CON-warrants-and-attacks (consulted only).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

- [x] 1. (S1, S3) Write BOTH new tests in tests/test_reflexive_discipline.py,
      against the UNCHANGED tree: test_an_empty_own_battery_grounds_no_reach
      (currently must FAIL — the behaviour it demands does not exist yet) and
      test_coverage_exactly_at_the_floor_is_a_full_hit (currently must PASS —
      it pins behaviour that already holds and must keep holding).
      done-when: python -m pytest "tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach" "tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit" -q
      -> exactly 1 failed, 1 passed (the empty-battery one RED, the floor pin
      GREEN) — pasted

      PROOF (unchanged tree, before any src/ edit):
      $ python -m pytest "tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach" \
          "tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit" -q
      >       assert reach_sweep(empty) == []
      E       AssertionError: assert [('47b8d9f1d4...', 'foreign')] == []
      E         Left contains one more item: ('47b8d9f1d4f30c99192320338945306...', 'foreign')
      tests/test_reflexive_discipline.py:425: AssertionError
      FAILED tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach
      1 failed, 1 passed in 0.19s

      The RED line is the whole point of RULING 1: today an artifact with
      carried == [] reaches. The floor pin is GREEN before anything moves,
      so RULING 2 is pinned as a PRESERVED property, not a manufactured one.

- [ ] 2. (S1, S3) [COMMIT] Commit the two tests alone, red-then-green order
      preserved in history.
      done-when: git status --porcelain is empty AND git log -1 --stat names
      only tests/test_reflexive_discipline.py

- [ ] 3. (S1, S4) Add the E0 guard to reach_sweep's inner loop as its FIRST
      branch, with the comment stating why it is deliberately loop-invariant
      (it must not be hoisted above the clear-to-zero accounting), and add the
      inline deliberate-`<` comment at the coverage comparison.
      done-when: python -m pytest "tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach" "tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit" "tests/test_review_fixes.py::test_reach_clears_to_zero" -q
      -> 3 passed

- [ ] 4. (S2, S4) Rewrite the reach.py module docstring: SIX -> SEVEN exits,
      a new FIRST bullet "E0 empty-own-battery" carrying the ruling and its
      basis, and the one-line deliberate-floor note in the E5 bullet. Both
      cite this tranche.
      done-when: python -c "import pathlib; d=pathlib.Path('src/deepreason/measures/reach.py').read_text(); assert 'SEVEN exits' in d and 'E0 empty-own-battery' in d and d.count('2026-08-22-change-reach-p5-rulings') >= 2"
      -> exit 0

- [ ] 5. (S2) Update docs/map/SUB-evaluation.md's exit-documentation trap: its
      prose gains E0, and its `check:` asserts len(conts) == 5 and all SEVEN
      labels. Run the amended check standalone.
      done-when: the amended check command copied out of SUB-evaluation.md and
      run in a shell -> exit 0 (pasted)

- [ ] 6. (S2) Prove the amended check still bites in BOTH directions: with the
      E0 guard removed the count is 4 and the check must FAIL; with the E0
      label removed from the docstring it must FAIL. Restore after each.
      done-when: two pasted runs, each exit 1, and a third run after restore
      -> exit 0

- [ ] 7. (S5) Update the four fixtures SPEC.md M2 names, giving each reaching
      artifact the battery compile_interface would pin. No assertion touched.
      done-when: python -m pytest tests/test_reflexive_discipline.py tests/test_review_fixes.py tests/test_prose_refutation_boundaries.py -q
      -> 0 failed (pasted) AND git diff -- tests/ | grep -E "^-[[:space:]]+assert" is empty

- [ ] 8. (S6) Add the new Traps entry to docs/map/SUB-evaluation.md for this
      ruling pair (both rulings, their authority date, this tranche id) with a
      `check:` that runs the two new tests and asserts the E0 label is in the
      docstring; and extend the "Where to change what" coverage-threshold row
      with the floor pin test. Advance Verified-at only if that document's
      checks are actually re-run in this step.
      done-when: python tools/docs_verify.py 2>&1 | tail -5 -> failures are
      exactly the 3 pre-existing shallow-clone ones named in REQUEST.md C9
      (pasted)

- [ ] 9. (S2, S6) Map link and audit gates.
      done-when: python tools/docs_verify.py --links -> 0 unresolved AND
      python tools/docs_verify.py --audit -> no NEW un-failable check (pasted)

- [ ] 10. (S1..S6) [COMMIT] Commit the rulings, their docstring, their check,
      their fixtures and their map together — R3 requires the new exit and its
      documentation in ONE commit, and the fixtures must land with the guard
      or the tree is red between commits.
      done-when: git status --porcelain is empty AND git log -1 --stat names
      src/deepreason/measures/reach.py, tests/test_reflexive_discipline.py,
      tests/test_review_fixes.py and docs/map/SUB-evaluation.md

- [ ] 11. (S9) Mutation proof, ruling 1: delete the E0 guard, run the pin,
      restore, re-run.
      done-when: two pasted runs — RED (1 failed) then GREEN (1 passed)

- [ ] 12. (S9) Mutation proof, ruling 2: break the floor the other way (make
      coverage exactly 0.5 provisional), run the pin, restore, re-run.
      done-when: two pasted runs — RED (1 failed) then GREEN (1 passed) AND
      git diff -- src/ is empty after restore

- [ ] 13. (S7) Add the E0 branch to rehearsal.py's own exit classifier, in the
      same position reach_sweep takes it, and update S2's `note` to record the
      ruling.
      done-when: python -c "import pathlib; s=pathlib.Path('experiments/2026-08-22-live-reach-rich-run/rehearsal.py').read_text(); assert 'E0 empty-own-battery' in s"
      -> exit 0

- [ ] 14. (S7) Re-run the rehearsal against the fixed tree and paste S2, S8a,
      S8c; copy the regenerated JSON into this tranche as
      rehearsal-after-p5-rulings.json.
      done-when: python experiments/2026-08-22-live-reach-rich-run/rehearsal.py
      -> S2 exit is the E0 label with 0 hits and 0 reach events, S8a exit is
      "HIT full", S8c exit is "E4 criterion-fail" (all three pasted)

- [ ] 15. (S8) Add the E0 branch and label to
      experiments/2026-08-21-measure-reach-firing/census.py (module docstring
      vocabulary + rederived_census counters), plus the one-line note that the
      committed census JSON predates E0.
      done-when: python -c "import pathlib; s=pathlib.Path('experiments/2026-08-21-measure-reach-firing/census.py').read_text(); assert 'E0 empty-own-battery' in s"
      -> exit 0 AND git diff --stat -- experiments/2026-08-21-measure-reach-firing/census.json experiments/2026-08-21-measure-reach-firing/census-verdicts.json is empty

- [ ] 16. (S7, S8) [COMMIT] Commit the two instruments and the pasted
      rehearsal evidence.
      done-when: git status --porcelain is empty AND git log -1 --stat names
      rehearsal.py, census.py and rehearsal-after-p5-rulings.json

- [ ] 17. (all) Wheel smokes as a control — the public surface is untouched
      (SPEC.md: wheel_smoke_pins == []), so both must pass unchanged.
      done-when: python scripts/wheel_smoke.py -> exit 0 AND
      python -u scripts/wheel_operational_smoke.py -> exit 0 (both pasted)

- [ ] 18. (all) Map check, FULL mode (not --fast: this tranche changed src/).
      done-when: python tools/docs_verify.py -> failures are exactly C9's 3
      pre-existing shallow-clone ones (pasted)

- [ ] 19. (all) Full gate: python -m pytest tests/ -q -n 4. Run it on an idle
      box, never concurrently with docs_verify.
      done-when: output ends "N passed, 0 failed" with N >= 3818 + 2 new
      tests, allowing for C9's 5 known MCP-thread flakes re-run serially and
      shown green (pasted)

- [ ] 20. (all) [COMMIT] Push and confirm clean tree.
      done-when: git status --porcelain is empty AND git rev-parse HEAD ==
      git rev-parse origin/claude/reach-p5-rulings-codify-097nkz
