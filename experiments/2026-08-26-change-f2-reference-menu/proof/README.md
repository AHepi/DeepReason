# Proof artifacts — F2 reference menu

## `s14_unforked_green.txt` / `s14_forked_red.txt` — the one-authority mutation proof

R10's words: "the menu and the diagnostic derive from ONE source
(mutation-prove: fork the lists in a scratch copy, a divergence test goes
RED)".

**The fork.** In a scratchpad copy of `src/deepreason/llm/repair.py`, the
one call to `legal_handles_for` inside `_scratch_reference_guidance` was
replaced with `resolved = None`, which drops the diagnostic back onto its
own locally composed list — the exact shape E26's law forbids, and the
shape the tree carried before `reference_menu.py` existed.

**The result, and the part worth reading.** Two tests were run against both
trees:

| test | unforked | FORKED |
|---|---|---|
| `test_menu_and_diagnostic_are_one_set` | PASS | **PASS** |
| `test_the_diagnostic_consumes_the_resolver_rather_than_agreeing_with_it` | PASS | **FAIL** |

The set-equality test does not detect the fork. That is not a defect in the
proof; it is the finding. Two independently maintained lists AGREE on any
fixture their authors thought of, which is how "two lists kept in
agreement" survives a test suite indefinitely and then diverges in
production on the case nobody wrote down. Set equality can only ever
sample; it cannot establish that there is one list.

So the divergence test that actually holds the claim is the CONSUMPTION
one: it diverts the resolver to a sentinel and demands the diagnostic
follow it. A consumer that re-derives the set locally cannot follow, and
goes red. Both tests ship — the first says the sets match today, the second
says they cannot stop matching.

The forked copy lived in the session scratchpad and was never committed
(CLAUDE.md: scratch files never in the repo). Only these outputs are.

## `s10_reused_modules_unchanged.txt` — reuse, not modification

`tools/blast_radius.py` reports CONTACT with the replay-validation frozen
surface for any change that declares `ordered_refs`, because
`invariants.py` references that symbol. R3 instructs this tranche to REUSE
`ordered_refs`; it modifies neither it nor `invariants.py`.

The file is `git diff --stat 4760a32ef -- src/deepreason/invariants.py
src/deepreason/scratch/render.py src/deepreason/evidence/render.py`,
captured empty. Its durable companion is
`test_the_reused_modules_are_not_modified_by_the_menu_machinery`, which
asserts the structural claim instead of the byte one — a byte pin would go
red the day a later, unrelated tranche edits `invariants.py` legitimately,
and a test that fails for a reason other than its own claim is a test that
gets deleted.
