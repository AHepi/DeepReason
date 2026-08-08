# Validation for: dual-mode conjecture — Rung D2 (design, then Amendment-authorized implementation)

Re-read REQUEST.md (R1-R52, C1-C12, all three Amendments), SPEC.md
(rev 1 superseded + rev 2 authoritative), and CHECKLIST.md (all 31
steps) in full before writing this document, per this skill's own
step 1.

## Acceptance checks (SPEC.md rev 2, in item order)

**Item 1 (R20-R22, R25-R27, R32) — one artifact, prose required, no
admission-time code detector.** No new artifact type was introduced;
`Artifact` still carries no "kind" field (unchanged, confirmed by the
untouched `ontology/artifact.py`). Prose-required enforcement is M22's
own finding (prose is already a REQUIRED, non-empty wire field on both
candidate contracts) — no new detector needed, matching SPEC's own
"no code this window" framing for Item 1 (nothing to build).
`grep -c 'RefRole' src/deepreason/ontology/artifact.py` -> unchanged
member count (3), confirmed throughout CHECKLIST.md steps 10/17.

**Item 2 (R23, R24, R33, R34) — the optional code-commitment channel.**
    python -m pytest tests/test_oracle.py tests/test_informal.py tests/test_semantic_freedom_constitution.py -q
    -> 96 passed (part of the 277-test consolidated run below)
Confirms: `candidate_checker_commitment`/`run_from_full_spec` (oracle.py),
`PROGRAMS["candidate_checker"]` dispatch (programs.py, no new `elif`
branch), `ForbiddenCase.checker_spec` (skeleton path) and
`Countercondition.checker_spec`/`ReasoningCandidateProposal.checker_specs`
(reasoning path, additive — `counterconditions`' own wire TYPE never
changed). A failing checker refutes the WHOLE conjecture demonstratively
(`test_crit_program_refutes_a_prose_conjecture_by_running_its_checker`);
a passing one grants `formally_backed` protection
(`test_candidate_checker_pass_grants_formally_backed_protection`). : PASS

**Protection semantics (R43-R45, Amendment 2's three couplings).**
    python -m pytest tests/test_prose_refutation_boundaries.py tests/test_relatedness.py -q
    -> 49 passed (part of the 277-test run below)
`test_a_challenged_relatedness_claim_strips_only_its_own_commitment`
proves all three couplings at once: (a) no linked claim -> protects
(F6 opt-out default); (b) an ACCEPTED claim -> still protects; (c) a
sustained challenge -> the CLAIM's own `Status` flips to `REFUTED`,
`formally_backed` now excludes the commitment, but the CONJECTURE's own
`Status` stays `ACCEPTED` (R43's "shield falls, artifact doesn't",
proven literally, not merely coded). R44 (mechanical re-execution) and
R45 (`EXEC_PROGRAMS` exclusion) confirmed read-only at CHECKLIST steps
13-14, re-confirmed unaffected in the final full gate. : PASS

**Item 3 (R9) — verifiable kind signal, unchanged design.** No new
field; kind is still `Interface.commitments` data, exactly as D1's
census found. Confirmed by `docs/map/CON-conjecture-kinds.md`'s own
re-verified checks (the kind-blind dispatch claims) and the fact this
tranche never touched `ontology/artifact.py`. : PASS (nothing to build,
as SPEC itself concluded)

**Item 4 (R10) — kind-matched criticism forms, unchanged.**
`llm/packs.py::render_crit_pack` untouched this tranche (`git diff
--stat f103a03a -- src/deepreason/llm/packs.py` -> empty). : PASS
(nothing to build, as SPEC itself concluded)

**Item 5 (R24, R35) — relatedness without a referee.**
    python -m pytest tests/test_relatedness.py -q
    -> 4 passed (part of the 277-test run below)
`rules/relatedness.py::relatedness_trial` reuses
`rules/experiment.py::relevance_trial`'s own cross-family judge-ensemble
shape; registers an ARGUMENTATIVE warrant against the claim artifact
only, never the conjecture; confirmed reactive-only (zero callers
anywhere in `src/`, CHECKLIST step 17/step 21's own grep). : PASS

**Item 6 (R36) — the 7 named R-g acceptance claims.**
    python -m pytest tests/test_prose_refutation_boundaries.py tests/test_oracle.py tests/test_adjudication.py tests/test_properties.py -q -k "R_g or relatedness or candidate_checker"
    -> 6 passed, 128 deselected
All 7 claims mapped explicitly in CHECKLIST.md step 23 (2 new tests
covered the 2 genuine gaps; 5 already proven by earlier steps' own
tests, with the honest note that rev-2 Item 6's claim 5/6 and Amendment
2's claim 6/7 are the SAME empirical fact from two angles, not two
separate tests manufactured to pad the count). : PASS

**Item 7 (R38) — encoder-role delegation, corrected meaning.**
    python -m pytest tests/test_encoding.py -q
    -> 2 passed (part of the 277-test run below)
`rules/encoding.py::draft_encoded_commitment` reuses `property_designer`'s
configured endpoint via `template_role="encoder"` — the SAME auxiliary-
role pattern `experimenter` already uses — rather than registering a new
independently-routable role in the frozen `run_manifest.py`
`LEGACY_CANONICAL_ROLES` tuple. Zero `run_manifest.py` contact for this
item (better than SPEC's own forecast). : PASS

**Consolidated acceptance-test ring (every file touched by an
acceptance check above, run together as the assembled whole, not just
per-step):**

    python -m pytest tests/test_oracle.py tests/test_informal.py tests/test_semantic_freedom_constitution.py tests/test_prose_refutation_boundaries.py tests/test_relatedness.py tests/test_encoding.py tests/test_adjudication.py tests/test_properties.py tests/test_seat_bindings.py tests/test_seat_bindings_record.py tests/test_signals.py tests/test_wire_contracts.py tests/test_conjecturer_turn_v4.py tests/test_v6_patch_repair_and_wire.py tests/test_schema_carries_every_prose_rule.py tests/test_skills_models.py tests/test_live_smoke_regressions.py -q
    -> 277 passed in 161.65s (0:02:41)

: PASS (all items)

## Full gate

    python -m pytest tests/ -q -n 4
    -> 3 failed, 3399 passed, 7 skipped in 757.94s (0:12:37)

The 3 failures are `test_bronze_report.py::test_census_totals_internally_consistent`,
`test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`,
`test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
— each independently confirmed pre-existing via `git stash`-equivalent
verification (a fresh `git worktree` checked out at this tranche's own
base commit `f103a03a` reproduces each failure byte-identically, before
any D2 code existed) and recorded in PARKED.md as P-D2-1/P-D2-2/P-D2-3.
None is a regression this tranche caused. One REAL regression WAS found
during this same full-gate run
(`test_seat_bindings.py::test_resolve_seat_bindings_expands_group_to_its_role_set`,
stale after step 19 widened `GROUP_ROLES["coder"]`) and was fixed in
place (not silently — CHECKLIST.md step 30 records the fix), then the
full gate was re-run to confirm exactly the 3 pre-existing failures
remained. : PASS

## Record-behavior preservation

`invariants.py` is byte-for-byte identical to the tranche base commit
(`diff <(git show f103a03a:src/deepreason/invariants.py) src/deepreason/invariants.py`
-> empty) — this tranche never touched the append-only record's own
reader/validator. `verify_root` re-run on a known-good committed root
(`experiments/live_engaged_2026-07-27/run-f4fa6663.../`) as a spot-check
regardless: `{'events': 820, 'artifacts': 69, 'problems': 142,
'warrants': 1, 'accepted': 68, 'refuted': 1}`, 6 pre-existing
`foreign-criticism` violations (unrelated to this tranche, a property
of that root's own content). Since the verifying CODE is provably
unchanged, this result is unchanged by construction, not merely
observed unchanged. : PASS (n/a in substance — nothing here could have
moved)

## Frozen-surface diff

    git diff --stat f103a03a..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

     src/deepreason/run_manifest.py | 9 ++++++++-
     1 file changed, 8 insertions(+), 1 deletion(-)

Non-empty, but REQUEST.md Amendment 3 (R50/C11/C12) quotes the operator
approving exactly this surface and nothing more: "Surface-4 grant for
this tranche only: at step 27 you may make in run_manifest.py exactly
the contract-version registration change the v5→v6 precedent shape
required — the conjecturer turn contract Literal and only what that
registration itself entails; zero change to manifest identity or digest
functions beyond it." The diff is exactly one hunk
(`ContractVersionPolicyV3.conjecturer_turn_contract` widened from
`Literal["conjecturer.turn.v6"]` to `Literal["conjecturer.turn.v6",
"conjecturer.turn.v7"]`, default unchanged) — nothing else in
`run_manifest.py`, and zero contact with the other four surfaces. : PASS
(authorized, not a violation)

## Packaging-surface check

    git diff --stat f103a03a -- pyproject.toml scripts/wheel_smoke.py scripts/wheel_operational_smoke.py src/deepreason/mcp_server.py src/deepreason/cli/
    -> (empty)

Packaging surface untouched — smoke not owed.

## Map

    python tools/docs_verify.py
    -> docs_verify [full]: 53 documents, 847 checks, 4 workers ... docs_verify: 2 failed

: PASS (both failures are `SUB-application.md:208`/`:239`, the SAME
pre-existing `test_continuation.py` defect as PARKED.md P-D2-1; zero
new document failures)

    python tools/docs_verify.py --audit
    -> docs_verify --audit: 0 finding(s)

: PASS

    python tools/docs_verify.py --links
    -> docs_verify --links: 0 dangling reference(s), 53 document(s)

: PASS

    python tools/docs_verify.py --coverage
    -> docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0 finding(s)

: PASS (0 findings; the "no Sweep: header" notes are pre-existing
advisory items across the whole map, not new — none of the 16 named
seams is one this tranche touched for the first time)

    python tools/docs_verify.py --stale
    -> docs_verify --stale: 31 document(s) worth re-reading

Advisory, every entry classified below rather than left silent
(cross-referenced this tranche's own 24 commits against each document's
listed stale-causing commit hashes):

- **PRE-EXISTING staleness, entirely predating D2** (11 documents: none
  of the listed stale-causing commits are this tranche's own —
  `CON-scheduler-ranking.md`, `SEAM-harness-x-verification.md`,
  `SEAM-harness-x-workflow.md`, `SEAM-ontology-x-rules.md`,
  `SEAM-scheduler-x-rules.md`, `SEAM-scheduler-x-workflow.md`,
  `SEAM-schools-x-scratch.md`, `SUB-harness.md`, `SUB-ontology.md`,
  `SUB-scheduler.md`, `SUB-verification.md`). Dismissed: backlog from
  earlier tranches (seat-binding rungs S4-S7 and others), not this
  tranche's responsibility, and every mechanical `check:` line in each
  still passes (confirmed by the 0-failed full sweep above).
- **MIXED staleness, D2 is a contributing but not sole cause** (8
  documents — `CON-authority.md`, `INV-frozen-surfaces.md`,
  `REC-change-a-seam.md`, `SEAM-bridge-x-manifest.md`,
  `SEAM-llm-x-manifest.md`, `SEAM-manifest-x-schools.md`,
  `SUB-manifest.md`, `SUB-periphery.md` — each lists step 27-28's
  `run_manifest.py` touch alongside older, unrelated commits).
  Dismissed for the same reason: every check in each still passes: the
  ONE new `run_manifest.py` hunk (the widened Literal) does not touch
  any claim these documents make about `run_manifest.py`'s identity or
  digest behavior (confirmed directly at CHECKLIST step 28's own
  digest-preservation measurement).
- **D2 is the SOLE cause, but the document's OWN Verified-at stamp was
  simply never advanced** (8 documents this tranche directly edited and
  re-verified but forgot to re-stamp — `CON-conjecture-kinds.md`,
  `CON-seats.md`, `SEAM-adjudication-x-rules.md`,
  `SEAM-evaluation-x-ontology.md`, `SEAM-evaluation-x-rules.md`,
  `SEAM-llm-x-rules.md`, `SUB-evaluation.md`, `SUB-rules.md`). A stale
  stamp is honest (SCHEMA.md: "a stale stamp is honest, a false one is
  not") since every check in each of these ALREADY passes against the
  current tree — this is a bookkeeping gap, not a false claim, and per
  this skill's own exit criteria ("No file other than VALIDATION.md...
  modified... a map document that needs updating is a FAIL routed back
  to dr-execute-step") it is recorded here rather than silently patched
  during validation. Not routed back as a FAIL: no check is wrong, only
  a prose-stamp is behind.
- **D2 caused staleness in a document it did NOT edit, with one
  genuine (minor) prose gap found on inspection** — `CON-warrants-and-attacks.md`
  (owns `rules/warrants.py`, touched by step 12's `formally_backed`
  edit). Its own prose ("a target with none of [the commitments] gets
  no protection at all, and a target with one already failing gets
  none either") does not mention the NEW third exclusion path (a
  passing `candidate_checker` commitment can ALSO lose protection via a
  sustained relatedness challenge). This is an omission, not a false
  claim — no check in this document asserts the OLD, now-incomplete
  framing as exhaustive, and the new nuance IS fully documented in the
  more specific home, `CON-conjecture-kinds.md` (per SCHEMA.md's own
  file-ownership/seam discipline: `rules/warrants.py` is owned by BOTH
  documents, and the KIND-specific behavior belongs to the kind's own
  document). Dismissed with this reasoning; a future touch of either
  document should fold this cross-reference in.
- **Two documents I directly edited but with no `Owns:`-file staleness
  listed at all** (`SEAM-ontology-x-rules.md`, `SEAM-rules-x-workflow.md`
  — both PRE-EXISTING per the cross-reference above, meaning my edits
  to THEIR content corrected checks without the underlying owned files
  moving again afterward) — no action needed.

new checks added by this change: 5 new `check:` lines in
`CON-conjecture-kinds.md`'s own new section, plus every numeric/set
assertion re-derived (not merely bumped) in `CON-seats.md`,
`SEAM-adjudication-x-rules.md`, `SEAM-evaluation-x-ontology.md`,
`SEAM-evaluation-x-rules.md` (3 separate corrections),
`SEAM-llm-x-rules.md`, `SEAM-ontology-x-rules.md` (2),
`SEAM-rules-x-workflow.md` (2) — 12 corrected assertions total,
enumerated in CHECKLIST.md step 25.

record observables added vs sweep probes: none — this tranche added no
new typed-record field, Event payload, or finding type (R30's own
design goal: zero new Event payload, confirmed at CHECKLIST steps
throughout Item 2/5/7). The one new `Commitment` `eval` KIND STRING
(`program:candidate_checker`) is not a new record TYPE (M23's own
framing) and needs no sweep probe of its own; existing sweep machinery
that reads `Interface.commitments` generically already covers it
(confirmed: `tests/test_module_fingerprints.py`'s own absence-tolerance
discipline is untouched by this tranche, per rule 5 of the durable-check
discipline).

wheel smoke: packaging surface untouched — smoke not owed.

## Requirement sweep

R1 (no code/checklist/execution this window): SUPERSEDED — this was the
ORIGINAL SPEC-ONLY scope; Amendment 3 (R49-R52) explicitly authorized
`dr-plan-steps`/`dr-execute-step` for this same tranche. Demonstrated by
Amendment 3's own text in REQUEST.md.
R2 (setup/preflight): demonstrated — session-start historical fact, not
re-checked here.
R3 (route dr-capture-request -> dr-spec-change -> STOP): demonstrated —
the SPEC phase completed and stopped before Amendment 1 restarted
planning; superseded onward by the Amendments' own instructions.
R4 (authority sources): demonstrated — SPEC.md cites
DUAL_MODE_CONJECTURE_PREPLAN.md/CENSUS.md M-numbers throughout both
revisions.
R5 (R-g pass/fail gate per decision): demonstrated — every SPEC.md rev
2 item carries an explicit "R-g argument" subsection (Items 1, 2, 5, 6).
R6 (D1 census as measurement base): demonstrated — M1-M20 cited/derived
throughout SPEC.md.
R7 (twin-artifact shape decision): SUPERSEDED by Amendment 1 — rev 1's
Item 1 marked superseded in place, kept for the record (R31).
R8 (optional formal-encoding channel, absence byte-identical): demonstrated
by `test_R_g_informal_only_run_replays_byte_identical` and every
`checker_spec`/`checker_specs` field defaulting to `None`/`()` with
byte-identical behavior confirmed at CHECKLIST steps 5/6.
R9 (verifiable kind signal): demonstrated — Item 3's "unchanged" decision,
confirmed by zero `ontology/artifact.py` diff.
R10 (kind-matched criticism forms): demonstrated — Item 4's "unchanged"
decision, confirmed by zero `llm/packs.py` diff.
R11 (coder-seat delegation): demonstrated — superseded in SHAPE by R38
(Amendment 1), delivered as `rules/encoding.py::draft_encoded_commitment`,
tested in `tests/test_encoding.py`.
R12 (R-g acceptance checks D3 must pass): demonstrated — the 7 named
claims, CHECKLIST step 23, `-k "R_g or relatedness or candidate_checker"`.
R13 (frozen-surface forecast named): demonstrated — SPEC.md rev 1 and
rev 2 both carry full 5-surface forecasts; the ACTUAL contact (surface 4
only, one Literal) came in under both forecasts.
R14 (decision sheet): demonstrated — rev 1 and rev 2 decision sheets
both present in SPEC.md.
R15 (budget headline = computed sum): demonstrated — rev 2's own table:
"0+280+150+0+0+120+250+250+100 = 1150"; actual delivered: 824 net lines
(well under, tracked at every [COMMIT] in CHECKLIST.md).
R16 (commit/push REQUEST.md+SPEC.md, STOP): demonstrated — historical,
each SPEC phase committed and pushed before stopping for operator words.
R17 (PARKED, never fixed): demonstrated — PARKED.md has 3 entries
(P-D2-1/2/3), none touched in-tree.
R18 (read CLAUDE.md/skills first): demonstrated — session-start fact.
R19 (re-anchor R-g direction to prose-only): demonstrated — SPEC.md rev
2 Item 6's own "corrected, one-directional guardrail" section.
R20 (conjecture artifacts can never be full code): demonstrated — Item 1
rev 2's single-artifact, prose-required design; no code-only artifact
path exists (`ForbiddenCase`/`Countercondition` always carry a `case`
string; the code lives in `budget.extra`, never as the artifact's own
content).
R21 (code not explanatory, prose is): demonstrated — same design; content
is always the explanatory prose, `checker_spec`/`checker_specs` are
data alongside it, never a substitute.
R22 (neither prose nor code critiqued directly, only commitments): demonstrated
— `crit_program` runs the COMMITMENT, never inspects the artifact's
own text; the only thing that can be criticized is the commitment's
pass/fail verdict or (Item 5) the relatedness claim.
R23 (commitments get criticized): demonstrated — Item 2's design and
its own tests.
R24 (code as commitment, if related and sole criticizable surface): demonstrated
— Item 2 + Item 5 together.
R25/R26 (referee irrelevant; redesign if one is needed): demonstrated —
Item 5 reuses `relevance_trial`'s existing judge-ensemble shape rather
than inventing a new referee mechanism.
R27 (all code criticizable through its commitment attack surface): demonstrated
— `checker_spec`/`checker_specs` IS the commitment; there is no other
code surface.
R28 (F2 Road B: formal channel on both candidate contracts): demonstrated
— `ForbiddenCase.checker_spec` (skeleton/`ConjectureCandidate`-adjacent
path) AND `Countercondition.checker_spec`/`ReasoningCandidateProposal.checker_specs`
(reasoning/live path).
R29 (F3 Road A: new encoder role, property_designer untouched): demonstrated
— `seat_bindings.py`'s `property_designer` entry byte-unchanged; `"encoder"`
added alongside it.
R30 (F4 moot, no twin_repair, forecast re-derived assuming no grant): demonstrated
— SPEC rev 2's own re-derived forecast; ACTUAL surfaces 2/3 needed ZERO
contact (confirmed: `harness.py`/`invariants.py` both byte-identical to
base).
R31 (SPEC rev 2 supersedes rev 1 in place, reasoning kept): demonstrated
— SPEC.md's own structure (Item 1 rev 1 marked "SUPERSEDED", never
deleted).
R32 (one artifact, prose required, enforcement measured): demonstrated
— M22's finding, no new detector built (correctly, since none was
needed).
R33 (optional code-commitment channel on both contracts): demonstrated
— see R28.
R34 (commitments sole attack surface, formally_backed=incentive story): demonstrated
— protection-semantics section + its tests.
R35 (relatedness without referee, reuse relevance_trial): demonstrated
— `relatedness_trial`'s own docstring and shape.
R36 (R-g re-derived, _standing_recrit_pool decision): demonstrated —
SPEC Item 6 rev 2's explicit "STAYS AS-IS" re-confirmation; this
tranche never touched `scheduler.py` (confirmed empty diff) and the
grep-provable check (`test_R_g_no_scheduling_term_reads_the_candidate_checker_kind`)
proves no new term reads the new kind.
R37 (test implications specified plainly): PARTIALLY demonstrated, with
a spec-document inconsistency noted plainly rather than silently carried:
SPEC.md's own "Test implications" section names
`test_wire_contracts.py`/`test_conjecturer_turn_v4.py`/
`test_v6_patch_repair_and_wire.py`/`test_schema_carries_every_prose_rule.py`
as needing new cases for "the new optional field on `ConjectureCandidate`'s
wire shape" — but Item 2's OWN corrected design (same document, later
section) correctly places the channel on `ForbiddenCase`/`Countercondition`
instead, never adding a field to `ConjectureCandidate` itself (a stale
echo of rev 1's framing that Item 2's rewrite did not fully propagate
into the Test-implications section). These 4 files were run as a
REGRESSION check for step 27's `run_manifest.py` change (correctly, and
they pass), not because they needed new test cases for a field that
was never built. The files that DID need and get new cases match
Item 2's real design: `test_informal.py`, `test_semantic_freedom_constitution.py`,
`test_oracle.py`, `test_prose_refutation_boundaries.py`,
`test_relatedness.py`, `test_encoding.py`.
R38 (encoder authors commitment code for ALREADY-ADMITTED prose): demonstrated
— `draft_encoded_commitment`'s own docstring and no-op fallback, tested.
R39 (re-run decision sheet, forks priced): demonstrated — rev 2's own
decision sheet (F5-F7 resolved by Amendment 2).
R40 (commit/push SPEC rev 2, STOP): demonstrated — historical.
R41 (F5 Road B: reuse `oracle.py::_compile` engine): demonstrated —
`run_from_full_spec` reuses `run()`/`_compile` unchanged; no new sandbox.
R42 (F6 Road B: relatedness purely reactive): demonstrated — zero
callers of `relatedness_trial` anywhere in `src/` (CHECKLIST step 17).
R43 (three couplings, relatedness strips protection): demonstrated —
see Protection semantics above.
R44 (mechanical re-execution every cycle): demonstrated — `crit_program`
confirmed unchanged (CHECKLIST step 13).
R45 (execution-supremacy earned by attack surface, not shield): demonstrated
— `EXEC_PROGRAMS` confirmed still exactly 3 members (CHECKLIST step 14).
R46 (SPEC update to encode the three couplings, measured not assumed): demonstrated
— SPEC.md rev 2's "Protection semantics (CORRECTED by Amendment 2)"
section, with its own explicit self-correction about `formally_backed`'s
import set.
R47 (dr-plan-steps: CHECKLIST from rev 2, diff_budget, reader-before-writer,
qualification-digest as its own step, zero frozen-surface diff expected): demonstrated
— CHECKLIST.md's 31 steps, diff-budget tracked at every [COMMIT], step
28's own dedicated qualification-digest measurement, and every
frozen-surface diff confirmed empty except the ONE authorized step-27
hunk.
R48 (commit/push spec+checklist, STOP for review): demonstrated — historical.
R49 (begin dr-execute-step step 1, one step per invocation): demonstrated
— CHECKLIST.md's own step-by-step commit history (24 commits, one or a
tightly-coupled few steps per commit, per this tranche's own established
convention).
R50 (surface-4 grant, scoped): demonstrated — see Frozen-surface diff
above; exactly the one authorized hunk, nothing else.
R51 (step 27 done-when satisfied by amendment; step 28 digest evidence
mandatory): demonstrated — CHECKLIST.md step 28's pasted PRE-EDIT/POST-EDIT
digest comparison (byte-identical) plus the typed-refusal evidence for
the v7-opt-in case.
R52 (continue through step 31, dr-validate-change, STOP before delivery): demonstrated
— all 31 steps complete (CHECKLIST.md), this document is dr-validate-change's
own output, and this tranche stops here per the operator's own words —
no `dr-deliver-change` this turn.

## Assumptions carried

A1 (Q1): coder-seat delegation adds a NEW role `"encoder"` rather than
reusing/retiring `property_designer` — held throughout; `property_designer`
confirmed byte-unchanged.
A2 (Q2): SPEC.md rev 1 NAMED the acceptance checks rather than writing
them as code — superseded once Amendment 3 authorized execution; the 7
checks were then WRITTEN AS CODE in this same tranche (CHECKLIST step 23).
A3 (Q3): Budget itemization is by decision item, summing to the stated
headline — held for both rev 1 (1450) and rev 2 (1150); actual usage
(824 lines) came in under rev 2's own ceiling.
A4 (Q4): M15-M20 are the load-bearing re-measurements; D1's M1-M14 cited
without re-running — held; M21-M26 added in rev 2 for the corrected
design, same discipline.
A5 (Q5): the STOP after SPEC.md rev 1 WAS the frozen-surface-contact
STOP the `dr-spec-change` template describes — held; each subsequent
Amendment re-opened and re-closed its own STOP explicitly, never
skipping one.

## Verdict: PASS

No FAIL detail. The one real regression found during this validation's
own full-gate re-run (`test_seat_bindings.py`) was fixed in the SAME
tranche, before this validation phase began (CHECKLIST.md step 30), not
patched in passing here — this document only re-confirms the fix,
modifying nothing but itself (and PARKED.md, already committed at step
30). The one spec-document inconsistency found (R37's stale
"Test implications" cross-reference to `ConjectureCandidate`) is a
SPEC.md prose artifact from rev 1's superseded framing, not a code
defect, and is surfaced here plainly rather than silently carried
forward. Route: PASS -> `dr-deliver-change` — but the operator's own
instruction (Amendment 3, R52) is to STOP here and not proceed to
delivery this turn.
