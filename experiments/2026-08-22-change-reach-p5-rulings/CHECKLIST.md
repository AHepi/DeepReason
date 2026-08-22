# Checklist for: codify two operator rulings on reach semantics (P5-reach)
State: next=17 blockers=none
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

- [x] 2. (S1, S3) [COMMIT] Commit the two tests alone, red-then-green order
      preserved in history.
      done-when: git status --porcelain is empty AND git log -1 --stat names
      only tests/test_reflexive_discipline.py

- [x] 3. (S1, S4) Add the E0 guard to reach_sweep's inner loop as its FIRST
      branch, with the comment stating why it is deliberately loop-invariant
      (it must not be hoisted above the clear-to-zero accounting), and add the
      inline deliberate-`<` comment at the coverage comparison.
      done-when: python -m pytest "tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach" "tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit" "tests/test_review_fixes.py::test_reach_clears_to_zero" -q
      -> 3 passed

      PROOF: 3 passed in 0.18s
      The third node id is the invariant the INNER placement protects; step 8's
      mutation run shows it going red under the outer placement.

- [x] 4. (S2, S4) Rewrite the reach.py module docstring: SIX -> SEVEN exits,
      a new FIRST bullet "E0 empty-own-battery" carrying the ruling and its
      basis, and the one-line deliberate-floor note in the E5 bullet. Both
      cite this tranche.
      done-when: python -c "import pathlib; d=pathlib.Path('src/deepreason/measures/reach.py').read_text(); assert 'SEVEN exits' in d and 'E0 empty-own-battery' in d and d.count('2026-08-22-change-reach-p5-rulings') >= 2"
      -> exit 0

      PROOF: exit 0 - SEVEN exits, E0 label, tranche cited 3 times

- [x] 5. (S2) Update docs/map/SUB-evaluation.md's exit-documentation trap: its
      prose gains E0, and its `check:` asserts len(conts) == 5 and all SEVEN
      labels. Run the amended check standalone.
      done-when: the amended check command copied out of SUB-evaluation.md and
      run in a shell -> exit 0 (pasted)

      PROOF: amended check exit=0
      (len(conts) == 5 and all SEVEN labels present in the module docstring)

- [x] 6. (S2) Prove the amended check still bites in BOTH directions: with the
      E0 guard removed the count is 4 and the check must FAIL; with the E0
      label removed from the docstring it must FAIL. Restore after each.
      done-when: two pasted runs, each exit 1, and a third run after restore
      -> exit 0

      PROOF:
      --- MUTATION A: remove the E0 guard (branch count falls to 4) ---
      check exit=1  (expected 1)
      --- MUTATION B: remove the E0 label from the docstring (branch still there) ---
      check exit=1  (expected 1)
      --- RESTORED ---
      check exit=0  (expected 0)

      The step-8 placement check was mutation-proven the same way, and the
      mutation also proves the claim the trap makes about it:
      --- MUTATION: hoist E0 to the outer loop (the placement the trap forbids) ---
      placement check exit=1  (expected 1)
      FAILED tests/test_review_fixes.py::test_reach_clears_to_zero - AssertionError...
      1 failed in 0.11s
      --- RESTORED ---
      placement check exit=0  (expected 0)

- [x] 7. (S5) Update the four fixtures SPEC.md M2 names, giving each reaching
      artifact the battery compile_interface would pin. No assertion touched.
      done-when: python -m pytest tests/test_reflexive_discipline.py tests/test_review_fixes.py tests/test_prose_refutation_boundaries.py -q
      -> 0 failed (pasted) AND git diff -- tests/ | grep -E "^-[[:space:]]+assert" is empty

      PROOF: 85 passed in 4.21s
      $ git diff -- tests/ | grep -E "^-[[:space:]]+assert"   -> empty
      Exactly the four tests SPEC.md M2 predicted, and no others.

- [x] 8. (S6) Add the new Traps entry to docs/map/SUB-evaluation.md for this
      ruling pair (both rulings, their authority date, this tranche id) with a
      `check:` that runs the two new tests and asserts the E0 label is in the
      docstring; and extend the "Where to change what" coverage-threshold row
      with the floor pin test. Advance Verified-at only if that document's
      checks are actually re-run in this step.
      done-when: python tools/docs_verify.py 2>&1 | tail -5 -> failures are
      exactly the 3 pre-existing shallow-clone ones named in REQUEST.md C9
      (pasted)

      PROOF:
      docs_verify [full]: 61 documents, 969 checks, 4 workers
        FAIL CON-run-identity.md:200  (git log over renamed run roots)
        FAIL CON-run-identity.md:202  -> fatal: ambiguous argument '1637e808'
        FAIL CON-run-identity.md:204  -> fatal: ambiguous argument 'f304fec1'
      docs_verify: 3 failed

      All three are C9's pre-existing shallow-clone failures: they resolve
      commit hashes this clone does not carry. No SUB-evaluation.md check
      fails. Verified-at advanced 7b82206d -> 7cae749c only after this
      document's own Verify: line was re-run: 112 passed in 22.29s.

- [x] 9. (S2, S6) Map link and audit gates.
      done-when: python tools/docs_verify.py --links -> 0 unresolved AND
      python tools/docs_verify.py --audit -> no NEW un-failable check (pasted)

      PROOF:
      docs_verify --links: 0 dangling reference(s), 61 document(s)
      docs_verify --audit: 0 finding(s)

- [x] 10. (S1..S6) [COMMIT] Commit the rulings, their docstring, their check,
      their fixtures and their map together — R3 requires the new exit and its
      documentation in ONE commit, and the fixtures must land with the guard
      or the tree is red between commits.
      done-when: git status --porcelain is empty AND git log -1 --stat names
      src/deepreason/measures/reach.py, tests/test_reflexive_discipline.py,
      tests/test_review_fixes.py and docs/map/SUB-evaluation.md

- [x] 11. (S9) Mutation proof, ruling 1: delete the E0 guard, run the pin,
      restore, re-run.
      done-when: two pasted runs — RED (1 failed) then GREEN (1 passed)

      PROOF (RULING 1 — delete the E0 guard):
      GUARD DELETED
      tests/test_reflexive_discipline.py:433: AssertionError
      FAILED tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach
      1 failed in 0.20s
      --- restore ---
      1 passed in 0.15s

- [x] 12. (S9) Mutation proof, ruling 2: break the floor the other way (make
      coverage exactly 0.5 provisional), run the pin, restore, re-run.
      done-when: two pasted runs — RED (1 failed) then GREEN (1 passed) AND
      git diff -- src/ is empty after restore

      PROOF (RULING 2 — break the boundary the other way):
      BOUNDARY BROKEN: '<' -> '<=' (coverage exactly at the floor becomes provisional)
      tests/test_reflexive_discipline.py:477: AssertionError
      FAILED tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit
      1 failed in 0.13s
      --- restore ---
      1 passed in 0.12s
      --- tree clean? ---
      (git diff --stat -- src/ empty == restored; the '<' comparison stands
      in the delivered tree, per C2)

- [x] 13. (S7) Add the E0 branch to rehearsal.py's own exit classifier, in the
      same position reach_sweep takes it, and update S2's `note` to record the
      ruling.
      done-when: python -c "import pathlib; s=pathlib.Path('experiments/2026-08-22-live-reach-rich-run/rehearsal.py').read_text(); assert 'E0 empty-own-battery' in s"
      -> exit 0

      PROOF: exit 0 — E0 label present in rehearsal.py

- [x] 14. (S7) Re-run the rehearsal against the fixed tree and paste S2, S8a,
      S8c; copy the regenerated JSON into this tranche as
      rehearsal-after-p5-rulings.json.
      done-when: python experiments/2026-08-22-live-reach-rich-run/rehearsal.py
      -> S2 exit is the E0 label with 0 hits and 0 reach events, S8a exit is
      "HIT full", S8c exit is "E4 criterion-fail" (all three pasted)

      PROOF (full run against the fixed tree; the three required rows first):
      S2 prose artifact vs wf-carrying seed        exit=E0 empty-own-battery       hits=0 reach_events=0 cov=0.5 novel=['uhi-energy-balance@r1']
      S8a prose conn: candidate vs seed (as shipped) exit=HIT full                   hits=1 reach_events=1 cov=0.6666666666666666 novel=['uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']
      S8c prose OFF-subject candidate vs seed (P1 landed) exit=E4 criterion-fail          hits=0 reach_events=0 cov=0.6666666666666666 novel=['uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']

      and the rest of the ladder, unchanged by this tranche:
      S1 same-criteria (seed vs ra:)               exit=E3 no-novel                hits=0 reach_events=0 cov=0.5 novel=[]
      S3 two seeds, different subject criteria     exit=HIT full                   hits=1 reach_events=1 cov=0.5 novel=['uhi-nocturnal-release@r1']
      S4 two seeds, foreign criterion unsatisfied  exit=E4 criterion-fail          hits=0 reach_events=0 cov=0.5 novel=['uhi-absent-subject@r1']
      S5 envelope vs integ: [relation-form]        exit=E4 criterion-fail          hits=0 reach_events=0 cov=1.0 novel=['relation-form@578e42df713e']
      S6 envelope vs conn: [hv,lineage,relation-form] exit=E4 criterion-fail          hits=0 reach_events=0 cov=0.3333333333333333 novel=['relation-form@578e42df713e']
      S8b prose conn: candidate vs seed (P1 landed) exit=HIT full                   hits=1 reach_events=1 cov=0.6666666666666666 novel=['uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']
      S7 envelope vs disc: []                      exit=E1 no-criteria             hits=0 reach_events=0 cov=None novel=[]

      Reading: S2 is the ONLY row this tranche moved. S3 is worth noting for
      RULING 2 — it is a full hit at coverage exactly 0.5, so the boundary
      the tranche pinned is live in the rehearsal ladder as well as in the
      unit pin. S5/S6 still exit E4 on relation-form alone, so PARKED P2-reach
      is untouched, as SPEC.md's out-of-scope section predicted.
      Copied into this tranche as rehearsal-after-p5-rulings.json.

- [x] 15. (S8) Add the E0 branch and label to
      experiments/2026-08-21-measure-reach-firing/census.py (module docstring
      vocabulary + rederived_census counters), plus the one-line note that the
      committed census JSON predates E0.
      done-when: python -c "import pathlib; s=pathlib.Path('experiments/2026-08-21-measure-reach-firing/census.py').read_text(); assert 'E0 empty-own-battery' in s"
      -> exit 0 AND git diff --stat -- experiments/2026-08-21-measure-reach-firing/census.json experiments/2026-08-21-measure-reach-firing/census-verdicts.json is empty

      PROOF:
      exit 0 — E0 in census.py
      (git diff --stat over the two committed JSON outputs: empty)
      census.py imports and compiles clean with E0

- [x] 16. (S7, S8) [COMMIT] Commit the two instruments and the pasted
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
