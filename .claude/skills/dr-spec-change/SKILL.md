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
   - A mechanism the request NAMES — a fixture to reuse, a file to copy,
     a pattern to follow — is a suggestion, not a requirement. Verify it
     actually reaches the code this change touches (trace the call path)
     before adopting it. If it cannot, that is a material contradiction:
     deliver the PROPERTY the requirement wants and record the
     contradiction in writing, or fork to the operator. Never adopt a
     named mechanism unverified, and never deviate from it silently.
     (Recorded misses this rule generalizes: docs/ERRATA.md E10 — a
     handover-named fixture that never executed the migrated code;
     docs/ERRATA_EXECUTOR.md X11 — a false premise in the authorization
     itself.)
3. Frozen-surface contact forecast — mandatory, in writing. Diff the
   planned target files against `docs/map/INV-frozen-surfaces.md`'s
   surface list and record the verdict in SPEC.md's "Frozen-surface
   contact forecast" section; "none expected" counts, but only after
   actually checking. ANY plausible contact stops the tranche HERE:
   commit SPEC.md and obtain the operator's words before `dr-plan-steps`
   runs. Contact discovered at validation is three commits too late —
   the tranche that proved it (docs/ERRATA_EXECUTOR.md X9, XE1) was
   technically perfect and still could not deliver. For changes that add
   data to the typed record, one more guardrail: the absence-tolerant
   READER lands before the writer emits, so every existing committed
   root stays valid with the new data absent (the rung-4 guardrail
   generalized; X8 is the precedent for keeping new fields out of frozen
   digests entirely). And a new typed-record OBSERVABLE (field, record
   type, finding) needs a sweep probe proposed for it in the spec: a
   sweep that never looks at the new data reports "byte-identical"
   trivially while proving nothing about it. The probe change is its own
   SEPARATE commit — extending `tools/root_sweep.py` resets the
   byte-identity baseline, so it never rides the same commit as the
   `src/` change it would judge, gets its own before/after capture on an
   unchanged tree, and follows the tool's probe rule (assert the
   attribute exists before reading it). Build every proposed test,
   check, and probe to `dr-execute-step`'s "Durable tests, checks, and
   probes" rules — they must survive dramatic repo changes, failing
   only when the guarded claim stops being true.
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

    ## Frozen-surface contact forecast
    none expected — checked against INV-frozen-surfaces.md
    | <surface>: <why contact is plausible> (STOP — operator words
      required before dr-plan-steps)

    ## Budget
    ~<n> lines, <n> commit(s). Frozen surfaces touched: none | <flagged>

## Exit criteria

- SPEC.md committed and pushed; every R number appears in some item
  (or is explicitly marked deferred with the operator's words allowing
  it).
- If "Questions for operator" is non-empty: stopped and asked.
- Return to the orchestrator.
