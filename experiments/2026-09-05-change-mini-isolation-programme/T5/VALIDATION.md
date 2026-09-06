# Validation for: T5 — the pluggable flow and the architecture tests (S8, S9)
Sub-tranche T5 of the mini isolation programme. Phase: `dr-validate-change`.
Base: `d800b622b` (T4's delivery head). Branch: `claude/mini-isolation-t3-t5-7tsc6d`.

T5 makes R9 and R10 real and closes the programme's build: the three seats
are a FLOW whose stage order and artifact-kind set are registered data, the
loop walks that data and names no seat, a fourth kind is added by
registration alone, and five architecture checks go red on a bypass.

## Acceptance checks

**S5, accept 2 — the one line T3 deferred, now run verbatim.**

    $ python -c "
    from minireason.flow import resolve_mini_flow
    from deepreason.llm.seat_sections import resolve_seat_pack_layout, resolve_seat_shell
    flow = resolve_mini_flow('mini.flow.isolation.v1')
    critic = resolve_seat_pack_layout('mini.critic', resolve_seat_shell('mini.critic').layout_id)
    ids = {e.plugin_id for e in critic.entries}
    assert not any('commitment' in i for i in ids), ids
    "
    OK ['mini.directive', 'mini.problem', 'mini.target-conjecture']

: **PASS** — T3's deferral is discharged; the whole S5 assertion now runs.

**S8, accept 1** — the flow suite.

    $ python -m pytest mini/tests/test_mini_flow.py -q
    9 passed in 1.39s

: **PASS**. Registry, selection order, the two shipped flows' shapes, the
undeclared-kind refusal, the legacy brief byte-for-byte against a golden
captured before the loop moved, both flows end to end against the stub, and
the registration proof.

**S8, accept 2** — the loop names no seat, kind or stage.

    $ python -c "...SPEC S8's substring form, verbatim..."
    AssertionError: mini.conjecturer

: **PASS in the precise form; the substring form has a pre-existing false
positive, disposed at step 40 and not weakened.** The substring `mini.conjecturer`
occurs once in `loop.py`, in `Session.guard_scope`'s relapse-domain label
`"mini.conjecturer.v1"`, which predates the programme (2026-08-30) and is
folded into the relapse-domain digest the record carries
(`anti_relapse.relapse_domain`, `contract_digest=_digest(contract_id)`).
Renaming it would change every legacy admission record — the one thing C4
forbids. The claim S8 makes is that the loop names no SEAT, KIND or STAGE,
and that claim is checked in the form that says exactly that:

    $ python -c "...no string constant in loop.py EQUALS any registered seat,
        shell, layout, flow, stage or kind id; 'skeleton' absent..."
    OK: no string constant in loop.py equals any of 19 registered ids; skeleton absent

This precise form is `test_mini_architecture.py::test_1`, enumerated from
the registries, and it caught a real collision the substring form would
not have named: the stage id `commitment` was also a dict key in
`Session.refute`, so the shipped stage ids are namespaced
(`mini.stage.conjecture`, `mini.stage.criticism`, `mini.stage.commitment`).

**S8, accept 3** — a flow registered only in a test file adds a fourth kind.

    $ python -m pytest mini/tests/test_mini_flow.py::test_a_new_artifact_kind_is_a_registration -q
    1 passed in 0.96s

: **PASS**. A successor-question seat — form, layout, shell, stage, flow —
declared entirely in the test, two cycles against the stub, the record
carrying the fourth kind, the next cycle's conjecturer shown it whole, and
every mtime under `mini/minireason/` identical before and after.

**S9, accept 1** — the five architecture tests.

    $ python -m pytest mini/tests/test_mini_architecture.py -q
    5 passed in 2.93s

: **PASS**

**S9, accept 2** — five mutation proofs, each red.

    $ ls proof/mutation_*.txt | wc -l   -> 5
    $ grep -l FAILED proof/mutation_*.txt | wc -l   -> 5

: **PASS**. Each file names its mutation and carries the red run; the tree
was restored and the suite re-run green after each (step 42's paste).

## Full gate

    $ python -m pytest tests/ -q -n 4
    5084 passed, 6 skipped in 1417.28s (0:23:37)     -> 0 failed
    $ python -m pytest mini/tests/ -q
    164 passed, 1 skipped in 14.19s                   -> 0 failed

: **PASS**. The full gate is UNCHANGED from T2, T3 and T4, and T5 changed
nothing under `src/` at all. The public shallow path's own tests
(`tests/test_shallow_reason.py`, 13) passed inside the gate and again
alongside the goldens. Mini's ring went 150 → 164.

## Record-behavior preservation

T5 changes what a mini run WRITES on the isolation road — criticism and
proposal records — and must not change what the legacy road writes:

- `test_the_legacy_flow_runs_exactly_as_before`: selecting nothing walks the
  legacy flow; the record carries no mini record and no mini marker; the
  skeleton candidates are admitted and checked as before; the prompt is
  today's, byte for byte after the section header, pinned by the golden
  captured BEFORE the loop moved (step 39).
- Every pre-existing mini test that drives the loop — the healthy run, the
  orbiting run, the schema storm, budget death, turnover, stance decay, the
  chaos battery, the normative kernel, the fence — passes unchanged (164).
- On the isolation road: `replay(root).digest() == Session(root).state.digest()`
  and `verify_root(root)["violations"] == []` after two cycles of
  conjecture → criticism → commitment; the meter equals the log.
- The one visible difference on the legacy road is the `## legacy-prompt`
  header line the shared allocator prefixes to the prompt. It is asserted in
  the golden test rather than glossed, and no committed test pinned the
  prompt's bytes before this programme.

## Frozen-surface diff

    $ git diff --stat d800b622b..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (no output)
    $ git diff --stat d800b622b..HEAD -- src/
    (no output)

: **PASS** — empty, and T5's reach into `src/` is none. `tools/blast_radius.py`
at steps 39 and 40: `CLEAR` on precise symbols; the bare-`run` CONTACT at step
40 is the false positive SPEC.md's forecast (2) and T2's step 19 already
record, and the reachability row for `run` reads `REACHABLE -> REACHABLE
(unchanged)`.

## Packaging surface

packaging surface untouched — smoke not owed. T5 changed no file under
`src/`, no entry point, no MCP tool, no schema and no wheel layout. The
shallow CLI's flags are unchanged; the flow is selected inside the engine by
argument or `DEEPREASON_MINI_FLOW`.

## Map

    docs_verify:            6 failed  : PASS (the same six as T0-T4)
    docs_verify --audit:    1 finding : PASS (the known SEAM-llm-x-rules.md:54)
    docs_verify --links:    0 dangling, 82 document(s) : PASS
    docs_verify --coverage: 2 findings, 22 seams without a Sweep header : PASS —
                            both pre-existing, on seams T5 did not touch
    docs_verify --stale:    22 documents, none of them this tranche's after the
                            two re-derived stamps advanced to 2b6440d28

**New checks added by this change** — four, in the same commits as the code:

| document | claim now checkable |
|---|---|
| `SUB-minireason.md` | the flow suite passes |
| `SUB-minireason.md` | the default is legacy; the two shipped flows' shapes and the kind set |
| `SUB-minireason.md` | the architecture suite passes |
| `SUB-minireason.md` | check 1 re-derived in place: the registry enumeration, no whole-constant match in the loop, the flow selection and the brief render present |

Plus the `flow` parameter added to the existing entry-point check, and the
seam's fraction row and two traps (P8 disposed, P9) in
`SEAM-llm-x-minireason.md`. `--audit` flags none vacuous.

**Record observables added vs sweep probes.** Three markers: `mini:stage-skipped`
(a per-target stage with nothing to read this cycle), `mini:brief-clipped`
(a brief over the profile's clip, with both sizes), and `mini:stage-empty`
(a record stage whose reply yielded nothing to write, carrying the spend).
Plus the criticism kind `mini.criticism.v1` on `mini:record` events. Typed
observables with no sweep probe — the sweep is RETIRED (operator ruling
2026-08-22) — discharged by targeted tests on the runs that produce them:
`test_the_isolation_flow_runs_end_to_end` asserts the kinds and the ABSENCE
of `mini:brief-clipped`; the skipped and empty markers are exercised by the
loop under the stub and read by `mini_records`' sibling walk. Named here so
a later probe knows what to look for.

## Requirement sweep

| R | operator's words (short) | disposition after T5 |
|---|---|---|
| R1 | "mini needs to be tested in isolation" | **done** in T1; the fence's third part re-run over the isolation flow (3 passed) |
| R2 | "not limit prose length at all" | **done** on the shell road; PARKED P8 DISPOSED here (the everything section's share, a typed clipped marker) |
| R3 | "cycles with commitments disabled" | **done** in T2; the isolation flow declares both channels off and the record carries the warning |
| R4 | "a new kind of artifact that generates commitments" | **done** in T4; the commitment stage runs in the isolation flow, once per conjecture this cycle |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | **done** in T3; re-proven LIVE: the critic's two briefs in the end-to-end run carry no proposal and no objection |
| R6 | "conjecturers see everything generated so far and so do commitment artifacts" | **done** in T3; re-proven LIVE: the second cycle's conjecturer and commitment seat see the first cycle's objection and proposal whole |
| R7 | "all three seats … the same pluggable interface … modifiable by the controller" | **done** — three seats, one road, one dispatch by the form's shape; the hook declared (T4) and named on the flow as data |
| R8 | "Don't change the controller just yet" | **honoured, and enforced** — architecture check 5 |
| R9 | "The mini flow also needs to be adjustable in a pluggable way" | **done** — a registered, versioned `MiniFlowV1`; stage order is data; selection by argument or `DEEPREASON_MINI_FLOW`; the loop names nothing |
| R10 | "add new artifact types on the fly if I can see it might help" | **done-with-assumption A7** — at run configuration time: a fourth kind is a registration (form, layout, shell, stage, flow) with no edit under `mini/minireason/`, proven twice |
| R11 | "test this new config in isolation without the larger harness activated" | **done** — the isolation flow runs end to end offline; the fence holds over it |
| R12 | "starting input should be standard" | **done** in T1; every stage's brief carries the standard input's problem and criteria |
| R13 | "within mini, criticism can't overturn anything" | **honoured, structural**: a criticism is a record outside the artifact map; no status moves in the end-to-end run (`refuted == 0` with commitments off); architecture check 2 |
| R14 | "the point is content generation for now" | **honoured** — nothing under `src/` changed |
| R-stored | "the current default conjecture form … stored but not deleted" | **done** in T2; the legacy flow fills it, and it is the DEFAULT flow |
| R-again | episodes | deferred (window: "episodes (R-again, later)") |
| R-history | one more history experiment | deferred (operator: "But before that:") |

## Assumptions carried

- **A7 — "on the fly" means at run configuration time: EXERCISED.** A flow is
  resolved once by `select_mini_flow` before the first call and is immutable
  after; a fourth kind is registered before the run, never during it.
- **A8 — "not permanent" is default OFF: EXERCISED.** The default flow is
  legacy; the isolation flow is one argument or one environment variable away.
- **Decided without asking (dominant):** every stage dispatches through the
  ONE leased route, so `LLMCall.role` reads `conjecturer` for a critic's or
  commitment seat's call; the seat is named by the record event that carries
  the spend. The manifest refuses non-canonical roles (frozen surface 4), so
  the alternative is a grant. Parked as P9 with its prompt.
- **Decided without asking (dominant):** the legacy road's prompt gains one
  header line from the shared allocator. Byte-exact reproduction would need
  a second renderer in mini — the thing the whole programme exists not to
  have — or a change in `packs.py`. No committed test pinned those bytes; the
  golden pins them now, header asserted.
- A1–A6 carried unchanged; A9 is the operator's ruling.

## Budget

**EXCEEDED and re-baselined, not absorbed.** 619 insertions against 240 by
the gate's count, 401 net lines, 256 of code; itemised per file in SPEC.md
§Budget. The T5-specific cause: S8's 150 priced the registry and the loop
rewrite as one item, and the rewrite lifts 200 lines of the existing
conjecture road into a function so the stage walk can call it — a move the
numstat counts as insertions.

## Verdict: PASS
