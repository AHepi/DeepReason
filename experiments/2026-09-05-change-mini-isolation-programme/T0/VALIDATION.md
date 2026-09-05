# Validation for: T0 — the prerequisites (S0a, S0b)
Sub-tranche T0 of the mini isolation programme. Phase: `dr-validate-change`.
Base: `1f8108c00a`. Branch: `claude/mini-isolation-t0-t2-upwc47`.

T0 delivers the two things SPEC.md measured DEAD and on which S5–S8 depend:
an operator's own section plugins are read by a run, and a brief composition
can be declared in a file. Without both, the later items would be a code edit
rather than configuration, and C8's enforcement clause could not be satisfied.

## Acceptance checks

**S0a, check 1** — `load_operator_plugins` has a call site under `src/`.

    $ python -c "import subprocess; out = subprocess.run(['grep','-rn',
      'load_operator_plugins','src/','--include=*.py'],capture_output=True,
      text=True).stdout; assert len([l for l in out.splitlines() if l.strip()]) >= 2"
    src/deepreason/llm/seat_sections.py:564:def load_operator_plugins(*, home=None, environ=None):
    src/deepreason/shallow.py:71:    from deepreason.llm.seat_sections import load_operator_plugins
    src/deepreason/shallow.py:73:    loaded, notices = load_operator_plugins(environ=environ)
    ASSERT OK: >= 2 lines

: **PASS**

**S0a, check 2** — the loader's own suite.

    $ python -m pytest tests/test_seat_section_home.py -q
    13 passed in 0.31s

: **PASS** (11 before this tranche, 13 after: the managed-path case and the
raises-on-import case)

**S0b** — a file-declared layout is registered; an unparseable one is refused.

    $ python -m pytest \
        tests/test_seat_section_home.py::test_a_file_declared_layout_is_registered \
        tests/test_seat_section_home.py::test_an_unparseable_layout_file_is_refused_typed -q
    2 passed in 1.91s

: **PASS**

**C4 (SPEC.md S10.3)** — the full harness's two briefs stay byte-identical.

    $ python -m pytest tests/test_conj_pack_legacy_golden.py \
        tests/test_crit_pack_legacy_golden.py -q
    15 passed in 0.38s

: **PASS**

## Full gate

    $ python -m pytest tests/ -q -n 4
    5077 passed, 6 skipped in 1113.62s (0:18:33)

: **PASS** — 0 failed, idle box, not concurrent with `docs_verify`.

    $ python -m pytest mini/tests/ -q
    94 passed, 1 skipped in 4.22s

: **PASS** — 95 collected, 0 failed. Run explicitly: the documented gate
passes `tests/` and so never reaches mini's suite (PARKED P1).

## Record-behavior preservation

**n/a — nothing here reads or validates the append-only record.** S0a writes
one sidecar file (`seat-plugins.json`) into a shallow run root; it appends no
event, registers no object, and touches no digest. `verify_root` enumerates
no root files (`grep -n "iterdir\|glob(" src/deepreason/invariants.py` →
nothing), so an added sidecar is invisible to it. A mini isolation run's
`verify_root` is owned by T6 step 49, where the record actually moves.

## Frozen-surface diff

    $ git diff --stat 1f8108c00a..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/
    (no output)

: **PASS** — empty, as SPEC.md's forecast (`frozen_surface_verdict: CLEAR`)
predicted. `blast_radius.py` agreed at every `[COMMIT]`: no
`frozen_surface_contacts`, no `frozen_adjacent_contacts`, and the one
reachability change (`load_operator_plugins` UNREACHABLE → REACHABLE) is the
row the census marked EXPECTED TO MOVE.

## Map

    docs_verify:            6 failed  : PASS (see below — none is this tranche's)
    docs_verify --audit:    1 finding : PASS (see below)
    docs_verify --links:    0 dangling reference(s), 80 document(s) : PASS
    docs_verify --coverage: 7 seams swept, 21 without a Sweep: header,
                            2 finding(s) : PASS — both name seams this tranche
                            does not touch:
                              SEAM-periphery-x-verification.md: enforcement
                                site not named: src/deepreason/amendment/apply.py
                              SEAM-schools-x-scratch.md: enforcement site not
                                named: src/deepreason/informal/trial.py
    docs_verify --stale:    23 document(s) (was 25)

**The six failures, and why none is owed here.** Four are named on this
window's own known-not-yours list: `SEAM-llm-x-rules.md:54` (an unparseable
check) and `CON-run-identity.md:211/213/215`. The two that are not on that
list by line number were REPRODUCED on the untouched base in this same
container (`git worktree add … 1f8108c00a`):

    base INV-frozen-surfaces.md:206  rc=1   (22 files match; this clone
        carries experiment records the check expects absent)
    INV-frozen-surfaces.md:876       rc=128 on `git show
        origin/claude/deepreason-p-s1-commitments-wowcib:…` — a branch this
        clone does not have

Both are checkout artefacts of this container, not claims that stopped being
true. `--audit`'s single finding is the same `SEAM-llm-x-rules.md:54` row.

**`--stale`, entry by entry.** Two documents were listed against commits from
THIS tranche, and both were repaired in step 8a rather than dismissed:
`SUB-application.md` (owns `shallow.py`) and `SUB-llm.md` (owns `llm/`). The
remaining 23 entries all name commits that pre-date `1f8108c00a` and belong
to other subsystems (`SEAM-scheduler-x-*`, `SUB-evaluation`, `SUB-workflow`,
`SUB-verification`, …); none is this tranche's to advance, and advancing a
stamp whose checks this tranche did not re-run would be a false stamp.

**New checks added by this change** — five, each mutation-proven before being
written down:

| document | claim now checkable |
|---|---|
| `REC-add-a-section-plugin.md` step 2 | a run reads the operator's directory and records both of the loader's lists |
| `REC-add-a-section-plugin.md` step 3 | a `.layout.json` declares a layout; a bad one is refused typed |
| `REC-add-a-section-plugin.md` step 4 | no `Config` field can name a layout, and the env variable is the selector |
| `SUB-application.md` | the shallow path CALLS the loader exactly once, both lists reach the record, and nothing else under `application/` opens that door |
| `SUB-llm.md` | the layout reader imports nothing from the file it reads, and keeps its typed refusal |

**Record observables added vs sweep probes.** One observable:
`seat-plugins.json` in a shallow run root, schema
`deepreason-shallow-seat-plugins.v1`. It is a SIDECAR, not a typed record
entry — no event, no object, no field on any existing schema — so the sweep
reads nothing new and no probe is owed. It is covered instead by the two
tests that read it back from a run
(`test_managed_path_loads_operator_plugins`,
`test_a_plugin_that_raises_on_import_is_a_notice_in_the_record`).

**wheel smoke:**

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas

The packaging surface did not move — no entry point, MCP tool, schema or
wheel-layout change — but the smoke was run anyway because `shallow.py` is
reachable from a console entry point, and a run costs seconds.

## Requirement sweep

T0 is the first of eight sub-tranches. Every R is listed; those another
sub-tranche owns say so, with the item that owns them.

| R | operator's words (short) | disposition after T0 |
|---|---|---|
| R1 | "mini needs to be tested in isolation" | owned by T1 (S1) — not yet |
| R2 | "not limit prose length at all" | owned by T2 (S2) — not yet |
| R3 | "cycles with commitments disabled" | owned by T2 (S3) — not yet |
| R4 | "a new kind of artifact that generates commitments" | owned by T4 (S4) — not yet |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | owned by T3 (S5) — not yet |
| R6 | "conjecturers see everything generated so far" | owned by T3 (S5) — not yet |
| R7 | "all three seats … the same pluggable interface" | **partly demonstrated**: its PREREQUISITES are done — a plugin an operator writes reaches a run (S0a) and a composition is declarable without Python (S0b). The three shells are T3 (S6) |
| R8 | "Don't change the controller just yet" | **honoured**: T0 declares no hook and calls no controller |
| R9 | "the mini flow … adjustable in a pluggable way" | owned by T5 (S8); its file-declared half is done here (S0b) |
| R10 | "add new artifact types on the fly" | owned by T5 (S8); its file-declared half is done here (S0b) |
| R11 | "test this new config in isolation" | owned by T1 (S1) — not yet |
| R12 | "starting input should be standard" | owned by T1 (S1) — not yet |
| R13 | "within mini, criticism can't overturn anything" | **honoured**: T0 builds no elimination road of any kind |
| R14 | "the point is content generation for now" | **honoured**: T0 changes no authority path |
| R-stored | "the current default conjecture form needs stored but not deleted" | owned by T2 (S2); nothing here touches any form |
| R-again | episodes | deferred (window: "episodes (R-again, later)") |
| R-history | one more history conjecture experiment | deferred (operator: "But before that:") |

**C4 held**: the full harness's default behaviour is unchanged and both
existing seats' goldens are byte-identical (15 passed above).

## Assumptions carried

Unchanged from SPEC.md; none is decided or disturbed by T0.

- A1 — "commitments disabled" means BOTH channels (T2 exercises it).
- A2 — "not limit prose length at all" means all three limits.
- A3 — the three seats are conjecturer, critic, commitment.
- A4 — "everything generated so far" means everything in the RUN.
- A5 — "standard" starting input is the frozen `RunInputManifestV2`.
- A6 — "the larger harness" is the eleven modules named in S1. **T1 has
  already measured a problem with this one and will amend it there; T0 does
  not depend on it.**
- A7 — "on the fly" means at run configuration time, not mid-run.
- A8 — "not permanent" is default OFF, registered, removable by configuration.
- A9 — Q-A is not an assumption but an operator ruling (E1 only).

## Verdict: PASS
