---
name: assembly
description: How an LLM agent selects, installs, and glues the machine's modules (gate, driver, checkers, skills) for a NEW task or repository. Use when setting up any workflow from these tools, deciding which pieces a task needs, or wiring a new artifact type into gated production. Enforces minimal installation and the standard glue patterns.
---

# Assembly (gluing the machine's pieces)

<!-- PROMPT-CORE-BEGIN -->
You are assembling a workflow from independent modules (see MODULES.md,
provided as read context). Rules:

1. MINIMAL INSTALL: list what the task actually requires before copying
   anything. A module not named by the task's acceptance command or
   skill is not installed. Models (the driver, M2) come LAST and only
   if unattended generation is actually wanted -- most workflows are
   complete without them.
2. Decide the three glue questions in order:
   a. What is "done"? -> a deterministic COMMAND with exit codes. If no
      checker exists for the artifact type, the FIRST task is building
      one (single stdlib file + a FORMAT.md grammar, following
      battery_digest.py as the template) -- never a model judging
      doneness.
   b. Who must not collide? -> if more than one actor or session will
      write, install the gate (M1) and put every artifact in a cone.
      One actor, one session: the gate is optional; evidence still
      says commit early.
   c. Who generates? -> humans or a chat agent: give them the relevant
      M4 skill prompt-cores directly. Unattended: install the driver,
      write the stage in treadle.toml with the skill, the checker as
      acceptance, and any grammar files as context_files (a skill may
      never demand conformance to a file the model cannot read).
3. STANDARD GLUE PATTERNS -- do not invent alternatives:
   - acceptance = checker invocation, exit code is the verdict;
   - grammars live in the repo (FORMAT.md files) and reach models as
     READ-ONLY REFERENCE context, never inlined into skills;
   - proposals have no authority: generated artifacts count only after
     the checker passes; a model's failure claim is evidence about the
      model, not the domain;
   - every new artifact type gets: a grammar, a checker, a skill, a
     stage -- in that order.
4. Report the assembly as a table (module -> why installed / why
   skipped) before running anything. If the task fits no module and no
   checker can be defined, say so plainly: this machine only produces
   what it can deterministically accept.
<!-- PROMPT-CORE-END -->
