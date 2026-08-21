# Parked: what this tranche deliberately did not do

Not defects this tranche introduced. Each is a scope boundary drawn on
purpose, with the reason, and a ready-to-paste prompt for a fresh window —
a follow-up should cost the operator a paste, not an authoring session.

**Part B found no real violation of the seats/evidence law.** All 11 attack
cases in `tests/test_seats_evidence_law.py` pass with no `xfail`, so R16's
"park the finding" branch did not fire. That is stated here explicitly so
the absence of a P-entry reads as a result rather than an omission.

---

## P1 — the V6 launch kill switch: convert it, or confirm it stays

Carried forward unchanged from
`experiments/2026-08-12-change-all-configs-allowed/PARKED.md` P3. This
tranche re-derived it (census row A23: `require_v6_launch_allowed` still
raises) and did NOT convert it, because the operator's instruction for this
window was "no stops" and this one genuinely needs their word rather than
more implementation effort.

> Ask the operator directly, before routing anything. `runtime/launch_policy.py`'s
> `require_v6_launch_allowed` has two `V6_LAUNCH_DISABLED` sources — an
> environment-variable rollback switch, and a central release-policy file
> that can disable ALL v6 launches during an incident. Both are still hard
> errors after the all-configurations law was fully delivered
> (2026-08-16; every other compile-time denial is now a typed notice).
> Two tranches in a row have declined to convert them on their own
> authority, with the same reasoning: an emergency valve that no longer
> stops anything is not "compile-time denial abolished", it is the removal
> of an operational safety valve, and the operator's own list of denial
> categories (family requirements, role conflicts, backend-identity gates,
> ceiling checks, combination restrictions) does not name it. The question
> is one sentence: should an incident kill switch convert to a disclosure
> like everything else, or stay a hard block? If the answer is convert,
> route through `dr-change-orchestrator`; the conversion itself is small
> (one function, two sources, the same `CompileNoticeV1` pattern) — it is
> the DECISION that is not the agent's to make.

## P2 — thread seat-binding resolutions into `compile_notices`

Carried forward from the same tranche's P4. Re-derived here: the three
seat-binding conflicts (`SEAT_BINDING_ROLE_CONFLICT`,
`SEAT_BINDING_GROUP_DUPLICATED`, `SCHOOL_SEAT_DUPLICATED`) are ALREADY
converted — they resolve deterministically and no longer refuse — so they
are not denial sites and were out of Part A's scope. What remains is
notice THREADING, whose blast radius through `preparation.py` no tranche
has measured.

> Route through `dr-change-orchestrator`. The three seat-binding conflicts
> in `src/deepreason/seat_bindings.py` resolve deterministically (a group
> naming its role directly beats one reaching it through an alias; then
> alphabetically-later wins; last-flag-wins for the two flag-parsing
> duplicates) but record no `CompileNoticeV1` anywhere, because
> `deepreason setup`'s seat-binding resolution runs long before any
> `compile_run_manifest` call — it persists a `{group: path}` file that
> `preparation.py` reads at manifest-build time. Goal: carry the resolution
> outcome from `seat_bindings.py` through `preparation.py` into the
> manifest's `compile_notices`, OR land it as a sibling disclosure printed
> at `setup` time if wiring it into the manifest proves too invasive.
> MEASURE THE BLAST RADIUS FIRST and write it into SPEC.md — two tranches
> have now declined this for exactly that reason. End state: a run whose
> seats were resolved by precedence says so in its own record, and
> `tests/test_seat_bindings.py` gains the pin.

## P3 — `_cmd_validate_intake`'s advisory branch is now unreachable

Found while flipping `tests/test_intake_form.py` (this tranche, S7). Not a
defect and not urgent — recorded so the next reader does not mistake the
dead branch for a bug or delete it as dead code.

> Read-only finding, no route needed unless the operator wants it acted on.
> `cli/main.py::_cmd_validate_intake` distinguishes a SEMANTIC violation
> (a typed `CODE:`-prefixed `ValueError` from `IntakeFormV1`'s own
> validators → report and exit 0) from a PARSE/SHAPE error (→ exit 1). That
> split is the 2026-08-12 all-configs-allowed R6 contract and is correct.
> But as of 2026-08-16 both of `IntakeFormV1`'s semantic checks resolve
> IN-MODEL instead of raising — `INTAKE_SEAT_CONFLICT` returns `seats`
> unchanged, `INTAKE_CYCLES_CEILING_EXCEEDED` clamps to the ceiling — so no
> input can currently construct a semantic violation, and the advisory
> branch never executes. The branch must STAY: it is the contract every
> future semantic check inherits. What is missing is a test that would
> notice if it broke, since no real input can exercise it any more. If the
> operator wants it pinned, the cheap version is a unit test over the
> `semantic_only` predicate with a synthetic `CODE:`-shaped `ValueError`;
> the honest alternative is to leave it and rely on the next semantic check
> to re-arm it. Recorded in `tests/test_intake_form.py::
> test_cli_validate_intake_accepts_a_resolved_semantic_input`'s docstring.

## P4 — preflight notices reach stderr, not the run record

Found while converting the two preflight functions (this tranche, S5).
Disclosed rather than fixed, because fixing it properly means choosing a
typed sink inside a live run, which is a design question this tranche's
SPEC did not scope.

> Route through `dr-change-orchestrator`. `preflight_payload` and
> `preflight_harness` now RETURN `tuple[CompileNoticeV1, ...]` instead of
> raising (all-configs-allowed completion, 2026-08-16), and all three
> callers — `cli/main.py`, `application/text_runs.py`,
> `ops.py::run_scheduler` — surface them through
> `run_manifest.report_preflight_notices`, which prints
> `NOTICE <code>: <message>` to stderr. That makes the disclosure VISIBLE
> but it does not make it part of the typed record: the manifest is frozen
> by preflight time, so `compile_notices` cannot take them, and nothing
> writes them to `log.jsonl` or `progress.jsonl`. Under CLAUDE.md's own
> epistemology ("the record is the only admissible evidence"), a disclosure
> that exists only on stderr is not evidence about the run. Goal: give
> preflight disclosures a typed home in the run record — most likely a
> process/diagnostic event appended at run start, carrying the same code,
> message, pointer and resolution — and pin it with a test that reads the
> record, not stdout/stderr. Scope the event shape against
> `DR-SUB-harness`'s event-application rules FIRST; that surface is frozen.
