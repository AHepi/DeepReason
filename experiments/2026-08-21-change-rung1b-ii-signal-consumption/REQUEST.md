# Request: "Rung 1b-ii of the v2 calculus program: the consumption side of the signal contract"

Captured: 2026-08-21 from the operator's tranche-opening message (this
window, message 1 — the only operator message so far).

## Verbatim

> Rung 1b-ii of the v2 calculus program: the consumption side of the
> signal contract. Route through dr-change-orchestrator; the workflow's
> own stop conditions apply, nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/calculus-rung1b-ii-signal-consumption-t8wq4n origin/main;
> git merge-base --is-ancestor c8071fc34 HEAD || re-fetch. pip install
> -e . --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`, never
> bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY: the operator's six-clause design, ledgered verbatim at
> experiments/2026-08-14-change-calculus-reconciliation-v2/REQUEST.md
> Amendment 2 (R29-R36), and now a standing law in CLAUDE.md ("The
> signal registry is a CONTRACT, and allocation changes are layered").
> Clauses (1), (3) and (6) landed in Rung 1b-i
> (experiments/2026-08-15-change-rung1b-signal-contract/). This tranche
> is clauses (2), (4), (5).
>
> READ FIRST: docs/map/INV-signal-contract.md and both REC recipes; then
> src/deepreason/controller.py (cap_envelope/clamp are the FREE layer,
> _policy_payload already reads policy from a registered artifact);
> docs/ERRATA.md E28 (the controller had never steered a real run —
> zero of 104 committed logs contained a policy body; envelope anchoring
> was fixed by the controller-steering tranche, 2026-08-13).
>
> SCOPE:
> (2) key signals by SEAT INSTANCE. Seat identity is already in the
>     record: seat-bindings.v1 (spec v1.7 §A) carries resolved group ->
>     provider/model/profile-digest into the log. Two structurally
>     asymmetric seats filled by one conjecturer must throttle
>     independently. Do NOT add a role — a new role moves every
>     qualification subject digest (~14 min battery per home) and any
>     rung that thinks it needs one must STOP and ask.
> (4) a compiled matrix test over configuration classes: solo,
>     no-schools, judges-off, legacy-on. Each compiles, the controller
>     attaches, every policy-referenced signal has a producer.
> (5) a topology that cannot produce a signal COMPILES, carrying a typed
>     "allocation open-loop for signal X" notice. Extend the
>     controller-authority record the E28 fix established. Disclose,
>     never die — the all-configurations law, fully delivered 2026-08-16
>     (CompileNoticeV1 is the established pattern; reuse it).
> Plus: migrate controller.py's three harness.state.status.get(...)
> reads into declared signals, paying down part of the 89-entry
> unspecified-declaration debt as you go (lower MIGRATION_DEBT by
> exactly what you fix).
>
> HARD CONSTRAINTS: allocation touches EFFICIENCY, NEVER EVIDENCE — no
> signal and no allocation decision may reach a label or a warrant; a
> test proves it (this is the row to be strictest about: seat identity
> in a signal key is provenance-shaped, and provenance reaching
> adjudication is the one thing the harness forbids by construction).
> No existing signal name changes spelling during migration — decline
> reasons and Measure inputs are compared against recorded roots.
>
> NOT OWED: any cross-version proof (the 2026-08-14 law); within-version
> integrity is covered by the ordinary gate.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (3755 passed at main
> c8071fc34); docs_verify has exactly 3 pre-existing CON-run-identity.md
> shallow-clone failures; 5 MCP-thread tests known-flaky under -n 4
> (isolate before attributing); both wheel smokes pass as of 2026-08-21.
> A parallel window may be working Rung 3b (frame separation) on
> rules/verification files — your blast radius (controller, signals,
> manifest Config knobs) is disjoint; if you find yourself editing a
> file that rung owns, STOP and say so.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full (baselines per docs/AUDIT_BASELINES.md). MUTATION PROOF on the
> efficiency-never-evidence test: break the guard once in a scratch
> copy, watch it go RED, restore, paste both runs. Map moves in the
> same commits (INV-signal-contract.md advances; run its checks before
> stamping). Commit and push every phase boundary (retry 2s/4s/8s/16s).
> Deliver R-by-R with pasted PROOF, closing with one line: which
> configuration classes the controller now attaches to, and how many of
> the 89 registry entries remain undeclared.

## Requirements

R1 (behavior): "key signals by SEAT INSTANCE. Seat identity is already in
the record: seat-bindings.v1 (spec v1.7 §A) carries resolved group ->
provider/model/profile-digest into the log."

R2 (behavior): "Two structurally asymmetric seats filled by one
conjecturer must throttle independently."

R3 (process): "Do NOT add a role — a new role moves every qualification
subject digest (~14 min battery per home) and any rung that thinks it
needs one must STOP and ask."

R4 (artifact): "a compiled matrix test over configuration classes: solo,
no-schools, judges-off, legacy-on. Each compiles, the controller
attaches, every policy-referenced signal has a producer."

R5 (behavior): "a topology that cannot produce a signal COMPILES,
carrying a typed 'allocation open-loop for signal X' notice."

R6 (behavior): "Extend the controller-authority record the E28 fix
established."

R7 (behavior): "Disclose, never die — the all-configurations law, fully
delivered 2026-08-16 (CompileNoticeV1 is the established pattern; reuse
it)."

R8 (behavior): "migrate controller.py's three harness.state.status.get(...)
reads into declared signals"

R9 (artifact): "paying down part of the 89-entry unspecified-declaration
debt as you go (lower MIGRATION_DEBT by exactly what you fix)."

R10 (artifact): "allocation touches EFFICIENCY, NEVER EVIDENCE — no
signal and no allocation decision may reach a label or a warrant; a test
proves it".

R11 (process): "MUTATION PROOF on the efficiency-never-evidence test:
break the guard once in a scratch copy, watch it go RED, restore, paste
both runs."

R12 (artifact): "Map moves in the same commits (INV-signal-contract.md
advances; run its checks before stamping)."

R13 (process): "Deliver R-by-R with pasted PROOF, closing with one line:
which configuration classes the controller now attaches to, and how many
of the 89 registry entries remain undeclared."

## Standing constraints

C1: "No existing signal name changes spelling during migration — decline
reasons and Measure inputs are compared against recorded roots." —
HARD CONSTRAINTS.

C2: "NOT OWED: any cross-version proof (the 2026-08-14 law);
within-version integrity is covered by the ordinary gate." — NOT OWED.

C3: "GATE: ring while iterating; full gate at the boundary; docs_verify
full (baselines per docs/AUDIT_BASELINES.md)." — GATE.

C4: "Commit and push every phase boundary (retry 2s/4s/8s/16s)." — GATE.

C5: "A parallel window may be working Rung 3b (frame separation) on
rules/verification files — your blast radius (controller, signals,
manifest Config knobs) is disjoint; if you find yourself editing a file
that rung owns, STOP and say so." — KNOWN CURRENT STATE.

C6: "the workflow's own stop conditions apply, nothing else stops." —
opening line.

C7: "Use `python -m pytest`, never bare pytest." — SETUP.

C8 (baselines, verbatim): "gate baseline 0 failed (3755 passed at main
c8071fc34); docs_verify has exactly 3 pre-existing CON-run-identity.md
shallow-clone failures; 5 MCP-thread tests known-flaky under -n 4
(isolate before attributing); both wheel smokes pass as of 2026-08-21."

## Open questions (for dr-spec-change)

Q1: R1/R2 say "key signals by seat instance", and C1 forbids changing any
existing signal's spelling. The controller's per-role KNOB names
(`cap:<role>`) are not registry signal names — does C1 bind them too?

Q2: R5 says a topology that cannot produce a signal compiles with a typed
notice. Which signals does "the allocation policy reference", and what
counts as a "producer" for each, decided from the compiled manifest
alone?

Q3: R4 names four configuration classes — "solo, no-schools, judges-off,
legacy-on" — but not their exact compiled shapes. Which existing config
fixtures do they resolve to?

Q4: R8 says migrate three `harness.state.status.get(...)` reads "into
declared signals". Does the controller stop reading `harness.state`
entirely, or keep reading it behind a declared-signal accessor?

Q5: R9 says "lower MIGRATION_DEBT by exactly what you fix" — which of the
89 migrated entries does this tranche have the evidence to fix?

## Scope note (recorded, not interpreted)

The same program's Amendment 3 table (R37-R41) lands attribution-priority
policy work "at Rung 1b-ii". The operator's tranche message above scopes
THIS window to clauses (2), (4), (5) plus the debt migration, and names
no attribution-priority work. R37-R41 are therefore neither delivered nor
declared dead here; they are parked in PARKED.md for a later Rung 1b-ii
continuation, with the discrepancy stated rather than resolved.

## Amendments

(none yet)

---

### Amendment 1 — 2026-08-21, the frozen-surface STOP exchange

Both operator messages are recorded, in order, with the supersession noted —
the convention the operator themself set for the all-configurations law
(`experiments/2026-08-12-change-all-configs-allowed/`).

#### 1a — the operator's first answer to Q-STOP-1, verbatim

> state digests, event application, verification formats, qualification digests
> — is off-plan for this rung. The rung's design should not need them; a design
> that does has grown beyond its scope, and the right move is the standing
> discipline: the window writes the request and its reason into SPEC.md before
> any code, and you (or I, on review) decide on the stated reason. Don't grant
> it verbally in chat — "a STOP already written in prose is not a STOP that was
> obeyed" is a ledgered trap for exactly this.

#### 1b — the operator's grant, verbatim (SUPERSEDES 1a for this contact)

> GRANTED: the 12-line reader fix in src/deepreason/invariants.py
> (_configured_role_cap), on three conditions.
>
> 1. READER-ONLY, PROVEN NOT ASSERTED: no writer and no record format
>    moves. Prove the old behavior is preserved where it was correct: a
>    targeted verify pass over current-version committed roots showing
>    no verification verdict moved — role-keyed knobs must resolve
>    byte-identically before and after; only the new seat-keyed form
>    (cap:role#N) resolves differently, and nothing recorded uses that
>    form yet, so zero verdicts may change. Paste the before/after.
>
> 2. MUTATION-PROVEN REGRESSION: a test that constructs the per-seat
>    knob with a route-authorised ceiling (the 16,384 case) and fails
>    under today's code (the 2500-token default-fallback refusal),
>    passes under the fix. Run it RED on the unfixed tree first and
>    paste both runs — the fallback refusing a legitimate limit IS the
>    red case.
>
> 3. LEDGER THE CONTACT: the grant lives in SPEC.md (already-committed
>    design, note it granted with this date), the map moves in the same
>    commit — INV-frozen-surfaces.md or the covering verification
>    document gains a line naming this contact and why a reader fix is
>    the permitted kind — and the run_manifest.py false alarm is rowed
>    as false-alarm-with-grep-proof, with that file untouched.
>
> The blast-radius tool's self-description stands: grep is not semantic
> proof. You proved the one real contact by measurement; proceed on the
> same standard.

| # | Requirement | Source |
|---|---|---|
| R14 | The 12-line reader fix in `src/deepreason/invariants.py` (`_configured_role_cap`) is **GRANTED**, 2026-08-21. | Amendment 1b preamble |
| R15 | **READER-ONLY, PROVEN NOT ASSERTED**: "no writer and no record format moves ... a targeted verify pass over current-version committed roots showing no verification verdict moved — role-keyed knobs must resolve byte-identically before and after; only the new seat-keyed form (cap:role#N) resolves differently, and nothing recorded uses that form yet, so zero verdicts may change. Paste the before/after." | Amendment 1b (1) |
| R16 | **MUTATION-PROVEN REGRESSION**: "a test that constructs the per-seat knob with a route-authorised ceiling (the 16,384 case) and fails under today's code (the 2500-token default-fallback refusal), passes under the fix. Run it RED on the unfixed tree first and paste both runs — the fallback refusing a legitimate limit IS the red case." | Amendment 1b (2) |
| R17 | **LEDGER THE CONTACT**: "the grant lives in SPEC.md (already-committed design, note it granted with this date)". | Amendment 1b (3) |
| R18 | "the map moves in the same commit — INV-frozen-surfaces.md or the covering verification document gains a line naming this contact and why a reader fix is the permitted kind". | Amendment 1b (3) |
| R19 | "the run_manifest.py false alarm is rowed as false-alarm-with-grep-proof, with that file untouched." | Amendment 1b (3) |
| R20 | "grep is not semantic proof. You proved the one real contact by measurement; proceed on the same standard." — every further contact claim in this tranche is settled by measurement, never by a grep hit alone. | Amendment 1b closing |

**Supersession note.** 1a stated that a design needing a frozen surface "has
grown beyond its scope" and refused a verbal grant. 1b grants the specific
12-line reader fix on the record, after the reason was written into SPEC.md
first. 1a's DISCIPLINE is therefore upheld, not overturned: the grant was given
against a committed, measured design, which is exactly what 1a demanded. 1a's
CONCLUSION for this contact — that it is off-plan — is superseded by 1b. No
other frozen surface is granted by 1b, and none is touched.

### Amendment 2 — 2026-08-22, retire the root sweep

Operator, verbatim, mid-tranche:

> ok. root sweep needs removal. It doesn't matter whether old records still
> verify.

| # | Requirement | Source |
|---|---|---|
| R21 | The **root sweep is removed**. "It doesn't matter whether old records still verify" — the instrument, and every obligation to run it, goes. | Amendment 2 |

**Routing decision, argued rather than assumed.** R21 is not the consumption
side of the signal contract; it is its own change, and CLAUDE.md's law is one
tranche, one goal. Measured blast radius outside `experiments/` (whose committed
tranche artifacts are immutable records and are never edited): **50 references
across `tools/root_sweep.py`, `CLAUDE.md`, four skills
(`dr-drive-harness`, `dr-spec-change`, `dr-ask-the-right-question`,
`dr-audit-broken`), `docs/AUDIT_BASELINES.md`, seven `docs/map/` documents,
`docs/harness-spec-v1.7-amendment.md`, three `docs/proposals/` plans, and
`tests/test_diff_budget.py`.** That is a tranche, not a step. Parked as P4 with
a ready-to-send prompt and the census above.

**What this tranche DOES do about it, because the collision is immediate.**
Step 32 was editing the one map trap that MANDATES the sweep
(`SUB-verification.md`: "the 42-root sweep is the instrument that must confirm
that before any future change here"). Writing that sentence forward now would
ship a document contradicting a standing operator instruction, so the mandate is
removed there and replaced with the census, which is the cheaper and stronger
instrument for the same question. No other document is touched for R21, and
`tools/root_sweep.py` is left in place for its own tranche.

**What this does NOT retract.** The sweep evidence already taken in this tranche
(`proof/sweep_before.txt`, `sweep_after.txt`, empty diff) stays in the record as
what it was: a measurement taken while the instrument still stood, discharging
grant condition 1 (R15) on the day it was asked for. R21 retires the
obligation going forward; it does not unmake a measurement already made.
