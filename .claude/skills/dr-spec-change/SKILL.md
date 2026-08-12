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
3. Frozen-surface contact forecast — mandatory, in writing. Run
   `python tools/blast_radius.py --files <every planned target file>
   --symbols <every planned target symbol>` (Rung G6,
   `docs/map/INV-frozen-surfaces.md`) and record its
   `frozen_surface_contacts`/`frozen_adjacent_contacts` result in
   SPEC.md's "Frozen-surface contact forecast" section; "none expected"
   counts, but only after actually running the gate — a hand-checked
   "none" is no longer sufficient once the gate exists to check it.
   ANY plausible contact (the gate's `frozen_surface_verdict: CONTACT`,
   or an `UNKNOWN` reachability entry the gate cannot resolve) stops the
   tranche HERE: commit SPEC.md and obtain the operator's words before
   `dr-plan-steps` runs. **The STOP message — and this document's own
   Frozen-surface contact forecast / Decision sheet sections — MUST
   embed `tools/blast_radius.py`'s computed `frozen_surface_contacts`
   (and `frozen_adjacent_contacts`) list verbatim, never a hand-written
   summary of it. A STOP that describes contact without pasting the
   tool's own list is not this checkpoint** — the words the operator
   gives in reply are words given over a disclosed, computed surface,
   never an inferred one (the design premise of
   `experiments/2026-08-10-change-blast-radius-analysis/REQUEST.md`).
   Contact discovered at validation is three commits too late —
   the tranche that proved it (docs/ERRATA_EXECUTOR.md X9, XE1) was
   technically perfect and still could not deliver, and the 2026-08-09
   incident (same file, "the frozen-surface stop did not hold") shows a
   STOP already written in prose is not a STOP that was obeyed — the
   gate exists precisely so that finding cannot be silently outrun by
   memory three steps later.
4. Record-observable guardrails, for changes that add data to the
   typed record: the absence-tolerant READER lands before the writer
   emits, so every existing committed root stays valid with the new
   data absent (the rung-4 guardrail generalized; X8 is the precedent
   for keeping new fields out of frozen digests entirely). A new
   typed-record OBSERVABLE (field, record type, finding) needs a sweep
   probe proposed for it in the spec: a sweep that never looks at the
   new data reports "byte-identical" trivially while proving nothing
   about it. The probe change is its own SEPARATE commit — extending
   `tools/root_sweep.py` resets the byte-identity baseline, so it never
   rides the same commit as the `src/` change it would judge, gets its
   own before/after capture on an unchanged tree, and follows the
   tool's probe rule (assert the attribute exists before reading it).
   Build every proposed test, check, and probe to `dr-execute-step`'s
   "Durable tests, checks, and probes" rules — they must survive
   dramatic repo changes, failing only when the guarded claim stops
   being true.
5. Blast-radius census — mandatory, pasted, BEFORE any fixture-drift
   prediction. Tool-backed (Rung G6): the same
   `tools/blast_radius.py` invocation step 3 already ran also reports
   `consumers` (tests, map documents, the qualification digest, the
   wheel-smoke pins) for every declared target — paste its
   `consumers.tests`/`consumers.map_checks` fields into SPEC.md's
   "Blast-radius census" section and classify EVERY hit: EXPECTED TO
   MOVE (the design predicts it) or MUST NOT MOVE. The manual grep

       grep -rn "<symbol>" tests/ docs/map/

   is RETAINED as a required cross-check specifically for anything the
   gate's own `reachability` field reports `UNKNOWN`, or for a symbol
   shape the gate cannot resolve (a role-dispatch string label rather
   than a Python identifier, for instance) — the gate augments the
   census, it does not remove the author's own judgment where the gate
   has said, in writing, that it cannot judge. A drift forecast written
   without this census is recall, and recall missed in two consecutive
   specs — under the MORE capable model both times (rung-5 PARKED P6):
   rung 4's prediction was too narrow; rung 5's spec predicted nothing
   and missed a test pinning "exactly one backend", the exact state
   that rung existed to change. The full gate caught both, three
   commits later than the census would have.
6. DESIGN-AND-STOP shape. When the deliverable IS the spec (a
   [DESIGN-AND-STOP] request), two more sections are mandatory, and
   their discipline is measure-don't-reason (the rung-4 M1-M5
   precedent, the one design spec that survived contact with the
   tree unchanged):
   - **Measurements**: every load-bearing design claim is a pasted
     command output. A claim with no measurement is an assumption and
     is moved to Assumptions, where the operator can see it.
   - **Options**: every considered option priced — files touched,
     frozen-surface contact, estimated lines, risk — and every
     rejection cites a measurement, not a preference.
7. Set the budget: total estimated changed lines and commits. If over
   ~300 lines, propose a split into ordered sub-tranches (each with
   its own delivery) rather than one sprawling one. The Budget
   section's headline number(s) MUST equal the computed sum of the
   itemized per-item estimates above — paste the arithmetic (e.g.
   `python3 -c "print(sum([...]))"`), never restated by hand. This is
   the number `tools/diff_budget.py`'s `DIFF_BUDGET_RESULT_V1.verdict`
   is checked against at every `[COMMIT]` step (`dr-execute-step`); a
   headline that contradicts its own itemization defeats the ceiling
   before the first commit (Rung S5, REQUEST.md Amendments 2/3: its
   headline said 220-300, its own itemization summed to 435).
8. Anti-invention pass: re-read SPEC.md and delete anything that does
   not trace to an R or C number. If it felt necessary, it is either
   an assumption (record it) or scope creep (PARKED.md).
9. Rubric pass — the last act before committing. Re-read the finished
   SPEC.md as a REVIEWER, not the author; any "no" routes back to that
   step before commit:
   - every R has a spec item with a machine-decidable accept?
   - blast-radius census pasted (or pasted-empty) and every hit
     classified?
   - frozen-surface contact forecast recorded?
   - every mechanism the request names traced to code it actually
     reaches?
   - DESIGN-AND-STOP only: every claim measured, every option priced?
   - nothing in the spec untraceable to an R/C number?
   Record the outcome as one line in SPEC.md ("Rubric: n/n yes").

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

    ## Blast-radius census
    <symbol/file>: <test or map check hit> -> EXPECTED TO MOVE |
      MUST NOT MOVE
    (every grep hit listed, none omitted; "no hits" is a valid census)

    ## Measurements (DESIGN-AND-STOP only)
    M1: <command> -> <pasted output> — supports <claim>

    ## Options (DESIGN-AND-STOP only)
    A: <files, frozen contact, ~lines, risk> | rejected: cites M<n>
    B: ... | CHOSEN: cites M<n>

    ## Budget
    ~<n> lines, <n> commit(s). Frozen surfaces touched: none | <flagged>

    Rubric: <n>/<n> yes

## Exit criteria

- SPEC.md committed and pushed; every R number appears in some item
  (or is explicitly marked deferred with the operator's words allowing
  it).
- The rubric pass ran and its line is in SPEC.md; a spec with no
  "Rubric:" line was committed without its last check.
- If "Questions for operator" is non-empty: stopped and asked.
- Return to the orchestrator.
