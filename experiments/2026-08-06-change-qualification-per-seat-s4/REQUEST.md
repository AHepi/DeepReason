# Request: qualification per seat — Rung S4 of role-seat separation

Captured: 2026-08-06 from the operator's message opening this
tranche, plus the plan document's own Rung S4 text.

## Verbatim

Operator's message opening this tranche:

> S3 accepted. Now Rung S4 via dr-change-orchestrator: qualification
> per seat, per docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md. Scope:
> deepreason qualify walks the distinct bound profiles — one full
> battery each, each cached by its own subject digest (S2's SM7 is
> the evidence this is already sound); deepreason status reports
> readiness per seat; a run with any unqualified seat refuses with a
> typed reason, at selection time, in the fingerprint-gating shape.
> Honor S2's named non-goal: never qualify a profile inside a
> manifest that mixes it with other seats' different bindings — one
> profile, uniformly bound, per qualification pass (the SM9 untested
> combination stays untested). Single-profile homes must hit the
> existing cache exactly as today. Accept: a two-profile home
> qualifies both and refuses typed when one battery is absent; full
> gate 0 failed; sweep byte-identical. One rung only — no S5
> record-stamping work.

The plan's own Rung S4 text, quoted verbatim from
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` lines 100-107:

> ### Rung S4 — qualification per seat  [EXECUTE]
> `deepreason qualify` walks the distinct bound profiles, one battery
> each, each cached by its own subject digest; `status` reports
> readiness per seat; a run with any unqualified seat refuses with a
> typed reason (the rung-6/fingerprint gating shape: refuse at
> selection, not at registration). Accept: two-profile home qualifies
> both and refuses when one battery is absent; single-profile homes
> hit the existing cache exactly as today.

## Requirements

R1 (behavior): "deepreason qualify walks the distinct bound profiles
— one full battery each, each cached by its own subject digest" —
`deepreason qualify` iterates every distinct `ProviderProfileV1`
bound by the home's seat bindings (plus the default/base profile) and
runs (or reuses, via cache) a full qualification battery for each.

R2 (process): "S2's SM7 is the evidence this is already sound" —
the per-profile subject-digest distinction relies on
`qualification_subject_payload`'s existing behavior (S2's SM7,
`experiments/2026-08-06-change-seat-binding-design-s2/SPEC.md`), not
new digest logic.

R3 (behavior): "deepreason status reports readiness per seat" — the
`status` command's output names each bound seat (role group) and its
own qualification readiness, not only one aggregate readiness.

R4 (behavior): "a run with any unqualified seat refuses with a typed
reason, at selection time, in the fingerprint-gating shape" — before
a run may launch (or `deepreason reason` proceeds), every distinct
bound profile must already be qualified; an unqualified one produces a
typed refusal, following the same "refuse at selection, not at
registration" shape the plan attributes to "rung-6/fingerprint
gating."

R5 (process, non-goal): "Honor S2's named non-goal: never qualify a
profile inside a manifest that mixes it with other seats' different
bindings — one profile, uniformly bound, per qualification pass (the
SM9 untested combination stays untested)." — each qualification pass
must build its manifest with the profile under test bound uniformly
to every role (matching today's `_config_for_profile` single-profile
shape), never a heterogeneous manifest mixing multiple distinct bound
profiles in one qualification pass.

R6 (process): "Single-profile homes must hit the existing cache
exactly as today." — a home with no `--seat` bindings (or bindings
that all resolve to the same profile as the default) must reuse
today's exact single-subject qualification/cache behavior, unchanged.

R7 (process): "Accept: a two-profile home qualifies both and refuses
typed when one battery is absent" — the acceptance test: a home with
two distinct bound profiles, `deepreason qualify` (or the run-launch
path) qualifies both; if only one battery is present/cached, launch
(or the readiness check) refuses typed.

R8 (process): "full gate 0 failed" — `pytest tests/ -q -n 4` must end
0 failed (net of any independently-confirmed pre-existing, unrelated
failure, per this program's established convention from Rungs S1/S3).

R9 (process): "sweep byte-identical" — the 42-root sweep
(`tools/root_sweep.py`) must produce a byte-identical result
before/after this change.

R10 (process): "One rung only — no S5 record-stamping work." — this
tranche delivers Rung S4 only; it does not begin S5 (seats in the
typed record) or any later rung.

## Standing constraints

C1 (from the plan document, quoted above): "the rung-6/fingerprint
gating shape: refuse at selection, not at registration" — the typed
refusal for an unqualified seat must follow this specific,
already-established pattern from a prior rung (rung 6); `dr-spec-change`
must locate and read that prior tranche's actual mechanism before
designing R4's refusal, not invent a new shape.

C2 (from S2's SPEC.md, inherited, quoted in the operator's message):
"never qualify a profile inside a manifest that mixes it with other
seats' different bindings" — SM9's untested combination stays
untested; this tranche must not exercise it either.

C3 (from CLAUDE.md, standing project instruction): frozen surfaces
(`docs/map/INV-frozen-surfaces.md`) require explicit operator
approval for contact; qualification subject digests are frozen
surface 5 — this tranche touches qualification ORCHESTRATION
(how many passes run, when), which S2's SPEC.md already forecast as
zero digest-function contact (SM7), but `dr-spec-change` must
re-confirm this holds for the concrete implementation, not merely
cite the prior forecast.

## Open questions (for dr-spec-change)

Q1: "the rung-6/fingerprint gating shape" — needs the actual prior
tranche/mechanism located and read before design; not resolvable from
this message alone.

Q2: What exactly counts as "the distinct bound profiles" for a home —
does it include the default/base profile (used by every role not
covered by any `--seat` group) as one of the profiles to qualify, or
only the explicitly `--seat`-bound ones? A single-profile home (R6)
implies the default profile itself must always be among the qualified
set (since it's what "hits the existing cache exactly as today"
means) — likely resolvable as "default profile + every distinct
profile named by resolve_seat_bindings, de-duplicated by profile
identity," but confirm in SPEC.md.

Q3: Where exactly does R4's "at selection time" refusal live — inside
`RunPreparationService.prepare` (where `resolve_completed_qualification`
already runs for the single-profile case today), or a new preflight
step? Needs tracing the existing single-profile qualification-refusal
path before deciding.

## Amendments

(none yet)
