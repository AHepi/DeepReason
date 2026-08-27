# Request: "model authored code execution switched off. I need to know if it's safe to switch on."

Captured: 2026-08-27, from the tranche instruction's AUTHORITY block
(operator's words, verbatim, 2026-08-27) plus the standing operator
ruling recorded in the monitor handover.

## Verbatim

Operator, 2026-08-27 (the tranche authority):

> model authored code execution switched off. I need to know if it's
> safe to switch on. Same with simulation. If so switch both on. The
> last window found out it's been off this whole time

Standing operator ruling (recorded in the monitor handover, and in
`docs/map/INV-evidence-channels.md` as operator 2026-08-26):

> Otherwise how is an LLM supposed to test code

and, same date, the ruling that made "live" mean "on by default":

> now the fix. including turning research and, simulation and coding
> permanently on

## Requirements

R1 (artifact): CENSUS — "model authored code execution switched off …
Same with simulation." Enumerate every capability channel that can
execute model-authored code, with, for each, its default state on
main, the exact switch that governs it, and whether the current
default matches the standing ruling. Proof: a table in SPEC.md with
`file:line` citations for every row.

R2 (artifact): SAFETY ASSESSMENT — "I need to know if it's safe to
switch on." For EACH containment property — (a) no network access,
(b) bounded wall time, (c) bounded memory, (d) file access confined to
the run's own sandbox directory, (e) no privilege beyond the harness
process — identify the code that ENFORCES it and the committed test
that PROVES it, and run those tests. A property enforced only by
docstring, convention, or the model's good behaviour counts as ABSENT.
Proof: SAFETY.md with per-property verdict, citations, and pasted test
output.

R3 (process): VERDICT GATE — "If so switch both on." The switch is
authorized only on a SAFE verdict. If every R2 property is
code-enforced and test-proven: verdict SAFE, proceed to R4. If ANY
property is absent or unprovable: verdict NOT PROVEN — STOP, commit
SAFETY.md with the gap list and a ready-to-send hardening prompt,
report, and switch nothing on.

R4 (behavior, conditional on SAFE): SWITCH BOTH ON — "If so switch
both on", as configuration per the modularity law: the enabled state
must be reachable without a code edit, and the "everything on" shape
must actually be everything-on — a configuration binding the python
toolchain gets a policy that can dispatch to it. Keep the declarative
profile available as a configuration choice. Per the
all-configurations law, a configuration that cannot reach its runner
still COMPILES and carries a typed disclosure — never a silent dead
channel, and never a new compile-time refusal.

R5 (behavior, conditional on SAFE): OFFLINE PROOF — a regression test
(or extended soak case) demonstrating end-to-end that a
`sandboxed_python_v1` proposal is accepted, dispatched, and executed
under the R2 containment on the enabled configuration, plus a mutation
proof shown RED then GREEN on the wiring. Same obligation for the
code-testing channel if R1 found it gated off.

R6 (process): PARK — "Every defect discovered on the way is PARKED
with a ready-to-send prompt, never fixed here. One tranche, one goal:
the goal is the census, the verdict, and (on SAFE) the switch."

## Standing constraints

C1: "research, simulation, and code-testing channels stay ON —
'Otherwise how is an LLM supposed to test code'" — standing operator
ruling, monitor handover; already encoded at
`docs/map/INV-evidence-channels.md`.

C2: "no exceptions pre-granted" for frozen surfaces — the tranche
instruction's FROZEN-SURFACE FORECAST. If the enablement path requires
touching `capabilities/state.py`, `harness.py`, `invariants.py`,
`verification/`, `run_manifest.py`, `qualification.py`, or
`route_fingerprint` in `llm/firewall.py` — STOP and ask.

C3: "this tranche is offline-only. Do not request the key; if anyone
supplies one, do not use it." — the tranche instruction's SETUP block.

C4: MUTUAL STOP LINES — "do not write anywhere under
`experiments/2026-08-27-change-technique-run/`, do not modify that
branch, its ladder, its DEEPREASON_HOME, or any running process; your
blast radius is src (non-frozen policy/config), tests/, docs/map/, and
your own new tranche directory only."

C5: "the root sweep is RETIRED — never run or propose one." — the
tranche instruction's KNOWN CURRENT STATE, and CLAUDE.md.

C6: Cost disclosure, not a defect — "changing capability opt-ins
changes the qualification subject, so the next live run pays a fresh
qualification battery (~14 min); say so in DELIVERY."

## Map preflight — resolved ids

Resolved from `docs/map/INDEX.md` before designing:

- `DR-INV-evidence-channels` (`docs/map/INV-evidence-channels.md`) —
  the three evidence-minting channels, on by default, and the one
  field that turns any of them off. **The governing document for this
  tranche.** Owns `src/deepreason/channels.py`.
- `DR-INV-frozen-surfaces` (`docs/map/INV-frozen-surfaces.md`) — read
  before designing, per C2.
- `DR-SUB-capabilities` (`docs/map/SUB-capabilities.md`) — simulation
  and research lifecycles; state digests are frozen.
- `DR-CON-capability-lifecycle` (`docs/map/CON-capability-lifecycle.md`)
  — typed proposal → admission → work order → result.
- `DR-SEAM-capabilities-x-rules` (`docs/map/SEAM-capabilities-x-rules.md`)
  — read BEFORE either subsystem, per the ordering rule.
- `DR-SUB-verification` (`docs/map/SUB-verification.md`) — **FROZEN**;
  `verification/contained.py` is the execution backend under
  assessment. Assessment is read-only; any change there is a C2 stop.
- `DR-SUB-manifest` (`docs/map/SUB-manifest.md`) — **FROZEN**;
  qualification subjects. C6 is the cost, not a contact.

Seam `capabilities × channels` is listed as **not yet written** in
`INV-evidence-channels.md`'s `Seams-undocumented:`. That is a finding,
not a blocker (map preflight rule 5): this tranche's change lives
exactly on it.

## Open questions (for dr-spec-change)

Q1: "model authored code execution" and "simulation" — the operator
names two things. Does "model authored code execution" mean the
`sandboxed_python_v1` runner profile (the thing that executes
model-authored Python) and "simulation" mean the simulation channel as
a whole, or are they two separate channels? R1's census must answer
this from the code before R4 acts.

Q2: R4 says "the enabled state must be reachable without a code edit".
`DEEPREASON_SIMULATION_RUNNER=contained` already achieves that today.
Does "switch both on" mean change the DEFAULT, or is the existing env
var enough? The operator's "it's been off this whole time" and the
2026-08-26 "permanently on" ruling bear on this; SPEC.md must record
the reading it takes.

Q3: Does the code-testing channel execute model-authored code at all,
or does it only compile commitments? `INV-evidence-channels.md` says
its enforcement is "unconditional — no gate exists", which would mean
it is already ON. R1 must settle this before R5's second obligation
applies.

## Amendments

### Amendment 1 — 2026-08-27, after the NOT PROVEN verdict was reported

Operator, verbatim:

> can you fix please. Frozen surface changes are permitted as long as you
> document what is affected.

**R7 (behavior): FIX the containment.** "can you fix please" — close the
escape SAFETY.md demonstrated, on every guard of that family, not only the
two the probe exercised. Supersedes R6's park-don't-fix instruction FOR
THE CONTAINMENT DEFECT ONLY (PARKED.md P1 and P2); every other parked
finding stays parked.

**C7 (constraint): frozen surfaces are GRANTED, conditional on
documentation.** "Frozen surface changes are permitted as long as you
document what is affected." This supersedes C2's "no exceptions
pre-granted" and the tranche instruction's STOP-and-ask requirement for
the surfaces this fix needs. The condition is not a formality: every
frozen surface touched is named, with what moved, why, and what it can
and cannot change about any committed root — recorded in FIX.md BEFORE
implementation and in `docs/map/INV-frozen-surfaces.md` as a granted
contact, per the discipline that document already records for the
2026-08-21, 2026-08-22, 2026-08-24, 2026-08-25 and 2026-08-27 grants.

**R8 (behavior): the switch-on the fix unblocks.** R3–R5 are unchanged
and still standing. The operator's original "If so switch both on" was
conditional on a SAFE verdict; the verdict was NOT PROVEN because of the
defect R7 now fixes. So once R7 lands, R2's assessment is re-run, and if
it returns SAFE the pre-authorized R4/R5 fire. If it does not return SAFE,
R3 stops the tranche again — the gate survives the fix.

### Amendment 2 — 2026-08-27, same exchange

Operator, verbatim:

> oh and it doesn't break other modules

**C8 (constraint): the fix may not break anything else.** This is an
acceptance check with teeth, not a reassurance. Discharged three ways,
all of which must pass:

1. The full gate at 0 failed — every module's own tests.
2. A POSITIVE test per hardened guard: legitimate model-authored code
   that uses ordinary attributes (`math.sqrt`, `rng.randint`, list and
   dict methods, a model-defined class's own attributes) still runs and
   still returns its verdict. A guard that closed the escape by
   rejecting everything would pass the gate and fail the operator.
3. An enumeration test proving the rejected set is exactly the
   introspection surface and nothing more — so "does not break other
   modules" is a property that can be re-derived, not a claim about
   today's test suite.

## Amendments (continued)

(append-only; later operator messages land here)
