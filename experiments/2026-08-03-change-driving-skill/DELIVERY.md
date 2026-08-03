# Delivered: "a skill that teaches other LLMs how to run the harness properly and where to look"

Branch: `claude/handover-defect-audit-33pv3d` (pushed, tree clean; head is
the commit carrying this file).

## What changed

`dr-drive-harness` is the new driving manual: six sections covering what
the harness is (the typed record is the only evidence), session preflight,
the public CLI lifecycle, live-run ladder rules, where to look before
modifying anything (map reading order, frozen surfaces first, the seam
file's exact name and the recipe document), and where to look when
something breaks (the record-first table, Traps, ERRATA) — ending in
routing to both workflow families and `dr-ask-the-right-question`. It is
an index over the owning authorities, so it cannot drift into a second
CLAUDE.md. Around it, the workflow got the organisation you asked for:
`.claude/skills/README.md` now indexes all 16 skills (both families phase
by phase with the artifact each owns, plus the two cross-cutting skills);
both orchestrators point newcomers at the driving manual; the four
workflow files that said "seam document" without a path now name
`docs/map/SEAM-<a>-x-<b>.md` (sides alphabetical) and
`docs/map/REC-change-a-seam.md`; CLAUDE.md routes to both cross-cutting
skills, the skills index, and adds `docs/ERRATA.md` to session-start
reading; and README gained an "Operating this repository" section
referencing the driving skill while shedding historical-boundary sprawl
(357 lines from 363, every does/how section intact). Zero `src/` changes;
gate 3290 passed, 0 failed; all docs_verify modes green.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "a skill that teaches other LLMs how to run the harness properly and where to look" | done | commit 93f3da74; VALIDATION S1 |
| R2 | "wire the current workflows into the skills" | done-with-assumption A4 (bidirectional) | commit 6c61994e; VALIDATION S2 + S1's back-references |
| R3 | "the workflow needs to be more organised" | done-with-assumption A1 | `.claude/skills/README.md`; VALIDATION S3 |
| R4 | "claude.md will need updating because of last turns changes and this turns modifications" | done | VALIDATION S4 (driving skill + skills index + ERRATA in the truth chain) |
| R5 | "readme... reference there... more narrowly focused" | done | VALIDATION S5 (Operating-this-repository section; 357 < 363; does/how intact) |
| R6 | "This skill needs to reference the current workflows" | done | VALIDATION S1 routing section |
| R7 | "workflows mention changes to seams, but doesn't explicitly state where to find the document and what it's called" | done | commit 6c61994e; VALIDATION S6 (four files name the path and the recipe) |
| R8 | "sub documents never mentions the seam documents... But this job is a later task." | deferred (operator: "this job is a later task. For now, focus on the others.") | PARKED.md entry with ready-made inputs |

## Assumptions the operator may override

- A1: "more organised" = an organising index + consistent cross-references,
  not restructuring the proven phase machinery.
- A2: "readme" = the root `README.md`.
- A3: the driving skill indexes the owning authorities rather than copying
  them.
- A4: R2 wired both directions, matching the dr-ask-the-right-question
  precedent.

## Map delta

No map change — zero `src/` behaviour changed; `.claude/skills/`, README
and CLAUDE.md are outside the map's charter. docs_verify: 0 failed /
0 audit / 0 dangling / 0 coverage findings; the four `--stale` entries
carry over the previous tranche's dismissal (stamp-lags-parent on commit
2456da55) with no owned file moved since.

## Parked (not done, not promised)

- R8, in your words, as the ready-made next change tranche: SUB documents
  cross-referencing their seams, plus an isolated-vs-seam-modification
  triage rule (inputs listed in PARKED.md).
- Parallel-load flake:
  `test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
  failed once under `-n 4` on a loaded box, passed solo/file/rerun; zero
  src/tests changes here. Defect-family candidate.
- A docs_verify mode for `.claude/skills/` checks (carried over).
