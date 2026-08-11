# Conjecture–Criticism Harness — v1.7 documentation amendment

**Status: descriptive, not behavior-changing.** This document amends
[`harness-spec-v1.3.md`](harness-spec-v1.3.md),
[`harness-spec-v1.4-amendment.md`](harness-spec-v1.4-amendment.md),
[`harness-spec-v1.5-amendment.md`](harness-spec-v1.5-amendment.md), and
[`harness-spec-v1.6-amendment.md`](harness-spec-v1.6-amendment.md). It
does not rewrite, reinterpret, or alter behavior established by any of
the four. Every surface named below already ships on `main` and is
already exercised by the test suite; this amendment closes a
documentation gap (measured 2026-08-11,
`experiments/2026-08-11-spec-drift-measurement/DRIFT_TABLE.md`: six
real, shipped surfaces the prior spec series never named), not a
behavior gap.

Two surfaces this program also found undocumented —
`LEGACY_CRITICISM_ENABLED` and `SCHOOL_SEATS_ENABLED` — are
DELIBERATELY EXCLUDED here: both exist only on a branch not yet merged
into `main` (`claude/adjudication-judge-seats-optins-4nb7ov`,
confirmed unmerged at time of writing). Documenting a flag `main`
does not yet have would recreate the exact drift this amendment exists
to close, in the opposite direction. They are deferred to a later
amendment once that branch lands.

## A. Seats and `seat-bindings.v1`

A seat is a named role-group slot (`conjecture`, `coder`, `scratch`,
`simulation`) a `--seat GROUP=PROFILE` binding assigns a specific
provider profile to at `deepreason setup` time. Seat resolution into
concrete routes happens at manifest-compile time
(`resolve_seat_bindings`/`resolve_seat_bindings_by_group`), but that
resolution is not itself part of the run's own append-only record —
nothing in the log otherwise says which model actually filled which
role.

`seat-bindings.v1` (`src/deepreason/seat_events.py`,
`SeatBindingsEventPayloadV1`) closes that gap: a typed, append-only
payload carrying the resolved `group -> provider/model/profile-digest`
identity into the log. The payload holds IDENTITY ONLY — no wall-clock,
no counter — so two runs bound to the same profiles stamp
byte-identical payloads, and any difference between two stamps is a
difference in the bindings themselves, never in when they were taken.
`tools/root_sweep.py` reads this payload (`recorded_seat_bindings`) as
part of its per-root verification sweep.

## B. `conjecturer.turn.v7` (dual-mode conjecture, additive)

`conjecturer_turn_contract` (`RunManifest`, `src/deepreason/
run_manifest.py`) is a closed `Literal["conjecturer.turn.v6",
"conjecturer.turn.v7"]`, DEFAULT `"conjecturer.turn.v6"` — v7 is
strictly opt-in. v7 adds the `program:candidate_checker` eval-kind
vocabulary entry to the skeleton/reasoning candidate conventions; it is
the SAME wire schema as v6, only a different manifest-facing label so a
conjecture may attach a runnable candidate-checker commitment (§C
below). Every existing committed root's manifest keeps validating and
replaying byte-for-byte under this amendment — v7 is additive to the
`Literal`, never a redefinition of v6's meaning.

## C. `candidate_checker`

A `program:candidate_checker` entry (`src/deepreason/llm/wire.py`) is
the eval-kind marker a conjecturer's turn may attach under the v7
contract (§B): a conjecture that comes with a runnable, checkable
commitment rather than prose alone. This is the CP1-M dual-mode formal
channel — formalism remains an option a conjecture may attach, never an
obligation any conjecture is penalized for lacking (the operator's
standing design law, `CLAUDE.md`).

## D. School-seat routing

A school is a conditioning lineage (v1.5 §A), not a route. When a
school binds a seat, `resolve_school_role_lease` (`src/deepreason/
llm/firewall.py`) resolves ONE call without consulting semantic or
model content: the runtime lease returned is compared against
`manifest.roles[role][seat]`, and any mismatch is a typed
`SCHOOL_ROUTE_LEASE_MISMATCH` refusal, never a silent substitution.
This is route-identity enforcement for the school-seat binding v1.5
already establishes conceptually; this amendment names the concrete
enforcement mechanism v1.5 left undocumented.

## E. Adjudication-blindness (blind-judge structure)

`adjudication-blindness` (`src/deepreason/verification/report.py`) is
one of the harness's typed EPISTEMIC checks (alongside
`bridge-epistemic`, `bridge-grounding`, `grounding-review` — distinct
from the OPERATIONAL checks `detection-total`/`time-travel`). It
verifies that when argued-criticism authority is `observe_only` (v1.3's
default posture: critics file scrutiny, prose changes no status), the
record self-reports that posture, and any judge/blind-same-model
adjudication structure in effect is exposed to a reader rather than
silently assumed. A reader of `positions.accepted` MUST consult this
finding before treating acceptance as adjudicated. `tools/root_sweep.py`
reports the count of `adjudication-blindness` findings per root.

## F. Config referee

`config_referee` (`src/deepreason/verification/report.py`,
`src/deepreason/llm/roles.py`) is an argumentative-critic role whose
ONLY target is run CONFIGURATION, not conjecture content: a periodic,
content-blind review gated by `manifest.inquiry_capability_policy.
config_referee.enabled` and, when a specific school is named, checked
against a frozen criticism binding for that school
(`manifest.criticism_policy.bindings`) via the typed contract
`config-referee.v1`. Unauthorized or unbound config-referee work is a
recorded difference (`"config referee work is not authorized by the
manifest"` / `"...school has no frozen criticism binding"`), never a
silent pass-through. Opt-in per the standing law that judge-shaped
seats are suspect-by-default (`CLAUDE.md`).

## Standing statutes (unchanged, restated for this amendment's scope)

Formalism is an option, never an obligation (§C). Seats and wrappers
change how content is generated, never what counts as evidence (§A,
§D). A solo run with everything on remains available; nothing in §A-F
requires a multi-model ensemble to function correctly, only to unlock
the diversity guarantees each section separately, explicitly names.
