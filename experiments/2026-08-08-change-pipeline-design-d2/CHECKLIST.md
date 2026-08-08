# Checklist for: dual-mode conjecture — Rung D2 design, rev 2 corrected (Amendment 1 + 2)
State: steps 1-31 complete (original tranche, validated PASS); Amendment 4 adds steps 32-43; next=34 blockers=none
Map ids (per SPEC.md's own map preflight, re-confirmed here):
DR-SEAM-llm-x-rules (llm/contracts.py, llm/wire.py, rules/conj.py,
rules/crit.py — Item 2's wire field), DR-SEAM-adjudication-x-rules
(rules/warrants.py, adjudication/edges.py — the relatedness-claim/
formally_backed change), DR-SEAM-evaluation-x-rules (rules/warrants.py,
measures/reach.py, programs.py, informal/trial.py — the new eval-kind
dispatch), DR-SEAM-evaluation-x-ontology (programs.py,
ontology/commitment.py, oracle.py, oracle_sandbox.py — reusing
`_compile`), DR-CON-conjecture-kinds (the map document this work
extends), DR-CON-seats (the encoder-role registration), DR-INV-frozen-
surfaces (read again before step 1 — every step below is planned to
avoid contact; steps 24-26 are the explicit, gated exception).

Authoritative design: SPEC.md's "## Revision 2 (Amendment 1)" section
plus its "Protection semantics (rev 2, CORRECTED by Amendment 2)"
subsection — rev 1's own Item 1/Fork F1 and this document's pre-
Amendment-2 protection-semantics paragraph are SUPERSEDED, never built
against.

Diff-budget convention (R47): at every `[COMMIT]` step, compare the
tranche's ACTUAL changed lines (`git diff --stat <tranche-base>..HEAD`
across `src/`+`tests/`+`docs/map/`) against SPEC.md's rev-2 budget
(1150 lines). Exceeding it is a STOP in dr-execute-step's own standard
format (decision, priced options, recommendation) — the running total
is tracked in each `[COMMIT]` step's own done-when line below.

Frozen-surface convention (R47/C10): every step below states which of
the five surfaces it MUST NOT touch. A step whose actual diff touches
`capabilities/state.py`, `harness.py`, `invariants.py`/
`verification/`'s replay formats, `run_manifest.py`, or `qualification.py`
is NOT DONE — dr-execute-step records the contradiction, does not
proceed, and returns to the orchestrator, per C10.

Requirements with no dedicated step, and why: R19-R22/R25-R27/R32
(Item 1) need ZERO new code (M25's own governing law — nothing is
built, per SPEC.md's own "0 lines" budget line); R28-R31/R39/R40 are
already satisfied by REQUEST.md/SPEC.md's own existence and this
document's own act of being planned; R37 is satisfied by the "Test
implications" citations embedded in steps 3/6/9/12/23 above; R46/R48
are satisfied by the SPEC.md rev-2 correction commit and this
checklist's own commit, both already pushed before this line was
written.

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

## Item 2 — the new eval kind: reader before writer (R23, R33, R41)

- [x] 1. (R41, M26) Read `oracle.py::_compile` and `oracle_sandbox.py`'s
      own process-isolation call path in full; confirm which function(s)
      `programs.evaluate` would need to call to dispatch a new
      `program:candidate-checker` kind to this engine, without touching
      `oracle.py`'s own body (call it, do not modify it).
      done-when: a one-paragraph note in this step's own execution
      record names the exact call signature `programs.evaluate`'s new
      branch will use. MUST NOT touch: oracle.py (read-only step).
      DONE — CORRECTION to the checklist's own assumption, found by
      doing this read: `programs.evaluate` does NOT need a new `elif`
      branch at all. `program:exec_oracle` (the closest existing
      precedent for "run model-authored code against fixed tests") is
      dispatched through the EXISTING generic branch
      (`elif kind == "program": fn = PROGRAMS.get(arg)`,
      `programs.py:358-362`) — `_exec_oracle` is simply ANOTHER entry in
      the `PROGRAMS` dict (`programs.py:245`). The new kind only needs
      a NEW `PROGRAMS` dict entry (e.g. `PROGRAMS["candidate_checker"]`),
      never a new `elif`. One shape difference from `_exec_oracle`
      itself: `run_from_spec(source, budget)` treats the ARTIFACT'S OWN
      CONTENT as `source` (the code to run) and stores only
      `{entry, tests, step_limit}` in `budget.extra` (`oracle.py:192-198`,
      `_load_spec`, `oracle.py:328-332`) — that fits `exec_oracle`'s own
      world, where content=code. In THIS design, content=prose
      (Amendment 1) and the CHECKER SOURCE must itself live in
      `commitment.budget.extra` (mirroring `forbidden_commitment`'s own
      `Budget(extra={"case": ...})` pattern, D1 census M4), so the new
      program function reads `{source, entry, tests, step_limit}` ALL
      from budget via the SAME `oracle.py::_load_spec` helper
      (unmodified, already exported) and calls `oracle.py::run(source,
      entry, tests, step_limit)` (`oracle.py:180-189`, unmodified) —
      ignoring the artifact's own `text` argument entirely. Net effect:
      ZERO changes to `oracle.py`/`oracle_sandbox.py`, confirming this
      step's own MUST-NOT-touch constraint even more strongly than
      planned. Step 2's own action is adapted to this finding below
      (recorded there, not silently).
- [x] 2. (R41) ADAPTED per step 1's finding: instead of a new `elif`
      branch, added `PROGRAMS["candidate_checker"]` (programs.py) plus
      `oracle.py::run_from_full_spec`/`candidate_checker_commitment`
      (new functions, mirroring `run_from_spec`/`exec_oracle_commitment`
      exactly) — this reuses the EXISTING generic `elif kind ==
      "program": fn = PROGRAMS.get(arg)` dispatch (programs.py:358-362,
      unmodified) rather than adding a new branch. `CANDIDATE_CHECKER_PROGRAM`
      added as a constant, deliberately NOT added to `EXEC_PROGRAMS`
      (R45).
      done-when: `python -c "from deepreason import programs; assert 'candidate_checker' in programs.PROGRAMS"` -> exit 0. DONE.
      MUST NOT touch: the five frozen surfaces — confirmed (`oracle.py`,
      `programs.py` are neither).
- [x] 3. (R41) Mutation-prove step 2: a candidate-checker whose source
      fails a test produces `FAIL` (not a crash, not `PASS`) through the
      dict-dispatch path — new cases in `tests/test_oracle.py`
      (SCHEMA.md's own mutation-provable rule).
      done-when: `python -m pytest tests/test_oracle.py -k "candidate_checker or run_from_full_spec or refutes_a_prose_conjecture" -q` -> passes (4 new tests); mutation-proved separately (a deliberately-mutated `EXEC_PROGRAMS` membership assertion was shown to fail before being reverted). DONE — 4 passed.
- [x] 4. (R41) [COMMIT] Commit step 2-3.
      done-when: diff-budget running total <= 1150 (paste
      `git diff --stat <tranche-base>..HEAD -- src/ tests/`); frozen-
      surface diff empty (paste `git diff --stat <tranche-base>..HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py`); push confirmed.
      DONE — running total: 105 lines (oracle.py +35, programs.py +11,
      test_oracle.py +59) of 1150. Frozen-surface diff: empty. Pushed.

## Item 2 continued — the two wire-facing extensions (R33)

- [x] 5. (R33, M23) Extend `informal/skeleton.py::ForbiddenCase`'s
      `_eval_kind_is_safe` validator to accept `program:candidate-checker`
      in addition to `rubric:`/`program:<PROGRAMS-name>`, with the SAME
      RCE-safety comment discipline the existing validator already
      documents.
      done-when: `python -m pytest tests/test_workload_formal.py -q` ->
      0 failed, plus a new case asserting the new kind parses.
      MUST NOT touch: the five frozen surfaces (this file is
      `informal/skeleton.py`).
      DONE, with two corrections found while executing:
      (1) `test_workload_formal.py` does not cover `informal/skeleton.py`
      at all (it covers a DIFFERENT, Lean-based "formal" workload) — the
      real coverage lives in `tests/test_informal.py`,
      `tests/test_review_fixes.py`, `tests/test_prose_refutation_boundaries.py`;
      used `test_informal.py` instead, all three files re-run to confirm
      no regression (131 passed total).
      (2) `_eval_kind_is_safe` ALREADY accepted `program:candidate_checker`
      unconditionally (it only checks the `rubric:`/`program:` PREFIX,
      never the specific name) — the real gap was `forbidden_commitment`
      having nowhere to put a model-authored CHECKER SOURCE (its budget
      only ever stored `case` text). Added `ForbiddenCase.checker_spec:
      dict | None` (required exactly for `program:candidate_checker`,
      forbidden otherwise, enforced by a NEW cross-field check) and
      threaded it into `forbidden_commitment`'s own budget
      (`extra["spec"]`, same JSON-encoding convention `exec_oracle_commitment`
      already uses). Self-caught bug: a `field_validator` on `checker_spec`
      alone never fired for the OMITTED-field case (Pydantic skips
      validators for defaulted, unset fields) — verified failing, fixed
      by switching to `model_validator(mode="after")`, re-verified passing,
      with a permanent regression test for exactly this
      (`test_candidate_checker_forbidden_case_requires_checker_spec`).
- [x] 5b. (R33) [COMMIT] Commit step 5 on its own (split from the
      original combined step-7 commit, since step 6 is separate,
      not-yet-done work — one step per invocation, per dr-execute-step).
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.
      DONE — running total: 208 lines (105 + skeleton.py +40 +
      test_informal.py +65 - 2 removed) of 1150. Frozen-surface diff:
      empty. Pushed.
- [x] 6. (R33, M24) Expose the eval-kind CHOICE on
      `ReasoningCandidateProposal`'s wire-facing `counterconditions` (today
      hardcoded to `eval="observation"` in `proposal_envelope`,
      `workloads/text.py:152-161`) — add the narrowest change that lets
      the model declare `program:candidate-checker` for one
      countercondition without changing the field's own wire TYPE
      (`tuple[str, ...]`) if avoidable; if not avoidable, name the exact
      shape change here rather than improvising it at execution time.
      done-when: `python -m pytest tests/test_semantic_freedom_constitution.py -q` -> 0 failed, plus a new case.
      MUST NOT touch: the five frozen surfaces (this file is
      `workloads/text.py`).
      DONE, checklist's own test-file citation confirmed CORRECT this
      time (verified via grep before trusting it, per the last two
      steps' corrections). `counterconditions` itself keeps its wire TYPE
      unchanged (`tuple[str, ...]`) — avoidable, so no contract-version
      bump needed for this piece: added an ADDITIVE, optional
      `checker_specs: tuple[dict | None, ...] = ()` field to
      `ReasoningCandidateProposal`, paired by index (empty/`None` entry
      = `eval="observation"`, unchanged behavior), with a
      `model_validator` enforcing the pairing length. Added the same
      `checker_spec` field + cross-field `model_validator` coupling to
      `Countercondition` (mirroring `ForbiddenCase.checker_spec`'s
      pattern from step 5, using `model_validator` not `field_validator`
      from the start this time — no repeat of that bug). Updated
      `proposal_envelope` to consume the pairing and
      `draft_countercondition_commitments` to thread `checker_spec` into
      the drafted commitment's `budget.extra["spec"]` (same JSON
      convention as `forbidden_commitment`); confirmed `Budget()`'s
      explicit default equals `Commitment`'s own `default_factory=Budget`
      so the no-checker_spec path is byte-for-byte unchanged.
      `python -m pytest tests/test_semantic_freedom_constitution.py -q`
      -> 15 passed (13 pre-existing + 2 new:
      `test_checker_specs_pair_by_index_without_changing_counterconditions_type`,
      `test_checker_specs_must_pair_one_to_one_with_counterconditions`).
      Ring re-run (semantic_freedom + skills_models + live_smoke_regressions
      + conjecturer_turn_v4 + oracle + informal): 115 passed, 0 failed.
- [x] 7. (R33) [COMMIT] Commit step 6 (step 5 already committed at 5b).
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty (same paste as step 4); push confirmed.
      DONE — `git diff --stat f103a03a -- src/ tests/` (base..working
      tree, cumulative): 7 files changed, 299 insertions(+), 5
      deletions(-) -> running total 294 of 1150. Frozen-surface diff
      (`capabilities/state.py`, `harness.py`, `invariants.py`,
      `run_manifest.py`, `qualification.py`): empty. Pushed.

## Protection semantics — the relatedness-claim mechanism (R43-R45, M27)

- [x] 8. (R43, M27, M21) Read `rules/experiment.py::active_properties`
      (the READER whose pattern this mirrors) and `relevance_trial` (the
      challenge shape being reused) once more in full against the
      CURRENT tree, confirming line numbers/behavior are unchanged since
      SPEC.md's own measurement.
      done-when: `sed -n '188,220p' src/deepreason/rules/experiment.py`
      output matches SPEC.md's own quoted text byte-for-byte (paste
      both side by side). MUST NOT touch: rules/experiment.py (read-only
      step).
      DONE — `sed -n '188,220p'` reproduced byte-for-byte SPEC.md's M27
      quotes (docstring lines 189-195, filter block lines 206-212, both
      unchanged at the SAME line numbers) and confirmed `relevance_trial`
      still at line 313 (M21). No drift since SPEC.md was written. No
      file touched other than this checklist; no commit needed for a
      read-only step.
- [x] 9. (R43, M27) Write the small "relatedness claim" artifact-minting
      helper (mirrors `register_fail_warrant`'s own small-nu-artifact
      pattern, D1 census M10) — proposed home: `rules/warrants.py`
      alongside `execution_backed`/`formally_backed`, or a new sibling
      module if `rules/warrants.py`'s own module docstring ("Six sites
      used to hand-build the same triple") suggests this is a
      DIFFERENT concern; decide at execution time by re-reading that
      docstring, do not assume.
      done-when: a new function exists whose signature accepts
      `(harness, conjecture_id, commitment_id, claim_text)` and returns
      the new artifact's id, with a docstring naming which R/M it
      implements.
      DONE — re-read `rules/warrants.py`'s own docstring at execution
      time as instructed: it names the nu/DEMONSTRATIVE-warrant/critic
      TRIPLE specifically ("hand-build the same triple"); a relatedness
      claim has no warrant and no critic, only a plain MENTION-linked
      artifact — a DIFFERENT concern per the docstring's own test, so
      built a new sibling module `rules/relatedness.py` (next to
      `warrants.py`/`experiment.py` in `rules/`) with
      `mint_relatedness_claim(harness, conjecture_id, commitment_id,
      claim_text, *, provenance_role="conjecturer") -> str`, docstring
      naming R43/M27. Verified live:
      `python -c "from deepreason.harness import Harness; from
      deepreason.rules.relatedness import mint_relatedness_claim; ..."`
      -> minted an artifact id, `art.interface.refs ==
      [Ref(target=<conjecture id>, role=RefRole.MENTION)]`.
- [x] 10. (R43, M17, M27) Link the new artifact to the conjecture via
      `Ref(target=conjecture.id, role=RefRole.MENTION)` — reuse the
      EXISTING `RefRole.MENTION` value (M17); do NOT add a new `RefRole`
      enum member (Amendment 1/C7 rejected the twin's own new-`RefRole`
      approach; this design deliberately reuses an existing one instead).
      done-when: `python -c "from deepreason.ontology.artifact import RefRole; assert len(RefRole) == 3"` -> exit 0 (still exactly `DEPENDENCE`/`MENTION`/`EVIDENCE`, no fourth member added).
      DONE — exit 0, `list(RefRole) ==
      [RefRole.DEPENDENCE, RefRole.MENTION, RefRole.EVIDENCE]`, no
      fourth member. `mint_relatedness_claim` (step 9) already wires
      this ref at creation time, so 9 and 10 landed as one
      implementation, verified by each step's own separate done-when.
      No persistent pytest test added yet for `rules/relatedness.py`
      itself — deferred to step 12, where `formally_backed`'s new
      per-commitment check gives this module its first real caller and
      `test_prose_refutation_boundaries.py` its first real coverage
      (SPEC.md's own "Test implications" section owes new cases there,
      not here).
- [x] 11. (R43) [COMMIT] Commit steps 9-10.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.
      DONE — `git diff --stat f103a03a -- src/ tests/` (base..working
      tree, cumulative, including new untracked
      `rules/relatedness.py` once staged): 8 files changed, 348
      insertions(+), 5 deletions(-) -> running total 343 of 1150.
      Frozen-surface diff: empty. Pushed.
- [ ] 12. (R43, M9) Add `formally_backed`'s ONE new per-commitment check
      (rules/warrants.py:61-100 today) — for a commitment of the new
      kind specifically, exclude it from the substantive/backing set
      IFF a linked relatedness-claim artifact exists AND its
      `harness.state.status` is not `Status.ACCEPTED`. No linked claim
      at all (the default) means backing stays intact (F6's opt-out
      shape, R42).
      done-when: `python -m pytest tests/test_prose_refutation_boundaries.py -q` -> 0 failed (every EXISTING case byte-identical) plus a new case proving the exclusion.
      MUST NOT touch: the five frozen surfaces (rules/warrants.py is
      none of them — it is frozen-ADJACENT per SPEC.md's own forecast,
      not literally on the list).
      DONE — added the check gated on `kappa.eval ==
      f"program:{CANDIDATE_CHECKER_PROGRAM}"` (so every other kind is a
      no-op, R-a), reading `rules.relatedness.relatedness_claim_holds`
      (new reader function in that same sibling module, step 9's first
      real caller). New test
      `test_a_challenged_relatedness_claim_strips_only_its_own_commitment`:
      no claim -> protects (opt-out default); claim minted, ACCEPTED ->
      still protects; claim challenged via the SAME ARGUMENTATIVE-warrant
      shape `relevance_trial` already uses (target=claim artifact, not
      the conjecture) -> claim's own Status flips to REFUTED,
      `formally_backed` now False for the conjecture, but the
      CONJECTURE's own Status stays ACCEPTED (R43's "shield falls,
      artifact doesn't", proven literally). Mutation-proved: reverted
      `rules/warrants.py` alone, re-ran the new test -> failed exactly at
      the `formally_backed(...) is False` assertion (`True is False`, the
      shield not falling), confirming the test can fail; restored.
      `python -m pytest tests/test_prose_refutation_boundaries.py -q` ->
      45 passed (44 pre-existing byte-identical + 1 new). One isolated,
      non-reproducing failure was observed mid-edit on an EARLIER,
      unrelated test (`test_formal_backing_covers_the_whole_formal_set...`,
      inside `execution_backed`, a function this step never touches);
      stashing/restoring the exact same diff and re-running 5x plus the
      isolated case all passed — recorded as a one-off environmental
      flake (not reproduced), not a regression, since the diff never
      touches `execution_backed`. Ring re-run
      (prose_refutation_boundaries + oracle + adjudication + properties):
      131 passed, 0 failed.
- [x] 13. (R44) Confirm (do not modify) that `crit_program`
      (rules/crit.py:895-919) already re-evaluates every commitment on
      every cycle it runs — R44 needs zero new code; this step is a
      read-and-cite, not a write.
      done-when: `grep -n "def crit_program" -A 3 src/deepreason/rules/crit.py` output matches D1 census M10's own quote.
      DONE — matches D1 census M10 byte-for-byte (same signature,
      docstring, and first two body lines at the same line number, 895).
- [x] 14. (R45) Confirm (do not modify) that `execution_backed`'s
      `EXEC_PROGRAMS` set (rules/warrants.py, D1 census M9) is NOT
      extended with the new kind — this step is a NEGATIVE check: prove
      the set still has exactly 3 members.
      done-when: `python -c "from deepreason.oracle import EXEC_PROGRAMS; assert EXEC_PROGRAMS == frozenset({'exec_oracle','property_oracle','dataset_oracle'})"` -> exit 0.
      DONE — exit 0, still exactly `{exec_oracle, property_oracle,
      dataset_oracle}`; `candidate_checker` confirmed NOT a member
      (R45, matches oracle.py's own comment at the constant's
      definition).
- [x] 15. (R44, R45) [COMMIT] Commit steps 13-14's own recorded evidence
      (no code change expected; if either check fails, that is a STOP,
      not a step to force green).
      ADAPTED: this checklist entry's own text omits step 12's code
      change (rules/warrants.py + rules/relatedness.py +
      test_prose_refutation_boundaries.py) from its commit scope — a
      planning-time gap, not a tree contradiction (steps 13/14 truly
      added no code, exactly as written). No commit boundary exists
      between step 11 and here, so this step's ACTUAL scope is steps
      12-14 together; committing that way rather than stopping to
      re-plan over a checklist wording gap, per this tranche's own
      precedent for small adaptations (steps 1, 2, 5).
      done-when: diff-budget running total <= 1150 (expect no increase
      from steps 13-14); frozen-surface diff empty; push confirmed.
      DONE — `git diff --stat f103a03a -- src/ tests/` (base..working
      tree, cumulative): 10 files changed, 446 insertions(+), 5
      deletions(-) -> running total 441 of 1150 (steps 13-14 added 0, as
      expected — read-only). Frozen-surface diff: empty. Pushed.

## Item 5 — relatedness challenge call site (R24, R35, F6/R42)

- [x] 16. (R35, M21) Write the new call site reusing `relevance_trial`'s
      own SHAPE (cross-family judge ensemble, referential-integrity +
      unanimity guards) for the narrow question "does this commitment's
      case follow from the claim's own explanation" — targets the NEW
      relatedness-claim artifact (step 9), never the conjecture or the
      commitment directly, mirroring `relevance_trial`'s own
      `target=prop_artifact.id` pattern exactly.
      done-when: a new function exists in `rules/experiment.py` (or a
      sibling module if that file's own scope note argues against it,
      decided at execution time) whose docstring names R24/R35/M21.
      DONE — `rules/experiment.py`'s own scope note ("the system designs
      its own experiments": generators/property proposals) argued
      against it, consistent with step 9's same finding for
      `warrants.py`'s docstring; built `relatedness_trial` in the SAME
      sibling module as steps 9-10/12 (`rules/relatedness.py`), all
      three now co-located as one concern. Docstring names R24/R35/M21
      (verified: `'R24' in doc and 'R35' in doc and 'M21' in doc` ->
      True). Registers an ARGUMENTATIVE fail warrant with
      `target=claim_artifact.id` on anything short of unanimous located
      passes, mirroring `relevance_trial` exactly — never the conjecture
      or the commitment. New file `tests/test_relatedness.py` (4 cases):
      mint+MENTION-link+content shape, opt-out default (no linked
      claim), unanimous pass leaves the claim ACCEPTED with no warrant,
      a losing trial refutes ONLY the claim while the conjecture's own
      Status stays ACCEPTED. Mutation-proved the challenge test: forced
      `relatedness_trial` to always return True without registering a
      warrant -> `test_relatedness_trial_sustained_challenge_refutes_only_the_claim`
      failed exactly at `assert result is False` (`True is False`);
      reverted, re-verified passing.
- [x] 17. (R42, F6) Confirm (do not add machinery for) this call site
      is REACTIVE only — no caller invokes it as a precondition to
      admitting a new commitment; it is invoked only when a critic
      RAISES a relatedness challenge.
      done-when: `grep -rn "<new-function-name>" src/deepreason/` shows
      NO call site inside any admission/compile path
      (`compile_interface_draft`, `rules/conj.py`'s own turn-processing).
      DONE — `grep -rn "relatedness_trial" src/deepreason/` shows
      exactly one hit: the function's own definition
      (`rules/relatedness.py`). No caller anywhere yet (reactive-only
      by construction — nothing invokes it as a precondition; the
      critic-side invocation belongs to a later tranche or the
      operator's own future instruction, not this one).
- [x] 18. (R35) [COMMIT] Commit steps 16-17.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.
      DONE — `git diff --stat f103a03a -- src/ tests/` (base..working
      tree, cumulative): 11 files changed, 618 insertions(+), 5
      deletions(-) -> running total 613 of 1150. Frozen-surface diff:
      empty. Pushed.

## Item 7 — encoder-role delegation (R38, F3-A/R29)

- [x] 19. (R29, M16) Add role `"encoder"` to `GROUP_ROLES["coder"]` in
      `seat_bindings.py` (currently `frozenset({"property_designer"})`)
      — becomes `frozenset({"property_designer", "encoder"})`;
      `property_designer` stays untouched (A1's own boundary).
      done-when: `python -c "from deepreason.seat_bindings import GROUP_ROLES; assert GROUP_ROLES['coder'] == frozenset({'property_designer','encoder'})"` -> exit 0.
      DONE — exit 0, `GROUP_ROLES['coder'] == frozenset({'property_designer', 'encoder'})`.
- [x] 20. (R38) Register role `"encoder"` in `llm/roles.py` (its own
      `ROLES` tuple and/or `TEMPLATES` dict, matching whichever
      registration shape `property_designer` itself already uses — read
      `llm/roles.py:125,314` first, mirror the SAME shape, do not invent
      a new one).
      done-when: `grep -n '"encoder"' src/deepreason/llm/roles.py` shows
      at least one hit in the same dict(s) `property_designer` appears
      in.
      DONE — `property_designer` appears ONLY in `TEMPLATES` (line 125)
      and `COMPACT_TEMPLATES` (line 314), NOT in the top-level `ROLES`
      tuple (that tuple is the SMALLER set of independently-routable
      roles; `roles.py`'s own module comment names `property_designer`-
      style entries as roles reused via `template_role`, not registered
      there). Added `"encoder"` to the SAME two dicts, mirroring
      `property_designer`'s exact shape, and NOT to `ROLES` — consistent
      with reusing its seat rather than adding an independent one (see
      step 21's design choice, which this follows from).
- [x] 21. (R38) Write the two-phase delegation call: when the `"coder"`
      seat is bound (`resolve_seat_bindings_by_group()`, M16), a
      follow-up call to role `"encoder"` drafts commitment source text
      from the ALREADY-ADMITTED conjecture's own prose; when not bound,
      the conjecturer's own turn embeds it inline (Item 2's existing
      fallback, no new code needed for this half).
      done-when: a new function exists whose docstring names R38 and
      whose fallback path is a no-op call to nothing beyond Item 2's own
      inline mechanism.
      DONE, with one load-bearing design finding recorded before
      writing any code: `run_manifest.py::LEGACY_CANONICAL_ROLES` (a
      FROZEN surface 4 tuple) is where a role becomes independently
      routable in the manifest — `property_designer` IS in that tuple,
      but the module's OWN comment (line 52) names roles like
      `experimenter`/`batch_critic` as "auxiliary prompt templates...
      reuse one of these seats and are not independently routable
      roles," via `adapter.call(<canonical-role>, ..., template_role=
      "<auxiliary>")` (`llm/adapter.py:898-900`'s own documented
      pattern; `rules/experiment.py:149` is the live precedent for
      `experimenter` reusing `"conjecturer"`). Amendment 3's grant
      (step 27) authorizes exactly ONE `run_manifest.py` Literal change
      and nothing else there — adding `"encoder"` to
      `LEGACY_CANONICAL_ROLES` would be a SECOND, unauthorized hunk on a
      frozen surface. Designed `"encoder"` the SAME way as
      `experimenter`: `rules/encoding.py::draft_encoded_commitment`
      calls `adapter.call("property_designer", pack, EncoderOutput,
      template_role="encoder")`, reusing `property_designer`'s own
      configured endpoint/routing (both already share
      `GROUP_ROLES["coder"]`, step 19) — ZERO `run_manifest.py` contact
      for this item, better than SPEC.md's own forecast ("a new role
      needs a route/role binding entry"). New `EncoderOutput`/
      `EncoderTestCase` contracts in `llm/contracts.py` (a bare `dict`
      test-case field is REJECTED by the wire firewall — found live,
      `llm/wire.py::_reject_unknown_fields` treats an untyped `dict`'s
      empty `properties: {}` as "no key is ever valid," raising `extra
      field at /tests/0/in`; fixed with an explicit `EncoderTestCase`
      model). New `tests/test_encoding.py` (2 cases: no-op when the
      seat is unbound, delegates and returns the drafted spec when
      bound). Mutation-proved both: forced `has_role` bound-check to
      `if False` -> `test_no_coder_seat_bound_is_a_no_op` failed with a
      real `KeyError` (no endpoint for `property_designer`); reverted,
      re-verified passing. `python -c "'R38' in
      inspect.getdoc(draft_encoded_commitment)"` -> True.
      Ring re-run (encoding + properties + wire_contracts +
      skills_models): 43 passed, 0 failed.
- [x] 22. (R38) [COMMIT] Commit steps 19-21.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.
      DONE — `git diff --stat f103a03a -- src/ tests/` (base..working
      tree, cumulative): 16 files changed, 758 insertions(+), 7
      deletions(-) -> running total 751 of 1150. Frozen-surface diff
      (all five, `run_manifest.py` included): empty. Pushed.

## R-g acceptance checks (Item 6, R36, 7 named tests: 5 original + 2 from Amendment 2)

- [x] 23. (R36) Write all 7 named regression tests from SPEC.md's Item 6
      (rev 2) and its Amendment-2 "New tests owed" list, in ONE step
      (they are one coherent proof, not 7 separable increments —
      splitting them would let a partial pass look like acceptance).
      done-when: `python -m pytest tests/test_prose_refutation_boundaries.py tests/test_oracle.py tests/test_adjudication.py tests/test_properties.py -q -k "R_g or relatedness or candidate_checker"` -> 0 failed, and the 7 named claims are each visibly covered (paste the collected test names).
      DONE — checked existing coverage FIRST rather than writing 7 blind
      new tests (2 of the 7 claims were already proven by earlier
      steps' own tests): claim-by-claim mapping —
      (1) informal-only byte-identical: NEW
      `test_R_g_informal_only_run_replays_byte_identical`
      (test_adjudication.py).
      (2) new-kind commitment FAILS -> refuted like any crit_program
      failure: already proven by step 2-4's own
      `test_crit_program_refutes_a_prose_conjecture_by_running_its_checker`
      (test_oracle.py) — same shape as
      `test_crit_program_refutes_wrong_code_by_running_it`, extended.
      (3) new-kind commitment PASSES -> formally_backed protection: NEW
      `test_candidate_checker_pass_grants_formally_backed_protection`
      (test_oracle.py).
      (4) no new scheduling term reads the new kind: NEW
      `test_R_g_no_scheduling_term_reads_the_candidate_checker_kind`
      (test_oracle.py, grep-provable, D1 M9(a)'s own method).
      (5) relatedness challenge never mutates the CANDIDATE's Status
      directly, only substantive-membership: already proven by step
      12's `test_a_challenged_relatedness_claim_strips_only_its_own_commitment`
      (test_prose_refutation_boundaries.py).
      (6) sustained challenge flips the CLAIM's own Status to REFUTED
      while the CONJECTURE's stays: the SAME test as (5) — both rev-2's
      Item-6 wording and Amendment 2's addition describe the identical
      empirical fact from two angles; recorded honestly as ONE test
      proving both rather than manufacturing a second, redundant one.
      (7) no relatedness claim at all still counts toward
      formally_backed (F6 opt-out): the SAME test's OWN first assertion
      (`formally_backed(...) is True` before any claim is minted),
      reinforced independently by step 16-18's
      `test_no_linked_claim_is_the_opt_out_default` (test_relatedness.py).
      Collected test names for the exact done-when command (6 distinct
      node ids — (2)/(5)/(6)/(7) reuse tests from earlier steps, so
      fewer than 7 NEW names, all 7 CLAIMS covered):
      `test_prose_refutation_boundaries.py::test_a_challenged_relatedness_claim_strips_only_its_own_commitment`,
      `test_oracle.py::test_candidate_checker_reads_source_from_budget_not_content`,
      `test_oracle.py::test_candidate_checker_never_joins_exec_programs`,
      `test_oracle.py::test_candidate_checker_pass_grants_formally_backed_protection`,
      `test_oracle.py::test_R_g_no_scheduling_term_reads_the_candidate_checker_kind`,
      `test_adjudication.py::test_R_g_informal_only_run_replays_byte_identical`
      (6 collected by -k; claim 2's own test doesn't match the keyword
      filter but exists and passes). Full ring (all 4 named files): 134
      passed, 0 failed. Mutation-proved the 3 brand-new checks: (a)
      appended a literal `# candidate_checker` line to scheduler.py ->
      the R-g grep test failed exactly as expected, reverted; (b)
      disabled the relatedness-gated `continue` branch in
      `formally_backed` -> the pass-grants-protection test failed
      (`False is True`), reverted; both re-verified passing after
      restore.
- [x] 24. (R36) [COMMIT] Commit step 23.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.
      DONE — `git diff --stat f103a03a -- src/ tests/` (base..working
      tree, cumulative): 17 files changed, 815 insertions(+), 7
      deletions(-) -> running total 808 of 1150. Frozen-surface diff:
      empty. Pushed.

## Map document (CON-conjecture-kinds.md v2)

- [x] 25. (all) Update `docs/map/CON-conjecture-kinds.md` in the SAME
      commit as the behavior it now describes would normally land (per
      CLAUDE.md's own rule) — since this checklist batches the map
      update as its own late step by necessity (dr-plan-steps plans,
      dr-execute-step lands code across many prior steps), this step's
      own done-when requires EVERY new `check:` line to be individually
      verified passing BEFORE commit, per this tranche's own D1
      precedent.
      done-when: `python tools/docs_verify.py` reports 0 failed
      including every new check in this document.
      DONE, with a real blast radius found and fixed, not just
      CON-conjecture-kinds.md v2: updated it (new Owns: entries for
      `rules/relatedness.py`/`rules/encoding.py`, a new prose section
      naming the kind/relatedness/encoder mechanisms with 5 new checks,
      2 new "Where it lives" rows, 3 new "Where to change what" rows,
      3 new Traps entries — wire-firewall dict rejection,
      run_manifest.py CANONICAL_ROLES-is-frozen precedent, the
      field_validator-skip-on-default bug). Running the FULL sweep
      surfaced that this tranche's own code (2 new `rules/` modules, a
      3rd/4th import on `formally_backed`, 3 new `Warrant()`/`Provenance()`
      mints, 2 new `adapter.call` sites) broke 12 OTHER map documents'
      numeric/set assertions that were counting exactly what changed —
      re-derived and fixed every one, each verified individually before
      the next full sweep: `CON-seats.md` (.call( count 43->45),
      `SEAM-adjudication-x-rules.md` (Warrant() count 2->3;
      state.status readers +relatedness.py), `SEAM-evaluation-x-ontology.md`
      (oracle.py sha256_hex count 6->7, "eight mint sites"->"nine"),
      `SEAM-evaluation-x-rules.md` (formally_backed's import set +2;
      WarrantType.ARGUMENTATIVE count 5->6; register_fail_warrant FILE
      count check tightened to anchor on the call, not a bare docstring
      mention, since `relatedness.py`'s own prose citing the name had
      inflated the loose count from 8 to 9 while true callers stayed 8),
      `SEAM-llm-x-rules.md` (rules<->llm coupling counts +2 files/+2
      call sites), `SEAM-ontology-x-rules.md` (create_artifact count
      12->15; Provenance() count (5,14)->(5,17)),
      `SEAM-rules-x-workflow.md` (rules/ submodule count 12->14;
      adapter.call unbound-site set +2, documented as DORMANT —
      confirmed zero callers anywhere in `src/` for either new
      function, a stronger property than the existing 4 sites'
      "deferred under v6" story). Also found (via the full sweep, NOT
      anticipated by the checklist): `tests/test_signals.py`'s AST scan
      caught two unregistered `record_llm_calls` tags this tranche
      introduced (`"encoder-delegation"`, `"relatedness-trial"`) —
      registered both in `src/deepreason/signals.py` with real
      documentation, a genuine gap this tranche caused, not merely a
      stale count. Residual: 2 failures
      (`SUB-application.md:208`/`:239`), both tracing to the SAME
      pre-existing `test_continuation.py` defect — confirmed
      byte-identically reproducing on a fresh worktree at this
      tranche's own base commit `f103a03a`, with an empty diff for
      every file that test's own machinery touches; recorded as
      `PARKED.md` P-D2-1, matching CLAUDE.md's own "S6 PARKED P1/P3"
      shorthand for this recurring defect class. Final
      `python tools/docs_verify.py`: `docs_verify: 2 failed` (both
      PARKED, zero new).
- [x] 26. (all) [COMMIT] Commit step 25.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.
      DONE — `git diff --stat f103a03a -- src/ tests/` (base..working
      tree, cumulative): 18 files changed, 823 insertions(+), 7
      deletions(-) -> running total 816 of 1150 (docs/ and PARKED.md
      not counted against the code budget, per this tranche's own
      convention). Frozen-surface diff: empty. Pushed.

## STOP gate — the contract-version question (frozen surface 4, C10)

- [ ] 27. (R47, C10) **STOP, do not execute past this point without
      fresh operator words.** This tranche's own measurement
      (`run_manifest.py::ContractVersionPolicyV3.conjecturer_turn_contract`
      is a hardcoded `Literal["conjecturer.turn.v6"]`) shows that
      REGISTERING the new wire-schema shape as a distinct, qualifiable
      contract version — the convention every prior schema change in
      this codebase has followed (v4->v5->v6), needed so qualification
      (surface 5) does not silently certify a model against a schema it
      was never tested on — REQUIRES editing this exact `Literal`, a
      genuine touch to `run_manifest.py` (frozen surface 4). This
      directly contradicts "zero frozen-surface diff expected" for this
      ONE piece of work specifically (every other step above avoids all
      five surfaces). Steps 1-26 above do NOT depend on this — they are
      buildable and testable with the new eval kind reachable only
      through `informal/skeleton.py`'s existing schema-version-agnostic
      convention (a JSON-content shape, not a wire-contract version)
      and the reasoning path's `counterconditions` field (step 6, also
      not itself contract-version-gated in the same way). Whether to (a)
      accept this one frozen-surface contact explicitly, (b) defer the
      new-contract-version work to its own future tranche with its own
      authorization request, or (c) find a third option this measurement
      missed, is the operator's decision, not this checklist's.
      done-when: the operator's words are recorded in REQUEST.md as
      Amendment 3 before any further step in this section is planned or
      executed.
      DONE — Amendment 3 recorded in REQUEST.md (verified:
      `grep -n "Amendment 3" REQUEST.md` shows the heading and the
      standing-constraints section). Per the amendment's own words
      ("at step 27 you may make... exactly the contract-version
      registration change") and the operator's follow-up ("Step 27's
      done-when is satisfied by this amendment"), executed the scoped
      edit as part of this step: in `run_manifest.py`'s
      `ContractVersionPolicyV3`, widened
      `conjecturer_turn_contract: Literal["conjecturer.turn.v6"] =
      "conjecturer.turn.v6"` to
      `Literal["conjecturer.turn.v6", "conjecturer.turn.v7"] =
      "conjecturer.turn.v6"` — additive, default UNCHANGED, so every
      existing committed root's manifest keeps validating and
      replaying byte-for-byte (R-a); v7 is opt-in only. Chose a
      WIDENED Literal over a straight replace (V2->V3's own shape)
      specifically because a straight replace to
      `Literal["conjecturer.turn.v7"]` alone would REJECT every
      existing v6 manifest on load — verified this reasoning against
      `test_conjecturer_turn_v4.py`'s own live assertion that a v6
      turn's `attempt_trace` contract_id is exactly
      `{"conjecturer.turn.v6"}` (unchanged default), not a broken
      replay. `git diff src/deepreason/run_manifest.py` shows EXACTLY
      one hunk, this one Literal, nothing else — no change to manifest
      identity or digest functions. `python -c "from deepreason.run_manifest
      import ContractVersionPolicyV3; d=ContractVersionPolicyV3();
      assert d.conjecturer_turn_contract=='conjecturer.turn.v6';
      v7=ContractVersionPolicyV3(conjecturer_turn_contract='conjecturer.turn.v7');
      assert v7.conjecturer_turn_contract=='conjecturer.turn.v7'"` ->
      OK. `python -m pytest tests/test_wire_contracts.py
      tests/test_conjecturer_turn_v4.py
      tests/test_v6_patch_repair_and_wire.py
      tests/test_schema_carries_every_prose_rule.py -q` -> 75 passed,
      0 failed.

## Qualification-digest consequences (its own step, R47)

- [x] 28. (R47) IF Amendment 3 authorizes surface-4 contact (step 27):
      after the contract-version bump lands, run
      `qualification_subject_payload` against BOTH the old and new
      manifest shapes and confirm (a) the OLD digest is unchanged (old
      cached qualifications remain valid) and (b) the NEW digest
      differs (new runs requalify) — this is a MEASUREMENT step, no
      code change, isolated so the consequence is visible on its own
      line rather than buried inside step 27's own commit.
      DONE, with one finding worth stating plainly: (b) is not a "two
      hashes differ" measurement — it is a TYPED REFUSAL, and that is
      the STRONGER, correct proof for a registration-only grant.
      (a) OLD DIGEST UNCHANGED — pasted evidence, a REAL committed v6
      root (`experiments/live_engaged_2026-07-27/run-f4fa6663.../
      run-manifest.json`), same fixed test profile, digest computed
      PRE-EDIT (temporarily restored `run_manifest.py` to
      `f103a03a`'s own copy) vs POST-EDIT (this step's own change):
        PRE-EDIT digest:  07e7227680633f8dccb416f13ab79a736a24e99205deb301636443d8c1476aa3
        POST-EDIT digest: 07e7227680633f8dccb416f13ab79a736a24e99205deb301636443d8c1476aa3
      Byte-identical. `run_manifest.py` restored to its post-step-27
      state immediately after (`git diff` shows the single intended
      hunk, confirmed).
      (b) NEW DIGEST — attempted the literal ask (build a
      `RunManifest` with `conjecturer_turn_contract="conjecturer.turn.v7"`
      from the SAME real committed manifest, mutated) and it does NOT
      produce a second, merely-different digest: it raises
      `V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED at
      /contract_schema_repair_policy/grants: contract
      conjecturer.turn.v7 lacks exact repair authority` — a pydantic
      `model_validator` on `RunManifest` ITSELF (not just
      `compile_run_manifest`), so even direct `RunManifest.model_validate`
      refuses. This is EXACTLY the intended consequence of a
      registration-only grant (Amendment 3/C11/C12 scope): the Literal
      now RECOGNIZES `"conjecturer.turn.v7"` as a syntactically valid
      value (pydantic gets past the type check), but wiring it to a
      real repair-authority grant is a SEPARATE `run_manifest.py` hunk
      this amendment explicitly does not authorize ("any additional
      run_manifest.py hunk is a stop, not a judgment call"; C11: "does
      not authorize touching... qualification.py at all"). No
      digest can be computed for a v7 manifest AT ALL yet — stronger
      than "differs," it is TYPE-REFUSED, so nothing can silently
      qualify a model against the untested v7 schema (the exact R47
      safety property this registration exists to protect). This
      residual wiring is explicitly future-tranche work, named here so
      it isn't silently assumed done.
      No code change this step (pure measurement); `run_manifest.py`
      touched only transiently to compute the PRE-EDIT digest, restored
      immediately, confirmed via `git diff` before moving on.
      done-when: two pasted `qualification_subject_digest(...)` outputs,
      old != new, old matches the digest recorded on an existing
      committed root using `conjecturer.turn.v6` unmodified.

## Full gate and final cleanliness

- [x] 29. (all) Map check: `python tools/docs_verify.py` and
      `python tools/docs_verify.py --audit` and
      `python tools/docs_verify.py --links`.
      done-when: 0 failed, 0 findings, 0 dangling (paste all three).
      DONE —
      `python tools/docs_verify.py` -> `docs_verify: 2 failed`, both
      `SUB-application.md:208`/`:239`, both `test_continuation.py`'s
      SAME pre-existing defect (PARKED.md P-D2-1, confirmed reproducing
      at this tranche's own base commit `f103a03a`) — zero NEW
      failures from this tranche's own 26 prior steps' worth of code.
      `python tools/docs_verify.py --audit` ->
      `docs_verify --audit: 0 finding(s)`.
      `python tools/docs_verify.py --links` ->
      `docs_verify --links: 0 dangling reference(s), 53 document(s)`.
- [x] 30. (all) Full gate: `python -m pytest tests/ -q -n 4`.
      done-when: output ends "N passed, M failed" (paste it verbatim);
      any failure is read against this tranche's own PARKED.md
      pre-existing-failure ledger (P1: `test_module_fingerprints`; P2:
      `test_continuation`, both from D1) before being called a
      regression.
      DONE, with ONE real regression found and fixed, three confirmed
      pre-existing. First run:
      `4 failed, 3398 passed, 7 skipped in 750.16s (0:12:30)` —
      `test_bronze_report.py::test_census_totals_internally_consistent`,
      `test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`,
      `test_seat_bindings.py::test_resolve_seat_bindings_expands_group_to_its_role_set`,
      `test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`.
      Checked each against the tree BEFORE calling any of them a
      regression (this tranche's own worked discipline, not the
      checklist's pre-populated P1/P2 guess alone — the guess named 2,
      the gate found 4):
      - `test_seat_bindings.py::test_resolve_seat_bindings_expands_group_to_its_role_set`
        — REAL REGRESSION, found and fixed. Step 19 widened
        `GROUP_ROLES["coder"]` to `{"property_designer", "encoder"}`;
        this test's own stale assertion (`set(resolved) ==
        {"property_designer"}`) was written before that step landed.
        Fixed the assertion to `{"property_designer", "encoder"}` plus
        an explicit check that `"encoder"` resolves to the same bound
        profile — the CORRECT, intended behavior this tranche's own
        Item 7 design produces, not a weakening.
      - `test_continuation.py::...` (P2) and
        `test_module_fingerprints.py::...` (P1) — both CONFIRMED
        pre-existing at base commit `f103a03a`, matching the
        checklist's own pre-populated guess; P1 additionally recorded
        as `PARKED.md` P-D2-2 (it hadn't been separately ledgered yet).
      - `test_bronze_report.py::test_census_totals_internally_consistent`
        — a THIRD pre-existing failure the checklist's own P1/P2 guess
        did not anticipate (159 vs 165 `gate_measures`/`gate_blocked`
        mismatch in a forensic report over RETAINED historical roots,
        `experiments/bronze_flat_2026-07-13/`) — confirmed reproducing
        byte-identically at `f103a03a`, unrelated to anything this
        tranche touched. Recorded as `PARKED.md` P-D2-3.
      Re-run after the ONE real fix (full gate, not a partial ring, to
      honor the same discipline as the first run):
      `3 failed, 3399 passed, 7 skipped in 757.94s (0:12:37)` — exactly
      the 3 confirmed-pre-existing failures
      (`test_bronze_report.py::test_census_totals_internally_consistent`,
      `test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`,
      `test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
      — PARKED.md P-D2-3/P-D2-1/P-D2-2), zero new. This tranche's own
      net contribution: 3398 -> 3399 passed (the one real fix), 4
      failed -> 3 failed (that same fix), same 3 pre-existing failures
      before and after.
- [x] 31. (all) [COMMIT] Final push and clean-tree confirmation.
      done-when: `git status --porcelain` is empty AND
      `git log --oneline -1 origin/claude/pipeline-design-d2` matches
      local HEAD; total diff-budget across the whole tranche pasted
      one final time against the 1150-line ceiling (or the ceiling as
      revised by Amendment 3, if step 27 changed scope).
      DONE — `git status --porcelain` empty (nothing pending; step 30's
      own commit already left the tree clean, no separate commit
      needed here). Local HEAD `a5c7bffe` == remote
      `origin/claude/pipeline-design-d2` HEAD `a5c7bffe` (both pasted,
      identical). Final `git diff --stat f103a03a -- src/ tests/`: 20
      files changed, 833 insertions(+), 9 deletions(-) -> 824 net
      lines against the 1150-line ceiling (unrevised — Amendment 3
      scoped surface-4 contact only, never the code budget). Frozen-
      surface diff, final: `run_manifest.py` only, 9 lines (8
      insertions, 1 deletion) — exactly step 27's one authorized hunk,
      nothing else on any of the five surfaces across the whole
      tranche.

## Amendments

### Amendment 4 (post-validation operator correction: pure-code conjectures must mechanically fail)

Steps 32+ below implement SPEC.md's Revision 3 (REQUEST.md's Amendment
4). Map ids: DR-SEAM-evaluation-x-ontology (programs.py,
informal/skeleton.py), DR-SUB-evaluation (programs.py, informal/),
DR-SUB-periphery (workloads/text.py), DR-CON-conjecture-kinds. Diff-
budget ceiling for this amendment: 175 lines (SPEC.md Revision 3's own
computed sum), tracked against `git diff --stat b84b69e4..HEAD -- src/
tests/` (b84b69e4 = Revision 3's own SPEC.md commit, the base for this
amendment's own budget — separate from, and additional to, the main
tranche's 1150-line ceiling already closed at step 31). Frozen-surface
diff MUST stay EMPTY for this amendment — no grant this time, any hunk
on the five surfaces is a STOP.

- [ ] 32. (Item 8, M30) Add `is_pure_code(text: str) -> bool` to
      `programs.py`, implementing exactly M30's measured design (AST
      parse; empty/unparseable -> False; single bare string-literal
      expression -> False; every top-level statement one of
      FunctionDef/AsyncFunctionDef/ClassDef/Import/ImportFrom -> True;
      anything else -> False). Add direct unit tests covering all 6 of
      M30's own prototyped cases (pure function, real prose, bare
      docstring, mixed prose+code, import+def, bare class) plus the
      bare-assignment-sequence case proving A6's own narrow-scope
      choice (assignments alone do NOT trip it).
      done-when: `python -m pytest tests/test_programs.py -k is_pure_code -q` -> all new cases pass, 0 failed. MUST NOT touch: the
      five frozen surfaces (this file is `programs.py`, none of them).
      DONE — new `tests/test_programs.py` (no prior file existed) with
      8 cases (M30's own 6 plus the bare-assignment case from A6, plus
      an empty-content case). `python -m pytest tests/test_programs.py
      -k is_pure_code -q` -> 8 passed. Mutation-proved: replaced the
      final `return all(...)` with `return False` -> 3 of 8 tests
      correctly failed (the three TRUE-positive rejection cases);
      reverted, re-verified 8 passed. Ring re-run (test_programs +
      test_oracle + test_informal): 75 passed, 0 failed.
- [x] 33. (Item 8) [COMMIT] Commit step 32.
      done-when: diff-budget running total <= 175; frozen-surface diff
      empty; push confirmed.
      DONE — `git diff --stat b84b69e4 -- src/ tests/`: 2 files
      changed, 80 insertions(+) -> running total 80 of 175. Frozen-
      surface diff: empty. Pushed.
- [ ] 34. (Item 8, M28) Extend `workloads/text.py::reasoning_wf_program`
      to call `is_pure_code` against `envelope.claim` and
      `envelope.mechanism`, failing (with a clear error message naming
      which field) if either trips it. Add 4 tests to
      `tests/test_workload_text.py`: a pure-code claim is refuted when
      run through `crit_program` on a live-shaped artifact; a
      prose-with-code-fragment claim still passes (R57(a)'s protected
      case); a docstring-only claim still passes; an existing
      reasoning-workload fixture (any one already in the suite) is
      confirmed unaffected (byte-identical pass verdict before and
      after this step, mutation-checked by temporarily reverting and
      confirming the new tests fail).
      done-when: `python -m pytest tests/test_workload_text.py tests/test_semantic_freedom_constitution.py -q` -> 0 failed, 4 new cases visible in the collected list. MUST NOT touch: the five
      frozen surfaces (this file is `workloads/text.py`).
      DONE — checklist's own "4 tests... a pure-code claim is refuted
      when run through crit_program" wording adapted at execution
      time: called `reasoning_wf_program` directly (the same function
      `programs.evaluate`/`crit_program` dispatch to) rather than
      building a full harness+artifact+crit_program round-trip,
      matching this file's OWN existing test style
      (`test_reasoning_envelope_checks_form_not_truth` already tests
      the sibling `_reasoning_envelope_wf` the same direct way). 4
      cases: pure-code CLAIM fails naming "claim" in the error;
      pure-code MECHANISM fails naming "mechanism" (proving both
      fields checked independently, not just claim); prose quoting
      code inline still passes (R57(a)); a bare-docstring claim still
      passes. `python -m pytest tests/test_workload_text.py
      tests/test_semantic_freedom_constitution.py -q` -> 24 passed (4
      new + 20 existing, 0 regressions). Mutation-proved: replaced the
      field-loop range with `()` (no-op) -> the 2 true-positive tests
      failed correctly; reverted, confirmed the pre-existing map check
      on `reasoning_wf_program`'s own signature/attribute-access shape
      (`SEAM-evaluation-x-ontology.md:54`) still passes unchanged.
- [x] 35. (Item 8) [COMMIT] Commit step 34.
      done-when: diff-budget running total <= 175; frozen-surface diff
      empty; push confirmed.
      DONE — `git diff --stat b84b69e4 -- src/ tests/`: 4 files
      changed, 137 insertions(+) -> running total 137 of 175. Frozen-
      surface diff: empty. Pushed.
- [ ] 36. (Item 8, M28) Extend `informal/skeleton.py::skeleton_wf_program`
      to call `is_pure_code` against `skeleton.claim` and
      `skeleton.mechanism`, mirroring step 34's exact shape and error-
      message convention. Add the same 4 test cases (adapted to the
      skeleton shape) to `tests/test_informal.py`.
      done-when: `python -m pytest tests/test_informal.py -q` -> 0
      failed, 4 new cases visible in the collected list. MUST NOT
      touch: the five frozen surfaces (this file is
      `informal/skeleton.py`).
- [ ] 37. (Item 8) [COMMIT] Commit step 36.
      done-when: diff-budget running total <= 175; frozen-surface diff
      empty; push confirmed.
- [ ] 38. (Item 8, map) Update `docs/map/CON-conjecture-kinds.md`'s own
      dual-mode section (added earlier in this same tranche) to name
      this new mechanical check — one new sentence/paragraph plus one
      new `check:` line proving a pure-code claim is refuted through
      each of the two extended programs. Re-run `python
      tools/docs_verify.py` before committing (every new check verified
      individually first, per this tranche's own established
      discipline).
      done-when: `python tools/docs_verify.py` reports 0 failed
      including the new check in this document.
- [ ] 39. (Item 8) [COMMIT] Commit step 38.
      done-when: diff-budget running total <= 175; frozen-surface diff
      empty; push confirmed.
- [ ] 40. (all) Blast-radius ring: run every file SPEC.md Revision 3's
      own census named as EXPECTED TO MOVE ONLY IF / MUST NOT MOVE:
      `python -m pytest tests/test_workload_text.py tests/test_replay_reasoning.py
      tests/test_runtime_workload_integration.py tests/test_verify_workload_roots.py
      tests/test_v6_three_root_concurrency.py tests/test_semantic_freedom_constitution.py
      tests/test_workflow_shadow_c0.py tests/test_informal.py tests/test_security.py
      tests/test_trial_accounting.py tests/test_candidate_compilation.py tests/test_guards.py -q`.
      done-when: 0 failed — every MUST-NOT-MOVE prediction confirmed
      true in practice, not just in the census's own forecast.
- [ ] 41. (all) Map check: `python tools/docs_verify.py` and `python
      tools/docs_verify.py --audit` and `python tools/docs_verify.py --links`.
      done-when: 0 failed, 0 findings, 0 dangling (paste all three).
- [ ] 42. (all) Full gate: `python -m pytest tests/ -q -n 4`.
      done-when: output ends "N passed, M failed" (paste it verbatim);
      any failure read against PARKED.md's existing P-D2-1/2/3 ledger
      before being called a regression — expect exactly those 3 and no
      more.
- [ ] 43. (all) [COMMIT] Final push and clean-tree confirmation.
      done-when: `git status --porcelain` is empty AND `git log
      --oneline -1 origin/claude/pipeline-design-d2` matches local
      HEAD; total diff-budget for this amendment pasted one final time
      against the 175-line ceiling.
