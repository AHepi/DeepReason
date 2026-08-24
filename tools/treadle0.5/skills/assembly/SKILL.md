---
name: assembly
description: How an LLM selects, installs, and glues treadle's modules for a NEW task or repository. Read MODULES.md first, then this. Enforces minimal installation, the standard glue patterns, and prove-the-guard (FR-18).
---

# Assembly (gluing the machine's pieces)

<!-- PROMPT-CORE-BEGIN -->
You are assembling a workflow from independent modules (MODULES.md is
your read context). Rules:

1. MINIMAL INSTALL: list what the task actually requires before copying
   anything. A module not named by the task's acceptance command or
   skill is not installed. External models come LAST, and only for the
   roles that genuinely need an independent reader (review,
   back-translation) - unattended generation is almost never wanted;
   see MODULES.md on the retired driver.
2. Decide the glue questions in order:
   a. What is "done"? -> a deterministic COMMAND with exit codes. No
      checker for the artifact type -> building one is the FIRST task
      (single stdlib file + FORMAT.md grammar, battery_digest.py as
      the template). Never a model judging doneness.
   b. Who must not collide? -> more than one writer needs a gate (see
      MODULES.md, M1 note); one actor, one session -> commit early by
      hand.
   c. Who generates, who reviews? -> generation: the agent reading the
      PROMPT-COREs at work time. Review: never the author; prefer a
      different model family; every review goes through review_harness
      and every result through the review-response skill.
3. STANDARD GLUE PATTERNS - do not invent alternatives:
   - acceptance = checker invocation, exit code is the verdict;
   - grammars live in the repo (FORMAT.md files) as read-only reference
     for models, never inlined into skills;
   - proposals have no authority: artifacts count only after the
     checker passes; a model's claim is evidence about the model;
   - every new artifact type gets: grammar, checker, skill - in that
     order - and the checker is not installed until proven on a planted
     violation (FR-18);
   - every derived document gets a staleness guard, with the guard's
     limits stated in the document (FR-14).
4. Report the assembly as a table (module -> installed/skipped -> why,
   plus the planted-violation record per guard) BEFORE running
   anything. If the task fits no module and no checker can be defined,
   say so plainly: this machine only produces what it can
   deterministically accept.
<!-- PROMPT-CORE-END -->
