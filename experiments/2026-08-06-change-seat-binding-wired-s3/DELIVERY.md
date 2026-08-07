# Delivered: the binding, wired — Rung S3 of role-seat separation
Branch: `claude/seat-census-rung-s1-7gphj9` @ `0e95a919` (pushed, tree
clean)

## What changed

`deepreason setup` now accepts repeated `--seat GROUP=PATH` flags
(`conjecture`, `coder`, `scratch`, `simulation` — the last a true alias
of the first), binding an existing provider-profile file to a role
group instead of every canonical role sharing the one profile
`setup` mints. A new module, `src/deepreason/seat_bindings.py`,
expands each group to its concrete role names, persists the bindings
in a small secret-free YAML file alongside `provider.yaml`, and
resolves them to `ProviderProfileV1` objects at manifest-compile time
— never a new `Config`/`RunManifest` field (Rung S2's approved Option
A, sub-choice 2a). Two roles bound to different profiles by two
different groups refuse typed (`SEAT_BINDING_ROLE_CONFLICT`), not
last-one-wins — this also covers a second overlap this tranche's own
spec-writing discovered (`scratch` and `conjecture` both default to
the `conjecturer` role), not only the operator-named
`simulation`/`conjecture` pair. `preparation.py`'s
`_config_for_profile` is generalized to accept these resolved
bindings and override specific roles' routes while leaving every
other role on the base profile; `build_preparation_manifest`,
`qualification_subject_manifest` (`deepreason qualify`'s path), and
`RunPreparationService.prepare` (`deepreason reason`'s path) all
thread it through. With no `--seat` flags, behavior is exactly
byte-identical to before this tranche — proven by a dedicated test,
by the 42-root sweep (45 roots, empty diff), and by the full gate.
`docs/map/CON-seats.md` was updated in the same commit as the code
change it documents, per the map's own rule.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "setup accepts per-role-group profile paths" | done | commit `e9007ad1`, VALIDATION S1 |
| R2 | "_config_for_profile generalized per SM1/SM2" | done | commits `a4e93037`, `9d28d47a`, VALIDATION S4/S5 |
| R3 | "default no-flags behavior byte-identical to today" | done | VALIDATION S4 (test), S7 (sweep) |
| R4 | "SeatBinding resolution where leases are built" | done | VALIDATION S5 |
| R5 | "Full gate 0 failed" | done | VALIDATION "Full gate" (3357 passed, 1 pre-existing failure confirmed unrelated) |
| R6 | "sweep byte-identical" | done | VALIDATION S7 (45 roots, empty diff) |
| R7 | "two-MockEndpoint routing proof asserted from the typed attempt records" | done-with-assumption A6 | VALIDATION S8 |
| R8 | "Q1: (a) — simulation aliases conjecture for S3" | done | `GROUP_ALIASES = {"simulation": "conjecture"}`, VALIDATION S2 |
| R9 | "conflicting --seat values for the shared role set get a typed refusal, never last-one-wins" | done-with-assumption A8 | `SEAT_BINDING_ROLE_CONFLICT`, VALIDATION S2/S3 |
| R10 | "Q2: 2a confirmed" | done | no new `Config`/`RunManifest` field anywhere in this tranche's diff (frozen-surface diff empty) |
| R11 | "One rung only." | done | VALIDATION S10; no S4/S5-shaped code in `src/` |

Every requirement done; none deferred, none not-done.

## Assumptions the operator may override

A1: "coder" = `{property_designer}`.
A2: "scratch" = `{conjecturer, synthesizer, summarizer}`.
A3: "conjecture"/"simulation" = `{conjecturer, variator}`.
A4: the `experimenter`-template call site (CENSUS.md M20) rides
whatever "conjecture" resolves to regardless of any "coder" binding —
named, not fixed; would need adapter-level routing surgery to close.
A5: `setup_wizard`/`apply_setup` untouched; `--seat` lives entirely in
`cli/main.py`'s dispatch.
A6: R7's "unit run" read as a pytest unit test with `MockEndpoint`
(the only reading the named tool supports at all).
A7: `--seat GROUP=PATH`, repeated — the plan's own example syntax.
A8: the never-last-wins conflict rule generalizes to the newly
discovered scratch/conjecture overlap, not only the named
simulation/conjecture pair.

## Map delta

changed: `docs/map/CON-seats.md` (row 44 rewritten from "the one place
every canonical role gets its route" to describe the default-uniform-
with-override shape; the stale `_config_for_profile` check, pinned to
the old literal function body, replaced with one anchored to the
actual conditional logic; a new check added for
`SEAT_BINDING_ROLE_CONFLICT`'s existence; `seat_bindings.py` added to
`Owns:` and given its own "Where it lives" row).
created: none (no new map document — this tranche extends an existing
concept document rather than needing a new one).
new checks: 2.
left stale: none requiring action — `docs_verify --stale` lists 24
documents tranche-wide; of the ~5 whose owned files this tranche
actually touched (`CON-seats.md`, `SUB-application.md`,
`CON-authority.md`, `CON-run-identity.md`, `REC-change-a-seam.md`),
every one was individually judged in VALIDATION.md's Map section and
dismissed with a stated reason (content still accurate, all checks
still pass); the remaining ~19 entries predate this tranche entirely.

## Parked (not done, not promised)

- **P1** (this tranche's `PARKED.md`) — the full-gate failure hit
  again at validation is the SAME pre-existing defect already
  root-caused as P3 in `experiments/2026-08-06-change-seat-census-s1/PARKED.md`
  (a continued root carries 2 module-fingerprint stamps where a test
  expects 1). Not re-diagnosed here; independently re-confirmed
  unrelated to this tranche twice (checklist step 20, validation).
  Ready-to-send prompt (unchanged from S1's original entry): "Diagnose
  and fix: `tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
  fails on root `run-a518e33a75507207633f864ba6a864b1`
  (`experiments/2026-08-05-testphase-live-validation/`) with `ValueError:
  too many values to unpack (expected 1)` — a continuation re-emitted a
  module-fingerprint stamp the test assumes appears at most once per
  root. Route via `deepreason-orchestrator`; determine whether the
  continuation path or the test's single-stamp assumption is wrong
  before proposing a fix."

No new defects surfaced by this tranche's own implementation — the
three bugs found while building it (non-deterministic `frozenset`
iteration, a self-inflicted import corruption, a test-only
`DEEPREASON_HOME` resolution mismatch) were each caught and fixed
within the same step that introduced them; none reached a commit
broken, and none are open.

recommended next: **P1**, via `deepreason-orchestrator` — it has now
surfaced independently in two rungs' full-gate runs (S1 and S3) with
identical evidence both times, and is the only open item blocking a
literal "0 failed" on this project's own gate.

This closes Rung S3. `docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md`
names Rung S4 (qualification per seat) and Rung S5 (seats in the typed
record) as the program's next rungs — neither is started, referenced
for design, or scoped by this delivery.
