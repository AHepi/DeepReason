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
