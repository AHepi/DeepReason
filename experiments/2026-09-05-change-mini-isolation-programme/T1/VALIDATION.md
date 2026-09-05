# Validation for: T1 — isolation, the standard input, the fence (S1, S11a)
Sub-tranche T1 of the mini isolation programme. Phase: `dr-validate-change`.
Base: `d319f2d6c` (T0's delivery head). Branch: `claude/mini-isolation-t0-t2-upwc47`.

T1 does two things: it lets a mini run start from the STANDARD frozen input
(R12), and it turns "in isolation" from a claim into a test (R1, R11). It also
creates the first map document for `mini/minireason/` (S11a), which had none.

## Acceptance checks

**S1, accept 1** — the fence passes, and each part fails under a mutation
proven in the same commit.

    $ python -m pytest mini/tests/test_isolation_fence.py -q
    3 passed in 2.55s

`proof/fence_mutation.txt` carries the three mutations, each red, then green
again with a clean `git status`:

    MUTATION 1  a mini module imports deepreason.scheduler
      -> mini imports the larger harness directly:
         mini/minireason/rotate.py:1: deepreason.scheduler
    MUTATION 2  the eager text-run import returns
      -> importing mini pulls in fenced packages the record modules do not:
         ['deepreason.application.text_runs']
    MUTATION 3  a lazy `import deepreason.qualification` inside loop.run
      -> a mini run imported the larger harness while running:
         ['deepreason.qualification']
         Parts 1 and 2 BOTH pass under this mutation. That is why part 3 exists.

: **PASS**

**S1, accept 2** — the shallow surface.

    $ python -m pytest tests/test_shallow_reason.py -q
    13 passed in 0.51s

: **PASS** (6 before this tranche, 13 after)

**S1, accept 3 (added by the amendment)** — ARM C empty.

    $ python experiments/.../proof/fence_measure.py
    ARM C  what MINI adds beyond ARM A: []

: **PASS**

**S11a** — the map document's own checks.

    $ python tools/docs_verify.py --links
    0 dangling reference(s), 81 document(s)      (was 80)

Every one of `SUB-minireason.md`'s eleven checks was run by hand before being
written down (11/11 rc=0), and `--audit` flags none of them as vacuous.

: **PASS**

**C4 (SPEC.md S10.3)** — the full harness's two briefs stay byte-identical.

    $ python -m pytest tests/test_conj_pack_legacy_golden.py \
        tests/test_crit_pack_legacy_golden.py -q
    15 passed in 0.37s

: **PASS**

## Full gate

    $ python -m pytest tests/ -q -n 4
    5084 passed, 6 skipped in 1287.99s (0:21:27)      -> 0 failed
    $ python -m pytest mini/tests/ -q
    101 passed, 1 skipped in 5.78s                    -> 0 failed

: **PASS**. 5077 → 5084 (step 11's seven `--run-input` cases); 95 → 101 (the
three fence parts and the three frozen-input cases in `test_compat.py`).
Nothing weakened.

## Record-behavior preservation

**The record moves in T1, and the check is that it moves only where specified.**
A mini root binds one run input, and T1 adds a second legal kind. What is
proven:

- The constant process root is byte-identical when no frozen input is given —
  `mini/tests/test_compat.py::test_no_supplied_input_still_binds_the_constant_process_root`
  compares `manifest.run_input_digest` against `mini_run_input()`'s own digest.
- A supplied frozen input binds THAT record, and the manifest's
  `run_input_digest` is the frozen record's — same file,
  `::test_a_supplied_frozen_input_is_bound_instead_of_the_process_root`.
- Reopening a root against a different frozen input is refused typed
  (`MINI_ROOT_RUN_INPUT_MISMATCH`), while rebinding the same one still works,
  because that is the crash-recovery path.
- Mini's replay invariant is untouched: `mini/tests/test_loop.py::
  test_healthy_run_no_orbit_and_replayable` still asserts `replay(root).digest()
  == Session(root).state.digest()` and passes.

`verify_root` over a mini isolation run is owned by T6 step 49, where the
programme's own checklist places it.

## Frozen-surface diff

    $ git diff --stat d319f2d6c..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/
    (no output)

: **PASS** — empty. `blast_radius.py` agreed at both code commits: no
`frozen_surface_contacts`, no `frozen_adjacent_contacts`, no unpredicted
reachability change.

## Map

    docs_verify:            6 failed  : PASS (the same six as T0, all pre-existing)
    docs_verify --audit:    1 finding : PASS (the same known SEAM-llm-x-rules.md:54)
    docs_verify --links:    0 dangling, 81 document(s) : PASS
    docs_verify --stale:    23 document(s), none of them this tranche's

`--stale` listed `SUB-application.md` during this validation, against two
commits from this tranche. That was repaired in **step 14a** rather than
dismissed — the second time in this programme that map work was scoped to the
one document a checklist step named while other steps changed files a
different document owns. Recorded as a finding in the checklist.

**New checks added by this change** — thirteen:

| document | checks | claim |
|---|---|---|
| `SUB-minireason.md` (new) | 11 | mini's size, its entry-point signatures, that its `State` recomputes nothing, the transactional-only fields, the two starting inputs, the fence, that `Session.refute` never labels a status, the where-to-change ring, and three Traps written to go RED WHEN FIXED |
| `INDEX.md` | 1 | exactly one engine directory outside `src/deepreason/` is claimed by the map |
| `SUB-application.md` | 1 | the eager text-run import has not returned, and the lazy accessor is still there |

**Record observables added vs sweep probes.** One: the result payload's
`run_input` block (`source`, `problem_id`, `run_input_digest`, `criteria`,
`notices`). It is a RESULT field, not a typed record entry — no event, no
object, no field on any existing schema — so the sweep reads nothing new and no
probe is owed. Three tests read it back from a run instead. The frozen
`RunInputManifestV2` itself is not a new observable: it is the record the full
harness already binds, now bound by mini too, and `verify_run_input` already
covers it.

**wheel smoke:**

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas

Run because T1 DOES move the public CLI surface (`--run-input`, and `question`
made optional). No pinned expectation moved — the smoke pins console entry
points, the MCP tool set and schema shas, and the wheel layout, none of which a
new argument on an existing verb changes — so no pin was updated.

## Requirement sweep

| R | operator's words (short) | disposition after T1 |
|---|---|---|
| R1 | "mini needs to be tested in isolation" | **done** — the fence is three tests, each mutation-proven (VALIDATION S1 accept 1) |
| R2 | "not limit prose length at all" | owned by T2 (S2) — next |
| R3 | "cycles with commitments disabled" | owned by T2 (S3) — next |
| R4 | "a new kind of artifact that generates commitments" | owned by T4 (S4) |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | owned by T3 (S5) |
| R6 | "conjecturers see everything generated so far" | owned by T3 (S5) |
| R7 | "all three seats … the same pluggable interface" | prerequisites done in T0; the shells are T3 (S6) |
| R8 | "Don't change the controller just yet" | **honoured** — no hook declared, no controller called |
| R9 | "the mini flow … adjustable in a pluggable way" | file-declared half done in T0; the flow is T5 (S8) |
| R10 | "add new artifact types on the fly" | file-declared half done in T0; the rest is T5 (S8) |
| R11 | "test this new config in isolation without the larger harness activated" | **done-with-amendment** — the fence proves mini reaches for nothing in the larger harness and adds nothing to the record modules' own closure. It does NOT prove no code in the four transitively-loaded packages executes; SPEC.md §S1 says so, and so does the test's docstring |
| R12 | "starting input should be standard" | **done** — `--shallow --run-input ROOT` takes the `RunInputManifestV2` that `deepreason input freeze` writes and the full harness takes (VALIDATION S1 accept 2) |
| R13 | "within mini, criticism can't overturn anything" | **honoured** — T1 builds no elimination road |
| R14 | "the point is content generation for now" | **honoured** — no authority path changed |
| R-stored | "the current default conjecture form … stored but not deleted" | owned by T2 (S2); nothing in T1 touches any form |
| R-again | episodes | deferred (window: "episodes (R-again, later)") |
| R-history | one more history experiment | deferred (operator: "But before that:") |

## Assumptions carried

- A1–A5, A7, A8 — unchanged, none decided by T1.
- **A6 — AMENDED during this sub-tranche, before step 10 ran.** The eleven
  modules stand as the list of what mini must not USE, but the fence measures
  three things that can be true rather than one that cannot. See SPEC.md §S1
  and §A6, and `proof/fence_arms.txt`.
- A9 — Q-A is an operator ruling (E1 only), not an assumption.

## Budget

**EXCEEDED and re-baselined, not absorbed.** 218 insertions against a ceiling
of 170, measured from T0's delivery head, before `SUB-minireason.md`. SPEC.md
§Budget now carries the per-file itemisation and the reason: S1 priced
accepting the flag, not the three disclosure-and-refusal obligations standing
laws attach to it (~110 lines), and 17 further lines are the S1 amendment's own
consequence and were priced at nothing. T1 is restated at ~300; the programme
total moves 1 320 → ~1 450. No later sub-tranche number is touched.

## Verdict: PASS
