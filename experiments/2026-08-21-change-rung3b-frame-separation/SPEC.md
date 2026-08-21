# Spec for: Rung 3b — the frame-separation invariant

Traces: every item cites R numbers from `REQUEST.md`. Untraceable items are bugs.

## The design in one paragraph

One new module, `src/deepreason/calculus/separation.py`, holding a DERIVED
predicate over replayed state and one enforcement function. Definition 7.1's
`Q_L` needs no construction: `build_dep` emits `dep` edges from
`RefRole.DEPENDENCE` **and from nothing else** (`DR-SUB-adjudication`, *Entry
points*), so mention edges are already absent from the graph the harness
records. The predicate therefore reads `harness.state.att` and
`harness.state.dep`, forgets direction, and computes connected components. The
enforcement returns a frozen `Consultability` verdict; it writes nothing,
registers nothing, and mints nothing, which is R64's whole content.

## Items

**S1 (R1, R2) — the predicate.**
Files: `src/deepreason/calculus/separation.py` (new).
Before: no frame-separation predicate exists anywhere in the tree (census below:
zero hits).
After: three symbols.

- `_components(nodes, edges) -> dict[str, frozenset[str]]` — private, pure.
  Undirected connected components. A node with no incident edge maps to the
  singleton `{node}`, which is what makes Definition 7.2 evaluable on an empty
  graph instead of raising.
- `adjudication_component(harness, node) -> frozenset[str]` — **Definition
  7.1**, `Comp_L(x)`, over `att ∪ dep` with direction forgotten. Derived on
  every call from replayed state; nothing is stored and nothing is cached across
  calls (C4, and the same shape `views.py` already uses).
- `frame_separated(harness, assertion, subject) -> bool` — **Definition 7.2**,
  `Comp_L(f) ∩ Comp_L(b) = ∅`.

R2 is satisfied structurally rather than by a filter this rung adds: there is no
mention edge in `att` or `dep` to exclude. The acceptance check proves the
CONSEQUENCE (a mention-only link leaves the two separated) rather than the
absence of a line of code.

    accept: python -m pytest tests/test_calculus_frame_separation.py::test_a_mention_leaves_the_assertion_and_its_subject_separated -q
            -> 1 passed

**S2 (R3) — the enforcement, and its typed diagnostic.**
Files: same module.
After: `Consultability` (a frozen dataclass: `consultable: bool`, `code: str |
None`, `detail: tuple[str, ...]`) and `consultability(harness, assertion,
subject) -> Consultability`, plus two module-level codes:

- `FRAME_NOT_SEPARATED = "frame-not-separated"` — `Comp(f) ∩ Comp(b) ≠ ∅`.
  `detail` carries the shared component, sorted, so a reader sees WHICH nodes
  joined them rather than only that something did.
- `FRAME_ENDPOINT_UNREGISTERED = "frame-endpoint-unregistered"` — the assertion
  or the subject is not a registered artifact, so the graph condition cannot be
  evaluated at all. `detail` names the missing ids. See A1.

The code is a value a caller branches on, never message text — the same contract
`ClaimDecodeError.code` already carries in this package.

    accept: python -m pytest tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable -q
            -> 1 passed

**S3 (R4) — never a manufactured refutation.**
Files: same module; proven in two independent ways.

1. BEHAVIOURALLY, in the gate: the violation test captures `state.att`,
   `state.dep`, `state.status`, the warrant map and the log line count before
   the call and asserts every one of them EQUAL after it. That is R7's
   "byte-identical label comparison" in its strongest available form.
2. STRUCTURALLY, in the map: `separation.py` contains no call that could write —
   a negative grep for the write surface (`create_artifact`, `register_`,
   `record_`, `blobs.put`, `Warrant`) PAIRED with a positive anchor on the same
   file, per `SCHEMA.md`'s check-writing rule 1.

    accept: python -m pytest tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable -q
            -> 1 passed  (the same test carries the before/after capture)
    accept: ! grep -qE "create_artifact|register_|record_|blobs\.put|Warrant" src/deepreason/calculus/separation.py && grep -q "def consultability" src/deepreason/calculus/separation.py
            -> exit 0

**S4 (R5) — the scope boundary, stated.**
Files: the module docstring, and this section.

> **SCOPE BOUNDARY.** Full frame assertions do not exist until Rung 4. This rung
> ships the PREDICATE and the ENFORCEMENT over the graph shapes current
> machinery can construct, so that Rung 4 builds its frame layer against an
> invariant that already exists and already refuses. Rung 4's gate then invokes
> Theorem 7.3 instead of re-arguing it.
>
> Not built here, and each named so a later reader can see the line was drawn
> deliberately: **no frame-assertion artifact** (`poietic.frame-assertion.v1`
> stays declared-and-unbuilt in `CLAIM_SCHEMAS`, refused by `decode` with
> `claim-schema-not-implemented`); **no standing view** — nothing enumerates
> consulted assertions, and `Consult_L`/`Background_L` are not implemented;
> **no scope DSL** — `σ: Π_L → {0,1}` is Rung 4's.
>
> The consequence, stated so it is not discovered later as a surprise:
> `consultability` has no CALLER in `src/` at the end of this rung. That is the
> boundary working, not an omission. It is exercised by the gate over real
> constructed graphs, and the enforcement site is Rung 4's to wire.

    accept: python -c "
    from deepreason.calculus import CLAIM_SCHEMAS, ClaimDecodeError, decode
    assert 'poietic.frame-assertion.v1' in CLAIM_SCHEMAS
    try:
        decode('{\"schema\": \"poietic.frame-assertion.v1\"}')
        raise SystemExit('accepted - wrong')
    except ClaimDecodeError as e:
        assert e.code == 'claim-schema-not-implemented', e.code
    "       -> exit 0 (verified at spec time)
    accept: ! grep -rqE "Consult_L|Background_L|standing_frames|frame_scope" src/deepreason/ && grep -q "SCOPE BOUNDARY" src/deepreason/calculus/separation.py
            -> exit 0

**S5 (R6) — the gate EXHIBITS the separation, not the mention.**
Files: `tests/test_calculus_frame_separation.py` (new).
Two constructions, both built through the ordinary harness write path:

| Construction | Graph | What it exhibits |
|---|---|---|
| ρ `mention`s X | `att = {}`, `dep = {}` | `Comp(ρ) = {ρ}`, `Comp(X) = {X}` — DISJOINT SETS asserted, not "ρ has a mention ref" |
| the above, then a critic C warrants an attack on X | `att = {(C, X)}`, `dep = {}` | `Comp(X) = {X, C}`, `Comp(ρ) = {ρ}` — still disjoint; X falls to `REFUTED` and ρ's label is UNCHANGED |

The second row is Theorem 7.3 in full: `L'` extends `L` by exactly a new critic
component whose only connection to the old graph is an attack on `b`, and
`ℓ_{L'}(f) = ℓ_L(f)`. Measured, not assumed — M1 below.

    accept: python -m pytest tests/test_calculus_frame_separation.py::test_a_mention_leaves_the_assertion_and_its_subject_separated tests/test_calculus_frame_separation.py::test_wound_persistence_holds_when_the_separation_does -q
            -> 2 passed

**S6 (R7) — the violation is inert.**
Files: same test file. The construction is the one Definition 7.2's own sentence
names — "reach records supporting `f` must mention, rather than depend on, the
subject":

    X                      the subject
    M -dependence-> X      a supporting record that DEPENDS on the subject
    ρ -mention->    X      the mention law is obeyed
    ρ -dependence-> M      and the assertion rests on that record

`dep = {(M, X), (ρ, M)}`, so undirected ρ–M–X is one component and `Comp(ρ) ∩
Comp(X) = {ρ, M, X} ≠ ∅`. The mention law holds and separation fails — which is
precisely the gap Rung 3b exists to close. Asserted: `consultable is False`,
`code == FRAME_NOT_SEPARATED`, `detail` contains both endpoints, and the
five-way before/after capture of S3(1) is equal.

    accept: python -m pytest tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable -q
            -> 1 passed

**S7 (R8) — the mutation proof.**
Not a code item: a procedure run at the validation step, recorded in
VALIDATION.md with BOTH pasted runs. Copy the tree to the session scratchpad,
neuter `frame_separated` there to `return True`, run the violation test, observe
RED, discard the copy. `__pycache__` is cleared before the measurement
(`SCHEMA.md`: "stale `__pycache__` survives a revert").

    accept: VALIDATION.md contains the RED run and the restored GREEN run, both pasted verbatim, with the mutated line shown.

**S8 (R9) — the axiom ledger.**
Not a code item: VALIDATION.md names, with the evidence for each,
**A6 PROVED** (consulted frame assertions satisfy frame-separation — the
predicate exists, is computed from state, and refuses),
**A5 PROVED** (mention, not depend — S5 row 1 exhibits the mention AND the
separation it buys),
**A1 PRESERVED** (append-only log, state a pure fold — S6's log-line-count
capture is unchanged by the check),
**A3 PRESERVED** (status = grounded pass then support pass — S6's status capture
is unchanged, and `separation.py` imports nothing from `adjudication`).

    accept: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/separation.py').read_text()); mods=[n.module or '' for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names]; assert not any('adjudication' in m for m in mods), mods; assert 'def frame_separated' in pathlib.Path('src/deepreason/calculus/separation.py').read_text()"
            -> exit 0

**S9 (R11) — frozen surfaces.** See the forecast section: computed CLEAR.

**S10 (R12) — the map moves in the same commit.**
Files: `docs/map/SUB-calculus.md` (owns the package; `Owns:` gains
`separation.py`, `Seams-undocumented:` gains `calculus x adjudication`, and a
new section states the invariant with two checks) and
`docs/map/CON-standing-and-background.md` (the concept document for the standing
axis; gains the invariant under *Invariants* and a row under *Where to change
what*). `Verified-at:` advances on both, and only after their checks are RUN.

    accept: python tools/docs_verify.py -> 3 failed (the pre-existing CON-run-identity.md shallow-clone baseline, docs/AUDIT_BASELINES.md), 0 new
    accept: grep -q "separation.py" docs/map/SUB-calculus.md && grep -q "frame-separation" docs/map/CON-standing-and-background.md

**S11 (R13) — gate discipline.** Ring = `tests/test_calculus_frame_separation.py
tests/test_calculus_claim_substrate.py tests/test_adjudication.py` while
iterating. Boundary = `python -m pytest tests/ -q -n 4` (0 failed) and
`python tools/docs_verify.py` FULL.

**S12 (R10, R14) — size and delivery.** Budget below; DELIVERY.md is
`dr-deliver-change`'s R-by-R table with pasted proof and the closing
Rung-4-builder line.

## Assumptions (operator may override)

**A1 (R3).** An unregistered endpoint gets its own typed refusal
(`FRAME_ENDPOINT_UNREGISTERED`) rather than a silent `consultable = True`.
Reading: Definition 7.2 says nothing about unregistered nodes, and the literal
component reading would make an unregistered pair "separated" — i.e. a frame
whose subject does not exist would be reported CONSULTABLE. Chosen because it is
the smallest reading that does not lie, and because this repo has the exact
precedent in `premises.py::premise_rent_sweep`: "'we could not check' must never
look like 'we checked and it was fine'". Six lines. Assumed, operator may
override.

**A2 (R1).** `Comp_L(x)` for a node with no incident `att`/`dep` edge is the
singleton `{x}`. Definition 7.1 builds `Q_L` from the edge relation, which leaves
isolated vertices formally undiscussed; the singleton is the standard reading and
the only one on which an empty graph is separated rather than an error. Assumed,
operator may override.

**A3 (R12).** The invariant is stated in the two documents that already cover it
(`DR-SUB-calculus` owns the code, `DR-CON-standing-and-background` owns the
concept) rather than in a new `INV-frame-separation.md`. Reading: LADDER §5b
assigns the v2 axiom `INV-` document to **Rung 4** ("owned by Rung 4 — the first
rung that has all four layers to separate"), so minting a separate `INV-` here
would duplicate the document Rung 4 must write. Assumed, operator may override.

## Questions for operator (STOP if non-empty)

(none — every fork above was decided against the record or the ladder, per
`dr-ask-the-right-question`'s dominance test)

## Out of scope (explicit)

- **Wiring `consultability` into `premises.py::standing_attributions`.** That
  function is the codebase's only existing `Consult_L`, so it is the tempting
  neighbour. NOT REQUESTED, and refused for a reason beyond scope: it would
  change Rung 2's DELIVERED cascade semantics (one critic attacking both an
  attribution and its premise joins their components, which would disarm the
  cascade), and R64's subject is a consulted FRAME ASSERTION, which LADDER §5b
  assigns to Rung 4. Parked (PARKED.md P1).
- A `poietic.frame-assertion.v1` body, `Consult_L`, `Background_L`, the scope
  predicate σ, the compatibility criterion of §6.2, the departure protocol —
  all Rung 4. Not requested.
- Theorem 7.3's own general proof as a property test over random graphs. Not
  requested; the rung's gate exhibits the precondition, which is what LADDER
  asks for.
- Fixing `INDEX.md`'s missing concept rows (found while scoping — see
  PARKED.md P2). Not requested, not this tranche.

## Frozen-surface contact forecast

**CLEAR — computed, not hand-checked.** `tools/blast_radius.py`, verbatim:

    "frozen_surface_contacts": [],
    "frozen_adjacent_contacts": [],
    "frozen_surface_verdict": "CLEAR"

    disclosure_summary: "This change touches none of the five frozen surfaces.
    0 test file(s) and 0 map document(s) assert on the touched targets today.
    Reachability here means a syntactic call path exists from a known entry
    point; it does not prove the path is ever actually exercised at runtime --
    a symbol can be syntactically reachable and still never fire because of a
    runtime precondition this gate does not evaluate."

Invocation:

    python tools/blast_radius.py \
      --files src/deepreason/calculus/__init__.py docs/map/SUB-calculus.md \
              docs/map/CON-standing-and-background.md \
      --symbols adjudication_component frame_separated consultability \
                Consultability FRAME_NOT_SEPARATED FRAME_ENDPOINT_UNREGISTERED

Matches LADDER §4's Rung 3b row (all dashes). No operator grant is requested.

**Recorded, because it is the reason this section says CLEAR rather than
CONTACT.** The first invocation named the predicate `separated` and the gate
returned `frozen_surface_verdict: CONTACT` —

    {"surface": "replay-validation record formats (invariants.py)",
     "tier": "SYMBOL_INDIRECT", "target": "separated",
     "detail": "'separated' referenced in src/deepreason/invariants.py
                (grep-based; not proof of semantic contact)"}

`src/deepreason/invariants.py:503` is the English word inside a comment
("`# separated by arbitrary intervening records.`"), not a symbol. The symbol was
renamed `frame_separated` — which is the better name for Definition 7.2 anyway —
rather than the finding argued away, so the gate itself now reports CLEAR and no
reader has to trust a paragraph over a tool.

## Blast-radius census

Gate-reported consumers for the declared targets: `"tests": []`,
`"map_checks": []`, `"qualification_digest": []`, `"wheel_smoke_pins": []`.

All six new symbols returned `reachability: UNKNOWN` — expected, since none of
them exists in the tree yet, and exactly the case `dr-spec-change` §5 says the
manual grep must cover. Run, pasted:

    adjudication_component           0 hits    frame-not-separated             0 hits
    frame_separated                  0 hits    frame-endpoint-unregistered     0 hits
    consultability                   0 hits    test_calculus_frame_separation  0 hits
    Consultability                   0 hits    separation.py                   0 hits
    FRAME_NOT_SEPARATED              0 hits
    FRAME_ENDPOINT_UNREGISTERED      0 hits
    (grep -rn over tests/ docs/map/ src/)

Consumers of the two EXISTING files this tranche edits, enumerated in full:

| Consumer | Of | Classification |
|---|---|---|
| `tests/test_calculus_claim_substrate.py::test_the_compiler_is_the_only_authority_on_ref_roles` | globs `src/deepreason/calculus/*.py` and asserts `role_sites == {"compiler.py"}` | **MUST NOT MOVE** — `separation.py` reads `state.att`/`state.dep` and never touches `RefRole`. The single highest-risk hit in this census, and the reason the census was run before the code |
| `tests/test_calculus_claim_substrate.py::test_no_field_was_added_to_problem_state_or_event` | the package's no-new-state property | **MUST NOT MOVE** — nothing is stored |
| `tests/test_calculus_claim_substrate.py` (imports `deepreason.calculus`, `.operations`, `.programs`) | `__init__.py`'s exports | **MUST NOT MOVE** — the edit is additive; every existing name keeps its place in `__all__` |
| `src/deepreason/programs.py` (imports `deepreason.calculus.programs`) | the two structural programs | **MUST NOT MOVE** — no program is added or changed |
| `docs/map/SUB-calculus.md` checks (`len(CLAIM_SCHEMAS) == 9`, `_STRUCTURAL_PROGRAMS`, `! grep -rq "deepreason.calculus" src/deepreason/scheduler/`, the `premises.py` hand-kept-in-step check) | the package's shape | **MUST NOT MOVE** — no schema name is added (`poietic.frame-assertion.v1` is already in the closed set), no program is added, the scheduler is untouched, `premises.py` is untouched |
| `docs/map/SUB-calculus.md` `Owns:` / `Seams-undocumented:` headers | the header itself | **EXPECTED TO MOVE** — S10 |
| `docs/map/CON-standing-and-background.md` *Invariants* / *Where to change what* | the concept | **EXPECTED TO MOVE** — S10 |

## Measurements

**M1 — both constructions behave as the design claims, measured before the
design was written down.** Scratch probe over the ordinary harness write path
(`scratchpad/probe1.py`), pasted:

    GOOD   att []  dep []
           status {rho: ACCEPTED, X: ACCEPTED}
    AFTER  att [(C, X)]  dep []
           status {X: REFUTED, rho: ACCEPTED, nu: ACCEPTED, C: ACCEPTED}
           rho 8ed525f4  X fbc9cfdb  nu a7714dbe  C 9daec59d

    VIOL   att []  dep [(M, X), (rho2, M)]
           ids rho2 f4743238  X2 fbc9cfdb  M c4ef82f7

Supports S5 (a mention produces NO edge in either relation, so the components
are singletons and stay disjoint when the subject is attacked — and ρ stays
`ACCEPTED` while X goes `REFUTED`, which is Theorem 7.3's conclusion) and S6
(the depends-on-the-subject reach record joins ρ and X into one component
through `dep` alone).

**M2 — mention edges need no filter.** `DR-SUB-adjudication`, *Entry points*:
"`build_dep(artifacts)` — support edges from `RefRole.DEPENDENCE` refs, and from
nothing else." Supports S1's claim that R2 is a property of the recorded graph
rather than a line this rung writes.

## Options

**A — a new `INV-frame-separation.md` map document.** ~60 extra lines, and it
duplicates the v2 axiom `INV-` document LADDER §5b assigns to Rung 4.
*Rejected*: cites LADDER §5b.

**B — wire the enforcement into `premises.py::standing_attributions`.** ~15
lines of `src/`, but it changes Rung 2's delivered cascade semantics and R64's
subject is a frame assertion, not an attribution. *Rejected*: cites the
out-of-scope section and LADDER §5b's A5 row (attributions → Rung 2, frame
assertions → Rung 4).

**C — predicate + enforcement in `calculus/separation.py`, exercised by the
gate, wired by Rung 4.** Two new files, two map documents edited, zero frozen
contact (computed), ~193 lines. **CHOSEN**: cites M1 (both graph shapes are
constructible today, so the gate has real exhibits rather than hand-built
fixtures) and M2 (no filter needed).

## Budget

    python3 -c "print(sum([82, 7, 82, 14, 8]))"   -> 193

| Item | Lines |
|---|---|
| `src/deepreason/calculus/separation.py` (new) | 82 |
| `src/deepreason/calculus/__init__.py` (exports) | 7 |
| `tests/test_calculus_frame_separation.py` (new) | 82 |
| `docs/map/SUB-calculus.md` | 14 |
| `docs/map/CON-standing-and-background.md` | 8 |
| **total** | **193** |

~193 lines, 2 commits (code+tests+map together — SCHEMA.md rule 1 — then
validation artifacts). Frozen surfaces touched: **none** (computed CLEAR).

**Stated against R10.** LADDER estimates 80–140; this plan is 193, under the
~200 STOP threshold but above the ladder's upper figure. What accounts for the
difference, itemized so the operator can see nothing Rung-4-shaped leaked in:
`separation.py` at 82 lines IS inside the ladder's estimate on its own. The
overshoot is entirely the gate the tranche instruction mandates — 82 lines of
test carrying two exhibited constructions, a Theorem 7.3 extension, and a
five-way before/after equality capture — plus 22 lines of map. No requirement
grew, no Rung 4 machinery is present, and `src/` totals 89 lines.

Rubric: 6/6 yes.
