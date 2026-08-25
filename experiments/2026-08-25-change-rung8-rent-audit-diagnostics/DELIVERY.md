# Delivered: Rung 8 — rent, the authority audit, capture integration, the §14 diagnostics

Branch: `claude/rung-8-closing-calculus-xgxyzt` (pushed, tree clean).
Base: `origin/main` at `462d6091d` (Rung 7 delivered).
`VALIDATION.md` verdict: **PASS**. The v2 calculus program's closing rung.

## What changed

The harness now measures six things about its own reasoning that it could not
measure before, and each is a deterministic function of a fixed span of
sequence numbers rather than of a clock: how far the conjecture stream has
contracted into repeated forms, how evenly new criticism is spread over its
targets, what fraction of old unrefuted work has nobody arguing with it, how
often a refutation is itself refuted, how much criticism lands on the machinery
that turns judgments into attacks, and how much of the live warrant chain
terminates in something outside the current judgment loop
(`src/deepreason/capture/diagnostics.py`).

A deterministic controller reads those six and may enter one attention mode —
widening the frame slice so a candidate sees more of the frame's own standing
attackers and more of the departures already declared against it
(`capture/hysteresis.py`). It may not touch an attack edge, a dependency edge
or a label, and that is exhibited by a differential over one scripted record
and mutation-proven twice, not promised.

Promotion now costs rent: a candidate background must be articulated —
commitments, enumerable assumption ids, stated vocabulary — before it may frame
anything, as a sixth pinned promotion criterion whose three legs fail
separately so a critic can argue with the one that fired
(`calculus/promotion.py`). And §9.9's authority claims are now a program that
runs over a replayed root and has been shown to fail on a seeded violation of
each of its five clauses (`calculus/audit.py`).

Every elevation of a background is logged with a before/after pair carrying the
diagnostic vector and the number of problems the new grant now frames — the
first number this harness has ever had for how much of a run a frame sits on
top of. Ten empirical constants ship as `Config` knobs, and `RESULTS.md` names
sixteen of them across the whole program with their evidence or the word
`unmeasured`.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "RENT (§9.3) as an explicit criterion set on promotion… must be ARTICULATED" | **done** | `fe2384f04`, VALIDATION S1 — criterion 6, three legs, each killed by a different named test |
| R2 | "THE AUTHORITY AUDIT (§9.9) as an executable replay program, not prose" | **done** | `84a85997f`, VALIDATION S3 — five clauses, C5 and P6 as differentials on a copy |
| R3 | "IT MUST BE ABLE TO FAIL: seed a violation and show it fails, then show the tree passes" | **done** | VALIDATION S3 — five seeds, five catches in the audit's own words, then GREEN |
| R4 | "promotion events log before/after conditioning diagnostics" | **done** | `3d530ab11`, VALIDATION S6 — `::test_every_elevation_gets_both_a_before_and_an_after` |
| R5 | "the existing capture/ instruments extend to the new surface" | **done** | `b88c52270`, VALIDATION S5/S6 — the controller reuses `raw_flags`'s four thresholds; the slice's surface is counted |
| R6 | "K_frame, scope-predicate budgets, slice budgets, orphan scheduling ship as Config knobs with recorded defaults and a measurement plan" | **done-with-assumption A2** | `786bf7ab5`, `89a30ecdc`, VALIDATION S2/S9 + SPEC §8. `K_frame` already shipped at Rung 5; orphan scheduling has NO constant and RESULTS says so |
| R7 | "the closing RESULTS.md names every constant with its evidence or the word 'unmeasured'" | **done** | `ca9cb0f07`, RESULTS §2 — sixteen constants |
| R8 | "THE §14 DIAGNOSTICS — six, each a deterministic function of a fixed sequence-number WINDOW" | **done-with-assumption A1** | `c9aba3956`, `3d530ab11`, VALIDATION S4/S7 |
| R9 | "Canonical rounding and declared fixed precision are PART OF THE POLICY (A10)" | **done** | VALIDATION S4 — `ROUND_HALF_EVEN`, precision in the payload, `none` for absence |
| R10 | "Each is a DECLARED signal through the registry" | **done** | `10a0e0b41`, VALIDATION S8 — eight declarations, none carrying the debt marker |
| R11 | "THE HYSTERESIS CONTROLLER… may NOT add or remove attack edges, dependency edges, or labels" | **done-with-assumptions A3, A5** | `b88c52270`, VALIDATION S5 — Theorem 14.1 exhibited, mutation-proven twice |
| R12 | "Policy is a recorded artifact through the existing VERSIONED layer… referee-reviewed via config_referee" | **done** | VALIDATION S5 — `capture14-hysteresis.v1`, attackable; `config_referee` is the existing role, no new role added |
| R13 | "Either re-found them on §14 or declare them a distinct family… Decide in SPEC.md with reasons" | **done** | SPEC §3 D1 — DISTINCT FAMILY, four reasons, three of them measurements; executed in `signals.py` and `DR-INV-signal-contract` |
| R14 | "IF a target-scoped edge-relevance diagnostic fits this rung's budget… otherwise PARK it with a ready prompt" | **done** | SPEC §3 D2 (priced, does not fit) + `PARKED.md` P1 |
| R15 | "GATE PROVES (each named in VALIDATION.md)" — six obligations | **done** | VALIDATION §8 — all six, each PASS with pasted proof |
| R16 | "the program's CLOSING LEDGER… rung by rung… and what the v2 program leaves deliberately open" | **done** | RESULTS §4, §4b, §4c — including §13's residue verbatim |
| R17 | "none beyond Config knobs… NO new LLM role. Public surface unchanged" | **done** | VALIDATION §4/§5 — one authorized contact, 21 insertions / 0 deletions; zero new roles; both smokes green |
| R18 | "If SPEC.md's plan exceeds ~1100, STOP and say what grew" | **done** | SPEC §11 planned 1 077. Execution reached **1 429** — STOP recorded at CHECKLIST step 20 with three priced options, disclosed to the operator at 680/1 100, ceiling NOT re-baselined |
| R19 | "Deliver R-by-R with pasted PROOF" | **done** | this table |
| R20 (Amdt 1) | "keep running tests for as long as you can… Keep going without permission" | **done** | full gate twice, `docs_verify` full twice plus `--audit`/`--links`/`--coverage`/`--stale`, both wheel smokes, `diff_budget` and `blast_radius` at every checkpoint, `--coverage` re-run at the base in a scratch worktree |

**No requirement is `not-done` and none is `deferred`.**

## Assumptions the operator may override

- **A1** the six are emitted from `_record_detection_signals`, once per cycle —
  the site that already promises a complete rather than sampled series.
- **A2** `m = 200` sequence numbers, `h = 50`, both recorded as **unmeasured**
  rather than defended.
- **A3** the controller writes no knob: it records a mode and a policy, and the
  render reads the policy. This is what keeps Theorem 14.1 structural.
- **A4** "succession rulings" as realizing objects means a trial's rival
  artifacts.
- **A5** `critic_budgets` is disclosed as owned-by-the-allocation-controller
  rather than steered — two controllers writing one seat cap is a defect this
  rung declined to create.
- **A6** assumption ids ARE commitment ids on this tree, because
  `DepartureDeclarationV1.broken_ids` and `render.frame_obligations` already
  say so. A separate assumption id space would be a new claim body.

## Map delta

**changed (11):** `DR-INDEX`, `DR-SUB-calculus`, `DR-SUB-scheduler`,
`DR-SUB-periphery`, `DR-SUB-adjudication`, `DR-CON-standing-and-background`,
`DR-CON-packs-and-token-economy`, `DR-SEAM-evaluation-x-rules`,
`DR-INV-frozen-surfaces`, `DR-INV-signal-contract`, `DR-INV-axiom-basis`.
**created:** none. **new checks: 22** (1 047 → 1 069), every one run before it
was written down.

`Verified-at:` advanced to `748c9ab61` on those eleven and on no others.

**left stale, each with its reason:** `DR-SUB-manifest` and
`DR-SEAM-manifest-x-schools` (stale because `run_manifest.py` moved; every
claim they make is unchanged and the new fact lives in `DR-INV-frozen-surfaces`
where it belongs); `DR-SEAM-scheduler-x-rules` (one call added inside the
emission site, which `DR-SUB-scheduler` documents); `DR-SUB-evaluation` (the
sixth criterion is documented in `DR-SUB-calculus`, which owns it);
`DR-SEAM-llm-x-rules`, `DR-SEAM-llm-x-scheduler`, `DR-SUB-application` (already
stale at the tranche base, for Rung 6 and epoch-3 commits; this tranche touched
none of their owned files).

## Errata

**E52 added**, in this commit. `RECONCILIATION.md`'s disposition column routes
S-7, S-21, G-4 and G-5 to "Rung 7"; the record shows all four were delivered by
Rung 8 — Rung 7's own DELIVERY reconciles ten requirements and none of them is
rent, the authority audit, or capture integration. **S-17 is the exception and
cuts the other way**: anomaly conservation really did land at Rung 7, so
`LADDER.md`'s Rung 8 header over-claims it. The cause is structural rather than
careless — the drift table was written when the program had seven rungs, and
`LADDER.md`'s own Correction 2 plus Amendment 2 shifted every later number by
one without re-numbering it. Left uncorrected in place, deliberately: rewriting
a delivered tranche's committed artifact would edit the record of what was
decided when.

## Parked (not done, not promised)

Four entries, each with a ready-to-send prompt in `PARKED.md`:

- **P1 — the IAF target-scoped edge-relevance diagnostic.** R14's park half,
  with its price (250–350 insertions on a tranche already over its ceiling) and
  with its unpaid caveat sequenced FIRST: re-run the flip-rate battery on
  post-Rung-7 roots before scoping anything, because 76 of the 96 roots it was
  measured on have an empty attack relation.
- **P2 — `blast_radius.py`'s symbol tier fires on generic English words.**
  Eleven false frozen-surface contacts for one ordinary tranche, with semantic
  contact disproved by direct measurement and then confirmed by controlled
  comparison: the same tree, more files declared, distinctive symbol names, and
  the eleven vanish. A disclosure gate that cries wolf eleven times is one a
  twelfth, real finding can hide inside.
- **P3 — `Provenance.event_seq` is 0 on every artifact in the tree.** Measured.
  This rung's criticism debt was one line from being a silently-wrong consumer
  of it; every other reader is un-audited.
- **P4 — the SPEC-estimate / diff-budget unit mismatch, third occurrence.**
  Rung 6, Rung 7, and now Rung 8 — past the `authoring-skills` E1 tripwire of
  two recorded failures.

**Recommended next: P2.** It is the cheapest of the four and it is the one that
degrades every future tranche rather than one: the frozen-surface stop is the
single mechanical tripwire on the path from design to delivery, and an
instrument that returns eleven false positives for ordinary work is an
instrument the next author will learn to skim. P1 is the largest and its first
step is a battery run the operator may want to schedule independently; P3 is a
read-only audit; P4 is process.

---

**What the harness now measures about its own reasoning that it could not
before:** whether its stream of conjectures has collapsed into repetitions,
whether its criticism is spreading or circling one target, how much old work
nobody is arguing with, how often it overturns its own refutations, whether the
machinery that turns judgments into attacks is itself under attack, how much of
its warrant chain touches anything outside its own judgment loop — and, at the
moment it elevates a background, how many of its own questions that background
now sits on top of.

**The one sentence the whole program earns:** a background frame costs its
holder a stated vocabulary, an enumerated set of assumptions, and commitments
held open to every relevant episode — and it buys the right to be consulted in
every pack in its scope and nothing else, because standing is render authority
that never reaches a label, and the calculus keeps the crisis visible without
ever being able to force a successor into existence.
