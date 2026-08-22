# Validation for: Rung 4 — frame assertions and the standing view

Run at `c5a4206b`, against SPEC.md's items S1–S14 and REQUEST.md's R1–R20.

## Acceptance checks

**S1 — the frame-assertion body, and the closed set that did not grow.** PASS

    $ python -c "from deepreason.calculus import CLAIM_SCHEMAS; assert len(CLAIM_SCHEMAS)==9"
    CLAIM_SCHEMAS = 9 (unchanged)

    test_a_frame_assertion_is_an_ordinary_artifact                       PASSED
    test_no_new_event_rule_and_no_kind_field                             PASSED
    test_bounded_validity_is_content_not_a_third_value                   PASSED
    test_bounded_requires_its_domain_and_tolerance_and_universal_forbids_them  PASSED
    test_a_case_that_is_the_subject_is_refused                           PASSED
    test_the_closed_name_set_did_not_grow                                PASSED

**S2 — the mention law as well-formedness.** PASS

    test_the_compiler_makes_the_subject_a_mention_and_the_case_a_dependence   PASSED
    test_a_wound_reference_is_a_mention_never_a_dependence                    PASSED
    test_an_assertion_that_depends_on_its_subject_fails_well_formedness       PASSED
    test_a_controller_compiled_assertion_passes_well_formedness               PASSED

    $ python -c "from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; assert 'frame_assertion_wf' in S"
    frame_assertion_wf in _STRUCTURAL_PROGRAMS: True

**S3 — consult through separation, Rung 3b INVOKED not re-implemented.** PASS

    $ git diff --stat origin/main -- src/deepreason/calculus/separation.py
    (empty)

    test_a_separated_assertion_addressed_to_a_promotion_problem_is_consulted  PASSED
    test_an_unseparated_assertion_is_unconsultable_with_rung3bs_own_code      PASSED
    test_an_unconsultable_assertion_moves_no_edge_no_warrant_no_label         PASSED
    test_an_assertion_outside_a_promotion_problem_is_never_consulted          PASSED

Rung 3b's module has a ZERO-LINE diff. `consultability_of` calls
`separation.consultability` and returns its `FRAME_NOT_SEPARATED` verbatim.

**S4 — `standing(b)` derived, never stored.** PASS

    test_standing_is_recomputed_from_the_log_and_never_stored            PASSED
    test_no_field_was_added_to_problem_state_or_event                    PASSED

    $ grep -rqE "state\.standing|standing:" src/deepreason/ontology/
    no stored standing in ontology/: confirmed

**S5 — sigma in D-5's fixed finite DSL.** PASS

    test_scope_evaluates_on_problem_metadata_alone                       PASSED
    test_the_op_vocabulary_is_closed                                     PASSED
    test_the_same_problem_and_state_give_the_same_answer                 PASSED
    test_a_free_form_predicate_is_refused                                PASSED

    $ python -c "<no eval/exec/compile in scope.py>"
    no eval/exec/compile in scope.py: confirmed

**S6 — the read-only surface, and all four pins.** PASS

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas
    exit=0

    $ python -u scripts/wheel_operational_smoke.py
    wheel operational smoke passed: installed setup, explicit qualification
    (80 qualification calls; 418 total calls), readiness, question-only
    reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
    restart, budget ceiling, and pre-V6 fail-closed admission
    exit=0

    $ python -m pytest tests/test_mcp.py tests/test_mcp_help.py -q
    89 passed

    test_the_standing_surface_is_read_only_and_calls_no_model            PASSED

Live output on a committed root, which is also the absence-tolerance proof:

    $ deepreason --root experiments/live_engaged_2026-07-27/run-f4fa6663... standing
    (no artifact is currently framing any problem)
    exit=0

**S7 — the axiom-basis INV document.** PASS

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 61 document(s)

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)

`--audit` refuses checks that cannot fail; it refuses none of the new
document's. Two rows (A8, A9) say NOT YET PROVED and deliberately carry no
check for the unproven half, with an instruction to add one in the rung that
lands the work.

**S8 — what a promotion problem IS.** PASS

    $ python -c "from deepreason.ontology import SpawnTrigger"
    len(SpawnTrigger) = 10 | PROMOTION = promotion

    test_ensure_promotion_problem_is_idempotent                          PASSED
    test_an_assertion_outside_a_promotion_problem_is_never_consulted     PASSED

**S9 — Prop 12.5, standing never adjudicates, in its strongest form.** PASS

    test_frame_assertions_do_not_move_a_single_label                     PASSED
    test_label_computation_names_no_standing_symbol                      PASSED
    test_no_adjudication_module_imports_the_standing_view                PASSED

### The mutation proof (R13), in full — it found the test vacuous TWICE

This is the part worth reading, because the test passed under two mutations
before it earned its verdict.

**Mutation 1** — leak `consulted` into `compute_label0`:

    +        from deepreason.calculus.standing import consulted as _leak
    +        label0 = compute_label0(nodes, att)
    +        for _g in _leak(self):
    +            label0[_g.subject_id] = "accepted"

    test_frame_assertions_do_not_move_a_single_label ....... 1 passed   <-- WRONG
    test_status_changes_without_standing_changing .......... 1 failed

The Prop 12.5 test did NOT go red. Cause: it framed an ACCEPTED subject, so a
leak setting consulted subjects to `accepted` changed nothing. A run where
standing could only ever AGREE with the label has nothing to catch.

**Fix 1** — the shared graph now REFUTES its subject in both roots. "Refuted and
still framing" is both the interesting case for the calculus and the only one
with anything to detect.

**Mutation 2** — same leak, against the strengthened test:

    test_frame_assertions_do_not_move_a_single_label ....... 1 passed   <-- STILL WRONG

Cause: `consulted` reads `state.status`, and during `_adjudicate` that is the
PREVIOUS state, which does not yet contain the assertion. The leak never fired.
The mutation, not the test, was inert.

**Mutation 3** — leak `frame_assertions`, which is status-independent and is the
real hazard (label computation reading the frame layer at all):

    +        from deepreason.calculus.standing import frame_assertions as _leak
    +        label0 = compute_label0(nodes, att)
    +        for _aid, _body in _leak(self):
    +            label0[_body.subject_ref] = "accepted"

    $ python -m pytest tests/test_calculus_standing.py -q
    E   assert harness.state.status[subject.id] == Status.REFUTED
    E   AssertionError: assert <Status.ACCEPTED> == <Status.REFUTED>
    FAILED test_frame_assertions_do_not_move_a_single_label
    FAILED test_status_changes_without_standing_changing
    2 failed, 6 passed                                                  <-- RED

**Restored:**

    $ git diff --stat src/deepreason/harness.py
    (empty)
    $ python -m pytest tests/test_calculus_standing.py -q
    8 passed                                                            <-- GREEN

Note what the mutation touched: `harness.py`, three lines. The standing module
was unchanged throughout. Prop 12.5 is a property of the LABEL computation, not
of the standing module's read-only-ness.

**S10 — Prop 12.4, axis independence, both directions.** PASS

    test_status_changes_without_standing_changing                        PASSED
    test_standing_changes_without_status_changing                        PASSED

**S11 — Thm 12.3, S-10, L-2.** PASS

    test_a_frame_assertion_inherits_every_exit                           PASSED
    test_revocation_has_no_rule_of_its_own                               PASSED
    test_amend_then_continue_over_a_root_carrying_a_frame_assertion      PASSED

Thm 12.3 exercises all three exits on ONE assertion: `refuted` by direct
attack, reinstated by attacking the attacker's validity node (Lemma 6.1), then
`suspended_unsupported` by refuting its reach case.

S-10 asserts the absence in both admissible forms, because either alone is
satisfiable by the wrong thing — a structural scan alone is satisfied by naming
the code something else, and a behavioural exhibit alone does not show absence.
The structural half is anchored to AST NAMES rather than to source text, after
the first version failed on its own docstrings explaining the absence: a scan
that counted the explanation would force the absence to go unexplained.

**S12 — the map moved in the same commits.** PASS. See the Map section.

**S13 — the `standing-integrity` check (FROZEN SURFACE 3, granted).** PASS

    test_standing_integrity_fires_on_a_violated_mention_law              PASSED
    test_standing_integrity_is_silent_on_a_clean_root                    PASSED
    test_standing_integrity_reports_nothing_on_a_root_that_predates_it   PASSED

The first was RED before the check existed (`AssertionError: []`, 0 findings
where 1 was expected) and RED AGAIN after the first implementation, which is
the finding worth keeping: the check initially used the STRICT
frame-assertion recogniser, which requires the declared interface to match the
controller's compiler. An assertion violating the mention law is therefore not
recognised by it at all, and the check reported NOTHING on a root purpose-built
to violate the law. Recognition for CONSULT must be strict; recognition for
INTEGRITY must not be.

**S14 — reader-before-writer. CORRECTED: no root sweep.** PASS

    test_standing_integrity_reports_nothing_on_a_root_that_predates_it   PASSED

A root sweep was started and the operator killed it mid-run ("Why are you doing
a root sweep"). They were right. CLAUDE.md's standing law — operator ruling
2026-08-22, and the literal HEAD commit of `main` this branch was cut from —
retires the sweep as an instrument: "A reader change is proven by targeted,
mutation-proven regression tests on fixtures or single-root replays committed
in the same tranche; that is both cheaper and stronger than a sweep, because a
sweep can only confirm what a targeted test already explains." The tranche
instruction's C7 permitted a sweep on a reader change; the law forbids it; the
law wins, and I had read it at session start. No sweep output is recorded,
because none should exist. Cost: wall-clock only.

## Full gate

    $ python -m pytest tests/ -q -n 4
    3815 passed, 6 skipped in 1110.49s (0:18:30)

**0 failed.** PASS. Baseline per `docs/AUDIT_BASELINES.md` is 0 failed; no
assertion was weakened anywhere to reach it.

One flake appeared later, in a serial re-run of a stamped document's `Verify:`
line: `test_application_text_runs_d0.py::test_result_does_not_enter_recovery_
while_process_local_worker_is_alive`. ISOLATED before attribution, per C10: it
passed inside the 3815-test gate and passes twice run alone. It is the known
thread-timing flake, it touches no code this tranche changed, and it is NOT
attributed here.

## Record-behavior preservation

`verify_root` over the committed root
`experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`
reports **no `standing-integrity` finding** — pinned as a test against a
`git ls-files`-tracked root rather than a session fixture, per the durable-probe
rule. The check recognises frame assertions by a body and a commitment no root
written before 2026-08-22 contains, so additivity is structural, not hoped for.

## Frozen-surface diff

    $ git diff --stat origin/main..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
     src/deepreason/invariants.py | 52 ++++++++++++++++++++++++++++++++++++++++++
     1 file changed, 52 insertions(+)

    $ git diff --numstat <same paths>
    52   0   src/deepreason/invariants.py

**Non-empty, and covered by the grant** (REQUEST.md Amendment 2; recorded in
`docs/map/INV-frozen-surfaces.md` surface 3). **Insertions only, zero
deletions**, so no existing finding's shape, name, order or detail string moved.
Surfaces 1, 2, 4, 5: zero lines. Surface 5 in particular stayed at zero — no new
LLM role, no qualification digest moved, so no ~14-minute battery is owed.

### Blast-radius drift check at the boundary

    verdict: CONTACT
    frozen_surface_contacts:
     - replay-validation record formats (invariants.py) | DIRECT | src/deepreason/invariants.py
     - replay-validation record formats (invariants.py) | SYMBOL_INDIRECT | consulted
     - replay-validation record formats (invariants.py) | SYMBOL_INDIRECT | declared_frame_assertions
     - manifest schemas and validators (run_manifest.py) | SYMBOL_INDIRECT | consulted
    frozen_adjacent_contacts: []
    consumers.qualification_digest: [{'target': 'consulted', 'tier': 'PLAUSIBLE',
        'detail': 'referenced in src/deepreason/run_manifest.py'}]
    reachability direction changes: []

SPEC.md forecast ONE entry; four are reported. Disposed by MEASUREMENT, not
assurance:

- The two `invariants.py` `SYMBOL_INDIRECT` rows are the SAME granted contact
  re-reported at symbol granularity — same surface, same file, already granted.
- The `run_manifest.py` row and the qualification-digest row are a **substring
  false positive**, the ledgered `clamp` shape. Measured:

      $ git diff --numstat origin/main..HEAD -- src/deepreason/run_manifest.py
      (no output — the file is untouched)

      $ grep -n "consulted" src/deepreason/run_manifest.py
      2393:  # authority knobs live on Config only, consulted at mint sites) -- the
      2400:  # gate lives on Config only, consulted at scheduler dispatch sites, and
      3416:  is consulted. Other provider entries are not discovered or used.

      $ <AST import scan of run_manifest.py>
      calculus imports: NONE

  All three hits are English prose in comments that predate this tranche. The
  gate states its own method in each detail string — "grep-based; not proof of
  semantic contact" — so this is the gate working as documented.

**No drift beyond the grant. No new STOP owed.**

## Map

    $ python tools/docs_verify.py
    FAIL CON-run-identity.md:200  (shallow clone: unknown revision)
    FAIL CON-run-identity.md:202  (shallow clone: unknown revision)
    FAIL CON-run-identity.md:204  (shallow clone: unknown revision)
    docs_verify: 3 failed

**3 failed, all the C10 pre-existing shallow-clone baseline, 0 new.** PASS

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)                                    PASS

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 61 document(s)         PASS

    $ python tools/docs_verify.py --coverage
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 2 finding(s)

**Baseline, PROVEN rather than assumed** — the identical line comes from a
worktree at `origin/main`:

    (worktree at origin/main)
    $ python tools/docs_verify.py --coverage
    SEAM-periphery-x-verification.md: enforcement site not named: .../amendment/apply.py
    SEAM-schools-x-scratch.md: enforcement site not named: .../informal/trial.py
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 2 finding(s)

Byte-identical. Neither finding is this tranche's.  PASS

    $ python tools/docs_verify.py --stale
    docs_verify --stale: 8 document(s) worth re-reading

Every entry dispositioned, none left silent:

| Document | Disposition |
|---|---|
| `CON-standing-and-background` | **UPDATED** — stamp advanced to `c5a4206b`, `Verify:` re-run (55 passed) |
| `SUB-calculus` | **UPDATED** — stamp advanced, `Verify:` re-run (55 passed) |
| `SUB-verification` | **UPDATED** — stamp advanced, `Verify:` re-run |
| `SUB-application` | **UPDATED** — stamp advanced, `Verify:` re-run (the one flake isolated and cleared above) |
| `CON-run-identity` | dismissed — stale since `bce018ae5`, the all-configs tranche. Predates this work; not ours to stamp |
| `CON-schools` | dismissed — same commit, same reason |
| `SEAM-manifest-x-schools` | dismissed — same commit, same reason |
| `SUB-evidence` | dismissed — stale since `1a32fb193` (P4). Predates this work |

**New map checks added by this change:** `INV-axiom-basis.md` (a new document,
14 checks); new checks in `SUB-calculus` (frame assertions, the standing view,
the no-write/no-adjudication structural check, revocation's absence),
`CON-standing-and-background` (Props 12.4 and 12.5, derived-not-stored, the
consult site), `SEAM-adjudication-x-authority` (the seam extended to standing,
two checks), `INV-frozen-surfaces` (the granted contact), `SUB-periphery` (the
four-pin trap). Every one was RUN before it was written down.

**Record observables added vs sweep probes:** one observable — the
`standing-integrity` finding. Its probe is
`test_standing_integrity_reports_nothing_on_a_root_that_predates_it`, pinned to
a committed root. **No `root_sweep.py` probe is owed or permitted**: the sweep
is retired as an instrument (CLAUDE.md, 2026-08-22), and the retirement ruling
names a single-root replay as the stronger substitute, which is what this is.

**Wheel smoke:** the packaging surface MOVED (one new MCP tool). Both smokes
re-run at the boundary, both exit 0 — pasted under S6.

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 frame assertion as an ordinary artifact | S1 — 6 tests, incl. no-kind-field and bounded-as-content |
| R2 the mention law as well-formedness | S2 — the dependence-on-subject case fails with its own reason `frame-assertion-depends-on-subject` |
| R3 consult through separation | S3 — `separation.py` zero-line diff; Rung 3b's code called and its code returned |
| R4 `standing(b)` derived, never stored | S4 — identical view from a re-materialized harness; no field added anywhere |
| R5 sigma in D-5's fixed DSL | S5 — closed 9-op vocabulary, problem-record-only leaves, determinism across re-materialization |
| R6 read-only `standing` surface + all four pins | S6 — both smokes exit 0, `test_mcp`/`test_mcp_help` 89 passed |
| R7 the axiom-basis INV document | S7 — `INV-axiom-basis.md`, 11 axioms, `--audit` refuses none of its checks |
| R8 Prop 12.5, strongest form | S9 — two runs, identical labels, subject refuted in both |
| R9 Prop 12.4, both directions | S10 — two tests, one per direction |
| R10 Thm 12.3, every exit | S11 — three exits on one assertion |
| R11 S-10, revocation's absence asserted | S11 — structural (AST names) AND behavioural |
| R12 L-2 operations parity | S11 — amend then continue over a manifest-launched root carrying an assertion |
| R13 mutation proof on the Prop 12.5 test | S9 — all three mutations and both restores pasted in full |
| R14 axiom ledger: proves A4, A5, A7; preserves A1, A3, A6 | S7 — each row carries its rung and an executable check |
| R15 surface-3 grant requested in SPEC.md BEFORE code | SPEC.md S13 + the pasted `frozen_surface_contacts`; disposition at REQUEST.md Amendment 2; recorded in `INV-frozen-surfaces` |
| R16 R-by-R delivery with pasted proof | DELIVERY.md |
| R17 ceiling 963 | superseded-by R19 |
| R18 variance recorded | REQUEST.md Amendment 3 |
| R19 ceiling 1850 | **EXCEEDED at 2290 — see below. Reported, not hidden** |
| R20 variance cause named | REQUEST.md Amendment 3, and below |

## The ceiling, stated plainly

    $ python tools/diff_budget.py origin/main --ceiling 1850 --paths src tests docs/map scripts
    {"areas": {"src": 822, "tests": 983, "docs/map": 481, "scripts": 4},
     "total_insertions": 2290, "ceiling": 1850, "verdict": "EXCEEDED"}

**2290 against 1850.** I estimated this tranche wrong three times — 963, then
1832, then over again — and the pattern in all three misses is the same and is
mine: I priced new modules and new map documents at roughly half what the
existing ones in this repo already run at, when both were measurable from the
tree before I wrote a line.

The work did not grow. Every line traces to an R, no Rung 5/6/7 machinery is
present, and `src/` at 822 is above the ladder's 500–700 but the excess there is
two modules' docstrings, not extra behaviour. What overran past 1850 after the
raise:

| Item | At the raise | Final | Why |
|---|---|---|---|
| `docs/map/` | ~215 | 481 | `INV-axiom-basis.md` at 259 against a ~95 estimate — 11 axioms each needing a statement, a rung, a preservation list and a runnable check, plus the two NOT-YET-PROVED rows' explanations |
| `tests/` | 982 | 983 | flat |
| `src/` | 822 | 822 | flat |

So the entire post-raise overrun is one document: the axiom ledger, which R7
mandates and which the operator declined to defer twice.

## Assumptions carried

- **A1** Rung 4 owns what a promotion problem IS (`SpawnTrigger.PROMOTION` plus
  an idempotent registration); Rung 5 owns WHEN one is spawned.
- **A2** Rung 4 owns the departure protocol's content SLOT only; Rung 6 owns its
  behaviour. Nothing here interprets or acts on it.
- **A3** Sigma reads the `Problem` record and nothing else — all five fields
  exposed, nothing outside reachable.
- **A4** The `RECRIT_STANDING` collision is DISAMBIGUATED in the map, not
  renamed. Renaming is a compatibility decision and was not requested; parked
  with its price at PARKED.md P1.
- **A5** An absence is proven structurally AND behaviourally.
- **A6** No new LLM role, so frozen surface 5 stays at zero.

## Verdict: **PASS**

Every acceptance check passes, the full gate is 0 failed, the frozen-surface
contact is inside its grant with insertions only, the map verifies at its
baseline with 0 new failures and 0 vacuous checks, both wheel smokes are green,
and every R is demonstrated.

The one thing a reader should not skip: R19's ceiling is exceeded at 2290, and
that is a reporting fact, not a hidden one. It is the operator's call whether
the overrun matters; it is mine that it was visible before they were asked.
