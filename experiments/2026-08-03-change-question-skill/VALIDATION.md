# Validation for: "create a skill for less intelligent LLMs ask the right questions in relation to this harness"

Validated at HEAD after step 8 (tranche base `ca1fd131`; skill commit
`b66b7f52`; wiring commit `b4141169`). All acceptance checks re-run fresh
this phase.

## Acceptance checks

S1: section count / frontmatter / provenance / committed-artifact refs on
`.claude/skills/dr-ask-the-right-question/SKILL.md`:

    sections: 6
    frontmatter: ok
    provenance: ok      (86f1248e, dr-decide-or-ask lineage credited)
    refs: 14            (criterion: >= 4)
    : PASS

S2: `grep -l dr-ask-the-right-question` over the four wiring targets:

    .claude/skills/deepreason-orchestrator/SKILL.md
    .claude/skills/dr-change-orchestrator/SKILL.md
    .claude/skills/dr-spec-change/SKILL.md
    CLAUDE.md
    : PASS (all four)

S3: `grep -q "## The survey (R2)" SPEC.md` -> survey section present : PASS

## Full gate

    python -m pytest tests/ -q -n 4   (step 7, at tree b4141169)
    -> 3290 passed, 7 skipped in 668.07s (0:11:08)   # 0 failed : PASS

Not re-run in this phase, with the reasoning recorded per the repo's own
law ("preserve results and re-derive only what moved", CLAUDE.md): the
only commit after the gate ran is step 8, which touched exactly
`experiments/2026-08-03-change-question-skill/CHECKLIST.md` — a tranche
markdown no test imports. `git diff --stat b4141169..HEAD` shows that one
file. Instrument cited with the number.

## Record-behavior preservation

n/a by construction, pasted as proof: `git diff --stat ca1fd131..HEAD --
src/` is EMPTY (0 lines) — this tranche changed no reader, writer, or any
`src/` file at all.

## Frozen-surface diff

    git diff --stat ca1fd131..HEAD -- src/deepreason/capabilities/state.py \
      src/deepreason/harness.py src/deepreason/invariants.py \
      src/deepreason/run_manifest.py src/deepreason/qualification.py
    -> (empty)   : PASS

## Map

    docs_verify:            0 failed (46 documents)            : PASS
    docs_verify --audit:    0 finding(s)                        : PASS
    docs_verify --links:    0 dangling, 46 document(s)          : PASS
    docs_verify --coverage: 6 seams swept, 0 finding(s)         : PASS
    docs_verify --stale:    4 entries, each dismissed below

--stale dismissals — all four entries cite the SAME commit, `2456da55`,
the previous tranche's fix: `INV-frozen-surfaces.md`,
`SEAM-harness-x-verification.md`, `SUB-verification.md` were each UPDATED
in that very commit (Traps entries, census correction) and stamped with
its parent `df0fd0fd`, because a commit cannot contain its own hash — the
stamp mechanically lags by one and the docs already describe the change
the entry points at. `REC-change-a-seam.md` owns `docs/map/` wholesale, so
any map motion flags it; its content (the recipe) is untouched by either
tranche. Nothing to update.

New checks added by this change: none in `docs/map/` — deliberate, not an
omission. This tranche changed no `src/` behaviour, and `.claude/skills/`
is outside the map's charter (CHECKLIST header; REQUEST map note). The
skill's claims are pinned instead by S1's grep set, re-run above. A
docs_verify mode for skill files is parked (SPEC "Out of scope").

## Requirement sweep

R1 (create the skill): demonstrated by S1 output — the file exists with
    the six sections, loadable frontmatter, and it registers in the
    session's skill list.
R2 (look over the framework): demonstrated by S3 output — the survey is a
    committed section of SPEC.md naming the gap, plus Q4's prior-art read.
R3 (close the reasoning gap / think about the right things): demonstrated
    by S1 — sections 1, 3, 5, 6 are the authority ladder, the record-first
    diagnostic sequence, falsifiable-fork framing, and the wrong-question
    table, each grounded in a committed scar.
R4 (understand the operator's questions and requests): demonstrated by
    S1 — section 2 is the operator-idiom translation table, every row
    citing a real committed exchange; section 4 derives answers from the
    operator's recorded values.
R5 (integrated tightly): demonstrated by S2 — both orchestrators route
    their stop-and-ask through the skill, dr-spec-change filters its
    question batch through it, CLAUDE.md names it as cutting across both
    families.

## Assumptions carried (operator may override)

A1: "right questions" spans record, framework, and operator, in cost
    order; operator comprehension has its own section.
A2: mechanism is a cross-cutting subskill + four-file wiring, not a third
    workflow family and not a bare document.
A3: audience is future agent sessions operating this repo via
    `.claude/skills/`; the provider model (glm-5.2, packs) is out of scope.
A4: `dr-decide-or-ask` absorbed as credited prior art; kw8imd lineage not
    resurrected.

## Verdict: PASS
