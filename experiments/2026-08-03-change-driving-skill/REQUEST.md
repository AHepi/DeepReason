# Request: "a skill that teaches other LLMs how to run the harness properly and where to look"

Captured: 2026-08-03, from the operator's message following delivery of the
dr-ask-the-right-question tranche (third change message this session).

## Verbatim

> There needs to be a skill that teaches other LLMs how to run the harness
> properly and where to look for modifications or problem diagnosis. You
> need to wire the current workflows into the skills. While you're at it,
> the workflow needs to be more organised, claude.md will need updating
> because of last turns changes and this turns modifications. readme needs
> to be updated so that this driving skill is reference there, and it's
> more narrowly focused on what the harness does and how to do things. This
> skill needs to reference the current workflows. The workflows mention
> changes to seams, but doesn't explicitly state where to find the document
> and what it's called. For later, the sub documents never mentions the
> seam documents they're involved with, and how to tell whether a
> modification is just isolated or requires directions from rec-seam
> document. But this job is a later task. For now, focus on the others.

## Requirements

R1 (artifact): "There needs to be a skill that teaches other LLMs how to
run the harness properly and where to look for modifications or problem
diagnosis."

R2 (behavior): "You need to wire the current workflows into the skills."

R3 (behavior): "the workflow needs to be more organised"

R4 (artifact): "claude.md will need updating because of last turns changes
and this turns modifications."

R5 (artifact): "readme needs to be updated so that this driving skill is
reference there, and it's more narrowly focused on what the harness does
and how to do things."

R6 (behavior): "This skill needs to reference the current workflows."

R7 (behavior): "The workflows mention changes to seams, but doesn't
explicitly state where to find the document and what it's called."

R8 (behavior, DEFERRED by the operator's own words): "the sub documents
never mentions the seam documents they're involved with, and how to tell
whether a modification is just isolated or requires directions from
rec-seam document. But this job is a later task. For now, focus on the
others." — deferred (operator approved, verbatim above); goes to PARKED.md
as a named later tranche.

## Standing constraints

C1: "take this opportunity to fix documentation as you go" — operator,
earlier this session; standing grant, bounded per its first encoding
(repair what the work touches; park the rest).

C2 (repo law, CLAUDE.md): route ALL substantive work through the workflow
families; the map moves in the same commit as what it describes; scratch to
the session scratchpad.

C3 (this session, delivered tranche): `dr-ask-the-right-question` now
exists and is wired at the stop-and-ask points; this request's new skill
must not duplicate or contradict it.

## Open questions (for dr-spec-change)

Q1: "the workflow needs to be more organised" — organised HOW? The words
underdetermine: a routing/organisation problem in the skill set (now 15
skills, two families + one cross-cutting, with no single index), or the
internal structure of the orchestrator files themselves?

Q2: "readme" — the repo has `README.md` at root; confirm no other README is
meant (e.g. docs/README). Current root README content and length unknown
until read; "more narrowly focused" implies it currently carries excess.

Q3: R1's skill ("run the harness properly", "where to look") vs the
existing map + CLAUDE.md: the content exists scattered (CLAUDE.md live-run
rules, docs/map INDEX, ladder conventions). Is the skill primarily an
INDEX over those authorities with the run-lifecycle spine, or new prose?
(dr-ask-the-right-question section 1 argues for index-over-authorities.)

Q4: "wire the current workflows into the skills" (R2) and "This skill
needs to reference the current workflows" (R6) — R6 is a subset of R2 read
narrowly; does R2 additionally mean the WORKFLOWS reference the new skill
(bidirectional wiring, as was done for dr-ask-the-right-question)?

## Amendments

(append-only)
