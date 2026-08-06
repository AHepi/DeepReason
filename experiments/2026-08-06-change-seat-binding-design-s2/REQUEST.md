# Request: seat-binding design — Rung S2 of role-seat separation

Captured: 2026-08-06 from the operator's message opening this tranche
(the message immediately following Rung S1's delivery in the same
session).

## Verbatim

> S1 census accepted. Now Rung S2 via dr-change-orchestrator: the
> seat-binding design. DESIGN-AND-STOP — through dr-spec-change ONLY,
> stop after committing SPEC.md and present it. The plan
> (docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md) names the decisions
> this spec must make: the binding surface (price setup-time named
> profiles vs manifest-declared, measured not argued), qualification
> treatment for multiple bound profiles (frozen surface 5 — flag any
> contact), replay validity for old roots (absence reads as
> single-seat), and the continuation-identity rule (a resumed run
> keeps its bindings or refuses typed — apply rung 7's placement
> law). Every option priced with measurements; every rejection cites
> one; the census is your evidence base — cite its M-numbers rather
> than re-deriving. The frozen-surface contact forecast is where this
> spec lives or dies. One rung only; the three kill-risks named at
> the plan's end must each appear as a measurement, not a worry.

Rung S2's own text, quoted verbatim from
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` lines 57-89:

> ### Rung S2 — seat binding design  [DESIGN-AND-STOP]
> The one rung where all the danger lives; everything after it is
> mechanical. SPEC only, priced options, measurements not arguments.
> Decisions it must make (with the rung-7 placement law applied):
>
> - **The binding surface.** A `SeatBinding` maps role-group → provider
>   profile. Where declared? Options to price: (a) setup-time named
>   profiles (`deepreason setup --seat conjecture=<profile>
>   --seat coder=<profile> --seat scratch=<profile>
>   --seat simulation=<profile>`, default: all seats → the single
>   profile, exactly today's behaviour); (b) manifest-declared seat
>   section. Expect (a) resolved at compile time with the RESULT
>   recorded (see S5) to win — but the manifest half is measured, not
>   assumed, because provider identity is manifest-bound today and a
>   judged verdict's seat is epistemically load-bearing.
> - **Qualification treatment (frozen surface 5).** Each distinct
>   profile bound to any seat is its own qualification subject: full
>   battery per profile (~14 min each, cached thereafter). Design
>   question to price: does a seat-scoped battery exist (conjecturer
>   seat qualified on conjecture cases only), or does every profile take
>   the full battery? Cheaper first version: full battery per profile,
>   seat-scoping deferred.
> - **Replay validity.** Committed roots carry no seat bindings; every
>   reader must treat absence as "single-seat run" (reader-before-writer,
>   rung-4 guardrail). Old roots must never move — the S1 census feeds a
>   blast-radius census here.
> - **Continuation identity.** A continued run must continue under the
>   SAME seat bindings its manifest/compiled config bound — a
>   continuation that silently swaps a seat's model is the rung-7
>   label-time mistake wearing a new hat. Typed refusal if bindings
>   cannot be satisfied.
> STOP: operator words required on the chosen option AND explicitly for
> any manifest/qualification contact before S3 plans anything.

The three kill-risks, quoted verbatim from
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` lines 153-163:

> ## What could kill it (named now, so S2 measures them)
>
> - The manifest may bind provider identity too tightly for named
>   profiles to stay out of it — then S2's option (b) territory, full
>   requalification cost per home, operator call.
> - Roles used inside QUALIFICATION itself must stay pinned to the seat
>   being qualified, or the battery measures a chimera.
> - Budget/steering signals (llm/budget.py, config_referee) may assume
>   one model's token economics; per-seat budgets are S2 pricing, not
>   an afterthought.

## Requirements

R1 (process): "DESIGN-AND-STOP — through dr-spec-change ONLY, stop
after committing SPEC.md and present it." — this tranche produces
SPEC.md only; no CHECKLIST.md, no execution, no code.

R2 (behavior): "the binding surface (price setup-time named profiles
vs manifest-declared, measured not argued)" — SPEC.md must price both
named options from the plan (setup-time named profiles vs
manifest-declared seat section) with measurements, not argument.

R3 (behavior): "qualification treatment for multiple bound profiles
(frozen surface 5 — flag any contact)" — SPEC.md must determine and
flag whether the chosen binding design contacts frozen surface 5
(qualification subject digests).

R4 (behavior): "replay validity for old roots (absence reads as
single-seat)" — SPEC.md must address how committed roots without seat
bindings are read, and confirm no existing root moves.

R5 (behavior): "the continuation-identity rule (a resumed run keeps
its bindings or refuses typed — apply rung 7's placement law)" —
SPEC.md must state and justify how continuation identity is preserved,
explicitly applying the mint-time-vs-label-time law from
`experiments/2026-08-04-change-rung7-authority-as-declared-policy/`.

R6 (process): "Every option priced with measurements; every rejection
cites one" — every priced option's rejection (if rejected) must cite a
specific measurement (M-number), not a bare assertion.

R7 (process): "the census is your evidence base — cite its M-numbers
rather than re-deriving" — SPEC.md cites
`experiments/2026-08-06-change-seat-census-s1/CENSUS.md`'s M-numbers
where applicable rather than re-measuring call sites from scratch.

R8 (process): "The frozen-surface contact forecast is where this spec
lives or dies." — SPEC.md must produce an explicit, evidenced
frozen-surface contact forecast (per `docs/map/INV-frozen-surfaces.md`'s
five surfaces) as a central, load-bearing section, not an afterthought.

R9 (process): "One rung only" — this tranche delivers Rung S2's design
only; it does not begin S3 (wiring), S4 (qualification), or any later
rung.

R10 (behavior): "the three kill-risks named at the plan's end must
each appear as a measurement, not a worry" — each of the three
kill-risks quoted above must be addressed by a specific measurement in
SPEC.md, with a stated outcome (defused, real-and-priced, or
escalated), not left as unexamined prose.

## Standing constraints

C1 (from `dr-change-orchestrator`'s map preflight, standing procedure):
map preflight (INDEX.md, INV-frozen-surfaces.md, relevant SEAM/SUB
docs) performed before designing — `docs/map/INV-frozen-surfaces.md`
was read in full this session before any design reasoning began.

C2 (from CLAUDE.md, standing project instruction): "STOP: operator
words required on the chosen option AND explicitly for any
manifest/qualification contact before S3 plans anything" (plan
document's own words, quoted above under Rung S2) — this SPEC does not
authorize S3; it presents priced options for the operator to approve
or redirect.

## Open questions (for dr-spec-change)

(none anticipated at capture time — the plan's own text and this
session's four parallel research threads on manifest route-seat
machinery, qualification subject digests, continuation lease
resolution, and the setup-CLI/rung-7-law precedent are expected to
answer every named decision with measurements; any genuine ambiguity
found while writing SPEC.md is recorded there under its own Assumptions/
Questions sections per that skill's procedure, not backfilled here.)

## Amendments

(none yet)
