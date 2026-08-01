---
name: dr-plan-steps
description: Convert an approved SPEC.md into an ordered, checkable step list (CHECKLIST.md) where each step has one done-criterion. Use after SPEC.md, and again (partial re-plan) after a validation failure.
---

# Plan the steps

Input: SPEC.md (re-read REQUEST.md and SPEC.md in full first). Output:
CHECKLIST.md — the complete ordered path from the current tree to the
accepted change. Execution will do NOTHING that is not a step here, so
missing steps here means missed work later. Plan against that.

## Ordering rules

1. Dependencies first, verification interleaved: a step that writes a
   test precedes the step whose change it guards; a step that runs a
   check follows immediately after the change it checks — not batched
   at the end where failures lose their cause.
2. One step = one action with ONE done-criterion (a command and its
   expected output, or "file exists containing <marker>"). If a step
   needs the word "and", split it.
3. Include the boring steps that get forgotten — they are the point of
   this skill: creating directories, `chmod +x`, updating the ladder
   or docs SPEC says to update, retiring an occupied run root (rename
   commit FIRST), the subsystem test ring, the FULL gate
   (`pytest tests/ -q -n 4`, expect 0 failed), the tranche commit
   with its message, the push with retry, and the final
   `git status --porcelain` cleanliness check.
4. Every step cites its spec item (S-number). A step with no S-number
   is scope creep — delete it or send it to PARKED.md.
5. Mark checkpoint steps `[COMMIT]` at natural boundaries (at minimum:
   after tests-written, after each spec item lands, after the gate).
   The container can vanish; work between commits is work at risk.

## CHECKLIST.md template

    # Checklist for: <request headline>
    Re-read REQUEST.md + SPEC.md before every step. Execute strictly
    in order. One step per dr-execute-step invocation.

    - [ ] 1. (S1) <action>
          done-when: <command> -> <expected>
    - [ ] 2. (S1) [COMMIT] <action>
          done-when: ...
    - [ ] 3. (S2) ...
    ...
    - [ ] N-1. (all) Full gate: pytest tests/ -q -n 4
          done-when: output ends "N passed, 0 failed" (paste it)
    - [ ] N. (all) [COMMIT] push and confirm clean tree
          done-when: git status --porcelain is empty AND branch head
          is on origin

## Re-planning after a validation failure

Touch only the steps implicated by the failure: append new steps
(N+1...) that correct course; never rewrite history of checked steps —
their pasted outputs are the audit trail.

## Exit criteria

- CHECKLIST.md committed and pushed; every S-number covered by >=1
  step; every step has a done-criterion.
- No code changed in this phase.
- Return to the orchestrator.
