# SPEC — Rung 2: the premise channel

Traces to REQUEST.md M1–M11. **Diff budget: 900 lines** — production 500,
tests 250, docs 150, budgeted as separate line items per the estimator
correction recorded in Rung 1b-i.

## The two design questions this rung had to settle

### Q1 — problems in `dep`, or a query? **DECIDED: a query.**

The operator asked why the attribution is not simply an edge, since edges and
support propagation already exist. Under the 2026-08-14 law the old objection
(record compatibility) is retired, so the fork was re-priced on its merits.

Putting problems into `dep` would make Pass 2 mark them for free: refute the
premise, and π becomes `suspended_unsupported` — "orphaned, not false" at the
problem layer in the machinery that already computes it at the artifact layer.
That is genuinely elegant, and two things kill it:

1. **§9.8 requires LAZY materialisation; Pass 2 is EAGER.** The calculus is
   explicit: "the fall is one event; its thousandfold consequence is paid as the
   frontier is touched, not all at once." Pass 2 labels every dependent on every
   recomputation. On the grounded-extension root — 2,894 problems — that is the
   difference between a cheap fall and one that touches the whole frontier at
   once. A derived query is lazy by construction; a Pass-2 label cannot be.
2. **The free part is the smaller half.** Pass 2 would give one label. It gives
   no grades (premise refuted vs premise unaccredited), no three resolutions, no
   closure records. That machinery has to be built either way.

A third consideration, recorded but not load-bearing: problems in `dep` would
put them one edge-role away from `att`, and a problem carrying `refuted` is what
N3 forbids. The query keeps that impossible by construction rather than by
discipline.

**Recorded as reversible.** If a live run shows the query is the bottleneck, the
`dep` design is available and the law no longer stands in its way.

### Q2 — what produces an attribution? **DECIDED: the critic seat, on a dumb rule, with signals for later.**

Amendment 3 puts the long-term answer in the allocation layer. Rung 2 ships the
hook and the evidence source, not the policy:

- **The producer:** the critic seat's pack gains an invitation to file a premise
  attribution against the problem it is working, alongside its ordinary attack
  on a candidate. No new seat, no new role (qualification digests do not move).
- **The trigger:** deliberately simple and deterministic — offered when a
  problem has ≥ `PREMISE_INVITE_AFTER` refuted candidates and carries no
  standing attribution. This redirects ATTENTION on failure; it mints no
  problem, so H1 is intact (M10).
- **The signals, declared through the Rung 1b-i contract** so Rung 1b-ii's
  policy has something to consume: problem thrash, attack-target entropy, and
  the independence-resolution rate — the calculus's own over-binding diagnostic
  (§9.8).
- **The anti-E28 gate:** a test proving the producer actually fires. The harness
  has twice shipped a mechanism no producer ever reached (the controller that
  never steered; the reach trigger that never fired). Not a third time.

## Changes

| # | Change | R |
|---|---|---|
| S1 | `presupposition-wf` — a program commitment parsing an artifact into ⟨problem-id, premise-id⟩, passing iff both resolve and the parsed premise is the artifact ρ `mention`s. Registered as an ordinary artifact (P6/Refl). | M1 |
| S2 | The mention-law check: an attribution carrying a `dependence` ref on its premise FAILS `presupposition-wf`. | M2 |
| S3 | The premise rent battery — a demarcation criterion requiring a SUBSTANTIVE commitment, reusing `measures/reach.py::_substantive`. Builds the `crit` half of `active()`, today an unimported stub. | M7 |
| S4 | `premise_orphaned(π)` as a derived predicate with both grades; lazy materialisation; scheduler deprioritisation (attention only). | M3, M5 |
| S5 | The three resolutions as registered artifacts: retire / translate / independence. Retirement removes π from selection, never deletes it, and is itself attackable. | M4, M11 |
| S6 | The producer: pack invitation + the deterministic offer rule + three declared signals. | M8 |
| S7 | The problem-layer lifecycle map document, in the same commit. | — |

## Acceptance checks

| # | Check |
|---|---|
| A1 | An attribution with a `dependence` ref on its premise fails `presupposition-wf` |
| A2 | Refuting a premise with no standing attribution marks nothing |
| A3 | Filing an attribution against an unrefuted premise marks nothing |
| A4 | Attribution unrefuted ∧ premise refuted ⇒ π marked, correct grade |
| A5 | **The operator's siren sequence, end to end, solo**: π posed, X and ρ registered, X refuted by the rent battery (a demonstrative verdict, status-changing under every authority mode), π marked, retired — with **no conjecture ever proposed on π** — then ν attacked, X reinstated, retirement attacked, π back on the frontier |
| A6 | Translate mints π₂ with lineage provenance; it is the ONLY path that mints a problem from a problem |
| A7 | Independence closes the orphan and the scheduler treats π as unmarked, computed from the resolution; π's own record is never mutated |
| A8 | Marks are lazy: a fall over N problems materialises no orphan until a problem is focused |
| A9 | An uncited/unattributed conjecture is neither refused nor down-ranked (M9) |
| A10 | **The producer fires** in an offline run of the loop, and the three signals are emitted and declared |
| A11 | A v2 run carrying attributions replays and re-derives identically (within-version integrity) |
| A12 | Full gate 0 failed; `docs_verify` full; `blast_radius` disclosed in advance |

## Scope boundary — D-8

Rung 2 ships the channel for premises that fall **by demarcation or by a failing
formal commitment**. A premise that is contentful and wrong **by argument alone**
needs argumentative status authority, which no solo configuration has today
(drift row W-1). That is D-8, unanswered, and Rung 2's SPEC must not let a green
gate imply the channel is complete.

## Out of scope

The allocation policy and its forms (Rung 1b-ii + its own experiment program);
frame assertions and standing (Rung 4); the successor-trigger deletion (Rung 3,
which depends on this rung's *translate*).
