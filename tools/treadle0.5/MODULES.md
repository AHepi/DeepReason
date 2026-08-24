# MODULES.md — what exists, and the minimal-install rule

A module not named by your task's acceptance command or skill is not
installed. Read this table, write your own assembly table (skills/assembly),
and copy only what that table names.

| module | what it is | install when |
|---|---|---|
| **M3 checkers** | | |
| `checkers/battery_digest.py` + `FORMAT.md` | acceptance for example batteries: `--write` fills digests, `--verify` is the exit-code verdict | your task produces a battery |
| `checkers/consistency_packet.py` + `claims.json` | cross-document claim extraction with `--write`/`--verify`; fails when a document changes a claim another document also states | the same fact is stated in two or more documents that are edited by hand |
| `checkers/influence_probe.py` | instrumented read-surface measurement: what layer B actually touches of layer A after phase P | any "X can/cannot affect Y" claim — measure it, never argue it |
| `checkers/review_harness.py` + `LEDGER_FORMAT.md` | external-model review calls: packet assembly from named file slices, prompt-size governor, hash-chained call ledger | an independent (non-author, ideally non-family) model reviews your artifacts |
| **M4 skills** (PROMPT-CORE blocks; an agent reads the block before doing the work) | | |
| `assembly` | selecting and gluing modules for a new task | always, first |
| `example-battery` | concrete positives, near-misses, boundaries before any meaning is written | any semantic term |
| `mapping-table` | every term↔interpretation binding is a table row | any pinning or doc-code reconciliation |
| `term-pinning` | weakest-meaning pins, occurrence tables, vacuity probes, **dispositions** | any PIN-* record |
| `denotation-tests` | executable checks of a pin against the twin, incl. **option discrimination** | any pin with a runnable twin |
| `minimal-pair-review` | review only through contrast pairs | any semantic review |
| `semantic-round-trip` | blind back-translation audit | before sealing any pin |
| `discharge-typing` | every verdict cites a route and checker; narrow greens | any ledger or verdict recording |
| `decision-mapping` **(new)** | typing an open-item queue: roots, riders, tiers, eliminations | any "what is actually on the desk" document |
| `expressibility-probe` **(new)** | the two-part test behind any "X is not expressible" claim | before that sentence is written |
| `precedent-transport` **(new)** | analogies must transport the invariant the precedent protects | any argument of the form "A does it this way, so B should" |
| `review-response` **(new)** | the find → verify → refute-or-accept-in-writing → act loop | every external review received |

## Not carried from 0.4.1, and why

**M1 `swarm_gate.py`.** One actor, one session, one branch throughout the
source cycle; the gate's job (write collision prevention) never arose, and its
source is lost with the 0.4.1 archive. If a second writer or unattended run
joins, rebuild it or restore it from a 0.4.1 copy — its contract was: every
artifact in a cone, one writer per cone, commit-early enforced mechanically.

**M2 driver (board, `treadle.toml`, stage table, `treadle run`).** Retired on
field evidence, not lost. The source cycle never ran it; what replaced it —
an agent working the `review-response` loop against external reviewers, with
the `review_harness` ledger for provenance — caught more defects than
unattended generation plausibly would have, including reversing the author's
own recommendation twice. The transport slot M2's client filled now belongs
to `review_harness.py`'s injected transport. Install a driver only when the
work is genuinely unattended AND every stage's acceptance is a deterministic
command; a review is never that shape (its verdict is a finding for a person,
not an exit code).

## The three glue questions (answer in order, in your assembly table)

a. **What is "done"?** A deterministic command with exit codes. No checker
   for your artifact type → building one is the first task (single stdlib
   file + a FORMAT.md grammar, `battery_digest.py` as the template). Never a
   model judging doneness.
b. **Who must not collide?** More than one writer → you need a gate (see M1
   note). One actor, one session → commit early, by hand.
c. **Who generates, and who reviews?** Generation: the agent reading the
   PROMPT-COREs. Review: never the author; prefer a different model family;
   route every review through `review_harness` so the packet and ledger rules
   apply, and work every result through `review-response`.

## Standard glue patterns — do not invent alternatives

- Acceptance = checker invocation; the exit code is the verdict.
- Grammars live in the repo as FORMAT.md files and reach models as read-only
  reference, never inlined into skills.
- Proposals have no authority: a generated artifact counts only after its
  checker passes; a model's claim is evidence about the model, not the domain.
- Every new artifact type gets: a grammar, a checker, a skill — in that
  order. And per FR-18: **the checker is not installed until it has been shown
  to fail on a planted violation.**
- Every derived document (a map, a summary, an audit restating a pin) gets a
  staleness guard on its inventory and a stated limit on what the guard does
  not check.
