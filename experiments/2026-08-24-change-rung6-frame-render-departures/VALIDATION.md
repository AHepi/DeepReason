# VALIDATION — Rung 6: frame render semantics and the departure protocol

Verdict: **PENDING** (boundary gate, full `docs_verify` and the operational
smoke are the last outstanding measurements; every other check below is
proven and pasted).

Authority: `SPEC.md` A1-A15 and `REQUEST.md` R1-R8, N1-N3, G1-G8.
Base: `origin/main` at `7ad1b273f`. Branch:
`claude/frame-render-departure-protocol-u4dnn7`.

Nothing below is asserted where it could be measured. Where a check could
have passed for the wrong reason, the mutation that makes it fail is run
and its output pasted — five of this tranche's checks turned out to be
exactly that, and each is recorded in CHECKLIST.md's failures section
rather than quietly fixed.

## 1. Requirement by requirement

| # | Requirement | Verdict | Proof |
|---|---|---|---|
| R1 | the frame slice — articulation digest AND standing attackers, in every pack in scope | **PASS** | `test_a_consulted_frame_renders_its_digest_and_its_standing_attackers`, `test_a_problem_outside_the_scope_carries_no_frame_slice`, `test_the_frame_reaches_a_conjecture_pack_end_to_end`, `test_both_rules_put_the_frame_in_the_pack_they_dispatch` (three call sites, not two) |
| R2 | the departure directive rides in the slice | **PASS** | `test_the_slice_carries_the_departure_directive_and_the_protocol` |
| R3 | declaration removes the hidden-premise target; the declaration is attackable | **PASS** | `test_declaring_a_departure_removes_the_held_obligation`, `test_a_departure_declaration_is_itself_attackable` |
| R4 | nothing scores departures (L-4) | **PASS** | `test_a_declared_departure_moves_no_label`, `test_a_departure_declaration_carries_no_dependence_edge`, `test_nothing_that_ranks_admits_or_accepts_reads_a_departure` — plus the mutation in §3 |
| R5 | scope predicates never read departures | **PASS** | `test_the_scope_dsl_cannot_name_a_departure` — structural: σ's whole evaluation domain is five `Problem` fields |
| R6 | P4's render half — the allocation settles what an inherited-context problem may cite | **PASS** | `test_a_dropped_citable_legend_is_disclosed_in_the_pack`, `test_the_disclosure_loop_reaches_a_fixed_point` |
| R7 | the third exit grade; `FrameDecisive` NOT adopted | **PASS** | `test_all_three_exit_grades_are_reachable_by_their_own_registration` (3 params), `test_the_three_grades_are_distinct_and_contestation_rounds_to_neither`, `test_no_module_rounds_a_suspended_frame_onto_a_neighbour`, `test_the_cli_prints_all_three_grades_with_their_meanings` |
| R8 | the diff overrun is disclosed, not re-baselined | **PASS** | §5 below; the 560 ceiling stands unchanged in SPEC.md |
| N1 | omit, don't redact | **PASS** | `test_the_frame_slice_emits_no_provenance_shaped_slot`, `test_an_absent_frame_renders_nothing_rather_than_a_no_frame_notice`, `test_nothing_dropped_means_no_withheld_notice_at_all` |
| N2 | the pack renderer is the memory policy; persistence at the TERMINAL step | **PASS** | `test_a_standing_attacker_at_cycle_k_still_renders_at_the_terminal_cycle` — asked at cycle 8, of the real pack, at a budget measured to bite |
| N3 | position is a hedge; build the gate where one is possible | **PASS** | two gates, neither depending on the model: the sections are non-droppable (`test_the_frame_slice_survives_a_budget_that_drops_everything_optional`) and `held_frame_obligations` subtracts from the record. Recorded as a hedge in `DR-CON-packs-and-token-economy` |

## 2. Gate obligations

| # | Obligation | Verdict | Proof |
|---|---|---|---|
| G1 | all three grades reachable, each by its own registration; render distinguishes them | **PASS** | §3 mutation; three separate graphs — a warranted attack (`fall`), a refuted reach case (`revocation`), an attacker in an unresolved cycle (`contestation`) |
| G2 | L-5 / Prop 12.5 at the render layer, strongest form, MUTATION PROVEN | **PASS** | §3 |
| G3 | L-4 asserted as an absence | **PASS** | §3, plus the negative-grep census over `scheduler/`, `rules/`, `adjudication/`, `informal/`, each paired with a positive anchor |
| G4 | C1 — byte-identical packs | **PASS** | `test_the_slice_is_byte_identical_across_renders` (two calls AND an independent replay), `test_attackers_render_in_id_order_whatever_order_the_state_holds` |
| G5 | no empty provenance-shaped slot | **PASS** | see N1 |
| G6 | terminal-cycle persistence | **PASS** | see N2 |
| G7 | the slice fits the budget; allocation logged; drops disclosed | **PASS** | `test_the_exact_crisis_section_is_bounded_by_construction`, `test_the_frame_slice_allocation_is_accounted`, `test_a_dropped_citable_legend_is_disclosed_in_the_pack` |
| G8 | axiom ledger — A9's render half PROVED; A3, A4, A10 PRESERVED | **PASS** | `DR-INV-axiom-basis`, four sections, every check re-run before it was written |

## 3. The mutation proofs

**G2 — the frame slice leaks into adjudication.** A consulted subject is
marked `accepted` because it frames, rather than because it survived
criticism. This is the shape Rung 4's own mutation took, applied one layer
out.

RED:

```
E  AssertionError: assert ({'c6f2aa8e6b...ed'>}, [], []) == ({'c6f2aa8e6b...ed'>}, [], [])
E    At index 0 diff: {'c6f2aa8e...': <Status.ACCEPTED: 'accepted'>}
E                  != {'c6f2aa8e...': <Status.REFUTED: 'refuted'>}
FAILED tests/test_frame_render.py::test_rendering_the_frame_slice_moves_no_label
1 failed, 34 passed in 2.79s
```

Restored, GREEN: `35 passed in 2.36s`.

**L-4 — the departure declaration compiles with a DEPENDENCE.** RED:

```
FAILED tests/test_frame_render.py::test_a_declared_departure_moves_no_label
FAILED tests/test_frame_render.py::test_a_departure_declaration_carries_no_dependence_edge
2 failed, 33 passed in 2.18s
```

Restored, GREEN: `35 passed`.

**Anti-`FrameDecisive`.** `Status.SUSPENDED → "revocation"` (the axiom
adopted): **3 failed**. `SUSPENDED` removed from `EXIT_GRADES` (the
two-exit claim): **3 failed**. Restored: `27 passed` at that step.

**N2 — the crisis section made droppable.** **2 failed** (budget survival
AND terminal persistence). Restored: `22 passed` at that step.

**Two declarations by one candidate must UNION, not overwrite.** Reverting
`declared_departures` to the assignment it originally used: **1 failed**.
Restored: `36 passed`. This one is a defect this tranche shipped and then
found by review — see §8 item 7.

**Six more**, listed in CHECKLIST.md's per-step proof: the slice stops
rendering attackers; the departure directive dropped; attackers rendered in
`state.att` order against a shuffled state; a `school:` slot emitted;
declaring a departure subtracts nothing; defeated attackers occupy crisis
slots.

## 4. Frozen surfaces

**ZERO CONTACT, and measured rather than asserted.** `tools/blast_radius.py`
over the actually-touched files and symbols returns
`"frozen_surface_verdict": "CLEAR"` with no contacts and no frozen-adjacent
contacts.

- **Surface 1** (`capabilities/state.py`) — untouched.
- **Surface 2** (`harness.py`) — untouched. A departure declaration is an
  ordinary artifact through the existing `create_artifact` path; no event
  rule and no state-application rule was added.
- **Surface 3** (`invariants.py`, `verification/`) — untouched, and
  actively protected: `invariants.py::_consulted_grants` imports
  `calculus.standing.consulted`, so SPEC.md's constraint F1 forbade
  touching `consulted()` or `StandingGrant`. The frame slice reads
  `state.att` in a new module instead.
- **Surface 4** (manifest schemas and validators) — untouched. **No new
  `Config` field**, so no `_versioned_source_config_data` line is owed and
  no qualification subject digest moves; the slice's caps are module
  constants beside `NEIGHBOURHOOD_N` and `ATTACKERS_N`.
- **Surface 5** (qualification subjects) — untouched, **because no new LLM
  role was added**. The ladder marks this the rung most tempted to add one.
  The articulation digest is a deterministic content head plus the
  subject's declared commitment ids, reaching no seat, pinned by A9's
  import check. The STOP-and-ask condition was never triggered.

## 5. Size — the ledgered overrun, disclosed per R8

| Area | Insertions |
|---|---|
| `src/` | **810** against SPEC.md's ledgered ceiling of **560** |
| `tests/` | 1153 |
| `docs/` | 385 |

Per file, `src/` only:

```
389  src/deepreason/calculus/render.py
165  src/deepreason/llm/packs.py
 57  src/deepreason/rules/crit.py
 49  src/deepreason/calculus/operations.py
 39  src/deepreason/calculus/claims.py
 32  src/deepreason/cli/main.py
 21  src/deepreason/calculus/compiler.py
 19  src/deepreason/calculus/programs.py
 13  src/deepreason/rules/conj.py
 12  src/deepreason/programs.py
 10  src/deepreason/calculus/standing.py
  4  src/deepreason/calculus/__init__.py
```

Three causes, and two were forced by measurement rather than chosen:

1. **The crisis/digest split** (step 7). SPEC.md specified ONE compressible
   section; at a tight budget it survived while `_bounded_view` cut the
   `STANDING ATTACKERS` block out of its middle. Splitting it doubled the
   section blocks in `packs.py` and added a second renderer and a third cap
   to `render.py`.
2. **A third `render_crit_pack` call site** (step 9) — the
   atomic-decomposition path, reached only after a batch critic exhausts
   its schema. SPEC.md did not know it existed.
3. **Documentation density.** Of `render.py`'s 389 lines, 125 are
   docstrings and 18 are comments; ~189 are executable. The repo's own
   convention is that a comment states the constraint the code cannot show.

The ceiling is **not re-baselined** (REQUEST.md Amendment 1 / R8). The
operator ruled *continue and disclose* at the step-9 stop, with the
breakdown in front of them.

## 6. Public surface

**No `frame`/`pack` inspection view shipped.** No new console entry point
and no new MCP tool; the richer standing view rides the EXISTING
`deepreason standing --json` and MCP `run_standing`, whose input schema is
unchanged — and the pinned sha is taken over `tools/list`, i.e. names,
descriptions and input schemas, so a richer RESULT moves no pin. `git diff
7ad1b273f -- scripts/` is empty: **none of the four pins moved**.

```
wheel smoke passed: isolated V6-only contents, clean imports, exact entry
points, module parity, MCP registration, and exact MCP schemas
```

## 7. The boundary gate

**`python tools/docs_verify.py` (FULL) — 3 failed, and all three are the
pre-existing shallow-clone failures the operator named.** None is this
tranche's:

```
docs_verify [full]: 64 documents, 1033 checks, 4 workers
  FAIL CON-run-identity.md:200: git log -M --diff-filter=R --name-status ...
  FAIL CON-run-identity.md:202: git log -1 --format=%s 1637e808 | grep -qi retire
      -> fatal: ambiguous argument '1637e808': unknown revision or path not in the working tree.
  FAIL CON-run-identity.md:204: test -z "$(git show -M --diff-filter=R ...
      -> fatal: ambiguous argument 'f304fec1': unknown revision or path not in the working tree.
docs_verify: 3 failed
```

Each names a commit this shallow clone does not contain; on a full clone
they pass. The FIRST pass of this run reported **6**, the extra three being
this tranche's own (`CON-packs-and-token-economy` — my new check crashed on
a non-literal section id; `SEAM-evaluation-x-ontology` — `programs.evaluate`'s
pinned dispatch list; `SEAM-rules-x-scratch` — `render_crit_pack`'s pinned
signature). All three are fixed and the count is back to the baseline.

**`python -m pytest tests/ -q -n 4`** — (pending; running on an idle box)

**`python scripts/wheel_smoke.py`** — PASS, pins unchanged (§6).

**`python -u scripts/wheel_operational_smoke.py`** — (pending)

## 8. Residue — what this tranche did NOT prove

Recorded because "accepted does not mean true", and because each of these
is a place a later reader could over-read the result.

1. **G6 is unconditional only within the cap.** What persists is the
   CRISIS, not any particular attacker: past `FRAME_SLICE_ATTACKERS_N`, an
   early wound can be displaced by later ones whose ids sort lower. It is
   disclosed by the count, never silent — `test_the_cap_can_displace_an_
   individual_attacker_and_says_so` pins exactly this, so the limit is a
   committed test rather than a caveat in prose.
2. **No live run.** This rung launches nothing (the operator's own
   instruction), so every claim here is offline. Whether a real provider
   model ACTS on the departure directive is untested and, per Q1, should
   not be assumed — which is why the load-bearing parts are the
   non-droppable sections and the deterministic subtraction rather than the
   directive's wording.
3. **The exit grades report a STATE, not a transition.** `standing_view
   ["exits"]` says which grade an assertion is in now, not the sequence
   number at which it left `U`. The Formalization defines an exit as a
   prefix transition; that reading is not implemented.
4. **The critic's frame is the FIRST problem its target is addressed to.**
   A target addressed to two problems in two different scopes carries only
   the first frame. Recorded in SPEC.md A-3.
5. **`DISCLOSED_ON_DROP` is four sections, not all of them.** A dropped
   `neighbourhood` or `crossover` is still silent. The line drawn is
   "absence changes what the model may DO", and it is a judgement.
6. **One defect shipped and was caught by REVIEW, not by the gate.**
   `declared_departures` originally assigned rather than unioned, so two
   declarations by one candidate against one subject overwrote each other.
   It is fixed and pinned, but the honest reading is that the test suite as
   written would not have found it — every test filed one declaration per
   candidate. What found it was re-reading the diff. Recorded because the
   next reader should not assume this file's coverage is exhaustive.
7. **The disclosure loop's convergence is MEASURED, not proved.** At most
   three passes across 115 budgets from 1 to 799. The obvious monotonicity
   argument is false and is corrected in place; the bound-exhaustion path
   over-names rather than under-reporting.
