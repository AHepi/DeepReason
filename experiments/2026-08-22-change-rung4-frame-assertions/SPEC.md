# Spec for: Rung 4 — frame assertions and the standing view
Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Authority read in full before this document, per C3: `LADDER.md` §Rung 4 plus
§2 (program-wide rules), §5 (proposition→rung table) and §5b (the axiom basis);
`docs/COMPUTABLE_CALCULUS.md` §9.1–9.4 and §12; `DECISIONS.md` D-5.

## Items

**S1 (R1, C3) — the frame-assertion body.**
`src/deepreason/calculus/claims.py`.
*Before:* `poietic.frame-assertion.v1` is in the CLOSED name set `CLAIM_SCHEMAS`
and is refused by `decode` with `claim-schema-not-implemented`.
*After:* `FrameAssertionV1` joins `_MODELS`/`_IMPLEMENTED`. Fields are exactly
Def 9.2's content: `subject_ref`, `scope` (a `declarative-scope.v1` document,
S5), `validity` ∈ {`universal`,`bounded`} with `validity_domain` /
`validity_tolerance`, `departure_protocol`, plus `reach_case_refs` (Def 9.2's
"dependence → each reach record cited as its case") and `succeeded_wound_refs`
("mention → the wounds of any incumbent it succeeds"). No `kind` field, no new
event rule: registration is `create_artifact`, exactly as a problem subject is.
A `model_validator` makes `bounded` CONTENT rather than a third value — bounded
requires both domain and tolerance, universal forbids both — and refuses
`subject_ref` appearing in `reach_case_refs` (a case that IS the subject would
be a dependence on the subject by another name).
    accept: `python -m pytest tests/test_calculus_frame_assertions.py -q` —
    `test_a_frame_assertion_is_an_ordinary_artifact`,
    `test_bounded_validity_is_content_not_a_third_value`,
    `test_no_new_event_rule_and_no_kind_field` pass.
    accept: `python -c "from deepreason.calculus import CLAIM_SCHEMAS; assert
    len(CLAIM_SCHEMAS)==9"` — the closed set does NOT grow; this rung supplies
    a producer for a name already declared.

**S2 (R2) — the mention law as well-formedness.**
`src/deepreason/calculus/compiler.py`, `src/deepreason/calculus/programs.py`,
`src/deepreason/measures/reach.py`.
*Before:* only `problem_subject_wf` / `premise_attribution_wf` exist.
*After:* `compile_interface` gains the frame-assertion rule — `subject_ref` →
`MENTION` (Law 9.4), each `reach_case_refs` → `DEPENDENCE`, each
`succeeded_wound_refs` → `MENTION`. `frame_assertion_wf` +
`FRAME_ASSERTION_COMMITMENT` join `programs.py`; the program checks the mention
law FIRST, with its own reason `frame-assertion-depends-on-subject`, before
delegating to the shared `_wf` controller-compiled comparison — so the
diagnostic names the law rather than reporting a generic interface mismatch.
`frame_assertion_wf` joins `_STRUCTURAL_PROGRAMS`: being a well-formed frame
assertion grounds no reach and immunises nothing.
    accept: `python -m pytest tests/test_calculus_frame_assertions.py -q` —
    `test_an_assertion_that_depends_on_its_subject_fails_well_formedness`
    (reason == `frame-assertion-depends-on-subject`),
    `test_the_compiler_makes_the_subject_a_mention_and_the_case_a_dependence`.
    accept: `python -c "from deepreason.measures.reach import
    _STRUCTURAL_PROGRAMS as S; assert 'frame_assertion_wf' in S"`

**S3 (R3) — consult through separation, invoking Rung 3b unchanged.**
`src/deepreason/calculus/standing.py` (new).
*Before:* `calculus/separation.py::consultability` has NO caller in `src/`, by
design (`DR-SUB-calculus` Traps row, Rung 3b's own SCOPE BOUNDARY).
*After:* `consultability_of` composes Def 9.2's four conditions in order —
recognised as a frame assertion; addressed to a promotion problem (S8);
`final(fa) == unrefuted`; and then **calls `separation.consultability`
verbatim** and returns ITS `Consultability` value with `FRAME_NOT_SEPARATED` /
`FRAME_ENDPOINT_UNREGISTERED` unchanged. Rung 3b's predicate is invoked, not
re-implemented and not re-argued: `separation.py` is not edited by this tranche.
    accept: `git diff --stat origin/main -- src/deepreason/calculus/separation.py`
    -> empty (Rung 3b's module is untouched).
    accept: `python -m pytest tests/test_calculus_frame_assertions.py -q` —
    `test_an_unseparated_assertion_is_unconsultable_with_rung3bs_own_code`
    (asserts the code string is imported from `separation`, not redefined) and
    `test_an_unconsultable_assertion_moves_no_edge_no_warrant_no_label`.
    accept: the `DR-SUB-calculus` "no caller in `src/`" check is REWRITTEN, not
    deleted (SCHEMA.md rule) — see S12.

**S4 (R4) — `standing(b)` as a derived view.**
`src/deepreason/calculus/standing.py`.
*After:* `standing_of(harness, subject_id)` returns a tuple of frozen
`StandingGrant` records recomputed from replayed state on every call —
Def 9.3, `standing(b) ⊒ background over σ ⇔ ∃ consulted fa`. `standing_view`
is the whole-run projection consumed by S9/S10 (render) only. Nothing is
stored: no field on `Problem`, `EpistemicState` or `Event`, no new event
payload, no relation table.
    accept: `python -m pytest tests/test_calculus_standing.py -q` —
    `test_standing_is_recomputed_from_the_log_and_never_stored` (registers a
    grant, reopens the root read-only in a fresh `Harness`, and asserts the
    identical view plus a byte-identical `log.jsonl` line count),
    `test_no_field_was_added_to_problem_state_or_event`.
    accept: `! grep -rqE "state\.standing|standing:" src/deepreason/ontology/`

**S5 (R5, C3) — σ in D-5's fixed finite DSL.**
`src/deepreason/calculus/scope.py` (new).
*Before:* no scope language exists.
*After:* `declarative-scope.v1`, whose SHAPE reuses `declarative_numeric_v1`
(spec v1.6, `simulation/compiler.py`): a JSON expression tree of
`{"const":…}` / `{"field":…}` / `{"list":…}` / `{"text":…}` leaves and
`{"op":…, "args":[…]}` nodes over a CLOSED nine-op vocabulary
(`and or not eq contains starts_with member any_contains empty`), with the same
depth and node bounds. It **evaluates**, it does not emit code — the numeric
mode's code-generation half is what makes that module 266 lines and is not
needed for a predicate. `compile_scope(document)` validates the whole tree up
front; `scope_admits(compiled, problem)` evaluates it against the `Problem`
record ALONE (`id`, `description`, `criteria`, `provenance.trigger`,
`provenance.from_`). No free-form predicate language, per D-5.
    accept: `python -m pytest tests/test_calculus_scope_predicate.py -q` —
    `test_scope_evaluates_on_problem_metadata_alone`,
    `test_the_op_vocabulary_is_closed`,
    `test_the_same_problem_and_state_give_the_same_answer` (C1 determinism, two
    evaluations plus one across a re-materialized harness),
    `test_a_free_form_predicate_is_refused`.
    accept: `python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/scope.py').read_text());
    assert not any(isinstance(n,ast.Call) and getattr(n.func,'id','') in
    {'eval','exec','compile'} for n in ast.walk(t))"`

**S6 (R6, C9) — the read-only `standing` surface, and all four pins.**
`src/deepreason/cli/main.py`, `src/deepreason/mcp_server.py`,
`scripts/wheel_smoke.py`, `scripts/wheel_operational_smoke.py`,
`tests/test_mcp.py`, `tests/test_mcp_help.py`.
*After:* `deepreason standing [--json]` prints the standing view for a root
(the `frontier`/`why` pattern: open `Harness`, render, return 0). MCP gains
`run_standing`, mirroring `run_findings` exactly — same `_RUN_ID` input schema
plus `json`, same `_managed_response` wrapper, read-only annotations. **Both
call no model and add no LLM role** (C4). All FOUR pins move in the SAME
commit: `EXPECTED_MCP_TOOLS` in both smoke scripts, the new
`EXPECTED_MCP_SCHEMA_SHA256`, `SUPPORTED_TOOLS` in `tests/test_mcp.py`, and
`SUPPORTED_TOOL_NAMES` in `tests/test_mcp_help.py`.
    accept: `python scripts/wheel_smoke.py` -> exit 0
    accept: `python -u scripts/wheel_operational_smoke.py` -> exit 0
    accept: `python -m pytest tests/test_mcp.py tests/test_mcp_help.py -q` -> 0 failed
    accept: `python -m pytest tests/test_calculus_standing.py -q` —
    `test_the_standing_surface_is_read_only_and_calls_no_model`.

**S7 (R7, R14) — the axiom-basis INV document.**
`docs/map/INV-axiom-basis.md` (new), `docs/map/INDEX.md` (one routing row).
*Before:* the map has NO id for the axiom basis; LADDER §5b assigns it to this
rung. Per `dr-drive-harness` §4 step 5, the missing id is a finding and
creating the document is part of the tranche.
*After:* A1–A10 plus Ax 4.1 (Genesis Inertness), each row carrying the
compressed statement, the rung that PROVES it, the rungs that PRESERVE it, and
an executable `check:` that would FAIL if the axiom stopped holding. A4, A5
(frame-assertion half) and A7 carry this rung's own proofs; A1, A3 and A6 carry
preservation checks.
    accept: `python tools/docs_verify.py` -> 3 failed (the pre-existing
    `CON-run-identity.md` shallow-clone baseline, C10), 0 new.
    accept: `python tools/docs_verify.py --audit` -> the new document's checks
    are not refused as unfailable.
    accept: `python tools/docs_verify.py --links` -> `DR-INV-axiom-basis`
    resolves.

**S8 (Q1→A1, serves R3/R15) — what a promotion problem IS.**
`src/deepreason/ontology/problem.py`,
`src/deepreason/calculus/operations.py`.
*After:* `SpawnTrigger.PROMOTION` plus `ensure_promotion_problem(harness,
subject_id, description)` — a deterministic, idempotent registration in the
`ensure_problem_subject` shape. This rung owns what a promotion problem IS,
because Def 9.2's consult condition is undefined without it; Rung 5 owns WHEN
one is spawned (the nomination measure-rule) and the five pinned criteria.
`ensure_promotion_problem` has a real caller in this rung's own consult path
and gate, so this is not `docs/ERRATA.md` E28's declared-and-unbuilt pattern.
    accept: `python -m pytest tests/test_calculus_frame_assertions.py -q` —
    `test_an_assertion_outside_a_promotion_problem_is_never_consulted`,
    `test_ensure_promotion_problem_is_idempotent`.
    accept: the three map checks pinning `len(SpawnTrigger) == 9` move to 10 in
    the same commit (census below).

**S9 (R8) — Prop 12.5, in its strongest form.**
`tests/test_calculus_standing.py`. No `src/` change: the property is that
`Harness._adjudicate` keeps reading `att`/`dep` only.
*Test:* build one graph twice in two roots. Root A registers the frame
assertions, its promotion problem, and its reach case; root B registers only
the artifacts the labels are computed over. Assert the `status` maps restricted
to the shared artifact ids are IDENTICAL, and that `att`/`dep` restricted the
same way are identical.
    accept: `python -m pytest tests/test_calculus_standing.py::test_frame_assertions_do_not_move_a_single_label -q`
    accept (R13, mutation): in a scratch copy, make `final_labels` consult the
    standing view; the test goes RED; restore; the test goes GREEN. Both runs
    pasted in VALIDATION.md.

**S10 (R9) — Prop 12.4, both directions.**
`tests/test_calculus_standing.py`.
*Test A (status moves, standing does not):* attack the SUBJECT. `status(b)`
goes `refuted`; `standing_of(b)` is unchanged, because the assertion only
MENTIONS `b`.
*Test B (standing moves, status does not):* attack the REACH CASE. The
assertion loses support → `suspended_unsupported` → no longer consulted →
`standing_of(b)` becomes empty; `status(b)` is unchanged.
    accept: `python -m pytest tests/test_calculus_standing.py -q` —
    `test_status_changes_without_standing_changing`,
    `test_standing_changes_without_status_changing`.

**S11 (R10, R11, R12) — Thm 12.3, S-10, and L-2.**
`tests/test_calculus_frame_assertions.py`, `tests/test_calculus_standing.py`.
*Thm 12.3:* three exits on one assertion — `refuted` by direct attack;
`suspended_unsupported` by refuting its reach case; reinstated (Lemma 6.1) by
attacking the attacker's validity node.
*S-10:* the absence is asserted in TWO admissible forms (Q5→A5): a structural
scan proving no `revoke`/`revocation` symbol or branch exists anywhere in
`src/deepreason/calculus/`, AND the behavioural exhibit that revocation
nonetheless happens — Test B of S10 is the whole mechanism.
*L-2:* `deepreason amend` then `deepreason continue` over a root carrying a
frame assertion, reaching the same typed terminal, with the assertion and its
standing intact across the amendment epoch.
    accept: `python -m pytest tests/test_calculus_frame_assertions.py::test_a_frame_assertion_inherits_every_exit
    tests/test_calculus_frame_assertions.py::test_revocation_has_no_rule_of_its_own
    tests/test_calculus_standing.py::test_amend_then_continue_over_a_root_carrying_a_frame_assertion -q`

**S12 (R15, C9) — the map moves in the same commits.**
`docs/map/SUB-calculus.md`, `docs/map/CON-standing-and-background.md`,
`docs/map/SEAM-adjudication-x-authority.md`, `docs/map/INV-frozen-surfaces.md`,
`docs/map/SEAM-ontology-x-rules.md`, `docs/map/SUB-ontology.md`,
`docs/map/SUB-rules.md`, `docs/map/INDEX.md`.
`SUB-calculus`: the frame-assertion body, its compiler rule, the consult path;
the "`consultability` has NO caller" trap row REWRITTEN to say when it gained
one (never deleted — SCHEMA.md). `CON-standing-and-background`: advanced from
rationale to MECHANISM, per LADDER's exit-artifact list, and its
`RECRIT_STANDING` trap row rewritten (Q4→A4). `SEAM-adjudication-x-authority`:
the agreement extended from authority to standing — the seam whose content is
the ABSENCE of traffic now also says standing never reaches label computation,
with S9's test as its instrument. `INV-frozen-surfaces`: surface 3's granted
contact recorded in the shape of the 2026-08-21 seat-instance grant. The three
`len(SpawnTrigger) == 9` checks move to 10.
    accept: `python tools/docs_verify.py` -> 3 failed (baseline), 0 new.

**S13 (R15) — the `standing-integrity` epistemic check.**
`src/deepreason/invariants.py`, `src/deepreason/verification/report.py`.
**FROZEN SURFACE 3 — grant requested below, BEFORE any code.**
*After:* `verify_root` gains one additive `fail("standing-integrity", …)` clause
with two limbs, exactly as R15 words them: (a) the mention law held — no
recognised frame assertion in the root carries a `DEPENDENCE` ref on its own
subject; (b) every assertion the standing view CONSULTS is addressed to a
promotion problem and is separated. `"standing-integrity"` joins
`_EPISTEMIC_CHECKS` so it routes to the epistemic channel. Additive: a root
with no frame assertions produces no new finding and its report is unchanged.
    accept: `python -m pytest tests/test_calculus_standing.py -q` —
    `test_standing_integrity_fires_on_a_violated_mention_law` (a hand-registered
    bad interface, RED before the check exists — pasted in VALIDATION.md).
    accept: an absence-tolerant reader lands with the writer in one commit —
    `verify_root` over a pre-existing committed root reports no
    `standing-integrity` finding (S14).

**S14 (C7) — reader-before-writer. CORRECTED at execution: no sweep.**
S13 changes a current-version reader, and this item originally planned an
informational root sweep on C7's wording ("run it only if you change a
current-version reader"). **That was wrong**: CLAUDE.md's standing law, operator
ruling 2026-08-22 and the literal HEAD commit of `main`, RETIRES the sweep as an
instrument outright — "A reader change is proven by targeted, mutation-proven
regression tests on fixtures or single-root replays committed in the same
tranche; that is both cheaper and stronger than a sweep, because a sweep can
only confirm what a targeted test already explains." A sweep was started and the
operator killed it mid-run. C7 permits; the law forbids; the law wins.

The proof the law asks for instead is what this tranche already commits, and it
is the stronger one: a single-root replay against a COMMITTED root predating the
frame layer, asserting the new check is silent on it — plus the mutation-proven
Prop 12.5 test, which a sweep could not have produced at all.
    accept: `python -m pytest tests/test_calculus_standing.py::test_standing_integrity_reports_nothing_on_a_root_that_predates_it -q`
    -> 1 passed, against a `git ls-files`-tracked root.
    accept: no `root_sweep.py` invocation appears anywhere in this tranche's
    artifacts as a required step.

## Assumptions (operator may override)

**A1 (Q1) — Rung 4 owns what a promotion problem IS; Rung 5 owns when one is
spawned.** Def 9.2 defines "consulted" as "addressed to a promotion problem ∧
final = unrefuted", so without the notion this rung cannot define its own
central predicate, and R15's own check names it. The smallest form that is not
`docs/ERRATA.md` E28's declared-and-unbuilt pattern is one enum member plus one
idempotent registration operation with a real caller here (S8). LADDER's Rung 5
work list is untouched: nomination as a measure-rule, the spawn trigger's
firing condition, and the five pinned criteria all stay there. Assumed,
operator may override.

**A2 (Q2) — Rung 4 owns the departure protocol's CONTENT SLOT only, not its
behaviour.** Def 9.2 lists it as a content field of the assertion; LADDER Rung
6 is titled "Frame render semantics and the departure protocol". So the body
carries `departure_protocol` as opaque authored text this rung stores and
renders verbatim, and nothing in this rung interprets or acts on it. Assumed,
operator may override.

**A3 (Q3) — σ reads the `Problem` record and nothing else.** The calculus says
"a total computable predicate over problem records"; R5 says "evaluated on
problem metadata alone". The `Problem` record is exactly `id`, `description`,
`criteria`, `provenance.trigger`, `provenance.from_`, and all five are exposed.
Nothing outside it is readable — not artifact state, not status, not the log —
which is what makes C1 determinism structural rather than promised. Assumed,
operator may override.

**A4 (Q4) — the `RECRIT_STANDING` collision is DISAMBIGUATED, not renamed.**
`CON-standing-and-background` parks the rename "to Rung 4, where the collision
becomes real". The collision does become real here. But the rename itself is,
in that document's own words, "a compatibility decision rather than vocabulary
work" — `RECRIT_STANDING` is a `Config` field readable from profile YAML — and
it appears nowhere in the operator's WORK list. Smallest reading: this rung
rewrites the trap row to state that the collision is now REAL and which sense
each name carries, and leaves the field name alone. The rename stays in
PARKED.md with its price. Assumed, operator may override.

**A5 (Q5) — an absence is proven structurally AND behaviourally.** A structural
scan alone can be satisfied by naming the code something else; a behavioural
exhibit alone does not show the absence. S11 does both. Assumed, operator may
override.

**A6 — no new LLM role, so surface 5 stays at zero (C4).** The standing view is
pure computation over replayed state; the CLI and MCP surfaces render it. No
seat, no pack section, no provider call. Nothing in this plan needs the
operator's ~14-minute STOP.

## Questions for operator — ASKED AND ANSWERED 2026-08-22

**Q-OP-1 — the frozen-surface grant (R15).** GIVEN, on the path R15 itself
prescribes: the computed contact is exactly the one R15 forecast, the request
was recorded in SPEC.md before any code, and the operator answered against this
committed document. Bounded to one additive clause plus the check name; any
wider contact is a new stop. Full reasoning: REQUEST.md Amendment 2.

**Q-OP-2 — the budget ceiling (C6).** ANSWERED. Operator, verbatim: "Proceed at
963 (Recommended)". **963 is this tranche's ledgered ceiling** (R17); C6's ~900
is `superseded-by:R17`. Variance recorded at REQUEST.md R18.

## Out of scope (explicit)

- Nomination as a measure-rule, the promotion spawn trigger's firing condition,
  and the five pinned promotion criteria — LADDER Rung 5. Not requested.
- Frame render semantics, pack frame slices, the departure protocol's
  behaviour — LADDER Rung 6. Not requested.
- Wounds, falls, succession, Prop 9.6 — LADDER Rung 7. Not requested.
- Renaming `Config.RECRIT_STANDING` / `_standing_recrit_pool` — A4; PARKED.
- Moving `premises.py` onto the claim substrate, and gating
  `standing_attributions` on separation — Rung 3b PARKED P1. Not requested.
- `knowledge(a)` (Prop 12.6) — LADDER Rung 5, D-4. Not requested.

## Frozen-surface contact forecast

`python tools/blast_radius.py --files <the eleven existing target files>
--symbols FrameAssertionV1 frame_assertion_wf compile_scope evaluate_scope
standing consulted_frame_assertions ensure_promotion_problem
file_frame_assertion`

`frozen_surface_verdict: CONTACT`

`frozen_surface_contacts` (the tool's own list, verbatim):

    [
     {
      "surface": "replay-validation record formats (invariants.py)",
      "tier": "DIRECT",
      "target": "src/deepreason/invariants.py",
      "detail": "target file is surface path src/deepreason/invariants.py"
     }
    ]

`frozen_adjacent_contacts`: `[]`

`consumers.qualification_digest`: `[]` — surface 5 stays at zero (A6, C4).
`consumers.wheel_smoke_pins`: `[]` — the gate reports none because the new tool
name does not exist yet; S6 moves all four pins by hand and the smokes are the
accept.

`reachability`: all eight declared symbols report `status_current: UNKNOWN` —
they do not exist yet. Per `dr-spec-change` step 5 the manual grep is therefore
REQUIRED as the cross-check, and it is the census below.

**This is R15's forecast contact, and the grant is requested here, before any
code, per the discipline and `INV-frozen-surfaces`'s own Trap ("A STOP already
written in prose is not a STOP that was obeyed").** What is asked for: ONE
additive `fail("standing-integrity", …)` clause in `verify_root` plus the
check's name in `_EPISTEMIC_CHECKS`. No existing finding's shape, name, order or
detail string changes; a root with no frame assertions produces byte-identical
output, which S14's sweep measures rather than asserts.

Surfaces 1 (`capabilities/state.py`), 2 (`harness.py`), 4 (`run_manifest.py`)
and 5 (`qualification.py`): **zero**, and the gate agrees — none appears in the
contact list. Per C5, no `Config` knob is planned; if execution finds one is
needed, it lands with its unconditional `_versioned_source_config_data` line for
EVERY schema version and the tranche says so at that step.

## Blast-radius census

Every hit from the gate's `consumers` plus the manual grep, classified. Nothing
omitted.

**`standing` (bare symbol) — 24 test hits, ALL prose or unrelated identifiers.**
Verified by `grep -rn "\bstanding\b" tests/ docs/map/`: `_standing_recrit_pool`,
`standing_attributions`, `RECRIT_STANDING`, `under standing attack`, and English
prose. **MUST NOT MOVE.** Two are load-bearing and named here so they cannot be
outrun: `tests/test_calculus_vocabulary.py:81` (`assert "standing" not in
counts`) and `CON-standing-and-background`'s check
(`! grep -q '"standing"' src/deepreason/status_display.py`). This rung's new
symbols are `standing_of` / `standing_view` / `run_standing`, and
`status_display.py` is not edited.

**`FrameAssertionV1`, `frame_assertion_wf`, `compile_scope`, `evaluate_scope`,
`consulted_frame_assertions`, `ensure_promotion_problem`,
`file_frame_assertion`, `run_standing`, `standing-integrity`** — zero hits in
`src/`, `tests/`, `docs/map/`. No collision. **NOTHING TO MOVE.**

**`len(SpawnTrigger) == 9` / the exact sorted trigger-name list — 3 map checks.**
`docs/map/SUB-rules.md:144`, `docs/map/SUB-ontology.md:131`,
`docs/map/SEAM-rules-x-scratch.md:142`. **EXPECTED TO MOVE** (S8 adds
`PROMOTION`); all three update in the same commit. No TEST pins the count —
`tests/test_decommissioned_pipeline_stays_out.py` asserts `SUCCESSOR` exists and
has no producer, which stays true.

**`len(CLAIM_SCHEMAS) == 9` — `docs/map/SUB-calculus.md:17`. MUST NOT MOVE.**
This rung supplies a producer for an already-declared name; the closed set does
not grow. This is the check that would catch an accidental ontology addition.

**`consultability` has no caller in `src/` — `docs/map/SUB-calculus.md` Traps.**
**EXPECTED TO MOVE**: S3 gives it its first caller, which is what Rung 3b said
Rung 4 would do. Rewritten to say when, never deleted (SCHEMA.md).

**`src/deepreason/invariants.py` — 58 map-check hits across 20 documents.**
All assert OTHER invariants of that file; an ADDITIVE clause moves none of them.
**MUST NOT MOVE**, and `docs_verify` full is the instrument (S7 accept).

**`src/deepreason/measures/reach.py` — 7 map-check hits.** The
`_STRUCTURAL_PROGRAMS` membership check in `SUB-calculus.md` names two programs
by literal; **EXPECTED TO MOVE** to name three.

**`src/deepreason/cli/main.py`, `src/deepreason/mcp_server.py`.** The four
wheel-smoke/MCP pins. **EXPECTED TO MOVE**, all four in one commit (R6).

## Blast-radius census — ADDENDUM, recorded at execution (2026-08-22)

The census above missed ONE map check, and it is recorded rather than quietly
fixed, because a census that is corrected silently stops being an instrument.

**`docs/map/SEAM-evaluation-x-ontology.md:54` — the program-call census inside
`programs.py::evaluate`.** It pins the exact sorted list of functions that
`evaluate` calls with an `artifact` argument, and registering
`frame_assertion_wf` in `PROGRAMS` adds a name to it. **EXPECTED TO MOVE**,
updated in the same commit as the code.

Why the census missed it: the declared target list named
`src/deepreason/calculus/programs.py` but NOT `src/deepreason/programs.py` —
the top-level program registry a new program must also be registered in. The
gate reported consumers only for files it was given, and it was not given that
one. The lesson is the census's own: declare the registry a new entry lands in,
not only the module that defines the entry.

What caught it: `docs_verify --fast` at the Phase B/C map step, which is where
the plan put it — three commits before the boundary gate would have. That is
the census working through its backstop rather than failing.

## Budget

    python3 -c "print(sum([45, 22, 30, 3, 85, 110, 55, 6, 15, 28, 1, 25, 40]))"   -> 465   # src
    python3 -c "print(sum([6, 290, 202]))"                                        -> 498   # pins + tests + map
    python3 -c "print(465 + 498)"                                                 -> 963   # total

| Item | Lines |
|---|---|
| `calculus/claims.py` — `FrameAssertionV1` + validator (S1) | 45 |
| `calculus/compiler.py` — the frame rule (S2) | 22 |
| `calculus/programs.py` — `frame_assertion_wf` + commitment (S2) | 30 |
| `measures/reach.py` — one structural-program name (S2) | 3 |
| `calculus/scope.py` (new) — σ's fixed DSL (S5) | 85 |
| `calculus/standing.py` (new) — consult path + derived view (S3, S4) | 110 |
| `calculus/operations.py` — promotion problem + file assertion (S8) | 55 |
| `ontology/problem.py` — `SpawnTrigger.PROMOTION` (S8) | 6 |
| `calculus/__init__.py` — exports | 15 |
| `invariants.py` — `standing-integrity` (S13) **[FROZEN 3]** | 28 |
| `verification/report.py` — one check name (S13) | 1 |
| `cli/main.py` — `deepreason standing` (S6) | 25 |
| `mcp_server.py` — `run_standing` (S6) | 40 |
| **`src/` subtotal** | **465** |
| the four public-surface pins (S6) | 6 |
| `tests/` — three files, ~14 test functions (S1-S13) | 290 |
| `docs/map/` — new `INV-axiom-basis.md` (~95) + 7 edited documents (~107) (S7, S12) | 202 |
| **total** | **963** |

4 commits: (1) body + compiler + wf + scope, (2) standing view + consult path +
promotion problem, (3) the public surface + all four pins, (4) the
`standing-integrity` check. Map documents ride the commit that changes their
code (SCHEMA.md rule 1). Validation artifacts follow.

**Stated against C6, and answered.** LADDER estimates 500–700; `src/` at **465
is BELOW the ladder's own lower bound**. The total of **963 exceeded the ~900
STOP threshold by 63 lines**; the tranche stopped, itemized the variance, priced
three roads, and the operator chose "Proceed at 963". 963 is the ceiling
`tools/diff_budget.py` is checked against at every `[COMMIT]` step. No
requirement grew and no Rung 5/6/7 machinery is present.

**Declared areas, for `tools/diff_budget.py --paths`:** `src tests docs/map
scripts`. The ceiling measures THE CHANGE, not the tranche's own ledger
(REQUEST.md, SPEC.md, CHECKLIST.md, PARKED.md, VALIDATION.md, DELIVERY.md);
without `--paths` the tool sums those too and reports EXCEEDED on documents the
itemization above never counted. `dr-execute-step` prescribes the flag; naming
the areas here is what makes it usable.

Frozen surfaces touched: **surface 3 (`invariants.py`), additive, grant
requested above.**

Rubric: 6/6 yes.
