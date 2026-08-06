# Request: seat census — Rung S1 of role-seat separation

Captured: 2026-08-06 from the operator's task message opening this
session, plus its cited source document
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` (which records the
program-originating instruction as spoken 2026-08-06 by the operator
to the monitor session that wrote the plan).

## Verbatim

Program-originating instruction (quoted in
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` lines 6-10 as the
operator's words to the session that authored the plan):

> Actually make the step by step plan to separate them properly. Along
> with the simulation and scratch. Make them free to assign whatever
> model a user wants. Then use them in packages later.

This session's task message, opening instruction:

> Branch claude/delivery-rungs-handover-m22sdy. Preflight per
> dr-drive-harness (resync, editable install, read CLAUDE.md). Then
> read docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md in full — it is the
> program plan; this tranche is Rung S1 only.
> Execute Rung S1 via dr-change-orchestrator: the seat census. MEASURE
> ONLY — no src/ change, no design. Enumerate every provider call
> site (rules, informal, scratch, capabilities, workloads,
> qualification, doctor), and for each record: which llm/roles.py
> role it renders, which lease it selects, and whether its profile is
> frozen per-role today. Also measure what select_lease can already
> vary. Every claim is a pasted command output. Deliverables: the
> measured table in the tranche dir, plus docs/map/CON-seats.md with
> runnable checks, docs_verify full mode 0 failed.
> One rung only. Stop after delivering S1 and present the census — do
> not begin S2's design. Anything broken you find along the way is
> parked with a ready-to-run entry.

The rung's own text, quoted verbatim from
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` lines 44-55:

> ### Rung S1 — seat census  [MEASURE ONLY, no code]
> Enumerate every provider call site and classify it by role and
> consumer: rules/conj.py, rules/crit.py, informal/trial.py, scratch/*
> (authoring, conjecture, service), capabilities/* (simulation +
> research), workloads/* (code, formal, text, website), qualification,
> doctor. For each: which `llm/roles.py` role it renders, which lease
> it selects, whether its profile is frozen per-role today.
> Deliverable: a measured table (M-numbers, pasted commands) in the
> tranche + `docs/map/CON-seats.md` naming the seat concept. Also
> measure the lease/seat mechanism's current degrees of freedom — what
> `select_lease` can already vary. Accept: every call site in the
> table; docs_verify green with the new document's checks.

## Requirements

R1 (process): "MEASURE ONLY — no src/ change, no design." — no file
under `src/` is edited in this tranche, and no design/decision work
(Rung S2 territory) is performed.

R2 (behavior): "Enumerate every provider call site and classify it by
role and consumer: rules/conj.py, rules/crit.py, informal/trial.py,
scratch/* (authoring, conjecture, service), capabilities/* (simulation
+ research), workloads/* (code, formal, text, website), qualification,
doctor."

R3 (behavior): "For each: which `llm/roles.py` role it renders, which
lease it selects, whether its profile is frozen per-role today."

R4 (behavior): "Also measure the lease/seat mechanism's current
degrees of freedom — what `select_lease` can already vary."

R5 (process): "Every claim is a pasted command output."

R6 (artifact): "Deliverable: a measured table (M-numbers, pasted
commands) in the tranche" — the measured table, with M-numbered
entries and pasted command output, lives in the tranche directory.

R7 (artifact): "`docs/map/CON-seats.md` naming the seat concept" with
"runnable checks" (per this session's phrasing) — a new map document,
`docs/map/CON-seats.md`, following the existing `docs/map/` CON-*
convention (checkable `check:` lines).

R8 (process): "Accept: every call site in the table; docs_verify green
with the new document's checks" / this session's phrasing: "docs_verify
full mode 0 failed" — `python tools/docs_verify.py` (no `--fast`) must
report 0 failed, including the new document's checks.

R9 (process): "One rung only. Stop after delivering S1 and present the
census — do not begin S2's design." — deliver S1 only; do not draft,
price, or decide any part of Rung S2 (`SeatBinding`, manifest/
qualification contact, etc.).

R10 (process): "Anything broken you find along the way is parked with
a ready-to-run entry." — defects discovered during the census are
recorded in `PARKED.md` with enough detail to hand to
`deepreason-orchestrator` later, not fixed here.

## Standing constraints

C1: "Preflight per dr-drive-harness (resync, editable install, read
CLAUDE.md)." — environment preflight required before work; performed
this session (see commit history: branch resynced from
`origin/claude/delivery-rungs-handover-m22sdy`, editable install
verified via `which deepreason`).

C2: "read docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md in full — it is
the program plan; this tranche is Rung S1 only." — the plan document
is the program's authority; only its Rung S1 section is in scope here.

C3 (from CLAUDE.md, standing project instruction): "Commits: one
defect or one change per commit; message states what, why, the live
evidence (run ids), and 'Full gate: N passed, 0 failed' when code
changed." — not applicable to gate-running here since R1 forbids
`src/` changes, but commit discipline still applies to the tranche's
own artifacts.

## Open questions (for dr-spec-change)

Q1: The plan's call-site list ("rules/conj.py, rules/crit.py,
informal/trial.py, scratch/* ..., capabilities/* ..., workloads/*
..., qualification, doctor") is a naming sketch, not necessarily an
exhaustive or exactly-pathed list against the current tree. Does the
census enumerate exactly those named files/globs, or every actual
provider call site reachable by grepping the codebase (which may
include sites the sketch's names don't exactly match, e.g. renamed or
additional modules)?

Q2: "whether its profile is frozen per-role today" — the plan's own
anchors section says "today every lease resolves to the one provider
profile `setup` bound," implying the answer may be uniformly "not
frozen per-role, single shared profile" for every site. Does the
census still need a per-site column confirming this, or is a single
measured statement (with supporting command output) sufficient,
with the table still enumerating each site individually for R2/R6?
(Leaning: per-site column still required, since R6 requires the table
per call site; this question is about whether the *measurement method*
can be a single class of check applied to each row rather than N
distinct investigations.)

Q3: "docs/map/CON-seats.md naming the seat concept" — should this new
document additionally cross-reference existing SEAM-llm-x-* documents
(the plan cites `select_lease`, which lives in the llm/manifest seam
territory), and does it need an `INDEX.md` entry to satisfy
`docs_verify --links`? (`docs_verify` full mode, not `--links`
explicitly, was requested — need to confirm whether full mode
subsumes the links check.)

## Amendments

(none yet)
