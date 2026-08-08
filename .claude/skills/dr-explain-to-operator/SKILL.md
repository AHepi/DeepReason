---
name: dr-explain-to-operator
description: Communication discipline for EVERY message the operator will read - intermediary status reports, phase-boundary reports, STOP questions, failure notices, and the final message alike. Answer the operator's actual worry first, gloss every technical term conservatively in plain language as you go, and close every FINAL output with exactly one everyday analogy. Load at the start of every session, before the first message the operator will see.
---

# Explain to the operator

Binding, not stylistic. Recorded 2026-08-08 from the operator's own
words (the authority for this skill):

> It needs to be used during every intermediary output, not just the
> last one. Also, the analogy is useful. Keep it for every last
> output. The intermediary messages that are emitted before
> termination needs to put effort into spelling out, as conservatively
> as possible, what the technical terms mean and what they do.

This extends the explanation style already recorded in CLAUDE.md
(2026-08-06). That style was being applied only to final summaries.
It applies to EVERY message the operator reads.

## What counts as an operator-facing message

Anything the operator's eyes will land on before your window
terminates: progress updates between steps, phase-boundary reports
("SPEC.md committed"), STOP questions, failure notices, budget
overrun reports, AskUserQuestion text and its options, and the final
message. If the operator might read it, this skill governs it.
Internal artifacts (SPEC.md, CHECKLIST.md, code, map documents) keep
full technical precision and are NOT glossed — this skill governs
messages, never the ledger.

## The three rules

**1. Every message: worry first.** The first sentence answers what the
operator is actually anxious to know — did it work, is anything lost,
what do you need from me — before any mechanism. When a finding sounds
like bad news, state what it does NOT mean for their intent before
what it does mean. Corrections to your own earlier claims are stated
plainly, once, without hedging.

**2. Every INTERMEDIARY message: gloss technical terms
conservatively.** Every term of art carries its plain-language meaning
in-line, at first use in that message. Conservative means: when unsure
whether the operator holds the term, gloss it — the cost of an
unneeded gloss is a few words; the cost of a missing one is a
re-explanation round. Keep the precise term AND add the meaning; never
replace precision with vagueness. The gloss says what the thing IS and
what it DOES for the operator's intent:

- "the qualification battery (the ~14-minute set of ~1,100 test calls
  that certifies a model can fill each role before a real run is
  allowed to use it)"
- "verify_root came back green (the replay check that re-derives the
  whole run from its log and confirms nothing in the record is
  corrupt or altered)"
- "a typed refusal (the run declining to start for a recorded,
  machine-readable reason — not a crash)"
- "R19 (your authorization limiting the harness.py change to exactly
  two additions)"

Never cite a requirement number, artifact name, commit hash, or error
code without saying in the same breath what it says or what it means
for the work. "Blocked by R19" is not a report; "blocked by R19 (your
rule that the change may touch harness.py in exactly two places, and
this would be a third)" is.

**3. Every FINAL output: full style plus exactly ONE analogy.** The
last message before you stop — end of tranche, end of window, or a
STOP that hands control back — carries the complete CLAUDE.md style:
worry-first, does-NOT-mean before does-mean for bad news, forks
priced as real-world roads (what the operator can do, when, at what
cost) with a recommendation, owning your part plainly when a prior
instruction or rule caused confusion — and closes with ONE short,
accurate, everyday analogy. The analogy is required, singular, and
must actually fit: a wrong analogy is worse than none, so test it
against the mechanism before writing it ("the fire marshal certifies
the room as arranged, or each chair individually"). Intermediary
messages need no analogy; the final one always does.

## Anti-patterns (each of these has cost the operator a round trip)

- Jargon chains: "qualify hit the cached subject digest so reason
  refused shallow-tier" — three unglossed terms in one clause.
- Citation-as-explanation: "per SPEC.md Item S7" with no statement of
  what S7 requires.
- Style-only-at-the-end: five terse intermediary updates followed by
  one polished summary. The operator reads the intermediaries too;
  that is when they decide whether to intervene.
- Burying the answer: mechanism first, verdict in paragraph three.
- Multiple analogies, or an analogy on every intermediary message —
  the analogy earns its force by appearing exactly once, at the end.
- Glossing inside SPEC.md/CHECKLIST.md — internal artifacts are for
  re-derivation and keep full precision; the message layer is where
  meaning is spelled out.

## Relation to the other cross-cutting skills

`dr-ask-the-right-question` decides WHETHER and WHAT to ask;
this skill governs HOW anything — question, report, or verdict — is
worded once it is headed for the operator's eyes. Load both at
session start; they compose, never conflict.
