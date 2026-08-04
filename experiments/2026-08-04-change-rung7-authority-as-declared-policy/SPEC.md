# Spec for: Rung 7 — authority as a declared policy
Traces: every item cites R/C numbers. Untraceable items are bugs.
DESIGN-AND-STOP: this document is the whole deliverable. No CHECKLIST.md,
no code change, no map change, no gate run follows in this tranche.

## The finding that governs this spec (R6, R4, Q1, Q2)

R6 asks for "routing every status change through one narrow gate
consulting a declared policy." Measured against the tree, that sentence
contains two halves with opposite verdicts:

**Half 1 — "one narrow gate" for status changes: ALREADY EXISTS, and is
one line.** `final_labels` is the only producer of `Status` values and
`Harness._adjudicate` is its only caller and the sole writer of
`state.status` (M1). There is nothing to build, consolidate, or narrow.
Q1 is answered: this half of R6 is satisfied by the code as it stands.

**Half 2 — "consulting a declared policy" AT that gate: forbidden, and
the cost is measured, not argued.** A committed root's labels are not
replayed from its log; they are RECOMPUTED on every open. Making the
label function policy-dependent and reopening the *same committed bytes*
flips `run-f4fa6663`'s recorded `REFUTED` count from 1 to 0 (M5). Across
the tree that exposure is 6 committed roots and 26 recorded `REFUTED`
verdicts (M6c). `INV-frozen-surfaces.md`'s governing principle — "a
change that invalidates existing replay-valid roots is wrong by
definition" (C4) — and `SUB-adjudication.md`'s own instruction — "fix
readers, not labels" (C7) — both forbid it. Q2 is answered: the literal
reading is not achievable.

**The asymmetry that makes a safe design exist.** The same experiment run
at the other end of the chain gives the opposite result: sabotaging
`register_fail_warrant` so that any execution of the mint path raises,
then reopening the same root, changes nothing — `att=1`, `REFUTED=1`,
identical (M6). Replay never executes `rules/`; `harness.py` does not
import it at all (M6b). **A policy consulted at MINT time is invisible
to replay; a policy consulted at LABEL time reinterprets every recorded
root.** That single measured distinction is this spec's whole design.

So, per C5 (ERRATA E10's rule: a named mechanism is a suggestion the
spec phase must verify for reachability; deliver the PROPERTY and record
the contradiction in writing) and `dr-spec-change` procedure step 2, this
spec delivers the property R6 wants — *one declared policy governs who
may change a Status, and no status-bearing judgement escapes it* — at
the mint boundary, and records the contradiction rather than silently
redesigning around it.

## Items

S1 (R1, R2, C1): route `dr-change-orchestrator` →
`dr-capture-request` → `dr-spec-change`, then stop. | before: no rung-7
tranche | after: `REQUEST.md` + `SPEC.md` only.
    accept: `ls experiments/2026-08-04-change-rung7-authority-as-declared-policy/`
    → `REQUEST.md SPEC.md` at the point this tranche ends; no
    `CHECKLIST.md`, `VALIDATION.md`, or `DELIVERY.md`; `git diff --stat`
    for this tranche shows no `src/`, `tests/`, or `docs/map/` path.

S2 (R4, R7, C4, C7): the frozen-surface contact forecast, below, is
derived from measurement (M1, M5, M6, M6c, M8, M10) rather than from
reading the surface list — R4 makes it this spec's load-bearing section.
    accept: every claim in "Frozen-surface contact forecast" cites an
    `M<n>`; the one option that contacts a frozen surface is rejected on
    a pasted measurement, not on judgement.

S3 (R6, C5): deliver R6's PROPERTY at the mint boundary. Target files
(future execute tranche only): `src/deepreason/authority.py` (gains the
declared-policy object and its single resolution entry point),
`src/deepreason/rules/crit.py`, `src/deepreason/informal/trial.py`,
`src/deepreason/ops.py`, `src/deepreason/scheduler/scheduler.py` (the
five modules that reach an authority decision today — M4a, M9). | before:
the authority decision is assembled per-call from 6 `Config` knobs across
2 closed vocabularies sharing 1 word, via 3 distinct entry points
(`trial_authority_for`, `argumentative_authority_mode`,
`_resolve_authority`), at 5 supremacy-guard sites and 3
`trial_authority_for` sites (M4b, M7, M9) | after: one
`DeclaredAuthorityPolicy` value object, constructed once per run by
projecting those same existing fields (plus the manifest's already-frozen
`CriticismPolicyV1.authority` where manifest-bound), passed explicitly to
each mint site, with the three existing entry points reduced to
constructors of it. **No new `Config` field, no new manifest field, no
new record type** — the policy is a projection of what is already
declared, which is what keeps its frozen contact at zero (M8).
    accept (future tranche, PROPERTIES not mechanisms per C5): (a) every
    site that today reaches an authority decision obtains it from one
    resolution function, provable by an AST check that no module outside
    `authority.py` reads an authority `Config` field directly; (b) the
    full gate 0 failed; (c) the 42-root sweep byte-identical and, as the
    stronger instrument this spec's own measurement suggests, the 6
    att-bearing roots' `REFUTED` counts unchanged at 26 total (M6c);
    (d) a regression proving a policy-dependent LABEL function is NOT
    what was built — i.e. `adjudication/` still imports nothing but
    `ontology` (M2).

S4 (R6, R7): the two argumentative mint sites that consult no authority
and no supremacy guard at all —
`imports.register_epistemic_import_failure` and
`experiment.relevance_trial` (M4c) — are brought under the declared
policy OR given a recorded, checked exemption naming why. Today they are
neither gated nor documented as exempt, which is the one place R6's
"every status change" is literally unmet at the mint boundary.
    accept (future tranche): each of the two either routes through the
    resolution function, or carries a `docs/map/` claim with a check
    pinning its exemption; a test proves the choice.

S5 (R5, C2, C3): scope fence. No rung-6 execution work (rung 6 is
deferred by its own R13). P7 stays parked — this tranche neither
investigates nor fixes the `attempt-validity` violation, despite rung 7
being the tranche nearest `invariants.py` and therefore most tempted.
    accept: `grep -rn "attempt-validity\|module_conformance" experiments/2026-08-04-change-rung7-authority-as-declared-policy/SPEC.md`
    → hits only this item and the Out-of-scope bullets, none proposing
    work.

S6 (R3): stop after committing SPEC.md and present it.
    accept: the tranche's last action is a push of SPEC.md and a
    presentation to the operator; no phase skill runs after
    `dr-spec-change`.

S7 (R8): precondition — rungs 1-4 delivered before this SPEC is written.
    accept: `experiments/2026-08-03-change-rung1-sockets-on-paper/DELIVERY.md`
    through `experiments/2026-08-04-change-rung4-module-fingerprints/DELIVERY.md`
    all exist (they do; rung 5 is delivered too, and rung 6 is an
    approved deferred SPEC).

## Assumptions (operator may override)

A1 (Q3): the scatter worth consolidating is the LLM-mediated-text
authority decision only — the one `CON-authority.md` says the policy
governs ("Only LLM-mediated *text* judgements pass through this policy —
deterministic, execution, formal, browser and verifier-backed paths keep
their established status-changing behaviour and never consult it").
Measured: 6 of the 8 modules that mint demonstrative warrants import no
authority at all (M4d), and a `code` or `formal` workload receives
`TrialAuthority.STATUS` without consulting any knob (M9b). Consolidating
those exempt paths into the gate is Option C, rejected below.

A2 (Q4): "declared" means `Config`-projected, not manifest-declared.
Smallest reading with zero frozen contact: the manifest half is already
frozen and already passed explicitly on manifest-bound calls, so the
policy object CONSUMES it rather than redeclaring it. Adding an authority
section to the manifest is Option B, rejected below.

A3: the policy object adds no new `Config` field. If a future amendment
adds one, `_versioned_source_config_data` must gain an explicit
unconditional `pop` for it — the trap is real and already cost one
tranche a refuted first fix (`INV-frozen-surfaces.md` Traps;
`ENGAGED_CRITICISM_AUTHORITY` is popped unconditionally at
`run_manifest.py:2151`, M8).

A4: no typed reason string moves. `execution-backed`,
`same-school-critic`, `no-critic-school`, `single-judge-seat` and the
`["scrutiny", target, critic]` Measure inputs are each single-site in
`src/` (M10) and are compared against recorded roots; the consolidation
renames none of them.

A5: this spec does not make authority a *registered module* in the
rung-3/5 sense. R6 says "declared policy", not "registered backend".
Should the operator later want authority pluggable, rung 6's conformance
framework is registry-agnostic by its own A1 and would apply — noted as
a forward link, explicitly not scoped here.

## Out of scope (explicit)

- Making the label computation configurable in any form — measured
  forbidden (M5), Option A.
- A manifest authority section — frozen surface 4, Option B.
- Bringing deterministic/execution/formal mint sites under the policy —
  Option C; a behavior change to paths deliberately exempt today (M4d,
  M9b), not requested by R6.
- P7 (`attempt-validity`) — C3, S5.
- Rung 6 execution — C2; deferred by rung 6's own R13.
- Fixing the `argumentative_authority_mode` error-message asymmetry
  (`CON-authority.md` records one refusal naming the vocabulary and one
  not) — a real wart, adjacent to every file this rung touches, not
  requested. PARKED candidate for the execute tranche.
- The dead `single_family_trial` `Config` value (`CON-schools.md` Traps:
  cannot complete a trial; parked as dead weight in the 2026-08-01
  tranche) — consolidation will make it more visible, not less; removing
  it is a separate decision.

## Frozen-surface contact forecast

**This is the section R4 says the spec lives or dies on.** Each verdict
cites a measurement.

| Surface | Contact under the CHOSEN design (D) | Evidence |
|---|---|---|
| 1. `capabilities/state.py` digests | none — file not touched | not in S3's target list |
| 2. `harness.py` event application / well-formedness | **none** — the gate is at mint time, upstream of the log. `_adjudicate` and `_validate_warrant` are unmodified | M1, M6 (replay never executes the mint path), M6b |
| 3. Replay-validation formats (`invariants.py`, `verification/`) | none — no new record, no new finding type, no format change | S3 adds no record type |
| 4. Manifest schemas AND validators | **none** — the policy consumes the already-frozen `CriticismPolicyV1.authority`, adds no field, widens no `Literal` | A2; M7 (manifest vocabulary stays the 2 values it has) |
| 5. Qualification subject digests | none — no `Config` field added, so `source_config_hash` and `engine_config_json` are untouched | A3, M8 |
| Frozen-adjacent: `route_fingerprint` | none — routing is not an authority decision (`CON-authority.md` Traps: "Assuming authority picks the judge ensemble. It does not.") | not in S3's target list |
| Frozen-adjacent: typed reason strings | none — no rename | A4, M10 |
| Frozen-adjacent: recorded roots' labels | **none, and this is the measured centre of the design** — 6 att-bearing roots / 26 `REFUTED` verdicts stay put, because a mint-time gate cannot reach them | M5 (what would move them), M6 (why this design does not), M6c (the exposure) |

**Verdict: zero frozen-surface contact for Option D — but only because
the gate sits at mint time.** The same feature placed one layer
downstream contacts surfaces 2 and 3 and moves committed evidence (M5).
The forecast is therefore not "none expected" in the routine sense; it is
"none, conditional on the placement decision", and the placement decision
is the spec.

## Blast-radius census

Pasted from `grep -rln "<symbol>" tests/ docs/map/`, run per symbol.
Every hit classified; nothing omitted.

| Symbol | tests/ | docs/map/ | Classification |
|---|---|---|---|
| `final_labels` | 0 files | 7 files | **MUST NOT MOVE** — Option A would move all 7 and the label semantics under them; D does not touch it |
| `_adjudicate` | 1 file | 6 files | **MUST NOT MOVE** — same |
| `_validate_warrant` | 0 files | 4 files | **MUST NOT MOVE** — write-boundary, surface 2 |
| `register_fail_warrant` | 5 files (`test_workload_formal`, `test_easy`, `test_scheduler`, `test_evidence_view`, `test_simulation_backend`) | 12 files | **MUST NOT MOVE for the 12 call sites / 8 modules count.** `SEAM-adjudication-x-rules.md` pins `-eq 12`, `-eq 8`, `-eq 2` hand-built-in-`rules/`, and `-eq 4` `nu_interface=` sites with exact-equality checks. D adds a policy PARAMETER, not a call site, so the counts hold — but any execute tranche must re-run `docs_verify` in FULL mode, not `--fast`, to confirm (the E10 companion lesson) |
| `trial_authority_for` | 2 files (`test_text_authority_policy`, `test_workload_formal`) | 2 files (`SUB-scheduler`, `CON-authority`) | **EXPECTED TO MOVE** — D reduces it to a constructor of the policy object; both map documents own claims about it and must move in the same commit (`SCHEMA.md` rule 1) |
| `execution_backed` / `formally_backed` | 2 / 1 files | 7 / 10 files | **MUST NOT MOVE** — the supremacy guards are a separate concern from authority and are consulted strictly ABOVE the authority branch (`CON-warrants-and-attacks.md`). D must not merge them into the policy; doing so is the recorded 2026-08-01 mistake (widening the wrong guard) |
| `ARGUMENTATIVE_AUTHORITY` | 6 files (`test_text_authority_policy`, `test_config`, `test_manifest_integration`, `test_prose_refutation_boundaries`, `test_criticism_authority`, `test_semantic_freedom_constitution`) | 6 files | **EXPECTED TO MOVE** in reading path only — the field keeps its name, default and vocabulary (A3, A4); what changes is who reads it. `test_config` and `test_manifest_integration` pin the field itself and MUST NOT MOVE |

Highest-risk census entry: `register_fail_warrant`'s four exact-equality
counts in `SEAM-adjudication-x-rules.md`. They are the kind of check
`SCHEMA.md` rule 6 ("counts are claims") exists to make load-bearing, and
they will fail loudly rather than silently if D drifts into adding a mint
site.

## Measurements

M1: the "one narrow gate" already exists —
```
$ grep -rn "state\.status *=" src/deepreason --include=*.py
src/deepreason/harness.py:2170:        self.state.status = {i: final[i] for i in self.state.artifacts}
$ grep -rn "final_labels" src/deepreason --include=*.py
src/deepreason/harness.py:26:from deepreason.adjudication.support import final_labels
src/deepreason/harness.py:2166:        final = final_labels(compute_label0(nodes, att), dep)
src/deepreason/adjudication/support.py:15:def final_labels(
```
— supports the finding's Half 1. One writer, one call, no third path.

M2: `_adjudicate`'s inputs are the record and nothing else —
```
$ grep -rn "authority\|Authority" src/deepreason/adjudication/
  (no hits in adjudication/)
```
`_adjudicate` reads `state.artifacts`, `warrants`, `commitments`,
`state.carries` — no `Config`, no policy — supports S3 accept (d).

M3: the mint surface —
```
$ grep -rn "register_fail_warrant(" --include=*.py src/deepreason | grep -v "def "
count: 12     modules: 8
```
plus 4 hand-built `Warrant(` outside the constructor (`informal/trial.py`
×2, `rules/experiment.py`, `rules/vision.py`) and a 5th in
`imports.py:838` — 17 mint sites total.

M4a: 7 modules import `authority.py` (`config`, `scheduler`,
`informal/trial`, `run_manifest` ×2 function-local, `rules/crit`, `ops`).
M4b: 5 supremacy-guard call sites across 3 modules.
M4c: the two unguarded argumentative sites —
```
imports.register_epistemic_import_failure:  authority=False backed=False ARGUMENTATIVE=True
experiment.relevance_trial:                 authority=False backed=False ARGUMENTATIVE=True
```
— supports S4.
M4d: of the 8 modules minting demonstrative warrants, only
`informal/trial.py` and `rules/crit.py` import authority; the other 6
(`skills/adoption`, `measures/hv`, `workloads/formal`, `informal/audits`,
`rules/act`, `rules/experiment`) do not — supports A1 and Option C's
rejection.

M5: **a policy consulted at LABEL time moves committed evidence** —
```
$ python -c "<open run-f4fa6663 read-only; then patch final_labels to a
              policy-dependent variant and reopen the SAME bytes>"
  baseline: artifacts=69 att=1 REFUTED=1
  same bytes, policy-dependent label fn: REFUTED=0
  => recorded root moved: True
```
— supports the finding's Half 2 and Option A's rejection.

M6: **a policy consulted at MINT time cannot** —
```
$ python -c "<patch register_fail_warrant to raise on any call, reopen
              the same root>"
  root opened with the mint constructor sabotaged: att=1 REFUTED=1
$ grep -c "from deepreason.rules\|import deepreason.rules" src/deepreason/harness.py
0
```
— supports the chosen placement and the whole frozen-surface forecast.

M6c: the exposure a label-time policy would put at risk —
```
git-tracked roots with a log.jsonl: 47
  opened: 33   refused to open: 14
  roots with att>0: 6   roots with a REFUTED artifact: 6
  total att edges: 26   total REFUTED artifacts: 26
  by top dir: {'experiments': 44, 'runs': 3}
```
Instrument note, per the repo's standing rule (ERRATA E5/E8: cite the
instrument with the number): this is a THIRD instrument — git-tracked
files named `log.jsonl` — and it reconciles with the two known ones
exactly: 42 sweep rows over `experiments/` + rung 5's 2 committed A/B
arm roots = 44, plus the 3 no-manifest roots under `runs/` = 47. The 14
that refuse to open are the known pre-v6 raisers.

M7: the declaration surface being consolidated —
```
  Config knobs governing authority: 6
    ARGUMENTATIVE_AUTHORITY          default='observe_only'
    TEXT_RUBRIC_AUTHORITY            default=OBSERVE_ONLY
    PAIRWISE_AUTHORITY               default=OBSERVE_ONLY
    INFRASTRUCTURE_REVIEW_AUTHORITY  default=OBSERVE_ONLY
    CALIBRATION_RECEIPT              default=None
    ENGAGED_CRITICISM_AUTHORITY      default='observe_only'
  Config vocabulary (ARGUMENTATIVE): ['observe_only','single_family_trial','trial_required']
  manifest vocabulary:               ['defended_trial','observe_only']
  shared words:                      ['observe_only']
  independently-configured surfaces: 3
```

M8: the `Config`-field trap is live —
```
$ grep -n "ENGAGED_CRITICISM_AUTHORITY" src/deepreason/run_manifest.py
2145:    # ENGAGED_CRITICISM_AUTHORITY postdates every schema version's frozen
2151:    data.pop("ENGAGED_CRITICISM_AUTHORITY", None)
```
— supports A3 (and is why D adds no field).

M9: three `trial_authority_for` call sites, none manifest-preflighted
(`scheduler.py:1081`, `scheduler.py:1820`, `ops.py:141`).
M9b: the exemption a universal gate would destroy —
```
   workload_profile=text    -> TrialAuthority.OBSERVE_ONLY
   workload_profile=code    -> TrialAuthority.STATUS
   workload_profile=formal  -> TrialAuthority.STATUS
```
— supports Option C's rejection.

M10: each frozen-adjacent typed string is single-site in `src/`
(`"execution-backed"`, `"same-school-critic"`, `"no-critic-school"`,
`"single-judge-seat"` → 1 each; `"scrutiny"` → 3) — supports A4.

## Options

**A — declared policy consulted at the label gate** (`final_labels` /
`Harness._adjudicate`), the literal reading of R6. Files:
`adjudication/support.py`, `harness.py`. Frozen contact: surfaces 2 and
3 directly. ~lines: ~80 (deceptively small). Risk: **fatal**.
**REJECTED — cites M5**: the same committed bytes yield a different
`REFUTED` count, so 6 roots and 26 recorded verdicts change meaning
without any root being edited. This is `INV-frozen-surfaces.md`'s
definition of a wrong change (C4) and `SUB-adjudication.md`'s explicit
prohibition (C7).

**B — declare the policy in the manifest** (a new authority section on
`RunManifest`, mirroring `CriticismPolicyV1`). Files: `run_manifest.py`,
`authority.py`, the five consumers. Frozen contact: **surface 4
(schemas AND validators) and surface 5 (every qualification subject
digest derives from the manifest)**. ~lines: ~450 plus a full
requalification cost. Risk: high. **REJECTED — cites M7 and M8**: the
manifest vocabulary is a closed 2-value `Literal` that
`CON-authority.md` records as unwidenable, and the 2026-08-01 tranche
already attempted exactly this shape (school-bound judge seats) and
redesigned to avoid the manifest entirely. Adding a field also
invalidates every cached qualification (~14 min per home, M7 of the
rung-6 spec).

**C — universal mint-time gate over all 17 mint sites** (M3), so that
"every status change" is literally true at the mint boundary. Files:
`authority.py` plus all 8 demonstrative-minting modules plus the 5
argumentative sites. Frozen contact: none directly. ~lines: ~700+. Risk:
high — **REJECTED, cites M4d and M9b**: 6 of the 8 demonstrative-minting
modules deliberately consult no authority, and `code`/`formal` workloads
receive `STATUS` without reading a knob. A universal gate silently
subjects deterministic, execution, formal, browser and verifier-backed
paths to a policy written for LLM-mediated text — a behavior change of
much larger scope than R6 asks for, and one that would make a
deterministic oracle's verdict configurable.

**D — declared policy object, projected from existing declarations,
consulted at the LLM-mediated-text mint sites** (the ones already gated),
plus an explicit decision on the two currently-ungated argumentative
sites. Files: `authority.py`, `rules/crit.py`, `informal/trial.py`,
`ops.py`, `scheduler/scheduler.py`, plus the owed map delta. Frozen
contact: **none** (forecast table above; M1, M5/M6, M8, M10). ~lines:
~400-550 including tests and map. Risk: low-medium — the risk is
refactor drift, not semantics, and the census names exactly which
exact-equality checks catch it. **CHOSEN — cites M1, M2, M5, M6, M6c,
M8, M10 together.**

**E — write the missing seam document only** (`SEAM-adjudication-x-authority.md`),
recording the M5/M6 asymmetry and the exemption inventory, and change no
code. Files: `docs/map/` only (a new seam document, plus `INDEX.md`'s
matrix row and both sides' `Seams:` headers per ERRATA E9's lesson).
Frozen contact: none. ~lines: ~180. Risk: none.
**NOT REJECTED — recommended as D's first sub-tranche, and offered as a
standalone reduced-scope choice.** The map preflight found this pair
listed `Seams-undocumented:` on `SUB-adjudication.md` (REQUEST.md, Map
preflight), and `SCHEMA.md` says a missing seam document is a finding.
E alone captures this spec's most durable output — the measured reason
the gate must sit at mint time — permanently in the map, where the next
executor reads it before designing rather than after.

## Budget

Option D is ~400-550 lines, above the ~300-line soft guideline, so per
`dr-spec-change` step 6 it is proposed as **three ordered sub-tranches,
each independently deliverable, the ladder stopping safely after any**:

- **7a** (= Option E, ~180 lines, docs only, zero risk):
  `SEAM-adjudication-x-authority.md` + `INDEX.md` matrix row + both
  sides' `Seams:` headers, carrying the M5/M6 measurements as checks.
  Accept: `docs_verify` full mode 0 failed, `--audit` 0, `--links` 0.
- **7b** (~250-350 lines): the `DeclaredAuthorityPolicy` object and the
  already-gated sites (S3). Accept: full gate 0 failed; 42-root sweep
  byte-identical; the 6 att-bearing roots' `REFUTED` total unchanged at
  26 (M6c); `adjudication/` import surface unchanged (M2).
- **7c** (~80-120 lines): the two ungated argumentative sites (S4) —
  gate or recorded exemption, with a test either way.

Frozen surfaces touched: **none**, conditional on the mint-time
placement — which is the whole content of this spec, not a footnote.

**This tranche itself spends 0 `src/` lines, 0 `docs/map/` lines, and 0
commits beyond REQUEST.md and this SPEC** — R2/R3 (DESIGN-AND-STOP) mean
nothing above is built now.

Rubric: 6/6 yes — every R (R1-R8) has a spec item with a
machine-decidable accept (S1-S7); the blast-radius census is pasted with
every symbol classified MUST NOT MOVE or EXPECTED TO MOVE, including the
four exact-equality counts most likely to catch drift; the
frozen-surface contact forecast is measured surface by surface and
states its own conditionality rather than claiming a bare "none"; the
mechanism R6 names — a policy at the status-change gate — was traced to
the code it would actually reach, measured to move committed roots (M5),
and the contradiction recorded in writing rather than silently
redesigned (C5); every design claim is measured (M1-M10) and every
rejection cites a measurement; nothing above is untraceable to an R/C
number.
