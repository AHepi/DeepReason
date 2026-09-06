# Validation for: T3 — the mini source adapter and the three shells (S5, S6)
Sub-tranche T3 of the mini isolation programme. Phase: `dr-validate-change`.
Base: `14cc5da495` (main, carrying T2's delivery). Branch: `claude/mini-isolation-t3-t5-7tsc6d`.

T3 makes R5 and R6 real and discharges the third limit of R2: who sees what
in mini is a registered layout walked through the one public road the full
harness's seats share, a critic's brief has no slot a commitment proposal
could fill, and the seats that see everything see it whole.

## Acceptance checks

**S5, accept 1** — the exposure suite.

    $ python -m pytest mini/tests/test_mini_exposure.py -q
    6 passed in 3.76s

: **PASS**

**S5, accept 2** — the layout assertion, verbatim from SPEC.md.

    $ python -c "
    from minireason.flow import resolve_mini_flow
    ...
    "
    ModuleNotFoundError: No module named 'minireason.flow'

: **PASS with one line deferred to T5, and the deferral is the plan's own.**
The assertion's first line resolves `mini.flow.isolation.v1` from a flow
registry that SPEC.md S8 assigns to T5 (CHECKLIST step 39); it cannot run
before that registry exists. The lines that state S5's claim run and pass:

    $ python -c "
    import minireason.seats
    from deepreason.llm.seat_sections import resolve_seat_pack_layout, resolve_seat_shell
    critic = resolve_seat_pack_layout('mini.critic', resolve_seat_shell('mini.critic').layout_id)
    ids = {e.plugin_id for e in critic.entries}
    assert not any('commitment' in i for i in ids), ids
    "
    OK ['mini.directive', 'mini.problem', 'mini.target-conjecture']

T5's validation re-runs the assertion whole.

**S5, accept 3** — a rendered critic brief over a run containing commitment
proposals contains NONE of their bytes.

    $ python -m pytest mini/tests/test_mini_exposure.py::test_critic_brief_carries_no_proposal_bytes -q
    1 passed in 1.51s

: **PASS**. A byte assertion over a live root: two standing conjectures, two
refuted, three planted proposals with sentinel bodies. Not one body, sentinel
or proposal id reaches the critic's brief; its target is there whole. The
companion test proves the structural half — every critic receipt is a
`rendered` section, none an absent slot. Mutation-proven at step 28: a critic
layout given the everything section turns both red.

**S6, accept 1 (C4)** — the full harness's two briefs stay byte-identical.

    $ python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q
    15 passed in 0.44s

: **PASS**

**S6, accept 2** — the form each seat fills is its shell's, verbatim.

    $ python -c "
    from minireason.seats import form_for_seat
    from deepreason.llm.seat_sections import resolve_seat_shell
    for seat in ('mini.conjecturer','mini.critic','mini.commitment'):
        assert form_for_seat(seat).form_id == resolve_seat_shell(seat).form_id
    "
    OK

: **PASS**. `SeatShellV1.form_id` has its first consumer; PARKED P3's full
harness half stays parked.

**S6, accept 3** — the shell suite.

    $ python -m pytest mini/tests/test_mini_seat_shell.py -q
    6 passed in 1.13s

: **PASS**. Includes the two-halves test: binding the critic's shell in the
conjecturer's seat changes both the brief rendered and the form asked for.

**The sources suite (step 24-26's own checks, not in SPEC.md's accept list
but load-bearing for S5):**

    $ python -m pytest mini/tests/test_mini_sources.py -q
    8 passed

: **PASS** — the before-state (the dict view cannot feed the plugins), the
adapter, writes-nothing (log bytes, next seq, digest, replay digest,
`verify_root` unchanged), frozen criteria only from the standard input,
everything shown whole (twelve ~700-char conjectures), the retention rule
withholding oldest-first and naming what it withheld, recency needing its
window, and the AST assertion that no mini source reads a status.

## Full gate

    $ python -m pytest tests/ -q -n 4
    5084 passed, 6 skipped in 1411.00s (0:23:31)     -> 0 failed
    $ python -m pytest mini/tests/ -q
    136 passed, 1 skipped in 9.45s                    -> 0 failed

: **PASS**. The full gate is UNCHANGED from T2 (5084), which is expected
rather than a coincidence: `git diff --stat 14cc5da495 -- src/` is one file,
29 insertions, the public entry nothing under `tests/` exercises differently.
Mini's ring went 116 → 136.

## Record-behavior preservation

T3 changes no reader or validator of the append-only record, so the
`verify_root` spot-check over committed roots is not owed. What it does add is
a READER of a live root's state — the source adapter — and that reader is held
to the never-append clause with measurements rather than a promise:

- `test_the_adapter_writes_nothing`: after two requests and two walks,
  `log.jsonl`'s bytes, `harness._next_seq`, `state.digest()`,
  `replay(root).digest()` and `verify_root(root)["violations"] == []` are all
  unchanged.
- `test_rendering_every_brief_appends_nothing`: all three seats' briefs
  rendered over the planted root; digest, seq and `verify_root` unchanged.

## Frozen-surface diff

    $ git diff --stat 14cc5da495..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (no output)
    $ git diff --stat 14cc5da495..HEAD -- src/
     src/deepreason/llm/packs.py | 29 +++++++++++++++++++++++++++++
     1 file changed, 29 insertions(+)

: **PASS** — empty, and the second line bounds the whole of T3's reach into
`src/`. `tools/blast_radius.py` at every `[COMMIT]` step: `CLEAR`, no
contacts, no adjacent contacts, `qualification_digest: []`,
`wheel_smoke_pins: []`. No reachability drift: the two public entries went
`UNKNOWN -> UNREACHABLE` at step 25 (new symbols, no consumer yet) and every
mini symbol reads `UNKNOWN -> UNKNOWN` because its consumers live in
`mini/tests/`, the census blind spot PARKED P1 records.

## Packaging surface

packaging surface untouched — smoke not owed. T3 changed no entry point, no
CLI flag, no MCP tool, no schema and no wheel layout; its one `src/` change
adds two functions to a module the smokes do not pin.

## Map

    docs_verify:            6 failed  : PASS (the same six as T0-T2; INV-frozen-surfaces'
                                        rows are the window's :181/:736, shifted)
    docs_verify --audit:    1 finding : PASS (the known SEAM-llm-x-rules.md:54)
    docs_verify --links:    0 dangling, 82 document(s) : PASS (81 -> 82)
    docs_verify --coverage: 2 findings, 22 seams without a Sweep header : PASS —
                            both findings on seams T3 did not touch
                            (periphery x verification; schools x scratch);
                            the new seam states why it carries no header
    docs_verify --stale:    22 documents, none of them this tranche's after the
                            six re-derived stamps advanced to f8100b9b0

**One failure this tranche CAUSED, fixed in the same commit that caused it**
(step 25): `CON-packs-and-token-economy.md:293` pinned "only two renderers are
on the IR" by counting callers of `_allocate_sections`, and `allocate_seat_brief`
was a third the moment it existed. Moved with the code, not deleted: the claim
names the public entry and pins all three callers.

**New checks added by this change** — eleven, in the same commits as the code
they describe:

| document | claim now checkable |
|---|---|
| `SEAM-llm-x-minireason.md` (new) | fifty crossings one way, none back, resolved on the AST |
| `SEAM-llm-x-minireason.md` | mini renders through the public road only (the AST test) |
| `SEAM-llm-x-minireason.md` | binding another shell changes both what is shown and what is asked; goldens unmoved |
| `SEAM-llm-x-minireason.md` | every mini form is a `WireContract`, the stored one the shipped instance, and no `mini.` id in the V6 Literal |
| `SEAM-llm-x-minireason.md` | mini's call verifies the lease and clips at the profile |
| `INV-seat-section-plugins.md` | each public entry is one call to its private counterpart |
| `INV-seat-section-plugins.md` | `form_id` has a consumer, and it reads the shell |
| `SUB-minireason.md` | the critic layout is exactly problem · target · directive, every mini entry mandatory |
| `SUB-minireason.md` | everything shown whole; the retention rules (the sources suite) |
| `SUB-minireason.md` | each seat's shell is the registered one, its form the shell's, the two full-harness shells unchanged |
| `CON-packs-and-token-economy.md` | the three callers of the allocator, by name |

Each was shown red under a mutation before it was written down (steps 28
and 29 carry the pastes); `--audit` flags none as vacuous.

**Record observables added vs sweep probes.** None. T3 writes nothing to any
record: the adapter and the plugins read, the receipts return to the caller,
and the retention notice lives in the brief the call layer blobs as the
prompt. The one recorded thing a mini run will gain — the brief itself, as
`prompt_ref` — is an existing observable.

## Requirement sweep

| R | operator's words (short) | disposition after T3 |
|---|---|---|
| R1 | "mini needs to be tested in isolation" | **done** in T1; the fence re-run at every T3 step that added a module (3 passed) |
| R2 | "mini artifact forms need to not limit prose length at all" | **done for all three limits on the shell road.** Field bounds and the skeleton went in T2; the truncation of what a seat is SHOWN goes here — `mini.everything-so-far` renders every artifact whole (twelve ~700-char conjectures where the legacy loop showed 8 at 300 chars). ONE silent limit remains, one layer down, and is named rather than hidden: mini's call layer clips every prompt at the profile's pack budget (PARKED P8, binding on T5) |
| R3 | "cycles with commitments disabled" | **done** in T2 |
| R4 | "a new kind of artifact that generates commitments" | its form (T2) and its SHELL and LAYOUT ship here (`seat.mini.commitment.v0`); the seat's writer is T4 (S4) |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | **done** — structural: the critic layout registers no section that could carry a proposal; byte-asserted over a live root with planted proposals; mutation-proven |
| R6 | "conjecturers see everything generated so far and so do commitment artifacts" | **done** — both layouts carry `mini.everything-so-far`; every proposal and every conjecture, standing and refuted, shown whole with no status; what stays visible as the pool grows is a registered rule with a disclosed withheld notice, never a verdict |
| R7 | "all three seats … the same pluggable interface with relaxed forms" | **the interface half done**: three shells through one public road, each seat's form resolved through its shell; the "calibrated on the fly and modifiable by the controller" half is T4's declared hook (S7) |
| R8 | "Don't change the controller just yet" | **honoured** — no hook, no controller call in T3 |
| R9 | "the mini flow … adjustable in a pluggable way" | the seat side is now configuration (layouts as data, directives as layout params, file-declared layouts through T0's road); the flow is T5 |
| R10 | "add new artifact types on the fly" | a new type's form (T2), layout and shell are registrations now; the flow stage is T5 |
| R11 | "test this new config in isolation" | **done** in T1 |
| R12 | "starting input should be standard" | **done** in T1; here the standard input's criteria reach every mini brief through `mini.problem` |
| R13 | "within mini, criticism can't overturn anything" | **honoured, and enforced one layer further**: no mini source reads a status (AST), no mini brief renders a label (bytes), the critic's directive says "it overturns nothing" |
| R14 | "the point is content generation for now" | **honoured** — no authority path changed; `src/` diff is the public entry alone |
| R-stored | "the current default conjecture form … stored but not deleted" | **done** in T2; here it is one selection away from any mini seat (`DEEPREASON_MINI_FORM`, or a shell naming it) |
| R-again | episodes | deferred (window: "episodes (R-again, later)") |
| R-history | one more history experiment | deferred (operator: "But before that:") |

## Assumptions carried

- **A2 — "not limit prose length at all" means all three limits: DISCHARGED
  on the shell road, with one residue named.** The third limit is gone from
  what the shells render. The call layer's profile clip is a fourth the
  design did not see; it is parked (P8) with a binding note for T5, not
  absorbed and not hidden.
- **A4 — "everything generated so far" means everything in the RUN:
  EXERCISED.** `mini.everything-so-far` walks the whole record's artifact
  map, not one problem's; a future multi-problem flow narrows it by
  parameter.
- A1, A3, A5, A6 (amended in T1), A7, A8 — carried unchanged. A9 is the
  operator's ruling, not an assumption.
- **One decision taken without asking, dominant under the operator's
  recorded values (`dr-ask-the-right-question` §4):** retention rules ship
  as `everything` (default) and `recency`; "novelty by the equivalence
  tiers", the ruling's other example, is a registration when wanted, not
  built here — building it would be machinery no generated evidence has
  asked for yet ("tokens are cheap; the agent is not").

## Budget

**EXCEEDED and re-baselined, not absorbed.** 636 insertions against 240,
itemised per file in SPEC.md §Budget with code separated from docstring
(`sources.py` 384 = 223 code / 63 docstring / 21 comment / 77 blank;
`seats.py` 223 = 129 / 47 / 14 / 33; `packs.py` 29). Trimmed before
disclosing (566 → 550 at step 26). The cause PARKED P7 names, plus one
specific to T3: the retention-as-a-rule ruling arrived after SPEC.md's numbers
were written. T3 restated as ~640; programme ~2 100.

## Verdict: PASS
