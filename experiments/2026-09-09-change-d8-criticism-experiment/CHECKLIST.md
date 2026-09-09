# Checklist for: does criticism, once connected and allowed to bite, make the harness's output materially better than the plain model? — TRANCHE 1 (instruments, offline proofs, sealed pre-registration; NO LIVE CALL)

State: next=18 blockers=none  (budget stop RESOLVED at step 17 by the operator: "Raise." -- ceiling 6500, SPEC Amendment 4, itemized from a measured 4498 base. The raise buys lines, not live calls: C9 still binds)  (step 10a inserted: a fixture positive control for the argumentative column, because no committed root can drive it)  (SPEC Amendment 2 at step 3: the diff ceiling is 4400, itemized; the earlier 2010 counted only authored lines and would have tripped on accounting, not scope)
Re-read REQUEST.md (with Amendment 1) + SPEC.md (with Amendment 1) before every
step. Execute strictly in order. One step per dr-execute-step invocation.

Map ids this plan was scoped from (`docs/map/INDEX.md`, seams before
subsystems): `DR-CON-criticism-source`, `DR-CON-discharge-channel`,
`DR-CON-authority`, `DR-CON-warrants-and-attacks`, `DR-CON-evidence-states`,
`DR-CON-run-identity`, `DR-CON-configuration-stages`, `DR-CON-seats`,
`DR-CON-schools`, `DR-SEAM-adjudication-x-authority`,
`DR-SEAM-manifest-x-schools`, `DR-SUB-rules`, `DR-SUB-adjudication`,
`DR-SUB-manifest`, `DR-SUB-application`, `DR-INV-frozen-surfaces`.

**No map document is modified by this tranche** (SPEC S16: nothing under `src/`
or `mini/` changes, so nothing the map describes changes). No `Verified-at:`
stamp is advanced. Planning rule 6 is therefore satisfied vacuously, and that
is stated rather than left silent.

**Two gates are NOT owed and will NOT be run**, per R31/S16 and CLAUDE.md's
MANDATORY block: the full test gate (no file under the repository's `tests/`
changes) and `tools/docs_verify.py` (no map document changes). Step 31 proves
the precondition rather than asserting it.

**One shared instrument IS touched, and it is data:** `scripts/cycle_soak.py`
gains three `CASES` rows (step 24). `SoakCase` is a frozen dataclass whose
`config_path` is READ from this tranche's own committed configuration and whose
`builder` is a module this tranche owns; nine committed cases set the
precedent, and no test pins the case set (`grep -rn "CASES" tests/` returns
only the unrelated `PRODUCTION_CASES_PER_PAIR`). `scripts/` is neither `src/`
nor `mini/`, so R36 is not touched.

---

- [x] 1. (S16) Create the tranche's working directories: `tools/`, `runs/`,
      `tests/`, `proof/`.
      done-when: `ls -d experiments/2026-09-09-change-d8-criticism-experiment/{tools,runs,tests,proof}`
      lists four directories, exit 0.
      PROOF:
      ```
      experiments/2026-09-09-change-d8-criticism-experiment/proof
      experiments/2026-09-09-change-d8-criticism-experiment/runs
      experiments/2026-09-09-change-d8-criticism-experiment/tests
      experiments/2026-09-09-change-d8-criticism-experiment/tools
      exit=0
      ```

- [x] 2. (S8, S9) Copy the three source instruments BYTE-FOR-BYTE, no edits in
      this step: `compose_result.py` and `judge_pairwise.py` from
      `experiments/2026-09-06-change-writers-room-organiser-testing/tools/`,
      `arm0.py` from
      `experiments/2026-09-05-change-mini-isolation-programme/d8/`.
      done-when: `proof/COPIES.sha256` records all three digests and
      `sha256sum -c proof/COPIES.sha256` exits 0 against BOTH the sources and
      the copies (identical digests, pasted).
      PROOF:
      ```
      $ cd tools && sha256sum -c ../proof/COPIES.sha256
      compose_result.py: OK
      judge_pairwise.py: OK
      arm0.py: OK

      $ sha256sum <the three sources>
      7c2835448886465ffd07ffadc9d057ac0a83da5f58d30dbff96509b4d81b9c62  .../organiser-testing/tools/compose_result.py
      1f6c8f9005a2b49cce5884f1404d36a1393783f17fff6d0bb23720e095e261cd  .../organiser-testing/tools/judge_pairwise.py
      c33b87a90ff496dcf50a0c01624fdf5246e791729d49f4d19951112c25c20ccb  .../mini-isolation-programme/d8/arm0.py
      ```
      The judge instrument's digest equals the one the organiser tranche's
      PREREG Amendment 9 sealed, so the copy is the STRICTER post-Amendment-9
      instrument (it refuses a unit whose root does not replay), not an
      earlier one.

- [ ] 3. (S8, S9) [COMMIT] the directories and the untouched copies, with the
      three digests in the message.
      done-when: `git status --porcelain experiments/2026-09-09-*/` empty and
      the branch head is on origin.

- [x] 4. (S9, R22) Write `tools/coupling_placebo.py`: per criticism, whether the
      candidate AFTER it changed and whether the candidate BEFORE it changed,
      the DIFFERENCE reported as the only evidence, per root, with n.
      done-when: `python tools/coupling_placebo.py --help` exits 0 and the
      module imports no transport (`grep -c "urllib\|requests\|http" ` is 0).
      PROOF: `--help` exits 0; the transport grep returns `0`.
      HOW IT WAS BUILT, and this is the substance of the step: the measurement
      is NOT reimplemented. W2's own two instruments are copied into
      `tools/w2_census.py` and `tools/w2_q5.py` with exactly ONE line changed
      in each — the repo-root computation, because the files sit one directory
      deeper here — proven by `diff` against the originals after reversing that
      line, which reports no other difference. `coupling_placebo.py` is a
      driver over them: it adds the per-arm table and the typed empty case and
      forms no opinion about a rate. Reimplementing W2's method would have
      produced a second instrument to keep in agreement with the first, which
      is the thing the repository's own modularity law exists to prevent.
      A second, unplanned finding this step resolved: W2's `helped` measure
      already falls back to SURVIVAL (`status == accepted`) where a root has no
      scalar checker, which is exactly what this tranche's composition roots
      need — so no new scoring hook was written, and none should be.

- [x] 5. (S9) Prove it against W2's own published table: run it on the two
      roots W2 measured and compare to
      `experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`.
      done-when: every reproduced coupling/placebo/difference cell matches W2's
      to 0.1 percentage point, pasted side by side into
      `proof/W2_REPRODUCTION.txt`; a mismatch is a blocker, not a rounding note.
      PROOF (`proof/W2_REPRODUCTION.txt`, 32 fields, all OK):
      ```
      | P-R1 | R1_mechanical | 118 | 17.8% | 30.5% | **-12.7 pp** | 38.1% | 82.2% |
      | P-R1 | R2_prose_quote |  54 | 98.1% | 100.0% | **-1.9 pp** | 37.7% |  1.9% |
      | P-C1 | R1_mechanical | 341 |  9.4% |  3.5% | **+5.9 pp** |  0.0% | 90.6% |
      | P-C1 | R2_prose_quote |  60 | 100.0% | 100.0% | **+0.0 pp** | 0.0% | 0.0% |

      REPRODUCTION OK: every rate, denominator and count matches W2's
      committed output within 0.1 pp.
      ```
      Each of the four rows equals W2's published table cell for cell. The
      denominators (118, 54, 341, 60), the coupled counts (21, 53, 32, 60) and
      the helped counts (8, 20, 0, 0) matched EXACTLY, so the 0.1 pp tolerance
      was never exercised. Both scoring paths were exercised: P-C1 through its
      own rational checker, P-R1 through the survival fallback this tranche
      will use.

- [x] 6. (S9) Prove the empty case is typed, not silent: run it on a committed
      root with zero argumentative criticisms.
      done-when: output contains `n=0` and NO rate is printed.
      PROOF (`proof/EMPTY_CASE_TYPED.txt`):
      ```
      | no-criticism control | failed-epoch1-run-8e22d0431fd2b98d | R1_mechanical | **n=0** | — | — | — | — | — |
      | no-criticism control | failed-epoch1-run-8e22d0431fd2b98d | R2_prose_quote | **n=0** | — | — | — | — | — |
      ```
      The root was chosen by W2's own census rather than by inspection: its
      `roots.json` lists the 60 committed roots that carry criticism, and this
      is one of the 30 that do not. The proof file carries a positive control
      beside it — the same command on a root that DOES carry criticism returns
      n=1 and n=13 with rates — so the n=0 is a property of the root, not of
      the tool. Why this matters downstream: an arm that dies before any
      criticism is written must be reported as UNMEASURED, never as
      measured-at-zero.
      One defect in this step's own tool, found and fixed inside the step: a
      root named both by `--label` and positionally was measured twice and
      printed twice, which a reader counting rows would have read as two
      independent measurements.

- [x] 7. (S9) [COMMIT] the coupling instrument and its two proofs.
      done-when: tree clean for the tranche, head on origin.

- [x] 8. (S10, R23) Write `tools/record_census.py`: per root, attack edges
      minted; warrants split demonstrative / argumentative; refutations;
      evidence states read from `deepreason results --json`, never re-derived.
      done-when: `python tools/record_census.py --help` exits 0.

- [x] 9. (S10) Prove the evidence-state row is a READ and not a second
      derivation, on a committed root.
      done-when: the census's evidence-state row equals that root's
      `results --json` `evidence_states.counts` byte-for-byte, both pasted to
      `proof/CENSUS_AGREES.txt`.

- [x] 10. (S10) [COMMIT] the census instrument and its proof.
       done-when: tree clean, head on origin.

- [x] 10a. (S10, R23) [inserted at step 10] A fixture positive control for the
       argumentative warrant column, with a mutation proof — because a corpus
       scan in step 9/10 measured 1 141 warrants across the 20 most
       criticism-heavy committed roots and ZERO argumentative among them, so
       no committed root can drive that branch and a zero from ARM A could not
       be told from a broken instrument.
       done-when: `tests/test_record_census.py` passes on both roads, and
       collapsing the two roads drives it RED.
       PROOF (`proof/ARGUMENTATIVE_COLUMN_LIVE.txt`):
       ```
       corpus scan: warrants by road {'demonstrative': 1141}
                    roots with ANY argumentative warrant: NONE

       $ pytest tests/test_record_census.py -q      ->  3 passed
       --- with the roads collapsed (mutation) ---
       FAILED ...test_the_argumentative_column_moves...   1 failed, 2 passed
       --- restored ---                                   3 passed
       ```
       Registered now so it is not decided later: if ARM A terminates cleanly
       with 0 argumentative warrants, that is a FINDING about granted
       authority, not a broken instrument.
       A second symbol collision was fixed in this step for the reason step 6
       fixed the first: `render` matched words in `invariants.py` and
       `run_manifest.py` and made the gate report frozen-surface CONTACT.
       Renamed; the gate re-reads CLEAR.

- [x] 11. (S2, R5, A3) Edit the copied `tools/arm0.py` in exactly one place: `K`
       becomes a required argument. Nothing else moves.
       done-when: `diff` against the copy shows changes confined to the `K`
       definition and its argument parsing, pasted into `proof/ARM0_DIFF.txt`.
       PROOF: `proof/ARM0_DIFF.txt` carries the whole diff. It is THREE changes,
       not the one this step's line predicted, and the extra two are recorded
       rather than absorbed:
       (a) `K` becomes a required argument — the planned change;
       (b) the frozen input is reached by an explicit path from the
           repository rather than from this file's neighbours, because the
           instrument moved tranches and the old relative path resolved
           somewhere else here (same class of change as step 4's repo-root
           line);
       (c) a `--dry-run` is added, because step 12's done-criterion is that no
           call is made and the copied instrument had no way to demonstrate
           that.
       Each is forced by the move or by the checklist's own next step; none
       changes what a live call sends.

- [x] 12. (S2, C9) Prove it makes no call: `--dry-run`.
       done-when: it prints the prompt's sha256 and byte size, exits 0, and no
       network call is made; the printed question digest equals the digest of
       `input-d8`'s `problem.description`.
       PROOF (`proof/ARM0_DIFF.txt`), run with the credential DELIBERATELY
       removed from the environment:
       ```
       $ env -u OLLAMA_API_KEY python arm0.py 9 --dry-run
       { "calls_that_would_be_made": 9, "dry_run": true, "k": 9,
         "model": "qwen3.5:397b", "question_bytes": 450,
         "question_sha256": "e8e720d251b3cab2cddd548cb5064a74575404c8ae47f347f840faa6021a19b1" }
       rc=0

       independent sha256: e8e720d251b3cab2cddd548cb5064a74575404c8ae47f347f840faa6021a19b1
       no K -> rc=2      K=0 -> rc=2
       ```
       The digest is re-derived from the frozen input by a separate command,
       not merely printed by the instrument under test. That mattered: the
       dry run CAUGHT a path defect in change (b) above — the first version
       resolved the frozen input outside `experiments/` and failed loudly. Had
       the wrong path happened to exist, ARM 0 would have answered a different
       question and nothing in its output would have said so.

- [x] 13. (S2) [COMMIT] arm0 and its dry-run proof.
       done-when: tree clean, head on origin.

- [x] 14. (S8 §5, R16, R19, M7) Extend the copied `tools/compose_result.py` with
       `--per-position` only: one file per surviving position, deterministic
       order, nothing else changed.
       done-when: `diff` against the copy shows the composed TEXT path
       unchanged (the existing `--out`/`--json` bytes are identical on a
       committed root, proven by digest before and after).
       PROOF (`proof/PER_POSITION_DETERMINISTIC.txt`):
       ```
       before: 21bd15edcfc92215dd9533c69b52a75b7e695725763cdd466ba9f1ab7c321c9f
       after : 21bd15edcfc92215dd9533c69b52a75b7e695725763cdd466ba9f1ab7c321c9f
       COMPOSED TEXT IDENTICAL / SUMMARY JSON IDENTICAL
       self-test, both versions: 43 surviving, 0 refuted, 53423 chars
       ```
       Built as ONE renderer called twice (`_position_block`), so a
       per-position unit is byte-identical to its own paragraph inside the
       composed unit — checked directly: of 36 units, the number whose text
       does not appear verbatim in the composed unit is NONE. Two renderers
       would have let the secondary comparison drift away from the primary one
       silently, which is the drift the secondary comparison exists to be
       immune from.

- [x] 15. (S8 §5) Prove determinism: run `--per-position` twice on the same
       committed root.
       done-when: the two output sets are byte-identical
       (`diff -r` exits 0), pasted to `proof/PER_POSITION_DETERMINISTIC.txt`.
       PROOF: `diff -r /tmp/pp1 /tmp/pp2` produced no output, rc=0, over 36
       units. Units are named by ORDINAL, never by artifact id: a filename
       that renumbered when a lower-sorting position arrived is the one thing
       a stable unit may not do.

- [x] 16. (S8 §5, R19, A5) Implement the bare-essay counterpart rule: paragraphs
       split on blank lines, essay order, concatenated greedily from the first
       until within 1.5× of the position unit's character count; the ratio
       reported.
       done-when: on the three committed D8 ARM 0 essays the rule produces a
       stated, reproducible set of counterpart units with their ratios, twice
       identically.
       PROOF (`proof/ESSAY_COUNTERPARTS.txt`). The rule was written THREE
       times, and each correction came from its own self-test rather than from
       review — which is the entire reason it is built before PREREG seals it:
       - v1, first paragraph prefix at or above the target: ratios 1.73 / 1.84
         / 1.94, EVERY pair unmatched.
       - v2, closest paragraph prefix, two-sided: still empty, and measurably
         so. The first essay's paragraph prefixes are 358, 464, 469, 579, 741,
         2212, … and NOT ONE lies in the [800, 1800] window a 1200-character
         position allows.
       - v3, SENTENCE prefixes (sealed): the same essay has six prefixes in
         that window. Self-test: ratios 0.90 / 0.97 / 0.95, all matched.
       End to end on the 36 real units: **108 pairs, 108 within the length
       rule, 0 excluded**, twice byte-identically. The secondary comparison is
       therefore REACHABLE, which is the property that matters given the
       primary comparison is expected to be NULLed by length.
       Two boundaries are asserted and hold: an unreachable target reports
       UNMATCHED with its shortfall rather than padding the essay, and a
       target far below one sentence reports UNMATCHED rather than passing a
       one-sided test. The two-sidedness is load-bearing — a one-sided rule
       would let a tenth-length fragment count as within the length rule,
       smuggling the confound back in under the rule written to exclude it.
       DEVIATION, recorded: this step also added `tools/essay_counterparts.py`.
       The plan implied the rule would live in the composer; it is a separate
       instrument because the composer reads a RUN ROOT and this reads
       ESSAYS, and giving the composer a second input shape would have been
       the larger change.

- [x] 17. (S8 §5) [COMMIT] the composer extension and its two proofs.
       done-when: tree clean, head on origin.
       PROOF: tree clean, head on origin. Blast radius CLEAR.
       **BUDGET GATE: EXCEEDED, 4498 of 4400.** Recorded here as the stop it
       is. Measured causes, both specific:
       (a) 857 lines of W2's own instruments copied verbatim
           (`w2_census.py` 519, `w2_q5.py` 338), a step-4 decision that was
           right — reimplementing the placebo measurement would have created
           two things to keep in agreement — and that no itemization included,
           because the itemization was written before the decision.
       (b) the workflow documents carry their evidence inline: SPEC.md 906
           (three amendments), CHECKLIST.md 441 (every done-criterion's pasted
           output), REQUEST.md 261, PARKED.md 186 = 1 794 against 1 190
           budgeted for those four PLUS the two not yet written.
       Estimated remaining: ~1 660 of instruments and PREREG, plus ~300 for
       VALIDATION and DELIVERY, so the tranche lands near 6 450.
       Not resolved in this window: SPEC Amendment 2 states in writing that
       approaching this ceiling is a signal to SPLIT, not to amend a third
       time, and a window that amends its own ceiling whenever it trips is a
       window with no ceiling.

- [ ] 18. (S8 §6, R17) Prove the copied `tools/judge_pairwise.py`'s CRITERIA are
       byte-identical to the organiser tranche's, by `diff` AND by the tool's
       own `criteria-check`.
       done-when: `diff` is empty and `criteria-check` prints sha256
       `fab3fde2f3a2000bd5f7415e7a7ae3be013fd8b83b4fd52395eef4b18327df28`.

- [ ] 19. (S8 §7, R20) Extend it to the five pairings (C vs 0, V vs 0, C vs V,
       A vs C, A vs 0), keeping Amendment 9's refusals unchanged: a unit whose
       root is not `completed`, or whose `REPLAY_VALIDATION.json` reports any
       violation, is refused.
       done-when: a unit test in the tranche's own `tests/` drives BOTH
       refusals red-then-green against fixtures, output pasted.

- [ ] 20. (S8 §8, R21) Prove the decision rule reports PER PAIR OF RUNS and
       cannot pool: a fixture with two runs per arm whose per-pair verdicts
       differ must print two verdicts, never one.
       done-when: the tranche test asserts exactly that and fails when the
       pooling line is reinstated (RED output pasted).

- [ ] 21. (S8 §6-§9) [COMMIT] the judging instrument and its three proofs.
       done-when: tree clean, head on origin.

- [ ] 22. (S4, R8) Write `tools/critic_stub.py`: a loopback endpoint bound to
       `argumentative_critic` only, importing `scripts/wheel_operational_smoke.py`'s
       stub the way `cycle_soak.py:58` does, overriding ONLY the objection text.
       done-when: it starts, serves one argumentative-critic request, and the
       reply validates against the shipped critic contract; the import is the
       shared stub (no second stub is minted — `grep` proves the import).

- [ ] 23. (S4, R7, Amendment 1) Write `tools/make_vacuous_bank.py`: deterministic
       from a seed and a target length distribution; entries name no artifact
       id, no claim text, no mechanism.
       done-when: `--self-test` reproduces a committed fixture bank
       byte-for-byte from a fixed seed, exit 0.

- [ ] 24. (S4, R9) Write the vacuity check and DRIVE IT RED: plant one
       target-specific entry and prove the check fails; restore and prove it
       passes.
       done-when: both outputs pasted to `proof/VACUITY_RED.txt` — the check
       fails for the reason it claims to test.

- [ ] 25. (S4) [COMMIT] the stub, the bank generator and the vacuity proof.
       done-when: tree clean, head on origin.

- [ ] 26. (S3, S5, A1) Write `tools/build_manifest.py` and `runs/config-{c,v,a}.yaml`:
       three compiled configurations, ARM A differing from ARM C ONLY in the
       authority pair and the two-seat judge ensemble
       (`qwen3.5:397b`/`glm-5.2`, taken verbatim from
       `experiments/2026-08-25-poietics-program/run-config.yaml`).
       done-when: all three compile, and `--dry-run` prints each role matrix
       without a provider call.

- [ ] 27. (S5) Prove route identity: ARM A's and ARM C's role tables compared
       field by field.
       done-when: every role but `judge` has an identical `route_sha256`;
       `judge` has two seats of two families. Tool output, not eyeballing,
       pasted to `proof/ARM_A_ROUTE_IDENTITY.txt`.

- [ ] 28. (S5) Prove the authority gate is really on, and the ensemble really
       obtainable, on ARM A's own compiled artifact — and drive the second RED
       by collapsing the judge role to one seat.
       done-when: `_authority` returns `trial_required` (not `observe_only`),
       `_select_judge_ensemble` returns two seats, and the collapsed variant
       raises `JudgeEnsemblePolicyError`; all three pasted.

- [ ] 29. (S5, Amendment 1's open question) Answer by dry-run, not by reading:
       does a defended trial also require `JUDGE_SEATS_ENABLED` and a
       `rubric_policy` other than `forbid` to dispatch?
       done-when: the answer is recorded in `proof/TRIAL_PRECONDITIONS.txt`
       with the command that produced it, and `runs/config-a.yaml` carries
       whatever it requires.

- [ ] 30. (S3, R6) Prove the open-criticisms rendering on an OFFLINE stub root of
       ARM C's shape: criticism reaches the seat that writes the next candidate.
       done-when: the section-plan receipts naming `dr.open-criticisms` are
       counted `n of m` (the `armR.sh:33-35` shape), n > 0, pasted to
       `proof/ARMC_RENDERS.txt`.

- [ ] 31. (S4, R9) Prove ARM V's objections reach the next candidate EXACTLY as
       ARM C's do: same section, same priority, same disposition.
       done-when: the two stub roots' section-plan receipts for that section
       differ only in the objection text, `diff` output pasted to
       `proof/ARMV_SAME_PATH.txt`.

- [ ] 32. (S3, S4, S5) [COMMIT] the manifest builder, the three configurations
       and the five proofs.
       done-when: tree clean, head on origin.

- [ ] 33. (S12, R25) Add three `CASES` rows to `scripts/cycle_soak.py` — data
       only, `config_path` pointing at this tranche's committed configurations.
       done-when: `python -u scripts/cycle_soak.py --list` shows the three new
       ids and every pre-existing id, unchanged.

- [ ] 34. (S12) Soak ARM C's shape to cycle 8 against the stub.
       done-when: the run ends green; log committed to `runs/soak-c.log`.

- [ ] 35. (S12) Soak ARM V's shape.
       done-when: green; `runs/soak-v.log` committed.

- [ ] 36. (S12) Soak ARM A's shape — the one carrying a granted authority and a
       two-seat ensemble, so the one most likely to fail offline.
       done-when: green; `runs/soak-a.log` committed. A RED here is a finding
       for SPEC, not a step to retry blind.

- [ ] 37. (S12) [COMMIT] the three cases and the three soak logs.
       done-when: tree clean, head on origin.

- [ ] 38. (S8, R15) Write `PREREG.md`: §0 what is fixed for every arm (by
       digest) and WHICH values are rules awaiting a measurement (ARM V's bank,
       ARM 0's K) rather than fixed numbers; §0's own disclosure row for R35's
       one-model deviation; §1-§4 the arms; §5 the unit and its two refusals;
       §6 the instrument; §7 the five pairings; §8 the rule; §9 the length rule
       with its ceiling registered against it; §10 the secondary comparison;
       §11 the predictions.
       done-when: every section present; every digest in §0 re-derived by
       command in the same step and pasted.

- [ ] 39. (S11, R24) Write `claims.json` — every §11 prediction a claim, each
       with a falsifier and "not shown able to fail" standing.
       done-when: `python tools/record_claims.py <claims.json>` exits 0 and no
       claim lacks a standing or a falsifier.

- [ ] 40. (S8, R15) [COMMIT] PREREG.md and claims.json, SEALED: the commit
       message carries `sha256sum PREREG.md` verbatim.
       done-when: the pushed commit message contains the digest, and
       `sha256sum -c` against the committed file passes.

- [ ] 41. (C9, R38) Prove tranche 1 spent nothing.
       done-when: no tranche-1 artifact carries a provider response; the
       credential file's atime/mtime are unchanged since capture; and
       `git log --all --stat | grep -c "d8-criticism-experiment/env"` is 0.

- [ ] 42. (S16, R36) Prove the scope held.
       done-when: `git diff --stat origin/main -- src/ mini/ tests/` is EMPTY.
       This is also the proof that the full gate and `docs_verify` are not
       owed; both are therefore not run (R31, and CLAUDE.md's MANDATORY block).

- [ ] 43. (all) [COMMIT] push and confirm clean.
       done-when: `git status --porcelain` is empty AND the branch head is on
       origin.

Then: `dr-validate-change` (VALIDATION.md), then `dr-deliver-change`
(DELIVERY.md with the R-by-R table), then STOP — tranche 2 is a separate
tranche and does not begin unprompted (R39, R40).
