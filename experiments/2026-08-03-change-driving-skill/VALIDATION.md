# Validation for: "a skill that teaches other LLMs how to run the harness properly and where to look"

Tranche base `140bb3d7` (previous delivery); validated at HEAD `a31f1082`.
All acceptance checks re-run fresh this phase.

## Acceptance checks

S1 (driving skill): sections: 6; frontmatter loads (the skill registered in
this session's own skill list at step 1); greps — deepreason-orchestrator 1,
dr-change-orchestrator 1, dr-ask-the-right-question 1, REC-change-a-seam 1,
INV-frozen-surfaces 2, `SEAM-<a>-x-<b>` 2. : PASS

S2 (workflows → skill): `grep -l dr-drive-harness` lists both orchestrator
SKILL.md files. : PASS

S3 (organising index): `.claude/skills/README.md`, 55 lines (≤80); both
family names, all 12 phase skills, both cross-cutting skills present (no
MISSING). : PASS

S4 (CLAUDE.md): dr-drive-harness 1, ERRATA 1; both cross-cutting skills and
the skills index now named in "Which workflow to use"; ERRATA in the
session-start truth chain. : PASS

S5 (README): dr-drive-harness 1; 357 lines (< 363); "Install and operate",
amend, "MCP public facade", "Architecture and safety" all retained; new
"Operating this repository" section absorbs the old developer-only section;
historical-boundaries compressed; two repetition trims (amend lead-in, MCP
amendment paragraph now defers to the CLI section). : PASS

S6 (seam pointers): `grep -l REC-change-a-seam` over the four files → 4 of 4
(both orchestrators, dr-plan-steps, dr-execute-step), each also naming
`docs/map/SEAM-<a>-x-<b>.md` sides-alphabetical. : PASS

S7 (R8 deferral parked): PARKED.md carries the entry with the operator's
"later task" quote and ready-made inputs for the later tranche. : PASS

## Full gate

    python -m pytest tests/ -q -n 4
    -> 3290 passed, 7 skipped in 765.17s (0:12:45)   # 0 failed : PASS

First attempt recorded 1 failure
(`test_v6_nonconjecture_recovery.py::test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`,
761s run on a loaded box). Pre-existing/flake evidence, per the
stash-equivalent test: this tranche's diff against base contains ZERO
`src/` or `tests/` lines (`git diff --stat 140bb3d7..HEAD -- src/ tests/`
→ empty), the identical code passed 3290/0 twice earlier today, and the
test passes solo (4.52s), with its whole file (21 passed), and on the
immediate full rerun above. Parked as a defect-family candidate.

## Record-behavior preservation

n/a by construction: zero `src/` changes (diff pasted empty above); no
reader or validator touched.

## Frozen-surface diff

    git diff --stat 140bb3d7..HEAD -- src/deepreason/capabilities/state.py \
      src/deepreason/harness.py src/deepreason/invariants.py \
      src/deepreason/run_manifest.py src/deepreason/qualification.py
    -> (empty; the whole src/ diff is empty)   : PASS

## Map

    docs_verify:            0 failed                      : PASS
    docs_verify --audit:    0 finding(s)                  : PASS
    docs_verify --links:    0 dangling, 46 document(s)    : PASS
    docs_verify --coverage: 6 seams swept, 0 finding(s)   : PASS
    docs_verify --stale:    4 entries — the same four as the previous
    tranche's validation (all pointing at commit 2456da55, dismissed there:
    stamp-lags-parent artifact; the documents were updated in that very
    commit). No owned file has moved since; dismissal carries over.

New checks added by this change: none in `docs/map/` — deliberate: no
`src/` behaviour changed and `.claude/skills/` remains outside the map's
charter. The artifacts' shape is pinned by this file's grep set.

## Requirement sweep

R1: demonstrated by S1 — dr-drive-harness exists, six sections, registered.
R2: demonstrated by S2 (workflows → skill) with S1's references back
    (skill → workflows): bidirectional under A4.
R3: demonstrated by S3 — the organising index; assumption A1.
R4: demonstrated by S4 — CLAUDE.md now reflects last turn's additions
    (dr-ask-the-right-question already present; ERRATA added) and this
    turn's (driving skill, skills index).
R5: demonstrated by S5 — README references the driving skill and is
    tighter with does/how intact.
R6: demonstrated by S1's routing section (both families +
    dr-ask-the-right-question named).
R7: demonstrated by S6 — seam document path, naming convention, and the
    recipe document are now explicit at all four sites.
R8: deferred (operator: "But this job is a later task. For now, focus on
    the others.") — parked with the quote (S7).

## Assumptions carried

A1: "more organised" = organising index + consistent cross-references.
A2: "readme" = root README.md.
A3: the driving skill is an index over authorities, not a second CLAUDE.md.
A4: R2 read as bidirectional wiring.

## Verdict: PASS
