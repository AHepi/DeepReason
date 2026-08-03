# Request: "create a skill for less intelligent LLMs ask the right questions in relation to this harness"

Captured: 2026-08-03, from the operator's message immediately following the
close of the attached-evidence defect tranche (verify-outcome PASS report).

## Verbatim

> Ok. Now I need you to create a skill for less intelligent LLMs ask the
> right questions in relation to this harness. there's already two workflows
> available. But there seems to be an appropriate reasoning gap that can make
> the LLM think about the right things. And other LLMs don't seem to
> understand my questions and requests like you do. So can you take a look
> over the current framework and see if you can add something. Ensure its
> integrated tightly into the current framework.

## Requirements

R1 (artifact): "create a skill for less intelligent LLMs ask the right
questions in relation to this harness"

R2 (process): "take a look over the current framework and see if you can add
something" — the survey of the existing framework is itself requested work,
prior to and shaping the addition.

R3 (behavior): "there seems to be an appropriate reasoning gap that can make
the LLM think about the right things" — the addition must close a reasoning
gap: make a less capable model think about the right things, not merely
follow steps.

R4 (behavior): "other LLMs don't seem to understand my questions and requests
like you do" — the addition must specifically help a less capable model
understand the OPERATOR'S questions and requests, not only the codebase.

R5 (process): "Ensure its integrated tightly into the current framework." —
not a standalone document: wired into the existing two workflow families and
their conventions.

## Standing constraints

C1: "there's already two workflows available" — same message. The two
families (`deepreason-orchestrator`, `dr-change-orchestrator`) are the given
structure; the addition complements them rather than duplicating or
replacing them.

C2: "take this opportunity to fix documentation as you go" — operator,
earlier this session (2026-08-03, mid-defect-tranche). Standing grant, still
in force; documentation defects found while surveying are repaired or
parked, per its GOAL.md encoding.

C3 (repo law, CLAUDE.md): route ALL substantive work through one of the two
skill families; one tranche, one goal; scratch files to the session
scratchpad, never the repo.

## Open questions (for dr-spec-change)

Q1: "ask the right questions" — questions addressed to WHOM? To the operator
(clarifying an ambiguous request before working), to the record (what to
measure before theorizing), or to itself (self-check prompts)? The verbatim
words support all three; R4's emphasis on the operator's requests suggests at
least the first is central.

Q2: Should the new skill be a third routable entry point (invoked before/
alongside the two orchestrators), a subskill the orchestrators reference, or
a checklist document the existing skills point at? R5 ("integrated tightly")
constrains but does not decide the mechanism.

Q3: "less intelligent LLMs" — is there a concrete target (e.g. the glm-5.2
provider model driving live runs, a smaller Claude operating this repo, or
any future agent session)? Determines vocabulary and how much context the
skill must self-carry.

Q4: Is the sibling-branch skill `dr-decide-or-ask` ("derive the operator's
answer before spending their attention", commit 86f1248e on
claude/handover-package-committed-kw8imd, not present on this branch)
intended as prior art to absorb, or is that lineage abandoned?

## Map note (finding, not blocker)

`.claude/skills/` is outside `docs/map/` coverage by the map's own charter
("docs/map describes src/deepreason/"). No DR- id covers the skills
framework; nothing in this change touches `src/`. If the spec decides the
skill needs checkable claims, `tools/docs_verify.py` currently verifies only
`docs/map/` documents — SPEC.md must state whether the new skill carries
checks and, if so, how they run.

## Amendments

(append-only)
