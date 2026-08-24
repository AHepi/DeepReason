# CHECKLIST — Rung 6

State: **step 7 next**
Authority: `SPEC.md` items S1-S9; `REQUEST.md` R1-R7, N1-N3, G1-G8.
Rule: one step per `dr-execute-step` invocation; a step is done only when
its done-criterion output is PASTED below it.
Diff ceiling for `tools/diff_budget.py` at each `[COMMIT]`: **560**
production lines over `src/`.

---

- [x] **1. The departure claim body** (S2)
  Add `poietic.departure-declaration.v1` to `CLAIM_SCHEMAS` and
  `_IMPLEMENTED`; add `DEPARTURE_DECLARATION_V1` and
  `DepartureDeclarationV1` with its validator.
  Done-criterion: `python -m pytest tests/test_calculus_claim_substrate.py
  tests/test_proof_debt.py -q` — green, with the predicted
  `len(CLAIM_SCHEMAS) == 10` fixture update and nothing else changed.

- [x] **2. The compiler rule and its two mentions** (S3, R4)
  `compile_interface` handles `DepartureDeclarationV1` → two MENTIONs,
  no dependence.
  Done-criterion: a pasted `python -c` showing the compiled interface's
  ref roles are exactly `{(subject, mention), (departing, mention)}`.

- [x] **3. Well-formedness program and registration** (S4)
  `calculus/programs.py` commitment + `departure_declaration_wf`;
  `programs.py` `_departure_declaration_wf` + `"structural"` ProgramSpec.
  Done-criterion: `python -m pytest tests/test_calculus_claim_substrate.py
  -q` green, plus a pasted evaluation returning `pass` on a well-formed
  body and `fail` on a mis-registered one.

- [x] **4. The authoring operation** (S5) `[COMMIT]`
  `operations.file_departure_declaration`, idempotent by content address.
  Done-criterion: pasted transcript registering one declaration twice and
  getting one artifact; `python -m pytest tests/test_calculus*.py -q`.
  Then commit: claim substrate half of the departure protocol.

- [x] **5. `calculus/render.py`** (S1) — the frame render layer
  Every symbol in SPEC.md S1's table. Writes nothing; imports no seat.
  Done-criterion: `python -c` printing a rendered slice for a framed
  problem and `None` for an unframed one, pasted.

- [x] **6. Regression tests for the slice** (A1, A3, A10, A11)
  `tests/test_frame_render.py`: digest + attackers render, out-of-scope
  renders nothing, departure directive present, byte-identical across
  renders, no provenance-shaped slot.
  Done-criterion: the four tests pass; each is shown RED first by a
  one-line mutation, pasted.

- [ ] **7. Pack sections** (S6.1) `[COMMIT]`
  `frame_slice_context` on both renderers; one non-droppable,
  compressible `frame-slice` section each.
  Done-criterion: `python -m pytest tests/test_pack_ir.py
  tests/test_pack_prefix.py tests/test_frame_render.py -q` green; the
  section-slot census (16 / 12) pasted. Then commit with the
  `DR-CON-packs-and-token-economy` census check updated in the SAME
  commit.

- [ ] **8. The drop disclosure** (S6.2, S6.3, R6, G7)
  `DISCLOSED_ON_DROP` + the bounded fixed-point loop in
  `_allocate_sections`.
  Done-criterion: A7's test passes; a pasted demonstration that a
  budget which drops `citable-evidence-blocks` produces a pack naming it
  withheld; and a pasted argument-by-measurement that the loop converges
  in ≤2 passes on the real renderers.

- [ ] **9. The two call sites** (S7) `[COMMIT]`
  `rules/conj.py` and `rules/crit.py` compute and pass the slice.
  Done-criterion: `python -m pytest tests/test_pack_prefix.py
  tests/test_crit_batch.py tests/test_harness_fixes.py
  tests/test_frame_render.py -q` green. Then commit with
  `DR-SEAM-llm-x-rules` and the NEW `DR-SEAM-calculus-x-rules` in the
  same commit.

- [ ] **10. N2's terminal-persistence test** (A2, G6)
  Multi-cycle offline run; the attacker registered at cycle k appears in
  the pack rendered at the terminal cycle.
  Done-criterion: the test passes and is shown RED under a mutation that
  renders the slice only on the first cycle, pasted.

- [ ] **11. The three exit grades** (S8, R7, G1) `[COMMIT]`
  `render.EXIT_GRADES` / `frame_exits`; `standing_view["exits"]`; the CLI
  render; the anti-`FrameDecisive` absence check.
  Done-criterion: A8's test passes, showing three distinct grades from
  three separate registrations. Then commit with
  `DR-CON-standing-and-background` updated in the same commit.

- [ ] **12. L-4 and L-5 proofs** (A5, A9, G2, G3)
  The no-label-moves test for the slice AND for a declared departure;
  the grep-based no-scoring absence check; the compiler-output absence
  check.
  Done-criterion: both tests pass, AND the **G2 mutation proof** is run —
  slice leaked into adjudication in a scratch copy, RED pasted, restored,
  GREEN pasted.

- [ ] **13. R5's scope-blindness proof** (A6)
  The scope DSL cannot name a departure; `scope.py` imports nothing from
  the declaration.
  Done-criterion: the test passes; the typed `ScopeError` code pasted.

- [ ] **14. Map documents** (S1-S9, §4) `[COMMIT]`
  `DR-SUB-calculus` (Owns + closed set 9→10 + the two-mention rule),
  `DR-INV-axiom-basis` (**A9 proved**, A3/A4/A10 preserved), `INDEX.md`'s
  seam matrix, and any residual check on the four documents already
  touched in earlier steps.
  Done-criterion: **every new check RUN before it is written down**, each
  output pasted; then `python tools/docs_verify.py` FULL.

- [ ] **15. The public-surface proof** (A14, C-PUBLIC)
  Done-criterion: `python scripts/wheel_smoke.py` and `python -u
  scripts/wheel_operational_smoke.py` both green with **pins unchanged**,
  both outputs pasted, and the statement that no view shipped.

- [ ] **16. Boundary gate** `[COMMIT]`
  Done-criterion: `python -m pytest tests/ -q -n 4` → 0 failed;
  `python tools/docs_verify.py` FULL → only the 3 pre-existing
  `CON-run-identity.md` shallow-clone failures;
  `python tools/diff_budget.py` under the 560 ceiling. All pasted.

---

## Proof, per step

**Step 1** — `python -m pytest tests/test_calculus_claim_substrate.py
tests/test_proof_debt.py -q` → `36 passed`.

**Step 2** — compiled interface of a `DepartureDeclarationV1`:
```
  commitments: ['claim:departure-declaration-wf@v1']
  refs       : [('CAND', 'mention'), ('SUBJ', 'mention')]
  dependence refs: [] -> none, L-4 by construction
```

**Step 3** — `departure_declaration_wf` on a well-formed body:
`('pass', {'schema': 'poietic.departure-declaration.v1'})`; on a
mis-registered one:
`('fail', {'reason': 'claim-interface-not-controller-compiled', 'detail': []})`;
a self-departure is refused at construction.

**Step 4** — the same declaration filed twice returns one artifact
(`907e9001…`, count unchanged). Ring: `tests/test_calculus_*.py
tests/test_proof_debt.py tests/test_promotion_criteria.py` → `115 passed`.
`tools/diff_budget.py` over `src`: **144** insertions, well under 560.
`tools/blast_radius.py` over the six touched files and five symbols:
`"frozen_surface_verdict": "CLEAR"`, no contacts, no adjacent contacts.

**Step 5** — the rendered slice for a problem in scope carries the
articulation head, the subject's commitment ids, its standing attackers
under a self-stating cap, the departure directive, the assertion's
protocol string and the already-declared departures; for a problem out of
scope `render_frame_slice_context` returns `None`.

**Step 6** — five mutations, each shown to APPLY before it was run
(mutations 2 and 3 silently no-op'd on the first attempt and proved
nothing; the retry asserts the replacement landed):

| Mutation | Result |
|---|---|
| the slice stops rendering standing attackers | **2 failed** (R1 test + the cap test) |
| the departure directive is dropped | **1 failed** (R2 test) |
| attackers render in `state.att` order | **1 failed** (the ordering test, after it was rewritten — see below) |
| a `school:` slot is emitted | **1 failed** (N1 test) |
| declaring a departure subtracts nothing | **1 failed** (R3 test) |

Restored: `10 passed`.

## Failures and re-plans

**Step 4 — SPEC.md was wrong about the fixture count.** SPEC.md said
`tests/test_proof_debt.py:108` was the only count assertion over
`CLAIM_SCHEMAS`; `tests/test_calculus_frame_assertions.py:192` carries the
same one and went red. The blast-radius census DID list that line and it
was mis-read as a membership assertion — E45's own lesson recurring inside
a spec that cites it. Both fixtures updated, SPEC.md corrected on the
record rather than silently.

**Step 6 — the first ordering test could not fail.** It registered three
attacks and asserted the render was id-sorted. `Harness._adjudicate` does
`self.state.att = sorted(att)` before any reader sees it, so the test
passed with the sort in `subject_attackers` DELETED: it measured the
harness, not this module. Replaced with one that hands the renderer a
reversed `att` and fails if the module leans on someone else's
sortedness; `render.py`'s own comment corrected in the same edit, since it
had claimed `att` was "a set" and "in log order" — it is neither.
