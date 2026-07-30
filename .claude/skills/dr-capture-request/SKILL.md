---
name: dr-capture-request
description: Record an operator's suggested change verbatim and split it into numbered requirements (REQUEST.md). First phase of every change tranche; no interpretation, no code reading.
---

# Capture the request

Input: the operator's message(s). Output: `REQUEST.md`. You quote; you
do not paraphrase, improve, or fill gaps. Interpretation happens in
`dr-spec-change`, where it is visible and reviewable — not here, where
it would silently replace the operator's words.

## Procedure

1. Copy the operator's suggestion VERBATIM into a quoted block. If the
   suggestion spans several messages (including earlier in the
   conversation), quote each with its position. Do not trim "context"
   — trimmed context is how inputs get forgotten.
2. Split into atomic requirements R1..Rn. Atomic = one testable
   obligation each. Split conjunctions ("do X and then Y" → R1: X,
   R2: Y). Keep the operator's own words in each requirement; add
   nothing.
3. Capture constraints stated anywhere in the conversation that bind
   this change (deadlines, "don't touch X", style preferences, budget
   remarks like "prioritise this"). These become C1..Cn with verbatim
   quotes.
4. Mark each requirement's kind: `behavior` (code must act
   differently), `artifact` (a file/document/skill must exist),
   `process` (how the work must be done, e.g. "commit as you go").
5. List open questions Q1..Qn — places where the words genuinely
   underdetermine the work. Do NOT answer them here.

## REQUEST.md template

    # Request: <operator's own headline words>
    Captured: <date> from <operator message position(s)>

    ## Verbatim
    > <exact quote(s)>

    ## Requirements
    R1 (<kind>): "<operator's words for this obligation>"
    R2 (<kind>): ...

    ## Standing constraints
    C1: "<verbatim>" — <where stated>

    ## Open questions (for dr-spec-change)
    Q1: <what the words leave undetermined>

    ## Amendments
    (append-only; later operator messages land here as R<n+1>... or
    "R2a supersedes R2", each with its verbatim quote)

## Exit criteria

- REQUEST.md committed and pushed.
- Zero interpretation performed: every R and C contains a quote.
- Return to the orchestrator.
