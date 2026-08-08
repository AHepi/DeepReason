# Checklist for: dual-mode conjecture — Rung D2 design, rev 2 corrected (Amendment 1 + 2)
State: next=8 blockers=none
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

- [ ] 8. (R43, M27, M21) Read `rules/experiment.py::active_properties`
      (the READER whose pattern this mirrors) and `relevance_trial` (the
      challenge shape being reused) once more in full against the
      CURRENT tree, confirming line numbers/behavior are unchanged since
      SPEC.md's own measurement.
      done-when: `sed -n '188,220p' src/deepreason/rules/experiment.py`
      output matches SPEC.md's own quoted text byte-for-byte (paste
      both side by side). MUST NOT touch: rules/experiment.py (read-only
      step).
- [ ] 9. (R43, M27) Write the small "relatedness claim" artifact-minting
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
- [ ] 10. (R43, M17, M27) Link the new artifact to the conjecture via
      `Ref(target=conjecture.id, role=RefRole.MENTION)` — reuse the
      EXISTING `RefRole.MENTION` value (M17); do NOT add a new `RefRole`
      enum member (Amendment 1/C7 rejected the twin's own new-`RefRole`
      approach; this design deliberately reuses an existing one instead).
      done-when: `python -c "from deepreason.ontology.artifact import RefRole; assert len(RefRole) == 3"` -> exit 0 (still exactly `DEPENDENCE`/`MENTION`/`EVIDENCE`, no fourth member added).
- [ ] 11. (R43) [COMMIT] Commit steps 9-10.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.
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
- [ ] 13. (R44) Confirm (do not modify) that `crit_program`
      (rules/crit.py:895-919) already re-evaluates every commitment on
      every cycle it runs — R44 needs zero new code; this step is a
      read-and-cite, not a write.
      done-when: `grep -n "def crit_program" -A 3 src/deepreason/rules/crit.py` output matches D1 census M10's own quote.
- [ ] 14. (R45) Confirm (do not modify) that `execution_backed`'s
      `EXEC_PROGRAMS` set (rules/warrants.py, D1 census M9) is NOT
      extended with the new kind — this step is a NEGATIVE check: prove
      the set still has exactly 3 members.
      done-when: `python -c "from deepreason.oracle import EXEC_PROGRAMS; assert EXEC_PROGRAMS == frozenset({'exec_oracle','property_oracle','dataset_oracle'})"` -> exit 0.
- [ ] 15. (R44, R45) [COMMIT] Commit steps 13-14's own recorded evidence
      (no code change expected; if either check fails, that is a STOP,
      not a step to force green).
      done-when: diff-budget running total <= 1150 (expect no increase
      from steps 13-14); frozen-surface diff empty; push confirmed.

## Item 5 — relatedness challenge call site (R24, R35, F6/R42)

- [ ] 16. (R35, M21) Write the new call site reusing `relevance_trial`'s
      own SHAPE (cross-family judge ensemble, referential-integrity +
      unanimity guards) for the narrow question "does this commitment's
      case follow from the claim's own explanation" — targets the NEW
      relatedness-claim artifact (step 9), never the conjecture or the
      commitment directly, mirroring `relevance_trial`'s own
      `target=prop_artifact.id` pattern exactly.
      done-when: a new function exists in `rules/experiment.py` (or a
      sibling module if that file's own scope note argues against it,
      decided at execution time) whose docstring names R24/R35/M21.
- [ ] 17. (R42, F6) Confirm (do not add machinery for) this call site
      is REACTIVE only — no caller invokes it as a precondition to
      admitting a new commitment; it is invoked only when a critic
      RAISES a relatedness challenge.
      done-when: `grep -rn "<new-function-name>" src/deepreason/` shows
      NO call site inside any admission/compile path
      (`compile_interface_draft`, `rules/conj.py`'s own turn-processing).
- [ ] 18. (R35) [COMMIT] Commit steps 16-17.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.

## Item 7 — encoder-role delegation (R38, F3-A/R29)

- [ ] 19. (R29, M16) Add role `"encoder"` to `GROUP_ROLES["coder"]` in
      `seat_bindings.py` (currently `frozenset({"property_designer"})`)
      — becomes `frozenset({"property_designer", "encoder"})`;
      `property_designer` stays untouched (A1's own boundary).
      done-when: `python -c "from deepreason.seat_bindings import GROUP_ROLES; assert GROUP_ROLES['coder'] == frozenset({'property_designer','encoder'})"` -> exit 0.
- [ ] 20. (R38) Register role `"encoder"` in `llm/roles.py` (its own
      `ROLES` tuple and/or `TEMPLATES` dict, matching whichever
      registration shape `property_designer` itself already uses — read
      `llm/roles.py:125,314` first, mirror the SAME shape, do not invent
      a new one).
      done-when: `grep -n '"encoder"' src/deepreason/llm/roles.py` shows
      at least one hit in the same dict(s) `property_designer` appears
      in.
- [ ] 21. (R38) Write the two-phase delegation call: when the `"coder"`
      seat is bound (`resolve_seat_bindings_by_group()`, M16), a
      follow-up call to role `"encoder"` drafts commitment source text
      from the ALREADY-ADMITTED conjecture's own prose; when not bound,
      the conjecturer's own turn embeds it inline (Item 2's existing
      fallback, no new code needed for this half).
      done-when: a new function exists whose docstring names R38 and
      whose fallback path is a no-op call to nothing beyond Item 2's own
      inline mechanism.
- [ ] 22. (R38) [COMMIT] Commit steps 19-21.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.

## R-g acceptance checks (Item 6, R36, 7 named tests: 5 original + 2 from Amendment 2)

- [ ] 23. (R36) Write all 7 named regression tests from SPEC.md's Item 6
      (rev 2) and its Amendment-2 "New tests owed" list, in ONE step
      (they are one coherent proof, not 7 separable increments —
      splitting them would let a partial pass look like acceptance).
      done-when: `python -m pytest tests/test_prose_refutation_boundaries.py tests/test_oracle.py tests/test_adjudication.py tests/test_properties.py -q -k "R_g or relatedness or candidate_checker"` -> 0 failed, and the 7 named claims are each visibly covered (paste the collected test names).
- [ ] 24. (R36) [COMMIT] Commit step 23.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.

## Map document (CON-conjecture-kinds.md v2)

- [ ] 25. (all) Update `docs/map/CON-conjecture-kinds.md` in the SAME
      commit as the behavior it now describes would normally land (per
      CLAUDE.md's own rule) — since this checklist batches the map
      update as its own late step by necessity (dr-plan-steps plans,
      dr-execute-step lands code across many prior steps), this step's
      own done-when requires EVERY new `check:` line to be individually
      verified passing BEFORE commit, per this tranche's own D1
      precedent.
      done-when: `python tools/docs_verify.py` reports 0 failed
      including every new check in this document.
- [ ] 26. (all) [COMMIT] Commit step 25.
      done-when: diff-budget running total <= 1150; frozen-surface diff
      empty; push confirmed.

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

## Qualification-digest consequences (its own step, R47)

- [ ] 28. (R47) IF Amendment 3 authorizes surface-4 contact (step 27):
      after the contract-version bump lands, run
      `qualification_subject_payload` against BOTH the old and new
      manifest shapes and confirm (a) the OLD digest is unchanged (old
      cached qualifications remain valid) and (b) the NEW digest
      differs (new runs requalify) — this is a MEASUREMENT step, no
      code change, isolated so the consequence is visible on its own
      line rather than buried inside step 27's own commit.
      done-when: two pasted `qualification_subject_digest(...)` outputs,
      old != new, old matches the digest recorded on an existing
      committed root using `conjecturer.turn.v6` unmodified.

## Full gate and final cleanliness

- [ ] 29. (all) Map check: `python tools/docs_verify.py` and
      `python tools/docs_verify.py --audit` and
      `python tools/docs_verify.py --links`.
      done-when: 0 failed, 0 findings, 0 dangling (paste all three).
- [ ] 30. (all) Full gate: `python -m pytest tests/ -q -n 4`.
      done-when: output ends "N passed, M failed" (paste it verbatim);
      any failure is read against this tranche's own PARKED.md
      pre-existing-failure ledger (P1: `test_module_fingerprints`; P2:
      `test_continuation`, both from D1) before being called a
      regression.
- [ ] 31. (all) [COMMIT] Final push and clean-tree confirmation.
      done-when: `git status --porcelain` is empty AND
      `git log --oneline -1 origin/claude/pipeline-design-d2` matches
      local HEAD; total diff-budget across the whole tranche pasted
      one final time against the 1150-line ceiling (or the ceiling as
      revised by Amendment 3, if step 27 changed scope).

## Amendments
(none yet — re-planning after a validation failure or a frozen-surface
STOP appends here, never rewrites checked steps above)
