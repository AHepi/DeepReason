---
name: dr-spec-change
description: Translate a captured request into a concrete, bounded change specification (SPEC.md) with per-requirement acceptance checks and recorded assumptions. Use after REQUEST.md exists or gains amendments.
---

# Specify the change

Input: REQUEST.md (re-read it in FULL first, including amendments).
Output: SPEC.md mapping every requirement to concrete work with a
machine-decidable acceptance check. This is the only phase where
interpretation happens, and it happens in writing.

## Procedure

1. For EVERY R in REQUEST.md (no skips — walk the numbers in order),
   write a spec item: target files, behavior before → behavior after,
   and an acceptance check (a command + expected output, or an
   artifact-exists-with-content check). A requirement with no
   acceptance check is not specified yet.
2. Resolve each open question Q:
   - If the readings differ only in minor detail: pick the smallest
     reasonable one and record it under Assumptions with the words
     "assumed, operator may override".
   - If the readings differ materially (different files, different
     behavior, >2x effort): put it in "Questions for operator" and
     STOP after committing SPEC.md — present the batched questions.
     Never start implementation with a material ambiguity open.
     First load `dr-ask-the-right-question` and run each candidate
     question through it: the record or the operator's recorded values
     answer most of them, and only survivors of its dominance test
     belong in the batch (each with a recommendation).
3. Check each spec item against DeepReason's frozen surfaces (state
   digests, event application, replay record formats, qualification
   subjects, manifest schemas). If touched: flag the item, stop for
   operator approval.
4. Set the budget: total estimated changed lines and commits. If over
   ~300 lines, propose a split into ordered sub-tranches (each with
   its own delivery) rather than one sprawling one.
5. Anti-invention pass: re-read SPEC.md and delete anything that does
   not trace to an R or C number. If it felt necessary, it is either
   an assumption (record it) or scope creep (PARKED.md).

## SPEC.md template

    # Spec for: <request headline>
    Traces: every item cites R/C numbers. Untraceable items are bugs.

    ## Items
    S1 (R1): <files> | before: <...> | after: <...>
        accept: <command> -> <expected>
    S2 (R2, C1): ...

    ## Assumptions (operator may override)
    A1 (Q1): <chosen reading, one line, and why it is the smallest>

    ## Questions for operator (STOP if non-empty)
    ...

    ## Out of scope (explicit)
    <nearest tempting neighbors, each with "not requested">

    ## Budget
    ~<n> lines, <n> commit(s). Frozen surfaces touched: none | <flagged>

## Exit criteria

- SPEC.md committed and pushed; every R number appears in some item
  (or is explicitly marked deferred with the operator's words allowing
  it).
- If "Questions for operator" is non-empty: stopped and asked.
- Return to the orchestrator.
