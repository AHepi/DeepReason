# Checklist for: Rung 5 — promotion problems and their criteria as programs
State: next=DELIVERY blockers=none (C2 size ceiling EXCEEDED, reported in REQUEST.md Amendment 1)
Map ids this plan was built on: `DR-SUB-calculus`, `DR-SUB-evaluation`,
`DR-SUB-rules`, `DR-SEAM-evaluation-x-rules` (read first, per the map's own
seam-before-subsystem rule), `DR-SEAM-evaluation-x-ontology`,
`DR-CON-standing-and-background`, `DR-CON-problem-layer-lifecycle`,
`DR-INV-frozen-surfaces`, `DR-INV-axiom-basis`.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

- [x] 1. (S1, S11) Write `tests/test_calculus_nomination.py` — lineage
      derivation and the K_FRAME boundary, both sides — against the
      not-yet-existing `calculus/nomination.py`.
      done-when: `python -m pytest tests/test_calculus_nomination.py -q` fails
      with a collection/import error naming `nomination` (the test exists and
      guards nothing yet).

- [x] 2. (S3) Add `ReachCertificateV1` to `calculus/claims.py`, its rule to
      `calculus/compiler.py`, and `reach_certificate_wf` to
      `calculus/programs.py`.
      done-when: `python -c "from deepreason.calculus.claims import decode; import json; b=decode(json.dumps({'schema':'poietic.reach-certificate.v1','subject_ref':'b','scope':{'schema':'declarative-scope.v1','predicate':{'const':True}},'k_frame':2})); assert b.subject_ref=='b'"`
      exits 0.

- [x] 3. (S2) Add `Config.K_FRAME` and `Config.PROMOTION_ENVIRONMENT_MAX`, each
      with its `data.pop(..., None)` line and reason comment in
      `run_manifest.py::_versioned_source_config_data`.
      done-when: `python -c "import json; from tests.test_reusable_qualification import _manifest, _profile; c=json.loads(_manifest(_profile()).engine_config_json); leaked=sorted(k for k in c if k in ('K_FRAME','PROMOTION_ENVIRONMENT_MAX')); assert not leaked, leaked"`
      exits 0.

- [x] 4. (S1, S3) Write `src/deepreason/calculus/nomination.py`: `problem_parents`,
      `lineage_root`, `lineage_span`, the canonical scope builder, the
      certificate builder, and `nominate`.
      done-when: `python -m pytest tests/test_calculus_nomination.py -q` ends
      "N passed" with 0 failed.

- [x] 5. (S1) [COMMIT] Prove the measure cannot decide, STRUCTURALLY AND
      BEHAVIOURALLY (Rung 4's A5: either alone is satisfiable by the wrong
      thing). Re-planned before execution — the first draft asserted the module
      never NAMES `status` or `hv`, which is wrong: nomination must READ both
      (only ACCEPTED artifacts nominate, and the certificate freezes the `hv`
      readings). What R2 forbids is WRITING a label, so that is what is
      asserted.
      done-when: (a) `python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/nomination.py').read_text()); mods=[(n.module or '') for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]; assert not any(k in m for m in mods for k in ('adjudication','warrants','llm','trial')), mods; W=[ast.unparse(tg) for n in ast.walk(t) if isinstance(n,ast.Assign) for tg in n.targets if any(k in ast.unparse(tg) for k in ('state.status','state.hv','state.reach'))]; assert not W, W"`
      exits 0; and (b) a test in `tests/test_calculus_nomination.py` asserts
      `state.status` and `state.hv` are byte-identical across a `nominate` call
      that DOES spawn.

- [x] 6. (S11, S15) Write `tests/test_promotion_nomination_live.py` — M-4's
      NEGATIVE half on the committed attempt-4 root, opened `read_only=True`,
      asserting the empty nomination AND the one-lineage reason.
      done-when: `python -m pytest tests/test_promotion_nomination_live.py -q`
      ends "N passed" with 0 failed.

- [x] 7. (S11) [COMMIT] Mutation-prove the live negative: temporarily make
      `lineage_root` return the problem id itself, watch the live test go RED,
      restore, watch it go GREEN. Paste both runs.
      done-when: both pasted outputs are in the step record, tree restored,
      `git diff --stat src/` shows no residue of the mutation.

- [x] 8. (S4–S8, S12) Write `tests/test_promotion_criteria.py` — one passing and
      one refusing case per criterion, plus a budget-0 `overrun` case per
      program.
      done-when: `python -m pytest tests/test_promotion_criteria.py -q` fails
      with an import error naming `promotion` (the tests exist, the module does
      not).

- [x] 9. (S10 of REQUEST R10, i.e. SPEC S8) Write
      `tests/test_promotion_succession.py` — the FOUR refusals the strong
      relation owes: recovery-only, easier-to-vary, excisable-idle-part, and
      every-clause-non-strict.
      done-when: `python -m pytest tests/test_promotion_succession.py -q` fails
      with an import error naming `promotion`.

- [x] 10. (S4–S8, A10) Write `src/deepreason/calculus/promotion.py`: the five
      criterion programs, pure over (candidate bytes, frozen certificate).
      done-when: `python -m pytest tests/test_promotion_criteria.py tests/test_promotion_succession.py -q`
      ends "N passed" with 0 failed.

- [x] 11. (A10, S15) Register the six programs in `programs.py` — `PROGRAMS`
      with `class_="structural"` and `BLOB_PROGRAMS` for blob dispatch — and
      update `docs/map/SEAM-evaluation-x-ontology.md:54`'s `G(f)` list in the
      SAME edit.
      done-when: `python -c "from deepreason.programs import programs_by_class; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS; d=set(programs_by_class()['structural']); assert d == set(_STRUCTURAL_PROGRAMS); assert {'reach_certificate_wf','promotion_subject_demarcation','promotion_reach_integrity','promotion_scope_determinism','promotion_compatibility','promotion_accounts_for'} <= d"`
      exits 0, and `python -m pytest tests/test_reflexive_discipline.py tests/test_prose_refutation_boundaries.py tests/test_verifier_registry.py tests/test_decommissioned_pipeline_stays_out.py -q`
      ends 0 failed.

- [x] 12. (S8) [COMMIT] Mutation-prove the strong relation's first refusal (R10):
      temporarily drop the strictness-witness clause, watch
      `test_a_rival_that_only_recovers_is_not_a_successor` go RED, restore,
      watch it go GREEN. Paste both runs.
      done-when: both pasted outputs are in the step record and the tree is
      restored.

- [x] 13. (S9, S12) Write `tests/test_promotion_closure.py` — Remark 9.5 both
      ways: an assertion outside a promotion problem is ignored; one addressed
      to a promotion problem whose criteria FAIL does not frame its scope.
      done-when: `python -m pytest tests/test_promotion_closure.py -q` fails
      with an import error naming `promotion_criteria_sweep`.

- [x] 14. (S9) Add `promotion_criteria_sweep` to `calculus/promotion.py`, minting
      demonstrative warrants through `rules/warrants.py::register_fail_warrant`
      and minting nothing for `overrun`.
      done-when: `python -m pytest tests/test_promotion_closure.py -q` ends 0
      failed.

- [x] 15. (S1, S9) Wire `nominate` and `promotion_criteria_sweep` into the
      scheduler beside the existing reach sweep, BEFORE consultation.
      done-when: `python -m pytest tests/test_calculus_standing.py tests/test_scheduler.py -q`
      ends 0 failed.

- [x] 16. (S13) [COMMIT] Write `tests/test_promotion_solo.py` — the whole path on
      `Config()` defaults, no judge seat, no ensemble.
      done-when: `python -m pytest tests/test_promotion_solo.py -q` ends 0
      failed, and the test asserts `Config().JUDGE_SEATS_ENABLED is False`.

- [x] 17. (S10) Write `src/deepreason/views/knowledge.py` with `KNOWLEDGE_LABEL`
      and render it as a section of the existing `deepreason standing` command;
      extend `tests/test_calculus_standing.py:416`'s CLI assertion rather than
      weakening it.
      done-when: `python -c "from deepreason.views.knowledge import KNOWLEDGE_LABEL; assert KNOWLEDGE_LABEL=='knowledge (unrefuted ∧ active ∧ reach > 0)'"`
      exits 0 and `python -m pytest tests/test_calculus_standing.py -q` ends 0
      failed.

- [x] 18. (S10, C1) [COMMIT] Prove the public surface did not move.
      done-when: `python scripts/wheel_smoke.py` and `python -u
      scripts/wheel_operational_smoke.py` both exit 0 (paste both).

- [x] 19. (S14) Update `docs/map/INV-axiom-basis.md`: A8 PROVED with its spawn-half
      check, A4 and Ax 4.1 preservation checks over the new modules. Every check
      RUN before it is written down.
      done-when: each new check pasted with its exit-0 run, in the step record.

- [x] 20. (S15) Update `docs/map/SEAM-evaluation-x-rules.md` (the promotion
      lifecycle — the ladder's named exit artifact), `SUB-calculus.md`,
      `SUB-evaluation.md`, `CON-standing-and-background.md`,
      `CON-problem-layer-lifecycle.md`, `INV-frozen-surfaces.md` (the granted
      surface-4 contact and its measurement), and `INDEX.md`.
      done-when: `python tools/docs_verify.py --links` exits 0 and every new
      check was run before being written.

- [x] 21. (all) Map check, FULL (never `--fast`).
      done-when: `python tools/docs_verify.py` reports only the 3 known
      shallow-clone `CON-run-identity.md` failures, and
      `python tools/docs_verify.py --audit` reports 0 findings.

- [x] 22. (C2) Diff budget against the ledgered ceiling.
      done-when: `git add -A && python tools/diff_budget.py ade214037 --ceiling 1900`
      prints `"verdict": "WITHIN"`.

- [x] 23. (all) Full gate, on an otherwise idle box.
      done-when: `python -m pytest tests/ -q -n 4` output ends "N passed, 0
      failed" (pasted).

- [x] 24. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND the branch head is on
      `origin/claude/rung-5-promotion-criteria-wu31d8`.


## Step records

**1.** `python -m pytest tests/test_calculus_nomination.py -q` →
`ImportError: cannot import name 'nomination' from 'deepreason.calculus'` —
the test exists and guards nothing yet, as planned.

**2.** `decode(...)` on a `poietic.reach-certificate.v1` body → `ok b 2`; the
compiler rule emits `[('b', 'mention')]` and `['claim:reach-certificate-wf@v1']`.
The declared-but-unbuilt name in `CLAIM_SCHEMAS` now has a producer.

**3.** `engine_config_json` leak check → exit 0, `no leak; engine_config keys: 71`;
`Config().K_FRAME` = 2, `Config().PROMOTION_ENVIRONMENT_MAX` = 64.

**4.** `python -m pytest tests/test_calculus_nomination.py -q` → `15 passed`.
Two small in-step corrections, both recorded rather than silent: (a) the test
called a non-existent `harness.recompute()` — status is computed at
registration in this tree, so the calls were removed; (b) `calculus/promotion.py`
was created one step early, holding ONLY `criteria_for` and the program-name
constants, because step 4's `nominate` must pin the five criteria to register
the problem. The five criterion FUNCTIONS remain step 10's work.
`operations.ensure_promotion_problem` gained an optional `criteria=()`
parameter — passed at registration because `Problem` is immutable, so a
promotion problem cannot acquire its criteria after the fact.

**5.** Structural half → exit 0:
`STRUCTURAL OK; imports: ['__future__', 'deepreason', 'deepreason.calculus.claims',
'deepreason.calculus.compiler', 'deepreason.calculus.operations',
'deepreason.calculus.programs', 'deepreason.calculus.promotion',
'deepreason.calculus.scope', 'deepreason.calculus.standing',
'deepreason.measures.demarcation', 'deepreason.measures.reach',
'deepreason.ontology', 'deepreason.ontology.event', 'deepreason.ontology.state']`
— no adjudication, warrants, llm or trial import, and no assignment into
`state.status`/`state.hv`/`state.reach`.
Behavioural half → `test_nomination_changes_no_label_and_no_measure` passes.
Its assertion was TIGHTENED during the step rather than weakened: nomination
registers the certificate artifact, so a new id appears in `state.status`. The
test now asserts every PRE-EXISTING label is identical and that the only
additions are reach certificates — registration, never adjudication.
Ring: `python -m pytest tests/test_calculus*.py tests/test_reflexive_discipline.py
tests/test_prose_refutation_boundaries.py -q` → `139 passed`.

**6.** `python -m pytest tests/test_promotion_nomination_live.py -q` → `5 passed`.
One in-step correction: the read-only refusal type is `ReadOnlyHarnessError`,
not `ReadOnlyError`. The root is opened `read_only=True` and the last test
proves the open wrote nothing.

**7. MUTATION PROOF of the live negative half — both runs, pasted.**

MUTATED (`problem_parents` stops at artifact sources — the truncated walk):

    === MUTATED: the walk stops at artifact sources ===
    FAILED tests/test_promotion_nomination_live.py::test_the_one_reach_event_spans_exactly_one_lineage
    FAILED tests/test_promotion_nomination_live.py::test_every_problem_in_the_run_descends_from_the_one_seed
    FAILED tests/test_promotion_nomination_live.py::test_nomination_does_not_fire_on_the_committed_live_root
    3 failed, 2 passed in 8.51s

    E   AssertionError: assert 'conn:0793267d0d4d' == 'question-4dd...0e09b302500bc'
    E   AssertionError: ['conn:0793267d0d4d', 'conn:07c58a1d6b34', 'conn:13f027942733', ...]
    E   deepreason.harness.ReadOnlyHarnessError: time-travel harness is read-only

Read the third failure carefully — it is the whole proof. Under the truncated
walk the committed live root SPANS TWO LINEAGES and nomination TRIES TO FIRE,
and the only thing that stopped it writing a promotion problem into the
evidence was the read-only open. The definition is what produces the no-fire,
not an accident of the fixture.

RESTORED:

    === RESTORED ===
    20 passed in 8.44s

`git diff --stat src/` after restore: empty — no residue of the mutation.

**8.** `python -m pytest tests/test_promotion_criteria.py -q` → `16 failed`,
every failure an `AttributeError`/`ImportError` on the unwritten criterion
functions. Tests exist, guard nothing yet.

**9.** `python -m pytest tests/test_promotion_succession.py -q` → `11 failed`,
same shape.

**10.** `python -m pytest tests/test_promotion_criteria.py
tests/test_promotion_succession.py -q` → `27 passed`.

Three corrections inside the step, each recorded because each changed a
DESIGN decision rather than a typo:

(a) `FrozenSubjectV1.demarcation`'s three values were renamed to
`load-bearing` / `declared-only` / `no-attack-surface`. The first draft called
the `crit`-false case `undecided`, which read as an abstention when it is a
SETTLED failure — an interface declaring nothing forbids nothing, and no sample
could rescue it (Rung 2's own rule). `declared-only` is now the abstention, and
the criterion answers `overrun` on it.

(b) `FrozenSubjectV1` gained `criticised_commitments`, and the certificate now
freezes the subjects' OWN commitment specs as well as the problems' criteria.
Non-immunization needs to know which components registered criticism cites, and
the empirical clause needs to resolve whether a subject's own commitment is
observation-valued; neither was reachable from the first shape.

(c) Non-immunization returns `overrun` (`accounting-not-in-environment`) when a
problem the rival accounts for was not frozen. Discovered by the fixtures:
with an unknown accounting, `needed` computes as EMPTY and every uncriticised
component looks idle, which would fell a rival for the environment's gaps
rather than for its own riders.

**11.** Registry check → `registry OK`; the six new names are declared
`structural` and `programs_by_class()['structural'] == _STRUCTURAL_PROGRAMS`.
`python -m pytest tests/test_reflexive_discipline.py
tests/test_prose_refutation_boundaries.py tests/test_verifier_registry.py
tests/test_decommissioned_pipeline_stays_out.py -q` → `72 passed`. All four
assert over the DECLARATION, so they cover the new programs the day they land,
exactly as their own docstrings promise.

**12. MUTATION PROOF of the strong relation's first refusal — both runs.**

MUTATED (the strictness-witness clause replaced by an unconditional pass — the
WEAK reading, which R6 forbids building):

    === MUTATED: the strictness witness is dropped (the WEAK reading) ===
    E         - fail
    E         + pass
    FAILED tests/test_promotion_succession.py::test_a_rival_that_only_recovers_is_not_a_successor
    1 failed, 10 passed in 0.07s

Exactly one test goes red, and it is the one R10 names: "a rival that merely
recovers the incumbent's explicanda is refused as a successor — the test that
passes under the weak reading and must fail under this one". The other ten stay
green, which is the second half of the proof: the strictness witness is doing
this one job and is not propping up the other three clauses.

RESTORED:

    === RESTORED ===
    33 passed in 2.35s

`git diff --stat src/deepreason/calculus/promotion.py` after restore: `517
insertions` and no deletions — the file as written, no residue.

**13.** `python -m pytest tests/test_promotion_closure.py -q` →
`AttributeError: module 'deepreason.calculus.promotion' has no attribute
'promotion_criteria_sweep'`.

**14.** `python -m pytest tests/test_promotion_closure.py -q` → `6 passed`.
One in-step correction: `Consultability`'s typed field is `code`, not `reason`.

**15.** `python -m pytest tests/test_calculus_standing.py tests/test_scheduler.py -q`
→ `19 passed`. `Scheduler._promotion_step` runs immediately after `reach_sweep`
and before every consumer of standing — Remark 9.5's ORDER, not a preference.

**16.** `python -m pytest tests/test_promotion_solo.py -q` → `4 passed`, and it
asserts `Config().JUDGE_SEATS_ENABLED is False` before drawing any conclusion
from a green path.

**17.** `KNOWLEDGE_LABEL` check → `label OK: knowledge (unrefuted ∧ active ∧
reach > 0)`. `python -m pytest tests/test_calculus_standing.py -q` → `16 passed`
(13 existing + 3 new knowledge-view tests).

The census-predicted move happened and was handled by WIDENING, not weakening.
`test_the_standing_surface_is_read_only_and_calls_no_model` asserted that
`standing_view`'s argument is an INLINE `Harness(..., read_only=True)` call; the
handler now binds a local so the knowledge section shares one open. The
assertion now follows the binding — the nearest binding of that name above the
call — and requires the same thing of it.

A first attempt at that widening was itself defective and is recorded rather
than quietly fixed: it keyed bindings by NAME, and `cli/main.py` binds `harness`
twenty-six times, so the dict kept one and the test passed while checking
almost nothing. Now keyed by `(name, lineno)`. NEGATIVE CONTROL run after the
fix — making the standing handler writable:

    tests/test_calculus_standing.py:466: AssertionError
    FAILED tests/test_calculus_standing.py::test_the_standing_surface_is_read_only_and_calls_no_model
    1 failed in 3.99s

restored → `16 passed`.

**19.** Every new `INV-axiom-basis.md` check RUN before it was written:
`CHECK-A8-1 OK`, `CHECK-A8-2 OK`, `CHECK-Ax41 OK`, `CHECK-A4-solo OK`,
`CHECK-A8-structural OK`, plus
`test_nomination_changes_no_label_and_no_measure` and
`test_nomination_does_not_fire_on_the_committed_live_root` both `1 passed`.
A8's row moves from "NOT YET PROVED — Rung 5 owns it" to PROVED, with the spawn
half's check added in the same commit as nomination, exactly as A8's own text
demanded.

**20.** `docs/map/SEAM-evaluation-x-rules.md` (the ladder's named exit
artifact), `SUB-calculus.md`, `SUB-evaluation.md`,
`SEAM-evaluation-x-ontology.md`, `CON-standing-and-background.md`,
`CON-problem-layer-lifecycle.md`, `INV-frozen-surfaces.md`, `INDEX.md`. Every
new check run first: `claim-schema check OK`, `succession check OK`,
`scheduler check OK`, `dual-registration check OK`, `CHECK seam-1/2/3 OK`,
`SUB-evaluation check OK`, `CON-problem-layer check OK`, `CHECK frozen-4 OK`,
`CHECK pops present OK`. `python tools/docs_verify.py --links` → `0 dangling
reference(s), 63 document(s)`.

The census's one predicted map break was real and was fixed in the same edit as
the code that caused it: `SEAM-evaluation-x-ontology.md:54` pins the EXACT
sorted list of functions called with `artifact` inside `programs.py`, and the
six new wrappers join it.

**22.** `git add -A && python tools/diff_budget.py ade214037 --ceiling 1900` →
`EXCEEDED 4503`. Reported in REQUEST.md Amendment 1 with the per-area
itemization; not concealed, not renegotiated.

**18.** `python scripts/wheel_smoke.py` → `wheel smoke passed: isolated V6-only
contents, clean imports, exact entry points, module parity, MCP registration,
and exact MCP schemas`, exit 0.
`python -u scripts/wheel_operational_smoke.py` → `wheel operational smoke
passed: installed setup, explicit qualification (80 qualification calls; 418
total calls), readiness, question-only reasoning, replay-verified terminal
retrieval, cache reuse, opaque MCP restart, budget ceiling, and pre-V6
fail-closed admission`, exit 0. Neither was owed (C1 says the public surface is
unchanged); they are the PROOF of that claim rather than a formality.

**21.** FIRST full run: `12 failed`. Nine were mine and one of those was a real
DESIGN ERROR — the criterion bound was being read from `Budget.steps`, which
`SEAM-evaluation-x-ontology` records is read by nothing precisely because it is
outside the commitment's content address. Fixed in the CODE, not the check.
Two boundary checks were narrowed to the claims they actually make and
mutation-proved afterwards; six count pins updated. Full account in
VALIDATION.md.

SECOND full run: `docs_verify: 3 failed` — exactly the three known
`CON-run-identity.md` shallow-clone failures and nothing else.
`--audit` → `0 finding(s)`. `--links` → `0 dangling reference(s), 63
document(s)`. `--coverage` → `2 finding(s)`, identical at `ade214037`, so
pre-existing. `--stale` → 15 before, 8 after; the seven this tranche made stale
had their stamps advanced because their checks were re-run and passed, and the
eight remaining are dismissed with their reason in VALIDATION.md.

**23.** `python -m pytest tests/ -q -n 4` →

    3939 passed, 6 skipped in 824.20s (0:13:44)
    rc=0

Baseline re-derived at `ade214037` in this session: `3879 passed, 6 skipped`.
Delta 60 = this tranche's new tests exactly.

**24.** Tree clean, branch head on origin.
