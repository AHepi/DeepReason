# SPEC — Rung 6: frame render semantics and the departure protocol

Authority: `REQUEST.md` (operator verbatim + R1-R7, N1-N3, G1-G8,
C-FROZEN / C-PUBLIC / C-SIZE / C-GATE / C-DELIVER).
Every item below cites the requirement it discharges. Every acceptance
check is a command or a named test.

## 0. Base facts, re-derived rather than assumed

| Fact | Value at this tranche's base (`7ad1b273f`) | How derived |
|---|---|---|
| Full gate | **3939 passed, 6 skipped, 0 failed** in 853.92s | `python -m pytest tests/ -q -n 4`, idle box, 2026-08-24 |
| Frozen-surface verdict for the declared radius | `CONTACT`, **both contacts false positives** — see §1 | `tools/blast_radius.py` with 10 files + 11 symbols |
| Consumers of the declared radius | 10 test files, 21 map documents | same run |

## 1. Frozen surfaces — the census, and why the verdict is disposed of

`tools/blast_radius.py --files <the ten below> --symbols render_conj_pack
render_crit_pack _pack_section standing_view consulted frames
compile_interface decode CLAIM_SCHEMAS ATTACKERS_N _allocate_sections`
returns `"frozen_surface_verdict": "CONTACT"` with **four**
`SYMBOL_INDIRECT` rows. Per E49, the census enumerates the SYMBOLS this
spec names as mechanisms, not only the files it plans to edit.

| Row | Disposition |
|---|---|
| `decode` in `run_manifest.py` | **substring false positive.** Every hit is `bytes.decode("utf-8")` (lines 3833, 4018) or prose. No import of `calculus.claims`. |
| `consulted` in `run_manifest.py` | **substring false positive.** Every hit is the English word in a comment (2393, 2400, 2414, 2425, 3439). |
| `decode` in `invariants.py` | **substring false positive.** `bytes.decode("utf-8")` (2645, 4015). |
| `consulted` in `invariants.py` | **REAL.** `invariants.py::_consulted_grants` imports `calculus.standing.consulted` for the Rung 4 `standing-integrity` check (frozen surface 3, granted contact). |

**The constraint that follows, and it is binding on every step below:**

> **F1. `consulted()` and `StandingGrant` are NOT TOUCHED.** No field is
> added to `StandingGrant`, and `consulted()` keeps its signature,
> semantics and output. The frame slice computes standing attackers from
> `harness.state.att` in a NEW module, so surface 3 receives **zero**
> contact and no grant is requested.

**F2. No new LLM role** (C-FROZEN). The articulation digest is a
DETERMINISTIC head-plus-commitments render, not a summarizer call: no seat
is reached, the pair inventory is unchanged, surface 5 stays at zero, and
no home owes a qualification battery rerun. **No summariser variant is
needed, so the STOP-and-ask condition is not triggered.**

**F3. No new `Config` field.** Slice sizes are module constants in the new
module, following `NEIGHBOURHOOD_N` / `ATTACKERS_N` / `FOUNDATION_CHARS`
in `llm/packs.py`. So no `_versioned_source_config_data` line is owed,
surface 4 receives zero contact, and no qualification subject digest
moves. G2's with/without comparison needs no knob — the renderer's
parameter is `None` versus a string.

**F4. Surfaces 1 and 2** (`capabilities/state.py`, `harness.py`) are not
in the declared radius at all. A departure declaration is an ORDINARY
artifact registered through the existing `create_artifact` path; it adds
no event rule and no state-application rule.

## 2. What ships — spec items

### S1 (R1, R7, N1, N2) — `src/deepreason/calculus/render.py`, new module

The frame render layer. Reads replayed state; writes nothing; imports no
`llm`, `adapter`, `seat`, `provider`, `qualification` or `adjudication`
symbol (the A9 import check, §5).

| Symbol | Contract |
|---|---|
| `FRAME_SLICE_ATTACKERS_N = 5` | how many standing attackers of the subject render |
| `ARTICULATION_DIGEST_CHARS = 400` | the compressed articulation head's char bound |
| `subject_attackers(harness, subject_id)` | `((attacker_id, status), ...)` from `state.att`, sorted by attacker id. Deterministic ordering, no provenance |
| `articulation_digest(harness, subject_id)` | `(head_text, commitment_ids)` — the subject's content head bounded by `ARTICULATION_DIGEST_CHARS` plus its declared commitment ids in interface order. This IS the "compressed, expandable by view" digest; the expansion is `deepreason standing --json` / MCP `run_standing` (S8) and `deepreason show` |
| `FrameSliceV1` | frozen dataclass: `assertion_id, subject_id, promotion_problem, digest_head, digest_truncated, commitment_ids, attackers, attackers_total, departure_protocol, declared_departures` |
| `frame_slices(harness, problem_id)` | one slice per CONSULTED grant whose σ admits the problem, sorted by `assertion_id`. Uses `consulted()` and `frames()` UNCHANGED (F1) |
| `render_frame_slice_context(harness, problem_id)` | the model-facing text, or `None` when no assertion frames the problem |
| `frame_obligations(harness, subject_id)` | the subject's declared commitment ids — the ids a departure may name |
| `declared_departures(harness, subject_id)` | `{departing_artifact_id: (broken_id, ...)}` from registered declarations |
| `held_frame_obligations(harness, subject_id, artifact_id)` | `frame_obligations − declared_departures[artifact_id]` — R3's deterministic gate |
| `EXIT_GRADES` | `{REFUTED: "fall", SUSPENDED_UNSUPPORTED: "revocation", SUSPENDED: "contestation"}` |
| `exit_grade(status)` | the grade, or `None` for `ACCEPTED` (still standing) |
| `frame_exits(harness)` | every frame assertion addressed to a promotion problem whose label is not `ACCEPTED`, with its grade, sorted by assertion id |

**Render shape** (one slice; sections omitted entirely when empty — N1):

```
FRAME (consulted; this is the coordinate system this problem is posed in,
not a claim you must accept):
  subject <id> — <articulation head, bounded>
  its commitments: <id>, <id>, ...
  STANDING ATTACKERS (3 of 7 shown, by id) — this frame ships its own crisis:
    - <attacker id> [<status>]: <head>
  DEPARTURES ARE PERMITTED. To break with this frame, declare which of its
  commitment ids you break with, as a list. A declared departure is not
  penalised anywhere; an UNDECLARED conflict is criticisable as a silent
  assumption. <departure_protocol>
  ALREADY DECLARED: <artifact id> breaks <commitment id>, ...
```

- **No provenance-shaped field appears at all** (N1): no author, school,
  seat, model, endpoint, role or origin — neither populated nor blanked.
  An absent part is ABSENT: no `(none)`, no `—`, no `redacted`.
- **No silent cap** (G7): `3 of 7 shown` states the cap in-band whenever
  `attackers_total > FRAME_SLICE_ATTACKERS_N`, and the digest carries an
  explicit truncation marker when `digest_truncated`. This mirrors
  `evidence/render.py::citable_legend`'s own
  `(+N further citable blocks not shown)` idiom, deliberately.
- **N3, recorded honestly:** the slice's POSITION in the pack is a hedge,
  not the mechanism. The mechanisms are (a) the section is NON-DROPPABLE,
  so allocation cannot silently remove it, and (b)
  `held_frame_obligations` is computed by the harness from the record —
  neither depends on the model honouring a rendered instruction.

### S2 (R2, R3) — the departure-declaration claim body

`calculus/claims.py`: add `"poietic.departure-declaration.v1"` to
`CLAIM_SCHEMAS` **and** to `_IMPLEMENTED` (this rung supplies the
producer, which is the condition that module's own docstring sets), plus
`DEPARTURE_DECLARATION_V1` and:

```
class DepartureDeclarationV1(_Body):
    subject_ref: str          # the frame subject departed from
    departing_ref: str        # the artifact that departs
    broken_ids: list[str]     # the subject's commitment ids broken with
    rationale: str
```

Validator: `broken_ids` non-empty and unique; `departing_ref !=
subject_ref` (an artifact cannot depart from itself).

**Predicted fixture update, declared IN ADVANCE per the gate rule:**
`tests/test_proof_debt.py:108` asserts `len(CLAIM_SCHEMAS) == 9`. It
becomes `== 10`.

**CORRECTED at step 4, and the correction is recorded rather than
quietly applied.** This paragraph first said "this is the only count
assertion over that tuple; the other consumers assert MEMBERSHIP". That
was wrong: `tests/test_calculus_frame_assertions.py:192` carries the same
count and failed at the step-4 ring. The blast-radius census DID list
that line — it was mis-read as a membership assertion, which is E45's
own lesson (classify per CHECK, not per file) recurring inside a spec
that cites E45. Both fixtures move to `== 10`, both keep their
declared-but-unbuilt assertion intact, and both docstrings state why the
count moved. No design item changes.

### S3 (R4, R5) — the compiler rule

`calculus/compiler.py`: `DepartureDeclarationV1` compiles to **two
MENTIONs and nothing else** — `subject_ref` and `departing_ref`.

The reason, and it IS L-4: a DEPENDENCE either way would give the
declaration a support edge, and pass 2 would then move a label because a
departure was declared. Two mentions create no `dep` edge and no `att`
edge, so **no label anywhere can move because an artifact declared a
departure**. R4 is discharged by construction, not by a rule that says so.

### S4 (R2) — well-formedness program and registration

`calculus/programs.py`: `DEPARTURE_DECLARATION_WF`,
`DEPARTURE_DECLARATION_COMMITMENT` (`claim:departure-declaration-wf@v1`),
and `departure_declaration_wf` delegating to the shared `_wf`.
`programs.py`: `_departure_declaration_wf` + a `"structural"`
`ProgramSpec`, exactly as `reach_certificate_wf` is wired.

STRUCTURAL, and for this rung's own reason: a well-formed declaration
must confer no immunity and ground no reach — otherwise declaring a
departure would BUY something, which is exactly what R4 forbids.

### S5 (R2, R3) — the authoring operation

`calculus/operations.py`: `file_departure_declaration(harness, *, problem,
subject_ref, departing_ref, broken_ids, rationale)`. Registers the
commitment and the artifact through `create_artifact` with
`compile_interface(body)`, matching `file_frame_assertion`'s shape.
Idempotent by content address.

### S6 (R1, R6, G7) — the pack sections and the drop disclosure

`llm/packs.py`:

1. `render_conj_pack` and `render_crit_pack` each gain
   `frame_slice_context: str | None = None`, rendered as ONE
   `_pack_section("frame-slice", ..., 4, droppable=False,
   compressible=True, min_tokens=96)`.
   - **Non-droppable** is the mechanism (N3): the allocator cannot
     silently remove it, and a shortfall surfaces as `mandatory_overflow`
     — the IR's own disclosed channel — never as a quiet cut.
   - **Compressible** because the doc's NEGATIVE rule forbids only the
     *droppable + non-compressible* pairing; and "compressed, expandable
     by view" is the calculus's own description of the digest.
   - **Priority 4** places it after the static, cacheable head (problem,
     criteria, mandatory-interface) and before the neighbourhood.
     Position is a HEDGE (N3), and the choice is recorded as such: the
     cache-prefix cost of putting a per-cycle-varying section ahead of
     the static foundation is the reason it is 4 and not 3.
   - Section-slot census moves: conj **15 → 16**, crit **11 → 12**. Both
     numbers are pinned by `DR-CON-packs-and-token-economy`'s own AST
     check, which moves in the same commit.

2. `DISCLOSED_ON_DROP: frozenset` = `{"citable-evidence-blocks",
   "frozen-evidence-context", "premise-invitation", "standing-attacks"}`
   — the sections whose absence changes what the model MAY DO (cite,
   criticise), not merely what it sees.

3. `_allocate_sections` gains a bounded fixed-point loop: allocate; if any
   `DISCLOSED_ON_DROP` section was dropped, re-allocate with a MANDATORY
   one-line `context-withheld` section naming the dropped ids; repeat
   while the dropped set GROWS, bounded by `len(sections) + 1` passes.
   - **Termination is provable, not hoped for:** adding a mandatory
     section only ever decreases `remaining`, `allocate_pack` admits
     droppable sections in `(priority, id)` order while `remaining`
     allows, so the dropped set is monotone non-decreasing across passes
     over a finite section set.
   - **This is R6, P4's render half:** the deterministic section
     allocation is what settles whether an inherited-context problem can
     cite anything, and after this it says so in-band instead of
     producing a pack that silently lists no ids.
   - When nothing is dropped the notice is ABSENT — no empty slot (N1).

### S7 (R1) — the two call sites

`rules/conj.py` and `rules/crit.py` call
`calculus.render.render_frame_slice_context(harness, problem_id)` and pass
the result as `frame_slice_context=`, exactly as
`citable_evidence_context` already travels. For the critic the problem is
the FIRST problem `_problem_context` would name for the target, resolved
from `state.addr` by the same rule, so the pack's frame agrees with the
pack's stated standard.

**New package edge: `rules` → `calculus`.** `rules/` imports no calculus
symbol today. This is a real new seam and it gets a real seam document
(§4). It is acyclic — nothing in `calculus/` imports `rules/`.

### S8 (R7, G1) — the three exit grades at the render layer

`calculus/standing.py::standing_view` gains an `"exits"` list, each entry
`{assertion, subject, promotion_problem, label, grade}` with `grade` one
of `fall` / `revocation` / `contestation`, sorted by assertion id.
Built from `render.frame_exits`. `consulted()` and `StandingGrant` are
untouched (F1); `standing_view` is not read by `invariants.py`.

`cli/main.py`'s `standing` command prints the three grades under distinct
headings with their labels spelled out, and **never collapses
contestation into either neighbour**. The text form states each grade's
meaning inline (fall = the assertion itself defeated; revocation =
accreditation lost, not wrong; contestation = unresolved, nobody has won).

**`FrameDecisive` is NOT adopted**, and the absence is asserted: no module
may contain a branch mapping `SUSPENDED` on a frame assertion onto either
`REFUTED` or `SUSPENDED_UNSUPPORTED` (§5, G1's negative check).

### S9 — exports

`calculus/__init__.py` re-exports the new public names.

## 3. Acceptance checks, per requirement

| # | Requirement | Acceptance check |
|---|---|---|
| A1 | R1 | `tests/test_frame_render.py::test_a_consulted_frame_renders_its_digest_and_its_standing_attackers` — the pack for a problem in scope carries the subject's articulation head, its commitment ids, and the attacker id; a problem OUT of scope carries none of it |
| A2 | R1, N2 | `::test_a_standing_attacker_at_cycle_k_still_renders_at_the_terminal_cycle` — multi-cycle offline run; the attacker registered early appears in the pack rendered at the LAST cycle. Persistence asserted at the terminal step (G6) |
| A3 | R2 | `::test_the_slice_carries_the_departure_directive_and_the_protocol` |
| A4 | R3 | `::test_declaring_a_departure_removes_the_held_obligation_and_is_itself_attackable` — `held_frame_obligations` loses the declared id; the declaration artifact takes an attack and becomes `REFUTED` like any artifact |
| A5 | R4 (L-4) | `::test_a_declared_departure_moves_no_label_and_no_rank` (G3): labels, `att`, `dep` and scheduler rank over the shared ids are byte-identical with and without the declaration; PLUS the structural absence check in §5 |
| A6 | R5 | `::test_the_scope_dsl_cannot_name_a_departure` — `_FIELDS`/`_LISTS` are closed to `Problem` fields; a scope document naming a departure field is a typed `ScopeError`; and `scope.py` imports nothing from the declaration module |
| A7 | R6, G7 | `::test_a_dropped_citable_legend_is_disclosed_in_the_pack` — under a budget that drops `citable-evidence-blocks`, the rendered pack names it as withheld instead of silently listing nothing |
| A8 | R7, G1 | `::test_all_three_exit_grades_are_reachable_and_the_render_distinguishes_them` — three separate registrations produce `R`, `SU`, `S` on a frame assertion; `standing_view["exits"]` reports fall / revocation / contestation, three distinct values, contestation rounded to neither |
| A9 | G2 | `::test_rendering_the_frame_slice_moves_no_label` — two roots, the same graph, one rendering a non-empty slice; statuses, `att` and `dep` over the shared ids identical. **MUTATION PROOF pasted in VALIDATION.md** |
| A10 | G4 (C1) | `::test_the_slice_is_byte_identical_across_renders` — same problem, same state, two calls, identical bytes; and two independently replayed harnesses over one root agree |
| A11 | G5 (N1) | `::test_no_pack_emits_an_empty_provenance_slot` — both renderers under an everything-absent state; no provenance-shaped label appears at all, populated or blank; plus an AST check that `packs.py` and `calculus/render.py` emit no placeholder for one |
| A12 | G7 | `::test_the_slice_fits_the_pack_budget_and_its_allocation_is_logged` — the slice's source size is bounded by construction; `AllocationResult.accounting()` names it |
| A13 | G8 | the A9 import check in `DR-INV-axiom-basis` extended to `calculus/render.py`; A3/A4/A10 preservation rows re-run |
| A14 | C-PUBLIC | `python scripts/wheel_smoke.py` and `python -u scripts/wheel_operational_smoke.py` both green with **pins unchanged** — no new MCP tool and no new console script ships, so no pin moves. Proven, not asserted |
| A15 | C-GATE | `python -m pytest tests/ -q -n 4` → 0 failed; `python tools/docs_verify.py` FULL → only the 3 pre-existing `CON-run-identity.md` shallow-clone failures |

## 4. Map documents, moving in the same commits

| Document | What moves |
|---|---|
| `DR-CON-packs-and-token-economy` | the frame slice's deterministic allocation; the 15→16 / 11→12 section-slot census check; the `DISCLOSED_ON_DROP` fixed-point loop and its termination argument; a new NEGATIVE rule that the frame slice is never droppable (**named by the ladder**) |
| `DR-SEAM-llm-x-rules` | `frame_slice_context` as the new crossing; the two new call sites (**named by the ladder**) |
| `DR-SEAM-calculus-x-rules` | **NEW.** The `rules` → `calculus` edge S7 creates. Recorded as a finding: `INDEX.md`'s matrix had no row for this pair because the pair did not interact until now |
| `DR-CON-standing-and-background` | the three exit grades and the `exits` section of the standing view |
| `DR-SUB-calculus` | `render.py` in `Owns:`; the departure body in the closed set (9 → 10); the compiler's two-mention rule |
| `DR-INV-axiom-basis` | **A9 proved** (the render-side check the document itself demands "in the same commit"); A3, A4, A10 preservation rows |
| `docs/map/INDEX.md` | the new seam in the matrix |
| `docs/ERRATA.md` | only if this tranche finds a committed claim wrong |

## 5. The structural absences (asserted, not hoped for)

- **L-4, no scoring:** no module under `src/deepreason/{scheduler,rules,
  adjudication,informal}` may reference `DepartureDeclarationV1`,
  `departure`, `broken_ids` or the declaration commitment id. A grep-based
  negative check, the same shape `DR-CON-conjecture-kinds` uses for R-g.
- **L-4, structurally:** `compile_interface` emits no `DEPENDENCE` for a
  departure declaration — asserted on the compiler's OUTPUT, so a future
  edit fails rather than passes.
- **R5:** `calculus/scope.py` imports nothing from `render.py` or the
  declaration body, and `_FIELDS`/`_LISTS` stay closed.
- **A9:** `calculus/render.py` imports no `llm`, `adapter`, `seat`,
  `provider`, `qualification` or `adjudication` symbol.
- **Anti-`FrameDecisive` (G1):** no module maps `Status.SUSPENDED` on a
  frame assertion onto `REFUTED` or `SUSPENDED_UNSUPPORTED`;
  `EXIT_GRADES` has exactly three distinct values over three distinct
  labels.

## 6. Size, against C-SIZE

| Item | Production lines (estimate) |
|---|---|
| S1 `calculus/render.py` | 185 |
| S2 claims body | 45 |
| S3 compiler rule | 20 |
| S4 wf program + registration | 35 |
| S5 authoring operation | 40 |
| S6 pack sections + drop disclosure | 80 |
| S7 two call sites | 35 |
| S8 exit grades + view + CLI | 55 |
| S9 exports | 10 |
| **Total** | **505** |

Ladder allowance: 300-450 **plus 60-100 for the third grade** = 360-550.
**505 is inside it**, and inside C-SIZE's ~700 ceiling. Ledgered ceiling
for `tools/diff_budget.py` at every `[COMMIT]`: **560 production lines**
(505 + 11% headroom), measured over `src/` only. Tests and map documents
are budgeted separately and are not counted against it, following P4's
own separation of the two ceilings.

## 7. Assumptions recorded (SPEC is silent → smallest reading)

- **A-1. The articulation digest is deterministic, not summarised.**
  REQUEST is silent on how the digest is produced. The smallest reading
  that satisfies C-FROZEN's no-new-role rule is a bounded content head
  plus the subject's declared commitment ids. No seat is reached.
- **A-2. Exit grades are keyed to the CURRENT label**, per the ladder's
  own table ("Three grades, keyed to the label"), not to a replayed
  prefix transition. The Formalization defines exit as a transition
  between consecutive prefixes; a render answering "what grade is this
  frame in NOW" needs only the label, and taking the transition road
  would mean replaying every prefix on every render (C1 cost, no reader
  gain). **Recorded as a limit:** `standing_view["exits"]` reports the
  grade an assertion is IN, not the sequence number it left `U` at.
- **A-3. The critic pack's frame is the first problem its target is
  addressed to.** `_problem_context` already shows up to three problems;
  the slice uses the first, so the frame agrees with the standard the
  pack leads with. Recorded because a target addressed to two problems in
  two different scopes could carry a second frame nothing renders.
- **A-4. `DISCLOSED_ON_DROP` is four sections, not all of them.** The
  smallest reading of "no silent caps" that is epistemically load-bearing:
  sections whose absence changes what the model MAY DO. A dropped
  `neighbourhood` changes only what it sees.
- **A-5. No frame/pack inspection VIEW ships as a new surface** (C-PUBLIC).
  The expansion path for the digest is the EXISTING `deepreason standing
  --json` / MCP `run_standing`, whose returned dict grows. The MCP schema
  sha is taken over `tools/list` — names, descriptions and INPUT schemas —
  so a richer result moves no pin. Proven by A14, not asserted.

## 8. Stop conditions live for this tranche

- A design wanting a NEW LLM role → STOP (C-FROZEN). **Not triggered:**
  the digest is deterministic (A-1).
- Frozen-record semantics contact → STOP. **Not triggered:** §1 disposes
  of all four census rows and F1-F4 keep every surface at zero.
- SPEC plan over ~700 production lines → STOP. **Not triggered:** 505.
- A step failing twice the same way → STOP.
