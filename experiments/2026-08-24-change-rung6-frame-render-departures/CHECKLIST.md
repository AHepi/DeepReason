# CHECKLIST — Rung 6

State: **step 14 next** (steps 12 and 13 landed together — 13's proof is in the same test file) (the step-9 diff-budget stop was resolved by the operator: continue and disclose — REQUEST.md Amendment 1)
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

- [x] **7. Pack sections** (S6.1) `[COMMIT]`
  `frame_slice_context` on both renderers; one non-droppable,
  compressible `frame-slice` section each.
  Done-criterion: `python -m pytest tests/test_pack_ir.py
  tests/test_pack_prefix.py tests/test_frame_render.py -q` green; the
  section-slot census (16 / 12) pasted. Then commit with the
  `DR-CON-packs-and-token-economy` census check updated in the SAME
  commit.

- [x] **8. The drop disclosure** (S6.2, S6.3, R6, G7)
  `DISCLOSED_ON_DROP` + the bounded fixed-point loop in
  `_allocate_sections`.
  Done-criterion: A7's test passes; a pasted demonstration that a
  budget which drops `citable-evidence-blocks` produces a pack naming it
  withheld; and a pasted argument-by-measurement that the loop converges
  in ≤2 passes on the real renderers.

- [x] **9. The two call sites** (S7) `[COMMIT]`
  `rules/conj.py` and `rules/crit.py` compute and pass the slice.
  Done-criterion: `python -m pytest tests/test_pack_prefix.py
  tests/test_crit_batch.py tests/test_harness_fixes.py
  tests/test_frame_render.py -q` green. Then commit with
  `DR-SEAM-llm-x-rules` and the NEW `DR-SEAM-calculus-x-rules` in the
  same commit.

- [x] **10. N2's terminal-persistence test** (A2, G6)
  Multi-cycle offline run; the attacker registered at cycle k appears in
  the pack rendered at the terminal cycle.
  Done-criterion: the test passes and is shown RED under a mutation that
  renders the slice only on the first cycle, pasted.

- [x] **11. The three exit grades** (S8, R7, G1) `[COMMIT]`
  `render.EXIT_GRADES` / `frame_exits`; `standing_view["exits"]`; the CLI
  render; the anti-`FrameDecisive` absence check.
  Done-criterion: A8's test passes, showing three distinct grades from
  three separate registrations. Then commit with
  `DR-CON-standing-and-background` updated in the same commit.

- [x] **12. L-4 and L-5 proofs** (A5, A9, G2, G3)
  The no-label-moves test for the slice AND for a declared departure;
  the grep-based no-scoring absence check; the compiler-output absence
  check.
  Done-criterion: both tests pass, AND the **G2 mutation proof** is run —
  slice leaked into adjudication in a scratch copy, RED pasted, restored,
  GREEN pasted.

- [x] **13. R5's scope-blindness proof** (A6)
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

**Step 7** — section-slot census after the split:
```
conj 17  crit 13
p4 ids conj: ['active-properties', 'citable-evidence-blocks', 'frame-crisis', 'frame-slice', 'frozen-evidence-context']
p4 ids crit: ['frame-crisis', 'frame-slice', 'target', 'target-support-chain']
```
`frame-crisis` sorts before `frame-slice` on id, so the crisis leads; the
pre-existing `target` / `target-support-chain` tie at 4 is unchanged. Ring:
`tests/test_pack_ir.py tests/test_pack_prefix.py tests/test_frame_render.py
tests/test_crit_batch.py tests/test_oracle.py
tests/test_prose_refutation_boundaries.py tests/test_harness_fixes.py
tests/test_compact_profiles.py` → **172 passed**.
`DR-CON-packs-and-token-economy`'s two new checks were RUN before they were
written down (`census OK`, `flags OK`, `2 passed`).

**Step 8** — a starved conjecture pack now names what it cut:
```
CONTEXT WITHHELD FOR BUDGET — these sections exist in this run and were cut
from THIS pack to fit its token budget, not because they are empty:
citable-evidence-blocks. Treat what you were shown as partial; do not
conclude the withheld content does not exist.
```
Convergence MEASURED rather than argued: at most **3** `allocate_pack`
passes across 115 budgets from 1 to 799, bound `len(sections)+1`. Ring
(incl. `test_v6_request_envelope.py`, `test_v6_context_continuation.py`) →
**191 passed**. Both new map checks run before being written down.

**Step 9** — both rules now compute the slice and pass both halves. The
call-site census found a THIRD site SPEC.md did not know about: the
atomic-decomposition path in `crit.py`, reached only after a batch critic
exhausts its schema, which renders one crit pack per target. Wired.
New map document `DR-SEAM-calculus-x-rules` created (the pair had no row in
`INDEX.md`'s matrix because it did not interact before this rung);
`DR-SEAM-llm-x-rules`, `INDEX.md`, `SUB-calculus.md` and `SUB-rules.md`
updated in the same commit. `docs_verify --links` → 0 dangling, 64
documents. Ring → **61 passed**.

**Step 10** — G6/N2. Eight cycles of accumulating ACCEPTED state, the wound
injected at cycle 2, the question asked only at cycle **8**, and asked of
the real `render_conj_pack` output at a budget that has already dropped the
neighbourhood. Mutation: make `frame-crisis` droppable →
**2 failed** (the budget-survival test AND the terminal-persistence test).
Restored → `22 passed`. A second mutation — defeated attackers occupy
crisis slots — → **1 failed**.

Two limits recorded as their own tests rather than left implicit: a
REFUTED attacker no longer occupies a crisis slot (it is a defeated attack,
not an open indictment, and under the cap it would displace a live one),
and the cap CAN displace an individual early attacker, which is disclosed
by the count rather than silent — so G6 is unconditional only while the
total is within the cap.

**Step 11** — R7/G1, the anti-`FrameDecisive` check. Three grades, each
reached by its OWN graph:

| grade | label | registration |
|---|---|---|
| `fall` | `refuted` | a warranted attack on the assertion |
| `revocation` | `suspended_unsupported` | the reach case it depends on is refuted |
| `contestation` | `suspended` | an attacker locked in an unresolved cycle |

Mutations: (a) `Status.SUSPENDED → "revocation"` (FrameDecisive adopted) →
**3 failed**; (b) `SUSPENDED` dropped from `EXIT_GRADES` (the two-exit
claim) → **3 failed**. Restored → `27 passed`.
`standing_view["exits"]` and the CLI both name each grade AND what it
means. Ring incl. `test_calculus_standing.py`,
`test_promotion_solo.py`, `test_calculus_vocabulary.py` → green.

**Steps 12-13** — L-5 and L-4, each mutation-proven.

**G2 MUTATION PROOF** (required verbatim by the operator). Mutation: the
slice leaks into adjudication — a consulted subject is marked `accepted`
because it frames, not because it survived criticism.

RED:
```
E  AssertionError: assert ({'c6f2aa8e6b...ed'>}, [], []) == ({'c6f2aa8e6b...ed'>}, [], [])
E    At index 0 diff: {'c6f2aa8e...': <Status.ACCEPTED: 'accepted'>}
E                  != {'c6f2aa8e...': <Status.REFUTED: 'refuted'>}
FAILED tests/test_frame_render.py::test_rendering_the_frame_slice_moves_no_label
1 failed, 34 passed
```
Restored, GREEN: `35 passed in 2.36s`.

**L-4 MUTATION PROOF.** Mutation: the departure declaration compiles with a
DEPENDENCE on the departing artifact instead of a mention. RED:
```
FAILED tests/test_frame_render.py::test_a_declared_departure_moves_no_label
FAILED tests/test_frame_render.py::test_a_departure_declaration_carries_no_dependence_edge
2 failed, 33 passed
```
Restored, GREEN: `35 passed`.

Also landed: rendering writes nothing to `log.jsonl` (byte-compared across
five renders); no scheduler/rules/adjudication/informal module names the
departure body, its commitment or `broken_ids` (negative greps, each paired
with a positive anchor); and R5 — sigma's evaluation domain is five
`Problem` fields, a scope naming a departure is a typed
`scope-field-unknown`, and `scope.py` knows nothing of the departure
machinery.

`DR-INV-axiom-basis`: **A9's render half PROVED** (three checks — no seat,
no write, no label movement); A3, A4 and A10 preservation rows added with
their own checks. Every check run before it was written down.

## Failures and re-plans

**Step 4 — SPEC.md was wrong about the fixture count.** SPEC.md said
`tests/test_proof_debt.py:108` was the only count assertion over
`CLAIM_SCHEMAS`; `tests/test_calculus_frame_assertions.py:192` carries the
same one and went red. The blast-radius census DID list that line and it
was mis-read as a membership assertion — E45's own lesson recurring inside
a spec that cites it. Both fixtures updated, SPEC.md corrected on the
record rather than silently.

**Step 12 — the L-4 behavioural test could not see a dependence leak.** Its
edge filter was `e[0] in ids`, which compares only edges FROM a shared node.
A penalty arrives the other way — an extra node the candidate is made to
depend on, or that depends on the candidate — so the dependence mutation
left it green while only the structural test failed. Widened to edges
INCIDENT on the shared ids in either direction; the mutation then takes both.

**Step 12 — the A3 preservation check was wrong twice, and both times it was
the check.** A name-based version ("no assignment target mentioning
`status`") flagged a local variable called `status`; a shape-based version
("no attribute or subscript targets") flagged a legitimate local dict write.
It now asserts the actual property — no assignment target rooted at
`harness` — and was proven non-vacuous by running it against the leak
mutation, where it fails naming the offending target.

**Step 11 — the first contestation fixture produced `refuted`, not
`suspended`.** It built a CHAIN — assertion ← critic ← counter ← rebuttal —
and grounded semantics reinstates the first critic across an odd chain, so
the assertion came out defeated. Contestation needs a CYCLE: the attacker
must be locked in a mutual attack so it is neither accepted nor defeated.
Warrants attach only at artifact registration (there is no
`register_warrant`), so the cycle is closed by letting the first critic name
a target that does not exist yet, which `Harness` admits.

**Step 11 — the CLI test could not call the CLI.** `standing` is a
root-admission command and refuses a root with no run manifest
(`MANIFEST_FILE_UNAVAILABLE`), so asserting on three printed lines would
have meant standing up a whole v6 manifest run — testing the admission gate
rather than the rendering. The exit rendering was lifted out of `main`'s
closure into a module-level `render_exit_grades(view)`, which is the better
shape anyway.

**Step 10 — the first terminal-persistence test could not fail either.**
Written at `token_budget=300`, it passed with `frame-crisis` made
droppable, so it measured nothing about what keeps the wound in the pack.
The budget was MEASURED (60/100/150/200 lose the wound under the mutation;
300 does not) and set to 200. Same class of error as step 6's ordering
test: a test that passes for a reason other than the one it names.

**Step 9 — DIFF BUDGET EXCEEDED, and the tranche STOPPED here.** 759
insertions over `src` against a ledgered ceiling of 560. Raised to the
operator with the per-file breakdown rather than re-baselined.
**RESOLVED**: the operator ruled *continue and disclose* — REQUEST.md
Amendment 1, new requirement R8. The ceiling stands unre-baselined and
DELIVERY.md carries the overrun as a result.

**Step 9 — the seam document's first draft asserted an acyclic edge; it is
a cycle.** `calculus/promotion.py` has imported
`rules.warrants.register_fail_warrant` since Rung 5, so `rules` ×
`calculus` runs both ways. The claim was written before its check was run
and the check refuted it in the same commit. Corrected to pin both
directions by name, plus a third check that the two directions never meet
(`render.py` imports no rule; `promotion.py` imports no render).

**Step 8 — my own termination argument was wrong, and the first two tests
failed against correct code.** SPEC.md S6.3 claimed the dropped set is
monotone as `remaining` decreases, so the loop provably converges. It is
not: `allocate_pack` is greedy and `continue`s past a section that will not
fit, so a smaller budget can afford a later small section it could not
afford before. Convergence is now a MEASURED property with a sweep behind
it, and the bound-exhaustion path names the union (over-naming, the safe
direction) rather than returning a pack that under-reports. Separately,
both new tests initially failed because they searched for section names as
bare substrings while the `context-withheld` notice sits at priority 1 and
renders near the TOP — so `pack.split("CONTEXT WITHHELD")[1]` read the
whole rest of the pack as the notice. Test bug, not a code bug; fixed with
a `_notice_body` helper that reads only the notice's own section.

**Step 7 — SPEC.md S6.1 specified one section; it had to become two.**
The single compressible section passed non-droppability and still lost the
wounds: at a budget of one token the section survived and `_bounded_view`
cut the `STANDING ATTACKERS` block out of its middle, so the pack showed a
frame with no visible crisis. Caught by the step-7 test rather than by
review. Split into an EXACT `frame-crisis` and a compressible
`frame-slice`, which is §9.5's own wording — only the digest is described
there as compressed. SPEC.md amended on the record.

**Step 6 — the first ordering test could not fail.** It registered three
attacks and asserted the render was id-sorted. `Harness._adjudicate` does
`self.state.att = sorted(att)` before any reader sees it, so the test
passed with the sort in `subject_attackers` DELETED: it measured the
harness, not this module. Replaced with one that hands the renderer a
reversed `att` and fails if the module leans on someone else's
sortedness; `render.py`'s own comment corrected in the same edit, since it
had claimed `att` was "a set" and "in log order" — it is neither.
