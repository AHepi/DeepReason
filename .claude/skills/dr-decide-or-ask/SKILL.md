---
name: dr-decide-or-ask
description: Before asking the operator anything, derive their answer from the record of their stated values; ask only genuine forks, and always with a recommendation. Load whenever any workflow phase says "stop and ask" or you are composing options for the operator.
---

# Decide or ask

Operator attention is the scarcest budget in the system. A question
whose answer is derivable from what the operator has already said is
not diligence — it is a cost, and it erodes trust. Before composing
any question, run this procedure.

## Step 1: derive the answer first

The operator's standing values are ON THE RECORD. Re-read, in order:
their verbatim words in REQUEST.md/GOAL.md for this tranche; CLAUDE.md
(frozen surfaces, gate discipline, honest-ledger rules); their prior
rulings in this and earlier tranches (DELIVERY.md reconciliations,
approved assumptions, RESULTS.md conventions). From those, this
operator's revealed preferences include:

- smallest correct change; fix readers, never invalidate committed
  records; no frozen surfaces without explicit approval
- never leave a standing spec/code contradiction — specs serve the
  ends, not their own wording
- a reachable defect or operator dead-end is fixed, not shipped
  recorded; a speculative improvement is PARKED, not built
- honesty over polish: negative and inconclusive results recorded as
  such; assumptions surfaced with an override note

## Step 2: the dominance test

For each option you were about to offer, ask: *would every reasonable
operator holding the values above choose the same one?* If yes, the
fork is FALSE — do not ask. Decide, act, and record one line in
SPEC.md/DELIVERY.md: "Decided without asking (dominant under your
recorded values): <choice> — override any time." Examples of false
forks: fix-a-two-line-doc-mismatch vs. leave-it; close a reachable
dead-end vs. ship it recorded; run the gate vs. skip it.

## Step 3: what genuinely earns a question

Ask ONLY when options survive the dominance test AND the choice
changes real stakes: frozen-surface or irreversible action; >2x effort
or cost divergence between defensible readings; a conflict WITHIN the
operator's own stated words; or taste on user-facing shape (naming,
report format) where their preference is unknowable. Batch all such
forks into one question set per tranche.

## Step 4: how to ask

- Lead with your recommendation and the one-sentence reason — never
  present options as a neutral menu when the record favors one.
- State each option's consequence for what the operator cares about
  (risk, cost to them, honesty of the record) — not implementation
  trivia they must decode.
- Include the do-nothing consequence explicitly if it leaves anything
  reachable-broken or contradictory: those are almost never what this
  operator wants, and listing them without saying so invites a wrong
  default.
- One screen, no scrolling context required: quote the minimum from
  the record that makes the question answerable cold.

## Exit criterion

Every question you almost asked is either answered-and-recorded
(dominant) or appears in the batched question set with a
recommendation. Zero questions whose answer a reader of CLAUDE.md and
this tranche's ledger could give without you.
