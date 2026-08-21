# Validation for: Rung 3b — the frame-separation invariant

Base: `main@c8071fc34`. Head at validation: `f2fba83ae`.

## Acceptance checks

**S1 (R1, R2) — the predicate.**

    $ python -m pytest tests/test_calculus_frame_separation.py::test_a_mention_leaves_the_assertion_and_its_subject_separated -q
    1 passed in 0.05s

PASS. The test asserts `Comp(rho) == {rho}` and `Comp(X) == {X}` — singleton
components, hence disjoint. That is the SEPARATION exhibited, not the mention
inferred from it.

**S2 (R3) — the enforcement and its typed diagnostic.**

    $ python -m pytest tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable -q
    1 passed in 0.06s

PASS. `verdict.consultable is False`, `verdict.code == FRAME_NOT_SEPARATED`,
and `set(verdict.detail) == {assertion, case, subject}` — the shared component
named, so a reader sees WHICH nodes joined the two rather than only that
something did.

**S3 (R4) — never a manufactured refutation.** Both halves.

    $ ! grep -qE "create_artifact|register_|record_|blobs\.put|Warrant" src/deepreason/calculus/separation.py && grep -q "def consultability" src/deepreason/calculus/separation.py
    exit=0

PASS structurally (negative grep paired with a positive anchor on the same
file, `SCHEMA.md` check-writing rule 1). PASS behaviourally through S6's
five-way before/after equality, below.

**S4 (R5) — the scope boundary held.**

    $ python -c "... decode('{\"schema\": \"poietic.frame-assertion.v1\"}') ..."
    exit=0        # still refused with claim-schema-not-implemented
    $ ! grep -rqE "Consult_L|Background_L|standing_frames|frame_scope" src/deepreason/ && grep -q "SCOPE BOUNDARY" src/deepreason/calculus/separation.py
    exit=0

PASS. No frame-assertion artifact, no standing view, no scope DSL. Checked,
not asserted — this is the SIZE clause's own diagnostic for Rung 4 leakage and
it comes back clean.

**S5 (R6) — the gate exhibits the separation, and Theorem 7.3 with it.**

    $ python -m pytest \
        tests/test_calculus_frame_separation.py::test_a_mention_leaves_the_assertion_and_its_subject_separated \
        tests/test_calculus_frame_separation.py::test_wound_persistence_holds_when_the_separation_does -q
    2 passed in 0.08s

PASS. The second test is Theorem 7.3 in full: `L'` extends `L` by exactly a new
critic component whose only connection to the old graph is an attack on `b`;
`Comp(b)` becomes `{b, critic}` and `Comp(f)` stays `{f}`; `b` falls to
`REFUTED` and `l(f)` equals the value `f` actually held before the extension.
Theorem 7.3's precondition is EXHIBITED, which is what LADDER Rung 3b asks for.

**S6 (R7) — the violation is inert.**

    $ python -m pytest tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable -q
    1 passed in 0.06s

PASS. `_capture(harness) == before` compares five things whole: `state.att`,
`state.dep`, every `state.status` label, the warrant map, and the `log.jsonl`
line count. Byte-identical labels, no attack edge, no warrant, no new event.

**S7 (R8) — the mutation proof.** Two mutations, both in throwaway copies under
the session scratchpad; `__pycache__` cleared in each before measuring
(`SCHEMA.md`: "stale `__pycache__` survives a revert"). The repository itself
was never mutated.

*Mutation A — `frame_separated` neutered.*

    === the line about to be neutered ===
    93-    components = _state_components(harness, assertion, subject)
    94-    return not components[assertion] & components[subject]
    === mutated ===
    93-    return True  # MUTATION: the separation check disabled
    === RED run ===
    >       assert not frame_separated(harness, assertion.id, subject.id)
    E       AssertionError: assert not True
    tests/test_calculus_frame_separation.py:114: AssertionError
    FAILED tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable
    1 failed, 3 passed in 0.24s
    === copy discarded; GREEN run on the real tree ===
    4 passed in 0.12s

*Mutation B — the shared component root neutered.* Mutation A proved the
PREDICATE can fail, but it left `consultability` green, because the enforcement
computes its own intersection from `_state_components` rather than calling
`frame_separated`. A mutation proof that stops there would leave the half R64
actually governs unproven. So the check was disabled one level down instead —
`_components` made to forget every `att`/`dep` edge:

    mutation B applied: _components ignores every att/dep edge
    E       assert True is False
    E        +  where True = Consultability(consultable=True, code=None, detail=()).consultable
    tests/test_calculus_frame_separation.py:111: AssertionError
    FAILED tests/test_calculus_frame_separation.py::test_wound_persistence_holds_when_the_separation_does
    FAILED tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable
    2 failed, 2 passed in 0.15s
    === copy discarded; GREEN on the real tree ===
    4 passed in 0.12s

PASS. Under B the enforcement returns `Consultability(consultable=True,
code=None, detail=())` where it must refuse, and the Theorem 7.3 exhibit loses
its component identity — both the predicate and the enforcement are shown
failable.

The two map checks were mutation-proved the same way BEFORE being written down
(`dr-execute-step`, "Durable tests, checks, and probes" rule 3): injecting
`harness.create_artifact` turned the no-write check RED, and adding `from
deepreason.adjudication.edges import build_dep` turned the import check RED with
`AssertionError: ['__future__', 'dataclasses', 'deepreason.adjudication.edges']`.

**S8 (R9) — the axiom ledger.**

    $ python -c "import ast,pathlib; ... assert not any('adjudication' in m for m in mods) ..."
    exit=0

| Axiom | Verdict | The evidence, named |
|---|---|---|
| **A6** — consulted frame assertions satisfy frame-separation | **PROVED** | The predicate exists (`frame_separated`, Definition 7.2), is computed from replayed state, and the enforcement REFUSES a construction that fails it — S1, S2, S6, and mutation B showing the refusal is failable rather than vacuous |
| **A5** — mention, not depend | **PROVED** | S5 row 1: the assertion `mention`s its subject AND the two components are disjoint. S6 proves the two conditions are independent — the mention law is fully obeyed there and separation fails anyway, which is exactly why A5 alone was not enough |
| **A1** — the log is append-only, state a pure fold over it | **PRESERVED** | S6's capture includes the `log.jsonl` line count and it is unchanged across the enforcement call: the check appends nothing. `separation.py` holds no call that could write (S3) |
| **A3** — status = grounded attack pass, then the acyclic support pass | **PRESERVED** | S6's capture includes every `state.status` label, unchanged. `separation.py` imports nothing from `adjudication` (S8 accept, exit 0): it consumes that package's OUTPUT through replayed state, never its logic, so no status can be computed anywhere else |

**S9 (R11) — frozen surfaces.** See the frozen-surface diff below.

**S10 (R12) — the map moved in the same commit.**

    $ grep -q "separation.py" docs/map/SUB-calculus.md && grep -q "Frame-separation" docs/map/CON-standing-and-background.md
    exit 0

PASS. Both documents moved in commit `1da817eaa`, the same commit as the code —
not in a trailing docs commit. Four new checks, each RUN before it was written
down.

**S11 (R13) / S12 (R10, R14)** — the gate below, and the budget under
*Requirement sweep* R10/R15.

## Full gate

    $ python -m pytest tests/ -q -n 4
    3759 passed, 6 skipped in 910.19s (0:15:10)

PASS. **0 failed.** Baseline is 3755 passed (`docs/AUDIT_BASELINES.md`); 3759 =
3755 + the 4 tests this rung adds. No known-flaky MCP-thread test fired, so no
isolation run was owed.

The ring, run at CHECKLIST step 10 before the boundary gate:

    $ python -m pytest tests/test_calculus_frame_separation.py \
        tests/test_calculus_claim_substrate.py tests/test_adjudication.py \
        tests/test_premise_channel.py -q
    58 passed in 1.10s

The census's highest-risk hit —
`test_the_compiler_is_the_only_authority_on_ref_roles`, which globs
`src/deepreason/calculus/*.py` and asserts `RefRole` appears only in
`compiler.py` — passes with `separation.py` inside that glob.

## Record-behavior preservation

The change touches no reader or validator of the append-only record, so this is
a spot-check rather than an owed proof. Run anyway, on one known-good root and
one defect-era root, at HEAD and at the base:

    HEAD (f2fba83ae)                    BASE (c8071fc34)
    run-6472629d... 0 violations         run-6472629d... 0 violations
      sha 88733c165b3d0f4e                 sha 88733c165b3d0f4e
    run-f4fa6663... 6 violations         run-f4fa6663... 6 violations
      checks ['foreign-criticism']         checks ['foreign-criticism']
      sha 99ea4d274a3ac0e3                 sha 99ea4d274a3ac0e3

UNCHANGED — the `verify_root` output digests are identical across the change.
`run-6472629d` is the committed adjudication-blindness demonstration and
`run-f4fa6663` carries six pre-existing `foreign-criticism` findings; both
verdicts are exactly what the base produces.

## Frozen-surface diff

    $ git diff --stat c8071fc34..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    (no output)

PASS — empty, which matches LADDER §4's Rung 3b row (all dashes) and the
`blast_radius.py` forecast SPEC.md pasted. No operator grant was requested and
none was needed.

Full changed-file list for the tranche:

    docs/map/CON-standing-and-background.md |  13 +++-
    docs/map/SUB-calculus.md                |  45 ++++++++++-
    src/deepreason/calculus/__init__.py     |  14 ++++
    src/deepreason/calculus/separation.py   | 111 +++++++++++++++++++++++++
    tests/test_calculus_frame_separation.py | 134 +++++++++++++++++++++++++++++
    5 files changed, 312 insertions(+), 5 deletions(-)

## Map

    docs_verify:            60 documents, 928 checks, 3 failed  : PASS
    docs_verify --audit:    0 finding(s)                        : PASS
    docs_verify --links:    0 dangling reference(s), 60 docs    : PASS
    docs_verify --coverage: 6 seams swept, 16 without a Sweep: header, 2 findings : PASS

`docs_verify`'s 3 failures are exactly the recorded baseline — all three are
`CON-run-identity.md` git-history checks that need an unshallowed clone
(`docs/AUDIT_BASELINES.md`: "3 pre-existing failures, all `CON-run-identity.md`
git-history checks"). Two fail with `fatal: ambiguous argument ... unknown
revision`, which is the shallow clone, not a false claim. **0 new.**

`--coverage`'s 2 findings name `SEAM-periphery-x-verification.md`
(`amendment/apply.py`) and `SEAM-schools-x-scratch.md` (`informal/trial.py`) —
neither document nor either site is touched by this tranche. Proven
mechanically rather than by inspection: the same command at the base commit
`c8071fc34`, in a temporary worktree, returns the identical line —
`6 seam(s) swept, 16 without a Sweep: header, 2 finding(s)`. Zero delta.

    docs_verify --stale: 6 document(s) worth re-reading

Each entry judged, none left silent:

| Entry | Disposition |
|---|---|
| `SUB-calculus.md`: 1 commit since `5deec374` — `1da817eaa` | **Dismissed, structural.** That one commit IS this tranche's own code+map commit, and a document cannot carry the hash of the commit that contains it. The base already showed this document at **2** commits since `e901bb05`, so the change strictly REDUCED its staleness; the residue is the unavoidable self-reference, which is also the convention every prior tranche here leaves |
| `CON-run-identity.md`, `CON-schools.md`, `SEAM-manifest-x-schools.md`: 1 commit each, all `bce018ae5` | **Dismissed, not ours.** Pre-existing at the base with the same counts and the same commit (`all-configs-allowed`, a different tranche) |
| `SUB-evidence.md`: 1 commit, `1a32fb193` | **Dismissed, not ours.** Pre-existing at the base; the P4 tranche |
| `SUB-scheduler.md`: 4 commits since `e6badeead` | **Dismissed, not ours.** Pre-existing at the base; Rung 2 and the all-configs tranche |

    new checks added by this change:
      SUB-calculus.md            — the separation section, 2 checks
                                   (behavioural: the two exhibit tests;
                                    structural: no-write + no-adjudication-import)
      SUB-calculus.md Traps      — 2 checks (the mention-is-not-enough trap;
                                   the no-caller-by-design trap)
      CON-standing-and-background.md — 1 check (the invariant is importable and
                                   its gate passes)
    record observables added vs sweep probes:
      NONE. This rung adds no field, record type, event or finding to the typed
      record — `separation.py` writes nothing, and `git diff` over the five
      frozen surfaces is empty. So no sweep probe is owed, and this is a
      recorded judgement rather than an omission: "sweep byte-identical" would
      be trivially true here because there is no new data for a sweep to read.
    wheel smoke: packaging surface untouched — smoke not owed.
      $ git diff --stat c8071fc34..HEAD -- pyproject.toml src/deepreason/mcp* \
          src/deepreason/cli* scripts/
      (no output)
      No console entry point, MCP tool, schema sha or wheel-layout pin moves,
      which is what the tranche instruction predicted ("public surface should
      not move this rung, so no re-pin is expected").

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 predicate, derived from replayed state | S1 output; `adjudication_component`/`frame_separated` recompute components on every call and store nothing (SUB-calculus *State it owns* unchanged, its check green in the full `docs_verify` run) |
| R2 mention edges excluded | S1 output — the mention yields singleton components. The exclusion needs no code: `build_dep` emits `dep` from `RefRole.DEPENDENCE` and from nothing else (`DR-SUB-adjudication`, *Entry points*) |
| R3 typed unconsultable diagnostic | S2 output (`FRAME_NOT_SEPARATED` with the shared component in `detail`), plus `test_an_unregistered_endpoint_is_unconsultable_not_silently_fine` → `1 passed` for `FRAME_ENDPOINT_UNREGISTERED` |
| R4 never a manufactured refutation | S3 (structural, exit 0) and S6 (behavioural, five-way equality) |
| R5 scope boundary in SPEC.md | SPEC.md item S4 states it; S4's two accept commands both exit 0, so it also HELD |
| R6 separation HOLDS, exhibited | S5 output — both constructions, including Theorem 7.3's extension |
| R7 violation inert, byte-identical labels | S6 output |
| R8 mutation proof | S7 — two mutations, RED then GREEN, both pasted |
| R9 axiom ledger | S8 table: A6 and A5 PROVED, A1 and A3 PRESERVED, each with its evidence named |
| R10 size / STOP if the plan exceeds ~200 | **Discharged in both halves.** The PLAN was 193, under the threshold. The ACTUAL diff is 312, which tripped `diff_budget.py`'s ceiling; it was raised as a STOP with the line-for-line variance, not absorbed. `superseded-by:R15` as a ceiling |
| R11 frozen surfaces: none | Frozen-surface diff empty; `blast_radius.py` `frozen_surface_verdict: "CLEAR"` at spec time and again at the commit checkpoint, `--against c8071fc34` |
| R12 map moves in the same commits | S10; commit `1da817eaa` carries code, exports and both map documents together |
| R13 gate discipline | Ring 58 passed; full gate 3759 passed / 0 failed; `docs_verify` FULL at baseline |
| R14 delivery R-by-R with pasted proof | DELIVERY.md (`dr-deliver-change`) |
| R15 312 is this tranche's ceiling | Operator, Amendment 1, verbatim: "Proceed at 312 (Recommended)" |
| R16 variance recorded so the ceiling keeps its meaning | The table immediately below |

### R16 — the variance, line for line

    separation.py          82 planned  111 actual  (+29)
    __init__.py             7 planned   14 actual   (+7)
    the four gate tests    82 planned  134 actual  (+52)
    SUB-calculus.md        14 planned   45 actual  (+31)
    CON-standing-...md      8 planned   13 actual   (+5)
    ---------------------------------------------------
    total                 193 planned  312 actual (+119)

What it is NOT: scope growth. The SIZE clause's own diagnostic — "growth here
means Rung 4 work is leaking in" — is CHECKED, twice, and comes back clean (S4).
`src/` ships exactly the seven public names SPEC.md S1/S2 named and not one
more, and `src/` totals 125 insertions against the ladder's own 80–140 estimate
for the whole rung.

What it IS: an estimation error of mine, concentrated in prose density. The
tests overran by 52 lines because each of the four carries a docstring naming
the requirement and the theorem it discharges; the map overran by 36 because
four checks plus two `Traps` entries cost more than the 22 lines I guessed. The
lesson for Rung 4's spec: in this repo a test file's docstrings run roughly
0.6 lines per line of assertion, and a map section with N checks costs ~10N.

## Assumptions carried (operator may override)

| A | Assumption |
|---|---|
| A1 | An unregistered endpoint gets its own typed refusal (`FRAME_ENDPOINT_UNREGISTERED`) rather than a silent `consultable = True`. The literal component reading would report a frame whose subject does not exist as SEPARATED, hence consultable; the precedent for refusing instead is `premises.py::premise_rent_sweep` — "we could not check" must never look like "we checked and it was fine" |
| A2 | `Comp_L(x)` for a node with no incident `att`/`dep` edge is the singleton `{x}`. Definition 7.1 builds `Q_L` from the edge relation and leaves isolated vertices formally undiscussed; the singleton is the only reading on which an empty graph is separated rather than an error |
| A3 | The invariant is stated in the two documents that already cover it rather than in a new `INV-frame-separation.md`, because LADDER §5b assigns the v2 axiom `INV-` document to **Rung 4** |

## Verdict: PASS
