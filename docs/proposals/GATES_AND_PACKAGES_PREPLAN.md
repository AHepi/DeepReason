# Pre-plan: gates and packages — signals driving behavior through typed on/off valves

Status: PROPOSED. Written 2026-08-09 by the monitor session. Extends
BEHAVIOR_MODES_PREPLAN and the adjudication/judge/schools opt-in spec
(experiments/2026-08-09-change-adjudication-judge-seats-optins/).
Authority is the operator's words, verbatim:

> The machinery that is fed directly from signals need to be
> abstracted as packages that affect the behaviour of the harness at
> large. This is a part of the modularisation. ... Config evolution is
> important, but it's only one package that has one particular
> function; to allocate resources. Those same signals need to be able
> trigger other package behaviour as well. Such as packages that
> temporarily block flowing of ideas from scratch pad to conjecture. I
> can see this as essential for creating harness "Modes" in the
> future. And that's another function of modularity: to treat the
> movement of information from one part to another like gates with on
> and off switches. This seems messy, but the functioning is simple;
> gates can only be turned on and off. That's it. But these switches
> will need a lot of hardening and fail-safes. That's the really hard
> bit. Creating the gates so they don't crash anything. Then isolating
> the flip to do only one thing.

## The doctrine (three rules, the entire hardening story)

1. **A gate flip is a typed event in the append-only record** — the
   triggering signal recorded, the flip recorded, well-formedness
   fencing what a flip may touch; replay reproduces the causal chain.
   Mid-run flips thereby stop being label-time violations: the record
   IS the authority for when each gate stood open.
2. **Fail-to-default, never crash**: every gate has a declared default
   state; any failure in flip machinery degrades to the default and
   records that it did.
3. **One flip, one effect; no cascades**: a gate never flips another
   gate. Packages compose gate settings; gates never compose
   themselves. Signal → package → flip(s) is the only causal shape,
   and every hop is typed.

Existing gates-in-fragments this unifies (census basis: the opt-in
tranche's Half 1, BASIN_REPORT, CON-authority): observe_only
(criticism→status), capability grants, the anti-relapse gate, the
scratch→conjecture bounded channel, the config_referee cadence gate,
and every opt-in the current spec designs.

## Staging (the guard against building the framework first)

- **Stage 1 (approval-ready now)**: the opt-in tranche's surfaces ship
  as STATIC mint-time gates — frozen in the manifest, no dynamic
  machinery, trivial hardening.
- **Stage 2 — BENCHED (operator, 2026-08-09: "I think I'm going to
  bench the mid run gate flips for now since it's not necessary for
  modes. But abstracting signals is still a helpful move since
  historical runs have proven that dynamic behaviour can be
  helpful.")**: no dynamic flip machinery for now; all gates are
  static and mint-time frozen, which modes do not need more than.
  What survives of this stage immediately: SIGNAL ABSTRACTION as a
  static surface — the signals (convergence/gate-block rate, referee
  verdicts, and the liveness census's confirmed-live set) become
  typed, uniformly consumable outputs that packages, config, and
  operators read at run boundaries; nothing consumes them mid-run to
  flip anything. The anti-attractor pilot returns when the operator
  unbenches dynamic flips.
- **Stage 3 (only after the pilot survives)**: the package vocabulary
  generalizes; modes = named packages; S7 consumes. Dials (D4's
  load-mix weights) stay a separate, continuous surface: gates are
  topology (whether information flows), dials are budgets (how much).

R-g and the seats/evidence guardrail bind throughout: no gate or
package may key on conjecture KIND, and no package may let generated
content skip criticism. The solo law binds: every gate must have a
solo-compatible setting.
