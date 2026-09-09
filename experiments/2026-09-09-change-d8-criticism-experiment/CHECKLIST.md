# Checklist for: does criticism, once connected and allowed to bite, make the harness's output materially better than the plain model? — TRANCHE 1 (instruments, offline proofs, sealed pre-registration; NO LIVE CALL)

State: next=1 blockers=none
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

- [ ] 1. (S16) Create the tranche's working directories: `tools/`, `runs/`,
      `tests/`, `proof/`.
      done-when: `ls -d experiments/2026-09-09-change-d8-criticism-experiment/{tools,runs,tests,proof}`
      lists four directories, exit 0.

- [ ] 2. (S8, S9) Copy the three source instruments BYTE-FOR-BYTE, no edits in
      this step: `compose_result.py` and `judge_pairwise.py` from
      `experiments/2026-09-06-change-writers-room-organiser-testing/tools/`,
      `arm0.py` from
      `experiments/2026-09-05-change-mini-isolation-programme/d8/`.
      done-when: `proof/COPIES.sha256` records all three digests and
      `sha256sum -c proof/COPIES.sha256` exits 0 against BOTH the sources and
      the copies (identical digests, pasted).

- [ ] 3. (S8, S9) [COMMIT] the directories and the untouched copies, with the
      three digests in the message.
      done-when: `git status --porcelain experiments/2026-09-09-*/` empty and
      the branch head is on origin.

- [ ] 4. (S9, R22) Write `tools/coupling_placebo.py`: per criticism, whether the
      candidate AFTER it changed and whether the candidate BEFORE it changed,
      the DIFFERENCE reported as the only evidence, per root, with n.
      done-when: `python tools/coupling_placebo.py --help` exits 0 and the
      module imports no transport (`grep -c "urllib\|requests\|http" ` is 0).

- [ ] 5. (S9) Prove it against W2's own published table: run it on the two
      roots W2 measured and compare to
      `experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`.
      done-when: every reproduced coupling/placebo/difference cell matches W2's
      to 0.1 percentage point, pasted side by side into
      `proof/W2_REPRODUCTION.txt`; a mismatch is a blocker, not a rounding note.

- [ ] 6. (S9) Prove the empty case is typed, not silent: run it on a committed
      root with zero argumentative criticisms.
      done-when: output contains `n=0` and NO rate is printed.

- [ ] 7. (S9) [COMMIT] the coupling instrument and its two proofs.
      done-when: tree clean for the tranche, head on origin.

- [ ] 8. (S10, R23) Write `tools/record_census.py`: per root, attack edges
      minted; warrants split demonstrative / argumentative; refutations;
      evidence states read from `deepreason results --json`, never re-derived.
      done-when: `python tools/record_census.py --help` exits 0.

- [ ] 9. (S10) Prove the evidence-state row is a READ and not a second
      derivation, on a committed root.
      done-when: the census's evidence-state row equals that root's
      `results --json` `evidence_states.counts` byte-for-byte, both pasted to
      `proof/CENSUS_AGREES.txt`.

- [ ] 10. (S10) [COMMIT] the census instrument and its proof.
       done-when: tree clean, head on origin.

- [ ] 11. (S2, R5, A3) Edit the copied `tools/arm0.py` in exactly one place: `K`
       becomes a required argument. Nothing else moves.
       done-when: `diff` against the copy shows changes confined to the `K`
       definition and its argument parsing, pasted into `proof/ARM0_DIFF.txt`.

- [ ] 12. (S2, C9) Prove it makes no call: `--dry-run`.
       done-when: it prints the prompt's sha256 and byte size, exits 0, and no
       network call is made; the printed question digest equals the digest of
       `input-d8`'s `problem.description`.

- [ ] 13. (S2) [COMMIT] arm0 and its dry-run proof.
       done-when: tree clean, head on origin.

- [ ] 14. (S8 §5, R16, R19, M7) Extend the copied `tools/compose_result.py` with
       `--per-position` only: one file per surviving position, deterministic
       order, nothing else changed.
       done-when: `diff` against the copy shows the composed TEXT path
       unchanged (the existing `--out`/`--json` bytes are identical on a
       committed root, proven by digest before and after).

- [ ] 15. (S8 §5) Prove determinism: run `--per-position` twice on the same
       committed root.
       done-when: the two output sets are byte-identical
       (`diff -r` exits 0), pasted to `proof/PER_POSITION_DETERMINISTIC.txt`.

- [ ] 16. (S8 §5, R19, A5) Implement the bare-essay counterpart rule: paragraphs
       split on blank lines, essay order, concatenated greedily from the first
       until within 1.5× of the position unit's character count; the ratio
       reported.
       done-when: on the three committed D8 ARM 0 essays the rule produces a
       stated, reproducible set of counterpart units with their ratios, twice
       identically.

- [ ] 17. (S8 §5) [COMMIT] the composer extension and its two proofs.
       done-when: tree clean, head on origin.

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
