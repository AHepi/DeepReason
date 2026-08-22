# Request: codify two operator rulings on reach semantics (P5-reach)
Captured: 2026-08-22, from the operator's tranche brief opening this session
(single message; the whole message is quoted below).

## Map preflight (resolved before any design; CLAUDE.md / dr-drive-harness §4)

Resolved ids, read in this order:

- `DR-INV-frozen-surfaces` — read FIRST. `src/deepreason/measures/reach.py`
  appears on no frozen list; the five frozen surfaces (state digests, harness
  event application, replay-validation formats, manifest schemas +
  validators, qualification subjects) are untouched by this tranche. The
  record shape does change in one direction only: an artifact with an empty
  own battery stops emitting reach/addr Measure events it would previously
  have emitted. That is within-version behaviour, not a record FORMAT change.
- `DR-SEAM-evaluation-x-rules` — read BEFORE either subsystem, per the one
  ordering rule. `Owns:` names `src/deepreason/measures/reach.py`. Its
  involved fraction is `_substantive` / `_STRUCTURAL_PROGRAMS`, the predicate
  reach shares with prose immunity. **Neither ruling touches that predicate**
  — R1 gates on the REACHING ARTIFACT's own battery being empty, R2 pins a
  comparison operator — so the seam's shared surface is out of scope and
  `rules/warrants.py::formally_backed` cannot move.
- `DR-SUB-evaluation` — the covering document for `reach_sweep`'s exits. It
  owns the exit-documentation trap and check (line 218-227) and the
  "Which criteria are too weak to ground reach" row. This is where the
  Traps entry for this ruling pair lands.
- `DR-CON-warrants-and-attacks` — consulted, not modified: its reach rows
  point at `_substantive`/`_STRUCTURAL_PROGRAMS` only.

## Verbatim

> Change tranche: codify two operator rulings on reach semantics
> (P5-reach). Route through dr-change-orchestrator; the workflow's own
> stop conditions apply, nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/reach-p5-rulings-t6wm2d origin/main; git merge-base
> --is-ancestor 2a744325f HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`, never
> bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY for REQUEST.md: the operator approved (2026-08-22) the
> monitor's two recommendations on
> experiments/2026-08-22-reach-structural-programs-fix/PARKED.md
> P5-reach — ledger both recommendation texts and the approval:
> RULING 1: an artifact carrying an EMPTY own commitment battery may
> NOT ground reach. Basis: the Bronze Age docstring's own words ("no
> reach from an empty, trivial, or unguarded battery") applied to the
> reaching artifact; the rent law's cousin — an artifact that forbids
> nothing earns no promotion signal. This is NOT a formalism-kind
> penalty: emptiness of commitments is not informality, and no
> admission, rank, or criticism outcome moves — only reach
> eligibility.
> RULING 2: coverage exactly EQUAL to REACH_COVERAGE_MIN remains a
> FULL hit, as written (`<` comparison stands). A floor means "at
> least"; the boundary becomes deliberate, not inherited.
>
> SCOPE:
> S1 the empty-battery guard: a reaching artifact with no commitments
>    of its own takes a NEW typed rejection exit in reach_sweep.
>    The exit-documentation check from the structural-programs fix
>    (mutation-proven both ways) asserts every exit is documented —
>    the new exit and that docstring/check move in the SAME commit.
> S2 the boundary pin: a test constructing coverage == floor asserts
>    HIT full; a one-line doc note marks the `<` comparison
>    deliberate, citing this tranche.
> S3 rehearsal re-run: experiments/2026-08-22-live-reach-rich-run/
>    rehearsal.py against the fixed tree — S2 (empty battery) must now
>    take the NEW exit; S8a must remain HIT; S8c must remain E4. Paste
>    all three. Update the 08-21 census tooling's exit vocabulary if
>    it enumerates exits by name.
>
> TESTS: mutation-proven on both rulings — disable the empty-battery
> guard in a scratch copy (test RED), restore (GREEN); flip `<` to
> `<=`... rather, break the boundary the other way (make 0.5
> provisional) and watch the pin test go RED; paste both runs.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (3818 at 2a744325f);
> docs_verify 3 pre-existing shallow-clone failures; 5 MCP-thread
> tests flaky under -n 4; smokes green; the sweep is retired. A
> parallel window is executing the reach-rich LIVE run from the frozen
> design — it runs against main-at-launch, so your change does not
> affect it; its census may report P5-shaped events, which these
> rulings will then classify. A second parallel window is running a
> read-only census; no shared files with either.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full. Map moves in the same commits (the reach-covering document's
> Traps gains this ruling pair). Commit and push every phase boundary
> (retry 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF, closing with
> one line per ruling: what reach_sweep now does that is deliberate.

## The two ruling texts, as approved

The operator's brief instructs: "ledger both recommendation texts and the
approval". The recommendation texts are quoted in full in the brief above and
are restated here as the standing rulings so later phases cite one place.

**RULING 1 (approved 2026-08-22).** Verbatim:

> an artifact carrying an EMPTY own commitment battery may NOT ground reach.
> Basis: the Bronze Age docstring's own words ("no reach from an empty,
> trivial, or unguarded battery") applied to the reaching artifact; the rent
> law's cousin — an artifact that forbids nothing earns no promotion signal.
> This is NOT a formalism-kind penalty: emptiness of commitments is not
> informality, and no admission, rank, or criticism outcome moves — only reach
> eligibility.

**RULING 2 (approved 2026-08-22).** Verbatim:

> coverage exactly EQUAL to REACH_COVERAGE_MIN remains a FULL hit, as written
> (`<` comparison stands). A floor means "at least"; the boundary becomes
> deliberate, not inherited.

The question these rulings answer was parked, with both readings left open, at
`experiments/2026-08-22-reach-structural-programs-fix/PARKED.md` P5-reach:
"decide and record whether an artifact carrying an EMPTY own commitment
battery may ground reach, and whether coverage exactly equal to
REACH_COVERAGE_MIN should be a full hit or provisional -- so both answers are
deliberate rather than inherited." The rulings above select, in that parked
prompt's own enumeration, option (b) for the first question and option (a) for
the second.

## Requirements

R1 (behavior): "an artifact carrying an EMPTY own commitment battery may
   NOT ground reach" — RULING 1.

R2 (behavior): "a reaching artifact with no commitments of its own takes a
   NEW typed rejection exit in reach_sweep" — S1.

R3 (artifact): "The exit-documentation check from the structural-programs fix
   (mutation-proven both ways) asserts every exit is documented — the new exit
   and that docstring/check move in the SAME commit." — S1.

R4 (behavior): "coverage exactly EQUAL to REACH_COVERAGE_MIN remains a FULL
   hit, as written (`<` comparison stands)" — RULING 2.

R5 (artifact): "a test constructing coverage == floor asserts HIT full" — S2.

R6 (artifact): "a one-line doc note marks the `<` comparison deliberate,
   citing this tranche" — S2.

R7 (process): "rehearsal re-run: experiments/2026-08-22-live-reach-rich-run/
   rehearsal.py against the fixed tree — S2 (empty battery) must now take the
   NEW exit; S8a must remain HIT; S8c must remain E4. Paste all three." — S3.

R8 (artifact): "Update the 08-21 census tooling's exit vocabulary if it
   enumerates exits by name." — S3.

R9 (process): "mutation-proven on both rulings — disable the empty-battery
   guard in a scratch copy (test RED), restore (GREEN); flip `<` to `<=`...
   rather, break the boundary the other way (make 0.5 provisional) and watch
   the pin test go RED; paste both runs." — TESTS.

R10 (artifact): "Map moves in the same commits (the reach-covering document's
   Traps gains this ruling pair)." — GATE.

R11 (process): "Deliver R-by-R with pasted PROOF, closing with one line per
   ruling: what reach_sweep now does that is deliberate." — GATE.

## Standing constraints

C1: "This is NOT a formalism-kind penalty: emptiness of commitments is not
    informality, and no admission, rank, or criticism outcome moves — only
    reach eligibility." — RULING 1. Binds the blast radius: nothing outside
    reach eligibility may change. (Also the operator design law "Formalism is
    an option, never an obligation", CLAUDE.md.)

C2: "`<` comparison stands" — RULING 2. The comparison operator in
    `reach_sweep` is NOT edited; only pinned and annotated.

C3: "Do NOT change REACH_COVERAGE_MIN's VALUE as part of this." — carried
    from the parked prompt this tranche executes
    (`experiments/2026-08-22-reach-structural-programs-fix/PARKED.md`
    P5-reach), and consistent with C2.

C4: "Use `python -m pytest`, never bare pytest." — SETUP.

C5: "GATE: ring while iterating; full gate at the boundary; docs_verify
    full." — GATE.

C6: "Commit and push every phase boundary (retry 2s/4s/8s/16s)." — GATE.

C7: "the workflow's own stop conditions apply, nothing else stops." —
    opening line.

C8: "A parallel window is executing the reach-rich LIVE run from the frozen
    design — it runs against main-at-launch, so your change does not affect
    it ... A second parallel window is running a read-only census; no shared
    files with either." — KNOWN CURRENT STATE. No coordination required; do
    not touch either window's working files.

C9: "KNOWN CURRENT STATE: gate baseline 0 failed (3818 at 2a744325f);
    docs_verify 3 pre-existing shallow-clone failures; 5 MCP-thread tests
    flaky under -n 4; smokes green; the sweep is retired." — the baseline
    every validation delta is measured against.

C10: Branch. The brief's SETUP names `claude/reach-p5-rulings-t6wm2d`; the
    session's designated development branch is
    `claude/reach-p5-rulings-codify-097nkz`, already checked out at
    `2a744325f` (the exact commit the brief's `merge-base --is-ancestor`
    guard names). The designated branch wins; the ancestry guard is
    satisfied either way. Recorded here rather than silently reconciled.

## Open questions (for dr-spec-change)

Q1: WHERE the empty-battery exit is taken — the outer per-artifact loop
    (decided once per artifact) or the inner per-pair loop (decided per
    pair). R2 says "takes a NEW typed rejection exit", and the existing exit
    taxonomy is PAIR-level, while the property being tested is
    ARTIFACT-level. The exit-documentation check (R3) counts `continue`
    statements in the INNER loop, so the two placements need different check
    amendments.

Q2: What the new exit is NAMED. The existing vocabulary is E1..E5 + "HIT
    full", in the order `reach_sweep` takes them. A guard on the reaching
    artifact is decided BEFORE E1, so appending "E6" would name it out of
    order; "E0" would not, but no precedent exists either way. The name
    enters three places (module docstring, `census.py`, `rehearsal.py`), so
    it must be chosen once.

Q3: Whether "EMPTY own commitment battery" means `artifact.interface.
    commitments` being empty specifically, or a broader emptiness (e.g. an
    interface whose commitments are all unregistered). The brief's own
    evidence pointer — rehearsal S2, `"carried": []` — is the narrow
    reading; the broader one is not stated.

Q4: Whether the 08-21 census tooling change (R8) is in-scope as an EDIT to a
    committed measurement instrument whose recorded outputs (`census.json`,
    `census-verdicts.json`) were produced by the old vocabulary. R8 says
    "Update ... if it enumerates exits by name" without saying whether the
    recorded outputs are re-derived.

## Amendments

(append-only; later operator messages land here)

**Amendment 1 (2026-08-22).** Raised at CHECKLIST.md step 10, where
`tools/diff_budget.py` returned `EXCEEDED` (177 insertions against SPEC.md's
ledgered ceiling of 150, with ~18 more planned). Presented to the operator as
a stop in the standard format with three priced options. The operator chose,
verbatim:

> Raise ceiling to 210, continue (Recommended)

R12 (process): the SPEC.md insertion ceiling is 210, not 150. The overrun is
entirely test-docstring prose recording each pin's ruling authority and its
motivating record; production insertions (25) and map insertions (44) both
came in UNDER their per-item estimates. No requirement, file or behaviour
changes. SPEC.md's Budget section carries the re-itemisation.
