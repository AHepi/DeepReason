# Hidden-legacy inventory: designed architecture currently disconnected or buried

Started 2026-08-10 (`experiments/2026-08-10-change-blast-radius-analysis/`),
promoted from that tranche's own directory to this standing, repo-root
location per its SPEC.md Fork F4 (operator-approved, R6): the page's
own purpose — "so the operator can decide re-connection priorities from
a single page instead of archaeology-per-incident" — is a FUTURE-
discoverability promise, which only holds if a later session can find
the page without already knowing which tranche produced it.

One page, so the operator can decide re-connection priorities without
archaeology per incident. This document states what is disconnected
and, where traceable, how — it does not recommend a priority; that is
the operator's call once the page exists to make it from.

Append-only discipline, mirroring `docs/ERRATA.md`/`docs/ERRATA_EXECUTOR.md`'s
own convention: a new disconnected/buried piece found by any future
tranche is APPENDED as a new numbered item below (never inserted out of
order, never silently folded into an existing item); an existing item is
never deleted, only updated in place to record when/if it was
reconnected (the item's own "Current disposition" field is where that
update lands). The item numbering below (1-5) is this document's
initial population, consolidated from
`experiments/2026-08-10-change-blast-radius-analysis/CENSUS.md` Part B
at promotion time — items 6+ are for future tranches to add.

Traces: R5. Consolidates `CENSUS.md` Part B plus a targeted sweep of
`docs/map/*.md` Traps sections and `PARKED.md` files for additional
disconnected/buried pieces not already surfaced there.

## How to read this table

**Status** is the current, present-tense state (verified against the
tree at this tranche's head, not assumed from the citing document).
**Disconnection mechanism** is the commit or structural reason it cannot
be reached, where traceable. **Traceable to an authorized grant** notes
whether a specific authorization request can be shown to have caused the
disconnection (yes → cites it) or whether the origin predates the
available git history / cannot be isolated to one grant (no → says so
plainly, per this repo's own state-not-silence convention).

## 1. `property_designer` role — zero live dispatch paths

**What it is:** an LLM-callable role (`rules/experiment.py::propose_properties`)
meant to author property-oracle checks; the sole member of the `coder`
seat group (`GROUP_ROLES["coder"] = frozenset({"property_designer"})`,
`seat_bindings.py`).

**Status:** structurally dead. `propose_properties` early-returns unless
`oracle.py::checker_wf_commitment` finds an ALREADY-EXISTING
property-oracle commitment; the only function that mints a first one
(`property_oracle_commitment`) is called only by `admit_counterexample`,
which itself requires an existing property-oracle-typed commitment as
its own precondition. No public path constructs the first commitment.
No `log.jsonl` in this repository's history has ever recorded a
`property_designer` call.

**Disconnection mechanism:** bootstrap circularity in `oracle.py` —
present from whenever `admit_counterexample`'s precondition was written;
not introduced by the seat-binding tranches that later bound a seat to
it. Not traceable to a single "this commit killed it" moment; it appears
to have been unreachable since the oracle module's own design, only
DISCOVERED live in S6 (2026-08-08) and documented in `docs/ERRATA.md` E15.

**Traceable to an authorized grant:** the DISCOVERY is traceable
(`2026-08-06-change-seat-census-s1` and `-seat-binding-design-s2` bound a
seat to it without checking reachability), but the disconnection ITSELF
predates those tranches — see CENSUS.md B4 for the full chain.

**Current disposition:** `2026-08-08-change-pipeline-design-d2/SPEC.md`
Fork F3 explicitly parked retiring/repurposing it (Road A approved,
R29): "leave `property_designer` untouched (and its own S6 PARKED P1
defect unresolved)." Re-connection (giving it a real bootstrap path) or
retirement remains an open, disclosed, un-decided fork.

## 2. `ARGUMENTATIVE_AUTHORITY=single_family_trial` — dead configuration value

**What it is:** one of the selectable values for `Config.ARGUMENTATIVE_AUTHORITY`.

**Status:** dead weight. `docs/map/CON-schools.md` Traps: "cannot
complete a trial... Parked as dead weight, not removed." Still
selectable in `Config`'s vocabulary; selecting it produces no working
trial path.

**Disconnection mechanism:** superseded by the cross-school-criticism
substitute guarantee built in `experiments/2026-08-01-change-prose-can-refute/`
(CENSUS.md B3) — that tranche needed a working criticism-authority path
for single-family (solo) runs and built one that does not use this
value; the value itself was never removed.

**Traceable to an authorized grant:** yes — the same 2026-08-01 tranche
that built the working substitute (operator's own words: "Get rid of
that requirement. Prose can refute"). The authorization did not ask for
the old value's removal or retention; DELIVERY.md records it as a
PARKED item, not a decision either way.

## 3. `require_cross_family_judge_ensemble` / `LLMAdapter.school_judge_bindings` — superseded, retained

**What it is:** a judge-ensemble-based mechanism for cross-family
criticism authority, predating the 2026-08-01 tranche.

**Status:** superseded, not removed. `docs/map/CON-schools.md` Traps:
"Mistaking `require_cross_family_judge_ensemble` for the live guarantee.
It and `LLMAdapter.school_judge_bindings` are retained but superseded —
correct only for a manifest that authors judge bindings, which the
validator does not permit... The guarantee that actually runs is
cross-school *criticism* in `informal/trial.py`."

**Disconnection mechanism:** the same 2026-08-01 tranche (CENSUS.md B3)
discovered mid-flight that the judge-ensemble approach could not be
built (no manifest contract carries a judge-school binding —
`run_manifest.py::_validate_v4_criticism_policy` rejects any binding
whose role is not `argumentative_critic`) and pivoted to the criticism-based
substitute instead, leaving the judge-ensemble code path in place but
unreachable through any valid manifest.

**Traceable to an authorized grant:** yes, same tranche as item 2.

## 4. `bias_probes`, `premise_deletion_audit`, `planted_flaw_calibration` — never wired to production

**What they are:** three of the four functions in
`src/deepreason/informal/audits.py`, the judge-audit machinery (the
mechanism CLAUDE.md's own standing law requires be consulted before any
judge-authority decision: "judge seats are suspect-by-default... must
first consult the judge-audit evidence").

**Status:** never called from `src/` outside `informal/audits.py` itself
(`docs/map/SUB-evaluation.md`, a checked map claim) — reachable only from
tests or operator-invoked scripts, never from a live run. Only the
fourth function, `paraphrase_invariance_audit`, has a production call
site (`scheduler.py`). `bias_probes` specifically has never produced a
live number in the committed record
(`2026-08-09-change-judge-evidence-review/REVIEW.md` §2.2).

**Disconnection mechanism:** not traceable to a single commit in the
available git history (232 commits; `git log --follow` does not reach
the origin of `informal/audits.py`). The gap is currently DISCLOSED —
`SUB-evaluation.md` states it plainly today — but has not been closed.

**Traceable to an authorized grant:** no. Origin untraceable; recorded
here per this document's own state-not-silence rule rather than omitted
for lack of a citation.

**Why this matters for judge-authority decisions specifically:** the
operator's own standing law makes closing this gap a precondition, not
an optional nice-to-have, for any future decision that leans on judge
seats — `2026-08-09-change-judge-evidence-review/REVIEW.md` is the
record's own consultation of what audit evidence exists, and it found
three of four audit functions have never run live.

## 5. Escape hatches promised in a commit message, never present in the code

**What it is:** "Direct helper status modes and legacy v1 routes,"
named as remaining compatibility escape hatches in commit `83509657`'s
own message ("Make informal text adjudication advisory by default").

**Status:** never existed in the code as described. `authority.py::trial_authority_for`
computed a `mode` value reflecting these hatches and then discarded it,
hard-returning `OBSERVE_ONLY` unconditionally. This is not architecture
that was later disconnected — it is architecture the commit message
described as present that a direct read of the same commit's own diff
shows was never wired to anything. Distinct from items 1-4: nothing to
"reconnect," because the described behavior never existed to begin with.

**Disconnection mechanism:** the value was computed and immediately
discarded in the same commit that introduced it (`83509657`,
2026-07-14).

**Traceable to an authorized grant:** the AUTHORIZATION for this commit
predates the tranche-ledger discipline (2026-07-14, before REQUEST.md
ledgering began) and cannot be reconstructed beyond the commit message
itself; the DISCOVERY is fully traceable
(`experiments/2026-08-01-change-prose-can-refute/REQUEST.md`, operator's
own words on discovery: "Who the hell made that decision. That's so
unbelievably stupid.").

**Current disposition:** superseded by item 3's replacement mechanism
(cross-school criticism); listed here for completeness of the "promised
architecture" record, not as a live re-connection candidate.

## Related pattern, named but explicitly NOT part of this inventory: silently-connected dependencies

Two items from the sweep are the INVERSE of "disconnected architecture"
— a previously-cosmetic mechanism silently became LOAD-BEARING rather
than silently going dead. Listed here, separately, because conflating
the two patterns would blur the page's purpose (re-connection
priorities), but the operator should know both directions exist in the
record:

- **`Config.N_SCHOOLS`** — was a pure conjecture-diversity knob ("no
  routing, no status, no budget," `CON-schools.md`'s own words); is now
  a silent precondition for whether solo-run, status-changing criticism
  can fire at all (CENSUS.md B3). Nothing to reconnect — the opposite
  risk: if this value is ever changed for an unrelated reason (e.g.
  tuning conjecture diversity), criticism authority silently regresses
  to its pre-2026-08-01 broken state with no typed refusal surfaced.
- **Seven `SEAM-*.md` map documents** (`docs/ERRATA.md` E9) — existed in
  the tree but were undiscoverable via `INDEX.md`'s own routing matrix
  until a manual cross-reference sweep found them; corrected 2026-08-03.
  Not code architecture, but the same "exists but not where a reader
  would find it" shape.

## Targeted sweep: additional candidates checked, none found

- `docs/proposals/GATES_AND_PACKAGES_PREPLAN.md` cites
  `experiments/2026-08-09-change-adjudication-judge-seats-optins/` as
  authority; that directory does not exist in the committed tree — the
  cited tranche was never opened. This is PLANNED-BUT-NEVER-BUILT, a
  different category from this inventory's "built, then buried" scope;
  named here so a future reader does not re-discover the same dangling
  citation and mistake it for a disconnection.
- `docs/proposals/DETERMINISTIC_GATES_PREPLAN.md` G2-G5: also
  PLANNED-BUT-NEVER-BUILT, not disconnected — covered in `CENSUS.md`
  Part A4, not repeated here since nothing was ever connected to
  disconnect.
- Swept `docs/map/*.md` Traps sections and all 37 `PARKED.md` files for
  additional "dead"/"unreachable"/"orphan"/"silently" language beyond
  what CENSUS.md Part B already surfaced (B1-B7); no further distinct
  disconnected-architecture instance found beyond items 1-5 above and
  the two "considered and set aside" process-gap cases CENSUS.md Part B
  names explicitly (rung-7 P1, continue-run-rejection) — both of those
  are coverage/staleness gaps in the test suite, not disconnected
  production architecture, so they are not repeated as inventory rows
  here.
