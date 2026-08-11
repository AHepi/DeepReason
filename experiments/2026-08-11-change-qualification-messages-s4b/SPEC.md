# Spec for: per-role qualification error messages + human-readable error surface + schema-first intake tool

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items
are bugs. DESIGN-AND-STOP: no code lands from this SPEC without fresh
operator words (task handover, Item 4: "frozen surface 5 — no code
without fresh operator words").

## Addendum (2026-08-11, REQUEST.md Amendment 1 — operator approved)

Q1 resolved to **(a) narrow**: S1 becomes a message-only pass (see S1
below, revised) — zero change to `qualification_subject_payload` or
any frozen-surface-5 code, folded into S2's error-catalog work rather
than a separate item. Q3 resolved to **every caller**: S3's
`validate-intake`/`IntakeFormV1` is the default intake path for
everyone; `FORM_DR1_RUN_APPLICATION.md` becomes generated-only
documentation, never a second primary way to start a run. Both
resolutions match this SPEC's own recommendations verbatim — no design
changes below, only removing the STOP. Execution proceeds as two
sub-tranches per the Budget section's own recommendation: (i) S1+S2
combined (message-only qualification fix + error catalog mechanism +
44 entries), (ii) S3 (intake tool), each separately planned, executed,
validated, and delivered.

## Items

S1 (R1, Q1 — RESOLVED to option (a) narrow, Addendum above): Per-role
qualification, message-only — COLLAPSES INTO S2, zero standalone work.
Re-examined at resolution time: "per role" needs no change (already
true, Rung S3/S4); "added error messages" IS the catalog (S2). A2
already establishes S2 is purely additive, reading existing `.code`
strings without touching any raise site — so S1 requires ZERO edits to
`qualification.py`, `runtime/launch_policy.py`, or `readiness.py`.
Recording S1 as its own item only to close the loop on REQUEST.md R1;
its acceptance check IS S2's.
accept: S2's `deepreason explain-error <qualification-code>` covering
all ~21 `QualificationError` codes IS the demonstration that R1's
"added error messages" is satisfied — no separate check.

S2 (R2, R5-of-Item5's broadened scope): human-readable error-code
catalog. A full census (this tranche) found **572 deduplicated real
raise-site codes** across ~140 scattered exception classes, THREE
incompatible raise conventions (plain `ValueError(f"CODE: prose")`;
a `(code, message)` two-arg `__init__` shared by `QualificationError`/
`AdmissionStoreError`/`SchoolRouteResolutionError`/others; and
`RunManifestError(code, message, pointer)`, a THIRD convention adding a
JSON-pointer to the offending field), plus one typed-refusal-record
pattern (`AdmissionRefusalV1`, `code: Literal[...]` + `detail: str`,
meant to live IN the record). The only existing precedent for
code-triggered human prose anywhere in the codebase is
`cli/main.py:1724 _print_qualify_failure`, which prefix-matches
`"QUALIFICATION_EXECUTION_FAILED"`/`"DOCTOR_"` and appends one static
remediation sentence — S2 generalizes this ad hoc precedent into a
registry instead of growing more prefix-matches by hand. Target: new
file `src/deepreason/error_catalog.py` (a plain `dict[str,
ErrorCatalogEntry]` — code → {summary, what_it_means, next_action},
Pydantic `BaseModel` for consistency with the rest of the codebase's
typed-record style), CLI rendering hook in `cli/main.py` (catch typed
errors, look up `.code` — falling back to a parsed-prefix code string
for the plain-`ValueError` convention, which has no `.code` attribute
— print the catalog entry alongside the existing raw code/message,
never REPLACING the raw code, only appending prose), and a `deepreason
explain-error CODE` subcommand for out-of-band lookup.
accept: `deepreason explain-error QUALIFICATION_TIER_UNQUALIFIED`
(corrected 2026-08-11 at delivery — the original example,
`ADMISSION_DOSSIER_INVALID`, was never in the 44-entry scope this same
document's own "Family-grouped counts" paragraph below settles on;
`VALIDATION_i.md` records the inconsistency this fixes) prints a
non-empty plain-language summary; every code the catalog claims to
cover round-trips through a test asserting the code string in the
catalog is byte-identical to the code string in its raise site (no
silent respelling — the frozen-surface trap "renaming a typed reason
string" applies to the catalog's KEYS even though the catalog itself
is new and additive).

Family-grouped counts (572 total, from the census): BRIDGE_* 121,
TERMINAL_* 59, SCRATCH_* 54, JOLT_* 43, V6_* 33 (+13 more V3/V4/V5_*),
RUN_* 25, DOCTOR_* 23, QUALIFICATION_* 21, CONTINUE_* 19, ADMISSION_*
17, PREPARATION_* 15, AMEND(MENT)_* 15, SCHOOL_* 11, WORKFLOW_* 8,
ROUTE_* 8, SEAT_/PROVIDER_/MANIFEST_* 5 each, remainder singletons/
pairs across ~40 more prefixes. 572 codes is too large for one tranche
to catalog by hand at acceptable quality — S2's own budget (below)
covers the REGISTRY MECHANISM plus the ~21 QUALIFICATION_* and ~23
DOCTOR_* codes (44 entries, R1's own immediate complaint area,
directly measured this tranche with their current raw text — see
this tranche's ERROR_CENSUS.md); the remaining ~528 codes are explicit
residue for follow-on tranches, one family group at a time, never
silently declared "done" at 44/572.

S3 (R3, R4, C3, C4, Q3, Q4): schema-first intake tool, replacing
FORM_DR1_RUN_APPLICATION.md as the DEFAULT intake path (scope of
"default for whom" is Questions for operator Q3, not resolved here).
Target: new file `src/deepreason/intake_form.py` defining
`IntakeFormV1(BaseModel)` mirroring FORM_DR1's Parts A-D (mandatory)
and E-H (optional) fields, with Pydantic field validators encoding the
FORM's own stated conditions (B1a: no conflicting profiles on a shared
role; D1a: question+config identity; F3a: F2 or F3 required for any
judge trial) as validation rules rather than prose the operator must
read and self-check. `IntakeFormV1.model_json_schema()` is the
machine-validatable schema (M1 below shows this pattern is already
load-bearing elsewhere in the codebase — RunManifest and Config both
export JSON Schema this same way; this is not a new paradigm import).
New CLI command `deepreason validate-intake FILE.json` (or `.yaml`)
loads the file, validates it via `IntakeFormV1.model_validate`, and on
failure renders every violation through S2's catalog (human-readable,
before any token is spent — R2/R5 and R3/R4 share this one surface by
design, per the task handover's "design them together"). New MCP tool
`validate_intake` wrapping the identical validator (same code path,
not a re-implementation) for model callers. `FORM_DR1_RUN_APPLICATION.md`
is regenerated FROM `IntakeFormV1`'s field descriptions/docstrings by a
new `tools/render_form_dr1.py`, replacing today's hand-maintained prose
(which already carries 5 stale `†`-pending markers for the unmerged
adjudication branch — regeneration cannot fix those until that branch
merges, but removes the CLASS of drift, not just today's instance).
accept: `deepreason validate-intake <a file missing a mandatory field>`
exits non-zero with a human-readable message citing S2's catalog;
`python tools/render_form_dr1.py --check` (diff mode) exits 0 against a
freshly generated `FORM_DR1_RUN_APPLICATION.md`, proving the committed
file is not stale relative to its own generator.

## Addendum 2 (2026-08-11, sub-tranche (ii) execution scoping)

Re-examined at execution time against the actual CLI/config surface
(`cli/main.py`'s real `add_argument` calls, `preparation.py`'s real
ceiling constants), not FORM_DR1's prose alone:

**Modeled as `IntakeFormV1` fields with real Pydantic validators:**
Part A (provider setup: `--provider`, `--endpoint`, `--model`,
`--model-revision`, `--family`, `--context-window-tokens`,
`--maximum-completion-tokens`, `--credential-env`, `--reasoning`), Part
B1 (`--seat GROUP=PROFILE`, repeatable, with B1a's conflict rule
implemented by reusing `seat_bindings.py`'s own
`GROUP_ALIASES = {"simulation": "conjecture"}` — not a re-derived
alias table, the same one), Part D mandatory fields (`question`,
`--cycles`, `--token-budget`, `--shallow`, `--dossier`, `--attach`,
`--allow-partial`) with D2/D3's ceilings enforced by importing
`PUBLIC_MAX_CYCLES`/`PUBLIC_MAX_TOKEN_BUDGET` directly from
`preparation.py` (not re-declared constants — if the real ceiling
changes, the form's validation follows automatically).

**Explicitly NOT modeled, with reasons (a scope boundary, not an
oversight):**
- Part C (qualification) — describes a PROCESS (`deepreason qualify`)
  and its OUTCOME (a tier), not form fields a caller fills in; nothing
  to validate offline.
- D1a (question+config = run identity, collision detection) — requires
  comparing against EXISTING run roots under a `DEEPREASON_HOME`,
  external filesystem state a standalone file validator does not have
  access to and should not reach for (this would turn a pure schema
  validator into a stateful one, contradicting the whole point of "no
  dialog state, repairable").
- D4 (shallow mandatory when tier is SHALLOW) — the tier is an OUTCOME
  of qualification (external state), not something the intake file
  itself declares; same reasoning as D1a.
- Parts B2/B3/E2/E3/F1/F3 (school seats, `LEGACY_CRITICISM_ENABLED`,
  `SCHOOL_SEATS_ENABLED`, `--judge-seats`, `--blind-same-model-judges`)
  — confirmed AGAIN at execution time (`git merge-base --is-ancestor
  <adjudication-branch-tip> origin/main`, still false) these do not
  exist as real CLI flags on `main`; per `PARKED.md` Residue 3, modeled
  only once that branch merges.

**MCP tool + packaging-surface consequence (new this addendum, not in
the original SPEC — found during execution, not anticipated at design
time):** adding `validate_intake` as an MCP tool changes
`mcp_server.py`'s `_tools()` output, which is exactly what
`scripts/wheel_smoke.py`/`wheel_operational_smoke.py` pin
(`EXPECTED_MCP_TOOLS`, `EXPECTED_MCP_SCHEMA_SHA256`) — per CLAUDE.md's
rule and this program's own Item 1 finding, both pins update in the
SAME commit as the tool registration, and both smokes re-run in that
commit.

## Assumptions (operator may override)

A1 (Q2): "fully kitted" (R2) is read at the BROADER scope the task
handover's Item 5 states explicitly — every typed error code across
the public surface, not only qualification-failure codes — because
that instruction is later and more specific than REQUEST.md's own R2
wording, and covering only qualification codes would leave the CLI's
non-qualification refusals (admission, amendment, run-identity) in the
same unreadable state R2 complains about. Smallest-reasonable-reading
rule does not apply here since the two readings do not conflict — the
broader one is a superset that satisfies both R2's letter and Item 5's
explicit scope.

A2: S2's catalog is purely ADDITIVE prose keyed by existing code
strings; no raise-site CODE string may be renamed, and no `message`
field's raw text is claimed to be evidence-comparable (verified this
tranche: `grep -rn QualificationError src/deepreason/harness.py
src/deepreason/invariants.py` returns no hits — qualification errors
never enter the append-only log, so their `message` text carries no
frozen-surface risk; the same check should be re-run per error family
before S2 executes, not assumed to generalize).

A3: S3's `IntakeFormV1` is a STANDALONE Pydantic model, never a
subclass of or code-sharing arrangement with `RunManifest` — it
VALIDATES a caller's intent before that intent reaches the existing
CLI-flag parsing/manifest-compilation path, which is otherwise
unchanged. This is the design choice that keeps S3 off frozen surface
4 (manifest schemas AND their validators): `IntakeFormV1` widens
nothing `RunManifest`'s own validators accept, because it never touches
those validators at all.

## Questions for operator (STOP — this SPEC does not proceed past this section)

**Q1 (was REQUEST.md's Q1, material — different files, frozen-surface-5
contact, >2x effort difference).** Does R1 ("qualification needs to be
per role with added error messages") mean:

- **(a) narrow** — keep today's qualification UNIT exactly as Rung
  S4/S4b-parked left it (per-profile loop reports outcomes per role
  ALREADY, S2 of that rung; combination-subject qualification still
  gates launch, per Option 2b) and add ONLY human-readable messages
  on top (this SPEC's S2, applied to qualification's existing codes) —
  zero frozen-surface-5 contact, small; or
- **(b) broad** — build S4b's parked Option 1 (per-role PROVENANCE
  qualification: N already-qualified profiles mix freely without a
  fresh COMBINATION battery), which PARKED.md already flags as "real
  frozen-surface-5 contact when eventually built" requiring
  `qualification_subject_payload`'s digest-equality check to accept a
  report synthesized from independent single-profile qualifications
  rather than one battery run against the launching manifest.

Recommendation: **(a) narrow**, this tranche. M5/M6 (cited in
PARKED.md) already proved combination-subject qualification is
CORRECT; Option 1 buys COST savings for operators who reshuffle seat
bindings often, which the operator's own words don't ask for ("per
role with added error messages" reads as a readability complaint, not
a cost complaint) — and (a) delivers the readability fix immediately
while (b) requires its own full frozen-surface-5 `dr-spec-change` cycle
PARKED.md already anticipated as separate work. If the operator meant
(b), that is real, valuable, and already scoped in PARKED.md — just not
what R1's plain words most directly ask for.

**Q3 (was REQUEST.md's Q3, material — changes what "default" means for
every future caller, not only this tranche's files).** Should
`IntakeFormV1`/`validate-intake` become the default intake path for
SMALL MODELS ONLY (R4's own verbatim scope), or for EVERY caller,
including the operator's own interactive CLI use and larger models
(the task handover's Item 5 monitor recommendation: "should be the
default for EVERY caller, not only smaller models")?

Recommendation: **every caller**. The monitor's stated reasoning
(bounded artifact, no dialog state, repairable) is not model-size-
dependent — a human operator benefits from the same properties, and
FORM_DR1's prose form (Parts A-H) already exists as documentation;
making the schema+validator path the DEFAULT for everyone does not
remove the prose form, it demotes it from "the thing you fill out" to
"the thing generated FROM the schema for reading" (S3's own
render_form_dr1.py). Narrowing to small models only would mean
maintaining two intake paths as equally-primary, which reintroduces
the drift risk R3/R4 complain about in the first place.

Both Q1 and Q3 need the operator's own words before `dr-plan-steps`
runs on either half of this tranche (S1 depends on Q1; S3's scope
depends on Q3). S2 (the catalog) and S3's mechanics (Pydantic schema +
CLI + MCP tool, independent of WHO defaults to it) have no material
fork and may proceed once approved, regardless of Q1/Q3's answers.

## Out of scope (explicit)

- Actually implementing S4b Option 1 (per-role provenance) — Q1(b), if
  chosen, is its own future `dr-spec-change` cycle per PARKED.md, not
  folded into this tranche even on approval.
- Rewriting FORM_DR1_RUN_APPLICATION.md's CONTENT (Parts A-H's actual
  fields) — S3 changes how the document is PRODUCED (generated, not
  hand-maintained), not what it currently documents. Content changes
  ride the adjudication branch's own merge, separately.
- Any change to `run_manifest.py`'s Pydantic models or validators —
  A3 makes this explicit; `IntakeFormV1` is additive and standalone.
- A general-purpose "wizard"/interactive prompt flow — the monitor's
  recommendation (verified, not inherited, per M1-M3) is that a
  validated file beats an interactive dialog for EVERY caller; no
  option below prices an interactive wizard because REQUEST.md never
  asks for one and the research supports the file-based path over it.

## Frozen-surface contact forecast

- **Surface 5 (qualification subject digests, `qualification.py`):
  contact PLAUSIBLE, gated on Q1.** Q1(a) (recommended): no contact —
  confirmed, S2's catalog only reads existing `QualificationError.code`
  strings, never `qualification_subject_payload`. Q1(b): contact
  CONFIRMED by PARKED.md's own text ("real frozen-surface-5 contact
  when eventually built") — STOP required before any Q1(b) code, exactly
  as PARKED.md already says.
- **Surface 4 (manifest schemas AND validators, `run_manifest.py`):
  none expected.** A3's standalone-model design keeps `IntakeFormV1`
  off `RunManifest` entirely; verified by grep — `IntakeFormV1` is a
  new file, not a modification to `run_manifest.py`.
- **Surface 1 (capability state digests): none expected** — no item
  touches `capabilities/state.py`.
- **Surface 2 (harness event application): none expected** — confirmed
  this tranche (A2): `QualificationError` never reaches `harness.py`.
- **Surface 3 (replay-validation record formats): none expected** — no
  item touches `invariants.py`/`verification/` record shapes; S2's
  catalog is a lookup table, not a record format.
- **`route_fingerprint` (frozen-adjacent): none expected** — no item
  touches `llm/firewall.py`.

## Blast-radius census

`QualificationError`: 18 hits in `tests/`/`docs/map/` (raise-site and
message-content tests only — none assert on the catalog, which is new;
all EXPECTED TO MOVE ZERO — S2 never renames a code or edits an
existing raise-site's raw message, per A2).

`qualification_subject_payload`: 5 hits, ALL in `docs/map/` (
`SUB-manifest.md` x3 including an exact-key-set `check:`,
`INV-frozen-surfaces.md` x1, `SEAM-rules-x-scratch.md` x1,
`SEAM-bridge-x-manifest.md` x1 with an exact-key-set `check:`) — MUST
NOT MOVE under Q1(a); every one of these is exactly the surface-5
tripwire Q1(b) would need to touch deliberately, with its own future
spec.

`require_v6_production_qualification`: 26 hits across `src/deepreason/
runtime/launch_policy.py`, `cli/main.py`, `application/text_runs.py`,
`ops.py`, `bridge/transactional_adapter.py`, `scratch/authoring.py`
(the 5 call sites PARKED.md already names) plus compiled `.pyc` noise —
MUST NOT MOVE under Q1(a) (S2 only wraps its raised errors' display,
never its logic); PLAUSIBLY MOVES under Q1(b) (Option 1 changes what a
report's digest may legitimately be checked against).

`get_seat_readiness`: 7 hits, `tests/`/`docs/map/` — MUST NOT MOVE;
already reports per-role readiness since Rung S3, unaffected by either
Q1 fork or S2/S3.

`FORM_DR1`/`FORM_DR-1`: 0 hits outside `docs/FORM_DR1_RUN_APPLICATION.md`
itself — no test or map document asserts on its content today, so S3's
regeneration has no other blast radius to account for.

## Measurements

M1: `python3 -c "from deepreason.run_manifest import RunManifest; print(len(RunManifest.model_json_schema()['properties']))"`
→ `32` — confirms `RunManifest` (a Pydantic `BaseModel`) already
exports a JSON Schema via the standard library method; the codebase's
own precedent for "schema is the source of truth, not hand-written
prose" already exists for the compiled manifest. `IntakeFormV1`
reuses this exact mechanism at the CLI-flag/pre-compilation layer,
which does not yet have a typed model — S3 is filling a gap the
codebase's own pattern already implies should exist, not importing an
external paradigm.

M2: `grep -rn "class.*Error" src/deepreason/qualification.py` →
`class QualificationError(ValueError)` at line 67, with `__init__(self,
code: str, message: str)` — confirms the `code`+`message` shape S2
extends is already uniform across at least this family; a fuller
per-family census (all raise sites, not just qualification) is
recorded separately as this tranche's own residue (see PARKED.md).

M3: `grep -rn "QualificationError" src/deepreason/harness.py
src/deepreason/invariants.py` → no hits — supports A2's claim that
qualification error text carries no replay-validation risk.

M4 (Diátaxis/standards research, run this tranche via background
research, full report in this tranche's directory): Diátaxis's
Reference/Explanation/How-to/Tutorial split, ADR (Architecture Decision
Records), and docs-as-code were researched; none is a form-intake
standard per se, but JSON Schema as a "validated config file" pattern
is the industry-standard mechanism for exactly this shape of problem
(a bounded, machine-checkable, human-fillable artifact) and is already
native to this codebase's Pydantic-everywhere convention (RunManifest,
Config, SeatBindingV1, ModuleFingerprintV1 are all `BaseModel`/
`FrozenRecord`) — supports Options B below over hand-rolling a bespoke
schema format.

## Options

**Per-role qualification (S1, gated on Q1):**
- A: narrow — human-readable messages only, zero new qualification
  logic. Files: `qualification.py` (message text only, no code
  changes to the digest/subject functions), `error_catalog.py`. ~40-80
  lines. Frozen contact: none. Risk: low. RECOMMENDED (cites M2, M3).
- B: broad — S4b Option 1, per-role provenance qualification. Files:
  `qualification.py` (surface 5), `runtime/launch_policy.py`,
  `readiness.py`. Estimated 200-400 lines (PARKED.md's own estimate
  band for a frozen-surface-5 redesign). Frozen contact: surface 5,
  confirmed. Risk: high, needs its own SPEC/STOP cycle. Rejected FOR
  THIS TRANCHE, not rejected outright — PARKED.md already holds its
  ready-to-run entry point.

**Error surface (S2):**
- A: catalog as a `dict` constant, no schema, hand-maintained parallel
  list. Rejected: exactly reproduces the drift problem R2/R3 complain
  about (a second hand-maintained artifact that can silently
  desynchronize from the code strings it describes).
- B: catalog as a Pydantic-validated registry with a test asserting
  every entry's key matches a real raise-site string (S2 as specified
  above). CHOSEN (cites M2 — the codebase's uniform `code`+`message`
  shape makes a single registry keyed on `code` tractable).

**Intake tool (S3):**
- A: interactive CLI wizard (prompt-driven). Rejected: the monitor's
  recommendation, verified against M1's precedent — a wizard has
  dialog state a validated file does not, is not repairable the way a
  file+diff is, and REQUEST.md's own words ("a tool should be the
  default... simple enough for a coding human to fill out and for
  later documentation") describe an artifact, not a conversation.
- B: JSON-Schema-validated file + `IntakeFormV1` Pydantic model + CLI
  validate command + MCP tool + generated FORM_DR1. CHOSEN (cites M1,
  M4). Reuses the codebase's own established pattern rather than
  introducing a new one.
- C: hand-write a JSON Schema document independent of any Pydantic
  model. Rejected: duplicates B's validation logic in two places
  (schema file + whatever actually enforces it), reintroducing the
  exact prose/code drift risk this tranche exists to close; B gets the
  schema for free from the model that also does the validating.

## Budget

S2: ~120-170 lines (registry mechanism + CLI hook + explain-error
subcommand + one round-trip test + 44 hand-written entries for the
QUALIFICATION_*/DOCTOR_* families only — the census found 572 codes
total; the other ~528 are explicit residue, never silently claimed
covered). S3: ~150-250 lines (`IntakeFormV1` model + validate-intake
CLI command + MCP tool wrapper + render_form_dr1.py + tests). S1: 0
lines, confirmed final (Addendum above) — collapses entirely into S2,
no separate raise-site edits.

    python3 -c "print(sum([170, 250, 0]))"  # -> 420

Total: ~420 lines upper bound (S2+S3; S1 adds 0), across an estimated
3-4 commits (S2 alone; S3's model+validator; S3's CLI+MCP wiring; S3's
FORM_DR1 regeneration + docs_verify pass). Over the ~300-line
rung-split guidance — executed as a two-sub-tranche split per this
SPEC's own recommendation: (i) S1+S2 (message catalog, ~170 lines),
(ii) S3 (intake tool, ~250 lines), each with its own delivery, rather
than one ~420-line commit sequence. Frozen surfaces touched: **none**
— Q1(a) confirmed, A3 holds, S1(b) remains out of scope.

Rubric: 8/8 yes — every R has a spec item or an explicit STOP (R1→S1/Q1;
R2→S2/A1; R3,R4→S3/Q3; R5→S3; R6→M4; C1,C2 out of scope with reason;
C3,C4→Q3); blast-radius census pasted and classified; frozen-surface
contact forecast recorded per surface; every named mechanism (the
monitor's schema recommendation) traced to real code (M1); measurements
pasted for every load-bearing claim; options priced with rejections
citing measurements; nothing untraceable to an R/C number.
