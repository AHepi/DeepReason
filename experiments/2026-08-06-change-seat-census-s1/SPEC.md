# Spec for: seat census — Rung S1 of role-seat separation
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Operational definitions (needed before the table can be built)

**Provider call site** = a source location that dispatches a request to a
provider through `LLMAdapter.call(...)` (or a subclass's `.call(...)`,
e.g. `TransactionalAdapter`), OR — for the one exception the tree
contains — renders a role prompt and builds an `EndpointLease` directly
without going through `LLMAdapter.call` at all (`cli/doctor.py`'s
qualification battery, confirmed by grep: it calls `render_role_prompt`
and constructs `EndpointLease(...)` inline, and contains zero occurrences
of `select_lease`). A site is identified by `file:line` of the `.call(`
(or `render_role_prompt(`) invocation, not by the enclosing function —
one function may hold more than one call site (e.g. `rules/conj.py` has
several `adapter.call(role="conjecturer", ...)` sites for different
sampling paths).

**Which role it renders** = the literal `role=` (or first positional)
argument to `.call`, and separately `template_role=` when present
(`template_role` selects an alternate prompt template while still
dispatching on the *first* argument's endpoint/role plumbing — spec'd in
`adapter.py`'s `call` docstring: "template_role lets an auxiliary
contract... reuse a configured endpoint with a different prompt
template"). Both are recorded when both appear on one call.

**Which lease it selects** = traced through `_render_request`: every
`.call(...)` without an explicit `endpoint_lease=` resolves
`select_lease(self.leases, role, endpoint_index)` where `endpoint_index`
defaults to `0` unless the call site passes a nonzero seat (ensembles,
e.g. `judge`). `doctor.py`'s battery is the one path that never calls
`select_lease`; it builds `EndpointLease(role=pair.role, seat=pair.seat,
route=route)` directly from a locally resolved `route`, which is measured
and named as such, not glossed over as "same mechanism."

**Whether its profile is frozen per-role today** = whether the
*presentation* (`ModelProfile`: standard/frontier/compact) a call site
renders under can differ from another role's presentation within the
same run. Traced in `adapter.py`: `LLMAdapter.__init__` takes one
`model_profile: str | None` parameter, stored as `self.base_model_profile`
— a single value on the adapter instance, consulted by `profile_for`/
`base_profile_for` for *every* role identically (compact-recovery is the
only per-role state, and it is a reactive downgrade after schema-repair
exhaustion, not an operator-assigned per-role profile). This is assumed
to resolve uniformly "No" for every ordinary call site before the table
is built (A2 below); the table still carries a per-row column so a site
that measures differently (if any) is visible, not asserted away.

## Items

S1 (R2, R6): Enumerate every provider call site across the named
consumers (rules, informal, scratch, capabilities, workloads, workflows,
qualification, doctor) using the call-site definition above.
    accept: `grep -rn "\.call(" src/deepreason --include="*.py"` plus
    `grep -n "render_role_prompt\|EndpointLease(" src/deepreason/cli/doctor.py`
    pasted in full in the tranche's CENSUS.md, every hit triaged
    (LLMAdapter-family call vs. unrelated `.call(` on another object,
    e.g. a pydantic/dict method — each triage decision stated inline).

S2 (R3): For every call site from S1, record role rendered, lease
selection path, and frozen-per-role status as an M-numbered table row
with the exact command output that established each column.
    accept: CENSUS.md contains one M-row per call site from S1's list,
    no call site dropped silently; a call site excluded as a false
    positive (`.call(` on a non-adapter object) is listed in an
    "excluded" subsection with the one-line reason, not omitted.

S3 (R4): Measure `select_lease`'s current degrees of freedom: what it
can vary (role, seat/ensemble-index) and what it structurally cannot
(anything not keyed by `(role, seat)` — e.g. call-site identity, workload
kind, or a per-call profile override) from its own source and its two
callers `leases_from_endpoints`/`leases_from_manifest`.
    accept: `sed -n` (or `grep -n -A N`) output of `select_lease`,
    `EndpointLease`, `leases_from_endpoints`, `leases_from_manifest` from
    `src/deepreason/llm/firewall.py` pasted in CENSUS.md, with a plain
    statement of the variance axes derived from that text alone.

S4 (R1): No file under `src/` is modified by this tranche.
    accept: `git diff --stat origin/claude/delivery-rungs-handover-m22sdy... -- src/`
    (or equivalent diff against the tranche's start point) shows no
    output, checked at delivery.

S5 (R5): Every factual claim in CENSUS.md and CON-seats.md is backed by
a pasted command + its literal output, not paraphrased memory of the
code.
    accept: manual re-read pass in dr-validate-change confirming no
    unbacked claim; spot-checked by re-running a sample of the pasted
    commands and diffing output.

S6 (R7): Author `docs/map/CON-seats.md` following the existing
`docs/map/` `SCHEMA.md` convention (doc-id comment, `Verified-at`/
`Verify`/`Owns`/`Seams` headers, prose sections, `` `check:` `` lines at
column 0) naming the seat concept: role -> lease -> route as it exists
today, cross-referencing `llm/roles.py` (ROLES/TEMPLATES), `llm/firewall.py`
(`EndpointLease`, `select_lease`), and `llm/adapter.py`
(`LLMAdapter.call`/`_render_request`). Add an `INDEX.md` row so the new
document is reachable (required for `docs_verify --links`, which is not
this rung's named acceptance gate but is cheap to keep green alongside
it — flagged as an assumption, A3).
    accept: `python tools/docs_verify.py --self-test` and a fresh full
    run parse `CON-seats.md` without a parse error; `Owns:` names only
    files this document actually describes truthfully today (no file
    claimed that the census did not verify).

S7 (R8): `python tools/docs_verify.py` (no `--fast`) reports 0 failed
across the whole `docs/map/` tree, including `CON-seats.md`'s own
`check:` lines.
    accept: pasted full-run output in the tranche, tail line reading
    `0 failed` (or the tool's equivalent all-clear phrasing — captured
    verbatim, not paraphrased).

S8 (R9): No Rung S2 design work performed — no `SeatBinding` shape, no
manifest/qualification-contact decision, no priced options. CENSUS.md
and CON-seats.md describe only what exists today.
    accept: manual re-read of both new documents confirms every sentence
    is in present tense about the current tree, not a proposal; any
    forward-looking note is explicitly labeled "not decided here, S2
    territory" or moved to PARKED.md / the plan document's own residue,
    never asserted as a recommendation.

S9 (R10): Every defect noticed while reading call sites (dead code,
inconsistent role naming, an apparent bypass of `select_lease`, etc.) is
logged in `PARKED.md` with the file:line, a one-line description, and
enough context (which grep found it) that `deepreason-orchestrator` can
start `dr-set-goal` from it directly — never fixed in this tranche.
    accept: `PARKED.md` exists (may legitimately be empty with a
    one-line "no defects found beyond X" if truly nothing surfaces);
    every entry has file:line.

S10 (R2, C2): The plan's own sketch names
`rules/conj.py, rules/crit.py, informal/trial.py, scratch/* (authoring,
conjecture, service), capabilities/* (simulation, research),
workloads/* (code, formal, text, website), qualification, doctor` — the
census additionally records, per A1 below, which of these named modules
turn out to hold zero call sites themselves and instead delegate to a
different module's call site (e.g. `workloads/website.py` is confirmed
by its own docstring, "Compatibility adapter around the existing website
state machine," to delegate to `workflows/website.py`; `qualification.py`
imports its battery machinery from `cli/doctor.py` and contains zero
`.call`/`render_role_prompt`/`select_lease` occurrences itself). The
table's consumer column names the REAL owning file, with the named
module noted as the delegating entry point.
    accept: CENSUS.md's table covers every call site found by S1's grep
    sweep, whether or not its file exactly matches the plan's sketch
    spelling; any plan-named module with zero call sites gets an
    explicit one-line "delegates to X" row, not a silent gap.

## Assumptions (operator may override)

A1 (Q1): The plan's call-site list is a naming sketch, not an exact
path list. The census enumerates every actual provider call site found
by grepping the live tree (per the call-site definition above), and
notes where a named module turns out to be a delegating wrapper rather
than a call site itself (S10) — assumed, operator may override.

A2 (Q2): The table still carries a per-row "frozen per-role today"
column even though the code-level answer is expected to be a uniform
"No, one `model_profile` per adapter/run" (see the operational
definition above) — the per-row column is populated from that single
measured mechanism, not re-derived from scratch per site, but every row
still gets one so a site that behaves differently is visible rather than
assumed away — assumed, operator may override.

A3 (Q3): `CON-seats.md` gets an `INDEX.md` entry and cross-references
the relevant `SEAM-llm-x-*` documents, because that is what
`docs/map/SCHEMA.md`'s own convention requires of any new document and
costs nothing extra; the tranche's named acceptance gate remains
`python tools/docs_verify.py` (full mode) at 0 failed exactly as
R8/this session's phrasing states, with `--links` treated as a
free bonus check, not a second required gate — assumed, operator may
override.

## Questions for operator

(none — all three opens resolved as smallest-reasonable-reading
assumptions above; none differ materially enough in files touched or
effort to warrant stopping)

## Out of scope (explicit)

- Designing `SeatBinding`, any manifest/qualification-contact decision,
  or pricing options — Rung S2, not requested here (R9).
- Fixing any defect found while reading call sites — parked, not fixed
  (R10).
- Modifying `src/` in any way, including comments or type hints — not
  requested; R1 forbids it outright.
- A seat-scoping recommendation for qualification (full battery per
  profile vs. per-seat battery) — that is S2 pricing territory per the
  plan document itself, not this rung's deliverable.

## Budget

~0 lines changed under `src/`. New files: `CENSUS.md` (measured table +
raw command output, tranche dir), `PARKED.md` (tranche dir, may be
near-empty), `docs/map/CON-seats.md`, one `docs/map/INDEX.md` row edit.
Estimated 1-2 commits (capture/spec already committed separately;
one commit for the census + map doc, one for delivery). Frozen surfaces
touched: none (read-only measurement; no state digests, event
application, replay formats, or qualification subjects touched).
